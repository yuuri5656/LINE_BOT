-- account_type ENUMに 'current' を追加
ALTER TYPE account_type ADD VALUE IF NOT EXISTS 'current';
