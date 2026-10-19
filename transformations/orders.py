"""Commandes : Bronze vers Silver."""
from transformations.common.cleaning import batch_date, canonicalize, clean_text
from transformations.common.dates import parse_dates
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "orders", ["order_id"]
FINAL = ["order_id", "customer_id", "warehouse_id", "order_date", "status", "batch_id"]
STATUSES = ["En cours", "Expédiée", "Livrée", "Annulée"]


def clean(raw):
    df = raw.copy()
    for c in ["order_id", "customer_id", "warehouse_id", "status"]:
        df[c] = clean_text(df[c])
    df["status"] = canonicalize(df["status"], STATUSES)
    ordered = parse_dates(df["order_date"])
    reasons = first_reason(df.index, [
        (df["order_id"].isna(), "identifiant manquant"),
        (df["customer_id"].isna(), "client manquant"),
        (df["warehouse_id"].isna(), "entrepôt manquant"),
        (ordered.isna(), "date de commande invalide"),
        (ordered > batch_date(df["batch_id"]), "date de commande dans le futur"),
        (df["status"].isna(), "statut invalide"),
    ])
    df["order_date"] = ordered
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "07_silver_orders.sql")