# Laboratorio 1 — Clúster CockroachDB, localidad y quórum

**Semana:** 5 · **Valor:** 2,5 % del curso · **Motor:** CockroachDB ×3  
**Prerrequisito:** lectura y ronda oral de Raft **antes** de ejecutar la falla.  
**Tiempo estimado:** 90–120 min desde un clúster nuevo; la clase inicia el recorrido
y el estudiante completa la evidencia siguiendo esta guía.  
Índice: [`../README.md`](../README.md).

Este laboratorio es el **punto de entrada al Proyecto 1**: la misma configuración de
Compose, el mismo cliente Python, las variables `PG*`, las regiones y las técnicas de
recolección de evidencia se reutilizan de S5 a S8. El laboratorio usa un dominio de
comercio mínimo; el P1 exige sustituirlo por el dominio del equipo.

---

## 1. Qué demostrará

Al terminar, podrá:

1. explicar la configuración de tres servidores con localidades distintas;
2. traducir los conceptos de fragmentación y asignación de Özsu a
   `REGIONAL BY ROW` y `GLOBAL`;
3. localizar filas y réplicas con `SHOW REGIONS` y `SHOW RANGES`;
4. medir p50 y p99 de lecturas y escrituras locales y remotas;
5. detener un nodo y relacionar continuidad, RTO y RPO con una mayoría Raft de dos
   nodos de un total de tres;
6. predecir por qué con dos nodos caídos queda un proceso activo, pero **no hay quórum**,
   y contrastarlo con la demostración del escenario B;
7. reutilizar el método en E2–E4 del Proyecto 1.

**No se mide hoy:** semi-join, bytes transferidos por operaciones de join, 2PC ni
partición de red. Esos temas pertenecen a semanas posteriores.

---

## 2. Modelo mental: de S4 a Cockroach

El ejemplo tiene tres sitios lógicos:

| Servicio | Localidad | Puerto en el host | Función |
| --- | --- | --- | --- |
| `crdb-1` | `region=cr-sj,zone=a` | SQL `26257`, UI `8080` | nodo de entrada (`gateway`) inicial |
| `crdb-2` | `region=cr-limon,zone=a` | no publicado | réplica; región hogar Limón |
| `crdb-3` | `region=us-east,zone=a` | no publicado | réplica; región hogar EE. UU. |

Compose los inicia con:

```text
cockroach start --insecure
  --advertise-addr=<servicio>
  --join=crdb-1,crdb-2,crdb-3
  --locality=region=<región>,zone=a
```

- `pedido LOCALITY REGIONAL BY ROW AS region` aproxima la **fragmentación horizontal
  primaria**: cada fila tiene una región hogar.
- `catalogo_producto LOCALITY GLOBAL` aproxima el catálogo pequeño que se quiere leer
  desde todas las regiones.
- Cada rango sigue teniendo réplicas Raft. **Una réplica Raft no es la réplica
  selectiva de Özsu.**

### Límite de “residencia” en este laboratorio

`REGIONAL BY ROW` fija afinidad y colocación del titular del lease (`leaseholder`),
pero no promete que
todas las copias físicas permanezcan en esa región. La evidencia de este laboratorio
demuestra la **región hogar y la localidad configurada**, no el cumplimiento legal de
residencia estricta. En el P1 debe declarar esta limitación; no puede afirmar que
“los datos de identificación personal (PII) nunca salen de la región”
basándose solo en este Compose.

Hay un segundo límite más concreto: una configuración RBR de producción requiere
normalmente **varios nodos por región** para colocar su conjunto de votantes y
réplicas no votantes. Este clúster
didáctico tiene uno por región, así que sus rangos RBR pueden aparecer
como **subreplicados (`under-replicated`)**. Por eso:

- `pedido` sirve para materializar e inspeccionar RBR;
- `ti4601_raft.public.raft_probe` es una tabla sin localidad multirregional,
  configurada con exactamente tres réplicas votantes, una por nodo; se usa en los
  escenarios A y B para demostrar una mayoría de dos nodos de un total de tres.

No atribuya la disponibilidad de `raft_probe` a `REGIONAL BY ROW`: corresponden a dos
fenómenos distintos que se observan en el mismo clúster.

Las tres “regiones” se ejecutan, además, en **una sola computadora**: son localidades
lógicas, no una WAN real.

---

## 3. Qué se entrega y qué debe hacer

