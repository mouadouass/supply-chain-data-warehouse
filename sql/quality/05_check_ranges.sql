SELECT 'Q_RNG_001' AS rule_id, 'order_items' AS table_name, 'Quantité vendue inférieure ou égale à 0' AS description,
       'bloquant' AS severity, count(*)::bigint AS errors, NULL::text AS details
FROM silver.order_items WHERE quantity <= 0
UNION ALL SELECT 'Q_RNG_002', 'order_items', 'Prix unitaire négatif', 'bloquant', count(*), NULL
FROM silver.order_items WHERE unit_price < 0
UNION ALL SELECT 'Q_RNG_003', 'products', 'Prix catalogue négatif', 'bloquant', count(*), NULL
FROM silver.products WHERE unit_price < 0
UNION ALL SELECT 'Q_RNG_004', 'inventory', 'Stock négatif', 'bloquant', count(*), NULL
FROM silver.inventory WHERE quantity_on_hand < 0
UNION ALL SELECT 'Q_RNG_005', 'warehouses', 'Capacité nulle ou négative', 'bloquant', count(*), NULL
FROM silver.warehouses WHERE capacity_units <= 0
UNION ALL SELECT 'Q_RNG_006', 'suppliers', 'Délai fournisseur négatif', 'bloquant', count(*), NULL
FROM silver.suppliers WHERE standard_lead_time_days < 0
UNION ALL SELECT 'Q_RNG_007', 'order_items', 'Quantité anormalement élevée (plus de 50)', 'avertissement', count(*), NULL
FROM silver.order_items WHERE quantity > 50
UNION ALL SELECT 'Q_RNG_008', 'order_items', 'Prix vendu à plus de 20 % du prix catalogue', 'avertissement', count(*), NULL
FROM silver.order_items i
JOIN (SELECT DISTINCT ON (product_id) product_id, unit_price AS catalog_price
      FROM silver.products ORDER BY product_id, batch_id DESC) p USING (product_id)
WHERE p.catalog_price > 0 AND abs(i.unit_price - p.catalog_price) > 0.2 * p.catalog_price;