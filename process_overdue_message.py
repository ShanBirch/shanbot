#!/usr/bin/env python3
"""
Manually process the overdue scheduled message for @xbraxeletx
"""

from dashboard_modules import response_review
import sqlite3
from datetime import datetime
import sys
import os

# Add the app directory to the path
current_dir = os.path.dirname(__file__)
app_dir = os.path.join(current_dir, 'app')
sys.path.insert(0, app_dir)


DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def process_overdue_message():
    """Manually process the overdue scheduled message for @xbraxeletx"""

    print("🚀 PROCESSING OVERDUE SCHEDULED MESSAGE")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the overdue message for @xbraxeletx
        cursor.execute("""
            SELECT * FROM scheduled_responses
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

        for i, row in enumerate(overdue_messages):
            print(f"📤 Processing message {i+1}:")
            print(f"   📅 Scheduled: {row[9]}")  # scheduled_send_time
            print(f"   💬 Response: {row[6][:50]}...")  # response_text
            print(f"   📨 Incoming: {row[5][:50]}...")  # incoming_message_text
            print()

            # Convert row to dict for processing
            scheduled_response = {
                'schedule_id': row[0],
                'review_id': row[1],
                'user_ig_username': row[2],
                'user_subscriber_id': row[3],
                'incoming_message_text': row[4],
                'incoming_message_timestamp': row[5],
                'response_text': row[6],
                'calculated_delay_minutes': row[7],
                'scheduled_send_time': row[8],
                'status': row[9],
                'created_at': row[10],
                'sent_at': row[11],
                'error_message': row[12],
                'original_response_time': row[13],
                'user_response_time': row[14],
                'user_notes': row[15],
                'manual_context': row[16],
                'processed_at': row[17],
                'ig_username': row[18]
            }

            try:
                # Use the response_review module to send the message
                print("🔄 Attempting to send message...")

                # Import the send function
                from dashboard_modules.response_review import send_scheduled_response

                # Send the message
                success = send_scheduled_response(scheduled_response)

                if success:
                    # Update status to sent
                    cursor.execute("""
                        UPDATE scheduled_responses
                        SET status = 'sent', sent_at = ?
                        WHERE schedule_id = ?
                    """, (datetime.now().isoformat(), row[0]))

                    # Update the review status
                    cursor.execute("""
                        UPDATE pending_reviews
                        SET status = 'sent', processed_at = ?
                        WHERE review_id = ?
                    """, (datetime.now().isoformat(), row[1]))

                    conn.commit()
                    print("✅ Message sent successfully!")
                    print(f"   📝 Updated status to 'sent'")
                    print(f"   🕐 Sent at: {datetime.now().isoformat()}")
                else:
                    print("❌ Failed to send message")
                    # Mark as failed
                    cursor.execute("""
                        UPDATE scheduled_responses
                        SET status = 'failed'
                        WHERE schedule_id = ?
                    """, (row[0],))
                    conn.commit()

            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()

        conn.close()
        print("\n🎉 Processing completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    process_overdue_message()