El repositorio entrega infraestructura y herramientas de observación; **no** entrega
un botón que configure y ejecute todo el laboratorio.

| Ya se proporciona | Trabajo del estudiante |
| --- | --- |
| Compose, imagen cliente y tres servicios CockroachDB | leer las opciones `--join` y `--locality`; levantar y verificar los nodos |
| `schema.sql`, `seed.sql` y `raft_probe.sql` como ejemplos del laboratorio | configurar regiones y aplicar cada archivo después de revisar su contenido |
| sondas `measure_latency.py` y `chaos_probe.py` | invocarlas, coordinar la falla, guardar evidencia y explicar los resultados |
| `verify_cluster.py` | corregir la configuración hasta superar cada comprobación |
| guía y consultas de inspección | producir su propia bitácora y cálculos |

El Makefile solo conserva atajos de **infraestructura**: construir, levantar, abrir
una terminal, consultar el estado, verificar y apagar. No existen objetivos de Make
que resuelvan la configuración, la medición o los escenarios de falla.

### Frontera con el Proyecto 1

En el P1 puede reutilizar Compose, las variables `PG*`, el método de medición y las
consultas de diagnóstico. Debe crear por cuenta propia:

- esquema y seed de su dominio;
- script reproducible de configuración;
- operaciones y programa de prueba de rendimiento;
- orquestación de la falla y producción de evidencia;
- justificación de RBR/GLOBAL y análisis RTO/RPO.

Entregar los archivos de este laboratorio renombrados o con cambios cosméticos
**no cumple los requisitos del P1**.

### Cómo usar esta guía

Trabaje en orden. Cada paso termina con un **resultado esperado** y un
**punto de control**. Si el resultado no coincide, no continúe: use la pista indicada
o la sección 11.

Los bloques llevan uno de estos contextos:

- **HOST:** terminal en la raíz de `repo-estudiantes/`;
- **APP:** shell del contenedor `app-crdb`, abierto con `make lab1-shell`;
- **PSQL:** prompt SQL abierto desde APP con `psql -X -v ON_ERROR_STOP=1`.

No ejecute comandos HOST dentro de `psql`, ni comandos que empiezan con `\` en Bash.

### Ruta completa y evidencia

| Paso | Trabajo | Puede avanzar cuando… | Evidencia |
| --- | --- | --- | --- |
| 0 | preparar host y licencia | Compose responde y existe `.env` | — |
| 1 | leer Compose y levantar | aparecen 3 nodos y localidades activos | `cluster-start.txt`, `node-status-initial.txt` |
| 2 | entrar por `app-crdb` | SQL responde y muestra 3 localidades | bitácora |
| 3 | configurar regiones | `SHOW REGIONS` lista 3 | bitácora; se consolida en paso 8 |
| 4 | aplicar esquema | una tabla es GLOBAL y otra RBR | bitácora; se consolida en paso 8 |
| 5 | cargar seed | hay una fila por región | bitácora; se consolida en paso 8 |
| 6 | preparar `raft_probe` | el rango muestra 3 votantes | bitácora; se consolida en paso 8 |
| 7 | verificar | `lab1-check` termina `6/6` | `config-check.txt` |
| 8 | consolidar inspección | el archivo contiene las 6 consultas | `cluster-inspect.txt` |
| 9 | medir | hay 200 muestras y 4 resúmenes | `latency*.{txt,csv}` |
| 10 | preparar el escenario A | lease en el nodo que se detendrá | `chaos-a-before.txt` |
| 11 | iniciar la sonda | aparecen writes sanos de baseline | `chaos-a.{txt,csv}` |
| 12 | provocar la falla | sonda observa recuperación con 2/3 | `chaos-a.{txt,csv}` |
| 13 | comprobar RTO/RPO | cálculo y commit previo verificados | `chaos-a-rpo.txt` |

Marque en su bitácora cada paso como `OK` antes de pasar al siguiente.
Use `evidence/comandos.md` para anotar el comando, el resultado y una explicación breve de
cada punto de control. No incluya la licencia.

**Si empieza desde cero:** siga los pasos 0–13.  
**Si reanuda un intento anterior:** ejecute `make lab1-status` y
`make lab1-check`; continúe desde el primer `[FAIL]`. No use `lab1-down-v` para
“probar suerte”: borra el estado que debe aprender a diagnosticar.

---

## 4. Preparar y levantar los servidores

### Paso 0 — requisitos

- Docker Engine + Compose v2 (`docker compose version`).
- Puertos `26257` y `8080` libres.
- Recomendado: 4 CPU, 4 GiB RAM disponibles y 5 GiB de disco.
- Ejecutar todo desde la raíz de `repo-estudiantes/`.

```bash
cd repo-estudiantes
test -f .env || cp .env.example .env
docker compose version
make build
mkdir -p evidence
test -f evidence/comandos.md \
  || printf '# Bitácora Laboratorio 1\n\n' > evidence/comandos.md
