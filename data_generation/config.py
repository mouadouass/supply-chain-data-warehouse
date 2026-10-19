"""Réglages de la génération des données.

Tout ce que l'on peut vouloir changer (volumes, période, taux de défauts,
histoire racontée par les données) se règle ICI et nulle part ailleurs.
"""
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------- Chemins
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = Path(__file__).resolve().parent / "reference"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean_reference"
TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"
INCOMING_DIR = PROJECT_ROOT / "data" / "incoming"      # lots quotidiens en attente de livraison
# ------------------------------------------------------- Reproductibilité
# Même SEED = exactement les mêmes données à chaque lancement.
SEED = 42

# ----------------------------------------------------------------- Période
START_DATE = date(2024, 10, 1)      # premier jour de l'historique
END_DATE = date(2026, 9, 30)        # dernier jour du lot 1
NEXT_DAY = date(2026, 10, 1)        # le jour de données apporté par le lot 2
# Livraison quotidienne : un lot de base (tout l'historique jusqu'à BASE_END_DATE), puis un lot
# par jour, de BASE_END_DATE + 1 jour jusqu'à NEXT_DAY. Un lot est nommé du jour de sa livraison
# (le lendemain des données qu'il contient).
BASE_END_DATE = date(2026, 8, 31)   # dernier jour de données du lot de base
BASE_LOT = "2026-09-01"             # nom du lot de base
STRESS_LOT = "stress_test"          # lot volontairement très défectueux

# ----------------------------------------------------------------- Volumes
N_CUSTOMERS = 1000
N_SUPPLIERS = 20
N_PRODUCTS = 200
N_ORDERS = 50_000                   # commandes sur la période START_DATE..END_DATE
CUSTOMER_REG_START = date(2023, 1, 1)
NEW_CUSTOMERS_LOT_2 = 3             # clients qui s'inscrivent le 01/10

# ------------------------------------------------------ Fournisseurs étrangers
FOREIGN_SUPPLIERS = [("Madrid", "Espagne"), ("Valence", "Espagne"),
                     ("Lyon", "France"), ("Shenzhen", "Chine")]

# --------------------------------------------------------------- Entrepôts
WAREHOUSES = [
    ("W01", "Entrepôt Casablanca", "Casablanca"),
    ("W02", "Entrepôt Tanger", "Tanger"),
    ("W03", "Entrepôt Fès", "Fès"),
    ("W04", "Entrepôt Oujda", "Oujda"),
    ("W05", "Entrepôt Marrakech", "Marrakech"),
]
# Entrepôt qui sert habituellement chaque région
REGION_TO_WAREHOUSE = {
    "Casablanca-Settat": "W01",
    "Rabat-Salé-Kénitra": "W01",
    "Tanger-Tétouan-Al Hoceïma": "W02",
    "Fès-Meknès": "W03",
    "Oriental": "W04",
    "Marrakech-Safi": "W05",
    "Souss-Massa": "W05",
    "Béni Mellal-Khénifra": "W05",
}

# ------------------------------------------------- Forme des ventes (saisonnalité)
SEASONALITY = {1: 0.90, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.00, 6: 1.05,
               7: 1.10, 8: 1.05, 9: 1.00, 10: 1.00, 11: 1.30, 12: 1.50}
WEEKDAY_FACTOR = [1.10, 1.05, 1.00, 1.00, 1.10, 0.80, 0.60]   # lundi..dimanche
GROWTH_OVER_PERIOD = 0.25           # +25 % de commandes entre le début et la fin
# Certaines catégories se vendent beaucoup plus à certains mois
CATEGORY_BOOSTS = {
    11: {"Électronique": 1.8}, 12: {"Électronique": 1.8},   # fêtes de fin d'année
    9: {"Bureau": 1.6},                                      # rentrée scolaire
}

# ------------------------------------------- L'histoire racontée par les données
STORY = {
    "cancel_rate": 0.06,
    "base_late_probability": 0.10,
    "late_suppliers": {"S004": 0.45, "S011": 0.35},   # fournisseurs toujours en retard
    "slow_warehouse": "W04",                          # entrepôt plus lent
    "slow_warehouse_late_bonus": 0.10,
    "slow_warehouse_ship_delay": 1,                   # +1 jour avant expédition
    "slow_warehouse_restock_delay": 3,                # réappro plus lent
    "peak_months_late_bonus": 0.10,                   # retards en novembre-décembre
    "peak_months": [11, 12],
    "n_stockout_prone_products": 6,                   # produits souvent en rupture
}
# Fournisseurs qui déménagent entre le lot 1 et le lot 2 (pour tester le SCD Type 2)
RELOCATING_SUPPLIERS = {"S002": "Rabat", "S009": "Agadir"}

# ----------------------------------------------------------- Taux de défauts
# nombre décimal (0.05) = proportion des lignes ; nombre entier (2) = nombre de lignes.
DEFECT_RATES = {
    "customers": {"exact_duplicates": 0.02, "case_duplicates": 0.01, "city_case": 0.15,
                  "city_missing": 0.03, "name_spaces": 0.05, "email_invalid": 0.03,
                  "date_mixed": 0.10},
    "suppliers": {"city_case": 0.10, "country_missing": 1, "negative_lead_time": 1,
                  "exact_duplicates": 1},
    "warehouses": {"city_case": 1, "name_spaces": 1},
    "products": {"exact_duplicates": 0.01, "category_typo": 0.05, "brand_missing": 0.03,
                 "price_negative": 0.01, "price_missing": 0.02, "supplier_orphan": 0.01},
    "orders": {"exact_duplicates": 0.015, "date_mixed": 0.15, "status_typo": 0.03,
               "future_date": 0.005, "customer_orphan": 0.01, "customer_missing": 0.005,
               "warehouse_orphan": 0.005},
    "order_items": {"exact_duplicates": 0.01, "quantity_invalid": 0.01,
                    "price_negative": 0.005, "price_missing": 0.005,
                    "product_orphan": 0.01, "order_orphan": 0.005},
    "deliveries": {"exact_duplicates": 0.01, "date_mixed": 0.10,
                   "delivered_without_arrival": 0.02, "arrival_before_ship": 0.01,
                   "order_orphan": 0.005, "cancelled_order_delivery": 0.005},
    "inventory": {"exact_duplicates": 0.01, "date_mixed": 0.05, "negative_quantity": 0.005,
                  "product_orphan": 0.0025, "warehouse_orphan": 0.0025,
                  "missing_days": 0.005},
}
STRESS_MULTIPLIER = 5               # le lot de test a 5 fois plus de défauts

# ------------------------------------------------- Colonnes finales de chaque table
COLUMNS = {
    "customers": ["customer_id", "customer_name", "customer_type", "email", "city",
                  "region", "registration_date"],
    "suppliers": ["supplier_id", "supplier_name", "city", "country",
                  "standard_lead_time_days"],
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
DATE_COLUMNS = {
    "customers": ["registration_date"], "products": ["created_date"],
    "orders": ["order_date"],
    "deliveries": ["ship_date", "expected_delivery_date", "actual_delivery_date"],
    "inventory": ["snapshot_date"],
}
