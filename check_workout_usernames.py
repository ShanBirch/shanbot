import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

cursor.execute(
    'SELECT DISTINCT ig_username FROM client_workout_sessions WHERE ig_username IS NOT NULL')
usernames = cursor.fetchall()

print(f"IG usernames with workouts ({len(usernames)}):")
for username in usernames:
    print(f"  {username[0]}")

# Check specific workout data for each user
print("\nWorkout counts:")
for username in usernames:
    cursor.execute(
        'SELECT COUNT(*) FROM client_workout_sessions WHERE ig_username = ?', (username[0],))
    count = cursor.fetchone()[0]
    print(f"  {username[0]}: {count} sessions")

conn.close()
