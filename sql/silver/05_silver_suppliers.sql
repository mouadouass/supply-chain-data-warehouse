-- Fournisseurs : pas de référence à vérifier.
INSERT INTO silver.suppliers (supplier_id, supplier_name, city, country, standard_lead_time_days,
                              batch_id)
SELECT supplier_id, supplier_name, city, country, standard_lead_time_days, batch_id
FROM silver.stg_suppliers;
