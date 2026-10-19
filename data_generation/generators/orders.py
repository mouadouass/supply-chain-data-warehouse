"""Commandes et lignes de commande : le cœur de l'activité.

L'histoire racontée : plus de ventes en novembre-décembre, moins le week-end,
une croissance sur deux ans, quelques gros clients et quelques produits stars.
"""
import numpy as np
import pandas as pd

from data_generation import config

ITEM_COUNTS = np.array([1, 2, 3, 4, 5, 6])
ITEM_PROBS = np.array([0.35, 0.28, 0.18, 0.10, 0.06, 0.03])
QUANTITIES = np.array([1, 2, 3, 4, 5, 10])
QUANTITY_PROBS = np.array([0.50, 0.20, 0.12, 0.08, 0.06, 0.04])


def _category_boost(categories, month):
    boost = np.ones(len(categories))
    for category, factor in config.CATEGORY_BOOSTS.get(month, {}).items():
        boost[categories == category] = factor
    return boost


def generate_orders(rng, customers, products, warehouses, n_orders=None):
    """Retourne (orders, items). `orders` contient une colonne interne is_cancelled."""
    n_orders = n_orders or config.N_ORDERS
    days = pd.date_range(config.START_DATE, config.NEXT_DAY)
    n_days = len(days)

    trend = 1 + config.GROWTH_OVER_PERIOD * np.arange(n_days) / (n_days - 1)
    season = np.array([config.SEASONALITY[d.month] for d in days])
    weekday = np.array([config.WEEKDAY_FACTOR[d.weekday()] for d in days])
    factor = trend * season * weekday
    in_period = days <= pd.Timestamp(config.END_DATE)
    daily_counts = rng.poisson(factor / factor[in_period].sum() * n_orders)

    n_cust, n_prod = len(customers), len(products)
    cust_weight = rng.pareto(1.5, n_cust) + 1       # quelques gros clients
    prod_weight = rng.pareto(1.2, n_prod) + 1       # quelques produits stars
    reg = customers["registration_date"].to_numpy()
    created = products["created_date"].to_numpy()
    categories = products["category"].to_numpy()
    prices = products["unit_price"].to_numpy()
    cust_ids = customers["customer_id"].to_numpy()
    prod_ids = products["product_id"].to_numpy()
    wh_ids = warehouses["warehouse_id"].to_numpy()
    home_wh = customers["region"].map(config.REGION_TO_WAREHOUSE).fillna(wh_ids[0]).to_numpy()

    order_rows, item_rows = [], []
    order_n = item_n = 0
    for d, day in enumerate(days):
        count = int(daily_counts[d])
        if count == 0:
            continue
        day64 = day.to_datetime64()
        p_cust = cust_weight * (reg <= day64)
        buyers = rng.choice(n_cust, size=count, p=p_cust / p_cust.sum())
        p_prod = prod_weight * (created <= day64) * _category_boost(categories, day.month)
        n_available = int((p_prod > 0).sum())
        p_prod = p_prod / p_prod.sum()

        for b in buyers:
            order_n += 1
            oid = f"O{order_n:06d}"
            wh = home_wh[b] if rng.random() < 0.8 else wh_ids[rng.integers(len(wh_ids))]
            cancelled = bool(rng.random() < config.STORY["cancel_rate"])
            order_rows.append((oid, cust_ids[b], wh, day, cancelled))
            k = min(int(rng.choice(ITEM_COUNTS, p=ITEM_PROBS)), n_available)
            for pi in rng.choice(n_prod, size=k, replace=False, p=p_prod):
                item_n += 1
                qty = int(rng.choice(QUANTITIES, p=QUANTITY_PROBS))
                price = round(float(prices[pi] * rng.uniform(0.95, 1.05)), 2)
                item_rows.append((f"OI{item_n:07d}", oid, prod_ids[pi], qty, price))

    orders = pd.DataFrame(order_rows, columns=["order_id", "customer_id", "warehouse_id",
                                               "order_date", "is_cancelled"])
    items = pd.DataFrame(item_rows, columns=config.COLUMNS["order_items"])
    return orders, items
