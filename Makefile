.PHONY: help verify up down load-db

help:
	@echo "TI-4601 · entorno Semana 2:"
	@echo "  make verify    Verifica Docker + Postgres + Python"
	@echo "  make up        Levanta Postgres (docker run)"
	@echo "  make down      Elimina el contenedor (datos efímeros)"
	@echo "  make load-db   Carga db/initialize.sql"
	@echo "  cd transactions && ./read.sh   # ejemplo Python"

verify:
	chmod +x scripts/*.sh transactions/*.sh
	./scripts/verificar_entorno.sh

up:
	chmod +x scripts/up.sh
	./scripts/up.sh

down:
	chmod +x scripts/down.sh
	./scripts/down.sh

load-db:
	chmod +x scripts/load_db.sh
	./scripts/load_db.sh
