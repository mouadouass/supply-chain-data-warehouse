-- VUE STOCKS : l'état ACTUEL de chaque produit dans chaque entrepôt (dernier jour connu).
-- Statut : Rupture (0), Stock bas (10 ou moins), Dormant (en stock mais aucune vente depuis 60 jours), Normal.
CREATE OR REPLACE VIEW gold.vw_inventory_status AS
WITH ref AS (
    SELECT max(full_date) AS today FROM gold.fact_inventory JOIN gold.dim_date USING (date_key)
), last_day AS (
    SELECT i.product_key, i.warehouse_key, i.quantity_on_hand
    FROM gold.fact_inventory i JOIN ref ON i.date_key = gold.date_key(ref.today)
), sales AS (
    SELECT p.product_id, w.warehouse_id,
           sum(f.quantity) FILTER (WHERE d.full_date > ref.today - 30) AS units_sold_30d,
           max(d.full_date) AS last_sale_date
    FROM gold.fact_sales f
    JOIN gold.dim_product p ON p.product_key = f.product_key
    JOIN gold.dim_warehouse w ON w.warehouse_key = f.warehouse_key
    JOIN gold.dim_date d ON d.date_key = f.date_key
    CROSS JOIN ref
    WHERE f.is_cancelled = 0
    GROUP BY p.product_id, w.warehouse_id
), shortage AS (
    SELECT p.product_id, w.warehouse_id, sum(i.is_out_of_stock) AS days_out_of_stock_30d
    FROM gold.fact_inventory i
    JOIN gold.dim_date d ON d.date_key = i.date_key
    JOIN gold.dim_product p ON p.product_key = i.product_key
    JOIN gold.dim_warehouse w ON w.warehouse_key = i.warehouse_key
    CROSS JOIN ref
    WHERE d.full_date > ref.today - 30
    GROUP BY p.product_id, w.warehouse_id
)
SELECT p.product_id, p.product_name, p.category,
       w.warehouse_id, w.warehouse_name,
       l.quantity_on_hand,
       coalesce(s.units_sold_30d, 0)        AS units_sold_30d,
       s.last_sale_date,
       ref.today - s.last_sale_date         AS days_since_last_sale,
       coalesce(sh.days_out_of_stock_30d, 0) AS days_out_of_stock_30d,
       CASE WHEN l.quantity_on_hand = 0 THEN 'Rupture'
            WHEN l.quantity_on_hand <= 10 THEN 'Stock bas'
            WHEN s.last_sale_date IS NULL OR ref.today - s.last_sale_date > 60 THEN 'Dormant'
            ELSE 'Normal' END               AS stock_status
FROM last_day l
CROSS JOIN ref
JOIN gold.dim_product   p ON p.product_key   = l.product_key
JOIN gold.dim_warehouse w ON w.warehouse_key = l.warehouse_key
LEFT JOIN sales    s  ON s.product_id  = p.product_id AND s.warehouse_id  = w.warehouse_id
LEFT JOIN shortage sh ON sh.product_id = p.product_id AND sh.warehouse_id = w.warehouse_id;