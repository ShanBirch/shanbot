#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta


def check_dm_vs_conversation_history():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    print("Checking if DMs were sent but not recorded properly...")

    # Check recent AI messages in conversation history
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    c.execute("""
        SELECT COUNT(*) 
        FROM conversation_history 
        WHERE message_type = 'ai' 
        AND timestamp >= ?
    """, (seven_days_ago,))

    ai_messages_count = c.fetchone()[0]
    print(f"AI messages sent in last 7 days: {ai_messages_count}")

    # Check DMs marked as sent in processing_queue
    c.execute("""
        SELECT COUNT(*) 
        FROM processing_queue 
        WHERE dm_status = 'sent'
        AND follow_back_checked_at >= ?
    """, (seven_days_ago,))

    recorded_dms = c.fetchone()[0]
    print(f"DMs recorded as 'sent' in processing_queue: {recorded_dms}")

    # Check users who followed back recently
    c.execute("""
        SELECT COUNT(*) 
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND follow_back_checked_at >= ?
    """, (seven_days_ago,))

    recent_followers = c.fetchone()[0]
    print(f"Users who followed back in last 7 days: {recent_followers}")

    # Check specific usernames to see if they have conversation history
    print("\nChecking specific users who need DMs:")

    c.execute("""
        SELECT username 
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
        ORDER BY follow_back_checked_at DESC
        LIMIT 5
    """)

    users_needing_dms = c.fetchall()

    for (username,) in users_needing_dms:
        # Check if this user has conversation history
        c.execute("""
            SELECT COUNT(*), MAX(timestamp)
            FROM conversation_history 
            WHERE ig_username = ?
        """, (username,))

        conv_count, last_msg = c.fetchone()
        print(f"  {username}: {conv_count} messages, last: {last_msg or 'None'}")

    conn.close()


if __name__ == "__main__":
    check_dm_vs_conversation_history()
