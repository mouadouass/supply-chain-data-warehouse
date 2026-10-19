"""Lance tous les contrôles qualité sur Silver et enregistre les résultats.

    python -m quality.run_quality          # affiche les règles en erreur
    python -m quality.run_quality --all    # affiche aussi les règles OK

Si une règle BLOQUANTE échoue, le programme se termine avec le code 1 : Airflow verra
l'échec et n'exécutera pas la suite (Gold).
"""
import argparse
import sys
from datetime import datetime

from ingestion import config
from ingestion.load_bronze import connect, run_sql_file

QUALITY_DIR = config.SQL_DIR / "quality"
COLUMNS = ["rule_id", "table_name", "description", "severity", "errors", "details"]


def evaluate(conn):
    """Exécute les règles (fichiers 02 à 09) et retourne la liste des résultats.
    Ne modifie rien dans la base."""
    results = []
    with conn.cursor() as cur:
        for path in sorted(QUALITY_DIR.glob("0[2-9]_*.sql")):
            cur.execute(path.read_text(encoding="utf-8"))
            for row in cur.fetchall():
                r = dict(zip(COLUMNS, row))
                r["errors"] = int(r["errors"])
                r["status"] = ("OK" if r["errors"] == 0 else
                               "ECHEC" if r["severity"] == "bloquant" else "AVERTISSEMENT")
                results.append(r)
    return sorted(results, key=lambda r: (r["rule_id"], r["table_name"]))


def store(conn, results):
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO audit.quality_results (run_id, rule_id, table_name, description, "
            "severity, errors, status, details) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(run_id, r["rule_id"], r["table_name"], r["description"], r["severity"],
              r["errors"], r["status"], r["details"]) for r in results])
    conn.commit()
    return run_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="affiche aussi les règles OK")
    args = parser.parse_args()

    conn = connect()
    try:
        run_sql_file(conn, QUALITY_DIR / "01_create_quality_results.sql")
        results = evaluate(conn)
        run_id = store(conn, results)
    finally:
        conn.close()

    failed = [r for r in results if r["status"] == "ECHEC"]
    warned = [r for r in results if r["status"] == "AVERTISSEMENT"]
    print(f"Contrôles qualité (exécution {run_id}) : {len(results)} règles | "
          f"{len(results) - len(failed) - len(warned)} OK | {len(warned)} avertissements | "
          f"{len(failed)} échecs bloquants\n")
    for r in results:
        if r["status"] == "OK" and not args.all:
            continue
        extra = f"  [{r['details']}]" if r["details"] else ""
        print(f"  {r['status']:<14}{r['rule_id']:<11}{r['table_name']:<12}"
              f"{r['errors']:>8,}  {r['description']}{extra}")

    if failed:
        print("\nPIPELINE ARRÊTÉ : au moins une règle bloquante a échoué.")
        sys.exit(1)
    print("\nAucune règle bloquante en échec : le pipeline peut continuer.")


if __name__ == "__main__":
    main()