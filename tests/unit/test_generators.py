"""Tests de la génération : données reproductibles, cohérentes, et rapport de défauts exact."""
import pandas as pd
import pytest

from data_generation import config

from data_generation.defects.inject import inject_lot
from data_generation.generators.snapshots import build_lots
from data_generation.main import build_world
from data_generation.utils.report import DEDUP, DefectReport

SMALL = dict(n_customers=120, n_products=50, n_orders=3000)


@pytest.fixture(scope="module")
def world():
    return build_world(**SMALL)


@pytest.fixture(scope="module")
def lots(world):
    return build_lots(world)          # (lot de base, [(nom du lot, tables, événements), ...])


@pytest.fixture(scope="module")
def base(lots):
    return lots[0]


def test_meme_seed_memes_donnees(world):
    again = build_world(**SMALL)
    pd.testing.assert_frame_equal(world["orders"], again["orders"])
    pd.testing.assert_frame_equal(world["items"], again["items"])


def test_identifiants_uniques(base):
    lot1 = base
    for table, key in [("customers", "customer_id"), ("products", "product_id"),
                       ("orders", "order_id"), ("order_items", "order_item_id"),
                       ("deliveries", "delivery_id")]:
        assert lot1[table][key].is_unique, table


def test_cles_etrangeres_propres(base):
    lot1 = base
    assert lot1["orders"]["customer_id"].isin(lot1["customers"]["customer_id"]).all()
    assert lot1["order_items"]["product_id"].isin(lot1["products"]["product_id"]).all()
    assert lot1["order_items"]["order_id"].isin(lot1["orders"]["order_id"]).all()
    assert lot1["deliveries"]["order_id"].isin(lot1["orders"]["order_id"]).all()


def test_valeurs_propres(base):
    lot1 = base
    assert (lot1["order_items"]["quantity"] > 0).all()
    assert (lot1["order_items"]["unit_price"] >= 0).all()
    assert (lot1["inventory"]["quantity_on_hand"] >= 0).all()


def test_dates_livraison_coherentes(base):
    d = pd.DataFrame(base["deliveries"]).dropna(subset=["actual_delivery_date"])
    assert (d["actual_delivery_date"] >= d["ship_date"]).all()
    assert (d["expected_delivery_date"] >= d["ship_date"]).all()


def test_pas_de_livraison_pour_commande_annulee(base):
    lot1 = base
    cancelled = lot1["orders"].loc[lot1["orders"]["status"] == "Annulée", "order_id"]
    assert not lot1["deliveries"]["order_id"].isin(cancelled).any()


def test_un_lot_par_jour_nomme_du_lendemain(lots):
    names = [name for name, _, _ in lots[1]]
    assert len(names) == 31 and names[0] == "2026-09-02" and names[-1] == "2026-10-02"
    assert names == sorted(set(names))


def test_les_lots_quotidiens_couvrent_toutes_les_nouvelles_commandes(world, lots):
    new_orders = world["orders"].loc[world["orders"]["order_date"] > pd.Timestamp(config.BASE_END_DATE),
                                     "order_id"]
    expected = int(world["items"]["order_id"].isin(new_orders).sum())
    assert sum(len(tables["order_items"]) for _, tables, _ in lots[1]) == expected


def test_les_fournisseurs_demenagent_dans_le_dernier_lot(lots):
    base, dailies = lots
    _, last_tables, events = dailies[-1]
    before = base["suppliers"].set_index("supplier_id")["city"]
    after = last_tables["suppliers"].set_index("supplier_id")["city"]
    assert len(events) == 2 and (before != after).sum() == 2


def test_fournisseurs_en_retard_de_l_histoire(world):
    d = world["deliveries"]
    d = d.assign(late=d["actual_delivery_date"] > d["expected_delivery_date"])
    rate = d.groupby("supplier_id")["late"].mean()
    if "S004" not in rate.index or len(d[d["supplier_id"] == "S004"]) < 30:
        pytest.skip("pas assez de livraisons de S004 dans ce petit jeu de test")
    assert rate["S004"] > rate.drop(["S004", "S011"]).mean() * 2


def test_rapport_de_defauts_exact(base):
    lot1 = base
    report = DefectReport("test")
    dirty = inject_lot(lot1, report, "test")
    summary = report.summary().set_index("table")
    for table in dirty:
        added = len(dirty[table]) - len(lot1[table])
        d = report.defects()
        sub = d[d["table"] == table]
        dup = int(sub.loc[sub["expected_treatment"] == DEDUP, "rows_affected"].sum())
        extra = int(sub.loc[sub["defect"].str.contains("annulée"), "rows_affected"].sum())
        dropped = int(sub.loc[sub["defect"].str.contains("manquant dans la série"), "rows_affected"].sum())
        assert added == dup + extra - dropped, table
        assert summary.loc[table, "dirty_rows"] == len(dirty[table])