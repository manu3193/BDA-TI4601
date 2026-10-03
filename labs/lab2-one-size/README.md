# Laboratorio 2 — One size fits all?

**Semana:** 9 

**Valor:** 2,5 % 

**Entrega:** martes 13 de octubre de 2026, 11:00 pm, PDF en TEC Digital (un PDF por grupo) .  
**Motores:** Postgres 16 (relacional) y Valkey 8 (clave-valor, fork abierto de Redis).  
**Datos:** [NYC Yellow Taxi Trip Data](https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data) en Kaggle, archivo `yellow_tripdata_2016-01.csv` (10 906 858 viajes, 1,7 GB).  


---

## 1. ¿Qué queremos comprobar?

En el paper de Stonebraker et al. los autores afirman que un solo motor diseñado para el procesamiento analítico de negocio (OLTP), no puede competir con motores especializados en otros mercados. Su evidencia central son datos financieros: dos proveedores envían cotizaciones, y cada 100 cotizaciones tardías de un proveedor se emite una alerta. StreamBase procesó 160 000 mensajes por segundo y un RDBMS comercial, 900, en la misma máquina.

Usted va a hacer un experimento similar con viajes de taxi. Se trata de un análisis para detectar anomalías en los viajes realizados que no reportaron distancia o tarifa. Cada cierta cantidad de anomalías se produce una alerta. El objetivo es realizar el procesamiento en la base de datos que permita calcular la cantidad de anomalías simulando un OLAP.

Además vamos a medir el tipo de consultas que se benefician del modelo relacional en rendimiento, específicamente los casos en los que se requiere materializar en disco y cuando es necesario responder preguntas que no se previeron al definir los indicadores clave de rendimiento (KPIs) a calcular en el procesamiento en streaming.

Se calcularán los siguientes KPIs:
| Paso | Pregunta                                                     |
| ---- | ------------------------------------------------------------ |
| 1    | ¿Cuánto cuesta guardar el mes entero en cada motor?          |
| 2    | ¿Cuánto es la tarifa promedio agrupada por método de pago? `AVG(fare_amount) GROUP BY payment_type`?    |
| 3a   | ¿Quién gana en lectura y update por llave?                   |
| 3b   | ¿Cuántos mensajes por segundo procesa cada motor en el dataset? |




## 2. Explicación del código


| Archivo            | Qué hace                                                               | ¿Deben agregar código?           |
| ------------------ | ---------------------------------------------------------------------- | -------------------------------- |
| `common.py`        | Lee el CSV desde el zip, abre conexiones, registra medidas, cronómetro | No, pero léalo primero           |
| `descargar.py`     | Baja el zip de Kaggle a `data/`                                        | No                               |
| `sql/pg_trips.sql` | Tabla `trips` de Postgres                                              | No                               |
| `cargar.py`        | Paso 1                                                                 | **Sí! TODO 1, TODO 2**           |
| `sql/olap.sql`     | La consulta de almacén                                                 | No                               |
| `analitica.py`     | Paso 2                                                                 | **Sí! TODO 3**                   |
| `sql/pg_feed.sql`  | Tablas y trigger del feed en Postgres                                  | No, pero es el modelo del TODO 4 |
| `lua/feed.lua`     | Lógica del feed en Valkey                                              | **Sí! TODO 4**                   |
| `escrituras.py`    | Paso 3                                                                 | **Sí! TODO 5**                   |
| `graficas.py`      | Gráficas y tabla del reporte                                           | No                               |


Cada TODO está marcado en el código con `# TODO n`, trae instrucciones paso a paso y termina en un `raise NotImplementedError` que ustedes deben reemplazar. Después de cada TODO, el script corre una **verificación automática** (despliega `OK:` o `VERIFICACIÓN FALLÓ:`).  Si la verificación no pasa, el codigo no es correcto. 

No cambie las firmas de las funciones ni los nombres de las llaves de Valkey ya que las verificaciones dependen de ellos.

## 3. Preparar el entorno

```bash
make build        # la imagen trae redis (cliente Python) y matplotlib
make lab2-up      # Postgres + Valkey
docker compose run --rm app python3 labs/lab2-one-size/descargar.py
```

