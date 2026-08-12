#!/usr/bin/env bash
# Baja y elimina el Postgres del curso (una acción).
# Sin volumen nombrado: al borrar el contenedor se pierden los datos (igual que bigdataclass).
set -euo pipefail
NAME=ti4601-postgres
docker rm -f "${NAME}" 2>/dev/null || true
echo "Contenedor ${NAME} eliminado."
