-- Entrepôts : pas de référence à vérifier.
INSERT INTO silver.warehouses (warehouse_id, warehouse_name, city, region, capacity_units, batch_id)
SELECT warehouse_id, warehouse_name, city, region, capacity_units, batch_id
FROM silver.stg_warehouses;
