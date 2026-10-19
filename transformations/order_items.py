"""Lignes de commande : Bronze vers Silver."""
from transformations.common.cleaning import clean_text, to_integer, to_number
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "order_items", ["order_item_id"]
FINAL = ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "batch_id"]


def clean(raw):
    df = raw.copy()
    for c in ["order_item_id", "order_id", "product_id", "quantity", "unit_price"]:
        df[c] = clean_text(df[c])
    quantity, q_ok = to_integer(df["quantity"])
    price = to_number(df["unit_price"])
    reasons = first_reason(df.index, [
        (df["order_item_id"].isna(), "identifiant manquant"),
        (df["order_id"].isna(), "commande manquante"),
        (df["product_id"].isna(), "produit manquant"),
        (~q_ok, "quantité invalide ou manquante"),
        (quantity <= 0, "quantité nulle ou négative"),
        (price.isna() & df["unit_price"].isna(), "prix manquant"),
        (price.isna(), "prix invalide"),
        (price < 0, "prix négatif"),
    ])
    df["quantity"], df["unit_price"] = quantity, price
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "10_silver_order_items.sql")
