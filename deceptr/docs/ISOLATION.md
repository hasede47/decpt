# DECEPTR - Isolation & Prevention Layer

## Network Architecture
The DECEPTR honeypot infrastructure is specifically designed to be deployed in a strictly isolated **DMZ (Demilitarized Zone)**. 

### 1. Ingress Rules (Inbound)
- **Allowed:** Port 2222 (mapped to SSH 22), Port 10443 (Web Honeypot), Port 445 (Dionaea SMB), etc.
- **Allowed:** Ingress from any external internet IP.

### 2. Egress Filtering (Outbound) - CRITICAL
Honeypots must **NEVER** be able to initiate outbound connections to the internal corporate network (LAN).
- **DENY:** All traffic from Honeypot subnet to Internal/Corporate Subnets (10.0.0.0/8, 192.168.0.0/16, etc.).
- **ALLOW:** Specific required outbound traffic (e.g., DNS 53 to public resolvers, TCP 443 to Threat Intel APIs like VirusTotal).
- **Rate Limiting:** Cap outbound bandwidth to prevent the honeypot from being used in DDoS attacks.

## Surrounding Controls
DECEPTR is a *detective* control. It must be paired with *preventive* controls:
- **MFA (Multi-Factor Authentication):** Enforced on all real remote access gateways.
- **EDR (Endpoint Detection and Response):** Deployed on all internal endpoints.
- **Least Privilege:** Internal SMB shares must restrict access strictly. The fake RH_Parlement share is intentionally open to lure attackers.

## Incident Response (Runbook)
When a DECEPTR alert fires (e.g., `CRITICAL: HONEYTOKEN TRIGGERED`):
1. **Triage:** Verify the IP in the DECEPTR Dashboard.
2. **Containment:** The `responder.py` module automatically blocks the IP at the firewall edge. Verify the block is active.
3. **Investigation:** Replay the Cowrie TTY session logs to see exactly what commands were executed.
4. **Remediation:** If lateral movement to the real network is detected, isolate the compromised internal machine immediately.
