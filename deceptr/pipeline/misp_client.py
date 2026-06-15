import logging
import aiohttp
import os

log = logging.getLogger("deceptr.misp")

MISP_URL = os.getenv("MISP_URL", "")
MISP_KEY = os.getenv("MISP_KEY", "")

class MISPClient:
    async def export_ioc(self, event: dict):
        if not MISP_URL or not MISP_KEY:
            return
            
        ip = event.get("src_ip")
        if not ip:
            return
            
        try:
            async with aiohttp.ClientSession() as s:
                payload = {
                    "Event": {
                        "info": f"DECEPTR Honeypot Detection - {event.get('event_type')}",
                        "Attribute": [
                            {
                                "type": "ip-src",
                                "value": ip,
                                "to_ids": True,
                                "comment": f"Detected by DECEPTR rule: {event.get('mitre_technique')} ({event.get('severity')})"
                            }
                        ]
                    }
                }
                
                async with s.post(
                    f"{MISP_URL}/events/add",
                    headers={
                        "Authorization": MISP_KEY,
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as r:
                    if r.status == 200:
                        log.info(f"MISP: IOC exporte avec succes ({ip})")
                    else:
                        log.debug(f"MISP: Erreur lors de l'export ({r.status})")
        except Exception as e:
            log.debug(f"Erreur MISP export: {e}")
