#!/usr/bin/env python3
"""
Test script to verify conversation history loading works with unified messages table
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def test_conversation_history_loading():
    """Test loading conversation history from the unified messages table."""

    print("🧪 TESTING CONVERSATION HISTORY LOADING")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Test 1: Check if messages table has data
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        print(f"📊 Total messages in unified table: {total_messages}")

        # Test 2: Get a sample user with recent activity
        cursor.execute("""
            SELECT DISTINCT ig_username, COUNT(*) as msg_count
            FROM messages 
            WHERE ig_username IS NOT NULL
            GROUP BY ig_username
            ORDER BY msg_count DESC
            LIMIT 5
        """)

        users = cursor.fetchall()
        print(f"\n👥 Top 5 users by message count:")
        for username, count in users:
            print(f"  • @{username}: {count} messages")

        # Test 3: Load conversation history for the first user
        if users:
            test_user = users[0][0]
            print(f"\n🔍 Testing conversation history for @{test_user}")

            cursor.execute("""
                SELECT message_text, timestamp, message_type, type, sender, subscriber_id, message, text
                FROM messages 
                WHERE ig_username = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (test_user,))

            messages = cursor.fetchall()
            print(f"📚 Found {len(messages)} recent messages")

            for i, (new_text, timestamp, new_type, old_type, sender, subscriber_id, old_message, old_text) in enumerate(messages[:3]):
                # Use new standardized columns first, fall back to old columns
                final_text = new_text if new_text is not None else (
                    old_text if old_text is not None else old_message)
                final_type = new_type if new_type is not None else (
                    old_type if old_type is not None else sender)

                print(
                    f"  {i+1}. [{final_type}] {final_text[:50]}... ({timestamp})")

        # Test 4: Check for the specific user from the logs
        test_user_from_logs = "xbraxeletx"
        print(
            f"\n🔍 Testing conversation history for @{test_user_from_logs} (from logs)")

        cursor.execute("""
            SELECT message_text, timestamp, message_type, type, sender, subscriber_id, message, text
            FROM messages 
            WHERE ig_username = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (test_user_from_logs,))

        messages = cursor.fetchall()
        print(f"📚 Found {len(messages)} messages for @{test_user_from_logs}")

        for i, (new_text, timestamp, new_type, old_type, sender, subscriber_id, old_message, old_text) in enumerate(messages):
            # Use new standardized columns first, fall back to old columns
            final_text = new_text if new_text is not None else (
                old_text if old_text is not None else old_message)
            final_type = new_type if new_type is not None else (
                old_type if old_type is not None else sender)

            print(
                f"  {i+1}. [{final_type}] {final_text[:50]}... ({timestamp})")

        conn.close()
        print("\n✅ Conversation history loading test completed successfully!")

    except Exception as e:
        print(f"❌ Error testing conversation history: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_conversation_history_loading()
