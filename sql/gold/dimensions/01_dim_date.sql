-- DIMENSION DATE : une ligne par jour, générée une fois pour toute la période.
CREATE SCHEMA IF NOT EXISTS gold;

-- Clé de date : 2026-10-01 devient 20261001
CREATE OR REPLACE FUNCTION gold.date_key(d date) RETURNS integer
LANGUAGE sql IMMUTABLE AS $$ SELECT to_char(d, 'YYYYMMDD')::integer $$;

-- Jour des données apportées par un lot : le lot du 2026-10-02 contient les données du 2026-10-01.
CREATE OR REPLACE FUNCTION gold.lot_data_date(batch text) RETURNS date
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN batch ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN batch::date - 1
                ELSE DATE '2026-10-01' END
$$;

DROP TABLE IF EXISTS gold.dim_date CASCADE;
CREATE TABLE gold.dim_date (
    date_key     integer PRIMARY KEY,
    full_date    date,
    year         integer,
    quarter      integer,
    month        integer,
    month_name   text,
    year_month   text,
    week_of_year integer,
    day_of_month integer,
    day_of_week  integer,        -- 1 = lundi ... 7 = dimanche
    day_name     text,
    is_weekend   boolean,
    is_holiday   boolean,
    holiday_name text
);

INSERT INTO gold.dim_date
SELECT gold.date_key(d), d,
       extract(year FROM d)::int, extract(quarter FROM d)::int, extract(month FROM d)::int,
       (ARRAY['janvier','février','mars','avril','mai','juin','juillet','août','septembre',
              'octobre','novembre','décembre'])[extract(month FROM d)::int],
       to_char(d, 'YYYY-MM'), extract(week FROM d)::int, extract(day FROM d)::int,
       extract(isodow FROM d)::int,
       (ARRAY['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'])[extract(isodow FROM d)::int],
       extract(isodow FROM d) >= 6,
       to_char(d, 'MM-DD') IN ('01-01','01-11','05-01','07-30','08-14','08-20','08-21','11-06','11-18'),
       CASE to_char(d, 'MM-DD')
            WHEN '01-01' THEN 'Nouvel An'
            WHEN '01-11' THEN 'Manifeste de l''Indépendance'
            WHEN '05-01' THEN 'Fête du Travail'
            WHEN '07-30' THEN 'Fête du Trône'
            WHEN '08-14' THEN 'Journée de Oued Eddahab'
            WHEN '08-20' THEN 'Révolution du Roi et du Peuple'
            WHEN '08-21' THEN 'Fête de la Jeunesse'
            WHEN '11-06' THEN 'Marche Verte'
            WHEN '11-18' THEN 'Fête de l''Indépendance' END
FROM (SELECT g::date AS d
      FROM generate_series(DATE '2023-01-01', DATE '2028-12-31', INTERVAL '1 day') AS g) days;
-- Les fêtes religieuses (dates lunaires) ne sont pas incluses.