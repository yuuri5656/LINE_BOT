-- ミニゲーム口座テーブルの削除
-- 実行日: 2025年12月1日
-- 理由: チップシステム導入により、ミニゲーム口座機能は廃止されました

-- minigame_accounts テーブルを削除
DROP TABLE IF EXISTS minigame_accounts CASCADE;

-- 説明:
-- - minigame_accounts テーブルは、ユーザーがミニゲーム用に銀行口座を登録する機能で使用されていました
-- - 現在は MinigameChip テーブルを使用したチップシステムに移行しているため、このテーブルは不要です
-- - CASCADE オプションにより、このテーブルに依存する外部キー制約も自動的に削除されます
