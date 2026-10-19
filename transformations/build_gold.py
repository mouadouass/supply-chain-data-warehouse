"""Construit la couche Gold (Star Schema) à partir de Silver. Relançable : tout est reconstruit.

    python -m transformations.build_gold                  # vérifie d'abord la qualité
    python -m transformations.build_gold --skip-quality   # sans la vérification

Gold ne démarre pas si une règle qualité BLOQUANTE échoue.
"""
import argparse
import sys
import time

from ingestion import config
from ingestion.load_bronze import connect, run_sql_file
from quality.run_quality import evaluate

GOLD_DIR = config.SQL_DIR / "gold"
TABLES = ["dim_date", "dim_customer", "dim_product", "dim_supplier", "dim_warehouse",
          "fact_sales", "fact_delivery", "fact_inventory",
          "vw_sales_summary", "vw_delivery_performance", "vw_inventory_status"]
# Colonnes de clés des faits : combien de lignes pointent vers « Inconnu » (-1) ?
FACT_KEYS = {
    "fact_sales": ["customer_key", "product_key", "supplier_key", "warehouse_key"],
    "fact_delivery": ["customer_key", "supplier_key", "warehouse_key"],
    "fact_inventory": ["product_key", "warehouse_key"],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-quality", action="store_true")
    args = parser.parse_args()

    conn = connect()
    try:
        if not args.skip_quality:
            blocking = [r for r in evaluate(conn) if r["status"] == "ECHEC"]
            conn.rollback()
            if blocking:
                print("GOLD NON CONSTRUIT : des règles qualité bloquantes échouent :")
                for r in blocking:
                    print(f"  {r['rule_id']} {r['table_name']} : {r['description']}")
                sys.exit(1)
            print("Contrôles qualité : aucune règle bloquante en échec.\n")

        files = (sorted((GOLD_DIR / "dimensions").glob("*.sql")) +
                 sorted((GOLD_DIR / "facts").glob("*.sql")) +
                 sorted((config.SQL_DIR / "views").glob("*.sql")))     # vues pour Power BI
        for path in files:
            t0 = time.time()
            run_sql_file(conn, path)
            print(f"  {path.name:<28}{time.time() - t0:>6.1f} s")

        print(f"\n{'table':<18}{'lignes':>10}")
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"SELECT count(*) FROM gold.{table}")
                print(f"{table:<18}{cur.fetchone()[0]:>10,}")
            print("\nLignes de faits rattachées à « Inconnu » (clé -1) :")
            for table, keys in FACT_KEYS.items():
                counts = []
                for key in keys:
                    cur.execute(f"SELECT count(*) FROM gold.{table} WHERE {key} = -1")
                    counts.append(f"{key} = {cur.fetchone()[0]}")
                print(f"  {table:<16}" + " | ".join(counts))
    finally:
        conn.close()


if __name__ == "__main__":
    main()