"""
DECEPTR — Étape 2 : Normalisation
Convertit les événements Cowrie bruts en schéma DECEPTR unifié.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("deceptr.normalizer")

# IPs privées → ne pas enrichir avec les APIs externes
PRIVATE_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.", "192.168.", "127.", "::1"
)

# Events Cowrie sans intérêt analytique
SKIP_EVENTS = {
    "cowrie.session.connect",
    "cowrie.session.closed",
    "cowrie.client.version",
    "cowrie.client.kex",
    "cowrie.server.version",
    "cowrie.client.size",
}


class Normalizer:
    def normalize(self, raw: dict) -> Optional[dict]:
        """
        Transforme un doc Cowrie brut en événement DECEPTR normalisé.
        Retourne None si l'événement doit être ignoré.
        """
        eventid = raw.get("eventid", "")

        if eventid in SKIP_EVENTS:
            return None

        src_ip = raw.get("src_ip", "")
        if not src_ip:
            return None

        event = {
            # Identité
            "event_id":   str(uuid.uuid4()),
            "timestamp":  raw.get("@timestamp") or raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "source":     "cowrie",

            # Réseau
            "src_ip":     src_ip,
            "src_port":   int(raw.get("src_port", 0)),
            "dst_port":   int(raw.get("dst_port", 2222)),
            "protocol":   "ssh" if raw.get("dst_port", 2222) == 2222 else "telnet",
            "session":    raw.get("session", ""),

            # Événement
            "event_type": self._map_event_type(eventid),
            "cowrie_event": eventid,

            # Credentials (si login)
            "username":   raw.get("username", ""),
            "password":   raw.get("password", ""),

            # Commandes (si shell)
            "command":    raw.get("input", ""),

            # Fichiers (si download)
            "filename":   raw.get("filename", raw.get("url", "")),
            "file_sha512":raw.get("sha512", ""),

            # Flags
            "login_success":   eventid == "cowrie.login.success",
            "malware_dropped": "file" in eventid.lower() and "download" in eventid.lower(),
            "is_private_ip":   any(src_ip.startswith(p) for p in PRIVATE_PREFIXES),

            # Champs enrichis (remplis par les étapes suivantes)
            "geo":              {},
            "abuse_score":      0,
            "vt_malicious":     0,
            "known_c2":         False,
            "mitre_technique":  "",
            "mitre_tactic":     "",
            "mitre_tech_name":  "",
            "risk_score":       0,
            "alerts":           [],
            
            # Canary tokens
            "canary_token":     raw.get("canary_token", ""),
            "user_agent":       raw.get("user_agent", ""),
        }

        return event

    def _map_event_type(self, eventid: str) -> str:
        mapping = {
            "cowrie.login.success":       "login_success",
            "cowrie.login.failed":        "login_attempt",
            "cowrie.command.input":       "command_execution",
            "cowrie.session.file_upload": "file_upload",
            "cowrie.session.file_download":"malware_download",
            "cowrie.direct-tcpip.request":"tunnel_attempt",
            "cowrie.session.connect":     "connection",
            "canary.triggered":           "honeytoken_triggered",
            "web.login.attempt":          "web_login_attempt",
        }
        return mapping.get(eventid, "unknown")
