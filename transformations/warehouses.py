"""Entrepôts : Bronze vers Silver."""
from transformations.common.cities import region_for, standardize_city
from transformations.common.cleaning import clean_text, to_integer
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "warehouses", ["warehouse_id"]
FINAL = ["warehouse_id", "warehouse_name", "city", "region", "capacity_units", "batch_id"]
HISTORY = ["warehouse_name", "city", "region", "capacity_units"]


def clean(raw):
    df = raw.copy()
    for c in ["warehouse_id", "warehouse_name", "city", "region"]:
        df[c] = clean_text(df[c])
    city = standardize_city(df["city"])
    df["region"] = df["region"].where(df["region"].notna(), region_for(city)).fillna("Inconnu")
    df["city"] = city.fillna("Inconnu")
    capacity, valid = to_integer(df["capacity_units"])
    reasons = first_reason(df.index, [
        (df["warehouse_id"].isna(), "identifiant manquant"),
        (df["warehouse_name"].isna(), "nom manquant"),
        (~valid, "capacité invalide ou manquante"),
        (capacity <= 0, "capacité nulle ou négative"),
    ])
    df["capacity_units"] = capacity
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "06_silver_warehouses.sql", HISTORY)
