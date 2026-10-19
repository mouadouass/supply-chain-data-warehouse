SELECT 'Q_DATE_001' AS rule_id, 'deliveries' AS table_name, 'Expédition avant la date de commande' AS description,
       'bloquant' AS severity, count(*)::bigint AS errors, NULL::text AS details
FROM silver.deliveries d JOIN silver.orders o USING (order_id)
WHERE d.ship_date < o.order_date AND o.status <> 'Annulée'   -- les commandes annulées sont signalées par Q_DATE_007
UNION ALL SELECT 'Q_DATE_002', 'deliveries', 'Date prévue avant l''expédition', 'bloquant', count(*), NULL
FROM silver.deliveries WHERE expected_delivery_date < ship_date
UNION ALL SELECT 'Q_DATE_003', 'deliveries', 'Arrivée avant l''expédition', 'bloquant', count(*), NULL
FROM silver.deliveries WHERE actual_delivery_date < ship_date
UNION ALL SELECT 'Q_DATE_004', 'orders', 'Commande datée après le jour du lot', 'bloquant', count(*), NULL
FROM silver.orders
WHERE order_date > (SELECT coalesce(max(batch_id) FILTER (WHERE batch_id ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')::date,
                                    DATE '2026-10-02') FROM silver.orders)
UNION ALL SELECT 'Q_DATE_005', 'inventory', 'Stock daté après le jour du lot', 'bloquant', count(*), NULL
FROM silver.inventory
WHERE snapshot_date > (SELECT coalesce(max(batch_id) FILTER (WHERE batch_id ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')::date,
                                       DATE '2026-10-02') FROM silver.inventory)
UNION ALL SELECT 'Q_DATE_006', 'deliveries', 'Livraison « Livrée » sans date d''arrivée', 'avertissement', count(*), NULL
FROM silver.deliveries WHERE delivery_status = 'Livrée' AND actual_delivery_date IS NULL
UNION ALL SELECT 'Q_DATE_007', 'deliveries', 'Livraison d''une commande annulée', 'avertissement', count(*), NULL
FROM silver.deliveries d JOIN silver.orders o USING (order_id) WHERE o.status = 'Annulée'
UNION ALL SELECT 'Q_DATE_008', 'deliveries', 'Livraison « En transit » avec une date d''arrivée', 'avertissement', count(*), NULL
FROM silver.deliveries WHERE delivery_status = 'En transit' AND actual_delivery_date IS NOT NULL
UNION ALL SELECT 'Q_DATE_009', 'orders', 'Commande expédiée ou livrée sans livraison', 'avertissement', count(*), NULL
FROM silver.orders o WHERE o.status IN ('Expédiée', 'Livrée')
  AND NOT EXISTS (SELECT 1 FROM silver.deliveries d WHERE d.order_id = o.order_id)
UNION ALL SELECT 'Q_DATE_010', 'inventory', 'Jours manquants dans la série de stock (produit x entrepôt)', 'avertissement',
       coalesce(sum((max_d - min_d + 1) - n), 0)::bigint, NULL
FROM (SELECT product_id, warehouse_id, min(snapshot_date) AS min_d, max(snapshot_date) AS max_d, count(*) AS n
      FROM silver.inventory GROUP BY 1, 2) t;