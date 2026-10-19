"""Déduplication : garder la ligne la plus récente d'une clé (lot le plus récent, puis dernière
ligne du fichier)."""


import pandas as pd


def keep_latest(df, key):
    """Une seule ligne par clé. Retourne (lignes gardées, nombre de lignes écartées)."""
    kept = (df.sort_values(["batch_id", "row_number_in_file"])
              .drop_duplicates(key, keep="last"))
    return kept, len(df) - len(kept)


def keep_versions(df, key, value_cols):
    """Pour les tables maîtres : une ligne par clé ET par lot, et on ne garde une nouvelle
    version que si une valeur a changé depuis la version précédente."""
    last = (df.sort_values(["batch_id", "row_number_in_file"])
              .drop_duplicates(key + ["batch_id"], keep="last")
              .sort_values(key + ["batch_id"]))
    signature = last[value_cols].apply(
        lambda row: "|".join("" if pd.isna(v) else str(v) for v in row), axis=1)
    previous = signature.groupby([last[k] for k in key]).shift()
    keep = previous.isna() | (signature != previous)
    return last[keep], len(df) - int(keep.sum())
