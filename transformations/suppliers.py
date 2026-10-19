"""Fournisseurs : Bronze vers Silver."""
from transformations.common.cities import standardize_city
from transformations.common.cleaning import clean_text, to_integer
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "suppliers", ["supplier_id"]
FINAL = ["supplier_id", "supplier_name", "city", "country", "standard_lead_time_days", "batch_id"]
HISTORY = ["supplier_name", "city", "country", "standard_lead_time_days"]


def clean(raw):
    df = raw.copy()
    for c in ["supplier_id", "supplier_name", "city", "country"]:
        df[c] = clean_text(df[c])
    df["city"] = standardize_city(df["city"]).fillna("Inconnu")
    df["country"] = df["country"].fillna("Inconnu")
    lead, valid = to_integer(df["standard_lead_time_days"])
    reasons = first_reason(df.index, [
        (df["supplier_id"].isna(), "identifiant manquant"),
        (df["supplier_name"].isna(), "nom manquant"),
        (~valid, "délai invalide ou manquant"),
        (lead < 0, "délai négatif"),
    ])
    df["standard_lead_time_days"] = lead
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "05_silver_suppliers.sql", HISTORY)
