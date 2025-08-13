#!/usr/bin/env python3
"""
Quick search for sign-up links and challenge enquiries.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def quick_search():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 QUICK SEARCH RESULTS")
    print("=" * 50)

    # 1. Count total messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    print(f"Total messages in database: {total_messages}")

    # 2. Count total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    print(f"Total users in database: {total_users}")

    # 3. Search for Calendly links
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%calendly%'")
    calendly_count = cursor.fetchone()[0]
    print(f"Messages with 'calendly': {calendly_count}")

    # 4. Search for challenge mentions
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%challenge%'")
    challenge_count = cursor.fetchone()[0]
    print(f"Messages with 'challenge': {challenge_count}")

    # 5. Search for vegan mentions
    cursor.execute("SELECT COUNT(*) FROM messages WHERE text LIKE '%vegan%'")
    vegan_count = cursor.fetchone()[0]
    print(f"Messages with 'vegan': {vegan_count}")

    # 6. Search for coaching mentions
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%coaching%'")
    coaching_count = cursor.fetchone()[0]
    print(f"Messages with 'coaching': {coaching_count}")

    # 7. Get recent Calendly links (last 10)
    cursor.execute("""
        SELECT ig_username, text, timestamp 
        FROM messages 
        WHERE text LIKE '%calendly%' 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    recent_calendly = cursor.fetchall()

    print(f"\n📅 Recent Calendly links sent ({len(recent_calendly)}):")
    for i, (username, text, timestamp) in enumerate(recent_calendly, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   Message: {text[:80]}...")
        print()

    # 8. Get recent challenge conversations
    cursor.execute("""
        SELECT DISTINCT ig_username, COUNT(*) as msg_count
        FROM messages 
        WHERE text LIKE '%challenge%' 
        GROUP BY ig_username 
        ORDER BY msg_count DESC 
        LIMIT 10
    """)
    challenge_users = cursor.fetchall()

    print(f"🎯 Users discussing challenge ({len(challenge_users)}):")
    for i, (username, count) in enumerate(challenge_users, 1):
        print(f"{i}. @{username} - {count} messages")

    conn.close()


if __name__ == "__main__":
    quick_search()
