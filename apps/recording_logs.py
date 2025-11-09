import psycopg2
from datetime import datetime, timezone, timedelta
import config

def recording_logs(event, user_id, text, display_name):
    # データベースに接続し、メッセージログを記録
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cur = conn.cursor()
        JST = timezone(timedelta(hours=9))
        jst_now = datetime.now(timezone.utc).astimezone(JST)
        cur.execute("""
            INSERT INTO logs (user_id, message, sent_at, display_name)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, text, jst_now, display_name)
        )
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
