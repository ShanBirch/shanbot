import sqlite3
import json

# Connect to SQLite database
conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:", [t[0] for t in tables])

# Check users table structure
if 'users' in [t[0] for t in tables]:
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nUsers table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Get sample data from users table
    cursor.execute("SELECT ig_username, metrics_json FROM users LIMIT 3")
    sample_users = cursor.fetchall()

    print(f"\nSample data ({len(sample_users)} users):")
    for username, metrics_json in sample_users:
        print(f"Username: {username}")
        if metrics_json:
            try:
                metrics = json.loads(metrics_json)
                print(f"  Metrics keys: {list(metrics.keys())}")
                # Look for coaching potential in metrics
                if 'coaching_potential' in str(metrics):
                    print("  Found coaching_potential!")
                if 'client_analysis' in metrics:
                    client_analysis = metrics['client_analysis']
                    if 'coaching_potential' in client_analysis:
                        score = client_analysis['coaching_potential'].get(
                            'score', 'N/A')
                        print(f"  Coaching score: {score}")
            except json.JSONDecodeError:
                print("  Invalid JSON in metrics")
        else:
            print("  No metrics_json")
        print()

    # Count total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    print(f"Total users in database: {total_users}")

conn.close()
