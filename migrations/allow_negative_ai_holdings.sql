-- AIトレーダーが空売り（マイナス数量）を持てるように制約を削除
ALTER TABLE ai_trader_holdings DROP CONSTRAINT ai_trader_holdings_quantity_check;
