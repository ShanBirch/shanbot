#!/usr/bin/env python3
"""
Comprehensive final report of ad responses and sign-up data.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def generate_final_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📊 SHANBOT COMPREHENSIVE ANALYTICS REPORT")
    print("=" * 60)

    # Get data from conversation_history table
    cursor.execute("SELECT COUNT(*) FROM conversation_history")
    total_messages = cursor.fetchone()[0]

    # Calendly links
    cursor.execute("""
        SELECT ig_username, message_text, timestamp 
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    calendly_results = cursor.fetchall()

    # Challenge sign-ups
    cursor.execute("""
        SELECT ig_username, message_text, timestamp 
        FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%')
        AND message_type = 'user'
        ORDER BY timestamp DESC
    """)
    challenge_results = cursor.fetchall()

    # Get data from messages table (ad responses)
    cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE lead_source = 'paid_plant_based_challenge'
    """)
    ad_responses = cursor.fetchone()[0]

    print(f"📈 DATABASE OVERVIEW:")
    print(f"   Total Messages in conversation_history: {total_messages}")
    print(f"   Ad Responses (from messages table): {ad_responses}")
    print()

    print(f"📅 CALENDLY LINKS SENT: {len(calendly_results)}")
    print("-" * 50)
    for i, (username, text, timestamp) in enumerate(calendly_results, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    print(f"🏆 CHALLENGE SIGN-UPS: {len(challenge_results)}")
    print("-" * 50)
    for i, (username, text, timestamp) in enumerate(challenge_results, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Get unique users from both sources
    calendly_users = set(username for username, _, _ in calendly_results)
    challenge_users = set(username for username, _, _ in challenge_results)

    # Get ad response users
    cursor.execute("""
        SELECT DISTINCT ig_username FROM messages 
        WHERE lead_source = 'paid_plant_based_challenge'
    """)
    ad_users = set(row[0] for row in cursor.fetchall())

    all_users = calendly_users | challenge_users | ad_users

    print(f"👥 TOTAL UNIQUE USERS: {len(all_users)}")
    print("-" * 50)
    print("Users who received Calendly links:")
    for username in sorted(calendly_users):
        print(f"  • @{username}")

    print("\nUsers who signed up for challenges:")
    for username in sorted(challenge_users):
        print(f"  • @{username}")

    print("\nUsers who responded to ads:")
    for username in sorted(ad_users):
        print(f"  • @{username}")

    # Recent activity (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n📊 LAST 30 DAYS ACTIVITY")
    print("=" * 60)

    # Recent Calendly links (simplified date check)
    recent_calendly = []
    for username, text, timestamp in calendly_results:
        try:
            # Handle different timestamp formats
            if '+10:00' in timestamp:
                clean_timestamp = timestamp.replace('+10:00', '')
            else:
                clean_timestamp = timestamp
            msg_date = datetime.fromisoformat(clean_timestamp)
            if msg_date >= start_date:
                recent_calendly.append((username, text, timestamp))
        except:
            # If we can't parse the date, include it anyway
            recent_calendly.append((username, text, timestamp))

    print(f"📅 Recent Calendly Links: {len(recent_calendly)}")
    for username, text, timestamp in recent_calendly:
        print(f"  • @{username} - {timestamp}")

    # Recent challenge sign-ups (simplified date check)
    recent_challenges = []
    for username, text, timestamp in challenge_results:
        try:
            # Handle different timestamp formats
            if '+10:00' in timestamp:
                clean_timestamp = timestamp.replace('+10:00', '')
            else:
                clean_timestamp = timestamp
            msg_date = datetime.fromisoformat(clean_timestamp)
            if msg_date >= start_date:
                recent_challenges.append((username, text, timestamp))
        except:
            # If we can't parse the date, include it anyway
            recent_challenges.append((username, text, timestamp))

    print(f"\n🏆 Recent Challenge Sign-ups: {len(recent_challenges)}")
    for username, text, timestamp in recent_challenges:
        print(f"  • @{username} - {timestamp}")

    conn.close()


if __name__ == "__main__":
    generate_final_report()
