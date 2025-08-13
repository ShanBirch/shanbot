#!/usr/bin/env python3
"""
Search the conversation_history table for Calendly links and challenge sign-ups.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def search_conversation_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 SEARCHING CONVERSATION HISTORY TABLE")
    print("=" * 60)

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM conversation_history")
    total_messages = cursor.fetchone()[0]
    print(f"Total messages in conversation_history: {total_messages}")

    # Search for Calendly links
    cursor.execute("""
        SELECT 
            ig_username,
            message_text,
            timestamp,
            message_type
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)

    calendly_results = cursor.fetchall()

    print(f"\n📅 CALENDLY LINKS FOUND: {len(calendly_results)}")
    print("-" * 50)
    for i, (username, text, timestamp, msg_type) in enumerate(calendly_results, 1):
        print(f"{i}. @{username} ({msg_type}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Search for challenge sign-ups
    cursor.execute("""
        SELECT 
            ig_username,
            message_text,
            timestamp,
            message_type
        FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%'
               OR message_text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        AND message_type = 'user'
        ORDER BY timestamp DESC
    """)

    challenge_results = cursor.fetchall()

    print(f"🏆 CHALLENGE SIGN-UPS FOUND: {len(challenge_results)}")
    print("-" * 50)
    for i, (username, text, timestamp, msg_type) in enumerate(challenge_results, 1):
        print(f"{i}. @{username} ({msg_type}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Search for any mention of "challenge"
    cursor.execute("""
        SELECT 
            ig_username,
            message_text,
            timestamp,
            message_type
        FROM conversation_history 
        WHERE message_text LIKE '%challenge%'
        ORDER BY timestamp DESC
    """)

    challenge_mentions = cursor.fetchall()

    print(f"💬 CHALLENGE MENTIONS: {len(challenge_mentions)}")
    print("-" * 50)
    # Show first 10
    for i, (username, text, timestamp, msg_type) in enumerate(challenge_mentions[:10], 1):
        print(f"{i}. @{username} ({msg_type}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Get unique users who sent either type of message
    all_users = set()

    for username, _, _, _ in calendly_results:
        all_users.add(username)

    for username, _, _, _ in challenge_results:
        all_users.add(username)

    print(f"👥 TOTAL UNIQUE USERS: {len(all_users)}")
    print("-" * 50)
    for i, username in enumerate(sorted(all_users), 1):
        print(f"{i}. @{username}")

    # Search last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n📊 LAST 30 DAYS ANALYSIS")
    print("=" * 60)

    # Recent Calendly links
    cursor.execute("""
        SELECT 
            ig_username,
            message_text,
            timestamp,
            message_type
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (start_date.isoformat(),))

    recent_calendly = cursor.fetchall()

    print(f"📅 RECENT CALENDLY LINKS (Last 30 days): {len(recent_calendly)}")
    print("-" * 50)
    for i, (username, text, timestamp, msg_type) in enumerate(recent_calendly, 1):
        print(f"{i}. @{username} ({msg_type}) - {timestamp}")
        print(f"   Message: {text[:80]}...")
        print()

    # Recent challenge sign-ups
    cursor.execute("""
        SELECT 
            ig_username,
            message_text,
            timestamp,
            message_type
        FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%'
               OR message_text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        AND message_type = 'user'
        AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (start_date.isoformat(),))

    recent_signups = cursor.fetchall()

    print(f"🏆 RECENT SIGN-UPS (Last 30 days): {len(recent_signups)}")
    print("-" * 50)
    for i, (username, text, timestamp, msg_type) in enumerate(recent_signups, 1):
        print(f"{i}. @{username} ({msg_type}) - {timestamp}")
        print(f"   Message: {text[:80]}...")
        print()

    conn.close()


if __name__ == "__main__":
    search_conversation_history()
