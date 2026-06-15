"""
DECEPTR — Étape 4 : Corrélation + MITRE ATT&CK
Mappe chaque événement Cowrie sur une technique ATT&CK.
Regroupe les événements par IP pour détecter les campagnes.
"""
import logging
from datetime import datetime, timezone

log = logging.getLogger("deceptr.correlator")

# ── Mapping MITRE ATT&CK ───────────────────────────────────────────────────────
# Source : MITRE ATT&CK v14 — techniques SSH/Telnet
ATTACK_MAP = {
    "login_attempt":     ("TA0001", "Initial Access",     "T1110",  "Brute Force"),
    "login_success":     ("TA0001", "Initial Access",     "T1078",  "Valid Accounts"),
    "command_execution": ("TA0002", "Execution",          "T1059",  "Command and Scripting Interpreter"),
    "file_upload":       ("TA0003", "Persistence",        "T1505",  "Server Software Component"),
    "malware_download":  ("TA0011", "Command and Control","T1105",  "Ingress Tool Transfer"),
    "tunnel_attempt":    ("TA0008", "Lateral Movement",   "T1021",  "Remote Services"),
    "connection":        ("TA0043", "Reconnaissance",     "T1595",  "Active Scanning"),
    "unknown":           ("TA0043", "Reconnaissance",     "T1595",  "Active Scanning"),
}

# Commandes Cowrie → sous-technique T1059
SHELL_COMMANDS = {
    ("wget",  "curl"):   ("T1059.004", "Unix Shell - Download"),
    ("chmod",):          ("T1059.004", "Unix Shell - Permission Change"),
    ("bash",  "sh"):     ("T1059.004", "Unix Shell - Shell Execution"),
    ("python","perl"):   ("T1059.006", "Python/Perl Execution"),
    ("nc",    "ncat"):   ("T1059.004", "Unix Shell - Netcat"),
    ("rm -rf","dd "):    ("T1485",     "Data Destruction"),
    ("uname", "whoami", "id", "pwd"): ("T1082", "System Information Discovery"),
    ("cat /etc/passwd",):("T1003",    "OS Credential Dumping"),
}


class Correlator:
    def correlate(self, event: dict) -> dict:
        """
        1. Mappe l'événement sur une technique ATT&CK
        2. Affine le mapping si commande shell reconnue
        3. Ajoute la date de corrélation
        """
        event_type = event.get("event_type", "unknown")

        # Mapping principal
        tactic_id, tactic, tech_id, tech_name = ATTACK_MAP.get(
            event_type,
            ("TA0043", "Reconnaissance", "T1595", "Active Scanning")
        )

        # Affinage pour les commandes shell
        if event_type == "command_execution":
            cmd = event.get("command", "").lower()
            for keywords, (sub_tech, sub_name) in SHELL_COMMANDS.items():
                if any(kw in cmd for kw in keywords):
                    tech_id   = sub_tech
                    tech_name = sub_name
                    break

        event["mitre_tactic_id"]  = tactic_id
        event["mitre_tactic"]     = tactic
        event["mitre_technique"]  = tech_id
        event["mitre_tech_name"]  = tech_name
        event["mitre_url"]        = f"https://attack.mitre.org/techniques/{tech_id.replace('.','/')}/"
        event["correlated_at"]    = datetime.now(timezone.utc).isoformat()

        return event
