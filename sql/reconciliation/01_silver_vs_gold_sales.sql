-- RÉCONCILIATION DES VENTES : ce qui est dans Silver doit être identique dans Gold.
-- Chaque ligne : (identifiant, description, valeur attendue = Silver, valeur obtenue = Gold).
SELECT 'R_SALES_001' AS check_id, 'Nombre de lignes de ventes' AS description,
       (SELECT count(*) FROM silver.order_items)::numeric AS expected,
       (SELECT count(*) FROM gold.fact_sales)::numeric AS actual
UNION ALL SELECT 'R_SALES_002', 'Chiffre d''affaires total (commandes annulées comprises)',
       (SELECT coalesce(sum(quantity * unit_price), 0) FROM silver.order_items),
       (SELECT coalesce(sum(total_amount), 0) FROM gold.fact_sales)
UNION ALL SELECT 'R_SALES_003', 'Chiffre d''affaires hors commandes annulées',
       (SELECT coalesce(sum(i.quantity * i.unit_price), 0)
        FROM silver.order_items i JOIN silver.orders o USING (order_id) WHERE o.status <> 'Annulée'),
       (SELECT coalesce(sum(total_amount), 0) FROM gold.fact_sales WHERE is_cancelled = 0)
UNION ALL SELECT 'R_SALES_004', 'Nombre de commandes distinctes',
       (SELECT count(DISTINCT order_id) FROM silver.order_items),
       (SELECT count(DISTINCT order_id) FROM gold.fact_sales)
UNION ALL SELECT 'R_SALES_005', 'Quantité totale vendue',
       (SELECT coalesce(sum(quantity), 0) FROM silver.order_items),
       (SELECT coalesce(sum(quantity), 0) FROM gold.fact_sales)
UNION ALL SELECT 'R_SALES_006', 'Ventes dupliquées par une jointure (doit être 0)',
       0::numeric,
       (SELECT count(*) - count(DISTINCT order_item_id) FROM gold.fact_sales)
UNION ALL SELECT 'R_SALES_007', 'Mois dont le chiffre d''affaires diffère entre Silver et Gold (doit être 0)',
       0::numeric,
       (SELECT count(*) FROM (
            SELECT to_char(o.order_date, 'YYYY-MM') AS ym, sum(i.quantity * i.unit_price) AS amount
            FROM silver.order_items i JOIN silver.orders o USING (order_id) GROUP BY 1) s
        FULL JOIN (
            SELECT d.year_month AS ym, sum(f.total_amount) AS amount
            FROM gold.fact_sales f JOIN gold.dim_date d USING (date_key) GROUP BY 1) g USING (ym)
        WHERE coalesce(s.amount, 0) <> coalesce(g.amount, 0));