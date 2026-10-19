-- Couche SILVER : données nettoyées, avec de vrais types (dates, entiers, décimaux).
-- Les tables "maîtres" (clients, fournisseurs, produits, entrepôts) gardent une ligne par
-- VERSION : une nouvelle ligne n'apparaît que si une valeur change d'un lot à l'autre.
-- (c'est ce qui permettra l'historisation SCD Type 2 dans Gold).

CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS silver.customers (
    customer_id text NOT NULL, customer_name text NOT NULL, customer_type text NOT NULL,
    email text, city text NOT NULL, region text NOT NULL, registration_date date NOT NULL,
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now(),
    PRIMARY KEY (customer_id, batch_id)
);
CREATE TABLE IF NOT EXISTS silver.suppliers (
    supplier_id text NOT NULL, supplier_name text NOT NULL, city text NOT NULL,
    country text NOT NULL, standard_lead_time_days integer NOT NULL CHECK (standard_lead_time_days >= 0),
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now(),
    PRIMARY KEY (supplier_id, batch_id)
);
CREATE TABLE IF NOT EXISTS silver.warehouses (
    warehouse_id text NOT NULL, warehouse_name text NOT NULL, city text NOT NULL,
    region text NOT NULL, capacity_units integer NOT NULL CHECK (capacity_units > 0),
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now(),
    PRIMARY KEY (warehouse_id, batch_id)
);
CREATE TABLE IF NOT EXISTS silver.products (
    product_id text NOT NULL, product_name text NOT NULL, category text NOT NULL,
    brand text NOT NULL, unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    supplier_id text NOT NULL, created_date date NOT NULL,
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now(),
    PRIMARY KEY (product_id, batch_id)
);
CREATE TABLE IF NOT EXISTS silver.orders (
    order_id text PRIMARY KEY, customer_id text NOT NULL, warehouse_id text NOT NULL,
    order_date date NOT NULL, status text NOT NULL,
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS silver.order_items (
    order_item_id text PRIMARY KEY, order_id text NOT NULL REFERENCES silver.orders (order_id),
    product_id text NOT NULL, quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS silver.deliveries (
    delivery_id text PRIMARY KEY, order_id text NOT NULL REFERENCES silver.orders (order_id),
    warehouse_id text NOT NULL, supplier_id text NOT NULL, carrier text,
    ship_date date NOT NULL, expected_delivery_date date NOT NULL, actual_delivery_date date,
    delivery_status text NOT NULL,
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS silver.inventory (
    snapshot_date date NOT NULL, product_id text NOT NULL, warehouse_id text NOT NULL,
    quantity_on_hand integer NOT NULL CHECK (quantity_on_hand >= 0),
    batch_id text NOT NULL, loaded_at timestamptz DEFAULT now(),
    PRIMARY KEY (snapshot_date, product_id, warehouse_id)
);

-- Tables de passage (staging) : même forme que les tables finales, sans contraintes.
CREATE TABLE IF NOT EXISTS silver.stg_customers  (LIKE silver.customers);
CREATE TABLE IF NOT EXISTS silver.stg_suppliers  (LIKE silver.suppliers);
CREATE TABLE IF NOT EXISTS silver.stg_warehouses (LIKE silver.warehouses);
CREATE TABLE IF NOT EXISTS silver.stg_products   (LIKE silver.products);
CREATE TABLE IF NOT EXISTS silver.stg_orders     (LIKE silver.orders);
CREATE TABLE IF NOT EXISTS silver.stg_order_items(LIKE silver.order_items);
CREATE TABLE IF NOT EXISTS silver.stg_deliveries (LIKE silver.deliveries);
CREATE TABLE IF NOT EXISTS silver.stg_inventory  (LIKE silver.inventory);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['customers','suppliers','warehouses','products','orders',
                           'order_items','deliveries','inventory'] LOOP
    EXECUTE format('ALTER TABLE silver.stg_%I ADD COLUMN IF NOT EXISTS source_file text, '
                   'ADD COLUMN IF NOT EXISTS row_number_in_file integer', t);
  END LOOP;
END $$;
