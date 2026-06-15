"""
DECEPTR — Étape 8 : Active Response (Boucle de Réponse Active)
Automatise le blocage des IP malveillantes via Firewall.
"""
import logging
import asyncio
import os
import platform

log = logging.getLogger("deceptr.responder")

# Mode simulation par défaut pour éviter de s'enfermer dehors (Lockout)
DRY_RUN = os.getenv("RESPONDER_DRY_RUN", "True").lower() == "true"

# Liste blanche d'IPs (Ne jamais bloquer ces IPs)
# Par exemple: DNS Google, IPs internes du Parlement, la passerelle
ALLOWLIST = {
    "127.0.0.1",
    "8.8.8.8",
    "10.0.0.1",
    # "192.168.1.100"
}

# Seuils pour déclencher le blocage
BLOCK_SEVERITIES = {"CRITICAL", "HIGH"}
BLOCK_MIN_ABUSE_SCORE = 80

class Responder:
    def __init__(self):
        self.os_type = platform.system()
        log.info(f"Active Response module loaded (OS: {self.os_type}, Dry Run: {DRY_RUN})")

    async def process(self, event: dict, alerts: list[dict]) -> None:
        """Détermine si l'attaquant doit être bloqué et exécute l'action."""
        src_ip = event.get("src_ip")
        if not src_ip or src_ip in ALLOWLIST:
            return

        should_block = False
        reason = ""

        # Condition 1 : Alerte HIGH/CRITICAL
        for alert in alerts:
            if alert.get("severity") in BLOCK_SEVERITIES:
                should_block = True
                reason = f"Alert {alert.get('severity')} - {alert.get('rule')}"
                break
        
        # Condition 2 : Score d'abus trop élevé
        if not should_block and event.get("abuse_score", 0) >= BLOCK_MIN_ABUSE_SCORE:
            should_block = True
            reason = f"High Abuse Score ({event.get('abuse_score')})"

        if should_block:
            await self._block_ip(src_ip, reason)

    async def _block_ip(self, ip: str, reason: str) -> None:
        """Bloque l'IP en fonction du système d'exploitation."""
        if DRY_RUN:
            log.warning(f"[RESPONDER - DRY RUN] L'IP {ip} serait bloquée. Raison: {reason}")
            return
        
        log.critical(f"[RESPONDER] Blocage actif de l'IP {ip}. Raison: {reason}")
        
        try:
            if self.os_type == "Linux":
                # Utilisation de UFW (Uncomplicated Firewall)
                cmd = f"sudo ufw deny from {ip} to any"
                await asyncio.to_thread(os.system, cmd)
            elif self.os_type == "Windows":
                # Utilisation de Windows Defender Firewall via netsh
                cmd = f'netsh advfirewall firewall add rule name="DECEPTR_BLOCK_{ip}" dir=in action=block remoteip={ip}'
                await asyncio.to_thread(os.system, cmd)
            else:
                log.error(f"[RESPONDER] OS non supporté pour le blocage automatique: {self.os_type}")
        except Exception as e:
            log.error(f"[RESPONDER] Erreur lors du blocage de {ip} : {e}")
