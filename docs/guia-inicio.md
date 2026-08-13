# Guía de inicio

## Camino oficial

```bash
chmod +x *.sh scripts/*.sh transactions/*.sh
./build_image.sh
make verify
```

Éxito: smoke test `answer` (John/Jane) y «Entorno listo».

No corra `transactions/*.py` en el host sin Docker.

## Manual

```bash
./build_image.sh
./scripts/up.sh          # 127.0.0.1:5433
./scripts/load_db.sh
make test-tx
./scripts/down.sh
```

Interactivo:

```bash
./scripts/up.sh && ./scripts/load_db.sh && ./run_image.sh
# dentro: cd transactions && ./read.sh && ./answer.sh
```

Detalle: `transactions/README.md` · fallos: README raíz.
