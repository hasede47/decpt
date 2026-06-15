# DECEPTR Logical Completion Status

## Completed In Repository

| Architecture element | Status |
|---|---|
| Official T-Pot sensor placement | Prepared as external DMZ sensor with install helper |
| Cowrie from T-Pot | Prepared via `tpot/docker-compose.deceptr-forwarder.yml` |
| Filebeat -> Logstash security | TLS enabled and verified with TLS 1.3 |
| Logstash ingestion | TCP/5044 exposed for T-Pot Filebeat |
| Redis queue | Configured and used by pipeline |
| Python collector / normalizer / enricher / correlator / scorer / detector | Implemented |
| Elasticsearch raw and enriched indices | Implemented |
| MySQL business tables | Implemented |
| MinIO object buckets | Implemented |
| FastAPI backend | Implemented |
| Dashboard and Kibana | Implemented |
| ElastAlert | Implemented |
| Host firewall templates | Added for Windows and Linux |
| Production mode without local Cowrie | Added with `docker-compose.tpot.yml` |

## Still Physical Or Environment-Specific

These items cannot be completed inside this repository alone:

| Item | Why |
|---|---|
| Real DMZ/LAN/Admin subnets | Requires router/firewall/virtual switch configuration |
| pfSense/FortiGate NAT and filtering | Requires the selected firewall appliance |
| VPN/MFA/Bastion host | Requires organization identity/network setup |
| Dedicated T-Pot VM/server | Must be provisioned outside this Compose project |
| Public attack traffic | Requires controlled exposure of the T-Pot sensor |