La descarga es un zip de 439 MB de Kaggle. Si su red bloquea el endpoint, instale el CLI de Kaggle en su máquina, configure su token y descargue el zip o el CSV en `labs/lab2-one-size/data/`:

```bash
kaggle datasets download elemento/nyc-yellow-taxi-trip-data -f yellow_tripdata_2016-01.csv -p labs/lab2-one-size/data
```

`data/` no se agrega el repo ni se agrega en la imagen de docker. Todos los comandos de abajo se corren con `docker compose run --rm app python3 labs/lab2-one-size/<script>`; para abreviar se escribe solo el nombre del script.

---



## 4. Los pasos, uno por uno



### Paso 1: Carga y espacio (`cargar.py`)

El mismo CSV entra a los dos motores.

- **Postgres** crea `trips` con 20 columnas tipadas (`sql/pg_trips.sql`) y la llena con `COPY`, el mecanismo de carga masiva: el cliente manda el CSV como flujo de bytes y el servidor lo parsea, sin un `INSERT` por fila. Después construye la llave primaria, un índice B-tree sobre `trip_id`, y corre `VACUUM ANALYZE` para que el optimizador tenga estadísticas en el paso 2.
- **Valkey** guarda cada viaje como un *hash*: la llave es `trip:<id>` y adentro hay un campo por columna, todo como texto. No hay tipos, no hay esquema, no hay disco. Como todo vive en RAM, se carga solo el primer millón y se extrapola (sino tardaría mucho tiempo para nuestras laptops).

**Importante:** Un row-store guarda los atributos de un registro juntos en páginas de 8 KiB. Una base de datos clave-valor guarda pares llave → valor en memoria, optimizados para resolver la consulta «dame el valor de esta llave» de la forma más óptima.

**TODO 1 —** `medir_espacio_postgres(cur)`**.** Postgres expone métodos para calcular el tamaño de cada relación con funciones del catálogo: `pg_relation_size` (solo el heap), `pg_indexes_size` (los índices) y `pg_total_relation_size` (todo, incluido TOAST). Escriba un `SELECT` que devuelva las tres para `'trips'` y retorne la fila.

**TODO 2 —** `cargar_valkey(r, limit)`**.** Guarde los viajes con `HSET`. La trampa es la red: un `HSET` enviado solo espera la respuesta antes de mandar el siguiente, y un millón de esperas se nota. Use un *pipeline*: encola comandos en el cliente y los envía juntos con `execute()`, un viaje de ida y vuelta por lote. Las instrucciones detalladas están en el código. Se verifica que Valkey tenga exactamente `limit` llaves y que el último viaje tenga `fare_amount`.

**Explique:** ¿Qué tienen en común ambos métodos de carga de datos en postgres? ¿Cómo se resuelve el overhead al cargar grandes cantidades de datos en cada sistema?

**Correr:**

```bash
cargar.py                      # ~2 min con el perfil completo
cargar.py --perfil reducido    # 2 M filas en Postgres; úselo si tiene < 8 GB de RAM
cargar.py --solo valkey        # repite solo Valkey (útil mientras depura el TODO 2)
```

¿Qué pasa si `TODO 1` falla  después del `COPY` ? 

Si le pasa, corrija su solución y vuelva a correr, la tabla se sobreescribe.

**Observe los** `bytes_por_fila` en cada motor y `ram_extrapolada_total` contra `disco_total`. **Responda** ¿Cuál motor de base de datos podría guardar un año entero en su laptop?

### Paso 2: La consulta de almacén (`analitica.py`)

El código lo que hace es realizar la misma consulta a los dos motores:

```sql
SELECT payment_type, AVG(fare_amount), COUNT(*) FROM trips GROUP BY payment_type;
```

- **Postgres** la resuelve adentro del RDBMS como un stored procedure. El script guarda el plan de `EXPLAIN (ANALYZE, BUFFERS)` en `evidence/plan_olap_postgres.txt` y mide la mediana de cinco corridas sobre la tabla completa y sobre el mismo millón de registros que tiene Valkey (`trip_id <= 1000000`). Al final, el script permite responder una pregunta nueva no anticipada, pero que es posible calcular con una consulta OLAP sobre un modelo relacional: la propina promedio por hora.
- **Valkey** no tiene método para agrupar `GROUP BY`. El programa del lado del cliente debe recorrer las llaves con `SCAN` y hacer el agrupamiento por su cuenta.

