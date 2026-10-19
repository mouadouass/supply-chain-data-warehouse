"""Produits : Bronze vers Silver."""
from transformations.common.cleaning import batch_date, canonicalize, clean_text, to_number
from transformations.common.dates import parse_dates
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "products", ["product_id"]
FINAL = ["product_id", "product_name", "category", "brand", "unit_price", "supplier_id",
         "created_date", "batch_id"]
HISTORY = ["product_name", "category", "brand", "unit_price", "supplier_id", "created_date"]
CATEGORIES = ["Électronique", "Alimentation", "Maison", "Mode", "Hygiène et beauté", "Bureau"]


def clean(raw):
    df = raw.copy()
    for c in ["product_id", "product_name", "category", "brand", "unit_price", "supplier_id"]:
        df[c] = clean_text(df[c])
    df["category"] = canonicalize(df["category"], CATEGORIES)
    df["brand"] = df["brand"].fillna("Inconnu")
    price = to_number(df["unit_price"])
    created = parse_dates(df["created_date"])
    reasons = first_reason(df.index, [
        (df["product_id"].isna(), "identifiant manquant"),
        (df["product_name"].isna(), "nom manquant"),
        (df["category"].isna(), "catégorie inconnue"),
        (price.isna() & df["unit_price"].isna(), "prix manquant"),
        (price.isna(), "prix invalide"),
        (price < 0, "prix négatif"),
        (df["supplier_id"].isna(), "fournisseur manquant"),
        (created.isna(), "date de création invalide"),
        (created > batch_date(df["batch_id"]), "date de création dans le futur"),
    ])
    df["unit_price"], df["created_date"] = price, created
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "04_silver_products.sql", HISTORY)