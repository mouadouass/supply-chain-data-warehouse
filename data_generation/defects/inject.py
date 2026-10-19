"""Injecte les défauts dans les données propres, et compte tout dans le rapport.

Règle importante : chaque ligne reçoit AU PLUS un défaut de valeur, et les doublons ne
copient que des lignes propres. Ainsi le rapport de vérité est exact.
"""
import numpy as np
import pandas as pd

from data_generation import config
from data_generation.defects import bad_formats, invalid_values, missing_values, orphans
from data_generation.defects.duplicates import case_variant_copies, exact_copies
from data_generation.utils.report import CORRIGE, DEDUP, REJETE, REMPLACE, SIGNALE
from data_generation.utils.seed import make_rng


class Injector:
    def __init__(self, df, table, rng, report, multiplier=1.0):
        self.df = df.reset_index(drop=True).astype(object)
        self.table, self.rng, self.report, self.mult = table, rng, report, multiplier
        self.rates = config.DEFECT_RATES[table]
        self.n0 = len(self.df)
        self.free = pd.Series(True, index=self.df.index)    # lignes encore sans défaut
        self.extra = []

    def _count(self, key):
        spec = self.rates[key]
        if isinstance(spec, int):
            return int(spec * self.mult)
        return int(round(spec * self.mult * self.n0))

    def _pick(self, key, where=None):
        mask = self.free.copy()
        if where is not None:
            mask &= where(self.df).reindex(self.free.index, fill_value=False).astype(bool)
        pool = mask.index[mask.to_numpy()].to_numpy()
        k = min(self._count(key), len(pool))
        return self.rng.choice(pool, size=k, replace=False) if k else np.array([], dtype=int)

    def apply(self, key, name, treatment, fn, where=None, **kw):
        idx = self._pick(key, where)
        fn(self.df, idx, self.rng, **kw)
        self.free.loc[idx] = False
        self.report.add(self.table, name, len(idx), treatment)

    def drop(self, key, name, treatment):
        idx = self._pick(key)
        self.df = self.df.drop(index=idx)
        self.free.loc[idx] = False
        self.report.add(self.table, name, len(idx), treatment)

    def add_rows(self, rows, name, treatment):
        self.extra.append(rows)
        self.report.add(self.table, name, len(rows), treatment)

    def duplicates(self, key, name, copy_fn=None, **kw):
        mask = self.free & self.free.index.isin(self.df.index)
        pool = mask.index[mask.to_numpy()].to_numpy()
        k = min(self._count(key), len(pool))
        idx = self.rng.choice(pool, size=k, replace=False) if k else np.array([], dtype=int)
        copies = copy_fn(self.df, idx, **kw) if copy_fn else exact_copies(self.df, idx)
        self.free.loc[idx] = False
        self.extra.append(copies)
        self.report.add(self.table, name, len(idx), DEDUP)

    def finish(self):
        out = pd.concat([self.df] + self.extra, ignore_index=True)
        self.report.record_counts(self.table, self.n0, len(out))
        return out


def _notna(column):
    return lambda d: d[column].notna() & (d[column] != "")


