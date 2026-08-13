#!/usr/bin/env bash
# Baja y elimina el Postgres del curso (una acción).
set -euo pipefail
NAME=ti4601-postgres
NET=ti4601
docker rm -f "${NAME}" 2>/dev/null || true
docker network rm "${NET}" >/dev/null 2>&1 || true
echo "Contenedor ${NAME} eliminado."
