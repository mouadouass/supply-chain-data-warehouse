"""Charge les fichiers de data/raw/ dans le schéma bronze, sans rien modifier.

Utilisation (depuis la racine du projet) :
    python -m ingestion.load_bronze                    # tous les lots pas encore chargés
    python -m ingestion.load_bronze --lot 2026-10-01   # un seul lot
    python -m ingestion.load_bronze --lot stress_test  # le lot de test (explicite)
    python -m ingestion.load_bronze --reset            # vide Bronze et le journal, puis recharge
"""
import argparse
import io
import time

import psycopg2

from ingestion import batch_tracking, config, extract

CHUNK = 100_000


def _field(value):
    """Texte entre guillemets ("" = texte vide), rien du tout = NULL."""
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return '"' + str(value).replace('"', '""') + '"'


def to_copy_buffer(df):
    buffer = io.StringIO()
    for row in df.to_numpy(dtype=object):
        buffer.write(",".join(_field(v) if v == v else "" for v in row) + "\n")
    buffer.seek(0)
    return buffer


def connect():
    if not config.DB["password"]:
        raise SystemExit("Mot de passe introuvable : vérifie le fichier .env à la racine.")
    return psycopg2.connect(**config.DB)


def run_sql_file(conn, path):
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        raise SystemExit(f"Le fichier {path.name} est vide : remplis-le d'abord.")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def init_database(conn):
    run_sql_file(conn, config.SQL_DIR / "00_schemas.sql")
    run_sql_file(conn, config.SQL_DIR / "bronze" / "01_create_bronze_tables.sql")


def reset(conn):
    with conn.cursor() as cur:
        for table in config.FILES:
            cur.execute(f"TRUNCATE bronze.{table}")
        cur.execute("TRUNCATE audit.batch_log")
    conn.commit()
    print("Bronze et journal des lots vidés.")


def load_table(conn, lot, table):
    """Charge une table d'un lot. Retourne le nombre de lignes, ou None si déjà chargé."""
    if batch_tracking.already_loaded(conn, lot, table):
        return None
    df, source_file = extract.read_table(lot, table)
    df["batch_id"] = lot
    df["source_file"] = source_file
    df["row_number_in_file"] = range(1, len(df) + 1)

    columns = ", ".join(config.COLUMNS[table] + config.TECHNICAL_COLUMNS)
    sql = f"COPY bronze.{table} ({columns}) FROM STDIN WITH (FORMAT csv)"
    try:
        with conn.cursor() as cur:
            for start in range(0, len(df), CHUNK):
                cur.copy_expert(sql, to_copy_buffer(df.iloc[start:start + CHUNK]))
            cur.execute(f"SELECT count(*) FROM bronze.{table} WHERE batch_id = %s", (lot,))
            in_db = cur.fetchone()[0]
        if in_db != len(df):
            raise RuntimeError(f"{table} : {len(df)} lignes dans le fichier, {in_db} en base")
        batch_tracking.log_batch(conn, lot, table, source_file, len(df))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lot", action="append", help="lot à charger (répétable)")
    parser.add_argument("--reset", action="store_true", help="vide Bronze avant de charger")
    args = parser.parse_args()

    conn = connect()
    try:
        init_database(conn)
        if args.reset:
            reset(conn)
        for lot in args.lot or extract.list_lots():
            print(f"\nLot {lot}")
            for table in config.FILES:
                start = time.time()
                rows = load_table(conn, lot, table)
                if rows is None:
                    print(f"  {table:<12} déjà chargé, ignoré")
                else:
                    print(f"  {table:<12} {rows:>9,} lignes chargées ({time.time() - start:.1f} s)")
        run_sql_file(conn, config.SQL_DIR / "bronze" / "02_bronze_indexes.sql")
        print("\nTerminé. Index créés.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
