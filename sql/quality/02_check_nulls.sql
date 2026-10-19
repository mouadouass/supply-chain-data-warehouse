SELECT 'Q_NULL_001' AS rule_id, 'customers' AS table_name, 'customer_id vide ou NULL' AS description,
       'bloquant' AS severity, count(*)::bigint AS errors, NULL::text AS details
FROM silver.customers WHERE customer_id IS NULL OR trim(customer_id) = ''
UNION ALL SELECT 'Q_NULL_002', 'suppliers', 'supplier_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.suppliers WHERE supplier_id IS NULL OR trim(supplier_id) = ''
UNION ALL SELECT 'Q_NULL_003', 'warehouses', 'warehouse_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.warehouses WHERE warehouse_id IS NULL OR trim(warehouse_id) = ''
UNION ALL SELECT 'Q_NULL_004', 'products', 'product_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.products WHERE product_id IS NULL OR trim(product_id) = ''
UNION ALL SELECT 'Q_NULL_005', 'orders', 'order_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.orders WHERE order_id IS NULL OR trim(order_id) = ''
UNION ALL SELECT 'Q_NULL_006', 'orders', 'customer_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.orders WHERE customer_id IS NULL OR trim(customer_id) = ''
UNION ALL SELECT 'Q_NULL_007', 'order_items', 'order_item_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.order_items WHERE order_item_id IS NULL OR trim(order_item_id) = ''
UNION ALL SELECT 'Q_NULL_008', 'deliveries', 'delivery_id vide ou NULL', 'bloquant', count(*), NULL
FROM silver.deliveries WHERE delivery_id IS NULL OR trim(delivery_id) = ''
UNION ALL SELECT 'Q_NULL_009', 'customers', 'Ville inconnue (information manquante dans la source)',
       'avertissement', count(*), NULL
FROM silver.customers WHERE city = 'Inconnu';