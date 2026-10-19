-- Livraisons : la commande, l'entrepôt et le fournisseur doivent exister.
WITH checked AS (
    SELECT s.*,
           CASE WHEN NOT EXISTS (SELECT 1 FROM silver.orders o WHERE o.order_id = s.order_id)
                THEN 'commande inexistante'
                WHEN NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = s.warehouse_id)
                THEN 'entrepôt inexistant'
                WHEN NOT EXISTS (SELECT 1 FROM silver.suppliers p WHERE p.supplier_id = s.supplier_id)
                THEN 'fournisseur inexistant' END AS reject_reason
    FROM silver.stg_deliveries s
), rejected AS (
    INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, source_file,
                                      row_number_in_file, raw_data)
    SELECT 'deliveries', reject_reason, batch_id, source_file, row_number_in_file,
           to_jsonb(c) - 'reject_reason' - 'loaded_at'
    FROM checked c WHERE reject_reason IS NOT NULL
)
INSERT INTO silver.deliveries (delivery_id, order_id, warehouse_id, supplier_id, carrier, ship_date,
                               expected_delivery_date, actual_delivery_date, delivery_status, batch_id)
SELECT delivery_id, order_id, warehouse_id, supplier_id, carrier, ship_date,
       expected_delivery_date, actual_delivery_date, delivery_status, batch_id
FROM checked WHERE reject_reason IS NULL;
