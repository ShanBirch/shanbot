import sqlite3
import os

# Define the absolute path to the SQLite database
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))
SQLITE_DB_PATH = os.path.join(APP_DIR, "analytics_data_good.sqlite")


def list_tables():
    """Lists all tables in the SQLite database."""
    conn = None
    try:
        if not os.path.exists(SQLITE_DB_PATH):
            print(f"Error: Database file not found at {SQLITE_DB_PATH}")
            return

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if tables:
            print("Tables found in the database:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No tables found in the database.")

    except sqlite3.Error as e:
        print(f"Error connecting to or querying SQLite database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    list_tables()
