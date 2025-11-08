import psycopg2
from datetime import datetime, timezone, timedelta

# データベースに接続し、メッセージログを記録
def recording_log(user_id, text):
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        JST = timezone(timedelta(hours=9))
        jst_now = datetime.now(timezone.utc).astimezone(JST)
        cur.execute("""
            INSERT INTO logs (line_id, message, sent_at, my_name)
            SELECT %s, %s, %s, my_name
            FROM users
            WHERE line_id = %s
            """,
            (user_id, text, jst_now, user_id)
        )
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
