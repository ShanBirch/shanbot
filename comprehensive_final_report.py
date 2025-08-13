#!/usr/bin/env python3
"""
Comprehensive final report showing all actual sent Calendly links and challenge sign-ups.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def comprehensive_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📊 COMPREHENSIVE SHANBOT ANALYTICS REPORT")
    print("=" * 60)

    # Get actual sent Calendly links from conversation_history
    cursor.execute("""
        SELECT ig_username, message_text, timestamp 
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    conversation_calendly = cursor.fetchall()

    # Get actual sent Calendly links from scheduled_responses
    cursor.execute("""
        SELECT user_ig_username, response_text, scheduled_send_time 
        FROM scheduled_responses 
        WHERE response_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND status = 'sent'
        ORDER BY scheduled_send_time DESC
    """)
    scheduled_calendly = cursor.fetchall()

    # Get actual sent Calendly links from messages table
    cursor.execute("""
        SELECT ig_username, text, timestamp 
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    messages_calendly = cursor.fetchall()

    # Get challenge sign-ups from conversation_history
    cursor.execute("""
        SELECT ig_username, message_text, timestamp 
        FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%'
               OR message_text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        AND message_type = 'user'
        ORDER BY timestamp DESC
    """)
    challenge_signups = cursor.fetchall()

    print(f"📅 ACTUAL CALENDLY LINKS SENT:")
    print(f"   From conversation_history: {len(conversation_calendly)}")
    print(f"   From scheduled_responses: {len(scheduled_calendly)}")
    print(f"   From messages table: {len(messages_calendly)}")
    print(
        f"   TOTAL: {len(conversation_calendly) + len(scheduled_calendly) + len(messages_calendly)}")
    print()

    # Combine all Calendly links and remove duplicates
    all_calendly = []

    # Add from conversation_history
    for username, text, timestamp in conversation_calendly:
        all_calendly.append(
            (username, text, timestamp, 'conversation_history'))

    # Add from scheduled_responses
    for username, text, timestamp in scheduled_calendly:
        all_calendly.append((username, text, timestamp, 'scheduled_responses'))

    # Add from messages table
    for username, text, timestamp in messages_calendly:
        all_calendly.append((username, text, timestamp, 'messages'))

    # Remove duplicates based on username and timestamp
    unique_calendly = []
    seen = set()

    for username, text, timestamp, source in all_calendly:
        # Create a key based on username and timestamp (within 1 hour)
        try:
            if isinstance(timestamp, str):
                if '+10:00' in timestamp:
                    clean_timestamp = timestamp.replace('+10:00', '')
                else:
                    clean_timestamp = timestamp
                dt = datetime.fromisoformat(clean_timestamp)
                key = (username, dt.strftime('%Y-%m-%d %H'))
            else:
                key = (username, timestamp)
        except:
            key = (username, str(timestamp))

        if key not in seen:
            seen.add(key)
            unique_calendly.append((username, text, timestamp, source))

    print(f"📅 UNIQUE CALENDLY LINKS SENT: {len(unique_calendly)}")
    print("-" * 50)
    for i, (username, text, timestamp, source) in enumerate(unique_calendly, 1):
        print(f"{i}. @{username} ({source}) - {timestamp}")
        print(f"   {text[:80]}...")
        print()

    print(f"🏆 CHALLENGE SIGN-UPS: {len(challenge_signups)}")
    print("-" * 50)
    for i, (username, text, timestamp) in enumerate(challenge_signups, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   {text[:80]}...")
        print()

    # Get unique users
    calendly_users = set(username for username, _, _, _ in unique_calendly)
    challenge_users = set(username for username, _, _ in challenge_signups)

    print(f"👥 UNIQUE USERS WHO RECEIVED CALENDLY LINKS: {len(calendly_users)}")
    print("-" * 50)
    for username in sorted(calendly_users):
        print(f"  • @{username}")

    print(
        f"\n👥 UNIQUE USERS WHO SIGNED UP FOR CHALLENGES: {len(challenge_users)}")
    print("-" * 50)
    for username in sorted(challenge_users):
        print(f"  • @{username}")

    # Recent activity (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n📊 LAST 30 DAYS ACTIVITY")
    print("=" * 60)

    recent_calendly = []
    for username, text, timestamp, source in unique_calendly:
        try:
            if isinstance(timestamp, str):
                if '+10:00' in timestamp:
                    clean_timestamp = timestamp.replace('+10:00', '')
                else:
                    clean_timestamp = timestamp
                dt = datetime.fromisoformat(clean_timestamp)
                if dt >= start_date:
                    recent_calendly.append((username, text, timestamp, source))
        except:
            # If we can't parse the date, include it
            recent_calendly.append((username, text, timestamp, source))

    print(f"📅 Recent Calendly Links (Last 30 days): {len(recent_calendly)}")
    for username, text, timestamp, source in recent_calendly:
        print(f"  • @{username} ({source}) - {timestamp}")

    recent_challenges = []
    for username, text, timestamp in challenge_signups:
        try:
            if isinstance(timestamp, str):
                if '+10:00' in timestamp:
                    clean_timestamp = timestamp.replace('+10:00', '')
                else:
                    clean_timestamp = timestamp
                dt = datetime.fromisoformat(clean_timestamp)
                if dt >= start_date:
                    recent_challenges.append((username, text, timestamp))
        except:
            # If we can't parse the date, include it
            recent_challenges.append((username, text, timestamp))

    print(
        f"\n🏆 Recent Challenge Sign-ups (Last 30 days): {len(recent_challenges)}")
    for username, text, timestamp in recent_challenges:
        print(f"  • @{username} - {timestamp}")

    conn.close()


if __name__ == "__main__":
    comprehensive_report()
