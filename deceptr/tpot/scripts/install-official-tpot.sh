#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
DECEPTR - Official T-Pot installer helper

Run this script on a clean Linux VM/server dedicated to T-Pot, not inside the
DECEPTR analysis server.

Recommended topology:
  Internet -> Firewall/NAT -> T-Pot sensor VM -> DECEPTR Logstash TLS 5044

The official T-Pot installer changes host services and ports, so a clean VM is
the safest deployment model.
MSG

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it first, then rerun this script." >&2
  exit 1
fi

cd "${HOME}"
if [ ! -d tpotce ]; then
  git clone https://github.com/telekom-security/tpotce
fi

cd tpotce
echo "Starting official T-Pot installer..."
echo "Choose the sensor/standard edition that matches your lab resources."
./install.sh

