-- FAIT STOCKS. Grain : une ligne = un produit, dans un entrepôt, pour un jour donné (photo du soir).
-- Attention : les stocks ne s'additionnent pas dans le temps (on prend le dernier jour ou la moyenne).
DROP TABLE IF EXISTS gold.fact_inventory;
CREATE TABLE gold.fact_inventory (
    date_key         integer NOT NULL,
    product_key      integer NOT NULL,
    warehouse_key    integer NOT NULL,
    quantity_on_hand integer NOT NULL,
    is_out_of_stock  smallint NOT NULL,    -- 1 = stock à zéro (rupture)
    is_low_stock     smallint NOT NULL,    -- 1 = stock inférieur ou égal à 10 (rupture comprise)
    PRIMARY KEY (date_key, product_key, warehouse_key)
);

INSERT INTO gold.fact_inventory (date_key, product_key, warehouse_key, quantity_on_hand,
                                 is_out_of_stock, is_low_stock)
SELECT gold.date_key(v.snapshot_date), coalesce(p.product_key, -1), coalesce(w.warehouse_key, -1),
       v.quantity_on_hand,
       CASE WHEN v.quantity_on_hand = 0 THEN 1 ELSE 0 END,
       CASE WHEN v.quantity_on_hand <= 10 THEN 1 ELSE 0 END
FROM silver.inventory v
LEFT JOIN gold.dim_product   p ON p.product_id   = v.product_id   AND v.snapshot_date BETWEEN p.start_date AND p.end_date
LEFT JOIN gold.dim_warehouse w ON w.warehouse_id = v.warehouse_id;

CREATE INDEX ON gold.fact_inventory (product_key);
CREATE INDEX ON gold.fact_inventory (warehouse_key);