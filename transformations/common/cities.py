"""Standardise les villes : NADOR, nador, Nador deviennent Nador."""
from functools import lru_cache

import pandas as pd

from ingestion import config
from transformations.common.cleaning import strip_accents

# Liste de référence partagée avec la génération des données
REFERENCE = config.PROJECT_ROOT / "data_generation" / "reference" / "cities.csv"
FOREIGN_CITIES = ["Madrid", "Valence", "Lyon", "Shenzhen"]


def _key(value):
    return " ".join(strip_accents(value).lower().split())


@lru_cache(maxsize=1)
def _reference():
    ref = pd.read_csv(REFERENCE, encoding="utf-8")
    canonical = {_key(c): c for c in ref["city"]}
    canonical.update({_key(c): c for c in FOREIGN_CITIES})
    return canonical, dict(zip(ref["city"], ref["region"]))


def standardize_city(series):
    canonical, _ = _reference()
    return series.map(lambda v: None if v is None or pd.isna(v)
                      else canonical.get(_key(v), str(v).strip().title()))


def region_for(city_series):
    _, regions = _reference()
    return city_series.map(lambda v: regions.get(v) if isinstance(v, str) else None)
