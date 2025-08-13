#!/usr/bin/env python3
"""
Send DMs to users who followed back but never received a message.
"""
from check_daily_follow_backs import DailyFollowBackChecker
import sys
import os
import sqlite3
from datetime import datetime

# Add the project directory to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def send_missing_dms():
    print("🔄 Sending DMs to users who followed back but never got messaged...")

    # Get users who need DMs
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    c.execute("""
        SELECT username, followed_at, follow_back_checked_at
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
        ORDER BY follow_back_checked_at DESC
    """)

    users_needing_dms = c.fetchall()
    conn.close()

    if not users_needing_dms:
        print("✅ No users need DMs - all caught up!")
        return

    print(f"📋 Found {len(users_needing_dms)} users who need DMs:")
    for username, followed_at, checked_at in users_needing_dms:
        print(f"  • {username} (followed: {followed_at[:10]})")

    # Confirm before proceeding
    response = input(
        f"\n🤖 Send DMs to these {len(users_needing_dms)} users? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled by user")
        return

    # Initialize the checker
    checker = DailyFollowBackChecker()

    try:
        # Setup Instagram driver
        if not checker.setup_driver():
            print("❌ Failed to setup Instagram driver")
            return

        if not checker.login_to_instagram():
            print("❌ Failed to login to Instagram")
            return

        success_count = 0

        # Send DM to each user
        for username, followed_at, checked_at in users_needing_dms:
            print(f"\n📤 Processing {username}...")

            try:
                # Generate personalized DM
                dm_message = checker.generate_dm_message(username, "business")

                # Send the DM
                if checker.send_dm_to_user(username, dm_message):
                    # Mark as fresh lead and store conversation
                    checker.mark_user_as_fresh_lead(username)
                    checker.store_dm_in_conversation_history(
                        username, dm_message)

                    # Update DM status in database
                    checker.update_dm_status(username, dm_message, "sent")

                    print(f"✅ Successfully sent DM to {username}")
                    success_count += 1
                else:
                    print(f"❌ Failed to send DM to {username}")
                    checker.update_dm_status(username, dm_message, "failed")

            except Exception as e:
                print(f"❌ Error processing {username}: {e}")
                checker.update_dm_status(username, "", f"failed: {str(e)}")

        print(f"\n📊 RESULTS:")
        print(f"   ✅ Successfully sent: {success_count}")
        print(f"   ❌ Failed: {len(users_needing_dms) - success_count}")
        print(f"   📈 Total processed: {len(users_needing_dms)}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Always cleanup
        checker.teardown_driver()


if __name__ == "__main__":
    send_missing_dms()