```

**No vuelva a copiar `.env.example` si ya recibió la licencia:** reemplazaría su
`.env`. Nunca pegue la licencia en capturas, bitácoras ni salidas de terminal.

### Paso 1 — interpretar Compose antes de ejecutarlo

Abra `docker-compose.yml` y complete en su bitácora:

1. nombre de los tres servicios;
2. `--advertise-addr` de cada uno;
3. lista común de `--join`;
4. región y zona de cada `--locality`;
5. volumen persistente de cada nodo.

Use esta plantilla antes de mirar la tabla de la sección 2:

| Servicio | `advertise-addr` | miembros de `join` | `region,zone` | volumen |
| --- | --- | --- | --- | --- |
| `crdb-1` |  |  |  |  |
| `crdb-2` |  |  |  |  |
| `crdb-3` |  |  |  |  |

Luego levante el clúster:

**HOST**

```bash
date --iso-8601=seconds | tee evidence/cluster-start.txt
make lab1-up
make lab1-status | tee evidence/node-status-initial.txt
```

`lab1-up` solo construye el cliente, inicia los tres procesos, ejecuta
`cockroach init` si hace falta y crea la base vacía `ti4601`. **No configura regiones
ni tablas.**

Deben aparecer tres nodos. Si falta uno, espere 10–20 segundos y repita
`make lab1-status`; no borre volúmenes ante el primer intento.

**Resultado esperado:**

- servicios `ti4601-crdb-1`, `ti4601-crdb-2` y `ti4601-crdb-3` en ejecución;
- tres filas en `cockroach node status`;
- columna `is_live` en `true`;
- localidades `region=cr-sj`, `region=cr-limon` y `region=us-east`.

Si no obtiene las cuatro condiciones, deténgase aquí.

Un clúster nuevo de CockroachDB `v24.3.0` tiene siete días de gracia para SQL
multi-región. Si el docente ya entregó una licencia, guárdela en `.env` en la raíz
del repositorio; Compose interpola el valor y lo pasa a `app-crdb`. Aplíquela ahora
sin imprimirla:

```bash
docker compose --profile lab1 run --rm --no-deps app-crdb \
  python3 labs/lab1-cluster/install_license.py
