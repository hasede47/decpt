# Architecture Reseau - DECEPTR v1 MVP

## Objectif

Cette vue montre les zones reseau, les ports exposes et les flux autorises. Les flux sont unidirectionnels autant que possible: Internet vers honeypot, puis honeypot vers analyse interne.

## Schema reseau

```mermaid
flowchart TB
  subgraph EXT["Zone externe"]
    Internet["Internet"]
    Attackers["Attaquants<br/>Bots / Scanners / Hackers"]
  end

  subgraph PERIM["Perimetre de securite"]
    FW["Firewall<br/>pfSense / FortiGate<br/>NAT / Filtrage / IDS-IPS / VPN"]
  end

  subgraph DMZ["DMZ - Zone publique 10.10.10.0/24"]
    TPOT["T-Pot Runtime<br/>Cowrie officiel<br/>IP logique: 10.10.10.10<br/>Ports: 22 / 23"]
    FB["Filebeat T-Pot Forwarder<br/>TLS vers Logstash"]
  end

  subgraph LAN["LAN interne - Analyse 10.10.20.0/24"]
    LS["Logstash<br/>TCP 5044 TLS"]
    RQ["Redis Queue<br/>6379 interne"]
    PY["Pipeline Python<br/>Collector / Normalizer / Enricher / Correlator / MITRE / Alerting"]
    ES["Elasticsearch<br/>9200"]
    SQL["MySQL<br/>3306 interne"]
    OBJ["MinIO<br/>9000 / 9001"]
    KB["Kibana<br/>5601"]
    API["FastAPI<br/>8000"]
    DASH["Dashboard<br/>8088"]
    EA["ElastAlert 2"]
  end

  subgraph SOC["Reseau Admin / SOC 10.10.30.0/24"]
    VPN["VPN Admin<br/>IPSec / SSL + MFA"]
    WS["SOC Workstation"]
  end

  Internet --> Attackers --> FW
  FW -->|"SSH/Telnet honeypot<br/>TCP 22/23"| TPOT
  TPOT --> FB
  FB -->|"Logs securises<br/>TCP 5044 / TLS 1.3"| LS
  LS --> RQ --> PY
  PY --> ES
  PY --> SQL
  PY --> OBJ
  ES --> KB
  ES --> EA
  SQL --> API
  ES --> API
  API --> DASH
  VPN --> WS
  WS -->|"HTTPS/HTTP lab<br/>5601 / 8000 / 8088 / 9001"| KB
  WS --> API
  WS --> DASH
  WS --> OBJ
```

## Ports reseau

| ID | Source | Destination | Port | Protocole | Role |
|---|---|---|---|---|---|
| R1 | Internet | T-Pot Cowrie | 22 | TCP | Honeypot SSH |
| R2 | Internet | T-Pot Cowrie | 23 | TCP | Honeypot Telnet |
| R3 | Filebeat T-Pot | DECEPTR Logstash | 5044 | TCP/TLS 1.3 | Envoi securise des logs |
| R4 | Logstash | Redis | 6379 | TCP interne | Queue d'evenements |
| R5 | Pipeline/API/Kibana | Elasticsearch | 9200 | HTTP interne | Logs et evenements |
| R6 | Pipeline/API | MySQL | 3306 | TCP interne | Donnees metier |
| R7 | Pipeline/API | MinIO | 9000 | HTTP/S3 interne | Objets, rapports, fichiers |
| R8 | Admin/SOC | Kibana | 5601 | HTTP lab / HTTPS prod | Dashboards analytiques |
| R9 | Admin/SOC | FastAPI | 8000 | HTTP lab / HTTPS prod | API REST |
| R10 | Admin/SOC | Dashboard | 8088 | HTTP lab / HTTPS prod | Dashboard SOC |
| R11 | Admin/SOC | MinIO Console | 9001 | HTTP lab / HTTPS prod | Console objets |

## Regles de securite

| Regle | Decision |
|---|---|
| Internet ne doit acceder qu'a Cowrie | Autoriser uniquement `TCP/22` et `TCP/23` vers la DMZ |
| T-Pot vers DECEPTR | Autoriser uniquement `TCP/5044` vers Logstash |
| Services internes | Ne pas exposer Redis/MySQL directement a Internet |
| Administration | Passer par VPN/MFA en production |
| TLS | Garder TLS 1.3 entre Filebeat et Logstash |

## Correspondance Docker actuelle

| Zone logique | Conteneurs |
|---|---|
| DMZ T-Pot | `cowrie`, `deceptr-tpot-forwarder` |
| Analyse interne | `deceptr-logstash`, `deceptr-redis`, `deceptr-pipeline`, `deceptr-elasticsearch`, `deceptr-mysql`, `deceptr-minio` |
| Visualisation/API | `deceptr-kibana`, `deceptr-api`, `deceptr-dashboard`, `deceptr-elastalert` |

