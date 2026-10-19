CREATE SCHEMA IF NOT EXISTS bronze;  -- données brutes
CREATE SCHEMA IF NOT EXISTS silver;  -- données nettoyées
CREATE SCHEMA IF NOT EXISTS gold;    -- Star Schema
CREATE SCHEMA IF NOT EXISTS audit;   -- contrôles qualité, suivi des lots