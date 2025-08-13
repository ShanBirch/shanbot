#!/usr/bin/env python3
"""
Script to search for sign-up links and challenge conversations in the database.
"""

import sqlite3
from datetime import datetime, timedelta

# Database path
DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def search_for_signup_links():
    """Search for any messages containing sign-up links."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Search for various sign-up link patterns
        cursor.execute("""
            SELECT 
                m.ig_username,
                m.text,
                m.timestamp,
                m.sender
            FROM messages m
            WHERE (m.text LIKE '%calendly%'
                   OR m.text LIKE '%cocospersonaltraining.com%'
                   OR m.text LIKE '%book%call%'
                   OR m.text LIKE '%schedule%call%'
                   OR m.text LIKE '%calendar%link%'
                   OR m.text LIKE '%booking%link%'
                   OR m.text LIKE '%sign%up%'
                   OR m.text LIKE '%join%')
            ORDER BY m.timestamp DESC
            LIMIT 50
        """)

        results = cursor.fetchall()

        print(f"Found {len(results)} messages with potential sign-up links:")
        print("=" * 60)

        for i, row in enumerate(results, 1):
            print(f"{i}. @{row[0]} ({row[3]}) - {row[2]}")
            print(f"   Message: {row[1][:100]}...")
            print()

        conn.close()

    except Exception as e:
        print(f"Error searching for sign-up links: {e}")


def search_for_challenge_conversations():
    """Search for conversations about the challenge."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Search for challenge-related keywords
        cursor.execute("""
            SELECT DISTINCT
                m.ig_username,
                COUNT(m2.id) as message_count,
                MAX(m.timestamp) as last_message
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
            GROUP BY m.ig_username
            ORDER BY last_message DESC
            LIMIT 50
        """)

        results = cursor.fetchall()

        print(
            f"Found {len(results)} users with challenge-related conversations:")
        print("=" * 60)

        for i, row in enumerate(results, 1):
            print(f"{i}. @{row[0]} - {row[1]} messages - Last: {row[2]}")

        conn.close()

    except Exception as e:
        print(f"Error searching for challenge conversations: {e}")


def search_recent_messages():
    """Search for recent messages to see what's happening."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get recent messages
        cursor.execute("""
            SELECT 
                m.ig_username,
                m.text,
                m.timestamp,
                m.sender
            FROM messages m
            WHERE m.timestamp >= datetime('now', '-7 days')
            ORDER BY m.timestamp DESC
            LIMIT 20
        """)

        results = cursor.fetchall()

        print(f"Recent messages (last 7 days):")
        print("=" * 60)

        for i, row in enumerate(results, 1):
            print(f"{i}. @{row[0]} ({row[3]}) - {row[2]}")
            print(f"   Message: {row[1][:100]}...")
            print()

        conn.close()

    except Exception as e:
        print(f"Error searching recent messages: {e}")


def main():
    print("Searching for sign-up links and challenge conversations...")
    print()

    search_for_signup_links()
    print()
    search_for_challenge_conversations()
    print()
    search_recent_messages()


if __name__ == "__main__":
    main()
