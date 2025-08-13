#!/usr/bin/env python3
"""
Inspect Alice Forster's actual workout data in the SQLite database
"""

import sqlite3
import json
from datetime import datetime, timedelta


def inspect_database_structure():
    """Look at the database structure and Alice's data"""
    try:
        conn = sqlite3.connect('analytics_data_good.sqlite')
        cursor = conn.cursor()

        print("=== DATABASE INSPECTION FOR ALICE FORSTER ===")

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nAvailable tables: {[table[0] for table in tables]}")

        # Look for Alice in each table
        for table_name in [table[0] for table in tables]:
            print(f"\n--- Checking table: {table_name} ---")

            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Columns: {column_names}")

            # Look for Alice's data
            if 'client_name' in column_names:
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE client_name LIKE '%Alice%' OR client_name LIKE '%Forster%' LIMIT 3")
            elif 'name' in column_names:
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE name LIKE '%Alice%' OR name LIKE '%Forster%' LIMIT 3")
            else:
                # Just show a few rows to understand structure
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")

            rows = cursor.fetchall()
            if rows:
                print(f"Found {len(rows)} rows:")
                for i, row in enumerate(rows):
                    print(f"  Row {i+1}: {dict(zip(column_names, row))}")
            else:
                print("No matching data found")

        # Specifically look for workout data
        print(f"\n=== SEARCHING FOR ALICE'S WORKOUT DATA ===")

        # Try different variations of Alice's name
        alice_variations = ['Alice Forster', 'Alice',
                            'Forster', 'alice forster', 'alice', 'forster']

        for table_name in [table[0] for table in tables]:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Look for workout-related data
            if any(keyword in table_name.lower() for keyword in ['workout', 'exercise', 'training']):
                print(f"\n--- Workout table: {table_name} ---")

                for name_var in alice_variations:
                    for col in column_names:
                        if 'name' in col.lower() or 'client' in col.lower():
                            cursor.execute(
                                f"SELECT * FROM {table_name} WHERE {col} LIKE ? LIMIT 5", (f'%{name_var}%',))
                            rows = cursor.fetchall()
                            if rows:
                                print(
                                    f"Found Alice data in {table_name}.{col}:")
                                for row in rows:
                                    print(f"  {dict(zip(column_names, row))}")
                                break
                    if rows:
                        break

        # Look for recent workout data (last 2 weeks)
        print(f"\n=== RECENT WORKOUT DATA (LAST 2 WEEKS) ===")
        recent_date = (datetime.now() - timedelta(days=14)
                       ).strftime('%Y-%m-%d')

        for table_name in [table[0] for table in tables]:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Look for date columns
            date_columns = [
                col for col in column_names if 'date' in col.lower() or 'time' in col.lower()]

            if date_columns and any(keyword in table_name.lower() for keyword in ['workout', 'exercise']):
                date_col = date_columns[0]
                print(
                    f"\n--- Recent data in {table_name} (using {date_col}) ---")

                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE {date_col} >= ? ORDER BY {date_col} DESC LIMIT 10", (recent_date,))
                rows = cursor.fetchall()

                if rows:
                    print(f"Found {len(rows)} recent entries:")
                    for row in rows[:3]:  # Show first 3
                        print(f"  {dict(zip(column_names, row))}")

        conn.close()

    except Exception as e:
        print(f"Database inspection error: {e}")


if __name__ == "__main__":
    inspect_database_structure()
