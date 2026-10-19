"""Le déroulement commun à toutes les tables Silver."""
from ingestion import config
from ingestion.load_bronze import run_sql_file
from transformations.common import db, dedup, rejects

SQL_DIR = config.SQL_DIR / "silver"


def process_table(conn, name, clean, key, final_columns, sql_file, history_cols=None):
    """1. lit Bronze  2. nettoie et valide  3. quarantaine  4. déduplique
    5. charge la table de passage  6. SQL : vérifie les références et insère."""
    source_columns = config.COLUMNS[name]
    raw = db.read_bronze(conn, name, source_columns)
    typed, reasons = clean(raw)

    bad = reasons.notna()
    rejects.write_rejects(conn, name, raw[bad], reasons[bad], source_columns)

    valid = typed.loc[~bad]
    if history_cols:
        kept, removed = dedup.keep_versions(valid, key, history_cols)
    else:
        kept, removed = dedup.keep_latest(valid, key)

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE silver.stg_{name}")
    db.copy_frame(conn, f"silver.stg_{name}", kept,
                  final_columns + ["source_file", "row_number_in_file"])
    run_sql_file(conn, SQL_DIR / sql_file)

    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM silver.{name}")
        silver_rows = cur.fetchone()[0]
        stats = dict(table_name=name, bronze_rows=len(raw), rejected_row_level=int(bad.sum()),
                     duplicates_removed=int(removed), rejected_fk=len(kept) - silver_rows,
                     silver_rows=silver_rows)
        cur.execute("INSERT INTO audit.silver_log (table_name, bronze_rows, rejected_row_level, "
                    "duplicates_removed, rejected_fk, silver_rows) VALUES "
                    "(%(table_name)s, %(bronze_rows)s, %(rejected_row_level)s, "
                    "%(duplicates_removed)s, %(rejected_fk)s, %(silver_rows)s)", stats)
    conn.commit()
    return stats
