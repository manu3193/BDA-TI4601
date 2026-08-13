# Guía corta — Semana 2

1. `make up` — levanta Postgres con volumen; el schema/CSV se cargan solos la primera vez.
2. `make verify` — comprueba el pipeline.
3. `make lab-concurrency ISOLATION=READ_COMMITTED` y luego `SERIALIZABLE`.
4. Leer `docs/fases-postgres-cockroach.md` antes de tocar el Proyecto 1.

Reset de datos: `make down-v && make up`.
