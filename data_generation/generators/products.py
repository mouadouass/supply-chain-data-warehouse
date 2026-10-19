"""Produits : le catalogue."""
import numpy as np
import pandas as pd

from data_generation import config
from data_generation.utils.writers import read_reference


def generate_products(rng, suppliers, n=None):
    n = n or config.N_PRODUCTS
    ref = read_reference("categories_brands.csv")
    type_idx = rng.permutation(np.resize(np.arange(len(ref)), n))   # tous les types sont représentés

    # Quelques fournisseurs fournissent beaucoup de produits, d'autres très peu
    sup_w = rng.pareto(1.3, len(suppliers)) + 1
    sup_ids = rng.choice(suppliers["supplier_id"].to_numpy(), size=n, p=sup_w / sup_w.sum())

    old = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 640, n), unit="D")
    new = pd.Timestamp("2024-10-01") + pd.to_timedelta(rng.integers(0, 520, n), unit="D")
    created = np.where(rng.random(n) < 0.85, old, new)

    rows = []
    for i in range(n):
        r = ref.iloc[type_idx[i]]
        brand = r["brands"].split("|")[rng.integers(len(r["brands"].split("|")))]
        code = f"{chr(65 + rng.integers(0, 26))}{rng.integers(100, 1000)}"
        price = round(float(rng.uniform(r["price_min"], r["price_max"])) * 2) / 2
        rows.append((f"P{i + 1:04d}", f"{r['product_type']} {brand} {code}", r["category"],
                     brand, price, sup_ids[i], created[i]))
    df = pd.DataFrame(rows, columns=config.COLUMNS["products"])
    df["created_date"] = pd.to_datetime(df["created_date"])
    return df
