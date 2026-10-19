"""Retient quels lots sont déjà chargés (table audit.batch_log)."""


def already_loaded(conn, batch_id, table):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM audit.batch_log WHERE batch_id = %s AND table_name = %s "
                    "AND status = 'loaded'", (batch_id, table))
        return cur.fetchone() is not None


def log_batch(conn, batch_id, table, source_file, rows):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO audit.batch_log (batch_id, table_name, source_file, rows_loaded) "
                    "VALUES (%s, %s, %s, %s)", (batch_id, table, source_file, rows))
