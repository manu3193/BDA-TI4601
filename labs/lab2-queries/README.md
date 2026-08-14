# Lab 2 — Consultas distribuidas (semi-join / costo)

**Semana práctica:** 7 · **Teoría preparada en S4–S5**  
**Motor:** mismo clúster Cockroach del Lab 1 (`make lab1-up`).  
**Índice:** [`../README.md`](../README.md).

> Stub: el código y la rúbrica completa se publican antes de S7. Esta página fija el
> contrato pedagógico para que S4/S5 puedan preparar la práctica.

## 1. Qué van a medir (contrato)

Sobre el clúster Lab 1, con esquema ≥3 tablas y datos suficientes:

| Métrica | Antes (join “caro”) | Después (reducción / semi-join) |
| --- | --- | --- |
| Bytes transferidos (aprox.) | | |
| Tiempo (ms) | | |
| Evidencia de plan (`EXPLAIN`) | | |

## 2. Teoría que ya deben traer

| Semana | Concepto |
| --- | --- |
| S4 | Localización, costo de comunicación, qué es un shuffle malo |
| S5 | Semi-join / reducción de transferencia (pizarra) |
| S7 | Bernstein & Chiu (lectura oral) + este lab |

## 3. Relación con Lab 1 / P1

Mismo stack. El informe Lab 2 pide **números**, no solo “el join corre”. La defensa P1
(S8) puede reutilizar estas mediciones.

## 4. Estado del repo

Pendiente de publicar: scripts de carga, consultas A/B y plantilla `evidence/`.
Hasta entonces usen el handout de métricas de S4 (`lecciones/S04/06-handout.md` en el
pack del curso).
