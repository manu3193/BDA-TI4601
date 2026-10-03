#!/usr/bin/env python3
"""Descarga yellow_tripdata_2016-01.csv (Kaggle: elemento/nyc-yellow-taxi-trip-data).

El endpoint de descarga de Kaggle entrega el archivo como zip y no exige cuenta
para este dataset público. Si su red lo bloquea, use el CLI de Kaggle
(ver README) y deje el zip o el CSV en labs/lab2-one-size/data/.
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile

from common import CSV_NAME, DATA, KAGGLE_DATASET, ZIP_PATH

URL = f"https://www.kaggle.com/api/v1/datasets/download/{KAGGLE_DATASET}/{CSV_NAME}"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if (DATA / CSV_NAME).exists() or ZIP_PATH.exists():
        print("Ya existe el archivo en data/. No se descarga de nuevo.")
        return
    tmp = ZIP_PATH.with_suffix(".part")
    print(f"Descargando {URL}")
    with urllib.request.urlopen(URL, timeout=60) as resp, tmp.open("wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = shown = 0
        while chunk := resp.read(1 << 20):
            out.write(chunk)
            done += len(chunk)
            if total and (done - shown >= 25_000_000 or done == total):
                shown = done
                sys.stdout.write(f"\r  {done / 1e6:,.0f} / {total / 1e6:,.0f} MB")
                sys.stdout.flush()
    print()
    with zipfile.ZipFile(tmp) as zf:
        info = zf.getinfo(CSV_NAME)
        print(f"  {CSV_NAME}: {info.file_size / 1e9:.2f} GB sin comprimir")
    tmp.rename(ZIP_PATH)
    print(f"Listo: {ZIP_PATH}")


if __name__ == "__main__":
    main()
