-- Historique des contrôles qualité : une ligne par règle et par exécution.
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.quality_results (
    id          bigserial PRIMARY KEY,
    run_id      text        NOT NULL,
    run_at      timestamptz NOT NULL DEFAULT now(),
    rule_id     text        NOT NULL,
    table_name  text        NOT NULL,
    description text        NOT NULL,
    severity    text        NOT NULL,   -- 'bloquant' ou 'avertissement'
    errors      bigint      NOT NULL,   -- nombre de lignes en erreur (0 = OK)
    status      text        NOT NULL,   -- 'OK', 'AVERTISSEMENT' ou 'ECHEC'
    details     text
);