-- Add columns to stock_symbols
ALTER TABLE stock_symbols ADD COLUMN IF NOT EXISTS short_interest INTEGER NOT NULL DEFAULT 0;
ALTER TABLE stock_symbols ADD COLUMN IF NOT EXISTS lending_fee_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.0010;

-- Add column to stock_accounts
ALTER TABLE stock_accounts ADD COLUMN IF NOT EXISTS margin_deposit NUMERIC(18, 2) NOT NULL DEFAULT 0;

-- Create user_stock_short_positions table
CREATE TABLE IF NOT EXISTS user_stock_short_positions (
    short_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    symbol_id INTEGER NOT NULL REFERENCES stock_symbols(symbol_id),
    quantity INTEGER NOT NULL,
    average_sell_price NUMERIC(18, 4) NOT NULL,
    total_proceeds NUMERIC(18, 2) NOT NULL,
    accrued_interest NUMERIC(18, 2) NOT NULL DEFAULT 0,
    stock_account_id INTEGER NOT NULL REFERENCES stock_accounts(stock_account_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
