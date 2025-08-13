#!/usr/bin/env python3
"""
Fix the missing user message by adding it to the messages table
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def fix_missing_user_message():
    """Add the missing user message to the messages table for @xbraxeletx"""

    print("🔧 FIXING MISSING USER MESSAGE")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the user's original message from pending_reviews
        cursor.execute("""
            SELECT 
                review_id,
                user_ig_username,
                incoming_message_text,
                created_timestamp
            FROM pending_reviews
            WHERE user_ig_username = 'xbraxeletx'
            ORDER BY review_id DESC
            LIMIT 1
        """)

        review = cursor.fetchone()

        if not review:
            print("❌ No pending review found for @xbraxeletx")
            return

        review_id, user_ig, incoming_msg, created_timestamp = review

        print(f"📋 Found user's original message:")
        print(f"   💬 Message: {incoming_msg}")
        print(f"   🕐 Created: {created_timestamp}")
        print()

        # Check if this message is already in the messages table
        cursor.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE ig_username = 'xbraxeletx' 
            AND message_text = ?
        """, (incoming_msg,))

        exists = cursor.fetchone()[0] > 0

        if exists:
            print("✅ User message already exists in messages table")
            return

        # Add the user message to the messages table
        # Use the same timestamp as the review creation
        user_timestamp = created_timestamp if created_timestamp else datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO messages (
                ig_username, 
                message_type, 
                message_text, 
                timestamp
            ) VALUES (?, ?, ?, ?)
        """, (user_ig, 'user', incoming_msg, user_timestamp))

        conn.commit()
        print("✅ User message added to messages table successfully!")
        print(f"   📝 Added: [{user_ig}] {incoming_msg[:50]}...")
        print(f"   🕐 Timestamp: {user_timestamp}")
        print()
        print("💡 The conversation history should now show both user and AI messages.")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_missing_user_message()
