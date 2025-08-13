import sqlite3
import json

# Connect to database
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
conn = sqlite3.connect(SQLITE_PATH)
cursor = conn.cursor()

print("=== COMPLETE DATABASE CHECK ===")

# Get total count of users
cursor.execute('''SELECT COUNT(*) FROM users 
                  WHERE ig_username IS NOT NULL 
                  AND ig_username != "" 
                  AND ig_username NOT LIKE "user_%"''')
total_users = cursor.fetchone()[0]
print(f"\nTotal users with ig_username: {total_users}")

# Get all users and their analysis status
cursor.execute('''
SELECT ig_username, subscriber_id, metrics_json
FROM users 
WHERE ig_username IS NOT NULL 
AND ig_username != "" 
AND ig_username NOT LIKE "user_%"
ORDER BY ig_username
''')

users_needing_analysis = []
users_with_analysis = []
all_users = cursor.fetchall()

print(f"\nChecking {len(all_users)} users...")

for row in all_users:
    ig_username, subscriber_id, metrics_json = row

    # Determine analysis status
    status = "No metrics"
    has_analysis = False

    if metrics_json:
        try:
            metrics = json.loads(metrics_json)
            if 'client_analysis' in metrics:
                analysis_source = metrics.get('analysis_source', 'unknown')
                if analysis_source == 'instagram_follower_analyzer':
                    status = "Has full Instagram analysis"
                    has_analysis = True
                else:
                    status = f"Has analysis from: {analysis_source}"
            else:
                status = "Has metrics but no client_analysis"
        except json.JSONDecodeError:
            status = "Invalid JSON in metrics"

    if has_analysis:
        users_with_analysis.append(ig_username)
    else:
        users_needing_analysis.append((ig_username, subscriber_id, status))

    print(f"  {ig_username} ({subscriber_id or 'N/A'}): {status}")

print(f"\n=== SUMMARY ===")
print(f"Total users: {len(all_users)}")
print(f"Users WITH Instagram analysis: {len(users_with_analysis)}")
print(f"Users NEEDING Instagram analysis: {len(users_needing_analysis)}")

if users_needing_analysis:
    print(f"\nUsers that need analysis:")
    for i, (username, sub_id, status) in enumerate(users_needing_analysis, 1):
        print(f"  {i:2d}. {username} ({sub_id or 'N/A'}) - {status}")

conn.close()
