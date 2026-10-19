"""Mauvais formats : casse, espaces, fautes de frappe, dates en formats mixtes."""
import unicodedata

import pandas as pd

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _strip_accents(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def change_case(df, idx, rng, column):
    for i in idx:
        v = str(df.at[i, column])
        df.at[i, column] = v.upper() if rng.random() < 0.5 else v.lower()


def add_spaces(df, idx, rng, column):
    for i in idx:
        df.at[i, column] = " " * int(rng.integers(1, 3)) + str(df.at[i, column]) + " " * int(rng.integers(1, 3))


def mix_date_formats(df, idx, rng, columns):
    """2026-10-01 devient 01/10/2026, 01-10-2026 ou 1 Oct 2026."""
    for col in columns:
        for i in idx:
            v = df.at[i, col]
            if pd.isna(v) or str(v) == "":
                continue
            y, m, d = str(v).split("-")
            choice = rng.integers(3)
            df.at[i, col] = (f"{d}/{m}/{y}" if choice == 0 else
                             f"{d}-{m}-{y}" if choice == 1 else f"{int(d)} {MONTHS[int(m) - 1]} {y}")


def misspell(df, idx, rng, column):
    """Livrée devient livree, LIVRÉE ou Livre."""
    for i in idx:
        v = str(df.at[i, column])
        choice = rng.integers(3)
        df.at[i, column] = (_strip_accents(v).lower() if choice == 0 else
                            v.upper() if choice == 1 else _strip_accents(v)[:-1])
