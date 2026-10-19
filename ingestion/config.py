"""Connexion à la base et description des sources. Les secrets viennent du fichier .env."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INCOMING_DIR = PROJECT_ROOT / "data" / "incoming"
SQL_DIR = PROJECT_ROOT / "sql"
IGNORED_LOTS = {"stress_test"}          # lot de test : jamais chargé automatiquement


def _read_env_file():
    values = {}
    path = PROJECT_ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


_ENV = _read_env_file()


def _get(name, default=None):
    return os.environ.get(name) or _ENV.get(name) or default


# Depuis ton ordinateur, la base s'appelle "localhost" (pas "postgres").
DB = {
    "host": _get("POSTGRES_HOST", "localhost"),
    "port": int(_get("POSTGRES_PORT", "5432")),
    "dbname": _get("POSTGRES_DB", "supply_chain_dw"),
    "user": _get("POSTGRES_USER", "dw_user"),
    "password": _get("POSTGRES_PASSWORD"),
}

# table -> fichier source
FILES = {
    "customers": "customers.csv", "suppliers": "suppliers.csv",
    "warehouses": "warehouses.csv", "products": "products.csv",
    "orders": "orders.csv", "order_items": "order_items.csv",
    "deliveries": "deliveries.json", "inventory": "inventory.csv",
}

# Colonnes attendues dans chaque source (doivent correspondre au SQL Bronze)
COLUMNS = {
    "customers": ["customer_id", "customer_name", "customer_type", "email", "city",
                  "region", "registration_date"],
    "suppliers": ["supplier_id", "supplier_name", "city", "country", "standard_lead_time_days"],
    "warehouses": ["warehouse_id", "warehouse_name", "city", "region", "capacity_units"],
    "products": ["product_id", "product_name", "category", "brand", "unit_price",
                 "supplier_id", "created_date"],
    "orders": ["order_id", "customer_id", "warehouse_id", "order_date", "status"],
    "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    "deliveries": ["delivery_id", "order_id", "warehouse_id", "supplier_id", "carrier",
                   "ship_date", "expected_delivery_date", "actual_delivery_date",
                   "delivery_status"],
    "inventory": ["snapshot_date", "product_id", "warehouse_id", "quantity_on_hand"],
}
TECHNICAL_COLUMNS = ["batch_id", "source_file", "row_number_in_file"]
