#!/usr/bin/env python3
"""
Check Dual Mode Smart Lead Finder Progress
Monitors both online and local modes simultaneously
"""

import sqlite3
import datetime
import time
import os

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_dual_mode_progress():
    """Get comprehensive progress for both modes."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get today's date
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # Online mode stats
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE DATE(followed_at) = ? AND search_mode = 'online'
        """, (today,))
        online_follows = cursor.fetchone()[0]

        # Local mode stats
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE DATE(followed_at) = ? AND search_mode = 'local'
        """, (today,))
        local_follows = cursor.fetchone()[0]

        # Recent leads (last 10)
        cursor.execute("""
            SELECT username, followed_at, hashtag_found, search_mode
            FROM processing_queue 
            WHERE DATE(followed_at) = ? 
            ORDER BY followed_at DESC 
            LIMIT 10
        """, (today,))
        recent_leads = cursor.fetchall()

        # Active runs (check for running sessions)
        cursor.execute("""
            SELECT run_type, status, leads_found, leads_followed, run_timestamp
            FROM lead_generation_runs 
            WHERE DATE(run_timestamp) = ? AND status IN ('started', 'running')
            ORDER BY run_timestamp DESC
        """, (today,))
        active_runs = cursor.fetchall()

        # Recent completed runs
        cursor.execute("""
            SELECT run_type, status, leads_found, leads_followed, run_timestamp, error_message
            FROM lead_generation_runs 
            WHERE DATE(run_timestamp) = ?
            ORDER BY run_timestamp DESC 
            LIMIT 5
        """, (today,))
        recent_runs = cursor.fetchall()

        conn.close()
        return online_follows, local_follows, recent_leads, active_runs, recent_runs

    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        return 0, 0, [], [], []


def display_progress():
    """Display comprehensive dual mode progress."""
    online_follows, local_follows, recent_leads, active_runs, recent_runs = get_dual_mode_progress()

    # Calculate totals
    total_follows = online_follows + local_follows
    online_remaining = max(0, 75 - online_follows)
    local_remaining = max(0, 75 - local_follows)
    total_remaining = online_remaining + local_remaining

    # Header
    print("🚀 DUAL-MODE SMART LEAD FINDER PROGRESS")
    print("=" * 60)
    print(f"⏰ Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Main stats
    print("📊 TODAY'S PROGRESS:")
    print(
        f"   🌱 Online Mode (cocos_connected):   {online_follows:2d}/75 ({online_remaining:2d} remaining)")
    print(
        f"   🏠 Local Mode (cocos_pt_studio):    {local_follows:2d}/75 ({local_remaining:2d} remaining)")
    print(
        f"   📈 Total Combined:                   {total_follows:2d}/150 ({total_remaining:2d} remaining)")
    print()

    # Progress bars
    online_progress = "█" * (online_follows // 3) + \
        "░" * ((75 - online_follows) // 3)
    local_progress = "█" * (local_follows // 3) + "░" * \
        ((75 - local_follows) // 3)

    print("📊 VISUAL PROGRESS:")
    print(f"   🌱 Online: [{online_progress}] {online_follows}/75")
    print(f"   🏠 Local:  [{local_progress}] {local_follows}/75")
    print()

    # Active status
    print("🚦 CURRENT STATUS:")
    if active_runs:
        for run_type, status, found, followed, timestamp in active_runs:
            mode = "ONLINE" if "online" in run_type else "LOCAL" if "local" in run_type else "DUAL"
            time_str = timestamp.split(
                'T')[1][:8] if 'T' in timestamp else timestamp
            print(
                f"   🟢 {mode} MODE: ACTIVE - Found: {found}, Followed: {followed} - Started: {time_str}")
    else:
        print("   ⚪ Both modes: IDLE (not currently running)")
    print()

    # Recent activity
    if recent_leads:
        print("✅ RECENT LEADS FOUND:")
        for username, followed_at, hashtag, mode in recent_leads:
            time_str = followed_at.split(
                'T')[1][:8] if 'T' in followed_at else followed_at
            mode_emoji = "🌱" if mode == "online" else "🏠"
            print(f"   {mode_emoji} @{username:<20} - {hashtag:<25} - {time_str}")
    else:
        print("⏳ No leads found yet today")
    print()

    # Recent run history
    if recent_runs:
        print("📋 RECENT RUN HISTORY:")
        for run_type, status, found, followed, timestamp, error in recent_runs:
            mode = "ONLINE" if "online" in run_type else "LOCAL" if "local" in run_type else "DUAL"
            time_str = timestamp.split(
                'T')[1][:8] if 'T' in timestamp else timestamp
            status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"
            error_text = f" - ERROR: {error[:30]}..." if error else ""
            print(
                f"   {status_emoji} {mode:<6} {status:<10} Found:{found:2d} Followed:{found:2d} {time_str}{error_text}")
    print()

    # Recommendations
    print("💡 RECOMMENDATIONS:")
    if total_remaining == 0:
        print("   🎉 Daily limit reached for both accounts! Great work!")
    elif online_remaining == 0:
        print("   🌱 Online limit reached - only local mode can continue")
    elif local_remaining == 0:
        print("   🏠 Local limit reached - only online mode can continue")
    else:
        print(
            f"   🚀 {total_remaining} follows remaining - dual mode can continue")
        if total_remaining > 50:
            print("   💪 Consider running dual mode for maximum efficiency")
    print()

    print("💻 TO LAUNCH:")
    print("   🚀 Dual Mode:   python dual_mode_smart_finder.py --mode dual")
    print("   🌱 Online Only: python smart_lead_finder.py --mode online")
    print("   🏠 Local Only:  python smart_lead_finder.py --mode local")
    print("   📊 Dashboard:   python run_dashboard.py")


def monitor_mode():
    """Continuous monitoring mode."""
    print("🔄 CONTINUOUS MONITORING MODE")
    print("Press Ctrl+C to stop")
    print("=" * 40)

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            display_progress()
            print("\n🔄 Refreshing in 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor_mode()
    else:
        display_progress()
