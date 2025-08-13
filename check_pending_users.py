#!/usr/bin/env python3
"""
Check pending users for follow-back processing
"""

import sqlite3
import os
from datetime import datetime, timedelta


def check_pending_users():
    """Check how many users need follow-back processing"""
    db_path = r'C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check total users needing follow-back processing
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
            AND (dm_status IS NULL OR dm_status != 'sent')
            AND followed_at >= DATE('now', '-30 days')
            AND followed_at < DATE('now', 'start of day')
        """)
        total_pending = cursor.fetchone()[0]

        print(f"📊 PENDING FOLLOW-BACK CHECKS:")
        print(f"   Total users needing processing: {total_pending}")

        if total_pending > 0:
            # Get date range
            cursor.execute("""
                SELECT MIN(followed_at), MAX(followed_at) FROM processing_queue 
                WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
                AND (dm_status IS NULL OR dm_status != 'sent')
                AND followed_at >= DATE('now', '-30 days')
                AND followed_at < DATE('now', 'start of day')
            """)
            date_range = cursor.fetchone()
            earliest_date, latest_date = date_range

            print(f"   Date range: {earliest_date} to {latest_date}")

            # Get breakdown by date (last 10 days)
            cursor.execute("""
                SELECT DATE(followed_at), COUNT(*) FROM processing_queue 
                WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
                AND (dm_status IS NULL OR dm_status != 'sent')
                AND followed_at >= DATE('now', '-10 days')
                AND followed_at < DATE('now', 'start of day')
                GROUP BY DATE(followed_at)
                ORDER BY DATE(followed_at) DESC
            """)
            daily_breakdown = cursor.fetchall()

            print(f"\n📅 BREAKDOWN BY DATE (Last 10 days):")
            for date, count in daily_breakdown:
                print(f"   {date}: {count} users")

        # Check when script was last run (look for recent follow-back results)
        cursor.execute("""
            SELECT MAX(follow_back_checked_at) FROM processing_queue 
            WHERE follow_back_checked_at IS NOT NULL
        """)
        last_run = cursor.fetchone()[0]

        if last_run:
            print(f"\n⏰ LAST SCRIPT RUN:")
            print(f"   {last_run}")

            # Calculate days since last run
            try:
                last_run_date = datetime.fromisoformat(
                    last_run.replace('Z', '+00:00'))
                days_since = (datetime.now() -
                              last_run_date.replace(tzinfo=None)).days
                print(f"   Days since last run: {days_since}")
            except:
                print(f"   Could not calculate time since last run")
        else:
            print(f"\n⏰ LAST SCRIPT RUN:")
            print(f"   No previous runs found")

        # Check for online mode specifically
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
            AND (dm_status IS NULL OR dm_status != 'sent')
            AND followed_at >= DATE('now', '-30 days')
            AND followed_at < DATE('now', 'start of day')
            AND search_mode = 'online'
        """)
        online_pending = cursor.fetchone()[0]

        print(f"\n🌱 ONLINE MODE (@cocos_connected):")
        print(f"   Pending users: {online_pending}")

        conn.close()

        return total_pending, online_pending

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None, None


if __name__ == "__main__":
    check_pending_users()
