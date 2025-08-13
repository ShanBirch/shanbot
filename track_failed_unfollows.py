#!/usr/bin/env python3
"""
Track and retry failed unfollows from the follow-back checker
"""

import sqlite3
import os
from datetime import datetime


def track_failed_unfollows():
    """Check for users who failed to unfollow and need retry"""
    db_path = r'C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check for users who failed to unfollow
        cursor.execute("""
            SELECT username, follow_back_status, follow_back_checked_at, followed_at
            FROM processing_queue 
            WHERE follow_back_status LIKE '%unfollow_failed%'
            ORDER BY follow_back_checked_at DESC
        """)

        failed_unfollows = cursor.fetchall()

        print(f"📊 FAILED UNFOLLOWS TRACKING:")
        print(f"   Total failed unfollows: {len(failed_unfollows)}")

        if failed_unfollows:
            print(f"\n📋 FAILED UNFOLLOWS LIST:")
            for i, (username, status, checked_at, followed_at) in enumerate(failed_unfollows, 1):
                print(f"   {i}. @{username}")
                print(f"      Status: {status}")
                print(f"      Checked: {checked_at}")
                print(f"      Originally followed: {followed_at}")
                print()

            # Count by status type
            cursor.execute("""
                SELECT follow_back_status, COUNT(*) 
                FROM processing_queue 
                WHERE follow_back_status LIKE '%unfollow_failed%'
                GROUP BY follow_back_status
            """)

            status_counts = cursor.fetchall()
            print(f"📈 FAILURE BREAKDOWN:")
            for status, count in status_counts:
                print(f"   {status}: {count} users")
        else:
            print(f"   ✅ No failed unfollows found!")

        # Check for users who need retry (failed more than 1 day ago)
        cursor.execute("""
            SELECT username, follow_back_status, follow_back_checked_at
            FROM processing_queue 
            WHERE follow_back_status LIKE '%unfollow_failed%'
            AND follow_back_checked_at < datetime('now', '-1 day')
            ORDER BY follow_back_checked_at ASC
        """)

        retry_candidates = cursor.fetchall()

        print(f"\n🔄 RETRY CANDIDATES (failed >1 day ago):")
        print(f"   Users ready for retry: {len(retry_candidates)}")

        if retry_candidates:
            print(f"\n📋 READY FOR RETRY:")
            for i, (username, status, checked_at) in enumerate(retry_candidates, 1):
                print(f"   {i}. @{username} (failed: {checked_at})")

        conn.close()

        return failed_unfollows, retry_candidates

    except Exception as e:
        print(f"❌ Error checking failed unfollows: {e}")
        return None, None


def retry_failed_unfollows():
    """Retry unfollowing users who previously failed"""
    failed_unfollows, retry_candidates = track_failed_unfollows()

    if not retry_candidates:
        print("✅ No users ready for retry!")
        return

    print(f"\n🚀 Ready to retry {len(retry_candidates)} failed unfollows")
    response = input("Proceed with retry? (y/n): ")

    if response.lower() != 'y':
        print("❌ Retry cancelled")
        return

    # Import and run the follow-back checker for retry
    try:
        from check_daily_follow_backs import DailyFollowBackChecker

        print("🔄 Starting retry process...")
        checker = DailyFollowBackChecker(username="cocos_connected")

        # Reset failed statuses to allow retry
        db_path = r'C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for username, status, checked_at in retry_candidates:
            cursor.execute("""
                UPDATE processing_queue 
                SET follow_back_status = 'pending'
                WHERE username = ?
            """, (username,))
            print(f"🔄 Reset @{username} status for retry")

        conn.commit()
        conn.close()

        print("✅ Statuses reset. Run the follow-back checker again to retry unfollows.")

    except Exception as e:
        print(f"❌ Error during retry setup: {e}")


if __name__ == "__main__":
    print("🔍 FAILED UNFOLLOWS TRACKER")
    print("=" * 50)

    track_failed_unfollows()

    print("\n" + "=" * 50)
    print("🔄 RETRY OPTIONS:")
    print("1. View failed unfollows (current)")
    print("2. Retry failed unfollows")

    choice = input("\nEnter choice (1 or 2): ")

    if choice == "2":
        retry_failed_unfollows()
    else:
        print("✅ Done!")
