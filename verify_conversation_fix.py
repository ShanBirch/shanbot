#!/usr/bin/env python3
"""
Verify that the conversation history is now complete
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def verify_conversation_fix():
    """Verify that the conversation history is now complete for @xbraxeletx"""

    print("✅ VERIFYING CONVERSATION HISTORY FIX")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check all messages for @xbraxeletx
        cursor.execute("""
            SELECT 
                message_text, 
                message_type, 
                type, 
                text, 
                sender, 
                message,
                timestamp
            FROM messages 
            WHERE ig_username = 'xbraxeletx'
            ORDER BY timestamp ASC
        """)

        messages = cursor.fetchall()

        print(f"📋 Found {len(messages)} messages for @xbraxeletx:")
        print()

        user_count = 0
        ai_count = 0

        for i, (new_text, new_type, old_type, old_text, sender, old_message, timestamp) in enumerate(messages):
            # Use new standardized columns first, fall back to old columns
            final_text = new_text if new_text is not None else (
                old_text if old_text is not None else old_message)
            final_type = new_type if new_type is not None else (
                old_type if old_type is not None else sender)

            if final_type == 'user':
                user_count += 1
                icon = "👤"
            elif final_type == 'ai':
                ai_count += 1
                icon = "🤖"
            else:
                icon = "❓"

            print(
                f"{i+1}. {icon} [{final_type}] {final_text[:50]}... ({timestamp})")

        print()
        print(f"📊 Summary:")
        print(f"   👤 User messages: {user_count}")
        print(f"   🤖 AI messages: {ai_count}")
        print(f"   📝 Total messages: {len(messages)}")

        if user_count > 0 and ai_count > 0:
            print("✅ SUCCESS: Conversation history is now complete!")
            print("💡 Both user and AI messages are now stored in the messages table.")
        else:
            print("❌ ISSUE: Conversation history is still incomplete.")
            if user_count == 0:
                print("   - Missing user messages")
            if ai_count == 0:
                print("   - Missing AI messages")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_conversation_fix()
