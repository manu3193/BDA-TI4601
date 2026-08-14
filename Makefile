# Instituto Tecnológico de Costa Rica — TI-4601
# Interfaz operativa genérica (Compose). Smoke tests = documentados en README, no targets.

.PHONY: help up down down-v build shell test-tx lab-concurrency \
	lab1-up lab1-down lab1-down-v lab1-shell reset-pg

COMPOSE := docker compose
ISOLATION ?= READ_COMMITTED
WORKERS ?= 40
RETRIES ?= 8

help:
	@echo "TI-4601 · entorno"
	@echo "  make up | down | down-v | build | shell | reset-pg"
	@echo "  make test-tx"
	@echo "  make lab-concurrency ISOLATION=READ_COMMITTED|SERIALIZABLE"
	@echo "  Lab 1: make lab1-up | lab1-shell | lab1-down | lab1-down-v"
	@echo ""
	@echo "Smoke test (manual): ver README.md § Verificar el entorno"
	@echo "Docs: labs/README.md · labs/lab0-concurrency/ · labs/lab1-cluster/"

up:
	$(COMPOSE) up -d postgres

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

lab-concurrency: up
	$(COMPOSE) run --rm -e ISOLATION=$(ISOLATION) -e WORKERS=$(WORKERS) -e RETRIES=$(RETRIES) \
		app python3 labs/lab0-concurrency/stress.py --isolation $(ISOLATION) --workers $(WORKERS) --retries $(RETRIES)

lab1-up:
	$(COMPOSE) --profile lab1 up -d crdb-1 crdb-2 crdb-3
	$(COMPOSE) --profile lab1 up crdb-init

lab1-down:
	$(COMPOSE) --profile lab1 down

lab1-down-v:
	$(COMPOSE) --profile lab1 down -v

lab1-shell:
	$(COMPOSE) --profile lab1 run --rm app-crdb bash