```

**Resultado esperado:** `Licencia instalada` o, durante la gracia inicial,
`COCKROACH_LICENSE está vacía`. Un error de conexión significa que el clúster aún no
está listo; no significa que deba borrar datos.

### Punto de control del paso 1

Explique antes de continuar:

- por qué los tres `--join` no significan que ya exista una base multi-región;
- qué parte de `--locality` es solo una etiqueta lógica;
- qué perdería si elimina los volúmenes.

---

## 5. Configurar la base paso a paso

### Paso 2 — entrar al cliente SQL

**HOST**

```bash
make lab1-shell
```

Cuando aparezca el indicador del contenedor, estará en el contexto **APP**:

```bash
pwd
psql -X -v ON_ERROR_STOP=1
```

`pwd` debe mostrar `/src`; por eso las rutas `labs/...` funcionan dentro del
contenedor. Cuando aparezca `ti4601=>`, estará en el contexto **PSQL**. Ejecute
`\conninfo` si quiere comprobar usuario, base y servidor. Luego consulte las
localities:

```sql
SELECT node_id, locality, is_live
FROM crdb_internal.gossip_nodes
ORDER BY node_id;
```

**Resultado esperado:** tres filas vivas que contienen `cr-sj`, `cr-limon` y
`us-east`. No continúe si falta una.

### Paso 3 — convertir la base en multi-región

En **PSQL**, ejecute **una sentencia a la vez** y lea su respuesta:

```sql
ALTER DATABASE ti4601 PRIMARY REGION "cr-sj";
ALTER DATABASE ti4601 ADD REGION "cr-limon";
ALTER DATABASE ti4601 ADD REGION "us-east";
SHOW REGIONS FROM DATABASE ti4601;
SELECT gateway_region();
```

**Resultado esperado:** tres filas; `cr-sj` marcada como primaria y las otras dos
como regiones de la base. `gateway_region()` debe devolver la región del nodo que
atendió la conexión.

En la bitácora responda:

1. ¿Por qué se define primero una región primaria?
2. ¿Qué comando prueba la configuración resultante?
3. ¿Agregar una región crea latencia WAN real?

Si una sentencia indica que la región ya existe, no la repita a ciegas: use
`SHOW REGIONS` y determine qué parte del trabajo estaba hecha.

**Punto de control:** guarde en la bitácora el resultado de `SHOW REGIONS` y escriba
`Paso 3: OK`.

### Paso 4 — aplicar y leer el esquema del ejemplo

Antes de ejecutarlo, abra [`schema.sql`](schema.sql) e identifique:

- la tabla `GLOBAL`;
- la tabla `REGIONAL BY ROW`;
- la columna que determina la región hogar;
- por qué esa columna forma parte de la clave primaria.

Desde **PSQL**:

```sql
\i labs/lab1-cluster/schema.sql
SHOW CREATE TABLE catalogo_producto;
SHOW CREATE TABLE pedido;
```

Copie a la bitácora únicamente las líneas `LOCALITY` que Cockroach generó y explique
la diferencia. No use estas tablas como diseño del P1.

**Resultado esperado:** `catalogo_producto` termina en `LOCALITY GLOBAL` y `pedido`
en `LOCALITY REGIONAL BY ROW AS region`. Si falla el tipo
`crdb_internal_region`, vuelva al Paso 3.

### Paso 5 — cargar datos mínimos

Revise [`seed.sql`](seed.sql) y prediga cuántas filas habrá por región. Aplíquelo:

```sql
\i labs/lab1-cluster/seed.sql
SELECT region, count(*)
FROM pedido
GROUP BY region
ORDER BY region;
```

`UPSERT` actualiza las filas existentes del catálogo y `ON CONFLICT DO NOTHING` evita
que volver a ejecutar el archivo de datos iniciales reinicie la versión de las filas
usadas en la medición. Para el P1 deberá diseñar un
generador o seed propio y justificar su volumen.

**Resultado esperado:** tres grupos (`cr-sj`, `cr-limon`, `us-east`) con una fila
cada uno. Si falta alguno, no edite IDs a mano: revise el error de `seed.sql`.

### Paso 6 — preparar la tabla de control Raft

Lea [`raft_probe.sql`](raft_probe.sql). Esta tabla no representa un dominio; existe
solo para observar una réplica votante en cada nodo.

```sql
\i labs/lab1-cluster/raft_probe.sql
SELECT range_id, lease_holder, voting_replicas, replica_localities
FROM [SHOW RANGES FROM TABLE
      ti4601_raft.public.raft_probe WITH DETAILS];
```

Espere cinco segundos y repita la consulta hasta que `voting_replicas` contenga tres
IDs. Espere hasta dos minutos. Si no observa tres votantes, **no ejecute el escenario
de falla** y revise los nodos con `make lab1-status`.

**Resultado esperado:** al menos una fila de rango y un arreglo de tres IDs, por
ejemplo `{1,2,3}`. El orden y los identificadores concretos pueden variar.

Salga de `psql` y del contenedor:

```text
\q
exit
```

### Paso 7 — usar el verificador como retroalimentación

De regreso en **HOST**:

```bash
set -o pipefail
make lab1-check | tee evidence/config-check.txt
```

El verificador es de solo lectura: no crea regiones, tablas ni filas. Si aparece
`[FAIL]`, corrija el primer fallo mediante los pasos anteriores y vuelva a ejecutar.
La meta es `6/6`.

**Resultado esperado:** seis líneas `[ OK ]`, un resumen `6/6` y un código de salida cero.
`lab1-check` no reemplaza `cluster-inspect.txt`: solo indica si puede avanzar.

```text
[ OK ] tres nodos/localities vivos
...
[ OK ] raft_probe tiene tres votantes

Resultado: 6/6 verificaciones.
```

### Paso 8 — producir evidencia de inspección

Desde **HOST**, vuelva a **PSQL**:

```bash
make lab1-shell
psql -X -v ON_ERROR_STOP=1
```

Redirija la salida de las seis consultas:

```sql
\o evidence/cluster-inspect.txt
SHOW REGIONS FROM DATABASE ti4601;
SHOW CREATE TABLE pedido;
SELECT region, count(*) FROM pedido GROUP BY region ORDER BY region;
SHOW ZONE CONFIGURATION FOR TABLE pedido;
SHOW RANGES FROM TABLE pedido WITH DETAILS;
SELECT range_id, lease_holder, voting_replicas, replica_localities
FROM [SHOW RANGES FROM TABLE
      ti4601_raft.public.raft_probe WITH DETAILS];
