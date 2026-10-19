"""La réconciliation doit réussir sur des données saines, et détecter un écart volontaire.
Lance d'abord : python -m transformations.build_gold"""
import pytest

from ingestion.load_bronze import connect
from transformations.run_reconciliation import evaluate


@pytest.fixture()
def conn():
    try:
        connection = connect()
        with connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM gold.fact_sales")
            if cur.fetchone()[0] == 0:
                pytest.skip("Gold est vide")
    except Exception:
        pytest.skip("base ou Gold non disponible")
    yield connection
    connection.rollback()
    connection.close()


def test_silver_et_gold_sont_reconcilies(conn):
    assert [r["check_id"] for r in evaluate(conn) if r["status"] == "ECART"] == []


def test_une_vente_perdue_est_detectee(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM gold.fact_sales WHERE sales_key = (SELECT min(sales_key) FROM gold.fact_sales)")
    ecarts = {r["check_id"] for r in evaluate(conn) if r["status"] == "ECART"}
    assert {"R_SALES_001", "R_SALES_002", "R_SALES_007"} <= ecarts     # rollback à la fin : rien n'est gardé