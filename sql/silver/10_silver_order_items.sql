-- Lignes de commande : la commande (propre) et le produit doivent exister.
-- Une ligne dont la commande a été rejetée est donc rejetée aussi.
WITH checked AS (
    SELECT s.*,
           CASE WHEN NOT EXISTS (SELECT 1 FROM silver.orders o WHERE o.order_id = s.order_id)
                THEN 'commande inexistante ou rejetée'
                WHEN NOT EXISTS (SELECT 1 FROM silver.products p WHERE p.product_id = s.product_id)
                THEN 'produit inexistant' END AS reject_reason
    FROM silver.stg_order_items s
), rejected AS (
    INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, source_file,
                                      row_number_in_file, raw_data)
    SELECT 'order_items', reject_reason, batch_id, source_file, row_number_in_file,
           to_jsonb(c) - 'reject_reason' - 'loaded_at'
    FROM checked c WHERE reject_reason IS NOT NULL
)
INSERT INTO silver.order_items (order_item_id, order_id, product_id, quantity, unit_price, batch_id)
SELECT order_item_id, order_id, product_id, quantity, unit_price, batch_id
FROM checked WHERE reject_reason IS NULL;
