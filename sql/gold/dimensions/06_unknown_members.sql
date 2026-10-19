-- LIGNE « INCONNU » (clé -1) dans chaque dimension : une référence manquante ne fait perdre aucune vente.
INSERT INTO gold.dim_date (date_key, full_date, year, quarter, month, month_name, year_month,
                           week_of_year, day_of_month, day_of_week, day_name, is_weekend,
                           is_holiday, holiday_name)
VALUES (-1, NULL, NULL, NULL, NULL, 'Inconnu', 'Inconnu', NULL, NULL, NULL, 'Inconnu', false, false, NULL);

INSERT INTO gold.dim_customer (customer_key, customer_id, customer_name, customer_type, email, city,
                               region, registration_date, start_date, end_date, is_current)
VALUES (-1, 'INCONNU', 'Inconnu', 'Inconnu', NULL, 'Inconnu', 'Inconnu', NULL,
        DATE '1900-01-01', DATE '9999-12-31', true);

INSERT INTO gold.dim_product (product_key, product_id, product_name, category, brand, unit_price,
                              supplier_id, created_date, start_date, end_date, is_current)
VALUES (-1, 'INCONNU', 'Inconnu', 'Inconnu', 'Inconnu', NULL, 'INCONNU', NULL,
        DATE '1900-01-01', DATE '9999-12-31', true);

INSERT INTO gold.dim_supplier (supplier_key, supplier_id, supplier_name, city, country,
                               standard_lead_time_days, start_date, end_date, is_current)
VALUES (-1, 'INCONNU', 'Inconnu', 'Inconnu', 'Inconnu', NULL, DATE '1900-01-01', DATE '9999-12-31', true);

INSERT INTO gold.dim_warehouse (warehouse_key, warehouse_id, warehouse_name, city, region, capacity_units)
VALUES (-1, 'INCONNU', 'Inconnu', 'Inconnu', 'Inconnu', NULL);