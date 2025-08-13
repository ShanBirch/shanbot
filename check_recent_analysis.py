import sqlite3
import json

# List of recently analyzed users
usernames = [
    "kelstar",
    "Kristyleecoop",
    "alice_forster",
    "calorie_tracking",
    "hrmnkahlon89",
    "izsaraiva",
    "shane_minahan"
]

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

for username in usernames:
    cursor.execute(
        "SELECT client_analysis_json FROM users WHERE ig_username = ?", (username,))
    row = cursor.fetchone()
    print(f"--- {username} ---")
    if row and row[0] and row[0] != "NULL":
        try:
            analysis = json.loads(row[0])
            print(json.dumps(analysis, indent=2))
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("No analysis found.")
    print()

conn.close()
