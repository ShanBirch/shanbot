#!/usr/bin/env python3
"""
Check the structure of the users table.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def check_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 CHECKING USERS TABLE STRUCTURE")
    print("=" * 50)

    # Get table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()

    print("Columns in users table:")
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")

    # Get sample data
    cursor.execute("SELECT * FROM users LIMIT 3")
    sample_data = cursor.fetchall()

    print(f"\nSample data:")
    for i, row in enumerate(sample_data, 1):
        print(f"  Row {i}: {row}")

    # Check for any status-related columns
    cursor.execute(
        "SELECT * FROM users WHERE ig_username LIKE '%cocos%' OR ig_username LIKE '%anna%'")
    relevant_users = cursor.fetchall()

    print(f"\nRelevant users:")
    for row in relevant_users:
        print(f"  {row}")

    conn.close()


if __name__ == "__main__":
    check_users_table()
