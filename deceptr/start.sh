#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "DECEPTR v1 - Architecture cible"
echo "Cowrie officiel T-Pot -> DECEPTR Logstash TLS -> Pipeline -> Dashboards"
echo "---------------------------------------------------------------"
echo ""

if ! docker info >/dev/null 2>&1; then
  echo "[ERREUR] Docker n'est pas demarre."
  exit 1
fi

if command -v pwsh >/dev/null 2>&1; then
  pwsh -ExecutionPolicy Bypass -File "$ROOT/scripts/start-architecture.ps1"
else
  echo "[INFO] PowerShell non disponible. Utilise la commande Docker directe:"
  echo "docker compose -f docker-compose.yml -f docker-compose.tpot.yml up -d --build"
  docker compose -f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.tpot.yml" up -d --build
fi

echo ""
echo "[OK] DECEPTR est actif en mode architecture."
echo "Dashboard DECEPTR : http://127.0.0.1:8088/index.html?v=3"
echo "API Docs          : http://127.0.0.1:8000/docs"
echo "Kibana DECEPTR    : http://127.0.0.1:5601"
