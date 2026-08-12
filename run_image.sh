#!/bin/bash
# Una acción: entrar a la imagen de trabajo (código montado en /src).
# Habla con Postgres del host en host.docker.internal:5433
docker run --rm -it \
  -v "$(pwd)":/src \
  -w /src \
  --add-host=host.docker.internal:host-gateway \
  -e PGHOST=host.docker.internal \
  -e PGPORT="${POSTGRES_PORT:-5433}" \
  -e PGUSER=ti4601 \
  -e PGPASSWORD=ti4601 \
  -e PGDATABASE=ti4601 \
  ti4601 \
  /bin/bash
