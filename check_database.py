#!/usr/bin/env python3
"""
Quick script to check what's in the conversation_history table
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


def check_database():
    """Check what's in the database"""

    db_path = get_db_path()
    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_history'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("❌ conversation_history table does not exist!")
            return

        print("✅ conversation_history table exists")

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM conversation_history")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total conversations: {total_count}")

        if total_count == 0:
            print("❌ No conversations found in the database")
            return

        # Get date range
        cursor.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM conversation_history")
        date_range = cursor.fetchone()
        print(f"📅 Date range: {date_range[0]} to {date_range[1]}")

        # Get sample of recent conversations
        cursor.execute("""
            SELECT ig_username, message_type, message_text, timestamp 
            FROM conversation_history 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()

        print("\n📝 Most recent 5 conversations:")
        for row in recent:
            print(
                f"  {row[3]} | {row[0]} | {row[1].upper()}: {row[2][:50]}{'...' if len(row[2]) > 50 else ''}")

        # Get user counts
        cursor.execute(
            "SELECT COUNT(DISTINCT ig_username) FROM conversation_history")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Unique users: {user_count}")

        # Get message type breakdown
        cursor.execute(
            "SELECT message_type, COUNT(*) FROM conversation_history GROUP BY message_type")
        message_types = cursor.fetchall()
        print("\n📈 Message types:")
        for msg_type, count in message_types:
            print(f"  {msg_type}: {count}")

    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_database()
