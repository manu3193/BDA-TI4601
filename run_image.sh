#!/bin/bash
# Shell en la imagen de trabajo (misma red Docker que Postgres).
docker run --rm -it \
  --network ti4601 \
  -v "$(pwd)":/src \
  -w /src \
  -e PGHOST=ti4601-postgres \
  -e PGPORT=5432 \
  -e PGUSER=ti4601 \
  -e PGPASSWORD=ti4601 \
  -e PGDATABASE=ti4601 \
  ti4601 \
  /bin/bash
