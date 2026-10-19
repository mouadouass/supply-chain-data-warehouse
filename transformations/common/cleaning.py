"""Outils de nettoyage réutilisables : texte, nombres, valeurs autorisées, e-mails."""
import unicodedata

import pandas as pd

NULL_TOKENS = {"", "null", "n/a", "na", "none", "nan", "<na>"}


def strip_accents(text):
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()


def clean_text(series):
    """Espaces inutiles supprimés ; '', NULL, N/A... deviennent une vraie valeur manquante."""
    s = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    s = s.mask(s.str.lower().isin(NULL_TOKENS))
    return s.astype(object).where(s.notna(), None)


def normalize_name(series):
    """ALI et EL AMRANI deviennent Ali et El Amrani (seulement si tout est en majuscules)."""
    def fix(v):
        return v.title() if isinstance(v, str) and v == v.upper() and any(c.isalpha() for c in v) else v
    return series.map(fix)


def canonicalize(series, allowed):
    """Corrige casse, accents et fautes de frappe vers la liste des valeurs autorisées.
    Retourne None si aucune valeur autorisée ne correspond."""
    keys = {a: strip_accents(a).lower() for a in allowed}

    def match(value):
        k = strip_accents(value).lower().strip()
        found = [a for a, ak in keys.items()
                 if k == ak or (len(k) >= 3 and len(k) >= len(ak) - 1 and ak.startswith(k))]
        return found[0] if len(found) == 1 else None

    mapping = {u: match(u) for u in series.dropna().unique()}
    result = series.map(mapping).astype(object)
    return result.where(result.notna(), None)


def is_valid_email(series):
    return series.astype("string").str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True, na=False)


def to_number(series):
    """Texte vers nombre ; NaN si ce n'est pas un nombre."""
    return pd.to_numeric(series.astype(object), errors="coerce")


def to_integer(series):
    """Retourne (nombres entiers en Int64, indicateur 'est un entier valide')."""
    num = to_number(series)
    valid = num.notna() & (num == num.round())
    return num.where(valid).astype("Int64"), valid
def batch_date(series):
    """Jour de référence d'un lot, pour détecter les dates dans le futur.
    Un lot dont le nom n'est pas une date (stress_test) est traité comme le lot du 2026-10-02."""
    parsed = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
    return parsed.fillna(pd.Timestamp("2026-10-02"))