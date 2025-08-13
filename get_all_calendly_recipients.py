#!/usr/bin/env python3
"""
Get everyone who received Calendly links from both tables.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_all_calendly_recipients():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📅 EVERYONE WHO RECEIVED CALENDLY LINKS")
    print("=" * 70)

    # Get from conversation_history table
    cursor.execute("""
        SELECT DISTINCT ig_username, message_text, timestamp
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND message_type = 'shannon'
        ORDER BY timestamp DESC
    """)
    conv_recipients = cursor.fetchall()

    # Get from messages table
    cursor.execute("""
        SELECT DISTINCT ig_username, text, timestamp
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND sender = 'shannon'
        ORDER BY timestamp DESC
    """)
    msg_recipients = cursor.fetchall()

    # Combine and remove duplicates
    all_recipients = []
    seen_users = set()

    # Add from conversation_history
    for username, text, timestamp in conv_recipients:
        if username not in seen_users:
            all_recipients.append(
                (username, text, timestamp, 'conversation_history'))
            seen_users.add(username)

    # Add from messages (if not already added)
    for username, text, timestamp in msg_recipients:
        if username not in seen_users:
            all_recipients.append((username, text, timestamp, 'messages'))
            seen_users.add(username)

    print(f"📅 TOTAL RECIPIENTS: {len(all_recipients)}")
    print("-" * 50)

    for i, (username, text, timestamp, source) in enumerate(all_recipients, 1):
        print(f"{i}. @{username} ({source}) - {timestamp}")
        print(f"   {text[:80]}...")
        print()

    # Check who signed up
    print(f"🏆 WHO SIGNED UP:")
    print("-" * 50)

    # Get sign-ups from conversation_history
    cursor.execute("""
        SELECT DISTINCT ig_username 
        FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%'
               OR message_text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        AND message_type = 'user'
    """)
    conv_signups = [row[0] for row in cursor.fetchall()]

    # Get sign-ups from messages
    cursor.execute("""
        SELECT DISTINCT ig_username 
        FROM messages 
        WHERE (text LIKE '%ready to join%' 
               OR text LIKE '%want to join%'
               OR text LIKE '%sign me up%'
               OR text LIKE '%I want to join%'
               OR text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        AND sender = 'user'
    """)
    msg_signups = [row[0] for row in cursor.fetchall()]

    all_signups = set(conv_signups + msg_signups)

    for username in sorted(all_signups):
        if username in seen_users:
            print(f"  ✅ @{username} - SIGNED UP")
        else:
            print(f"  ❌ @{username} - DID NOT SIGN UP")

    # Show who didn't sign up
    print(f"\n❌ WHO DIDN'T SIGN UP:")
    print("-" * 50)

    all_usernames = [username for username, _, _, _ in all_recipients]
    non_signups = [
        username for username in all_usernames if username not in all_signups]

    for username in sorted(non_signups):
        print(f"  • @{username}")

    print(f"\n📊 SUMMARY:")
    print(f"  Total recipients: {len(all_recipients)}")
    print(
        f"  Signed up: {len([u for u in all_usernames if u in all_signups])}")
    print(f"  Didn't sign up: {len(non_signups)}")

    conn.close()


if __name__ == "__main__":
    get_all_calendly_recipients()
