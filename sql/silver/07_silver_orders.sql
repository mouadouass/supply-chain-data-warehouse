-- Commandes : le client et l'entrepôt doivent exister (sinon quarantaine).
WITH checked AS (
    SELECT s.*,
           CASE WHEN NOT EXISTS (SELECT 1 FROM silver.customers c WHERE c.customer_id = s.customer_id)
                THEN 'client inexistant'
                WHEN NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = s.warehouse_id)
                THEN 'entrepôt inexistant' END AS reject_reason
    FROM silver.stg_orders s
), rejected AS (
    INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, source_file,
                                      row_number_in_file, raw_data)
    SELECT 'orders', reject_reason, batch_id, source_file, row_number_in_file,
           to_jsonb(c) - 'reject_reason' - 'loaded_at'
    FROM checked c WHERE reject_reason IS NOT NULL
)
INSERT INTO silver.orders (order_id, customer_id, warehouse_id, order_date, status, batch_id)
SELECT order_id, customer_id, warehouse_id, order_date, status, batch_id
FROM checked WHERE reject_reason IS NULL;
