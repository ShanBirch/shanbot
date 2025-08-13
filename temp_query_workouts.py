import sqlite3
import os

# Define the relative path to the SQLite database
SQLITE_DB_PATH = "app/analytics_data_good.sqlite"


def query_workout_sessions():
    """Queries and prints the first 5 rows of the client_workout_sessions table."""
    conn = None
    try:
        if not os.path.exists(SQLITE_DB_PATH):
            print(f"Error: Database file not found at {SQLITE_DB_PATH}")
            return

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        print("Querying client_workout_sessions table...")
        cursor.execute("SELECT * FROM client_workout_sessions LIMIT 5;")
        rows = cursor.fetchall()

        if rows:
            # Get column names from the cursor description
            column_names = [description[0]
                            for description in cursor.description]
            print("Columns:", column_names)
            print("First 5 rows:")
            for row in rows:
                print(row)
        else:
            print("No data found in client_workout_sessions table.")

    except sqlite3.Error as e:
        print(f"Error connecting to or querying SQLite database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    query_workout_sessions()
