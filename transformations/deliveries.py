"""Livraisons : Bronze vers Silver."""
from transformations.common.cleaning import canonicalize, clean_text
from transformations.common.dates import parse_dates
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "deliveries", ["delivery_id"]
FINAL = ["delivery_id", "order_id", "warehouse_id", "supplier_id", "carrier", "ship_date",
         "expected_delivery_date", "actual_delivery_date", "delivery_status", "batch_id"]
STATUSES = ["En transit", "Livrée"]


def clean(raw):
    df = raw.copy()
    for c in ["delivery_id", "order_id", "warehouse_id", "supplier_id", "carrier",
              "ship_date", "expected_delivery_date", "actual_delivery_date", "delivery_status"]:
        df[c] = clean_text(df[c])
    df["delivery_status"] = canonicalize(df["delivery_status"], STATUSES)
    ship = parse_dates(df["ship_date"])
    expected = parse_dates(df["expected_delivery_date"])
    actual = parse_dates(df["actual_delivery_date"])           # vide = pas encore arrivée
    reasons = first_reason(df.index, [
        (df["delivery_id"].isna(), "identifiant manquant"),
        (df["order_id"].isna(), "commande manquante"),
        (df["warehouse_id"].isna(), "entrepôt manquant"),
        (df["supplier_id"].isna(), "fournisseur manquant"),
        (ship.isna(), "date d'expédition invalide"),
        (expected.isna(), "date prévue invalide"),
        (actual.isna() & df["actual_delivery_date"].notna(), "date d'arrivée invalide"),
        (df["delivery_status"].isna(), "statut invalide"),
        (expected < ship, "date prévue avant l'expédition"),
        (actual < ship, "arrivée avant l'expédition"),
    ])
    df["ship_date"], df["expected_delivery_date"], df["actual_delivery_date"] = ship, expected, actual
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "08_silver_deliveries.sql")
