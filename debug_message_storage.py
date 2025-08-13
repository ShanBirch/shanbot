#!/usr/bin/env python3
"""
Debug why user messages aren't being stored in the messages table
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def debug_message_storage():
    """Debug the message storage issue for @xbraxeletx"""

    print("🔍 DEBUGGING MESSAGE STORAGE ISSUE")
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

        for i, (new_text, new_type, old_type, old_text, sender, old_message, timestamp) in enumerate(messages):
            # Use new standardized columns first, fall back to old columns
            final_text = new_text if new_text is not None else (
                old_text if old_text is not None else old_message)
            final_type = new_type if new_type is not None else (
                old_type if old_type is not None else sender)

            print(f"{i+1}. [{final_type}] {final_text[:50]}... ({timestamp})")

        print()

        # Check pending_reviews for the user's original message
        cursor.execute("""
            SELECT 
                review_id,
                user_ig_username,
                incoming_message_text,
                proposed_response_text,
                status,
                created_at
            FROM pending_reviews
            WHERE user_ig_username = 'xbraxeletx'
            ORDER BY review_id DESC
        """)

        reviews = cursor.fetchall()

        print(f"📋 Found {len(reviews)} pending reviews for @xbraxeletx:")
        print()

        for review in reviews:
            review_id, user_ig, incoming_msg, proposed_resp, status, created_at = review
            print(f"🔄 **Review ID {review_id}** - @{user_ig}")
            print(f"   📝 Status: {status}")
            print(f"   💬 Incoming: {incoming_msg[:50]}...")
            print(f"   🤖 Proposed: {proposed_resp[:50]}...")
            print(f"   🕐 Created: {created_at}")
            print()

        # Check if the user's original message should be in messages table
        if reviews:
            original_message = reviews[0][2]  # incoming_message_text
            print(f"🔍 The user's original message was: '{original_message}'")
            print(f"❌ This message is NOT in the messages table!")
            print()
            print(
                "💡 PROBLEM: The user's incoming message is only stored in pending_reviews,")
            print(
                "   but not in the messages table. This is why conversation history is incomplete.")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_message_storage()
