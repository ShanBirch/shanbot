#!/usr/bin/env python3
"""
Find people who received Calendly links but didn't sign up for the challenge.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def find_non_signups():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 FINDING PEOPLE WHO RECEIVED CALENDLY LINKS BUT DIDN'T SIGN UP")
    print("=" * 70)

    # Get all people who received Calendly links
    cursor.execute("""
        SELECT DISTINCT ig_username 
        FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND message_type = 'shannon'
    """)
    calendly_recipients = [row[0] for row in cursor.fetchall()]

    # Also check scheduled_responses table
    cursor.execute("""
        SELECT DISTINCT user_ig_username 
        FROM scheduled_responses 
        WHERE response_text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND status = 'sent'
    """)
    scheduled_recipients = [row[0] for row in cursor.fetchall()]

    # Also check messages table
    cursor.execute("""
        SELECT DISTINCT ig_username 
        FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
        AND sender = 'shannon'
    """)
    messages_recipients = [row[0] for row in cursor.fetchall()]

    # Combine all recipients
    all_recipients = set(calendly_recipients +
                         scheduled_recipients + messages_recipients)

    print(f"📅 TOTAL PEOPLE WHO RECEIVED CALENDLY LINKS: {len(all_recipients)}")
    print("-" * 50)
    for username in sorted(all_recipients):
        print(f"  • @{username}")

    # Get all people who signed up for challenges
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
    challenge_signups = [row[0] for row in cursor.fetchall()]

    # Also check for people who completed the onboarding form (using correct column names)
    cursor.execute("""
        SELECT DISTINCT ig_username 
        FROM users 
        WHERE client_status = 'paying_member' OR client_status = 'completed' OR client_status = 'active'
    """)
    active_clients = [row[0] for row in cursor.fetchall()]

    # Combine all signups
    all_signups = set(challenge_signups + active_clients)

    print(f"\n🏆 PEOPLE WHO SIGNED UP: {len(all_signups)}")
    print("-" * 50)
    for username in sorted(all_signups):
        print(f"  • @{username}")

    # Find people who received Calendly but didn't sign up
    non_signups = all_recipients - all_signups

    print(
        f"\n❌ PEOPLE WHO RECEIVED CALENDLY BUT DIDN'T SIGN UP: {len(non_signups)}")
    print("=" * 70)
    print("These are the people you should follow up with:")
    print()

    for i, username in enumerate(sorted(non_signups), 1):
        print(f"{i}. @{username}")

    # Get more details about these people
    print(f"\n📋 DETAILED ANALYSIS OF NON-SIGNUPS")
    print("=" * 70)

    for username in sorted(non_signups):
        print(f"\n👤 @{username}")

        # Get their conversation history
        cursor.execute("""
            SELECT message_text, timestamp, message_type
            FROM conversation_history 
            WHERE ig_username = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (username,))
        recent_messages = cursor.fetchall()

        if recent_messages:
            print(f"   Recent conversation:")
            for text, timestamp, msg_type in recent_messages:
                print(f"   {msg_type}: {text[:80]}...")
        else:
            print(f"   No recent conversation found")

        # Check if they're in the users table
        cursor.execute("""
            SELECT first_name, last_name, lead_source, client_status
            FROM users 
            WHERE ig_username = ?
        """, (username,))
        user_info = cursor.fetchone()

        if user_info:
            first_name, last_name, lead_source, client_status = user_info
            print(f"   Name: {first_name} {last_name}")
            print(f"   Lead Source: {lead_source}")
            print(f"   Client Status: {client_status}")
        else:
            print(f"   Not in users table")

    # Summary for follow-up
    print(f"\n📊 FOLLOW-UP SUMMARY")
    print("=" * 70)
    print(f"Total Calendly recipients: {len(all_recipients)}")
    print(f"Total signups: {len(all_signups)}")
    print(f"Non-signups to follow up: {len(non_signups)}")
    print(
        f"Conversion rate: {len(all_signups)/len(all_recipients)*100:.1f}%" if all_recipients else "N/A")

    # Recent activity (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"\n📅 RECENT ACTIVITY (Last 30 days)")
    print("=" * 70)

    recent_recipients = []
    for username in all_recipients:
        cursor.execute("""
            SELECT timestamp FROM conversation_history 
            WHERE ig_username = ? 
            AND message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
            ORDER BY timestamp DESC LIMIT 1
        """, (username,))
        result = cursor.fetchone()
        if result:
            try:
                timestamp = result[0]
                if isinstance(timestamp, str):
                    if '+10:00' in timestamp:
                        clean_timestamp = timestamp.replace('+10:00', '')
                    else:
                        clean_timestamp = timestamp
                    dt = datetime.fromisoformat(clean_timestamp)
                    if dt >= start_date:
                        recent_recipients.append((username, timestamp))
            except:
                # If we can't parse the date, include it
                recent_recipients.append((username, timestamp))

    recent_non_signups = [username for username,
                          _ in recent_recipients if username in non_signups]

    print(
        f"Recent Calendly recipients (last 30 days): {len(recent_recipients)}")
    print(f"Recent non-signups to follow up: {len(recent_non_signups)}")

    if recent_non_signups:
        print(f"\n🎯 PRIORITY FOLLOW-UPS (Recent):")
        for username in recent_non_signups:
            print(f"  • @{username}")

    conn.close()


if __name__ == "__main__":
    find_non_signups()
