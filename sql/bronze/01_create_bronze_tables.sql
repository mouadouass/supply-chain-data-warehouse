-- Couche BRONZE : copie brute des sources.
-- Toutes les colonnes sont en TEXTE : rien ne doit faire échouer le chargement.
-- 4 colonnes techniques sont ajoutées à chaque table.

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS audit;

-- Journal des lots chargés : évite de charger deux fois le même lot.
CREATE TABLE IF NOT EXISTS audit.batch_log (
    batch_id     text        NOT NULL,
    table_name   text        NOT NULL,
    source_file  text,
    rows_loaded  integer,
    status       text        NOT NULL DEFAULT 'loaded',
    loaded_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (batch_id, table_name)
);

CREATE TABLE IF NOT EXISTS bronze.customers (
    customer_id text, customer_name text, customer_type text, email text,
    city text, region text, registration_date text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.suppliers (
    supplier_id text, supplier_name text, city text, country text,
    standard_lead_time_days text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.warehouses (
    warehouse_id text, warehouse_name text, city text, region text,
    capacity_units text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.products (
    product_id text, product_name text, category text, brand text,
    unit_price text, supplier_id text, created_date text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.orders (
    order_id text, customer_id text, warehouse_id text, order_date text,
    status text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.order_items (
    order_item_id text, order_id text, product_id text, quantity text,
    unit_price text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.deliveries (
    delivery_id text, order_id text, warehouse_id text, supplier_id text,
    carrier text, ship_date text, expected_delivery_date text,
    actual_delivery_date text, delivery_status text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.inventory (
    snapshot_date text, product_id text, warehouse_id text,
    quantity_on_hand text,
    batch_id text, source_file text, row_number_in_file integer,
    loaded_at timestamptz DEFAULT now()
);