\o
```

El directorio `/src/evidence` del contenedor corresponde al directorio `evidence/`
que se ve desde el contexto HOST, porque Compose monta la raíz del repositorio en
`/src`.

Confirme que `\o` sin ruta devolvió la salida a la pantalla; luego salga:

```text
\q
exit
```

En **HOST**, compruebe que el archivo no está vacío:

```bash
test -s evidence/cluster-inspect.txt \
  && echo "Paso 8: OK" \
  || echo "Paso 8: FALTA EVIDENCIA"
```

Abrir <http://127.0.0.1:8080> sirve para explorar; no sustituye este archivo.

---

## 6. Medir latencia

### Paso 9 — producir las muestras

La sonda provista ejecuta cuatro casos desde un nodo de entrada fijo (`crdb-1`):

| Operación | Fila hogar | Interpretación |
| --- | --- | --- |
| lectura local | `cr-sj` | nodo de entrada y fila en la misma región lógica |
| lectura remota | `cr-limon` | nodo de entrada en SJ, fila hogar en Limón |
| escritura local | `cr-sj` | commit sobre fila hogar SJ |
| escritura remota | `cr-limon` | commit iniciado en SJ sobre fila hogar Limón |

Antes de ejecutarla, abra `measure_latency.py` y localice:

1. los cuatro casos;
2. la separación entre warm-up y muestras;
3. el reloj usado para cada observación;
4. el cálculo de p50 y p99;
5. las columnas del CSV.

Ejecute directamente la herramienta, no un target:

**HOST**

```bash
set -o pipefail
date --iso-8601=seconds | tee evidence/latency-start.txt
docker compose --profile lab1 run --rm --no-deps app-crdb \
  python3 labs/lab1-cluster/measure_latency.py \
    --runs 50 --warmup 5 --csv evidence/latency.csv \
  | tee evidence/latency-summary.txt
```

Compruebe que el CSV contiene 200 muestras y que cada caso tiene `n=50`. El p99 usa
*nearest rank*; no entregue solamente el promedio.

```bash
wc -l evidence/latency.csv
```

**Resultado esperado:** `201` líneas: una cabecera y 200 observaciones. La salida
resumen debe contener cuatro filas (`read/write` × `local/remote`) con p50 y p99.
Si hay menos, no complete valores manualmente: conserve el error y repita tras
corregir la causa.

Ejemplo de formato —sus números serán distintos—:

```text
operation locality home_region  n  p50_ms  p99_ms
read      local    cr-sj        50   ...      ...
read      remote   cr-limon     50   ...      ...
write     local    cr-sj        50   ...      ...
write     remote   cr-limon     50   ...      ...
```

### Interpretación obligatoria

Docker no añade distancia física: local y remoto pueden producir una razón cercana a 1 o
invertirse por ruido. Reporte lo medido y declare:

1. que las regiones son lógicas;
2. que la máquina, los recursos disponibles y el número de ejecuciones se
   mantuvieron constantes;
3. que inferir el costo WAN requeriría latencia controlada, ausente hoy.

En el P1 no puede entregar esta sonda con otros UUID: debe definir operaciones
representativas de su dominio y escribir su propia prueba de rendimiento reproducible.

---

## 7. Escenario A — falla de un nodo (obligatorio)

Objetivo: mover el lease de `raft_probe` al nodo que corresponde a `crdb-2`,
detenerlo, conservar mayoría 2/3 y medir la recuperación. Se necesitan **dos
terminales HOST**.

### Paso 10 — registrar precondición y mover el lease

Desde **HOST**:

```bash
make lab1-shell
psql -X -v ON_ERROR_STOP=1
```

En **PSQL**, active la captura antes de consultar:

```sql
\o evidence/chaos-a-before.txt

SELECT node_id, locality
FROM crdb_internal.gossip_nodes
ORDER BY node_id;

SELECT node_id, store_id
FROM crdb_internal.kv_store_status
ORDER BY node_id;

SELECT id, version, updated_at
FROM ti4601_raft.public.raft_probe
WHERE id = 1;

