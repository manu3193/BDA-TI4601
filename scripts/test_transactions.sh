#!/usr/bin/env bash
# Prueba end-to-end: Postgres oficial + pipeline transactions.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

chmod +x scripts/*.sh transactions/*.sh build_image.sh run_image.sh

echo "==> Postgres arriba + carga de datos"
./scripts/load_db.sh

echo "==> Imagen de trabajo"
if ! docker image inspect ti4601 >/dev/null 2>&1; then
  ./build_image.sh
fi

run_step() {
  local step="$1"
  echo "==> transactions/${step}"
  docker run --rm \
    --add-host=host.docker.internal:host-gateway \
    -e PGHOST=host.docker.internal \
    -e PGPORT="${POSTGRES_PORT:-5433}" \
    -e PGUSER=ti4601 \
    -e PGPASSWORD=ti4601 \
    -e PGDATABASE=ti4601 \
    -v "${ROOT}":/src \
    -w /src/transactions \
    ti4601 \
    python3 "${step}.py"
}

run_step read
run_step transform
run_step aggregate
run_step join
run_step answer

echo "==> OK — transactions usa Postgres correctamente"
