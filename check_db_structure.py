#!/usr/bin/env python3
"""
Check database structure to understand where conversation history is stored.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def examine_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 DATABASE STRUCTURE ANALYSIS")
    print("=" * 60)

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"📋 ALL TABLES ({len(tables)}):")
    for table in tables:
        print(f"  • {table[0]}")
    print()

    # Examine each table structure
    for table_name in [t[0] for t in tables]:
        print(f"📊 TABLE: {table_name}")
        print("-" * 40)

        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print("Columns:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")

        # Get sample data
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            print("Sample data:")
            for i, row in enumerate(sample_rows, 1):
                print(f"  Row {i}: {row}")
        print()

    # Look for conversation-related fields
    print("🔍 SEARCHING FOR CONVERSATION FIELDS")
    print("-" * 40)

    for table_name in [t[0] for t in tables]:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        conversation_fields = []
        for col in columns:
            col_name = col[1].lower()
            if any(keyword in col_name for keyword in ['conversation', 'message', 'text', 'chat', 'history']):
                conversation_fields.append(col[1])

        if conversation_fields:
            print(
                f"Table '{table_name}' has conversation fields: {conversation_fields}")

    # Check for JSON fields that might contain conversation data
    print("\n🔍 SEARCHING FOR JSON FIELDS")
    print("-" * 40)

    for table_name in [t[0] for t in tables]:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        json_fields = []
        for col in columns:
            col_name = col[1].lower()
            if 'json' in col_name:
                json_fields.append(col[1])

        if json_fields:
            print(f"Table '{table_name}' has JSON fields: {json_fields}")

            # Check sample JSON data
            for field in json_fields:
                cursor.execute(
                    f"SELECT {field} FROM {table_name} WHERE {field} IS NOT NULL LIMIT 1")
                result = cursor.fetchone()
                if result and result[0]:
                    print(f"  Sample {field}: {result[0][:200]}...")

    conn.close()


if __name__ == "__main__":
    examine_database()
