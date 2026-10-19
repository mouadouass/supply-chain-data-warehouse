"""Livraisons : une par commande non annulée.

L'histoire racontée : deux fournisseurs souvent en retard, un entrepôt plus lent,
et davantage de retards en novembre-décembre (la période de pointe).
"""
import numpy as np
import pandas as pd

from data_generation import config
from data_generation.utils.writers import read_reference


def generate_deliveries(rng, orders, items, products, suppliers):
    story = config.STORY
    carriers = read_reference("carriers.csv")

    o = orders.loc[~orders["is_cancelled"]].copy()

    # Fournisseur principal = celui du produit au montant le plus élevé de la commande
    it = items.assign(amount=items["quantity"] * items["unit_price"]).merge(
        products[["product_id", "supplier_id"]], on="product_id")
    main = it.loc[it.groupby("order_id")["amount"].idxmax(), ["order_id", "supplier_id"]]
    o = o.merge(main, on="order_id").reset_index(drop=True)
    n = len(o)

    lead = o["supplier_id"].map(suppliers.set_index("supplier_id")["standard_lead_time_days"]).to_numpy()
    is_slow = (o["warehouse_id"] == story["slow_warehouse"]).to_numpy()

    ship_delay = rng.choice([0, 1, 2, 3], size=n, p=[0.35, 0.40, 0.18, 0.07])
    ship_delay = ship_delay + is_slow * story["slow_warehouse_ship_delay"]
    ship = o["order_date"] + pd.to_timedelta(ship_delay, unit="D")
    expected = ship + pd.to_timedelta(lead, unit="D")

    p_late = np.full(n, story["base_late_probability"])
    for sid, prob in story["late_suppliers"].items():
        p_late[(o["supplier_id"] == sid).to_numpy()] = prob
    p_late = p_late + is_slow * story["slow_warehouse_late_bonus"]
    p_late = p_late + o["order_date"].dt.month.isin(story["peak_months"]).to_numpy() * story["peak_months_late_bonus"]
    p_late = np.clip(p_late, 0, 0.85)

    late = rng.random(n) < p_late
    delay = np.where(late, rng.integers(1, 6, n), rng.choice([-1, 0, 0, 0], size=n))
    actual = expected + pd.to_timedelta(delay, unit="D")

    carrier = rng.choice(carriers["carrier_name"].to_numpy(), size=n,
                         p=carriers["weight"] / carriers["weight"].sum())
    return pd.DataFrame({
        "delivery_id": [f"D{i + 1:06d}" for i in range(n)],
        "order_id": o["order_id"], "warehouse_id": o["warehouse_id"],
        "supplier_id": o["supplier_id"], "carrier": carrier,
        "ship_date": ship, "expected_delivery_date": expected, "actual_delivery_date": actual,
    })
