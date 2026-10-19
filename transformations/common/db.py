"""Lecture de Bronze et chargement rapide dans les tables de passage."""
import io

import numpy as np
import pandas as pd


def read_bronze(conn, table, source_columns):
    cols = source_columns + ["batch_id", "source_file", "row_number_in_file"]
    with conn.cursor() as cur:
        cur.execute(f"SELECT {', '.join(cols)} FROM bronze.{table} "
                    "ORDER BY batch_id, row_number_in_file")
        return pd.DataFrame(cur.fetchall(), columns=cols)


def _field(value):
    if value is None or value is pd.NA or value is pd.NaT or (isinstance(value, float) and value != value):
        return ""                                  # NULL
    if isinstance(value, (int, np.integer)):
        return str(value)
    return '"' + str(value).replace('"', '""') + '"'


def copy_frame(conn, table, df, columns):
    """COPY d'un DataFrame typé dans une table (dates en texte ISO, NULL préservés)."""
    prepared = {}
    for c in columns:
        s = df[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            s = s.dt.strftime("%Y-%m-%d")
        prepared[c] = s.astype(object)
    out = pd.DataFrame(prepared, index=df.index)
    buffer = io.StringIO()
    for row in out.to_numpy(dtype=object):
        buffer.write(",".join(_field(v) for v in row) + "\n")
    buffer.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)", buffer)
    conn.commit()
