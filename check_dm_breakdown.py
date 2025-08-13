#!/usr/bin/env python3
import sqlite3


def detailed_dm_breakdown():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    print("=== DETAILED DM STATUS BREAKDOWN ===")

    # All users who followed back since July 1st
    c.execute("""
        SELECT COUNT(*) 
        FROM processing_queue 
        WHERE follow_back_status = 'yes' 
        AND follow_back_checked_at >= '2025-07-01'
    """)
    total_yes = c.fetchone()[0]
    print(
        f"Total users marked as 'yes' (followed back) since July 1: {total_yes}")

    # Break down by DM status
    statuses = [
        ("= 'sent'", "sent"),
        ("IS NULL", "NULL"),
        ("= ''", "empty string"),
        ("= 'pending'", "pending"),
        ("LIKE '%failed%'", "failed"),
        ("= 'skipped'", "skipped"),
        ("LIKE '%error%'", "error")
    ]

    total_accounted = 0

    for condition, label in statuses:
        c.execute(f"""
            SELECT COUNT(*) 
            FROM processing_queue 
            WHERE follow_back_status = 'yes' 
            AND dm_status {condition}
            AND follow_back_checked_at >= '2025-07-01'
        """)
        count = c.fetchone()[0]
        if count > 0:
            print(f"  • dm_status {label}: {count}")
            total_accounted += count

    print(f"\nAccounted for: {total_accounted} / {total_yes}")

    if total_accounted != total_yes:
        print(f"Missing: {total_yes - total_accounted} users")

        # Find the missing ones
        print("\nFinding users with unexpected dm_status values...")
        c.execute("""
            SELECT DISTINCT dm_status, COUNT(*) 
            FROM processing_queue 
            WHERE follow_back_status = 'yes' 
            AND follow_back_checked_at >= '2025-07-01'
            AND dm_status NOT IN ('sent', '', 'pending')
            AND dm_status IS NOT NULL
            AND dm_status NOT LIKE '%failed%'
            AND dm_status != 'skipped'
            AND dm_status NOT LIKE '%error%'
            GROUP BY dm_status
        """)

        unexpected = c.fetchall()
        for status, count in unexpected:
            print(f"  • Unexpected dm_status '{status}': {count}")

    # Also check the original 52 vs 2 numbers from last 7 days
    print(f"\n=== ORIGINAL NUMBERS CHECK (Last 7 days) ===")

    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    c.execute("""
        SELECT COUNT(*) 
        FROM processing_queue 
        WHERE follow_back_status = 'yes' 
        AND follow_back_checked_at >= ?
    """, (seven_days_ago,))
    recent_yes = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) 
        FROM processing_queue 
        WHERE follow_back_status = 'yes' 
        AND dm_status = 'sent'
        AND follow_back_checked_at >= ?
    """, (seven_days_ago,))
    recent_sent = c.fetchone()[0]

    print(
        f"Last 7 days - Followed back: {recent_yes}, DMs sent: {recent_sent}")
    print(f"Missing DMs: {recent_yes - recent_sent}")

    conn.close()


if __name__ == "__main__":
    detailed_dm_breakdown()
