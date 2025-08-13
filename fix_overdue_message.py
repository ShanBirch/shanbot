#!/usr/bin/env python3
"""
Fix the overdue scheduled message by updating its status
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def fix_overdue_message():
    """Fix the overdue scheduled message for @xbraxeletx by marking it as sent"""

    print("🔧 FIXING OVERDUE SCHEDULED MESSAGE")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the overdue message for @xbraxeletx
        cursor.execute("""
            SELECT schedule_id, review_id, user_ig_username, response_text, scheduled_send_time
            FROM scheduled_responses
            WHERE user_ig_username = 'xbraxeletx' 
            AND status = 'scheduled'
            ORDER BY scheduled_send_time ASC
        """)

        overdue_messages = cursor.fetchall()

        if not overdue_messages:
            print("❌ No overdue messages found for @xbraxeletx")
            return

        print(
            f"📋 Found {len(overdue_messages)} overdue message(s) for @xbraxeletx")
        print()

        for i, (schedule_id, review_id, user_ig, response_text, scheduled_time) in enumerate(overdue_messages):
            print(f"🔧 Fixing message {i+1}:")
            print(f"   📅 Scheduled: {scheduled_time}")
            print(f"   💬 Response: {response_text[:50]}...")
            print()

            try:
                # Update the scheduled response status to 'sent'
                cursor.execute("""
                    UPDATE scheduled_responses
                    SET status = 'sent', sent_at = ?
                    WHERE schedule_id = ?
                """, (datetime.now().isoformat(), schedule_id))

                # Update the pending review status to 'sent'
                cursor.execute("""
                    UPDATE pending_reviews
                    SET status = 'sent', processed_at = ?
                    WHERE review_id = ?
                """, (datetime.now().isoformat(), review_id))

                conn.commit()
                print("✅ Message status fixed successfully!")
                print(f"   📝 Updated scheduled_responses status to 'sent'")
                print(f"   📝 Updated pending_reviews status to 'sent'")
                print(f"   🕐 Fixed at: {datetime.now().isoformat()}")
                print()

            except Exception as e:
                print(f"❌ Error fixing message: {e}")
                import traceback
                traceback.print_exc()

        conn.close()
        print("🎉 Fix completed!")
        print()
        print("💡 The message will no longer appear as 'scheduled' in the dashboard.")
        print("💡 The review will no longer appear in the pending queue.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_overdue_message()
