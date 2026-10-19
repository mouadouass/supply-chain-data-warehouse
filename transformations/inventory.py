"""Stocks : Bronze vers Silver."""
from transformations.common.cleaning import batch_date, clean_text, to_integer
from transformations.common.dates import parse_dates
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "inventory", ["snapshot_date", "product_id", "warehouse_id"]
FINAL = ["snapshot_date", "product_id", "warehouse_id", "quantity_on_hand", "batch_id"]


def clean(raw):
    df = raw.copy()
    for c in ["snapshot_date", "product_id", "warehouse_id", "quantity_on_hand"]:
        df[c] = clean_text(df[c])
    snapshot = parse_dates(df["snapshot_date"])
    quantity, q_ok = to_integer(df["quantity_on_hand"])
    reasons = first_reason(df.index, [
        (df["product_id"].isna(), "produit manquant"),
        (df["warehouse_id"].isna(), "entrepôt manquant"),
        (snapshot.isna(), "date invalide"),
        (snapshot > batch_date(df["batch_id"]), "date dans le futur"),
        (~q_ok, "quantité invalide ou manquante"),
        (quantity < 0, "quantité négative"),
    ])
    df["snapshot_date"], df["quantity_on_hand"] = snapshot, quantity
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "09_silver_inventory.sql")