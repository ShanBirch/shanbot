#!/usr/bin/env python3
"""
Comprehensive report of ad responses, sign-up links, and challenge enquiries.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_comprehensive_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📊 SHANBOT COMPREHENSIVE ANALYTICS REPORT")
    print("=" * 60)

    # 1. Database Overview
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    print(f"📈 DATABASE OVERVIEW:")
    print(f"   Total Messages: {total_messages}")
    print(f"   Total Users: {total_users}")
    print()

    # 2. Ad Responses (tagged users)
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE lead_source IS NOT NULL 
        AND lead_source != '' 
        AND is_in_ad_flow = 1
    """)
    ad_responses = cursor.fetchone()[0]
    print(f"🎯 AD RESPONSES (Tagged): {ad_responses}")
    print()

    # 3. Sign-up Links Sent
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%calendly%'")
    calendly_links = cursor.fetchone()[0]
    print(f"📅 CALENDLY LINKS SENT: {calendly_links}")
    print()

    # 4. Challenge Conversations
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%challenge%'")
    challenge_mentions = cursor.fetchone()[0]
    print(f"🏆 CHALLENGE MENTIONS: {challenge_mentions}")
    print()

    # 5. Vegan Conversations
    cursor.execute("SELECT COUNT(*) FROM messages WHERE text LIKE '%vegan%'")
    vegan_mentions = cursor.fetchone()[0]
    print(f"🌱 VEGAN MENTIONS: {vegan_mentions}")
    print()

    # 6. Coaching Conversations
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text LIKE '%coaching%'")
    coaching_mentions = cursor.fetchone()[0]
    print(f"💪 COACHING MENTIONS: {coaching_mentions}")
    print()

    # 7. Recent Calendly Links (Last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    cursor.execute("""
        SELECT ig_username, text, timestamp 
        FROM messages 
        WHERE text LIKE '%calendly%' 
        AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (start_date.isoformat(),))

    recent_calendly = cursor.fetchall()

    print(
        f"📅 RECENT CALENDLY LINKS SENT (Last 30 days): {len(recent_calendly)}")
    print("-" * 50)
    for i, (username, text, timestamp) in enumerate(recent_calendly, 1):
        print(f"{i}. @{username} - {timestamp}")
        print(f"   Message: {text[:100]}...")
        print()

    # 8. All Challenge Enquiries (Last 30 days)
    cursor.execute("""
        SELECT DISTINCT m.ig_username, COUNT(m2.id) as msg_count, MAX(m.timestamp) as last_msg
        FROM messages m
        LEFT JOIN messages m2 ON m.ig_username = m2.ig_username
        WHERE (m.text LIKE '%challenge%' 
               OR m.text LIKE '%vegan%'
               OR m.text LIKE '%plant%based%'
               OR m.text LIKE '%coaching%'
               OR m.text LIKE '%program%'
               OR m.text LIKE '%interested%'
               OR m.text LIKE '%tell me more%'
               OR m.text LIKE '%how much%'
               OR m.text LIKE '%price%'
               OR m.text LIKE '%cost%')
        AND m.sender = 'user'
        AND m.timestamp >= ?
        GROUP BY m.ig_username
        ORDER BY last_msg DESC
    """, (start_date.isoformat(),))

    challenge_enquiries = cursor.fetchall()

    print(
        f"🎯 ALL CHALLENGE ENQUIRIES (Last 30 days): {len(challenge_enquiries)}")
    print("-" * 50)
    for i, (username, count, last_msg) in enumerate(challenge_enquiries, 1):
        print(f"{i}. @{username} - {count} messages - Last: {last_msg}")

    # 9. High Engagement Users (10+ messages)
    cursor.execute("""
        SELECT ig_username, COUNT(*) as msg_count
        FROM messages 
        WHERE timestamp >= ?
        GROUP BY ig_username 
        HAVING COUNT(*) >= 10
        ORDER BY msg_count DESC
        LIMIT 20
    """, (start_date.isoformat(),))

    high_engagement = cursor.fetchall()

    print(
        f"\n🔥 HIGH ENGAGEMENT USERS (10+ messages, Last 30 days): {len(high_engagement)}")
    print("-" * 50)
    for i, (username, count) in enumerate(high_engagement, 1):
        print(f"{i}. @{username} - {count} messages")

    conn.close()

    return {
        'total_messages': total_messages,
        'total_users': total_users,
        'ad_responses': ad_responses,
        'calendly_links': calendly_links,
        'challenge_mentions': challenge_mentions,
        'vegan_mentions': vegan_mentions,
        'coaching_mentions': coaching_mentions,
        'recent_calendly': len(recent_calendly),
        'challenge_enquiries': len(challenge_enquiries),
        'high_engagement': len(high_engagement)
    }


if __name__ == "__main__":
    get_comprehensive_report()
