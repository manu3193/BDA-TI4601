.PHONY: help verify up down load-db build run test-tx

help:
	@echo "TI-4601 · entorno Semana 2:"
	@echo "  make build      Construye imagen ti4601 (Dockerfile)"
	@echo "  make run        Entra a la imagen de trabajo"
	@echo "  make up         Levanta Postgres (imagen oficial)"
	@echo "  make load-db    Carga CSVs de transactions en Postgres"
	@echo "  make test-tx    Prueba end-to-end transactions↔Postgres"
	@echo "  make verify     Verifica entorno + smoke test transactions"
	@echo "  make down       Elimina el contenedor Postgres"

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
