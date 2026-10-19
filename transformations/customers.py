"""Clients : Bronze vers Silver."""
from transformations.common.cities import region_for, standardize_city
from transformations.common.cleaning import (batch_date, canonicalize, clean_text, is_valid_email,
                                             normalize_name)
from transformations.common.dates import parse_dates
from transformations.common.rejects import first_reason
from transformations.common.runner import process_table

NAME, KEY = "customers", ["customer_id"]
FINAL = ["customer_id", "customer_name", "customer_type", "email", "city", "region",
         "registration_date", "batch_id"]
HISTORY = ["customer_name", "customer_type", "email", "city", "region", "registration_date"]


def clean(raw):
    df = raw.copy()
    for c in ["customer_id", "customer_name", "customer_type", "email", "city", "region"]:
        df[c] = clean_text(df[c])
    df["customer_name"] = normalize_name(df["customer_name"])
    df["customer_type"] = canonicalize(df["customer_type"], ["Particulier", "Entreprise"])
    df["email"] = df["email"].where(is_valid_email(df["email"]), None)       # e-mail invalide : vidé
    city = standardize_city(df["city"])
    df["region"] = df["region"].where(df["region"].notna(), region_for(city)).fillna("Inconnu")
    df["city"] = city.fillna("Inconnu")
    registered = parse_dates(df["registration_date"])
    lot_day = batch_date(df["batch_id"])
    reasons = first_reason(df.index, [
        (df["customer_id"].isna(), "identifiant manquant"),
        (df["customer_name"].isna(), "nom manquant"),
        (df["customer_type"].isna(), "type de client invalide"),
        (registered.isna(), "date d'inscription invalide"),
        (registered > lot_day, "date d'inscription dans le futur"),
    ])
    df["registration_date"] = registered
    return df, reasons


def run(conn):
    return process_table(conn, NAME, clean, KEY, FINAL, "03_silver_customers.sql", HISTORY)