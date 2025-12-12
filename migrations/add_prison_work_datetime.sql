-- 懲役システムに15分制限用のタイムスタンプカラムを追加
ALTER TABLE prison_sentences
ADD COLUMN last_work_datetime TIMESTAMPTZ DEFAULT NULL;