**Importante:** Definir la primitiva correcta en el motor. Postgres tiene un operador de agregación y un optimizador que lo ejecuta en paralelo junto a los datos. Valkey obliga a sacar cada fila por la red para agruparla afuera del motor, del lado del cliente.

**TODO 3 —** `agregar_lote(r, keys, sums, counts)`**.** Recibe un lote de llaves `trip:`*. Lea `payment_type` y `fare_amount` de cada una con `HMGET` en un pipeline y acumule en los diccionarios `sums` y `counts`. Usted está escribiendo a mano lo que el nodo `HashAggregate` del plan de Postgres hace dentro del RDBMS. 

**Observe:** Busque en el plan de ejecución, de abajo hacia arriba:

- `Parallel Seq Scan on trips`: cuántos *workers*, cuántas filas por *loop* y cuánto tiempo.
- `Buffers: shared read=…`: páginas de 8 KiB leídas. Multiplique por 8 KiB y compárelo con `disco_tabla` del paso 1. Postgres leyó la tabla entera, las 20 columnas, para usar dos. Eso es lo que un column-store evita.
- `Partial HashAggregate` y `Finalize GroupAggregate`: la agregación en dos fases, una por *worker* y otra al final.

**Reporte** los resultados y el análisis en su informe. 



### Paso 3 — Benchmark de Escrituras y el feed (`escrituras.py`)

**3a. Operación por llave:** Se seleccionan 2 000 viajes al azar (la semilla hace repetible la muestra). En cada uno, una lectura por llave y un update por llave. Compare la mediana de cada motor.

**Importante:** Con `autocommit`, cada `UPDATE` de Postgres es una transacción que no responde hasta que el WAL, su bitácora, se materializa a disco (`fsync`). Esa espera es el precio de la **D** de ACID. Valkey, como está configurado para este lab (`--appendonly no`), no escribe nada a disco.

**3b. El dataset:** Los primeros 10 000 viajes se reproducen como mensajes. Cada mensaje suma al conteo y a la tarifa de su tipo de pago. Si es una anomalía, suma a su proveedor, y cada `--umbral` anomalías de ese proveedor se emite una alerta.

**Importante:** Postgres procesa *outbound*: guarda el mensaje en `feed_trip` y un trigger actualiza los contadores. Valkey procesa *inbound*: el mensaje no se guarda, solo pasa por un script Lua que corre **dentro** del servidor, sin volver al cliente entre un paso y otro.

**TODO 4 —** `lua/feed.lua`**.** Traduzca a comandos de Valkey la lógica del trigger `feed_trip_after()` de `sql/pg_feed.sql`: `HINCRBY` y `HINCRBYFLOAT` sobre los hashes `agg:n`, `agg:suma`, `alarma:anomalias` y `alarma:alertas`. Los argumentos llegan en `ARGV` y **todos son strings**: compare `anom == '1'`, no `anom == 1`. Lea el trigger de postgres y el código en Lua lado a lado; deben hacer lo mismo.

**TODO 5 —** `enviar_en_lotes(conn, msgs, batch)`**.** La variante `postgres_lote` agrupa `batch` mensajes por transacción con `conn.transaction()` y `executemany`. El trigger se sigue disparando por cada fila; lo único que cambia es cuántas veces se espera al disco.

**Las seis variantes.** Están pensadas en pares, para poder observar los escenarios de forma separada:


| Variante                      | Qué es                                            | ¿Espera al disco en cada mensaje?              |
| ----------------------------- | ------------------------------------------------- | ---------------------------------------------- |
| `postgres_commit_por_mensaje` | un `INSERT` + trigger por transacción             | Sí (WAL)                                       |
| `postgres_commit_asincrono`   | igual, con `synchronous_commit = off`             | No: puede perder la última fracción de segundo |
| `postgres_lote`               | `--lote` mensajes por transacción (TODO 5)        | Una vez por lote                               |
| `valkey_por_mensaje`          | una llamada al script por mensaje (TODO 4)        | No                                             |
| `valkey_aof_always`           | igual, con la bitácora AOF y `appendfsync always` | Sí (AOF)                                       |
| `valkey_pipeline`             | `--lote` llamadas por viaje de red                | No                                             |


