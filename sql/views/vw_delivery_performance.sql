-- VUE LIVRAISONS : délais et retards par mois d'expédition, fournisseur et entrepôt.
CREATE OR REPLACE VIEW gold.vw_delivery_performance AS
SELECT d.year_month,
       s.supplier_id, s.supplier_name, s.city AS supplier_city,
       w.warehouse_name,
       count(*)                                                     AS deliveries,
       sum(f.is_delivered)                                          AS delivered,
       sum(f.is_late)                                               AS late,
       round(100.0 * sum(f.is_late) / nullif(sum(f.is_delivered), 0), 1) AS late_rate_pct,
       round(avg(f.delivery_days), 1)                               AS avg_delivery_days,
       round(avg(f.delay_days) FILTER (WHERE f.is_late = 1), 1)     AS avg_delay_when_late
FROM gold.fact_delivery f
JOIN gold.dim_date      d ON d.date_key      = f.ship_date_key
JOIN gold.dim_supplier  s ON s.supplier_key  = f.supplier_key
JOIN gold.dim_warehouse w ON w.warehouse_key = f.warehouse_key
GROUP BY d.year_month, s.supplier_id, s.supplier_name, s.city, w.warehouse_name;