def inject_lot(tables, report, lot, multiplier=1.0):
    """Retourne les mêmes tables, mais salies."""
    def rng_for(table):
        return make_rng(config.SEED, f"defects:{lot}:{table}")

    dirty = {}

    # ---- customers
    i = Injector(tables["customers"], "customers", rng_for("customers"), report, multiplier)
    i.apply("city_case", "Ville en casse différente", CORRIGE, bad_formats.change_case, column="city")
    i.apply("city_missing", "Ville manquante", REMPLACE, missing_values.blank_values, column="city")
    i.apply("name_spaces", "Espaces parasites dans le nom", CORRIGE, bad_formats.add_spaces, column="customer_name")
    i.apply("email_invalid", "E-mail invalide (sans @)", REMPLACE, invalid_values.break_email, column="email")
    i.apply("date_mixed", "Date d'inscription en format mixte", CORRIGE, bad_formats.mix_date_formats, columns=["registration_date"])
    i.duplicates("exact_duplicates", "Doublon exact")
    i.duplicates("case_duplicates", "Doublon avec nom en majuscules", case_variant_copies, column="customer_name")
    dirty["customers"] = i.finish()

    # ---- suppliers
    i = Injector(tables["suppliers"], "suppliers", rng_for("suppliers"), report, multiplier)
    i.apply("city_case", "Ville en casse différente", CORRIGE, bad_formats.change_case, column="city")
    i.apply("country_missing", "Pays manquant", REMPLACE, missing_values.blank_values, column="country")
    i.apply("negative_lead_time", "Délai négatif", REJETE, invalid_values.make_negative, column="standard_lead_time_days")
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["suppliers"] = i.finish()

    # ---- warehouses
    i = Injector(tables["warehouses"], "warehouses", rng_for("warehouses"), report, multiplier)
    i.apply("city_case", "Ville en casse différente", CORRIGE, bad_formats.change_case, column="city")
    i.apply("name_spaces", "Espaces parasites dans le nom", CORRIGE, bad_formats.add_spaces, column="warehouse_name")
    dirty["warehouses"] = i.finish()

    # ---- products
    i = Injector(tables["products"], "products", rng_for("products"), report, multiplier)
    i.apply("category_typo", "Catégorie mal écrite", CORRIGE, bad_formats.misspell, column="category")
    i.apply("brand_missing", "Marque manquante", REMPLACE, missing_values.blank_values, column="brand")
    i.apply("price_negative", "Prix négatif", REJETE, invalid_values.make_negative, column="unit_price")
    i.apply("price_missing", "Prix manquant", REJETE, missing_values.blank_values, column="unit_price")
    i.apply("supplier_orphan", "Fournisseur inexistant (S999)", REJETE, orphans.orphan_keys, column="supplier_id", fake_value="S999")
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["products"] = i.finish()

    # ---- orders
    i = Injector(tables["orders"], "orders", rng_for("orders"), report, multiplier)
    i.apply("date_mixed", "Date en format mixte", CORRIGE, bad_formats.mix_date_formats, columns=["order_date"])
    i.apply("status_typo", "Statut mal écrit", CORRIGE, bad_formats.misspell, column="status")
    i.apply("future_date", "Date dans le futur", REJETE, invalid_values.future_dates, column="order_date")
    i.apply("customer_orphan", "Client inexistant (C99999)", REJETE, orphans.orphan_keys, column="customer_id", fake_value="C99999")
    i.apply("customer_missing", "Client manquant", REJETE, missing_values.blank_values, column="customer_id")
    i.apply("warehouse_orphan", "Entrepôt inexistant (W99)", REJETE, orphans.orphan_keys, column="warehouse_id", fake_value="W99")
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["orders"] = i.finish()

    # ---- order_items
    i = Injector(tables["order_items"], "order_items", rng_for("order_items"), report, multiplier)
    i.apply("quantity_invalid", "Quantité nulle ou négative", REJETE, invalid_values.zero_or_negative, column="quantity")
    i.apply("price_negative", "Prix négatif", REJETE, invalid_values.make_negative, column="unit_price")
    i.apply("price_missing", "Prix manquant", REJETE, missing_values.blank_values, column="unit_price")
    i.apply("product_orphan", "Produit inexistant (P9999)", REJETE, orphans.orphan_keys, column="product_id", fake_value="P9999")
    i.apply("order_orphan", "Commande inexistante (O999999)", REJETE, orphans.orphan_keys, column="order_id", fake_value="O999999")
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["order_items"] = i.finish()

    # ---- deliveries
    i = Injector(tables["deliveries"], "deliveries", rng_for("deliveries"), report, multiplier)
    i.apply("date_mixed", "Dates en format mixte", CORRIGE, bad_formats.mix_date_formats,
            columns=["ship_date", "expected_delivery_date", "actual_delivery_date"])
    i.apply("delivered_without_arrival", "Livrée sans date d'arrivée", SIGNALE, missing_values.blank_values,
            where=lambda d: (d["delivery_status"] == "Livrée") & d["actual_delivery_date"].notna(),
            column="actual_delivery_date")
    i.apply("arrival_before_ship", "Arrivée avant l'expédition", REJETE, invalid_values.arrival_before_ship,
            where=lambda d: (d["delivery_status"] == "Livrée") & d["actual_delivery_date"].notna())
    i.apply("order_orphan", "Commande inexistante (O999999)", REJETE, orphans.orphan_keys, column="order_id", fake_value="O999999")
    cancelled = tables["orders"].loc[tables["orders"]["status"] == "Annulée", "order_id"].to_numpy()
    last_number = int(tables["deliveries"]["delivery_id"].str[1:].astype(int).max()) if len(tables["deliveries"]) else 0
    extra = orphans.deliveries_for_cancelled(i.df, i._count("cancelled_order_delivery"), i.rng, cancelled, last_number + 1_000)
    i.add_rows(extra, "Livraison d'une commande annulée", SIGNALE)
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["deliveries"] = i.finish()

    # ---- inventory
    i = Injector(tables["inventory"], "inventory", rng_for("inventory"), report, multiplier)
    i.apply("date_mixed", "Date en format mixte", CORRIGE, bad_formats.mix_date_formats, columns=["snapshot_date"])
    i.apply("negative_quantity", "Quantité négative", REJETE, invalid_values.make_negative, column="quantity_on_hand",
            where=lambda d: d["quantity_on_hand"] > 0)
    i.apply("product_orphan", "Produit inconnu (P9999)", REJETE, orphans.orphan_keys, column="product_id", fake_value="P9999")
    i.apply("warehouse_orphan", "Entrepôt inconnu (W99)", REJETE, orphans.orphan_keys, column="warehouse_id", fake_value="W99")
    i.drop("missing_days", "Jour manquant dans la série", SIGNALE)
    i.duplicates("exact_duplicates", "Doublon exact")
    dirty["inventory"] = i.finish()
    return dirty