SELECT range_id, lease_holder, voting_replicas
FROM [SHOW RANGES FROM TABLE
      ti4601_raft.public.raft_probe WITH DETAILS];
```

Identifique el `node_id` cuya localidad es `region=cr-limon`; ese es el proceso
`crdb-2` que se detendrá. Busque su `store_id` en la segunda consulta. En este
laboratorio hay un store por nodo y normalmente ambos números coinciden, pero
`RELOCATE LEASE TO` recibe un **identificador de almacén (`store_id`)**. Sustituya
`<STORE_CR_LIMON>` por ese número. **No escriba literalmente los signos `< >`.**

```sql
ALTER RANGE RELOCATE LEASE TO <STORE_CR_LIMON>
FOR SELECT range_id
FROM [SHOW RANGES FROM TABLE
      ti4601_raft.public.raft_probe WITH DETAILS];

SELECT range_id, lease_holder, voting_replicas
FROM [SHOW RANGES FROM TABLE
      ti4601_raft.public.raft_probe WITH DETAILS];
\o
\q
```

Luego salga del contenedor con `exit`.

**Resultado esperado:** `lease_holder` coincide con el `node_id` de `cr-limon`,
`voting_replicas` conserva tres IDs y `chaos-a-before.txt` contiene la versión
confirmada inicial. Si el lease no se movió, repita únicamente la última consulta
`SHOW RANGES` antes de concluir que la reubicación falló.

### Paso 11 — iniciar la sonda en Terminal A

En la primera terminal **HOST**:

```bash
set -o pipefail
rm -f evidence/chaos-a-stop.epoch
docker compose --profile lab1 run --rm --no-deps app-crdb \
  python3 labs/lab1-cluster/chaos_probe.py \
    --duration 30 \
    --signal-file evidence/chaos-a-stop.epoch \
    --csv evidence/chaos-a.csv \
  | tee evidence/chaos-a.txt
```

**Resultado esperado durante el baseline:** varias líneas `before-stop ok`. Espere
cinco segundos y no cierre esta terminal.

Si una ejecución termina antes de mostrar recuperación, restaure el nodo y repita con
`--duration 45`, usando nombres distintos para los archivos de evidencia, a fin de no
ocultar el primer
resultado.

### Paso 12 — provocar y registrar la falla en Terminal B

Antes de detener nada, conserve este comando de rescate:

```bash
docker start ti4601-crdb-2 ti4601-crdb-3
```

En la segunda terminal **HOST**, ejecute cada comando por separado y observe
Terminal A:

```bash
docker stop --timeout 0 ti4601-crdb-2
date +%s.%N > evidence/chaos-a-stop.epoch
date --iso-8601=ns | tee evidence/chaos-a-stop.txt
sleep 10
docker start ti4601-crdb-2
```

**Resultado esperado:** después de crear el archivo de señal, Terminal A puede mostrar
un `after-stop error` o un primer `after-stop ok` con latencia alta mientras ocurre
el failover. Antes de finalizar debe volver a mostrar writes OK con latencia normal.
No observar un error explícito también es válido si el write quedó bloqueado y luego
confirmó con 2/3.

Espere a que Terminal A termine. Restaure siempre el nodo aunque interrumpa la prueba.
Si `docker start` indica que ya estaba iniciado, continúe.

### Paso 13 — verificar recuperación y RPO

```bash
set -o pipefail
make lab1-status | tee evidence/chaos-a-node-status.txt
docker compose --profile lab1 run --rm --no-deps app-crdb \
  psql -X -v ON_ERROR_STOP=1 -c \
  "SELECT id, version, updated_at
   FROM ti4601_raft.public.raft_probe WHERE id=1;" \
  | tee evidence/chaos-a-rpo.txt
