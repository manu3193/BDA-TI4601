# Instituto Tecnológico de Costa Rica — TI-4601
# Interfaz operativa genérica (Compose). Smoke tests = documentados en README, no targets.

.PHONY: help up down down-v build shell test-tx lab-concurrency \
	lab1-up lab1-down lab1-down-v lab1-shell lab1-status lab1-check reset-pg \
	lab2-up lab2-down \
	lab3-up lab3-down lab3-down-v lab3-status lab3-shell lab3-app lab3-check \
	lab4-up lab4-down lab4-down-v lab4-ejecutar

COMPOSE := docker compose
NODE ?= mongo-1
ISOLATION ?= READ_COMMITTED
WORKERS ?= 40
RETRIES ?= 8

help:
	@echo "TI-4601 · entorno"
	@echo "  make up | down | down-v | build | shell | reset-pg"
	@echo "  make test-tx"
	@echo "  make lab-concurrency ISOLATION=READ_COMMITTED|SERIALIZABLE"
	@echo "  Lab 1: make lab1-up | lab1-status | lab1-shell | lab1-check"
	@echo "         make lab1-down | lab1-down-v"
	@echo "  Configuración, medición y chaos: seguir labs/lab1-cluster/README.md"
	@echo "  Lab 2 (S9): make lab2-up | lab2-down · labs/lab2-one-size/README.md"
	@echo "  Lab 3 (S10): make lab3-up | lab3-status [NODE=mongo-2] | lab3-shell [NODE=mongo-2] | lab3-app | lab3-check"
	@echo "               make lab3-down | lab3-down-v · labs/lab3-mongo-replicas/README.md"
	@echo "  Lab 4 (S13): make lab4-up | lab4-ejecutar | lab4-down | lab4-down-v"
	@echo "               notebook http://127.0.0.1:8888/lab?token=ti4601 · labs/lab4-neo4j/README.md"
	@echo ""
	@echo "Smoke test (manual): ver README.md § Verificar el entorno"
	@echo "Docs: labs/README.md · labs/lab0-concurrency/ · labs/lab1-cluster/ · labs/lab2-one-size/ · labs/lab3-mongo-replicas/"

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

lab2-up: up
	$(COMPOSE) --profile lab2 up -d valkey

lab2-down:
	$(COMPOSE) --profile lab2 stop valkey

lab1-up: build
	$(COMPOSE) --profile lab1 up -d crdb-1 crdb-2 crdb-3
	$(COMPOSE) --profile lab1 up crdb-init

lab1-down:
	$(COMPOSE) --profile lab1 down

lab1-down-v:
	$(COMPOSE) --profile lab1 down -v

lab1-shell:
	$(COMPOSE) --profile lab1 run --rm app-crdb bash

lab1-status:
	$(COMPOSE) --profile lab1 ps
	docker exec ti4601-crdb-1 cockroach node status --insecure

lab1-check:
	$(COMPOSE) --profile lab1 run --rm --no-deps app-crdb \
		python3 labs/lab1-cluster/verify_cluster.py

# --- Laboratorio 3: MongoDB (solo infraestructura; NO inicializa el conjunto) ---

lab3-up: build
	$(COMPOSE) --profile lab3 up -d mongo-1 mongo-2 mongo-3

lab3-status:
	$(COMPOSE) --profile lab3 ps
	-docker exec ti4601-$(NODE) mongosh --quiet --eval 'try { rs.status().members.forEach(function (m) { print(m.name + "  " + m.stateStr + "  health=" + m.health) }) } catch (e) { print("conjunto no inicializado o nodo sin respuesta: " + (e.codeName || e.message)) }'

lab3-shell:
	docker exec -it ti4601-$(NODE) mongosh

lab3-app:
	$(COMPOSE) --profile lab3 run --rm --no-deps app-mongo bash

lab3-check:
	$(COMPOSE) --profile lab3 run --rm --no-deps app-mongo \
		python3 labs/lab3-mongo-replicas/verify_replica.py

lab3-down:
	$(COMPOSE) --profile lab3 down

lab3-down-v:
	$(COMPOSE) --profile lab3 down -v

# --- Laboratorio 4: Neo4j de un nodo + notebook (actas municipales) ---

lab4-up:
	$(COMPOSE) --profile lab4 up -d --build neo4j lab4-notebook

lab4-ejecutar:
	$(COMPOSE) --profile lab4 exec -T lab4-notebook \
		jupyter nbconvert --execute --to notebook \
		--ExecutePreprocessor.timeout=900 \
		--output Lab4.ejecutado --output-dir /tmp \
		labs/lab4-neo4j/Lab4.ipynb

lab4-down:
	$(COMPOSE) --profile lab4 down

lab4-down-v:
	$(COMPOSE) --profile lab4 down -v
