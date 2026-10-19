"""Lit les fichiers sources d'un lot. Aucune transformation : tout reste du texte."""
import json

import pandas as pd

from ingestion import config


def list_lots():
    """Les lots disponibles, du plus ancien au plus récent (sans le lot de test)."""
    return sorted(p.name for p in config.RAW_DIR.iterdir()
                  if p.is_dir() and p.name not in config.IGNORED_LOTS
                  and any(p.glob("*.csv")))


def _as_text(value):
    return None if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)


def read_table(lot, table):
    """Retourne (DataFrame de texte, nom du fichier source)."""
    path = config.RAW_DIR / lot / config.FILES[table]
    if path.suffix == ".json":
        records = json.loads(path.read_text(encoding="utf-8"))
        df = (pd.DataFrame(records) if records else pd.DataFrame(columns=config.COLUMNS[table]))
        df = df.astype(object).map(_as_text)
    else:
        # dtype=str et keep_default_na=False : "NULL", "N/A" et "" restent tels quels
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")

    expected = config.COLUMNS[table]
    if set(df.columns) != set(expected):
        raise ValueError(f"{path.name} : colonnes inattendues {list(df.columns)} (attendu {expected})")
    return df[expected], f"{lot}/{path.name}"
