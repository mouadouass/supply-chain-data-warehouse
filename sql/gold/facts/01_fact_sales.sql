-- FAIT VENTES. Grain : une ligne = un produit vendu dans une commande.
-- Chaque ligne prend la version de chaque dimension qui était valable à la date de la commande.
DROP TABLE IF EXISTS gold.fact_sales;
CREATE TABLE gold.fact_sales (
    sales_key     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_item_id text    NOT NULL,        -- dimension dégénérée
    order_id      text    NOT NULL,        -- dimension dégénérée (pour compter les commandes)
    customer_key  integer NOT NULL,
    product_key   integer NOT NULL,
    supplier_key  integer NOT NULL,
    warehouse_key integer NOT NULL,
    date_key      integer NOT NULL,        -- date de la commande
    order_status  text    NOT NULL,
    is_cancelled  smallint NOT NULL,       -- 1 = commande annulée (exclue du chiffre d'affaires)
    quantity      integer NOT NULL,
    unit_price    numeric(12,2) NOT NULL,
    total_amount  numeric(14,2) NOT NULL   -- quantité x prix unitaire
);

INSERT INTO gold.fact_sales (order_item_id, order_id, customer_key, product_key, supplier_key,
                             warehouse_key, date_key, order_status, is_cancelled, quantity,
                             unit_price, total_amount)
SELECT i.order_item_id, i.order_id,
       coalesce(c.customer_key, -1), coalesce(p.product_key, -1), coalesce(s.supplier_key, -1),
       coalesce(w.warehouse_key, -1), gold.date_key(o.order_date), o.status,
       CASE WHEN o.status = 'Annulée' THEN 1 ELSE 0 END,
       i.quantity, i.unit_price, i.quantity * i.unit_price
FROM silver.order_items i
JOIN silver.orders o USING (order_id)
LEFT JOIN gold.dim_customer  c ON c.customer_id  = o.customer_id AND o.order_date BETWEEN c.start_date AND c.end_date
LEFT JOIN gold.dim_product   p ON p.product_id   = i.product_id  AND o.order_date BETWEEN p.start_date AND p.end_date
LEFT JOIN gold.dim_supplier  s ON s.supplier_id  = p.supplier_id AND o.order_date BETWEEN s.start_date AND s.end_date
LEFT JOIN gold.dim_warehouse w ON w.warehouse_id = o.warehouse_id
ORDER BY o.order_date, i.order_item_id;

CREATE INDEX ON gold.fact_sales (date_key);
CREATE INDEX ON gold.fact_sales (product_key);
CREATE INDEX ON gold.fact_sales (customer_key);