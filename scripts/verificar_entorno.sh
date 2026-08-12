#!/usr/bin/env bash
# Verifica prerrequisitos Semana 2. Un script = una acción.
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

echo "=== TI-4601 · verificación de entorno (Semana 2) ==="
echo

echo "Herramientas host:"
check "docker" docker version
check "python3" python3 --version
check "curl" curl --version
check "git" git --version

echo
echo "Servicio Postgres:"
./scripts/up.sh >/tmp/ti4601-up.log 2>&1 || true
if docker ps --format '{{.Names}}' | grep -qx "${NAME}"; then
  echo "  [OK]  contenedor ${NAME} en ejecución"
  ok=$((ok + 1))
  ready=0
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    if docker exec "${NAME}" pg_isready -U ti4601 >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "${ready}" -eq 1 ]]; then
    echo "  [OK]  postgres acepta conexiones (host port ${PORT})"
    ok=$((ok + 1))
  else
    echo "  [FAIL] postgres no responde; revise: docker logs ${NAME}"
    fail=$((fail + 1))
  fi
else
  echo "  [FAIL] no se pudo levantar Postgres (ver /tmp/ti4601-up.log)"
  fail=$((fail + 1))
fi

echo
echo "Ejemplo transactions (Python puro):"
if python3 -c "import csv; print('ok')" >/dev/null 2>&1; then
  echo "  [OK]  python3 + csv (stdlib)"
  ok=$((ok + 1))
else
  echo "  [FAIL] python3"
  fail=$((fail + 1))
fi

echo
echo "Resultado: ${ok} OK, ${fail} FAIL"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "Entorno listo. Pruebe: cd transactions && ./read.sh"
