-- FAIT LIVRAISONS. Grain : une ligne = une livraison.
-- Les livraisons de commandes annulées (anomalie signalée par Q_DATE_007) sont exclues.
DROP TABLE IF EXISTS gold.fact_delivery;
CREATE TABLE gold.fact_delivery (
    delivery_key       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    delivery_id        text    NOT NULL,
    order_id           text    NOT NULL,
    customer_key       integer NOT NULL,
    supplier_key       integer NOT NULL,
    warehouse_key      integer NOT NULL,
    order_date_key     integer NOT NULL,   -- 4 rôles de la dimension date
    ship_date_key      integer NOT NULL,
    expected_date_key  integer NOT NULL,
    actual_date_key    integer NOT NULL,   -- -1 si la livraison n'est pas arrivée
    carrier            text,
    delivery_status    text    NOT NULL,
    delivery_days      integer,            -- arrivée - expédition (vide si pas arrivée)
    delay_days         integer,            -- jours de retard (0 si à l'heure, vide si pas arrivée)
    is_delivered       smallint NOT NULL,  -- 1 = date d'arrivée connue
    is_late            smallint NOT NULL,  -- 1 = arrivée après la date prévue
    is_missing_arrival smallint NOT NULL   -- 1 = « Livrée » mais sans date d'arrivée (anomalie)
);

INSERT INTO gold.fact_delivery (delivery_id, order_id, customer_key, supplier_key, warehouse_key,
       order_date_key, ship_date_key, expected_date_key, actual_date_key, carrier, delivery_status,
       delivery_days, delay_days, is_delivered, is_late, is_missing_arrival)
SELECT d.delivery_id, d.order_id,
       coalesce(c.customer_key, -1), coalesce(s.supplier_key, -1), coalesce(w.warehouse_key, -1),
       gold.date_key(o.order_date), gold.date_key(d.ship_date), gold.date_key(d.expected_delivery_date),
       coalesce(gold.date_key(d.actual_delivery_date), -1),
       d.carrier, d.delivery_status,
       d.actual_delivery_date - d.ship_date,
       CASE WHEN d.actual_delivery_date IS NULL THEN NULL
            ELSE greatest(d.actual_delivery_date - d.expected_delivery_date, 0) END,
       CASE WHEN d.actual_delivery_date IS NOT NULL THEN 1 ELSE 0 END,
       CASE WHEN d.actual_delivery_date > d.expected_delivery_date THEN 1 ELSE 0 END,
       CASE WHEN d.delivery_status = 'Livrée' AND d.actual_delivery_date IS NULL THEN 1 ELSE 0 END
FROM silver.deliveries d
JOIN silver.orders o USING (order_id)
LEFT JOIN gold.dim_customer  c ON c.customer_id  = o.customer_id AND o.order_date BETWEEN c.start_date AND c.end_date
LEFT JOIN gold.dim_supplier  s ON s.supplier_id  = d.supplier_id AND o.order_date BETWEEN s.start_date AND s.end_date
LEFT JOIN gold.dim_warehouse w ON w.warehouse_id = d.warehouse_id
WHERE o.status <> 'Annulée'
ORDER BY d.ship_date, d.delivery_id;

CREATE INDEX ON gold.fact_delivery (supplier_key);
CREATE INDEX ON gold.fact_delivery (warehouse_key);
CREATE INDEX ON gold.fact_delivery (ship_date_key);