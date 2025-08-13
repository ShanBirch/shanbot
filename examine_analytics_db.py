#!/usr/bin/env python3
"""
Examine the analytics database to understand Nicole's workout history
"""

import sqlite3
import json
from datetime import datetime, timedelta


def examine_database():
    """Examine the analytics database structure and content"""

    print("=" * 60)
    print("ANALYTICS DATABASE EXAMINATION")
    print("=" * 60)

    try:
        conn = sqlite3.connect('analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nTables found: {len(tables)}")
        for table in tables:
            print(f"  • {table[0]}")

        # Examine each table structure
        for table_name in [t[0] for t in tables]:
            print(f"\n--- Table: {table_name} ---")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")

            # Get sample data
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")

            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print("Sample rows:")
                for i, row in enumerate(sample_rows):
                    print(f"  Row {i+1}: {row}")

        # Look specifically for Nicole's data
        print(f"\n--- SEARCHING FOR NICOLE'S DATA ---")

        # Try different table patterns
        potential_tables = [t[0] for t in tables if any(keyword in t[0].lower(
        ) for keyword in ['workout', 'exercise', 'session', 'client', 'user', 'nicole'])]

        for table_name in potential_tables:
            print(f"\nSearching {table_name} for Nicole...")
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE LOWER(name) LIKE '%nicole%' OR LOWER(client) LIKE '%nicole%' OR LOWER(user) LIKE '%nicole%' LIMIT 5;")
            nicole_data = cursor.fetchall()
            if nicole_data:
                print(f"Found Nicole data in {table_name}:")
                for row in nicole_data:
                    print(f"  {row}")

        conn.close()
        return True

    except Exception as e:
        print(f"Error examining database: {e}")
        return False


def find_nicole_workout_data():
    """Find Nicole's recent workout data"""

    print(f"\n--- NICOLE'S RECENT WORKOUT DATA ---")

    try:
        conn = sqlite3.connect('analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Get all tables again
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        # Try to find workout-related data
        for table_name in tables:
            try:
                # Try different column name patterns
                column_patterns = [
                    "SELECT * FROM {} WHERE client_name LIKE '%Nicole%' OR user_name LIKE '%Nicole%'",
                    "SELECT * FROM {} WHERE name LIKE '%Nicole%'",
                    "SELECT * FROM {} LIMIT 5"  # Just get some sample data
                ]

                for pattern in column_patterns:
                    try:
                        query = pattern.format(table_name)
                        cursor.execute(query)
                        results = cursor.fetchall()
                        if results:
                            print(f"\nData from {table_name}:")
                            for row in results[:3]:  # Show first 3 rows
                                print(f"  {row}")
                            break
                    except:
                        continue

            except Exception as e:
                continue

        conn.close()

    except Exception as e:
        print(f"Error finding Nicole's data: {e}")


if __name__ == "__main__":
    examine_database()
    find_nicole_workout_data()
