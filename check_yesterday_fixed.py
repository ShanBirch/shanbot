#!/usr/bin/env python3
import sqlite3


def check_yesterday_users():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    # Check users from 2025-01-06 (yesterday)
    print("Users from 2025-01-06 (yesterday):")
    c.execute("""
        SELECT username, followed_at, follow_back_status, dm_status 
        FROM processing_queue 
        WHERE DATE(followed_at) = '2025-01-06'
        LIMIT 10
    """)
    yesterday_users = c.fetchall()
    for user in yesterday_users:
        print(
            f"  {user[0]} | {user[1]} | follow_back: {user[2]} | dm: {user[3]}")

    print(f"\nTotal users from 2025-01-06: {len(yesterday_users)}")

    # Check the actual count
    c.execute(
        "SELECT COUNT(*) FROM processing_queue WHERE DATE(followed_at) = '2025-01-06'")
    total_yesterday = c.fetchone()[0]
    print(f"Total count from yesterday: {total_yesterday}")

    # Check status breakdown for yesterday
    print("\nStatus breakdown for yesterday:")
    c.execute("""
        SELECT follow_back_status, dm_status, COUNT(*) 
        FROM processing_queue 
        WHERE DATE(followed_at) = '2025-01-06'
        GROUP BY follow_back_status, dm_status
    """)
    status_breakdown = c.fetchall()
    for status in status_breakdown:
        print(
            f"  follow_back: {status[0]}, dm: {status[1]} -> {status[2]} users")

    # Check if ANY users meet the script criteria
    print("\nUsers that meet script criteria (from any recent date):")
    c.execute("""
        SELECT username, followed_at, follow_back_status, dm_status 
        FROM processing_queue 
        WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
        AND (dm_status IS NULL OR dm_status != 'sent')
        AND followed_at >= DATE('now', '-7 days')
        AND followed_at < DATE('now', 'start of day')
        LIMIT 5
    """)
    eligible_users = c.fetchall()
    for user in eligible_users:
        print(
            f"  {user[0]} | {user[1]} | follow_back: {user[2]} | dm: {user[3]}")

    if not eligible_users:
        print("  No users meet the criteria!")

        # Let's see what the issue is
        print("\nDebugging the criteria:")

        # Check without dm_status filter
        c.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
            AND followed_at >= DATE('now', '-7 days')
            AND followed_at < DATE('now', 'start of day')
        """)
        without_dm = c.fetchone()[0]
        print(f"  Without dm_status filter: {without_dm}")

        # Check without follow_back_status filter
        c.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE (dm_status IS NULL OR dm_status != 'sent')
            AND followed_at >= DATE('now', '-7 days')
            AND followed_at < DATE('now', 'start of day')
        """)
        without_follow = c.fetchone()[0]
        print(f"  Without follow_back_status filter: {without_follow}")

    conn.close()


if __name__ == "__main__":
    check_yesterday_users()
