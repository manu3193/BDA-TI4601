# Tarea 3 — Consultas y modelado de documentos en MongoDB

**Valor:** 1,5 % del curso · **Equipos:** los mismos del Laboratorio 3  
**Asignación:** miércoles 21 de octubre de 2026 · **Plazo:** 1 semana  
**Entrega:** miércoles 28 de octubre de 2026, 11:00 pm, un PDF por equipo (máximo 2 páginas) en TEC Digital, con el enlace al repositorio.  
**Prerrequisito:** diapositivas *Bases de datos orientadas a documentos* (ejemplo de ciudades, diapositivas 20 a 33).

La tarea se entrega **antes** que el [Laboratorio 3](README.md) y lo prepara: practica consultas, índices y decisiones de modelado sobre la misma boletería que usará el laboratorio, pero en un MongoDB de un solo nodo, sin conjunto de réplicas. No necesita haber resuelto ningún TODO del laboratorio.

Toda la evidencia va en `evidence/tarea3/` y cada cifra del PDF debe salir de un archivo de ahí.

---



## 1. Preparar el entorno (una sola vez)

Todo se ejecuta en contenedores, desde la raíz del repositorio.

```bash
make build                                         # imagen del curso, con pymongo
docker run -d --name ti4601-tarea3 mongo:8.0       # MongoDB de un nodo, solo para la tarea

# generar la semilla de la boletería (400 eventos)
docker compose run --rm --no-deps app \
  python3 labs/lab3-mongo-replicas/generar_datos.py

# importarla en la colección eventos
docker exec -i ti4601-tarea3 mongoimport --db boleteria --collection eventos --drop \
  < labs/lab3-mongo-replicas/data/eventos.jsonl
```

**Resultado esperado:** el generador imprime un manifiesto con `eventos: 400` y `mongoimport` termina con `400 document(s) imported successfully`. `data/eventos.jsonl` no viene en el repositorio: lo escribe `generar_datos.py`, y `labs/*/data/` no se versiona. Para abrir `mongosh`:

```bash
docker exec -it ti4601-tarea3 mongosh boleteria
```

Cada documento es un evento con sus zonas embebidas:

```json
{ "_id": "EV-0001", "nombre": "Concierto Andino 1", "categoria": "concierto",
  "ciudad": "Heredia", "recinto": "Arena Central", "fecha": "2026-12-04",
  "etiquetas": ["familiar", "accesible"],
  "zonas": [ { "nombre": "General", "precio": 8000, "capacidad": 300, "disponibles": 300 },
             { "nombre": "VIP", "precio": 45000, "capacidad": 60, "disponibles": 60 } ] }
```

El campo `patrocinador` solo existe en algunos eventos. Al terminar la tarea puede borrar el contenedor con `docker rm -f ti4601-tarea3`.

---



## 2. Parte A — Consultas (70 puntos)

Complete [`tarea/consultas.js`](tarea/consultas.js). El archivo ya está en el repositorio, con el encabezado de cada consulta y sin las respuestas. Debe ejecutarse completo con:

```bash
mkdir -p evidence/tarea3
docker exec -i ti4601-tarea3 mongosh --quiet boleteria --file /dev/stdin \
  < labs/lab3-mongo-replicas/tarea/consultas.js | tee evidence/tarea3/consultas.txt
```

El archivo se ejecuta como *script*, no como sesión interactiva, por lo que hay tres reglas:

- No use `use` ni `show`: la base ya es `boleteria`.
- Cada consulta debe imprimir su resultado con `.forEach(printjson)` o `printjson(...)`.
- Cada consulta imprime un encabezado (`print("== A1 ==")`) antes de su resultado.

Proyecte **solo** los campos que pide la pregunta.


