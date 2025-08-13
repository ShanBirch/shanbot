#!/usr/bin/env python3
"""
Check all tables in the database to find conversation data
"""

import sqlite3
import os
from pathlib import Path


def get_db_path():
    """Get the database path with fallback logic"""
    # Try relative path first
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))
    db_path = os.path.join(app_dir, "analytics_data_good.sqlite")

    if os.path.exists(db_path):
        return db_path

    # Try finding shanbot directory
    current_dir = Path(os.getcwd())
    for parent in [current_dir] + list(current_dir.parents):
        if parent.name.lower() == "shanbot":
            db_path = os.path.join(
                str(parent), "app", "analytics_data_good.sqlite")
            if os.path.exists(db_path):
                return db_path

    # Fallback to known absolute path
    fallback_path = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite"
    if os.path.exists(fallback_path):
        return fallback_path

    raise FileNotFoundError("Could not find the SQLite database file")


def check_all_tables():
    """Check all tables in the database"""

    db_path = get_db_path()
    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        print("\n" + "="*60)

        # Check each table for conversation-related data
        for table in tables:
            print(f"\n📊 TABLE: {table}")

            # Get table structure
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print("Columns:", [col[1] for col in columns])

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")

            # If table has data, show sample
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample = cursor.fetchall()
                print("Sample data:")
                for i, row in enumerate(sample, 1):
                    print(f"  Row {i}: {row}")

                # Check if this table might contain conversation data
                column_names = [col[1].lower() for col in columns]
                if any(keyword in ' '.join(column_names) for keyword in ['message', 'text', 'username', 'conversation']):
                    print("🔍 This table might contain conversation data!")

            print("-" * 40)

    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_all_tables()