- `valkey_aof_always` y `postgres_commit_por_mensaje`: **garantizan durabilidad**, para los distintos modelo.
- `valkey_por_mensaje` y `postgres_commit_asincrono`: **sin esperar materialización en disco** en ninguno de los dos.

**Incluya** en su informa la tabla con los resultados**

El script calcula en Python la respuesta esperada y verifica que las seis variantes la den. Si falla una de Postgres, el problema es el TODO 5; si fallan las de Valkey, el TODO 4.

**Correr:**

```bash
escrituras.py                                # 3a + 3b, 1–3 min
escrituras.py --solo-feed                    # solo 3b, mientras depura
escrituras.py --umbral 100 --mensajes 50000  # el Count100 exacto del paper; tarda varios minutos
```

El umbral por defecto es 10 con el objetivo de poder observar la alerta.

### Gráficas (`graficas.py`)

Lee `evidence/resultados.jsonl` y produce `evidence/graficas.png` (cuatro paneles, uno por paso) y `evidence/tabla.md` (todas las medidas). Si repite un paso, se usa la última medida de cada métrica. Para empezar de cero, borre el archivo `resultados.jsonl`.

---



## 5. Entregable

Un PDF por grupo con:

1. Su código de los TODO 1–5 y la salida con las líneas `OK:` de cada verificación.
2. `evidence/graficas.png` y `evidence/tabla.md`, generadas por ustedes. Indiquen máquina, sistema operativo, RAM y perfil del lab que utilizaron.
3. El plan de `evidence/plan_olap_postgres.txt`, con el nodo que más tiempo consume señalado y las páginas leídas en MiB.
4. Una respuesta de máximo 2 páginas a la pregunta:

> **Justifique por qué Stonebraker afirma que «One Size Fits All» es una idea ya desfasada, tomando como evidencia sus resultados experimentales.**

La respuesta debe usar al menos un número de cada paso, citar la sección del paper que corresponda y **desarrollar y justificar** estas tres apreciaciones. No basta con enunciarlas, cada una se justifica con sus mediciones.

- **Ningún motor gana todas las cargas de trabajo.** Diga en qué paso gana cada uno y por cuántas veces. Incluya las limitantes de Valkey que sus números muestran.

- **Que Valkey pierda el `GROUP BY` no refuta el argumento del dataarehouse.** Justifique por qué el paso 2 no pone a prueba una base de datos column-store, sino que pone a prueba una base de datos llave-valor que no tiene la primitiva de agregación. Use el plan del punto 3 de Postgres. 

- **La brecha de los resultados no es solo el overhead de fsync()** Con los dos pares de variantes del paso 3b, separe qué parte de la diferencia se debe a la durabilidad (materialización) por mensaje y qué parte se da cuando ambos sistemas se comparan materializando a disco en cada mensaje.

## 7. Rúbrica (2,5 %)


| Criterio                   | Peso | 0                                      | 50                                       | 100                                                                                  |
| -------------------------- | ---- | -------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------ |
| Código de los TODO         | 25 % | falta alguno o no pasa la verificación | los cinco pasan, sin explicar decisiones | los cinco pasan y el reporte explica por qué el pipeline y el lote cambian el tiempo |
| Predicción y evidencia     | 15 % | sin predicción o sin gráficas propias  | predicción o gráficas incompletas        | predicción previa, `graficas.png`, `tabla.md` y máquina declarada                    |
| Plan de Postgres leído     | 10 % | plan pegado sin comentario             | nodo señalado sin explicar               | nodo dominante y páginas leídas relacionados con row-store                   |
| Brecha del feed explicada  | 25 % | «Valkey es más rápido»                 | razón con un número                      | separa durabilidad de modelo con los dos pares de variantes                          |
| Justificación con el paper | 25 % | opinión sin métricas                   | métricas sin secciones                   | desarrolla las tres apreciaciones del entregable, con un número por paso y la sección del paper |




## 9. Limpiar datos

```bash
make lab2-down     # detiene Valkey; Postgres sigue
docker compose exec postgres psql -U ti4601 -c "DROP TABLE IF EXISTS trips, feed_trip, agg_pago, alarma_vendor CASCADE"
```

