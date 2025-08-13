import sqlite3
import json
from datetime import datetime

SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def check_leads_now():
    """Check for leads in the database right now"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='new_leads'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("❌ new_leads table doesn't exist yet")
            print("💡 This means the script hasn't created it yet - no leads found so far")
            conn.close()
            return

        # Count total leads
        cursor.execute("SELECT COUNT(*) FROM new_leads")
        total_count = cursor.fetchone()[0]

        if total_count == 0:
            print("📊 new_leads table exists but is empty")
            print("💡 The script is running but hasn't found any qualifying leads yet")
            conn.close()
            return

        # Get all leads with analysis data to check search mode
        cursor.execute("""
            SELECT username, coaching_score, hashtag_found, created_at, analysis_data 
            FROM new_leads 
            ORDER BY created_at DESC
        """)
        all_leads = cursor.fetchall()

        # Categorize by search mode
        local_leads = []
        online_leads = []
        unknown_leads = []

        for lead in all_leads:
            username, score, hashtag, created_at, analysis_data = lead
            try:
                analysis = json.loads(analysis_data) if analysis_data else {}
                search_mode = analysis.get('search_mode', 'unknown')

                if search_mode == 'local':
                    local_leads.append(lead)
                elif search_mode == 'online':
                    online_leads.append(lead)
                else:
                    unknown_leads.append(lead)
            except:
                unknown_leads.append(lead)

        print(f"🎉 Found {total_count} total leads in database!")
        print(f"📍 Local leads: {len(local_leads)}")
        print(f"🌱 Online leads: {len(online_leads)}")
        print(f"❓ Unknown mode: {len(unknown_leads)}")

        # Show recent local leads specifically
        if local_leads:
            print(f"\n🏠 RECENT LOCAL LEADS ({len(local_leads)} total):")
            for i, (username, score, hashtag, created_at, analysis_data) in enumerate(local_leads[:5], 1):
                print(f"\n{i}. @{username}")
                print(f"   📊 Score: {score}/100")
                print(f"   🔍 Found via: #{hashtag}")
                print(f"   📅 Added: {created_at}")
        else:
            print(f"\n🏠 NO LOCAL LEADS FOUND YET")
            print(
                "💡 If you're running in local mode, the script might still be searching...")
            print(
                "💡 Local leads are harder to find as they need to be in the Bayside area")

        # Show recent online leads
        if online_leads:
            print(
                f"\n🌱 RECENT ONLINE LEADS (showing 3 of {len(online_leads)}):")
            for i, (username, score, hashtag, created_at, analysis_data) in enumerate(online_leads[:3], 1):
                print(f"\n{i}. @{username}")
                print(f"   📊 Score: {score}/100")
                print(f"   🔍 Found via: #{hashtag}")
                print(f"   📅 Added: {created_at}")

        conn.close()

    except Exception as e:
        print(f"❌ Error checking database: {e}")


if __name__ == "__main__":
    print("🔍 Checking for new leads in real-time...")
    print("=" * 50)
    check_leads_now()
    print("\n💡 Run this script anytime to check current status!")
