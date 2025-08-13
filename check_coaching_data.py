import sqlite3
import json

# Connect to database
db_path = "app/analytics_data_good.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check for coaching analysis data
cursor.execute("""
    SELECT ig_username, coaching_potential_score, coaching_category 
    FROM followers 
    WHERE coaching_potential_score IS NOT NULL 
    LIMIT 10
""")

results = cursor.fetchall()
print(f"Found {len(results)} followers with coaching analysis")

if results:
    print("\nSample coaching data:")
    for username, score, category in results:
        print(f"  @{username}: {score}/100 ({category})")
else:
    print("No coaching analysis data found. You may need to run the analysis first.")

conn.close()
