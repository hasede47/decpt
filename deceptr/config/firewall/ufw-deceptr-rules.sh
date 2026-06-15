#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <TPOT_SENSOR_IP> <SOC_ADMIN_IP>" >&2
  exit 1
fi

TPOT_SENSOR_IP="$1"
SOC_ADMIN_IP="$2"

sudo ufw allow from "${TPOT_SENSOR_IP}" to any port 5044 proto tcp comment "DECEPTR Logstash TLS from T-Pot"
sudo ufw allow from "${SOC_ADMIN_IP}" to any port 8000 proto tcp comment "DECEPTR API from SOC"
sudo ufw allow from "${SOC_ADMIN_IP}" to any port 5601 proto tcp comment "DECEPTR Kibana from SOC"
sudo ufw allow from "${SOC_ADMIN_IP}" to any port 9200 proto tcp comment "DECEPTR Elasticsearch from SOC"
sudo ufw status numbered

