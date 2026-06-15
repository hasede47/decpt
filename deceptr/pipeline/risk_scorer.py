"""
DECEPTR — Étape 5 : Risk Scoring
Calcule un score de risque 0-100 basé sur :
  - Type d'événement (poids principal)
  - Score AbuseIPDB
  - Détections VirusTotal
  - IP C2 connue (Feodo Tracker)
  - Login réussi
  - Commande dangereuse exécutée
"""
import logging

log = logging.getLogger("deceptr.risk_scorer")

# Poids par type d'événement
EVENT_WEIGHTS = {
    "malware_download":  40,
    "login_success":     35,
    "command_execution": 30,
    "tunnel_attempt":    25,
    "file_upload":       20,
    "login_attempt":     10,
    "connection":         5,
    "unknown":            5,
}

# Commandes critiques → bonus de score
CRITICAL_COMMANDS = (
    "wget", "curl", "chmod +x", "bash", "python",
    "perl", "nc ", "ncat", "rm -rf", "/bin/sh",
    "cat /etc/passwd", "cat /etc/shadow",
)


class RiskScorer:
    def score(self, event: dict) -> dict:
        """
        Calcule le score de risque (0-100) et le niveau de sévérité.
        """
        score = 0

        # 1. Type d'événement (base)
        event_type = event.get("event_type", "unknown")
        score += EVENT_WEIGHTS.get(event_type, 5)

        # 2. AbuseIPDB — score max 25 points
        abuse = event.get("abuse_score", 0)
        score += min(25, int(abuse * 0.25))

        # 3. VirusTotal — max 20 points
        vt_mal = event.get("vt_malicious", 0)
        score += min(20, vt_mal * 4)

        # 4. IP C2 connue (Feodo) — +20 points
        if event.get("known_c2"):
            score += 20

        # 5. Commande critique — +15 points
        cmd = event.get("command", "").lower()
        if any(kw in cmd for kw in CRITICAL_COMMANDS):
            score += 15

        # 6. Login réussi — +10 points supplémentaires
        if event.get("login_success"):
            score += 10

        # 7. Chaînage de commandes (TTP Sequence) - Bonus +20 points
        if event_type == "command_execution":
            if ";" in cmd or "&&" in cmd or "|" in cmd:
                score += 20

        # Plafonner à 100
        score = min(100, score)

        event["risk_score"] = score
        event["severity"]   = self._severity(score)

        return event

    def _severity(self, score: int) -> str:
        if score >= 75: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 25: return "MEDIUM"
        return "LOW"
