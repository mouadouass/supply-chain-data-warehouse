-- RÉCONCILIATION DES LIVRAISONS, DES STOCKS ET DES DIMENSIONS.
SELECT 'R_DLV_001' AS check_id, 'Nombre de livraisons (hors commandes annulées)' AS description,
       (SELECT count(*) FROM silver.deliveries d JOIN silver.orders o USING (order_id)
        WHERE o.status <> 'Annulée')::numeric AS expected,
       (SELECT count(*) FROM gold.fact_delivery)::numeric AS actual
UNION ALL SELECT 'R_DLV_002', 'Livraisons arrivées',
       (SELECT count(*) FROM silver.deliveries d JOIN silver.orders o USING (order_id)
        WHERE o.status <> 'Annulée' AND d.actual_delivery_date IS NOT NULL),
       (SELECT coalesce(sum(is_delivered), 0) FROM gold.fact_delivery)
UNION ALL SELECT 'R_DLV_003', 'Livraisons en retard',
       (SELECT count(*) FROM silver.deliveries d JOIN silver.orders o USING (order_id)
        WHERE o.status <> 'Annulée' AND d.actual_delivery_date > d.expected_delivery_date),
       (SELECT coalesce(sum(is_late), 0) FROM gold.fact_delivery)
UNION ALL SELECT 'R_DLV_004', 'Livraisons dupliquées par une jointure (doit être 0)',
       0::numeric, (SELECT count(*) - count(DISTINCT delivery_id) FROM gold.fact_delivery)
UNION ALL SELECT 'R_INV_001', 'Nombre de lignes de stock',
       (SELECT count(*) FROM silver.inventory), (SELECT count(*) FROM gold.fact_inventory)
UNION ALL SELECT 'R_INV_002', 'Quantité totale en stock',
       (SELECT coalesce(sum(quantity_on_hand), 0) FROM silver.inventory),
       (SELECT coalesce(sum(quantity_on_hand), 0) FROM gold.fact_inventory)
UNION ALL SELECT 'R_INV_003', 'Lignes en rupture (stock à zéro)',
       (SELECT count(*) FROM silver.inventory WHERE quantity_on_hand = 0),
       (SELECT coalesce(sum(is_out_of_stock), 0) FROM gold.fact_inventory)
UNION ALL SELECT 'R_DIM_001', 'Nombre de clients distincts',
       (SELECT count(DISTINCT customer_id) FROM silver.customers),
       (SELECT count(DISTINCT customer_id) FROM gold.dim_customer WHERE customer_key <> -1)
UNION ALL SELECT 'R_DIM_002', 'Nombre de produits distincts',
       (SELECT count(DISTINCT product_id) FROM silver.products),
       (SELECT count(DISTINCT product_id) FROM gold.dim_product WHERE product_key <> -1)
UNION ALL SELECT 'R_DIM_003', 'Nombre de fournisseurs distincts',
       (SELECT count(DISTINCT supplier_id) FROM silver.suppliers),
       (SELECT count(DISTINCT supplier_id) FROM gold.dim_supplier WHERE supplier_key <> -1)
UNION ALL SELECT 'R_DIM_004', 'Nombre d''entrepôts distincts',
       (SELECT count(DISTINCT warehouse_id) FROM silver.warehouses),
       (SELECT count(DISTINCT warehouse_id) FROM gold.dim_warehouse WHERE warehouse_key <> -1)
UNION ALL SELECT 'R_DIM_005', 'Versions qui se chevauchent dans les dimensions historisées (doit être 0)',
       0::numeric,
       (SELECT count(*) FROM (
            SELECT a.supplier_key FROM gold.dim_supplier a JOIN gold.dim_supplier b
              ON a.supplier_id = b.supplier_id AND a.supplier_key < b.supplier_key
             AND a.start_date <= b.end_date AND b.start_date <= a.end_date
            UNION ALL
            SELECT a.product_key FROM gold.dim_product a JOIN gold.dim_product b
              ON a.product_id = b.product_id AND a.product_key < b.product_key
             AND a.start_date <= b.end_date AND b.start_date <= a.end_date
            UNION ALL
            SELECT a.customer_key FROM gold.dim_customer a JOIN gold.dim_customer b
              ON a.customer_id = b.customer_id AND a.customer_key < b.customer_key
             AND a.start_date <= b.end_date AND b.start_date <= a.end_date) chevauchements);