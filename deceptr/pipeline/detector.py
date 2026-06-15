"""
DECEPTR — Étape 6 : Détection
Applique des règles de détection sur l'événement enrichi.
Retourne une liste d'alertes déclenchées.
"""
import logging

log = logging.getLogger("deceptr.detector")


class Detector:
    """
    Règles de détection basées sur les événements Cowrie.
    Chaque règle retourne un dict d'alerte ou None.
    """

    RULES = [
        "_rule_malware_drop",
        "_rule_login_success",
        "_rule_critical_command",
        "_rule_c2_ip",
        "_rule_credential_capture",
        "_rule_high_risk",
        "_rule_obfuscated_command",
    ]

    def detect(self, event: dict) -> list[dict]:
        """Applique toutes les règles et retourne les alertes déclenchées."""
        alerts = []
        for rule_name in self.RULES:
            rule = getattr(self, rule_name)
            alert = rule(event)
            if alert:
                alerts.append(alert)
        return alerts

    def _rule_malware_drop(self, e: dict):
        if e.get("malware_dropped") or e.get("event_type") == "malware_download":
            return {
                "rule":    "MALWARE_DROP",
                "title":   "Malware déposé sur le honeypot",
                "detail":  f"Fichier : {e.get('filename', 'inconnu')}",
                "severity":"CRITICAL",
            }

    def _rule_login_success(self, e: dict):
        if e.get("login_success"):
            return {
                "rule":    "LOGIN_SUCCESS",
                "title":   "Connexion SSH réussie sur le honeypot",
                "detail":  f"user={e.get('username','?')} pass={e.get('password','?')}",
                "severity":"HIGH",
            }

    def _rule_critical_command(self, e: dict):
        cmd = e.get("command", "").lower()
        critical = ("wget", "curl", "chmod +x", "python", "perl", "nc ", "/bin/sh",
                    "cat /etc/passwd", "cat /etc/shadow", "rm -rf")
        if e.get("event_type") == "command_execution" and any(c in cmd for c in critical):
            return {
                "rule":    "CRITICAL_COMMAND",
                "title":   "Commande critique exécutée",
                "detail":  f"cmd={e.get('command','?')[:100]}",
                "severity":"HIGH",
            }

    def _rule_c2_ip(self, e: dict):
        if e.get("known_c2"):
            return {
                "rule":    "KNOWN_C2_IP",
                "title":   "IP C2 connue (Feodo Tracker)",
                "detail":  f"IP {e.get('src_ip')} répertoriée comme serveur C2 actif",
                "severity":"CRITICAL",
            }

    def _rule_credential_capture(self, e: dict):
        if e.get("event_type") == "login_attempt" and e.get("username") and e.get("password"):
            return {
                "rule":    "CREDENTIAL_CAPTURE",
                "title":   "Tentative de connexion avec credentials",
                "detail":  f"user={e.get('username','?')} pass={e.get('password','?')}",
                "severity":"MEDIUM",
            }

    def _rule_high_risk(self, e: dict):
        if e.get("risk_score", 0) >= 75 and not any([
            e.get("malware_dropped"), e.get("login_success"), e.get("known_c2")
        ]):
            return {
                "rule":    "HIGH_RISK_SCORE",
                "title":   f"Score de risque élevé : {e.get('risk_score')}/100",
                "detail":  f"ATT&CK : {e.get('mitre_technique')} — {e.get('mitre_tech_name')}",
                "severity":"HIGH",
            }

    def _rule_obfuscated_command(self, e: dict):
        cmd = e.get("command", "")
        # Détection basique de base64 ou hex encoding
        if "base64 " in cmd or "b64decode" in cmd or "\\x" in cmd:
            return {
                "rule":    "OBFUSCATED_COMMAND",
                "title":   "Commande obfusquée détectée (Base64/Hex)",
                "detail":  f"cmd={cmd[:100]}",
                "severity":"CRITICAL",
            }
