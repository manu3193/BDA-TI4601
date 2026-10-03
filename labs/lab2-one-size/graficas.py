#!/usr/bin/env python3
"""Genera las gráficas y la tabla del reporte a partir de evidence/resultados.jsonl.

Si un paso se corrió varias veces, se usa la última medida de cada métrica.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import EVIDENCE, RESULTS  # noqa: E402

PG, VK = "#336791", "#d9534f"


def latest() -> dict[tuple[str, str, str], dict]:
    if not RESULTS.exists():
        raise SystemExit("No hay evidence/resultados.jsonl. Corra los pasos 1 a 3.")
    out = {}
    for line in RESULTS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        out[(row["paso"], row["motor"], row["metrica"])] = row
    return out


def val(m, paso, motor, metrica):
    row = m.get((paso, motor, metrica))
    return row["valor"] if row else None


def bars(ax, labels, values, colors, title, unit, log=False):
    pairs = [(l, v, c) for l, v, c in zip(labels, values, colors) if v is not None]
    if not pairs:
        ax.set_visible(False)
        return
    ls, vs, cs = zip(*pairs)
    b = ax.bar(ls, vs, color=cs)
    ax.bar_label(b, labels=[f"{v:,.1f}" for v in vs], fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(unit)
    if log:
        ax.set_yscale("log")
    ax.tick_params(axis="x", labelrotation=20, labelsize=8)


def main() -> None:
    m = latest()
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    bars(
        axes[0][0],
        ["Postgres\n(disco)", "Valkey\n(RAM, extrapolado)"],
        [val(m, "1-carga", "postgres", "disco_total"),
         val(m, "1-carga", "valkey", "ram_extrapolada_total")],
        [PG, VK], "Paso 1 · Espacio para todo el mes", "MiB",
    )
    bars(
        axes[0][1],
        ["Postgres\nsubconjunto", "Valkey\nagregado en cliente", "Postgres\ntabla completa"],
        [val(m, "2-olap", "postgres", "mediana_subconjunto"),
         val(m, "2-olap", "valkey", "agregado_en_cliente"),
         val(m, "2-olap", "postgres", "mediana_completa")],
        [PG, VK, PG], "Paso 2 · GROUP BY payment_type", "ms (log)", log=True,
    )
    bars(
        axes[1][0],
        ["PG lectura", "VK lectura", "PG update", "VK update"],
        [val(m, "3a-puntual", "postgres", "lectura_por_llave_p50"),
         val(m, "3a-puntual", "valkey", "lectura_por_llave_p50"),
         val(m, "3a-puntual", "postgres", "update_por_llave_p50"),
         val(m, "3a-puntual", "valkey", "update_por_llave_p50")],
        [PG, VK, PG, VK], "Paso 3a · Operación por llave (p50)", "ms",
    )
    feed = [
        ("PG commit\npor mensaje", "postgres_commit_por_mensaje", PG),
        ("PG commit\nasíncrono", "postgres_commit_asincrono", PG),
        ("PG lote", "postgres_lote", PG),
        ("VK por\nmensaje", "valkey_por_mensaje", VK),
        ("VK AOF\nalways", "valkey_aof_always", VK),
        ("VK pipeline", "valkey_pipeline", VK),
    ]
    bars(
        axes[1][1],
        [f[0] for f in feed],
        [val(m, "3b-feed", f[1], "mensajes_por_s") for f in feed],
        [f[2] for f in feed], "Paso 3b · Feed del paper (Figura 3)", "mensajes/s (log)", log=True,
    )
    fig.suptitle("¿Una talla para todos? Postgres 16 (relacional) vs Valkey 8 (clave-valor)")
    fig.tight_layout()
    out = EVIDENCE / "graficas.png"
    fig.savefig(out, dpi=130)
    print(f"Gráfica: {out}")

    lines = ["| Paso | Motor | Métrica | Valor | Unidad |", "| --- | --- | --- | ---: | --- |"]
    for (paso, motor, metrica), row in sorted(m.items()):
        lines.append(f"| {paso} | {motor} | {metrica} | {row['valor']:,.3f} | {row['unidad']} |")
    (EVIDENCE / "tabla.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Tabla: {EVIDENCE / 'tabla.md'}")


if __name__ == "__main__":
    main()
