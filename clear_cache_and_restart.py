#!/usr/bin/env python3
"""
Clear Streamlit cache and restart dashboard to fix conversation history display
"""

import os
import shutil
import subprocess
import time


def clear_streamlit_cache():
    """Clear Streamlit cache to force reload of conversation history."""
    print("🧹 CLEARING STREAMLIT CACHE")
    print("=" * 40)

    # Find and clear .streamlit directory
    cache_dirs = [
        ".streamlit",
        os.path.expanduser("~/.streamlit"),
        os.path.expanduser("~/.cache/streamlit")
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared cache directory: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Could not clear {cache_dir}: {e}")
        else:
            print(f"ℹ️ Cache directory not found: {cache_dir}")

    print("✅ Cache clearing completed")


def restart_dashboard():
    """Restart the dashboard with fresh cache."""
    print("\n🔄 RESTARTING DASHBOARD")
    print("=" * 40)

    dashboard_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules\dashboard.py"

    if os.path.exists(dashboard_path):
        print(f"🚀 Starting dashboard: {dashboard_path}")
        print("💡 The dashboard should now show conversation history correctly!")
        print("\n📋 Instructions:")
        print("   1. The dashboard will open in your browser")
        print("   2. Go to 'Response & Review' section")
        print("   3. Conversation history should now be visible")
        print("   4. If not, try refreshing the browser page")

        # Start the dashboard
        try:
            subprocess.Popen([
                "python", "-m", "streamlit", "run", dashboard_path,
                "--server.headless", "true"
            ])
            print("✅ Dashboard started successfully!")
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            print("💡 You can manually start it with:")
            print(
                f"   python -m streamlit run {dashboard_path} --server.headless true")
    else:
        print(f"❌ Dashboard file not found: {dashboard_path}")


def main():
    """Main function to clear cache and restart dashboard."""
    print("🔧 FIXING CONVERSATION HISTORY DISPLAY")
    print("=" * 50)

    # Step 1: Clear cache
    clear_streamlit_cache()

    # Step 2: Wait a moment
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)

    # Step 3: Restart dashboard
    restart_dashboard()

    print("\n🎉 Process completed!")
    print("📊 Your conversation history should now be visible in the dashboard.")


if __name__ == "__main__":
    main()
