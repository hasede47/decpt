"""DECEPTR — Configuration centralisée depuis variables d'environnement"""
import os
from dotenv import load_dotenv

load_dotenv()

# Elasticsearch
ELASTIC_HOST     = os.getenv("ELASTIC_HOST",     "http://elasticsearch:9200")
ELASTIC_USER     = os.getenv("ELASTIC_USER",     "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "deceptr2025")
COWRIE_INDEX     = os.getenv("COWRIE_INDEX",     "cowrie-*")       # Lu par collector
EVENTS_INDEX     = os.getenv("EVENTS_INDEX",     "deceptr-events") # Écrit par pipeline

# MySQL
MYSQL_HOST       = os.getenv("MYSQL_HOST",     "mysql")
MYSQL_PORT       = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB         = os.getenv("MYSQL_DB",       "deceptr")
MYSQL_USER       = os.getenv("MYSQL_USER",     "deceptr")
MYSQL_PASSWORD   = os.getenv("MYSQL_PASSWORD", "mysql2025")

# Redis queue (Logstash -> Pipeline)
REDIS_HOST       = os.getenv("REDIS_HOST",     "redis")
REDIS_PORT       = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD   = os.getenv("REDIS_PASSWORD", "")
REDIS_QUEUE      = os.getenv("REDIS_QUEUE",    "deceptr:events")

# MinIO object storage
MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT",   "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "deceptr_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "MotDePasseMinIO2026!")
MINIO_SECURE     = os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}
MINIO_BUCKETS    = ("malware-samples", "downloads", "reports", "backups")

# Threat Intelligence
VIRUSTOTAL_KEY   = os.getenv("VIRUSTOTAL_KEY",  "")
ABUSEIPDB_KEY    = os.getenv("ABUSEIPDB_KEY",   "")
GEOIP_DB         = os.getenv("GEOIP_DB",        "/app/data/GeoLite2-City.mmdb")

# Feodo Tracker (public, sans clé)
FEODO_URL        = "https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.json"

# API
JWT_SECRET       = os.getenv("JWT_SECRET", "deceptr-secret-change-me")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_MIN   = 1440

# Pipeline
POLL_INTERVAL    = int(os.getenv("POLL_INTERVAL", "30"))   # secondes entre chaque collecte
LOG_LEVEL        = os.getenv("LOG_LEVEL", "INFO")
