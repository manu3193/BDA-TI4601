# Instituto Tecnológico de Costa Rica
## TI-4601 Bases de Datos Avanzados — entorno de estudiantes

Entrega **Semana 2**: Postgres efímero con `docker run` (estilo `bigdataclass/db`) y
ejemplo `transactions/` en **Python puro** (misma progresión que Big Data, sin Spark).

Labs/clúster llegarán en actualizaciones posteriores del repo.

Copyright: Instituto Tecnológico de Costa Rica.

---

## Arranque

```bash
git clone <url> ti4601 && cd ti4601
chmod +x scripts/*.sh transactions/*.sh
make verify
```

```bash
./scripts/up.sh          # docker run postgres:16 en :5433
./scripts/down.sh        # docker rm -f (sin volumen: datos se pierden)
cd transactions && ./read.sh && ./answer.sh
```

**No es Lab 1.** Tarea 1 (Abadi) va por TEC Digital.

## Por qué no hay `docker-compose` con volumes

Como en Big Data: un `docker run` basta. No hace falta volumen nombrado, healthcheck,
`mem_limit` ni init de extensiones para verificar entorno en Semana 2. Al hacer
`./scripts/down.sh` el contenedor se elimina y los datos también (igual que
`docker rm bigdata-db`).

## Qué hay

| Ruta | Rol |
| --- | --- |
| `scripts/up.sh` / `down.sh` | Subir / borrar Postgres |
| `scripts/verificar_entorno.sh` | `make verify` |
| `scripts/load_db.sh` + `db/initialize.sql` | Carga SQL opcional |
| `transactions/` | read → transform → aggregate → join → answer (Python) |

## Imagen

`postgres:16` · puerto host **5433** · user/pass/db `ti4601`
