#!/usr/bin/env python3
"""
SQLite Database Explorer for Progressive Overload AI
"""

import sqlite3
import json
from datetime import datetime


def explore_database():
    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    print("🗄️  ANALYTICS DATABASE EXPLORER")
    print("=" * 50)

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"\n📋 TABLES ({len(tables)} total):")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  • {table_name}: {count} records")

    print("\n" + "=" * 50)

    # Explore client_workout_sessions table specifically
    print("\n💪 CLIENT WORKOUT SESSIONS:")
    cursor.execute("SELECT * FROM client_workout_sessions LIMIT 5")
    sessions = cursor.fetchall()

    # Get column names
    cursor.execute("PRAGMA table_info(client_workout_sessions)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns: {', '.join(columns)}")

    print("\nSample data:")
    for session in sessions:
        print(f"  • {session}")

    # Check if there are specific clients we can analyze
    print("\n👥 CLIENT NAMES:")
    cursor.execute(
        "SELECT DISTINCT client_name_key FROM client_workout_sessions LIMIT 10")
    clients = cursor.fetchall()
    for client in clients:
        print(f"  • {client[0]}")

    # Check date range
    print("\n📅 DATE RANGE:")
    cursor.execute(
        "SELECT MIN(workout_date), MAX(workout_date) FROM client_workout_sessions")
    date_range = cursor.fetchone()
    print(f"  From: {date_range[0]} to {date_range[1]}")

    # Look for detailed workout data
    print("\n🔍 LOOKING FOR WORKOUT DETAILS...")

    # Check if there are any JSON columns with exercise data
    cursor.execute("PRAGMA table_info(client_workout_sessions)")
    columns_info = cursor.fetchall()

    for col_info in columns_info:
        col_name = col_info[1]
        if 'json' in col_name.lower() or 'data' in col_name.lower():
            print(f"  Found potential data column: {col_name}")
            cursor.execute(
                f"SELECT {col_name} FROM client_workout_sessions WHERE {col_name} IS NOT NULL LIMIT 1")
            sample = cursor.fetchone()
            if sample and sample[0]:
                print(f"    Sample data: {str(sample[0])[:200]}...")

    conn.close()
    print("\n✅ Database exploration complete!")


if __name__ == "__main__":
    explore_database()
