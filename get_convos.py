import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'app/analytics_data_good.sqlite'

today = datetime.now()
yesterday = today - timedelta(days=1)
start_of_yesterday = datetime(
    yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT timestamp, ig_username, type, text FROM messages WHERE timestamp >= ? ORDER BY timestamp ASC",
          (start_of_yesterday.isoformat(),))
convos = c.fetchall()

conn.close()

print(
    f'\n--- Conversations from {start_of_yesterday.strftime("%Y-%m-%d %H:%M:%S")} to {today.strftime("%Y-%m-%d %H:%M:%S")} ---\n')
for convo in convos:
    print(f'  [{convo[0]}] {convo[1]} ({convo[2]}): {convo[3]}')
