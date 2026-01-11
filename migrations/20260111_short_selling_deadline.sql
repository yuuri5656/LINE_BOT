-- Add due_date column to user_stock_short_positions
ALTER TABLE user_stock_short_positions ADD COLUMN IF NOT EXISTS due_date DATE;
