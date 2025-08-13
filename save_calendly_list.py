#!/usr/bin/env python3
"""
Save the list of Calendly recipients to a text file.
"""

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def save_calendly_list():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get from unified messages table (checking both new and old columns)
    cursor.execute("""
        SELECT DISTINCT ig_username, timestamp
        FROM messages 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
           OR text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    all_recipients = cursor.fetchall()

    # Create unique users set
    all_users = set()
    for username, _ in all_recipients:
        all_users.add(username)

    # Create filename with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"CALENDLY_RECIPIENTS_LIST_{current_date}.txt"

    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("📅 CALENDLY RECIPIENTS LIST\n")
        f.write("=" * 80 + "\n")
        f.write(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total unique recipients: {len(all_users)}\n")
        f.write("=" * 80 + "\n\n")

        f.write("📊 BREAKDOWN:\n")
        f.write("-" * 40 + "\n")
        f.write(f"From unified messages table: {len(all_recipients)}\n")
        f.write(f"Total unique users: {len(all_users)}\n\n")

        f.write("📅 ALL CALENDLY RECIPIENTS:\n")
        f.write("-" * 40 + "\n")
        for username, timestamp in all_recipients:
            f.write(f"• @{username} - {timestamp}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("📋 COMPLETE UNIQUE LIST:\n")
        f.write("=" * 80 + "\n")
        for i, username in enumerate(sorted(all_users), 1):
            f.write(f"{i:2d}. @{username}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF LIST\n")
        f.write("=" * 80 + "\n")

    print(f"✅ List saved to: {filename}")
    print(f"📅 Total recipients: {len(all_users)}")
    print(f"📁 File location: {filename}")

    conn.close()


if __name__ == "__main__":
    save_calendly_list()
