.PHONY: help verify up down load-db build run test-tx

help:
	@echo "TI-4601 · camino oficial: ./build_image.sh && make verify"
	@echo "  make build      Construye imagen ti4601"
	@echo "  make verify     Entorno + smoke test (Docker)"
	@echo "  make test-tx    Solo pipeline transactions↔Postgres"
	@echo "  make up         Levanta Postgres (127.0.0.1:5433)"
	@echo "  make load-db    Carga CSVs en Postgres"
	@echo "  make run        Shell en imagen ti4601"
	@echo "  make down       Elimina contenedor Postgres"
	@echo "No use transactions/*.sh en el host; use make test-tx o make run."

build:
	chmod +x build_image.sh
	./build_image.sh

run: build
	chmod +x run_image.sh
	./run_image.sh

up:
	chmod +x scripts/up.sh
	./scripts/up.sh

down:
	chmod +x scripts/down.sh
	./scripts/down.sh

load-db:
	chmod +x scripts/load_db.sh
	./scripts/load_db.sh

test-tx:
	chmod +x scripts/test_transactions.sh
	./scripts/test_transactions.sh

verify:
	chmod +x scripts/*.sh transactions/*.sh build_image.sh run_image.sh
	./scripts/verificar_entorno.sh
