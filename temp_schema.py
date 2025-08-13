import sqlite3
import os

SQLITE_DB_PATH = "app/analytics_data_good.sqlite"


def list_tables_and_schema():
    """Lists all tables and their schema in the SQLite database."""
    conn = None
    try:
        if not os.path.exists(SQLITE_DB_PATH):
            print(f"Error: Database file not found at {SQLITE_DB_PATH}")
            return

        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if tables:
            print("Database Schema:")
            for table in tables:
                print(f"\n--- Table: {table[0]} ---")
                print(table[1])
        else:
            print("No tables found in the database.")

    except sqlite3.Error as e:
        print(f"Error connecting to or querying SQLite database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    list_tables_and_schema()
