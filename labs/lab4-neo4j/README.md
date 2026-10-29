# Laboratorio 4 — Actas municipales en un grafo

**Valor:** 2,5 % del curso · **Equipos:** tres personas  
**Asignación:** miércoles 4 de noviembre de 2026 · **Plazo:** 2 semanas  
**Entrega:** miércoles 18 de noviembre de 2026, 11:00 pm. Un informe en PDF por equipo (máximo 4 páginas) en TEC Digital, con el enlace al repositorio donde está el notebook completado.

**Motor:** Neo4j 5 Community, un solo nodo.  
**Notebook:** [`Lab4.ipynb`](Lab4.ipynb)  
**Fuente:** el índice público de actas del Concejo Municipal de Belén, [actas municipales](https://www.belen.go.cr/web/guest/actas-municipales).

El laboratorio continúa la clase de bases de datos de grafos (`08-BDGrafos`). Allí vimos el grafo de propiedades, los nodos con etiquetas, las relaciones con tipo y dirección, y los patrones `MATCH ... RETURN` de Cypher. Aquí se usan esas ideas para cargar actas reales en Neo4j y para responder preguntas con un modelo de lenguaje que se apoya en el grafo.

El grafo es de un solo nodo a propósito. Mayoría, elecciones y réplicas ya se midieron en el Laboratorio 3.

---

## 1. Qué queda dentro y qué queda fuera

El índice lista actas desde 1992. Bajarlo entero no cabe en la sesión, y muchos archivos viejos no sirven para este ejercicio: algunos enlaces devuelven HTML y otros son PDF escaneados sin texto.

El notebook **lee el índice completo**, pero **carga solo cuatro actas de 2026** con texto digital y, de cada una, **solo las dos primeras páginas**:

| Acta | Para qué está |
| --- | --- |
| `58-2026`, `59-2026`, `60-2026`, `61-2026` | corpus del grafo |

Con eso alcanza para construir el grafo, recorrer caminos de uno y dos saltos y hacerle preguntas al modelo con un contexto que sí está en el grafo.

No se necesita ninguna clave de API. El modelo de *embeddings* (`paraphrase-multilingual-MiniLM-L12-v2`) y el modelo que redacta (`Qwen2.5-0.5B-Instruct`) vienen dentro de la imagen de Docker. Son modelos **preentrenados**: el curso los usa, no los entrena.

## 2. Qué aprenderá

1. Modelar un dominio como grafo de propiedades: actas, fragmentos de texto y personas como nodos, y `CONTIENE`, `SIGUE` y `PARTICIPA_EN` como relaciones con propiedades.
2. Cargar datos en Neo4j de forma **idempotente** con `MERGE`, parámetros y restricciones de unicidad.
3. Escribir consultas Cypher de uno y dos saltos, y compararlas con su equivalente en SQL.
4. Explicar qué es un modelo de lenguaje, qué es un *embedding* y cómo funciona la similitud coseno.
5. Combinar la búsqueda vectorial con el recorrido de caminos (GraphRAG) y orquestar la respuesta con LangGraph.
6. Leer la respuesta del modelo contra el contexto recuperado y reconocer una alucinación.

## 3. Cómo levantarlo

Ejecute desde la raíz del repositorio. La imagen parte de `quay.io/jupyter/pytorch-notebook`, que ya trae Jupyter y PyTorch para CPU, así que no se compila nada. La primera construcción solo agrega las librerías del laboratorio y descarga los dos modelos en la caché de la imagen.

```bash
make lab4-up
```

| Qué | Dónde |
| --- | --- |
| Notebook | http://127.0.0.1:8888/lab?token=ti4601 |
| Navegador de Neo4j | http://127.0.0.1:7474 |
| Usuario / contraseña | `neo4j` / `ti4601-grafos` |
| Bolt desde el navegador | `bolt://localhost:7687` |
| Bolt desde el notebook | `bolt://neo4j:7687` (ya viene en el entorno) |

Abra `labs/lab4-neo4j/Lab4.ipynb` y ejecute las celdas en orden. Al terminar:

```bash
make lab4-down
```

`make lab4-down-v` borra también el volumen del grafo. `make lab4-ejecutar` corre el notebook completo dentro del contenedor y sirve para comprobar que llega al final.

MongoDB y los demás perfiles no hacen falta. Déjelos apagados, porque la imagen del notebook y Neo4j ya ocupan bastante memoria.

## 4. Cómo está organizado el notebook

Las secciones 1 a 8 son lectura: un repaso del grafo de propiedades, lo nuevo de Cypher, una introducción a modelos de lenguaje y a técnicas de recuperación, la arquitectura y el diagrama del modelo de datos. Léalas antes de programar.

Los pasos 1 a 4 ya están resueltos: descargan los PDF, extraen el encabezado y los participantes, parten el texto con LlamaIndex y calculan los vectores. El paso 8 explica RAG pieza por pieza (el modelo codificador, el modelo generador y LangGraph) con figuras y tres celdas de demostración. El trabajo del equipo son **cinco TODO** en Cypher:

| TODO | Paso | Qué se escribe |
| --- | --- | --- |
| 1 | 5.3 | `MERGE` de `Persona` y de la relación `PARTICIPA_EN`, con `rol` y `cargo` en la relación |
| 2 | 5.4 | `MERGE` de `Fragmento`, sus propiedades y la relación `CONTIENE` |
| 3 | 6.1 | consulta de un salto: fragmentos por acta, con agregación |
| 4 | 6.2 | consulta de dos saltos: `Persona → Acta → Fragmento` filtrada por una palabra |
| 5 | 7 | recorrido de caminos después de la búsqueda vectorial (`OPTIONAL MATCH`, `collect`) |

Cada TODO tiene un ejemplo resuelto o una pista, y una celda de verificación que imprime una de tres respuestas:

- **`PENDIENTE`**: el TODO todavía vale `None`;
- **`OK`**: la consulta da el resultado esperado;
- **`VERIFICACIÓN FALLÓ`**: el mensaje dice qué revisar.

El notebook corre de principio a fin aunque haya TODO pendientes. Al final aparece un resumen del estado de los cinco TODO.

El paso 6.3 pide una **captura del navegador de Neo4j** con el grafo cargado; va en el informe.

## 5. Informe

Pegue las salidas del notebook en lugar de transcribirlas a mano. Cuatro páginas como máximo. Las preguntas son las mismas que aparecen al final del notebook:

1. **Corpus.** ¿Cuántos documentos publica el índice y cuántas actas entraron al grafo? Justifique el corte de cuatro actas y dos páginas, y explique qué haría el notebook con un PDF escaneado.
2. **Modelo de datos.** Incluya la captura del navegador de Neo4j (paso 6.3). Explique por qué `cargo` es una propiedad de `PARTICIPA_EN` y no de `Persona`.
3. **Uno y dos saltos.** Pegue sus consultas de los TODO 3 y 4 con su resultado. Compárelas con el SQL equivalente: ¿cuántos `JOIN` necesitaría un tercer salto?
4. **Idempotencia.** ¿Qué pasó, o qué habría pasado, si en el TODO 1 usaba `CREATE` en lugar de `MERGE`? Relaciónelo con el Laboratorio 3.
5. **Recuperación.** Con la salida del TODO 5, compare «solo vector» con «vector + acta». ¿Por qué la búsqueda solo por vector puede equivocarse de acta? Use la salida del paso 8.2: ¿qué papel juega que el codificador lea solo los primeros 128 tokens de cada fragmento?
6. **El modelo.** Para cada una de las tres preguntas del paso 9, diga si la respuesta es correcta según el contexto recuperado. Si el modelo afirma algo que no está en ese contexto, señálelo. Identificar una alucinación suma puntos; no es un defecto que haya que ocultar.
7. **Límite.** En una o dos oraciones: ¿qué tenía el conjunto de réplicas del Laboratorio 3 que este Neo4j no tiene?

## 6. Rúbrica (100 puntos, se escala a 2,5 %)

| Criterio | Pts | Cómo se obtiene el máximo |
| --- | --- | --- |
| Carga del grafo (TODO 1 y 2) | 25 | ambas verificaciones en `OK`, incluida la segunda carga sin duplicados; respuestas a las preguntas 2 y 4 |
| Consultas de uno y dos saltos (TODO 3 y 4) | 20 | verificaciones en `OK`, consultas y resultado en el informe, comparación con SQL (pregunta 3) |
| Recuperación por vector y por camino (TODO 5) | 20 | verificación en `OK` y una comparación razonada entre «solo vector» y «vector + acta» (pregunta 5) |
| Lectura crítica del modelo | 20 | las tres respuestas evaluadas contra el contexto, con las alucinaciones señaladas (pregunta 6) |
| Delimitación y límites | 15 | preguntas 1 y 7, con cifras tomadas de la salida |

**Topes.** Si el informe no trae salidas del notebook, cada criterio que dependa de una cifra vale la mitad. Un TODO que queda en `PENDIENTE` o en `VERIFICACIÓN FALLÓ` no suma la parte de código de su criterio; el análisis escrito se califica aparte.
