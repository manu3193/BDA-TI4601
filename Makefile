# Instituto Tecnológico de Costa Rica — TI-4601
# Orquestación: Docker Compose (sin scripts up/down/build manuales).

.PHONY: help up down down-v build shell verify test-tx lab-concurrency \
	lab1-up lab1-down lab1-down-v lab1-shell reset-pg

COMPOSE := docker compose
ISOLATION ?= READ_COMMITTED
WORKERS ?= 40
RETRIES ?= 8

help:
	@echo "TI-4601 · camino oficial S2:"
	@echo "  make up && make verify"
	@echo ""
	@echo "  make up              Postgres + volumen + initdb"
	@echo "  make verify          Smoke test pipeline ACID"
	@echo "  make test-tx         read→transform→aggregate→join→answer"
	@echo "  make lab-concurrency ISOLATION=READ_COMMITTED|SERIALIZABLE"
	@echo "  make shell           Bash en contenedor app (PG* inyectadas)"
	@echo "  make down / down-v   Apagar (down-v borra volumen → re-seed)"
	@echo ""
	@echo "Lab 1 / P1 (S5+, perfil lab1):"
	@echo "  make lab1-up | lab1-shell | lab1-down | lab1-down-v"
	@echo "Ver docs/fases-postgres-cockroach.md"

up:
	$(COMPOSE) up -d postgres
	@echo "Esperando Postgres healthy…"
	@for i in $$(seq 1 60); do \
	  if $(COMPOSE) exec -T postgres pg_isready -U ti4601 -d ti4601 >/dev/null 2>&1; then \
	    echo "  postgres listo"; exit 0; \
	  fi; \
	  sleep 1; \
	done; \
	echo "Postgres no respondió a tiempo"; exit 1

down:
	$(COMPOSE) down --remove-orphans

down-v:
	$(COMPOSE) down -v --remove-orphans

build:
	$(COMPOSE) build app

shell: up
	$(COMPOSE) run --rm app bash

reset-pg: down-v up
	@echo "Volumen recreado; initdb volvió a cargar CSV."

test-tx: up
	$(COMPOSE) run --rm app python3 transactions/read.py
	$(COMPOSE) run --rm app python3 transactions/transform.py
	$(COMPOSE) run --rm app python3 transactions/aggregate.py
	$(COMPOSE) run --rm app python3 transactions/join.py
	$(COMPOSE) run --rm app python3 transactions/answer.py
	@echo "==> OK — pipeline transactions (ACID + TEMP TABLE)"

verify: up build
	@echo "=== TI-4601 · verificación ==="
	@docker version >/dev/null
	@echo "  [OK]  docker"
	@$(COMPOSE) exec -T postgres pg_isready -U ti4601 -d ti4601 >/dev/null
	@echo "  [OK]  postgres healthy"
	@$(COMPOSE) run --rm app python3 transactions/answer.py | tee /tmp/ti4601-answer.txt
	@grep -q "John" /tmp/ti4601-answer.txt
	@grep -q "Jane" /tmp/ti4601-answer.txt
	@echo "  [OK]  smoke answer (John/Jane)"
	@echo "Entorno listo. Siguiente: make lab-concurrency ISOLATION=READ_COMMITTED"

lab-concurrency: up
	$(COMPOSE) run --rm -e ISOLATION=$(ISOLATION) -e WORKERS=$(WORKERS) -e RETRIES=$(RETRIES) \
		app python3 labs/01-concurrency/stress.py --isolation $(ISOLATION) --workers $(WORKERS) --retries $(RETRIES)

lab1-up:
	$(COMPOSE) --profile lab1 up -d crdb-1 crdb-2 crdb-3
	$(COMPOSE) --profile lab1 up crdb-init

lab1-down:
	$(COMPOSE) --profile lab1 down

lab1-down-v:
	$(COMPOSE) --profile lab1 down -v

lab1-shell:
	$(COMPOSE) --profile lab1 run --rm app-crdb bash
