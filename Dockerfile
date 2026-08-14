# Imagen de trabajo del estudiante (cliente Python + psycopg).
# El motor de datos lo define docker-compose.yml (postgres | cockroach).
FROM python:3.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       bash \
       postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY requirements.txt /src/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /src

CMD ["/bin/bash"]
