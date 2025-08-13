#!/usr/bin/env python3
"""
Investigate conversation storage duplication between conversation_history and messages tables.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def investigate_conversation_storage():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 INVESTIGATING CONVERSATION STORAGE DUPLICATION")
    print("=" * 70)

    # Check table structures
    print("📊 TABLE STRUCTURES")
    print("-" * 50)

    # conversation_history structure
    cursor.execute("PRAGMA table_info(conversation_history)")
    conv_columns = cursor.fetchall()
    print("conversation_history columns:")
    for col in conv_columns:
        print(f"  • {col[1]} ({col[2]})")

    print()

    # messages structure
    cursor.execute("PRAGMA table_info(messages)")
    msg_columns = cursor.fetchall()
    print("messages columns:")
    for col in msg_columns:
        print(f"  • {col[1]} ({col[2]})")

    # Count records in each table
    print(f"\n📈 RECORD COUNTS")
    print("-" * 50)

    cursor.execute("SELECT COUNT(*) FROM conversation_history")
    conv_count = cursor.fetchone()[0]
    print(f"conversation_history: {conv_count} records")

    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]
    print(f"messages: {msg_count} records")

    # Check for overlapping data
    print(f"\n🔄 DATA OVERLAP ANALYSIS")
    print("-" * 50)

    # Get sample data from both tables for the same user
    cursor.execute("""
        SELECT ig_username, COUNT(*) as count
        FROM conversation_history 
        GROUP BY ig_username 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_conv_users = cursor.fetchall()

    print("Top users in conversation_history:")
    for username, count in top_conv_users:
        print(f"  • @{username}: {count} messages")

    print()

    cursor.execute("""
        SELECT ig_username, COUNT(*) as count
        FROM messages 
        GROUP BY ig_username 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_msg_users = cursor.fetchall()

    print("Top users in messages:")
    for username, count in top_msg_users:
        print(f"  • @{username}: {count} messages")

    # Check for specific user data in both tables
    print(f"\n🔍 SAMPLE DATA COMPARISON")
    print("-" * 50)

    # Get a user that appears in both tables
    cursor.execute("""
        SELECT DISTINCT ch.ig_username
        FROM conversation_history ch
        INNER JOIN messages m ON ch.ig_username = m.ig_username
        LIMIT 3
    """)
    common_users = cursor.fetchall()

    if common_users:
        test_user = common_users[0][0]
        print(f"Comparing data for @{test_user}:")

        # Get conversation_history data
        cursor.execute("""
            SELECT message_text, timestamp, message_type
            FROM conversation_history 
            WHERE ig_username = ?
            ORDER BY timestamp DESC
            LIMIT 3
        """, (test_user,))
        conv_data = cursor.fetchall()

        print(f"\nconversation_history data:")
        for text, timestamp, msg_type in conv_data:
            safe_text = text[:60] + "..." if text else "None"
            print(f"  {msg_type}: {safe_text}")

        # Get messages data
        cursor.execute("""
            SELECT text, timestamp, sender
            FROM messages 
            WHERE ig_username = ?
            ORDER BY timestamp DESC
            LIMIT 3
        """, (test_user,))
        msg_data = cursor.fetchall()

        print(f"\nmessages data:")
        for text, timestamp, sender in msg_data:
            safe_text = text[:60] + "..." if text else "None"
            safe_sender = sender if sender else "None"
            print(f"  {safe_sender}: {safe_text}")

    # Check for Calendly links in both tables
    print(f"\n📅 CALENDLY LINK COMPARISON")
    print("-" * 50)

    cursor.execute("""
        SELECT COUNT(*) FROM conversation_history 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
    """)
    conv_calendly = cursor.fetchone()[0]
    print(f"Calendly links in conversation_history: {conv_calendly}")

    cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE text LIKE '%calendly.com/shannonrhysbirch/15min%'
    """)
    msg_calendly = cursor.fetchone()[0]
    print(f"Calendly links in messages: {msg_calendly}")

    # Check for challenge sign-ups in both tables
    print(f"\n🏆 CHALLENGE SIGN-UP COMPARISON")
    print("-" * 50)

    cursor.execute("""
        SELECT COUNT(*) FROM conversation_history 
        WHERE message_text LIKE '%ready to join%' OR message_text LIKE '%want to join%'
    """)
    conv_signups = cursor.fetchone()[0]
    print(f"Challenge sign-ups in conversation_history: {conv_signups}")

    cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE text LIKE '%ready to join%' OR text LIKE '%want to join%'
    """)
    msg_signups = cursor.fetchone()[0]
    print(f"Challenge sign-ups in messages: {msg_signups}")

    # Check timestamp patterns
    print(f"\n⏰ TIMESTAMP ANALYSIS")
    print("-" * 50)

    cursor.execute("""
        SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
        FROM conversation_history
    """)
    conv_time_range = cursor.fetchone()
    print(
        f"conversation_history: {conv_time_range[0]} to {conv_time_range[1]} ({conv_time_range[2]} records)")

    cursor.execute("""
        SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
        FROM messages
    """)
    msg_time_range = cursor.fetchone()
    print(
        f"messages: {msg_time_range[0]} to {msg_time_range[1]} ({msg_time_range[2]} records)")

    # Check for duplicate data
    print(f"\n🔄 DUPLICATE DATA ANALYSIS")
    print("-" * 50)

    # Check if the same messages exist in both tables
    cursor.execute("""
        SELECT COUNT(*) FROM conversation_history ch
        INNER JOIN messages m ON ch.ig_username = m.ig_username 
        AND ch.message_text = m.text
        AND ch.timestamp = m.timestamp
    """)
    exact_duplicates = cursor.fetchone()[0]
    print(f"Exact duplicates between tables: {exact_duplicates}")

    # Check for users in both tables
    cursor.execute("""
        SELECT COUNT(DISTINCT ch.ig_username) 
        FROM conversation_history ch
        INNER JOIN messages m ON ch.ig_username = m.ig_username
    """)
    common_users_count = cursor.fetchone()[0]
    print(f"Users appearing in both tables: {common_users_count}")

    conn.close()


if __name__ == "__main__":
    investigate_conversation_storage()
