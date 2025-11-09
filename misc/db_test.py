import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)")
cur.execute("INSERT INTO users (name) VALUES (%s)", ("Yuuri",))
conn.commit()

cur.execute("SELECT * FROM users")
print(cur.fetchall())

cur.close()
conn.close()
