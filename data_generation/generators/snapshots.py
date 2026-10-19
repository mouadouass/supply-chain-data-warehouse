"""Transforme le "monde complet" en lots de fichiers livrés par l'entreprise.

- Un LOT DE BASE : tout l'historique jusqu'à BASE_END_DATE.
- Puis UN LOT PAR JOUR : ce qui est nouveau ou modifié ce jour-là (nouvelles commandes, statuts
  qui changent, stocks du jour). Les tables de référence (clients, fournisseurs, produits,
  entrepôts) sont renvoyées en entier à chaque lot.
"""
import numpy as np
import pandas as pd

from data_generation import config
from data_generation.defects.supplier_changes import relocate_suppliers


def build_snapshot(world, asof):
    """L'état de l'entreprise à la fin du jour `asof` (sert au lot de base)."""
    asof = pd.Timestamp(asof)
    customers = world["customers"].loc[world["customers"]["registration_date"] <= asof].copy()
    orders = world["orders"].loc[world["orders"]["order_date"] <= asof].copy()
    deliveries = world["deliveries"]
    deliveries = deliveries.loc[deliveries["order_id"].isin(orders["order_id"])
                                & (deliveries["ship_date"] <= asof)].copy()

    delivered = deliveries["actual_delivery_date"] <= asof
    deliveries["delivery_status"] = np.where(delivered, "Livrée", "En transit")
    deliveries.loc[~delivered, "actual_delivery_date"] = pd.NaT

    # Statut d'une commande : déduit de sa livraison
    from_delivery = deliveries.set_index("order_id")["delivery_status"].map(
        {"Livrée": "Livrée", "En transit": "Expédiée"})
    orders["status"] = orders["order_id"].map(from_delivery).fillna("En cours")
    orders.loc[orders["is_cancelled"], "status"] = "Annulée"

    items = world["items"].loc[world["items"]["order_id"].isin(orders["order_id"])]
    inventory = world["inventory"].loc[world["inventory"]["snapshot_date"] <= asof]

    tables = {
        "customers": customers, "suppliers": world["suppliers"].copy(),
        "warehouses": world["warehouses"].copy(),
        "products": world["products"].loc[world["products"]["created_date"] <= asof].copy(),
        "orders": orders, "order_items": items, "deliveries": deliveries, "inventory": inventory,
    }
    return _to_source_format(tables)


def build_daily_lot(world, day):
    """Ce que la source livre pour UN jour : nouvelles commandes, commandes dont le statut change
    (expédiée ou livrée ce jour-là), livraisons parties ou arrivées, stocks du soir."""
    day = pd.Timestamp(day)
    orders, deliveries = world["orders"], world["deliveries"]

    moved = deliveries.loc[(deliveries["ship_date"] == day) | (deliveries["actual_delivery_date"] == day)]
    order_ids = set(orders.loc[orders["order_date"] == day, "order_id"]) | set(moved["order_id"])
    o = orders.loc[orders["order_id"].isin(order_ids)].copy()

    known = deliveries.loc[deliveries["order_id"].isin(order_ids) & (deliveries["ship_date"] <= day)].copy()
    delivered = known["actual_delivery_date"] <= day
    known["delivery_status"] = np.where(delivered, "Livrée", "En transit")
    known.loc[~delivered, "actual_delivery_date"] = pd.NaT
    status = known.set_index("order_id")["delivery_status"].map({"Livrée": "Livrée", "En transit": "Expédiée"})
    o["status"] = o["order_id"].map(status).fillna("En cours")
    o.loc[o["is_cancelled"], "status"] = "Annulée"

    new_order_ids = orders.loc[orders["order_date"] == day, "order_id"]
    tables = {
        "customers": world["customers"].loc[world["customers"]["registration_date"] <= day].copy(),
        "suppliers": world["suppliers"].copy(),
        "warehouses": world["warehouses"].copy(),
        "products": world["products"].loc[world["products"]["created_date"] <= day].copy(),
        "orders": o,
        "order_items": world["items"].loc[world["items"]["order_id"].isin(new_order_ids)],
        "deliveries": known.loc[known["delivery_id"].isin(moved["delivery_id"])],
        "inventory": world["inventory"].loc[world["inventory"]["snapshot_date"] == day],
    }
    return _to_source_format(tables)


def _to_source_format(tables):
    out = {}
    for name, df in tables.items():
        df = df[config.COLUMNS[name]].copy()
        for col in config.DATE_COLUMNS.get(name, []):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        out[name] = df.reset_index(drop=True)
    return out


def build_lots(world):
    """Retourne (lot de base, [(nom du lot, tables, événements), ...] un par jour)."""
    base = build_snapshot(world, config.BASE_END_DATE)
    days = pd.date_range(pd.Timestamp(config.BASE_END_DATE) + pd.Timedelta(days=1), config.NEXT_DAY)
    dailies = []
    for i, day in enumerate(days):
        tables, events = build_daily_lot(world, day), []
        if i == len(days) - 1:                       # les fournisseurs déménagent dans le dernier lot
            tables["suppliers"], events = relocate_suppliers(tables["suppliers"])
        dailies.append(((day + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), tables, events))
    return base, dailies