import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
c = conn.cursor()

print("=== Checking remaining alice/forster accounts ===")
c.execute("SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username LIKE '%alice%' OR ig_username LIKE '%forster%'")
rows = c.fetchall()

for row in rows:
    print(f"Username: {row[0]}, Subscriber ID: {row[1]}, Status: {row[2]}")

print(f"\nTotal accounts found: {len(rows)}")

if len(rows) == 1 and rows[0][0] == 'forster.alice':
    print("✅ Merge successful! Only forster.alice remains.")

    # Check message count
    c.execute("SELECT COUNT(*) FROM messages WHERE ig_username = 'forster.alice'")
    msg_count = c.fetchone()[0]
    print(f"✅ forster.alice has {msg_count} messages")

else:
    print("❌ Merge may not have completed correctly")

conn.close()
