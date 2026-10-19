"""Lecture des listes de référence et écriture des fichiers (CSV et JSON)."""
import json

import pandas as pd

from data_generation import config


def read_reference(filename):
    return pd.read_csv(config.REFERENCE_DIR / filename, encoding="utf-8")


def write_table(df, folder, name):
    """Écrit une table : JSON pour les livraisons (source API), CSV pour le reste."""
    folder.mkdir(parents=True, exist_ok=True)
    if name == "deliveries":
        path = folder / "deliveries.json"
        records = json.loads(df.to_json(orient="records", force_ascii=False))
        path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        path = folder / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
    return path


def write_lot(tables, folder):
    for name, df in tables.items():
        write_table(df, folder, name)
