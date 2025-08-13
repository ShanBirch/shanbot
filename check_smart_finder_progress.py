#!/usr/bin/env python3
"""
Check Smart Lead Finder Progress
Monitors the database to see how many leads have been found
"""

import sqlite3
import datetime

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def check_progress():
    """Check current progress of Smart Lead Finder."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check today's follows by mode
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # Online mode follows (cocos_connected)
        cursor.execute(
            "SELECT COUNT(*) FROM processing_queue WHERE DATE(followed_at) = ? AND search_mode = 'online'",
            (today,)
        )
        online_follows = cursor.fetchone()[0]

        # Local mode follows (cocos_pt_studio)
        cursor.execute(
            "SELECT COUNT(*) FROM processing_queue WHERE DATE(followed_at) = ? AND search_mode = 'local'",
            (today,)
        )
        local_follows = cursor.fetchone()[0]

        # Total follows
        total_follows = online_follows + local_follows

        # Check recent runs
        cursor.execute("""
            SELECT id, run_timestamp, status, leads_found, leads_followed, error_message 
            FROM lead_generation_runs 
            ORDER BY id DESC 
            LIMIT 5
        """)
        recent_runs = cursor.fetchall()

        # Check recent leads added today
        cursor.execute("""
            SELECT username, followed_at, hashtag_found 
            FROM processing_queue 
            WHERE DATE(followed_at) = ? 
            ORDER BY followed_at DESC 
            LIMIT 10
        """, (today,))
        recent_leads = cursor.fetchall()

        print(f"🚀 SMART LEAD FINDER PROGRESS REPORT")
        print(
            f"⏰ Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 DUAL-MODE FOLLOWS TODAY:")
        print(f"   🌱 Online Mode (cocos_connected): {online_follows}/75")
        print(f"   🏠 Local Mode (cocos_pt_studio): {local_follows}/75")
        print(f"   📊 Total Combined: {total_follows}/150")
        print(f"📈 Recent leads found today: {len(recent_leads)}")

        if recent_leads:
            print(f"\n✅ RECENT LEADS:")
            for username, followed_at, hashtag in recent_leads:
                time_str = followed_at.split(
                    'T')[1][:8] if 'T' in followed_at else followed_at
                print(f"   👤 @{username} - {hashtag} - {time_str}")

        print(f"\n📋 RECENT RUNS:")
        for run_id, timestamp, status, found, followed, error in recent_runs:
            time_str = timestamp.split(
                'T')[1][:8] if 'T' in timestamp else timestamp
            error_part = f" - ERROR: {error}" if error else ""
            print(
                f"   🏃 Run #{run_id}: {status} - Found: {found}, Followed: {followed} - {time_str}{error_part}")

        conn.close()

    except Exception as e:
        print(f"❌ Error checking progress: {e}")


if __name__ == "__main__":
    check_progress()
