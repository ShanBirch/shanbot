#!/usr/bin/env python3
"""
Simple search for Calendly links and challenge sign-ups.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def simple_search():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 SIMPLE SEARCH RESULTS")
    print("=" * 50)

    # Count total messages
    cursor.execute("SELECT COUNT(*) FROM conversation_history")
    total = cursor.fetchone()[0]
    print(f"Total messages: {total}")

    # Search for Calendly links
    cursor.execute("""
        SELECT COUNT(*) FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
    """)
    calendly_count = cursor.fetchone()[0]
    print(f"Calendly links found: {calendly_count}")

    # Search for challenge sign-ups
    cursor.execute("""
        SELECT COUNT(*) FROM conversation_history 
        WHERE (message_text LIKE '%ready to join%' 
               OR message_text LIKE '%want to join%'
               OR message_text LIKE '%sign me up%'
               OR message_text LIKE '%I want to join%')
        AND message_type = 'user'
    """)
    challenge_count = cursor.fetchone()[0]
    print(f"Challenge sign-ups found: {challenge_count}")

    # Get actual Calendly links
    cursor.execute("""
        SELECT ig_username, message_text, timestamp 
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    calendly_results = cursor.fetchall()

    print(f"\n📅 CALENDLY LINKS SENT:")
    for i, (username, text, timestamp) in enumerate(calendly_results, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   {text[:80]}...")
        print()

    # Get actual challenge sign-ups
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

    print(f"🏆 CHALLENGE SIGN-UPS:")
    for i, (username, text, timestamp) in enumerate(challenge_results, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   {text[:80]}...")
        print()

    # Get unique users
    all_users = set()
    for username, _, _ in calendly_results:
        all_users.add(username)
    for username, _, _ in challenge_results:
        all_users.add(username)

    print(f"👥 TOTAL UNIQUE USERS: {len(all_users)}")
    for username in sorted(all_users):
        print(f"  • @{username}")

    conn.close()


if __name__ == "__main__":
    simple_search()
