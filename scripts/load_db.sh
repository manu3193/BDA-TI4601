#!/usr/bin/env bash
# Carga db/initialize.sql en el Postgres del curso (opcional).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=ti4601-postgres
"${ROOT}/scripts/up.sh" >/dev/null
for _ in 1 2 3 4 5 6 7 8 9 10; do
  docker exec "${NAME}" pg_isready -U ti4601 >/dev/null 2>&1 && break
  sleep 1
done
docker exec -i "${NAME}" psql -U ti4601 -d ti4601 < "${ROOT}/db/initialize.sql"
echo "SQL cargado."
