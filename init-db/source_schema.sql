CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email TEXT,                   
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    country TEXT NOT NULL,
    city TEXT,                   
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    signup_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,            
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL,      
    payment_method TEXT NOT NULL,
    order_date TIMESTAMPTZ NOT NULL,  
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,         
    unit_price NUMERIC(10,2) NOT NULL, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    carrier TEXT NOT NULL,
    shipped_at TIMESTAMPTZ,         
    delivered_at TIMESTAMPTZ,   
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);