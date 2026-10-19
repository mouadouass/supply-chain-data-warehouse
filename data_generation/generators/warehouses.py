"""Entrepôts : où la marchandise est stockée."""
import pandas as pd

from data_generation import config
from data_generation.utils.writers import read_reference


def generate_warehouses(rng):
    cities = read_reference("cities.csv").set_index("city")
    rows = []
    for wid, name, city in config.WAREHOUSES:
        capacity = int(rng.integers(20, 61)) * 1000
        rows.append((wid, name, city, cities.loc[city, "region"], capacity))
    return pd.DataFrame(rows, columns=config.COLUMNS["warehouses"])
