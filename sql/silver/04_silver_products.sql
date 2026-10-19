-- Produits : le fournisseur doit exister dans silver.suppliers (sinon quarantaine).
WITH checked AS (
    SELECT s.*,
           CASE WHEN NOT EXISTS (SELECT 1 FROM silver.suppliers p WHERE p.supplier_id = s.supplier_id)
                THEN 'fournisseur inexistant' END AS reject_reason
    FROM silver.stg_products s
), rejected AS (
    INSERT INTO silver.rejected_rows (table_name, reject_reason, batch_id, source_file,
                                      row_number_in_file, raw_data)
    SELECT 'products', reject_reason, batch_id, source_file, row_number_in_file,
           to_jsonb(c) - 'reject_reason' - 'loaded_at'
    FROM checked c WHERE reject_reason IS NOT NULL
)
INSERT INTO silver.products (product_id, product_name, category, brand, unit_price, supplier_id,
                             created_date, batch_id)
SELECT product_id, product_name, category, brand, unit_price, supplier_id, created_date, batch_id
FROM checked WHERE reject_reason IS NULL;
