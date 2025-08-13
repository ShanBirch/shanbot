#!/usr/bin/env python3
"""
Search through the messages table for Calendly links.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def search_messages_calendly():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 SEARCHING MESSAGES TABLE FOR CALENDLY LINKS")
    print("=" * 70)

    # Search for Calendly links in messages table
    cursor.execute("""
        SELECT ig_username, text, timestamp, sender
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    calendly_messages = cursor.fetchall()

    print(f"📅 CALENDLY LINKS FOUND IN MESSAGES: {len(calendly_messages)}")
    print("-" * 50)

    for i, (username, text, timestamp, sender) in enumerate(calendly_messages, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   {text[:100]}...")
        print()

    # Get unique users who received Calendly links
    cursor.execute("""
        SELECT DISTINCT ig_username, sender
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY ig_username
    """)
    unique_recipients = cursor.fetchall()

    print(
        f"👥 UNIQUE USERS WHO RECEIVED CALENDLY LINKS: {len(unique_recipients)}")
    print("-" * 50)
    for username, sender in unique_recipients:
        print(f"  • @{username} (sent by: {sender})")

    # Search for other Calendly patterns
    print(f"\n🔍 SEARCHING FOR OTHER CALENDLY PATTERNS")
    print("-" * 50)

    patterns = [
        '%calendly%',
        '%shannonrhysbirch%',
        '%15min%',
        '%calendar%',
        '%book%'
    ]

    for pattern in patterns:
        cursor.execute(f"""
            SELECT COUNT(*) FROM messages 
            WHERE text LIKE ?
        """, (pattern,))
        count = cursor.fetchone()[0]
        print(f"Pattern '{pattern}': {count} matches")

    # Check for challenge sign-ups in messages
    print(f"\n🏆 CHALLENGE SIGN-UPS IN MESSAGES")
    print("-" * 50)

    cursor.execute("""
        SELECT ig_username, text, timestamp, sender
        FROM messages 
        WHERE (text LIKE '%ready to join%' 
               OR text LIKE '%want to join%'
               OR text LIKE '%sign me up%'
               OR text LIKE '%I want to join%'
               OR text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
        ORDER BY timestamp DESC
    """)
    challenge_signups = cursor.fetchall()

    print(f"Challenge sign-ups found: {len(challenge_signups)}")
    for i, (username, text, timestamp, sender) in enumerate(challenge_signups, 1):
        print(f"{i}. @{username} ({sender}) - {timestamp}")
        print(f"   {text[:100]}...")
        print()

    # Get recent messages with Calendly links
    print(f"\n📅 RECENT CALENDLY MESSAGES (Last 30 days)")
    print("-" * 50)

    cursor.execute("""
        SELECT ig_username, text, timestamp, sender
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND timestamp >= datetime('now', '-30 days')
        ORDER BY timestamp DESC
    """)
    recent_calendly = cursor.fetchall()

    print(f"Recent Calendly messages: {len(recent_calendly)}")
    for username, text, timestamp, sender in recent_calendly:
        print(f"  • @{username} ({sender}) - {timestamp}")
        print(f"    {text[:80]}...")

    # Check for users who got Calendly but didn't sign up
    print(f"\n❌ USERS WHO GOT CALENDLY BUT DIDN'T SIGN UP")
    print("-" * 50)

    # Get users who received Calendly links
    cursor.execute("""
        SELECT DISTINCT ig_username FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
    """)
    calendly_recipients = [row[0] for row in cursor.fetchall()]

    # Get users who signed up for challenges
    cursor.execute("""
        SELECT DISTINCT ig_username FROM messages 
        WHERE (text LIKE '%ready to join%' 
               OR text LIKE '%want to join%'
               OR text LIKE '%sign me up%'
               OR text LIKE '%I want to join%'
               OR text LIKE '%I%m Ready to join the Vegan Weight Loss Challenge%')
    """)
    challenge_recipients = [row[0] for row in cursor.fetchall()]

    # Find non-signups
    non_signups = set(calendly_recipients) - set(challenge_recipients)

    print(f"Non-signups: {len(non_signups)}")
    for username in sorted(non_signups):
        print(f"  • @{username}")

    conn.close()


if __name__ == "__main__":
    search_messages_calendly()
