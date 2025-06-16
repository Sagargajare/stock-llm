# schema.py
# This file contains the schema for the database.
schema = """
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    stock VARCHAR(50) NOT NULL,
    open NUMERIC(10, 2),
    high NUMERIC(10, 2),
    low NUMERIC(10, 2),
    close NUMERIC(10, 2),
    volume BIGINT,
    change_pct NUMERIC(5, 2)
);
"""