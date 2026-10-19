-- Index pour retrouver vite un lot ou une clé (créés après le chargement).
CREATE INDEX IF NOT EXISTS idx_b_customers_batch   ON bronze.customers (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_customers_key     ON bronze.customers (customer_id);
CREATE INDEX IF NOT EXISTS idx_b_suppliers_batch   ON bronze.suppliers (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_suppliers_key     ON bronze.suppliers (supplier_id);
CREATE INDEX IF NOT EXISTS idx_b_warehouses_batch  ON bronze.warehouses (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_products_batch    ON bronze.products (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_products_key      ON bronze.products (product_id);
CREATE INDEX IF NOT EXISTS idx_b_orders_batch      ON bronze.orders (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_orders_key        ON bronze.orders (order_id);
CREATE INDEX IF NOT EXISTS idx_b_items_batch       ON bronze.order_items (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_items_order       ON bronze.order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_b_deliveries_batch  ON bronze.deliveries (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_deliveries_order  ON bronze.deliveries (order_id);
CREATE INDEX IF NOT EXISTS idx_b_inventory_batch   ON bronze.inventory (batch_id);
CREATE INDEX IF NOT EXISTS idx_b_inventory_key     ON bronze.inventory (snapshot_date, product_id, warehouse_id);
