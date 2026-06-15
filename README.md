# DECEPTR v1 MVP - Final Folder

This folder contains the clean final project only.

Architecture:

```text
T-Pot Cowrie (ports 22/23)
  -> Filebeat forwarder TLS 1.3
  -> DECEPTR Logstash 5044
  -> Redis queue
  -> Python pipeline
  -> Elasticsearch / MySQL / MinIO
  -> Kibana / FastAPI / DECEPTR dashboard / ElastAlert
```

Excluded from this final architecture:
- extra T-Pot web tools outside the schema
- old fake DECEPTR services
- unrelated projects such as Pentagi, SIEM, Mongo, etc.

Architecture documents:
- `docs/architecture-fonctionnelle.md`
- `docs/architecture-reseau.md`
- `docs/architecture-technique.md`
- `docs/architecture-fonctionnelle.pdf`
- `docs/architecture-reseau.pdf`
- `docs/architecture-technique.pdf`
- `docs/architectures-deceptr.pdf`
- `docs/DECEPTR_Guide_Complet_Installation_Configuration.pdf`

Start:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

Dashboards:
- DECEPTR Dashboard: http://127.0.0.1:8088/index.html?v=3
- Kibana: http://127.0.0.1:5601
- API Docs: http://127.0.0.1:8000/docs
- MinIO: http://127.0.0.1:9001

Honeypot:
- SSH: `ssh root@127.0.0.1 -p 22`
- Telnet: `telnet 127.0.0.1 23`
