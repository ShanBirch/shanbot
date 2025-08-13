#!/usr/bin/env python3
"""
Test conversation history loading order for regenerate function
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def test_conversation_history_order():
    """Test if conversation history is being loaded in correct order"""

    print("🔍 TESTING CONVERSATION HISTORY ORDER")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Test with @xbraxeletx since we know they have messages
        test_user = 'xbraxeletx'

        print(f"📋 Testing conversation history for @{test_user}")
        print()

        # Check current order (DESC - newest first)
        cursor.execute("""
            SELECT message_text, timestamp, message_type
            FROM messages 
            WHERE ig_username = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (test_user,))

        desc_messages = cursor.fetchall()

        print("❌ CURRENT ORDER (DESC - newest first):")
        for i, row in enumerate(desc_messages):
            text, timestamp, msg_type = row
            # Handle NULL values
            text = text or "NULL"
            timestamp = timestamp or "NULL"
            msg_type = msg_type or "NULL"
            print(f"  {i+1}. [{msg_type}] {text[:50]}... ({timestamp})")

        print()

        # Check correct order (ASC - oldest first)
        cursor.execute("""
            SELECT message_text, timestamp, message_type
            FROM messages 
            WHERE ig_username = ? 
            ORDER BY timestamp ASC 
            LIMIT 5
        """, (test_user,))

        asc_messages = cursor.fetchall()

        print("✅ CORRECT ORDER (ASC - oldest first):")
        for i, row in enumerate(asc_messages):
            text, timestamp, msg_type = row
            # Handle NULL values
            text = text or "NULL"
            timestamp = timestamp or "NULL"
            msg_type = msg_type or "NULL"
            print(f"  {i+1}. [{msg_type}] {text[:50]}... ({timestamp})")

        print()
        print("💡 PROBLEM IDENTIFIED:")
        print("   The regenerate function is loading conversation history in DESC order")
        print("   (newest first), but AI needs it in ASC order (oldest first)")
        print("   to understand the conversation flow properly.")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_conversation_history_order()
