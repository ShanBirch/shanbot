#!/usr/bin/env python3
"""
Simple list of everyone who received Calendly links.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_simple_calendly_list():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📅 EVERYONE WHO RECEIVED CALENDLY LINKS")
    print("=" * 70)

    # Get from unified messages table (checking both new and old columns)
    cursor.execute("""
        SELECT DISTINCT ig_username, timestamp
        FROM messages 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
           OR text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    all_recipients = cursor.fetchall()

    print(f"From unified messages table: {len(all_recipients)}")
    for username, timestamp in all_recipients:
        print(f"  • @{username} - {timestamp}")

    print()

    # Create unique users set
    all_users = set()
    for username, _ in all_recipients:
        all_users.add(username)

    print(f"📅 TOTAL UNIQUE RECIPIENTS: {len(all_users)}")
    print("-" * 50)
    for username in sorted(all_users):
        print(f"  • @{username}")

    conn.close()


if __name__ == "__main__":
    get_simple_calendly_list()
