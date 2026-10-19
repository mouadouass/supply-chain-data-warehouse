"""Vérifie l'historisation SCD Type 2 dans Gold. Lance d'abord : python -m transformations.build_gold"""
import pytest

from ingestion.load_bronze import connect


@pytest.fixture()
def cur():
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM gold.dim_supplier")
        if cursor.fetchone()[0] == 0:
            pytest.skip("Gold est vide")
    except Exception:
        pytest.skip("base ou Gold non disponible")
    yield cursor
    conn.close()


def test_fournisseur_demenage_a_deux_versions(cur):
    cur.execute("SELECT city, start_date, end_date, is_current FROM gold.dim_supplier "
                "WHERE supplier_id = 'S002' ORDER BY start_date")
    rows = cur.fetchall()
    if len(rows) < 2:
        pytest.skip("le lot où S002 déménage (2026-10-02) n'est pas encore livré")
    old, new = rows
    assert str(old[1]) == "1900-01-01" and str(old[2]) == "2026-09-30" and old[3] is False
    assert str(new[1]) == "2026-10-01" and str(new[2]) == "9999-12-31" and new[3] is True
    assert old[0] != new[0]


def test_une_seule_version_actuelle_par_identifiant(cur):
    for table, key in [("dim_supplier", "supplier_id"), ("dim_product", "product_id"),
                       ("dim_customer", "customer_id")]:
        cur.execute(f"SELECT count(*) FROM (SELECT {key} FROM gold.{table} WHERE is_current "
                    f"GROUP BY 1 HAVING count(*) > 1) t")
        assert cur.fetchone()[0] == 0, table


def test_les_ventes_gardent_l_ancienne_ville(cur):
    cur.execute("SELECT count(*) FROM gold.fact_sales f JOIN gold.dim_supplier s USING (supplier_key) "
                "WHERE s.supplier_id = 'S002' AND f.date_key < 20261001 AND s.is_current")
    assert cur.fetchone()[0] == 0          # aucune vente d'avant le 1er octobre sur la version Rabat


def test_chaque_dimension_a_sa_ligne_inconnu(cur):
    for table, key in [("dim_date", "date_key"), ("dim_customer", "customer_key"),
                       ("dim_product", "product_key"), ("dim_supplier", "supplier_key"),
                       ("dim_warehouse", "warehouse_key")]:
        cur.execute(f"SELECT count(*) FROM gold.{table} WHERE {key} = -1")
        assert cur.fetchone()[0] == 1, table