```

Si el nodo todavía aparece con `is_live = false`, espere 10 segundos y repita
`make lab1-status`; no
declare RPO antes de recuperar el clúster.

Calcule y explique:

- **RTO observado:** marca de tiempo de la primera escritura confirmada después de
  la falla menos la marca de tiempo registrada para la falla;
- **RPO observado para operaciones confirmadas:** 0; compruebe que el valor confirmado
  antes de la falla no retrocedió;
- cantidad y tipo de errores transitorios.

La sonda reporta un RTO como comprobación, pero debe localizar las filas
correspondientes en el CSV y mostrar el cálculo. Los intentos sin confirmación tienen
un resultado desconocido y no deben contabilizarse como operaciones confirmadas
perdidas.

**Cómo localizar el RTO en el CSV**

1. Tome el número de `evidence/chaos-a-stop.epoch`.
2. Busque la primera fila con `phase=after-stop` y `status=ok`.
3. Reste el instante de falla de su columna `completed_epoch`.
4. Multiplique por 1000 para expresar milisegundos.
5. Compare con el RTO impreso por la sonda; explique cualquier diferencia de
   redondeo.

**Punto de control del paso 13:** el nodo está vivo, existe al menos una escritura con
estado `ok` posterior a la falla, la versión no retrocedió y todos los archivos
`chaos-a*` están presentes.

---

## 8. Escenario B — pérdida de quórum

**Opcional: demostración docente.** No forma parte de la rúbrica del escenario A. Este
escenario confirma la predicción 1/3. Use dos terminales y restaure ambos nodos al
terminar.

### B1 — Terminal A (HOST)

```bash
set -o pipefail
rm -f evidence/chaos-b-stop.epoch
docker compose --profile lab1 run --rm --no-deps app-crdb \
  python3 labs/lab1-cluster/chaos_probe.py \
    --label "Chaos B" --duration 45 \
    --signal-file evidence/chaos-b-stop.epoch \
    --csv evidence/chaos-b.csv \
  | tee evidence/chaos-b.txt
