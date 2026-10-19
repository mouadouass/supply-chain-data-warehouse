"""Quarantaine : les lignes invalides ne sont jamais supprimées en silence."""
import json

import pandas as pd
from psycopg2.extras import execute_values


def first_reason(index, checks):
    """Pour chaque ligne, le premier motif de rejet qui s'applique (sinon None).
    `checks` est une liste de (condition, motif)."""
    reason = pd.Series(None, index=index, dtype=object)
    for mask, text in checks:
        mask = mask.fillna(False).astype(bool)
        reason = reason.mask(reason.isna() & mask, text)
    return reason


def write_rejects(conn, table, raw_rows, reasons, source_columns):
    """Écrit dans silver.rejected_rows la ligne ORIGINALE (telle qu'elle était dans Bronze)."""
    if len(raw_rows) == 0:
        return
    rows = []
    for idx, row in raw_rows.iterrows():
        original = {c: (None if pd.isna(row[c]) else row[c]) for c in source_columns}
        rows.append((table, reasons[idx], row["batch_id"], row["source_file"],
                     int(row["row_number_in_file"]), json.dumps(original, ensure_ascii=False)))
    with conn.cursor() as cur:
        execute_values(cur,
                       "INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, "
                       "source_file, row_number_in_file, raw_data) VALUES %s", rows,
                       template="(%s,%s,%s,%s,%s,%s::jsonb)", page_size=5000)
    conn.commit()
