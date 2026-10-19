"""Vérifie que les règles qualité détectent bien une mauvaise donnée.
Ces tests ont besoin de la base : lance d'abord Bronze puis Silver."""
import pytest

from ingestion.load_bronze import connect
from quality.run_quality import evaluate


@pytest.fixture()
def conn():
    try:
        connection = connect()
    except Exception:
        pytest.skip("base de données non disponible")
    yield connection
    connection.rollback()
    connection.close()


def _errors(results, rule_id):
    return sum(r["errors"] for r in results if r["rule_id"] == rule_id)


def test_silver_ne_viole_aucune_regle_bloquante(conn):
    failed = [r["rule_id"] for r in evaluate(conn) if r["status"] == "ECHEC"]
    assert failed == []


def test_commande_sans_client_est_detectee(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO silver.orders (order_id, customer_id, warehouse_id, order_date, "
                    "status, batch_id) VALUES ('O_TEST', 'C_INCONNU', 'W01', '2026-01-01', "
                    "'Livrée', '2026-10-01')")
    assert _errors(evaluate(conn), "Q_FK_001") == 1       # rollback à la fin : rien n'est gardé


def test_livraison_avant_la_commande_est_detectee(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO silver.orders (order_id, customer_id, warehouse_id, order_date, "
                    "status, batch_id) SELECT 'O_TEST', customer_id, 'W01', '2026-01-10', 'Livrée', "
                    "'2026-10-01' FROM silver.customers LIMIT 1")
        cur.execute("INSERT INTO silver.deliveries (delivery_id, order_id, warehouse_id, supplier_id, "
                    "ship_date, expected_delivery_date, delivery_status, batch_id) "
                    "SELECT 'D_TEST', 'O_TEST', 'W01', supplier_id, '2026-01-05', '2026-01-08', "
                    "'En transit', '2026-10-01' FROM silver.suppliers LIMIT 1")
    assert _errors(evaluate(conn), "Q_DATE_001") == 1