"""
DECEPTR — Étape 3 : Enrichissement
Sources : GeoLite2 (local) + VirusTotal + AbuseIPDB + Feodo Tracker
"""
import asyncio
import logging
import time
from typing import Optional

import aiohttp
from config import VIRUSTOTAL_KEY, ABUSEIPDB_KEY, GEOIP_DB, FEODO_URL

log = logging.getLogger("deceptr.enricher")

# Cache IP → enrichissement (TTL 6h)
_CACHE: dict = {}
_CACHE_TTL = 21600

# Feodo Tracker — liste locale (rechargée toutes les heures)
_C2_IPS: set = set()
_C2_LOADED_AT: float = 0.0


class RateLimiter:
    """Limiteur de débit simple pour les APIs gratuites."""
    def __init__(self, rpm: int):
        self._rpm = rpm
        self._slots: list[float] = []

    async def acquire(self):
        now = time.monotonic()
        self._slots = [t for t in self._slots if now - t < 60]
        if len(self._slots) >= self._rpm:
            wait = 60 - (now - self._slots[0]) + 0.1
            await asyncio.sleep(wait)
        self._slots.append(time.monotonic())


class Enricher:
    def __init__(self):
        self._vt_rl = RateLimiter(4)    # VirusTotal : 4 req/min (free)
        self._ab_rl = RateLimiter(20)   # AbuseIPDB  : conservative
        self._geo   = None
        self._load_geoip()

    def _load_geoip(self):
        try:
            import geoip2.database
            self._geo = geoip2.database.Reader(GEOIP_DB)
            log.info("GeoLite2 chargé.")
        except Exception:
            log.warning("GeoLite2 non disponible. Déposer GeoLite2-City.mmdb dans pipeline/data/")

    async def load_feodo(self):
        """Charge la liste Feodo Tracker au démarrage."""
        await self._reload_feodo()

    async def enrich(self, event: dict) -> dict:
        """Enrichit l'événement avec GeoIP, VT, AbuseIPDB, Feodo."""
        ip = event.get("src_ip", "")

        # IPs privées → pas d'enrichissement externe
        if event.get("is_private_ip") or not ip:
            event["geo"] = {"country_iso": "LAN", "country_name": "Réseau local", "city": ""}
            return event

        # Cache
        cached = self._from_cache(ip)
        if cached:
            event.update(cached)
            return event

        # Rechargement Feodo si nécessaire
        await self._reload_feodo()

        # Enrichissement parallèle
        geo, abuse, vt = await asyncio.gather(
            self._geoip(ip),
            self._abuseipdb(ip),
            self._virustotal(ip),
            return_exceptions=True
        )

        enrichment = {}
        if isinstance(geo,   dict): enrichment["geo"]          = geo
        if isinstance(abuse, dict): enrichment["abuse_score"]  = abuse.get("abuseConfidenceScore", 0)
        if isinstance(vt,    dict): enrichment["vt_malicious"] = vt.get("malicious", 0)
        enrichment["known_c2"] = ip in _C2_IPS
        if enrichment["known_c2"]:
            enrichment["abuse_score"] = max(enrichment.get("abuse_score", 0), 90)

        self._to_cache(ip, enrichment)
        event.update(enrichment)
        return event

    async def _geoip(self, ip: str) -> dict:
        if not self._geo:
            return {"country_iso": "?", "country_name": "Inconnu", "city": "",
                    "latitude": 0.0, "longitude": 0.0, "asn": "", "org": ""}
        try:
            r = self._geo.city(ip)
            return {
                "country_iso":  r.country.iso_code   or "?",
                "country_name": r.country.name       or "Inconnu",
                "city":         r.city.name          or "",
                "latitude":     float(r.location.latitude  or 0),
                "longitude":    float(r.location.longitude or 0),
                "asn":          str(r.traits.autonomous_system_number or ""),
                "org":          r.traits.autonomous_system_organization or "",
            }
        except Exception:
            return {"country_iso": "?", "country_name": "Inconnu", "city": ""}

    async def _abuseipdb(self, ip: str) -> dict:
        if not ABUSEIPDB_KEY:
            return {}
        await self._ab_rl.acquire()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    headers={"Key": ABUSEIPDB_KEY, "Accept": "application/json"},
                    params={"ipAddress": ip, "maxAgeInDays": 90},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as r:
                    if r.status == 200:
                        return (await r.json()).get("data", {})
        except Exception as e:
            log.debug(f"AbuseIPDB {ip}: {e}")
        return {}

    async def _virustotal(self, ip: str) -> dict:
        if not VIRUSTOTAL_KEY:
            return {}
        await self._vt_rl.acquire()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
                    headers={"x-apikey": VIRUSTOTAL_KEY},
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as r:
                    if r.status == 200:
                        stats = (await r.json()).get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                        return {"malicious": stats.get("malicious", 0), "suspicious": stats.get("suspicious", 0)}
        except Exception as e:
            log.debug(f"VirusTotal {ip}: {e}")
        return {}

    async def _reload_feodo(self):
        global _C2_IPS, _C2_LOADED_AT
        if time.time() - _C2_LOADED_AT < 3600:
            return
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(FEODO_URL, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        data = await r.json(content_type=None)
                        _C2_IPS = {e["ip_address"] for e in data if e.get("ip_address")}
                        _C2_LOADED_AT = time.time()
                        log.info(f"Feodo Tracker : {len(_C2_IPS)} IPs C2 chargées")
        except Exception as e:
            log.debug(f"Feodo reload : {e}")

    def _from_cache(self, ip: str) -> Optional[dict]:
        if ip in _CACHE:
            d, ts = _CACHE[ip]
            if time.time() - ts < _CACHE_TTL:
                return d
            del _CACHE[ip]
        return None

    def _to_cache(self, ip: str, data: dict):
        if len(_CACHE) > 5000:
            oldest = sorted(_CACHE.items(), key=lambda x: x[1][1])[:500]
            for k, _ in oldest:
                del _CACHE[k]
        _CACHE[ip] = (data, time.time())
