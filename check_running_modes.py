#!/usr/bin/env python3
"""
Check Running Smart Lead Finder Modes
Shows which modes (local/online) are currently running
"""

import subprocess
import sqlite3
import datetime
import os


def check_running_processes():
    """Check for running Smart Lead Finder processes"""
    try:
        # Use tasklist to find python processes
        result = subprocess.run(['tasklist', '/fi', 'imagename eq python.exe', '/fo', 'csv'],
                                capture_output=True, text=True)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            python_processes = len(lines) - 1  # Subtract header
            return max(0, python_processes)
        return 0
    except:
        return 0


def check_database_activity():
    """Check recent database activity to see which modes are active"""
    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    if not os.path.exists(db_path):
        return None, None, None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check recent activity in the last 10 minutes
        ten_minutes_ago = (datetime.datetime.now() -
                           datetime.timedelta(minutes=10)).isoformat()

        # Check for recent online leads
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE search_mode = 'online' AND followed_at > ?
        """, (ten_minutes_ago,))
        recent_online = cursor.fetchone()[0]

        # Check for recent local leads
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE search_mode = 'local' AND followed_at > ?
        """, (ten_minutes_ago,))
        recent_local = cursor.fetchone()[0]

        # Check latest activity
        cursor.execute("""
            SELECT search_mode, followed_at FROM processing_queue 
            ORDER BY followed_at DESC LIMIT 1
        """)
        latest = cursor.fetchone()

        conn.close()
        return recent_online, recent_local, latest
    except Exception as e:
        print(f"Database error: {e}")
        return None, None, None


def get_daily_stats():
    """Get today's stats for both modes"""
    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    if not os.path.exists(db_path):
        return 0, 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # Today's online follows
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE search_mode = 'online' AND DATE(followed_at) = ?
        """, (today,))
        online_today = cursor.fetchone()[0]

        # Today's local follows
        cursor.execute("""
            SELECT COUNT(*) FROM processing_queue 
            WHERE search_mode = 'local' AND DATE(followed_at) = ?
        """, (today,))
        local_today = cursor.fetchone()[0]

        conn.close()
        return online_today, local_today
    except Exception as e:
        print(f"Database error: {e}")
        return 0, 0


def main():
    """Show comprehensive status of Smart Lead Finder modes"""
    print("🔍 SMART LEAD FINDER STATUS CHECK")
    print("=" * 50)

    # Check running processes
    python_processes = check_running_processes()
    print(f"🐍 Python Processes Running: {python_processes}")

    # Check database activity
    recent_online, recent_local, latest = check_database_activity()

    if recent_online is not None:
        print(f"\n📊 RECENT ACTIVITY (Last 10 minutes):")
        print(f"   🌱 Online Mode: {recent_online} new leads")
        print(f"   🏠 Local Mode: {recent_local} new leads")

        if latest:
            mode, timestamp = latest
            time_str = timestamp[:19] if len(timestamp) > 19 else timestamp
            print(f"   ⏰ Latest Activity: {mode} mode at {time_str}")

    # Today's stats
    online_today, local_today = get_daily_stats()
    total_today = online_today + local_today
    remaining = max(0, 75 - total_today)

    print(f"\n📈 TODAY'S PROGRESS:")
    print(f"   🌱 Online Leads: {online_today}")
    print(f"   🏠 Local Leads: {local_today}")
    print(f"   📊 Total Today: {total_today}/75")
    print(f"   🎯 Remaining: {remaining}")

    # Status indicators
    print(f"\n🚦 STATUS INDICATORS:")

    if recent_online and recent_online > 0:
        print("   🌱 ONLINE MODE: 🟢 ACTIVE (finding leads)")
    elif online_today > 0:
        print("   🌱 ONLINE MODE: 🟡 IDLE (ran today)")
    else:
        print("   🌱 ONLINE MODE: ⚪ NOT RUNNING")

    if recent_local and recent_local > 0:
        print("   🏠 LOCAL MODE: 🟢 ACTIVE (finding leads)")
    elif local_today > 0:
        print("   🏠 LOCAL MODE: 🟡 IDLE (ran today)")
    else:
        print("   🏠 LOCAL MODE: ⚪ NOT RUNNING")

    # Show how to launch
    print(f"\n💻 TO LAUNCH:")
    print("   🌱 Online: Click 'Find Vegan Leads' in dashboard")
    print("   🏠 Local: Click 'Find Local Leads' in dashboard")
    print("   📊 Dashboard: python run_dashboard.py")

    print(f"\n✅ Status check complete!")


if __name__ == "__main__":
    main()
