"""
DECEPTR — Étape 7a : Alertes
Envoie les alertes CRITICAL/HIGH par email via SMTP.
"""
import asyncio
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("deceptr.alerter")

SMTP_HOST  = os.getenv("SMTP_HOST", "")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", "")
SMTP_PASS  = os.getenv("SMTP_PASS", "")
ALERT_TO   = os.getenv("ALERT_TO", "")
SEV_SEND   = {"CRITICAL", "HIGH"}  # Seules ces sévérités déclenchent un email


class Alerter:
    async def process(self, event: dict, alerts: list[dict]) -> None:
        """Traite les alertes : log + email si sévérité suffisante."""
        for alert in alerts:
            sev = alert.get("severity", "LOW")
            log.warning(
                f"[ALERTE] {sev:8s} | {alert['rule']:25s} | "
                f"{event.get('src_ip','?'):15s} | {alert['title']}"
            )
            if sev in SEV_SEND and SMTP_HOST and ALERT_TO:
                await asyncio.to_thread(self._send_email, event, alert)

    def _send_email(self, event: dict, alert: dict) -> None:
        geo   = event.get("geo", {})
        pays  = geo.get("country_name", "?")
        score = event.get("risk_score", 0)
        sev   = alert.get("severity", "?")
        emoji = "🔴" if sev == "CRITICAL" else "🟠"

        subject = f"[DECEPTR] {emoji} {sev} — {alert['rule']} — {event.get('src_ip','?')}"
        html = f"""
        <html><body style="font-family:monospace;background:#080a0d;color:#ddeaf5;padding:24px">
        <h2 style="color:#4af0b4">DECEPTR — Alerte {sev}</h2>
        <table style="border-collapse:collapse">
          <tr><td style="color:#8fa3c0;padding:4px 12px">IP Attaquant</td>
              <td style="padding:4px 12px"><b>{event.get("src_ip","?")}</b></td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Pays</td>
              <td style="padding:4px 12px">{pays}</td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Type</td>
              <td style="padding:4px 12px">{event.get("event_type","?")}</td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">ATT&CK</td>
              <td style="padding:4px 12px">{event.get("mitre_technique","?")} — {event.get("mitre_tech_name","?")}</td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Risk Score</td>
              <td style="padding:4px 12px"><b>{score}/100</b></td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Règle</td>
              <td style="padding:4px 12px">{alert["rule"]}</td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Détail</td>
              <td style="padding:4px 12px">{alert.get("detail","")}</td></tr>
          <tr><td style="color:#8fa3c0;padding:4px 12px">Timestamp</td>
              <td style="padding:4px 12px">{event.get("timestamp","?")}</td></tr>
        </table>
        <p style="margin-top:20px;color:#3d4f6b">DECEPTR v1 · Chambre des Représentants du Maroc</p>
        </body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = ALERT_TO
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, ALERT_TO, msg.as_string())
            log.info(f"Email envoyé pour {alert['rule']} — {event.get('src_ip')}")
        except Exception as e:
            log.error(f"Erreur email : {e}")
