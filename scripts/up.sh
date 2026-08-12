#!/usr/bin/env bash
# Levanta Postgres (una acción). Estilo bigdataclass/db/run_image.sh
set -euo pipefail

NAME=ti4601-postgres
PORT="${POSTGRES_PORT:-5433}"

if docker ps -a --format '{{.Names}}' | grep -qx "${NAME}"; then
  docker start "${NAME}" >/dev/null
  echo "Contenedor ${NAME} ya existía — arrancado. Puerto ${PORT}."
else
  docker run --name "${NAME}" \
    -e POSTGRES_USER=ti4601 \
    -e POSTGRES_PASSWORD=ti4601 \
    -e POSTGRES_DB=ti4601 \
    -p "${PORT}:5432" \
    -d postgres:16
  echo "Postgres nuevo en localhost:${PORT} (user/pass/db: ti4601)."
fi
echo "Bajar: ./scripts/down.sh"
