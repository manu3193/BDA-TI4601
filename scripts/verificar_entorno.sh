#!/usr/bin/env bash
# Verifica prerrequisitos + smoke test transactions↔Postgres.
# El pipeline corre en Docker (imagen ti4601); no exige python3 en el host.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

ok=0
fail=0
NAME=ti4601-postgres
PORT="${POSTGRES_PORT:-5433}"

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  [OK]  ${name}"
    ok=$((ok + 1))
  else
    echo "  [FAIL] ${name}"
    fail=$((fail + 1))
  fi
}

echo "=== TI-4601 · verificación de entorno ==="
echo

echo "Herramientas host:"
check "docker" docker version
check "git" git --version

echo
echo "Servicio Postgres:"
if ./scripts/up.sh >/tmp/ti4601-up.log 2>&1; then
  :
else
  echo "  [FAIL] up.sh (ver /tmp/ti4601-up.log)"
  tail -n 20 /tmp/ti4601-up.log || true
  fail=$((fail + 1))
fi

if docker ps --format '{{.Names}}' | grep -qx "${NAME}"; then
  echo "  [OK]  contenedor ${NAME} en ejecución"
  ok=$((ok + 1))
  ready=0
  for _ in $(seq 1 30); do
    if docker exec "${NAME}" pg_isready -U ti4601 >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "${ready}" -eq 1 ]]; then
    echo "  [OK]  postgres acepta conexiones (127.0.0.1:${PORT})"
    ok=$((ok + 1))
  else
    echo "  [FAIL] postgres no responde; revise: docker logs ${NAME}"
    fail=$((fail + 1))
  fi
else
  echo "  [FAIL] no se pudo levantar Postgres"
  fail=$((fail + 1))
fi

echo
echo "Imagen de trabajo (Dockerfile):"
if docker image inspect ti4601 >/dev/null 2>&1; then
  echo "  [OK]  imagen ti4601 presente"
  ok=$((ok + 1))
elif ./build_image.sh >/tmp/ti4601-build.log 2>&1; then
  echo "  [OK]  imagen ti4601 construida"
  ok=$((ok + 1))
else
  echo "  [FAIL] no se pudo construir ti4601 (ver /tmp/ti4601-build.log)"
  tail -n 20 /tmp/ti4601-build.log || true
  fail=$((fail + 1))
fi

if [[ "${fail}" -eq 0 ]]; then
  echo
  echo "Smoke test transactions ↔ Postgres (vía Docker):"
  if ./scripts/test_transactions.sh >/tmp/ti4601-tx.log 2>&1; then
    echo "  [OK]  pipeline read→answer contra Postgres"
    ok=$((ok + 1))
    tail -n 12 /tmp/ti4601-tx.log | sed 's/^/         /'
  else
    echo "  [FAIL] test_transactions (ver /tmp/ti4601-tx.log)"
    tail -n 40 /tmp/ti4601-tx.log || true
    fail=$((fail + 1))
  fi
fi

echo
echo "Resultado: ${ok} OK, ${fail} FAIL"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "Entorno listo. Camino oficial: ./build_image.sh && make verify"
