"""Stocks : une photo par jour, produit et entrepôt.

On simule vraiment le stock : il baisse avec les ventes et remonte avec les
réapprovisionnements. Quelques produits sont volontairement mal approvisionnés
(ruptures fréquentes) et l'entrepôt lent est réapprovisionné plus tard.
"""
import numpy as np
import pandas as pd

from data_generation import config


def simulate_inventory(rng, orders, items, products, suppliers, warehouses):
    story = config.STORY
    days = pd.date_range(config.START_DATE, config.NEXT_DAY)
    D, P, W = len(days), len(products), len(warehouses)
    p_index = {pid: i for i, pid in enumerate(products["product_id"])}
    w_index = {wid: i for i, wid in enumerate(warehouses["warehouse_id"])}

    # Ventes (en unités) par jour, produit et entrepôt
    ok = orders.loc[~orders["is_cancelled"], ["order_id", "order_date", "warehouse_id"]]
    sales = items.merge(ok, on="order_id")
    d_idx = (sales["order_date"] - days[0]).dt.days.to_numpy()
    p_idx = sales["product_id"].map(p_index).to_numpy()
    w_idx = sales["warehouse_id"].map(w_index).to_numpy()
    S = np.zeros((D, P, W), dtype=np.int32)
    np.add.at(S, (d_idx, p_idx, w_idx), sales["quantity"].to_numpy())
    demand = S.mean(axis=0)                                  # demande moyenne par jour

    # Délai de réapprovisionnement : celui du fournisseur (+ retard de l'entrepôt lent)
    lead_p = np.maximum(2, products["supplier_id"].map(
        suppliers.set_index("supplier_id")["standard_lead_time_days"]).to_numpy().astype(int))
    extra = np.array([story["slow_warehouse_restock_delay"] if w == story["slow_warehouse"] else 0
                      for w in warehouses["warehouse_id"]])
    lead = lead_p[:, None] + extra[None, :]

    # Produits "sujets à rupture" : pris parmi les produits qui se vendent bien
    total = demand.sum(axis=1)
    top = np.argsort(total)[::-1][: max(story["n_stockout_prone_products"] * 3, 10)]
    prone = rng.choice(top, size=min(story["n_stockout_prone_products"], len(top)), replace=False)
    safety = np.ones(P)
    safety[prone] = 0.30

    reorder_point = np.ceil(demand * (lead + 4) * safety[:, None]).astype(int) + 2
    target = reorder_point + np.ceil(demand * 21 * safety[:, None]).astype(int) + 8

    stock = target.copy()
    on_order = np.zeros((P, W), dtype=int)
    incoming = np.zeros((D + int(lead.max()) + 2, P, W), dtype=int)
    out = np.empty((D, P, W), dtype=np.int32)
    pp, ww = np.meshgrid(np.arange(P), np.arange(W), indexing="ij")

    for d in range(D):
        arrived = incoming[d]
        stock = stock + arrived
        on_order = on_order - arrived
        stock = np.maximum(stock - S[d], 0)                  # on ne vend pas plus que le stock
        position = stock + on_order
        need = position <= reorder_point
        if need.any():
            qty = np.where(need, target - position, 0)
            np.add.at(incoming, (d + lead[need], pp[need], ww[need]), qty[need])
            on_order = on_order + qty
        out[d] = stock

    df = pd.DataFrame({
        "snapshot_date": np.repeat(days.values, P * W),
        "product_id": np.tile(np.repeat(products["product_id"].to_numpy(), W), D),
        "warehouse_id": np.tile(np.tile(warehouses["warehouse_id"].to_numpy(), P), D),
        "quantity_on_hand": out.reshape(-1),
    })
    # Un produit n'a pas de stock avant son ajout au catalogue
    created = np.tile(np.repeat(products["created_date"].to_numpy(), W), D)
    df = df.loc[df["snapshot_date"].to_numpy() >= created].reset_index(drop=True)
    return df, products["product_id"].to_numpy()[prone].tolist()
