import sqlite3
from datetime import datetime, timedelta

# Connect to the database
conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# Get recent sent reviews from today
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('''
SELECT review_id, user_ig_username, status, created_timestamp, reviewed_timestamp 
FROM pending_reviews 
WHERE status = 'sent' AND DATE(reviewed_timestamp) = ?
ORDER BY reviewed_timestamp DESC
LIMIT 5
''', (today,))

sent_today = cursor.fetchall()

print("REVIEWS SENT TODAY:")
print("=" * 80)
for row in sent_today:
    print(f"ID: {row[0]}, User: {row[1]}")
    print(f"Status: {row[2]}")
    print(f"Created: {row[3]}")
    print(f"Reviewed: {row[4]}")
    print("-" * 40)

print(f"\nTotal sent today: {len(sent_today)}")

# Get pending reviews
cursor.execute('''
SELECT review_id, user_ig_username, status, created_timestamp 
FROM pending_reviews 
WHERE status = 'pending_review'
ORDER BY created_timestamp DESC
''')

pending_rows = cursor.fetchall()

print(f"\nPENDING REVIEWS ({len(pending_rows)}):")
print("=" * 80)
for row in pending_rows:
    print(f"ID: {row[0]}, User: {row[1]}")
    print(f"Created: {row[2]} ({row[3]})")
    
    # Check how old this review is
    try:
        created_dt = datetime.fromisoformat(row[3])
        age = datetime.now() - created_dt
        hours_old = age.total_seconds() / 3600
        print(f"Age: {hours_old:.1f} hours old")
    except:
        print("Age: Unknown")
    
    print("-" * 40)

conn.close() 