-- Stocks : le produit et l'entrepôt doivent exister.
WITH checked AS (
    SELECT s.*,
           CASE WHEN NOT EXISTS (SELECT 1 FROM silver.products p WHERE p.product_id = s.product_id)
                THEN 'produit inexistant'
                WHEN NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = s.warehouse_id)
                THEN 'entrepôt inexistant' END AS reject_reason
    FROM silver.stg_inventory s
), rejected AS (
    INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, source_file,
                                      row_number_in_file, raw_data)
    SELECT 'inventory', reject_reason, batch_id, source_file, row_number_in_file,
           to_jsonb(c) - 'reject_reason' - 'loaded_at'
    FROM checked c WHERE reject_reason IS NOT NULL
)
INSERT INTO silver.inventory (snapshot_date, product_id, warehouse_id, quantity_on_hand, batch_id)
SELECT snapshot_date, product_id, warehouse_id, quantity_on_hand, batch_id
FROM checked WHERE reject_reason IS NULL;
