SELECT 'Q_DUP_001' AS rule_id, 'orders' AS table_name, 'order_id en double' AS description,
       'bloquant' AS severity, count(*)::bigint AS errors, NULL::text AS details
FROM (SELECT order_id FROM silver.orders GROUP BY 1 HAVING count(*) > 1) d
UNION ALL SELECT 'Q_DUP_002', 'order_items', 'order_item_id en double', 'bloquant', count(*), NULL
FROM (SELECT order_item_id FROM silver.order_items GROUP BY 1 HAVING count(*) > 1) d
UNION ALL SELECT 'Q_DUP_003', 'deliveries', 'delivery_id en double', 'bloquant', count(*), NULL
FROM (SELECT delivery_id FROM silver.deliveries GROUP BY 1 HAVING count(*) > 1) d
UNION ALL SELECT 'Q_DUP_004', 'customers', 'Même client en double dans un même lot', 'bloquant', count(*), NULL
FROM (SELECT customer_id, batch_id FROM silver.customers GROUP BY 1, 2 HAVING count(*) > 1) d
UNION ALL SELECT 'Q_DUP_005', 'order_items', 'Même produit deux fois dans une commande', 'avertissement', count(*), NULL
FROM (SELECT order_id, product_id FROM silver.order_items GROUP BY 1, 2 HAVING count(*) > 1) d
UNION ALL SELECT 'Q_DUP_006', 'deliveries', 'Commande avec plusieurs livraisons', 'avertissement', count(*), NULL
FROM (SELECT order_id FROM silver.deliveries GROUP BY 1 HAVING count(*) > 1) d;