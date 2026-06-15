# DECEPTR v1 — Architecture MVP

## Schema general

```
Internet
   |
   v
T-Pot (Cowrie SSH/Telnet)
   | cowrie.json
   v
Filebeat ---> Logstash ---> Elasticsearch (index cowrie-*)
                                  |
                                  v
                    Python Pipeline (collector.py)
                                  |
   +------------------------------+------------------------------+
   |          |           |            |            |            |
Normaliz.  Enrichiss.  Correlation  RiskScoring  Detection    Alerting
   |          |           |            |            |            |
   |     VirusTotal    MITRE ATT&CK   0-100      6 regles     Email
   |     AbuseIPDB
   |     GeoLite2
   |     Feodo Tracker
   v
Elasticsearch (deceptr-events-*) + MySQL 8 (alerts, iocs, attackers, campaigns)
   |                                          |
   v                                          v
Kibana (dashboards)              FastAPI (/api/...) ---> Dashboard HTML
   |
ElastAlert 2 ---> Email (CRITICAL/HIGH immediat)
```

## Les 7 etapes du pipeline

| # | Etape | Fichier | Role |
|---|---|---|---|
| 1 | Collecte | collector.py | Lit ES index `cowrie-*` (curseur timestamp) |
| 2 | Normalisation | normalizer.py | Cowrie brut → schema DECEPTR unifie |
| 3 | Enrichissement | enricher.py | GeoLite2 + VirusTotal + AbuseIPDB + Feodo |
| 4 | Correlation | correlator.py | Mapping MITRE ATT&CK |
| 5 | Risk Scoring | risk_scorer.py | Score 0-100 + severite |
| 6 | Detection | detector.py | 6 regles de detection |
| 7 | Alertes | alerter.py + storage.py | Email + ES + MySQL |

## Stockage

**Elasticsearch**
- `cowrie-*` : logs bruts (Filebeat → Logstash)
- `deceptr-events-*` : evenements enrichis (pipeline Python)

**MySQL 8**
- `alerts` — alertes generees par le detector
- `iocs` — indicateurs de compromission (1 ligne par IP)
- `attackers` — profils d'attaquants (credentials testes)
- `campaigns` — regroupement d'evenements par IP (fenetre 30min)
- `users` — comptes API (RBAC)
- `rapports_dgssi` — historique des rapports generes

## API FastAPI

| Endpoint | Methode | Description |
|---|---|---|
| `/api/auth/login` | POST | Authentification JWT |
| `/api/alerts` | GET | Liste paginee des alertes |
| `/api/alerts/stats` | GET | KPIs dashboard |
| `/api/alerts/timeline` | GET | Histogramme horaire (ES) |
| `/api/alerts/{id}/acknowledge` | PATCH | Acquitter une alerte |
| `/api/iocs` | GET | Liste des IoCs |
| `/api/iocs/{ip}` | GET | Detail d'une IP |
| `/api/attackers` | GET | Profils d'attaquants |
| `/api/campaigns` | GET | Campagnes detectees |
| `/api/dgssi/rapport` | GET | Rapport DGSSI HTML |
| `/api/dgssi/rapport/json` | GET | Rapport DGSSI JSON |
| `/api/dgssi/stats` | GET | Stats conformite |

## Reseaux Docker

- `dmz` — Cowrie uniquement (expose a Internet)
- `internal` — Pipeline, ES, MySQL, API, Kibana, ElastAlert (jamais expose)

## Perspectives post-MVP

- Multi-honeypots (Dionaea, Conpot, Canarytokens)
- Haute disponibilite (ES cluster, MySQL replica, Redis)
- Boucle de retroaction active (blocage pfSense automatique)
- Vault HashiCorp pour les secrets
- RBAC via Active Directory/LDAP
