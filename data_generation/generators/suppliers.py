"""Fournisseurs : qui fournit les produits, et depuis où."""
import pandas as pd

from data_generation import config
from data_generation.utils.writers import read_reference


def generate_suppliers(rng, fake, n=None):
    n = n or config.N_SUPPLIERS
    cities = read_reference("cities.csv")
    n_foreign = min(len(config.FOREIGN_SUPPLIERS), n)
    n_domestic = n - n_foreign
    dom_idx = rng.choice(len(cities), size=n_domestic, p=cities["weight"] / cities["weight"].sum())

    rows = []
    for i in range(n):
        if i < n_domestic:
            city, country, lead = cities["city"].iloc[dom_idx[i]], "Maroc", int(rng.integers(2, 6))
        else:
            city, country = config.FOREIGN_SUPPLIERS[i - n_domestic]
            low, high = {"Espagne": (5, 9), "France": (6, 10), "Chine": (12, 19)}[country]
            lead = int(rng.integers(low, high))
        rows.append((f"S{i + 1:03d}", fake.company(), city, country, lead))
    return pd.DataFrame(rows, columns=config.COLUMNS["suppliers"])
