#!/usr/bin/env python3
"""
Deep search for Calendly links across all tables and formats.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def deep_search():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 DEEP SEARCH FOR ALL CALENDLY LINKS")
    print("=" * 60)

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    total_calendly_found = 0

    for table_name in [t[0] for t in tables]:
        print(f"\n📊 SEARCHING TABLE: {table_name}")
        print("-" * 40)

        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # Find text/message columns
        text_columns = []
        for col in columns:
            col_name = col[1].lower()
            if any(keyword in col_name for keyword in ['text', 'message', 'content', 'data']):
                text_columns.append(col[1])

        if not text_columns:
            print("  No text columns found")
            continue

        # Search each text column for Calendly links
        for column in text_columns:
            try:
                # Search for various Calendly patterns
                patterns = [
                    '%calendly.com/shannonrhysbirch/15min%',
                    '%calendly%',
                    '%shannonrhysbirch%',
                    '%15min%'
                ]

                for pattern in patterns:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE {column} LIKE ?
                    """, (pattern,))
                    count = cursor.fetchone()[0]

                    if count > 0:
                        print(
                            f"  Found {count} matches in {column} with pattern: {pattern}")

                        # Get the actual data
                        cursor.execute(f"""
                            SELECT * FROM {table_name} 
                            WHERE {column} LIKE ?
                            LIMIT 5
                        """, (pattern,))
                        results = cursor.fetchall()

                        for i, row in enumerate(results, 1):
                            print(f"    Row {i}: {row}")

                        total_calendly_found += count

            except Exception as e:
                print(f"  Error searching {column}: {e}")

    print(f"\n🎯 TOTAL CALENDLY REFERENCES FOUND: {total_calendly_found}")

    # Also check the messages table specifically
    print(f"\n📋 SPECIFIC MESSAGES TABLE SEARCH")
    print("-" * 40)

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE text LIKE '%calendly%'
        """)
        messages_calendly = cursor.fetchone()[0]
        print(f"Calendly references in messages table: {messages_calendly}")

        if messages_calendly > 0:
            cursor.execute("""
                SELECT ig_username, text, timestamp 
                FROM messages 
                WHERE text LIKE '%calendly%'
                ORDER BY timestamp DESC
            """)
            messages_results = cursor.fetchall()

            for i, (username, text, timestamp) in enumerate(messages_results, 1):
                print(f"{i}. @{username} - {timestamp}")
                print(f"   {text[:100]}...")
                print()

    except Exception as e:
        print(f"Error searching messages table: {e}")

    # Check for any JSON fields that might contain conversation data
    print(f"\n🔍 SEARCHING JSON FIELDS")
    print("-" * 40)

    for table_name in [t[0] for t in tables]:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        json_columns = []
        for col in columns:
            col_name = col[1].lower()
            if 'json' in col_name:
                json_columns.append(col[1])

        if json_columns:
            print(f"Table {table_name} has JSON columns: {json_columns}")

            for column in json_columns:
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE {column} LIKE '%calendly%'
                    """)
                    count = cursor.fetchone()[0]

                    if count > 0:
                        print(
                            f"  Found {count} Calendly references in {column}")

                        cursor.execute(f"""
                            SELECT {column} FROM {table_name} 
                            WHERE {column} LIKE '%calendly%'
                            LIMIT 3
                        """)
                        results = cursor.fetchall()

                        for i, (json_data,) in enumerate(results, 1):
                            print(f"    JSON {i}: {json_data[:200]}...")

                except Exception as e:
                    print(f"  Error searching {column}: {e}")

    conn.close()


if __name__ == "__main__":
    deep_search()
