"""
DECEPTR — Étape 7b : Stockage
Écrit l'événement enrichi dans Elasticsearch (deceptr-events-*)
et synchronise les données métier dans MySQL (Alerts, Attackers, IoCs, Campaigns).
"""
import asyncio
import logging
from datetime import datetime, timezone

from elasticsearch import AsyncElasticsearch
from minio import Minio
from config import (
    ELASTIC_HOST, ELASTIC_USER, ELASTIC_PASSWORD, EVENTS_INDEX,
    MYSQL_HOST, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD,
    MINIO_ACCESS_KEY, MINIO_BUCKETS, MINIO_ENDPOINT, MINIO_SECRET_KEY, MINIO_SECURE
)

log = logging.getLogger("deceptr.storage")


def _mysql_datetime(value) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Storage:
    def __init__(self):
        self._es   = None
        self._pool = None
        self._minio = None

    async def connect(self):
        await self._connect_es()
        await self._connect_mysql()
        await asyncio.to_thread(self._connect_minio)

    def _connect_minio(self):
        try:
            self._minio = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
            )
            for bucket in MINIO_BUCKETS:
                if not self._minio.bucket_exists(bucket):
                    self._minio.make_bucket(bucket)
            log.info("MinIO connecte: buckets prets.")
        except Exception as e:
            self._minio = None
            log.warning(f"MinIO indisponible: {e}")

    # ── Elasticsearch ────────────────────────────────────────────────────────

    async def _connect_es(self):
        self._es = AsyncElasticsearch(
            hosts=[ELASTIC_HOST],
            basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            verify_certs=False,
        )
        for attempt in range(15):
            try:
                info = await self._es.info()
                log.info(f"Elasticsearch connecté : {info['version']['number']}")
                await self._create_index_template()
                return
            except Exception as e:
                log.warning(f"ES tentative {attempt+1}/15 : {e}")
                await asyncio.sleep(5)
        log.error("Elasticsearch inaccessible.")

    async def _create_index_template(self):
        template = {
            "index_patterns": [f"{EVENTS_INDEX}-*"],
            "template": {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "timestamp":         {"type": "date"},
                        "src_ip":            {"type": "ip"},
                        "severity":          {"type": "keyword"},
                        "event_type":        {"type": "keyword"},
                        "mitre_technique":   {"type": "keyword"},
                        "mitre_tactic":      {"type": "keyword"},
                        "risk_score":        {"type": "integer"},
                        "abuse_score":       {"type": "integer"},
                        "vt_malicious":      {"type": "integer"},
                        "known_c2":          {"type": "boolean"},
                        "login_success":     {"type": "boolean"},
                        "malware_dropped":   {"type": "boolean"},
                        "geo": {
                            "properties": {
                                "country_iso":  {"type": "keyword"},
                                "country_name": {"type": "keyword"},
                                "city":         {"type": "keyword"},
                                "location":     {"type": "geo_point"},
                            }
                        }
                    }
                }
            }
        }
        try:
            await self._es.indices.put_index_template(name="deceptr-events", body=template)
        except Exception as e:
            log.debug(f"Template : {e}")

    # ── MySQL ────────────────────────────────────────────────────────────────

    async def _connect_mysql(self):
        import aiomysql
        for attempt in range(10):
            delay = min(2 ** attempt, 30)
            try:
                self._pool = await aiomysql.create_pool(
                    host=MYSQL_HOST, db=MYSQL_DB,
                    user=MYSQL_USER, password=MYSQL_PASSWORD,
                    minsize=1, maxsize=5, autocommit=True, connect_timeout=10
                )
                log.info("MySQL connecté.")
                return
            except Exception as e:
                log.warning(f"MySQL tentative {attempt+1}/10 — retry {delay}s : {e}")
                await asyncio.sleep(delay)
        log.error("MySQL inaccessible.")

    # ── Sauvegarde ───────────────────────────────────────────────────────────

    async def save(self, event: dict, alerts: list[dict]) -> None:
        """Sauvegarde l'événement dans ES, puis les données métier dans MySQL."""
        await self._save_es(event)
        await self._save_mysql(event, alerts)

    async def _save_es(self, event: dict) -> None:
        if not self._es:
            return
        doc = {k: v for k, v in event.items() if k != "raw"}
        geo = doc.get("geo", {})
        if geo.get("latitude") and geo.get("longitude"):
            doc["geo"] = {**geo, "location": {"lat": geo["latitude"], "lon": geo["longitude"]}}
        index = f"{EVENTS_INDEX}-{datetime.now().strftime('%Y.%m')}"
        try:
            await self._es.index(index=index, document=doc)
        except Exception as e:
            log.error(f"ES save error : {e}")

    async def _save_mysql(self, event: dict, alerts: list[dict]) -> None:
        if not self._pool:
            return
        geo = event.get("geo", {})
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # 1. IoC (upsert via procédure stockée)
                    await cur.callproc("upsert_ioc", (
                        event.get("src_ip", ""),
                        geo.get("country_iso", ""),
                        geo.get("country_name", ""),
                        geo.get("city", ""),
                        float(geo.get("latitude", 0)),
                        float(geo.get("longitude", 0)),
                        geo.get("asn", ""),
                        geo.get("org", ""),
                        int(event.get("abuse_score", 0)),
                        int(event.get("vt_malicious", 0)),
                        int(event.get("known_c2", False)),
                        event.get("mitre_technique", ""),
                        event.get("mitre_tactic", ""),
                        event.get("mitre_tech_name", ""),
                        event.get("severity", "LOW"),
                        int(event.get("risk_score", 0)),
                    ))

                    # 2. Attacker (upsert)
                    await cur.callproc("upsert_attacker", (
                        event.get("src_ip", ""),
                        event.get("username", ""),
                        event.get("password", ""),
                        int(event.get("login_success", False)),
                    ))

                    # 3. Alertes (une ligne par règle déclenchée)
                    for alert in alerts:
                        await cur.execute("""
                            INSERT INTO alerts (
                                event_id, src_ip, rule_name, title, detail,
                                severity, event_type, mitre_technique, mitre_tactic,
                                mitre_tech_name, risk_score, country_iso, country_name,
                                abuse_score, vt_malicious, known_c2, timestamp
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (
                            event.get("event_id"),
                            event.get("src_ip"),
                            alert.get("rule"),
                            alert.get("title"),
                            alert.get("detail"),
                            alert.get("severity"),
                            event.get("event_type"),
                            event.get("mitre_technique"),
                            event.get("mitre_tactic"),
                            event.get("mitre_tech_name"),
                            event.get("risk_score", 0),
                            geo.get("country_iso", ""),
                            geo.get("country_name", ""),
                            event.get("abuse_score", 0),
                            event.get("vt_malicious", 0),
                            int(event.get("known_c2", False)),
                            _mysql_datetime(event.get("timestamp")),
                        ))

                    # 4. Campagne (regroupement par IP, mise à jour si récente)
                    await cur.callproc("update_campaign", (
                        event.get("src_ip", ""),
                        event.get("mitre_technique", ""),
                        event.get("severity", "LOW"),
                    ))

                    # 5. Honeytokens
                    if event.get("cowrie_event") == "canary.triggered" and event.get("canary_token"):
                        await cur.execute("""
                            INSERT INTO honeytokens (token_id, token_type, filepath, triggered, last_trigger_ip, last_trigger_date)
                            VALUES (%s, 'canary', 'unknown', 1, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                triggered=1, last_trigger_ip=VALUES(last_trigger_ip), last_trigger_date=VALUES(last_trigger_date)
                        """, (
                            event.get("canary_token"),
                            event.get("src_ip"),
                            _mysql_datetime(event.get("timestamp"))
                        ))

        except Exception as e:
            log.error(f"MySQL save error : {e}")