| #   | Pregunta                                                                                                                             | Operadores                                      |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------- |
| A1  | Nombre, recinto y fecha de los conciertos de Heredia entre el 1 de diciembre de 2026 y el 28 de febrero de 2027, ordenados por fecha | `find`, rango sobre `fecha`, `sort`, proyección |
| A2  | Eventos que tienen una zona VIP con precio menor a 48 000 colones; muestre el nombre del evento y **solo** su zona VIP               | `$elemMatch` en el filtro y en la proyección    |
| A3  | Eventos con la etiqueta `"accesible"` que no sean de categoría `"teatro"` ni `"conferencia"`                                         | consulta sobre un arreglo, `$nin`               |
| A4  | Cantidad de eventos **sin** patrocinador, por categoría                                                                              | `$exists`, `aggregate` con `$group`             |
| A5  | Capacidad total por ciudad (suma de las capacidades de todas las zonas de todos sus eventos), de mayor a menor                       | `$unwind`, `$group`, `$sort`                    |


**Índices (incluido en los 70 puntos).** Para **A1**, muestre `explain("executionStats")` antes y después de crear un índice compuesto que usted proponga, e incluya en el archivo el `createIndex`. Incluya en el PDF `totalDocsExamined`, `totalKeysExamined`, `nReturned` y la etapa (`COLLSCAN` o `IXSCAN`). Justifique el orden de los campos del índice.

Antes de escribir A2, pruebe en `mongosh` la versión **sin** `$elemMatch` (dos condiciones separadas sobre `zonas.nombre` y `zonas.precio`) y compare cuántos eventos devuelve cada una. Explique la diferencia en el PDF: es la misma idea que necesitará en el Paso 8 del laboratorio.

---



## 3. Parte B — Anidar o referenciar (30 puntos)

En la boletería, las zonas viven **dentro** del documento del evento. Para registrar las compras, un compañero propone guardar también cada orden como un elemento de un arreglo `ordenes` dentro del evento. Otra opción es una colección aparte `ordenes` que referencia al evento por su `_id`.

Responda en **media página como máximo**, con números:

1. Mida en `mongosh` el tamaño de una orden de ejemplo con `bsonsize({...})`, con los campos `_id`, `evento_id`, `zona`, `cantidad`, `estado` y `creada_en`. Estime cuántas órdenes caben en un evento antes del límite de 16 MB por documento.
2. ¿Qué pasa cuando cientos de compradores escriben al mismo tiempo sobre el **mismo** documento? Mencione una ventaja y una desventaja de que todo esté en un solo documento.
3. Dé una regla de una o dos oraciones para decidir cuándo embeber y cuándo referenciar. Aplíquela a un ejemplo de otro dominio que no sea la boletería ni el Proyecto 2.

---



## 4. Entregable

- **PDF de máximo 2 páginas** con las consultas, los resultados de `explain` antes y después del índice, la comparación de A2 y la Parte B.
- **En el repositorio:** `labs/lab3-mongo-replicas/tarea/consultas.js` y `evidence/tarea3/consultas.txt`, con commits de los tres integrantes.



## 5. Rúbrica (100 puntos, se escala a 1,5 %)


| Criterio                 | Pts | Cómo se obtiene el máximo                                                                                 |
| ------------------------ | --- | --------------------------------------------------------------------------------------------------------- |
| Consultas A1–A5          | 45  | el archivo corre completo y cada resultado responde la pregunta con proyecciones mínimas (9 por consulta) |
| Índice y `explain` de A1 | 15  | antes y después con las cuatro métricas; orden de campos justificado                                      |
| Comparación de A2        | 10  | cantidad de eventos con y sin `$elemMatch` y explicación correcta de la diferencia                        |
| Embeber o referenciar    | 30  | cálculo con `bsonsize()` (10), concurrencia sobre un documento (10), regla aplicada a otro dominio (10)   |


**Topes.** Cifras sin respaldo en `evidence/tarea3/`: no se puntúan. Un `consultas.js` que no corre completo: Consultas A1–A5 a la mitad.