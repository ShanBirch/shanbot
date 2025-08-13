#!/usr/bin/env python3
"""
Targeted search for specific Calendly link and challenge sign-up messages.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def search_specific_patterns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🎯 TARGETED SEARCH RESULTS")
    print("=" * 60)

    # Search for the specific Calendly link
    cursor.execute("""
        SELECT 
            ig_username,
            text,
            timestamp,
            sender
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)

    calendly_results = cursor.fetchall()

    print(f"📅 CALENDLY LINKS SENT: {len(calendly_results)}")
    print("-" * 50)
    for i, (username, text, timestamp, sender) in enumerate(calendly_results, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Search for "I'm Ready to join the Vegan Weight Loss Challenge"
    cursor.execute("""
        SELECT 
            ig_username,
            text,
            timestamp,
            sender
        FROM messages 
        WHERE text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%'
        ORDER BY timestamp DESC
    """)

    challenge_results = cursor.fetchall()

    print(f"🏆 CHALLENGE SIGN-UPS: {len(challenge_results)}")
    print("-" * 50)
    for i, (username, text, timestamp, sender) in enumerate(challenge_results, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Search for variations of "ready to join"
    cursor.execute("""
        SELECT 
            ig_username,
            text,
            timestamp,
            sender
        FROM messages 
        WHERE (text LIKE '%ready to join%' 
               OR text LIKE '%want to join%'
               OR text LIKE '%sign me up%'
               OR text LIKE '%I want to join%')
        AND sender = 'user'
        ORDER BY timestamp DESC
    """)

    join_variations = cursor.fetchall()

    print(f"📝 JOIN VARIATIONS: {len(join_variations)}")
    print("-" * 50)
    for i, (username, text, timestamp, sender) in enumerate(join_variations, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # Get all unique users who sent either type of message
    all_users = set()

    for username, _, _, _ in calendly_results:
        all_users.add(username)

    for username, _, _, _ in challenge_results:
        all_users.add(username)

    for username, _, _, _ in join_variations:
        all_users.add(username)

    print(f"👥 TOTAL UNIQUE USERS: {len(all_users)}")
    print("-" * 50)
    for i, username in enumerate(sorted(all_users), 1):
        print(f"{i}. @{username}")

    conn.close()


def search_last_30_days():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n📊 LAST 30 DAYS ANALYSIS")
    print("=" * 60)

    # Calendly links in last 30 days
    cursor.execute("""
        SELECT 
            ig_username,
            text,
            timestamp,
            sender
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (start_date.isoformat(),))

    recent_calendly = cursor.fetchall()

    print(f"📅 RECENT CALENDLY LINKS (Last 30 days): {len(recent_calendly)}")
    print("-" * 50)
    for i, (username, text, timestamp, sender) in enumerate(recent_calendly, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   Message: {text[:80]}...")
        print()

    # Challenge sign-ups in last 30 days
    cursor.execute("""
        SELECT 
            ig_username,
            text,
            timestamp,
            sender
        FROM messages 
        WHERE (text LIKE '%ready to join%' 
               OR text LIKE '%want to join%'
               OR text LIKE '%sign me up%'
               OR text LIKE '%I want to join%')
        AND sender = 'user'
        AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (start_date.isoformat(),))

    recent_signups = cursor.fetchall()

    print(f"🏆 RECENT SIGN-UPS (Last 30 days): {len(recent_signups)}")
    print("-" * 50)
    for i, (username, text, timestamp, sender) in enumerate(recent_signups, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   Message: {text[:80]}...")
        print()

    conn.close()


if __name__ == "__main__":
    search_specific_patterns()
    search_last_30_days()
