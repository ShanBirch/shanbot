#!/usr/bin/env python3
"""
Check scheduled messages and their status
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def check_scheduled_messages():
    """Check what scheduled messages exist and their status."""

    print("📅 CHECKING SCHEDULED MESSAGES")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if scheduled_responses table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scheduled_responses'
        """)

        if not cursor.fetchone():
            print("❌ scheduled_responses table doesn't exist")
            return

        # Check the actual structure of the table
        cursor.execute("PRAGMA table_info(scheduled_responses)")
        columns = cursor.fetchall()
        print("📋 Table structure:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
        print()

        # Get all scheduled responses with correct column names
        cursor.execute("""
            SELECT 
                review_id,
                user_ig_username,
                response_text,
                incoming_message_text,
                scheduled_send_time,
                calculated_delay_minutes,
                status
            FROM scheduled_responses
            ORDER BY scheduled_send_time DESC
            LIMIT 10
        """)

        scheduled_messages = cursor.fetchall()

        if not scheduled_messages:
            print("📭 No scheduled messages found")
        else:
            print(f"📋 Found {len(scheduled_messages)} scheduled messages:")
            print()

            for msg in scheduled_messages:
                review_id, user_ig, response_text, incoming_msg, scheduled_time, delay_mins, status = msg

                # Calculate if it's overdue
                try:
                    scheduled_dt = datetime.fromisoformat(
                        scheduled_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    is_overdue = scheduled_dt < now
                    time_diff = now - scheduled_dt

                    status_icon = "🔴" if is_overdue else "🟡" if scheduled_dt.hour == now.hour else "🟢"
                    overdue_text = f" (OVERDUE by {time_diff.total_seconds()/60:.1f} mins)" if is_overdue else ""

                except Exception as e:
                    status_icon = "❓"
                    overdue_text = f" (Error parsing time: {e})"

                print(f"{status_icon} **Review ID {review_id}** - @{user_ig}")
                print(f"   📅 Scheduled: {scheduled_time}")
                print(f"   ⏱️  Delay: {delay_mins} minutes")
                print(f"   📝 Status: {status}")
                print(f"   💬 Response: {response_text[:50]}...")
                print(f"   📨 Incoming: {incoming_msg[:50]}...")
                print(f"   {overdue_text}")
                print()

        # Check pending reviews
        cursor.execute("""
            SELECT 
                review_id,
                user_ig_username,
                incoming_message_text,
                proposed_response_text,
                status
            FROM pending_reviews
            WHERE status = 'auto_scheduled'
            ORDER BY review_id DESC
            LIMIT 5
        """)

        auto_scheduled_reviews = cursor.fetchall()

        if auto_scheduled_reviews:
            print(
                f"🤖 Found {len(auto_scheduled_reviews)} auto-scheduled reviews:")
            print()

            for review in auto_scheduled_reviews:
                review_id, user_ig, incoming_msg, proposed_resp, status = review
                print(f"🔄 **Review ID {review_id}** - @{user_ig}")
                print(f"   📝 Status: {status}")
                print(f"   💬 Incoming: {incoming_msg[:50]}...")
                print(f"   🤖 Proposed: {proposed_resp[:50]}...")
                print()

        conn.close()

    except Exception as e:
        print(f"❌ Error checking scheduled messages: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_scheduled_messages()
