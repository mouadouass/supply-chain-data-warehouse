-- Clients : pas de référence à vérifier, tout ce qui est propre est inséré.
INSERT INTO silver.customers (customer_id, customer_name, customer_type, email, city, region,
                              registration_date, batch_id)
SELECT customer_id, customer_name, customer_type, email, city, region, registration_date, batch_id
FROM silver.stg_customers;
