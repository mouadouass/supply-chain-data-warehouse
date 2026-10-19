-- QUARANTAINE : aucune ligne n'est supprimée en silence, elle est mise ici avec son motif.
CREATE TABLE IF NOT EXISTS silver.rejected_rows (
    id                 bigserial PRIMARY KEY,
    table_name         text NOT NULL,
    reject_reason      text NOT NULL,
    batch_id           text,
    source_file        text,
    row_number_in_file integer,
    raw_data           jsonb,
    rejected_at        timestamptz NOT NULL DEFAULT now()
);

-- Bilan de la dernière exécution, table par table.
CREATE TABLE IF NOT EXISTS audit.silver_log (
    table_name          text PRIMARY KEY,
    bronze_rows         integer,
    rejected_row_level  integer,   -- valeurs invalides détectées ligne par ligne
    duplicates_removed  integer,   -- doublons et versions identiques écartés
    rejected_fk         integer,   -- références vers une ligne inexistante
    silver_rows         integer,
    run_at              timestamptz NOT NULL DEFAULT now()
);
