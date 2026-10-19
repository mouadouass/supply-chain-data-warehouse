"""Réconciliation Silver / Gold : prouve qu'aucune ligne n'est perdue ni dupliquée.

    python -m transformations.run_reconciliation

Code de sortie 1 si un écart est trouvé (Airflow arrêtera alors le pipeline).
"""
import sys
from datetime import datetime

from ingestion import config
from ingestion.load_bronze import connect

RECON_DIR = config.SQL_DIR / "reconciliation"
COLUMNS = ["check_id", "description", "expected", "actual"]
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS audit.reconciliation_results (
    id          bigserial PRIMARY KEY,
    run_id      text        NOT NULL,
    run_at      timestamptz NOT NULL DEFAULT now(),
    check_id    text        NOT NULL,
    description text        NOT NULL,
    expected    numeric,                 -- valeur côté Silver
    actual      numeric,                 -- valeur côté Gold
    difference  numeric,
    status      text        NOT NULL     -- 'OK' ou 'ECART'
)
"""


def evaluate(conn):
    """Exécute les contrôles des fichiers de sql/reconciliation/. Ne modifie rien."""
    results = []
    with conn.cursor() as cur:
        for path in sorted(RECON_DIR.glob("*.sql")):
            cur.execute(path.read_text(encoding="utf-8"))
            for row in cur.fetchall():
                r = dict(zip(COLUMNS, row))
                r["difference"] = r["actual"] - r["expected"]
                r["status"] = "OK" if r["difference"] == 0 else "ECART"
                results.append(r)
    return sorted(results, key=lambda r: r["check_id"])


def store(conn, results):
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO audit.reconciliation_results (run_id, check_id, description, expected, "
            "actual, difference, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(run_id, r["check_id"], r["description"], r["expected"], r["actual"],
              r["difference"], r["status"]) for r in results])
    conn.commit()
    return run_id


def main():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE)
        conn.commit()
        results = evaluate(conn)
        run_id = store(conn, results)
    finally:
        conn.close()

    gaps = [r for r in results if r["status"] == "ECART"]
    print(f"Réconciliation Silver / Gold (exécution {run_id}) : {len(results)} contrôles | "
          f"{len(results) - len(gaps)} OK | {len(gaps)} écarts\n")
    print(f"  {'statut':<7}{'contrôle':<13}{'Silver':>16}{'Gold':>16}  description")
    for r in results:
        print(f"  {r['status']:<7}{r['check_id']:<13}{r['expected']:>16,.2f}{r['actual']:>16,.2f}  "
              f"{r['description']}".replace(".00 ", "    ", 2))
    if gaps:
        print("\nÉCART TROUVÉ : Gold ne correspond pas à Silver. Pipeline arrêté.")
        sys.exit(1)
    print("\nSilver et Gold sont parfaitement réconciliés.")


if __name__ == "__main__":
    main()