import sqlite3
import json
from datetime import datetime, timedelta


def check_workout_sessions():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Check table schema
    cursor.execute('PRAGMA table_info(client_workout_sessions)')
    columns = cursor.fetchall()

    print("=== CLIENT_WORKOUT_SESSIONS TABLE SCHEMA ===")
    for row in columns:
        print(f"  {row[1]} ({row[2]})")

    # Get sample data
    cursor.execute('SELECT * FROM client_workout_sessions LIMIT 5')
    sample_data = cursor.fetchall()

    print("\n=== SAMPLE DATA (First 5 rows) ===")
    if sample_data:
        # Get column names for reference
        cursor.execute('PRAGMA table_info(client_workout_sessions)')
        col_info = cursor.fetchall()
        col_names = [col[1] for col in col_info]

        for i, row in enumerate(sample_data):
            print(f"\n--- Row {i+1} ---")
            for j, value in enumerate(row):
                if j < len(col_names):
                    print(f"  {col_names[j]}: {value}")

    # Check how many total records
    cursor.execute('SELECT COUNT(*) FROM client_workout_sessions')
    total_count = cursor.fetchone()[0]
    print(f"\n=== TOTAL RECORDS: {total_count} ===")

    # Check unique users
    cursor.execute(
        'SELECT DISTINCT ig_username FROM client_workout_sessions WHERE ig_username IS NOT NULL')
    unique_users = cursor.fetchall()
    print(f"\n=== UNIQUE USERS WITH WORKOUT DATA: {len(unique_users)} ===")
    for user in unique_users[:10]:  # Show first 10
        print(f"  {user[0]}")

    # Check recent data (last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT ig_username, workout_date, exercise_name, sets, reps, weight 
        FROM client_workout_sessions 
        WHERE workout_date >= ? 
        ORDER BY workout_date DESC, ig_username
        LIMIT 10
    ''', (seven_days_ago,))

    recent_data = cursor.fetchall()
    print(f"\n=== RECENT WORKOUT DATA (Last 7 days) ===")
    for row in recent_data:
        print(
            f"  {row[0]} | {row[1]} | {row[2]} | Sets: {row[3]} | Reps: {row[4]} | Weight: {row[5]}")

    conn.close()


if __name__ == "__main__":
    check_workout_sessions()
