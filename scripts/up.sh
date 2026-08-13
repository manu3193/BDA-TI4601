#!/usr/bin/env bash
# Levanta Postgres (una acción). Estilo bigdataclass/db/run_image.sh
# - Red Docker ti4601: otros contenedores usan PGHOST=ti4601-postgres
# - Puerto en loopback del host: 127.0.0.1:5433 (psql local)
set -euo pipefail

NAME=ti4601-postgres
NET=ti4601
PORT="${POSTGRES_PORT:-5433}"

docker network create "${NET}" >/dev/null 2>&1 || true

if docker ps -a --format '{{.Names}}' | grep -qx "${NAME}"; then
  mapped="$(docker port "${NAME}" 5432 2>/dev/null | head -1 || true)"
  if [[ -n "${mapped}" && "${mapped}" != *":${PORT}" ]]; then
    echo "[WARN] ${NAME} ya existe con mapeo ${mapped}, no :${PORT}."
    echo "       Ejecute ./scripts/down.sh y vuelva a correr ./scripts/up.sh"
    exit 1
  fi
  docker network connect "${NET}" "${NAME}" >/dev/null 2>&1 || true
  docker start "${NAME}" >/dev/null
  echo "Contenedor ${NAME} ya existía — arrancado."
else
  docker run --name "${NAME}" \
    --network "${NET}" \
    -e POSTGRES_USER=ti4601 \
    -e POSTGRES_PASSWORD=ti4601 \
    -e POSTGRES_DB=ti4601 \
    -p "127.0.0.1:${PORT}:5432" \
    -d postgres:16
  echo "Postgres nuevo: host 127.0.0.1:${PORT} · red Docker ${NET} (hostname ${NAME})."
fi
echo "Bajar: ./scripts/down.sh"
