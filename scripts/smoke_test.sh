#!/usr/bin/env bash
# Post-deploy smoke test. Usage: bash scripts/smoke_test.sh [base_url]
set -euo pipefail
BASE_URL="${1:-http://localhost:8000}"

echo "Waiting for ${BASE_URL}/health ..."
for i in $(seq 1 30); do
  if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Service did not become healthy in time"
    exit 1
  fi
  sleep 2
done

echo "health : $(curl -fsS "${BASE_URL}/health")"
echo "version: $(curl -fsS "${BASE_URL}/version")"

curl -fsS -X POST -d "name=CI&message=smoke+test" -o /dev/null "${BASE_URL}/sign"
curl -fsS "${BASE_URL}/" | grep -q "smoke test"
echo "write/read through the database: OK"

curl -fsS "${BASE_URL}/metrics" | grep -q "guestbook_requests_total"
echo "metrics endpoint: OK"
echo "Smoke test passed"
