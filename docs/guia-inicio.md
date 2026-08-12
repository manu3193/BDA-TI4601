# Guía de inicio — Semana 2

## Camino corto (recomendado)

```bash
chmod +x *.sh scripts/*.sh transactions/*.sh
./build_image.sh
make verify
```

Éxito: `7 OK, 0 FAIL` y filas de `answer` (John/Jane).

## Camino manual

```bash
./build_image.sh
./scripts/up.sh
./scripts/load_db.sh
make test-tx
./scripts/down.sh
```

O con shell interactivo:

```bash
./scripts/up.sh && ./scripts/load_db.sh && ./run_image.sh
# dentro: cd transactions && ./read.sh && ./answer.sh
```

Detalle del ejemplo: `transactions/README.md`.
