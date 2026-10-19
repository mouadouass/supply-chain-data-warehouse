"""Construit toute la couche Silver à partir de Bronze (reconstruction complète, relançable).

Utilisation (depuis la racine du projet) :
    python -m transformations.run_silver
"""
import time

from ingestion import config
from ingestion.load_bronze import connect, run_sql_file
from transformations import (customers, deliveries, inventory, order_items, orders, products,
                             suppliers, warehouses)

# Ordre obligatoire : on ne peut vérifier une référence que si la table parente existe déjà.
STEPS = [customers, suppliers, warehouses, products, orders, order_items, deliveries, inventory]
TABLES = ["customers", "suppliers", "warehouses", "products", "orders", "order_items",
          "deliveries", "inventory"]


def reset(conn):
    names = [f"silver.{t}" for t in TABLES] + [f"silver.stg_{t}" for t in TABLES]
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {', '.join(names)}, silver.rejected_rows, audit.silver_log "
                    "RESTART IDENTITY")
    conn.commit()


def main():
    conn = connect()
    try:
        for f in ("01_create_silver_tables.sql", "02_create_rejected_tables.sql"):
            run_sql_file(conn, config.SQL_DIR / "silver" / f)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM bronze.customers")
            if cur.fetchone()[0] == 0:
                raise SystemExit("Bronze est vide : lance d'abord python -m ingestion.load_bronze")
        reset(conn)
        print(f"{'table':<12}{'Bronze':>10}{'rejetées':>10}{'doublons':>10}{'réf. KO':>9}{'Silver':>10}")
        for step in STEPS:
            t0 = time.time()
            s = step.run(conn)
            print(f"{s['table_name']:<12}{s['bronze_rows']:>10,}{s['rejected_row_level']:>10,}"
                  f"{s['duplicates_removed']:>10,}{s['rejected_fk']:>9,}{s['silver_rows']:>10,}"
                  f"   ({time.time() - t0:.1f} s)")
        with conn.cursor() as cur:
            cur.execute("SELECT table_name, reject_reason, count(*) FROM silver.rejected_rows "
                        "GROUP BY 1, 2 ORDER BY 1, 3 DESC")
            print("\nLignes en quarantaine (silver.rejected_rows), par motif :")
            for table, reason, n in cur.fetchall():
                print(f"  {table:<12}{reason:<40}{n:>6,}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
