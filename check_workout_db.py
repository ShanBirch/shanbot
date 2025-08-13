import sqlite3


def check_workout_database():
    db_path = r"app\analytics_data_good.sqlite"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔍 Checking client_workout_sessions table...")

        # Get all columns
        cursor.execute("PRAGMA table_info(client_workout_sessions)")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")

        # Get sample data
        cursor.execute("SELECT * FROM client_workout_sessions LIMIT 5")
        rows = cursor.fetchall()

        print("\nSample data:")
        for i, row in enumerate(rows):
            print(f"  Row {i+1}: {row}")

        # Check if there are more specific tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%workout%' OR name LIKE '%exercise%' OR name LIKE '%set%'")
        workout_tables = cursor.fetchall()

        print(
            f"\nAll workout-related tables: {[t[0] for t in workout_tables]}")

        # Look for any data that might contain detailed workout info
        cursor.execute(
            "SELECT * FROM client_workout_sessions WHERE client_name_key IS NOT NULL LIMIT 3")
        client_sessions = cursor.fetchall()

        print(f"\nSessions with client names:")
        for session in client_sessions:
            print(f"  {session}")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_workout_database()
