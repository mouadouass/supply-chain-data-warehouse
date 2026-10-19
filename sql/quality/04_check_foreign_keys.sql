SELECT 'Q_FK_001' AS rule_id, 'orders' AS table_name, 'Commande sans client' AS description,
       'bloquant' AS severity, count(*)::bigint AS errors, NULL::text AS details
FROM silver.orders o WHERE NOT EXISTS (SELECT 1 FROM silver.customers c WHERE c.customer_id = o.customer_id)
UNION ALL SELECT 'Q_FK_002', 'orders', 'Commande sans entrepôt', 'bloquant', count(*), NULL
FROM silver.orders o WHERE NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = o.warehouse_id)
UNION ALL SELECT 'Q_FK_003', 'order_items', 'Ligne de commande sans produit', 'bloquant', count(*), NULL
FROM silver.order_items i WHERE NOT EXISTS (SELECT 1 FROM silver.products p WHERE p.product_id = i.product_id)
UNION ALL SELECT 'Q_FK_004', 'order_items', 'Ligne de commande sans commande', 'bloquant', count(*), NULL
FROM silver.order_items i WHERE NOT EXISTS (SELECT 1 FROM silver.orders o WHERE o.order_id = i.order_id)
UNION ALL SELECT 'Q_FK_005', 'deliveries', 'Livraison sans commande', 'bloquant', count(*), NULL
FROM silver.deliveries d WHERE NOT EXISTS (SELECT 1 FROM silver.orders o WHERE o.order_id = d.order_id)
UNION ALL SELECT 'Q_FK_006', 'deliveries', 'Livraison sans entrepôt', 'bloquant', count(*), NULL
FROM silver.deliveries d WHERE NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = d.warehouse_id)
UNION ALL SELECT 'Q_FK_007', 'deliveries', 'Livraison sans fournisseur', 'bloquant', count(*), NULL
FROM silver.deliveries d WHERE NOT EXISTS (SELECT 1 FROM silver.suppliers s WHERE s.supplier_id = d.supplier_id)
UNION ALL SELECT 'Q_FK_008', 'inventory', 'Stock sans produit', 'bloquant', count(*), NULL
FROM silver.inventory v WHERE NOT EXISTS (SELECT 1 FROM silver.products p WHERE p.product_id = v.product_id)
UNION ALL SELECT 'Q_FK_009', 'inventory', 'Stock sans entrepôt', 'bloquant', count(*), NULL
FROM silver.inventory v WHERE NOT EXISTS (SELECT 1 FROM silver.warehouses w WHERE w.warehouse_id = v.warehouse_id)
UNION ALL SELECT 'Q_FK_010', 'products', 'Produit sans fournisseur', 'bloquant', count(*), NULL
FROM silver.products p WHERE NOT EXISTS (SELECT 1 FROM silver.suppliers s WHERE s.supplier_id = p.supplier_id);