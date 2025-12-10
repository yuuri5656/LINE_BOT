-- チップ残高を基本チップとボーナスチップに分離
-- 実行日: 2025年12月10日
-- 目的: チップ購入時のボーナスを悪用から保護

-- ステップ1: 新しいカラムを追加
ALTER TABLE minigame_chips
ADD COLUMN base_balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (base_balance >= 0);

ALTER TABLE minigame_chips
ADD COLUMN bonus_balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (bonus_balance >= 0);

ALTER TABLE minigame_chips
ADD COLUMN locked_base_balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (locked_base_balance >= 0);

ALTER TABLE minigame_chips
ADD COLUMN locked_bonus_balance DECIMAL(15, 2) DEFAULT 0 NOT NULL CHECK (locked_bonus_balance >= 0);

-- ステップ2: 既存データをマイグレーション
-- 現在の balance と locked_balance を新フィールドに移行
UPDATE minigame_chips
SET base_balance = balance,
    bonus_balance = 0,
    locked_base_balance = locked_balance,
    locked_bonus_balance = 0;

-- ステップ3: 古いカラムは削除せず残す（ロールバック対応）
-- 必要に応じて後で削除する

-- ステップ4: チェック制約を更新
-- base_balance + bonus_balance >= locked_base_balance + locked_bonus_balance
-- のような制約は、アプリケーション側で管理する

-- ステップ5: インデックスは既存のままで継続使用

-- チップ取引履歴テーブルに chip_type カラムを追加
ALTER TABLE chip_transactions
ADD COLUMN chip_type VARCHAR(50) DEFAULT 'mixed'; -- 'base' | 'bonus' | 'mixed'

-- 実行完了
