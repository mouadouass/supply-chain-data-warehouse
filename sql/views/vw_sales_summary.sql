-- VUE VENTES : le chiffre d'affaires par mois, catégorie, région du client et fournisseur.
-- (commandes annulées exclues, comme dans business_rules.md)
CREATE OR REPLACE VIEW gold.vw_sales_summary AS
SELECT d.year, d.month, d.year_month,
       p.category,
       c.region AS customer_region,
       s.supplier_name,
       sum(f.total_amount)         AS revenue,
       sum(f.quantity)             AS units_sold,
       count(DISTINCT f.order_id)  AS orders
FROM gold.fact_sales f
JOIN gold.dim_date     d ON d.date_key     = f.date_key
JOIN gold.dim_product  p ON p.product_key  = f.product_key
JOIN gold.dim_customer c ON c.customer_key = f.customer_key
JOIN gold.dim_supplier s ON s.supplier_key = f.supplier_key
WHERE f.is_cancelled = 0
GROUP BY d.year, d.month, d.year_month, p.category, c.region, s.supplier_name;