```

### B2 — Terminal B (HOST)

Antes de detener nodos, deje preparado el rescate:

```bash
docker start ti4601-crdb-2 ti4601-crdb-3
```

Después de observar baseline OK en Terminal A:

```bash
docker stop --timeout 0 ti4601-crdb-2 ti4601-crdb-3
date +%s.%N > evidence/chaos-b-stop.epoch
date --iso-8601=ns | tee evidence/chaos-b-stop.txt
sleep 8
docker start ti4601-crdb-2 ti4601-crdb-3
```

Mientras solo permanezca un nodo activo, una escritura no debe confirmarse: puede
fallar o agotar el tiempo de espera. Después de restaurar los nodos, espere a que la
sonda muestre nuevamente `after-stop ok`. Luego, demuestre con un
`UPDATE ... RETURNING` escrito por usted que:

1. modifica únicamente `raft_probe(id=1)`;
2. incrementa `version`;
3. devuelve la nueva versión y `updated_at`.

**Resultado esperado:** baseline OK, errores mientras queda 1/3 y al menos un OK
después de restaurar. Si la sonda termina antes de recuperar, conserve el error,
verifique `make lab1-status` y ejecute aparte su `UPDATE ... RETURNING`.

Esto no es una partición de red: los procesos están detenidos. `tc`/Toxiproxy
corresponde al Laboratorio 3.

---

## 9. Entregable del Laboratorio 1

Entregue un PDF de máximo 3 páginas, su bitácora de comandos y `evidence/`:

```text
evidence/
├── comandos.md
├── cluster-start.txt
├── node-status-initial.txt
├── config-check.txt
├── cluster-inspect.txt
├── latency-start.txt
├── latency.csv
├── latency-summary.txt
├── chaos-a-before.txt
├── chaos-a.txt
├── chaos-a.csv
├── chaos-a-stop.txt
├── chaos-a-node-status.txt
└── chaos-a-rpo.txt
```

El PDF debe contener:

1. diagrama de nodos/localidades y explicación de `--join` y `--locality`;
2. comandos usados para regiones, esquema y seed, con dos decisiones explicadas;
3. diferencia entre réplica Raft y fragmentación/asignación de Özsu, y por qué
   varios rangos implican varios grupos Raft;
4. p50/p99 de los cuatro casos, `n`, calentamiento (`warm-up`) y límites de Docker;
5. bitácora del escenario A: precondición, nodo, marcas de tiempo, errores y cálculo
   de RTO/RPO;
6. explicación de mayoría 2/3 y de por qué dos caídos bloquean;
7. puente P1: decisiones pendientes, no DDL copiado del ejemplo.

Distribución sugerida para respetar el máximo:

- **Página 1 — configuración:** topología, localidades, RBR/GLOBAL y diferencia con
  réplica Raft;
- **Página 2 — mediciones:** tabla de cuatro casos, método y límite de Docker local;
- **Página 3 — falla:** línea temporal, cálculo RTO/RPO, explicación 2/3 y puente P1.

### Lista de control antes de entregar

- [ ] `config-check.txt` termina en `6/6`.
- [ ] `cluster-inspect.txt` muestra tres regiones y tres votantes para `raft_probe`.
- [ ] `latency.csv` tiene 201 líneas incluida la cabecera.
- [ ] `chaos-a-before.txt` identifica el titular del lease que fue detenido.
- [ ] `chaos-a.csv` contiene filas `before-stop` y `after-stop`.
- [ ] El PDF muestra el cálculo del RTO, no solo el valor impreso por la sonda.
- [ ] El RPO se refiere a commits reconocidos, no a intentos.
- [ ] Ningún archivo contiene `COCKROACH_LICENSE`.
- [ ] La propuesta P1 usa dominio, esquema y programas propios.

### Rúbrica

| Criterio | 100 | 50 | 0 |
| --- | --- | --- | --- |
| Configuración propia | bitácora completa + 6/6 + explica decisiones | ejecuta sin explicar | solo usa artefactos ajenos |
| Clúster/localidad | 3 nodos + regiones + `SHOW CREATE/RANGES` | evidencia parcial | no opera |
| Mediciones | 4 casos, `n` ≥ 30, p50/p99 + método | faltan casos/método | sin números |
| Falla | precondición + evidencia fechada + cálculo RTO/RPO | solo “siguió arriba” | no se ejecutó |
| Raft | usa votantes/commit como evidencia y los distingue de la explicación teórica de término/elección | solo menciona quórum | explicación incorrecta |
| Puente P1 | enumera trabajo propio y reconoce límites | idea informal | presenta el laboratorio como P1 |

---

## 10. Contrato para el Proyecto 1

El laboratorio enseña un procedimiento; no entrega la implementación del proyecto.

**Puede reutilizar:**

- servicios Cockroach, red, volúmenes e imagen cliente;
- variables de conexión;
- consultas `SHOW REGIONS`, `SHOW CREATE` y `SHOW RANGES`;
- definiciones de p50, p99, RTO y RPO;
- estructura general: precondición → evento → medición → verificación.

**Debe producir desde cero:**

- predicados, relaciones, claves y localidades de su dominio;
- conjunto de datos y generador de carga representativos;
- programa que mida sus operaciones;
- automatización reproducible de la configuración y la falla;
- evidencia y argumento sobre si distribuir era necesario.

No se proporciona una plantilla SQL del P1. Su diseño debe salir del E1 v0 y cumplir
la especificación. Tampoco se indica qué tabla usar como equivalente de `raft_probe`:
el equipo debe diseñar una operación sobre una tabla con factor de replicación 3
(RF=3) que permita evaluar E4 sin hacer afirmaciones falsas sobre rangos RBR
subreplicados.

Contrato Postgres → Cockroach:
[`../../docs/fases-postgres-cockroach.md`](../../docs/fases-postgres-cockroach.md).

---

## 11. Recuperación y errores comunes

| Síntoma | Acción |
| --- | --- |
| `connection refused` al inicio | esperar 10–20 s; `make lab1-status` |
| solo aparecen 1–2 nodos | `docker compose --profile lab1 logs crdb-1 crdb-2 crdb-3` |
| `cluster already initialized` | normal con volúmenes existentes |
| región ya existe | inspeccionar `SHOW REGIONS`; no repetir la configuración completa |
| tabla o fila no existe | revisar qué archivo SQL omitió; aplicar solo ese paso |
| tabla con localidad incorrecta | corregir su DDL, eliminar únicamente esa tabla, previa autorización del docente, y reaplicar `schema.sql` |
| `lab1-check` falla | corregir el primer `[FAIL]`; el verificador no configura |
| nodo quedó detenido | `docker start ti4601-crdb-2 ti4601-crdb-3` |
| remoto ≈ local | resultado válido en Docker local; documentar límite |
| multi-región solicita licencia | verificar `.env` en la raíz y ejecutar `install_license.py` |

Para diagnosticar un nodo sin borrar datos:

```bash
docker compose --profile lab1 logs --tail 50 crdb-1 crdb-2 crdb-3
```

Apagado sin borrar datos:

```bash
make lab1-down
```

Reinicio limpio, **solo con autorización y respaldo**:

```bash
make lab1-down-v
make lab1-up
```

`lab1-down-v` elimina volúmenes. Después de usarlo, repita desde el Paso 1:
verifique nodos, vuelva a instalar la licencia si aplica y ejecute los pasos 2–13.
No existe un objetivo de Make que reconstruya su trabajo.

