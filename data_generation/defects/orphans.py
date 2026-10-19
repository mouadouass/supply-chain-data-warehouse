"""Clés orphelines : une référence vers quelque chose qui n'existe pas."""
import pandas as pd


def orphan_keys(df, idx, rng, column, fake_value):
    for i in idx:
        df.at[i, column] = fake_value


def deliveries_for_cancelled(df, n, rng, cancelled_order_ids, first_number):
    """Crée n livraisons rattachées à des commandes annulées (anomalie)."""
    n = min(n, len(cancelled_order_ids), len(df))
    if n == 0:
        return df.iloc[0:0].copy()
    rows = df.sample(n=n, random_state=int(rng.integers(1_000_000))).copy()
    rows["order_id"] = rng.choice(cancelled_order_ids, size=n, replace=False)
    rows["delivery_id"] = [f"D{first_number + k:06d}" for k in range(n)]
    return rows
