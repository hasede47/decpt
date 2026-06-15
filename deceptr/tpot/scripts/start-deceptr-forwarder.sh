#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${TPOT_DIR}/.env" ]; then
  cp "${TPOT_DIR}/.env.example" "${TPOT_DIR}/.env"
  echo "Created ${TPOT_DIR}/.env. Edit DECEPTR_LOGSTASH_HOST, then rerun." >&2
  exit 1
fi

if [ ! -f "${TPOT_DIR}/certs/ca.crt" ]; then
  echo "Missing ${TPOT_DIR}/certs/ca.crt" >&2
  echo "Copy it from DECEPTR: elk/certs/ca.crt" >&2
  exit 1
fi

docker compose \
  --env-file "${TPOT_DIR}/.env" \
  -f "${TPOT_DIR}/docker-compose.deceptr-forwarder.yml" \
  up -d

docker compose \
  --env-file "${TPOT_DIR}/.env" \
  -f "${TPOT_DIR}/docker-compose.deceptr-forwarder.yml" \
  logs --tail=80 deceptr-tpot-filebeat

