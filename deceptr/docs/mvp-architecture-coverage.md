# DECEPTR v1 MVP Architecture Coverage

This file maps the MVP architecture diagram to the implementation in this repository.

## Network Architecture

| Diagram block | Project implementation |
|---|---|
| Internet / attackers | External clients connect to published Cowrie ports `2222` and `2223`. |
| Firewall / perimeter | Represented as the host/network boundary before Docker; production deployment should place these published ports behind pfSense/FortiGate NAT rules. |
| DMZ / T-POT server | Production mode uses an external official T-Pot sensor; lab mode can use local `cowrie` service on Docker network `dmz`. |
| Cowrie SSH/Telnet | Production source is T-Pot Cowrie via `tpot/docker-compose.deceptr-forwarder.yml`; lab source is `cowrie/`, service `cowrie`, ports `2222` and `2223`. |
| Filebeat | `elk/filebeat.yml`, service `filebeat`, plus optional T-Pot forwarder in `tpot/`. |
| Logstash | `elk/logstash/pipeline/cowrie.conf`, service `logstash`, TLS Beats input on `5044`. |
| Internal LAN analysis services | Docker network `internal`. |
| Admin/SOC access | Dashboard, Kibana and API exposed through `dashboard/index.html`, `5601`, and `8000`. |

## Functional Architecture

| Diagram block | Project implementation |
|---|---|
| Detection | Cowrie captures SSH/Telnet activity and writes JSON logs. |
| Filebeat collection | Filebeat reads the Cowrie log volume and ships to Logstash. |
| Logstash parsing | Logstash normalizes timestamps and source IP fields. |
| Redis queue | `redis` service plus `config/redis/redis.conf`; Logstash pushes JSON to `REDIS_QUEUE`. |
| Python collector | `pipeline/collector.py` consumes Redis first, then falls back to `cowrie-*` Elasticsearch indices. |
| Normalizer | `pipeline/normalizer.py`. |
| Enricher | `pipeline/enricher.py` with VirusTotal, AbuseIPDB, GeoLite2, and Feodo Tracker. |
| Correlator / MITRE mapper | `pipeline/correlator.py`. |
| Risk scoring | `pipeline/risk_scorer.py`. |
| Alert generation | `pipeline/detector.py` and `pipeline/alerter.py`. |
| Logs storage | Elasticsearch service and `cowrie-*` / `deceptr-events-*` indices. |
| Business storage | MySQL service, `mysql/schema.sql`, `mysql/procedures.sql`. |
| Object storage | MinIO service; `pipeline/storage.py` creates `malware-samples`, `downloads`, `reports`, and `backups`. |
| Visualization | Kibana service plus `dashboard/index.html`. |
| API backend | FastAPI in `pipeline/api/`, exposed on port `8000`. |
| ElastAlert 2 | `elk/elastalert/`, service `elastalert`. |
| Notifications | Email SMTP in `pipeline/alerter.py`; webhook/syslog are extension points. |
| Users / actors | JWT authentication and roles in `pipeline/api/auth.py` and `mysql/schema.sql`. |

## Remaining Real-World Deployment Notes

The repository now matches the MVP diagram at software/service level when paired with an official external T-Pot sensor. The physical firewall, switch, VPN/MFA, and separated IP subnets are deployment infrastructure items and must be configured on the target network or virtualization platform.
