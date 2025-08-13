#!/usr/bin/env python3
"""
Test script to verify conversation checking logic
"""

import sqlite3
import sys
import os


def test_conversation_checking(username):
    """Test the conversation checking logic for a specific user"""

    # Database path - adjust if needed
    db_path = "app/analytics_data_good.sqlite"

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    print(f"🔍 Testing conversation check for @{username}")
    print("="*50)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test 1: Check processing_queue dm_status
        print("1️⃣ Checking processing_queue dm_status...")
        cursor.execute("""
            SELECT username, dm_status, dm_message, followed_at 
            FROM processing_queue 
            WHERE username = ?
        """, (username,))

        queue_result = cursor.fetchone()
        if queue_result:
            print(f"   ✅ Found in processing_queue:")
            print(f"      Username: {queue_result[0]}")
            print(f"      DM Status: {queue_result[1]}")
            print(f"      DM Message: {queue_result[2]}")
            print(f"      Followed At: {queue_result[3]}")

            if queue_result[1] in ['sent', 'delivered', 'already_messaged']:
                print(
                    f"   🚫 Would be SKIPPED due to dm_status: {queue_result[1]}")
            else:
                print(
                    f"   ✅ Would CONTINUE processing (dm_status: {queue_result[1]})")
        else:
            print(f"   📭 Not found in processing_queue")

        print()

        # Test 2: Check conversation_history
        print("2️⃣ Checking conversation_history...")
        cursor.execute("""
            SELECT COUNT(*) FROM conversation_history 
            WHERE ig_username = ? 
            AND message_text IS NOT NULL 
            AND message_text != ''
        """, (username,))

        total_messages = cursor.fetchone()[0]
        print(f"   📊 Total messages found: {total_messages}")

        if total_messages > 0:
            # Get recent messages
            cursor.execute("""
                SELECT message_text, timestamp, message_type 
                FROM conversation_history 
                WHERE ig_username = ? 
                AND message_text IS NOT NULL 
                AND message_text != ''
                ORDER BY timestamp DESC 
                LIMIT 3
            """, (username,))

            recent_messages = cursor.fetchall()
            print(f"   📝 Recent messages:")
            for msg in recent_messages:
                msg_type = msg[2] if msg[2] else 'unknown'
                print(f"      [{msg_type}] {msg[1]}: {msg[0][:50]}...")

            print(f"   🚫 Would be SKIPPED due to existing conversation history")
        else:
            print(f"   ✅ No conversation history found - would CONTINUE")

        print()

        # Test 3: Check for plant-based messages specifically
        print("3️⃣ Checking for plant-based intro messages...")
        cursor.execute("""
            SELECT COUNT(*) FROM conversation_history 
            WHERE ig_username = ? 
            AND message_text IS NOT NULL 
            AND message_text != ''
            AND message_text LIKE '%plant%'
        """, (username,))

        plant_messages = cursor.fetchone()[0]
        print(f"   🌱 Plant-based messages found: {plant_messages}")

        if plant_messages > 0:
            cursor.execute("""
                SELECT message_text, timestamp 
                FROM conversation_history 
                WHERE ig_username = ? 
                AND message_text LIKE '%plant%'
                ORDER BY timestamp DESC 
                LIMIT 2
            """, (username,))

            plant_msgs = cursor.fetchall()
            for msg in plant_msgs:
                print(f"      {msg[1]}: {msg[0]}")

            print(f"   🚫 Would be SKIPPED due to existing plant-based intro")

        print()

        # Final decision
        print("🎯 FINAL DECISION:")
        if queue_result and queue_result[1] in ['sent', 'delivered', 'already_messaged']:
            print(f"   🚫 SKIP - processing_queue dm_status: {queue_result[1]}")
        elif total_messages > 0:
            print(
                f"   🚫 SKIP - existing conversation history ({total_messages} messages)")
        else:
            print(f"   ✅ PROCEED - no existing conversation found")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_conversation_check.py <username>")
        print("Example: python test_conversation_check.py grateful_vegan_sunflower")
        return

    username = sys.argv[1]
    test_conversation_checking(username)


if __name__ == "__main__":
    main()
