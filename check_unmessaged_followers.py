#!/usr/bin/env python3
"""
Check Unmessaged Followers - Preview who needs to be messaged
"""

import os
import sqlite3
from datetime import datetime, timedelta


def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__),
                           'app', 'analytics_data_good.sqlite')
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def check_unmessaged_followers():
    """Check who needs to be messaged"""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    print("🔍 Checking for users who followed back but haven't been messaged...")
    print("="*70)

    # Get users who followed back but haven't been messaged
    query = """
    SELECT DISTINCT username, followed_at, follow_back_checked_at, dm_status
    FROM processing_queue 
    WHERE follow_back_status = 'yes'
    AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
    AND DATE(followed_at) >= DATE('now', '-14 days')
    ORDER BY follow_back_checked_at DESC
    """

    cursor.execute(query)
    users = cursor.fetchall()

    print(
        f"📊 Found {len(users)} users from processing_queue who followed back but haven't been messaged")
    print()

    # Filter by conversation history to double-check
    unmessaged_users = []
    already_messaged = []

    for username, followed_at, checked_at, dm_status in users:
        # Check conversation history
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp) as last_message
            FROM conversation_history 
            WHERE ig_username = ? AND message_type = 'ai'
        """, (username,))

        result = cursor.fetchone()
        ai_message_count = result[0]
        last_message = result[1]

        if ai_message_count == 0:
            unmessaged_users.append({
                'username': username,
                'followed_at': followed_at,
                'checked_at': checked_at,
                'dm_status': dm_status or 'NULL'
            })
        else:
            already_messaged.append({
                'username': username,
                'ai_messages': ai_message_count,
                'last_message': last_message
            })

    print("✅ USERS WHO NEED MESSAGING:")
    print("=" * 50)

    if unmessaged_users:
        for i, user in enumerate(unmessaged_users, 1):
            followed_date = datetime.fromisoformat(
                user['followed_at'].split('.')[0]).strftime('%Y-%m-%d')
            checked_date = datetime.fromisoformat(user['checked_at'].split(
                '.')[0]).strftime('%Y-%m-%d') if user['checked_at'] else 'Unknown'

            print(f"{i:2d}. @{user['username']}")
            print(f"    📅 Followed: {followed_date}")
            print(f"    ✅ Followed back: {checked_date}")
            print(f"    📨 DM Status: {user['dm_status']}")
            print()
    else:
        print("🎉 No users need messaging!")

    print("🔄 USERS ALREADY MESSAGED:")
    print("=" * 50)

    if already_messaged:
        for i, user in enumerate(already_messaged[:10], 1):  # Show first 10
            last_msg_date = datetime.fromisoformat(user['last_message'].split(
                '.')[0]).strftime('%Y-%m-%d %H:%M') if user['last_message'] else 'Unknown'
            print(
                f"{i:2d}. @{user['username']} - {user['ai_messages']} messages (last: {last_msg_date})")

        if len(already_messaged) > 10:
            print(f"    ... and {len(already_messaged) - 10} more")
    else:
        print("None found.")

    print()
    print("📋 SUMMARY:")
    print("=" * 30)
    print(f"👥 Total followed back: {len(users)}")
    print(f"📤 Need messaging: {len(unmessaged_users)}")
    print(f"✅ Already messaged: {len(already_messaged)}")

    # Show the message that would be sent
    message = "Heya :) Love your content! How long have you been vegan for?"
    print(f"\n💬 Message to send: '{message}'")

    print("\n🚀 To send messages, run:")
    print("   python message_new_followers.py --dry-run    (to preview)")
    print("   python message_new_followers.py             (to actually send)")

    conn.close()


if __name__ == "__main__":
    check_unmessaged_followers()
