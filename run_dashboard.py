#!/usr/bin/env python3
"""
Shannon's Bot Dashboard Launcher
Run the Streamlit dashboard with Smart Lead Finder
"""

import os
import sys
import subprocess


def main():
    """Launch the Streamlit dashboard."""
    print("🚀 Starting Shannon's Bot Dashboard...")

    # Path to the dashboard
    dashboard_path = os.path.join("app", "dashboard_modules", "dashboard.py")

    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard not found at: {dashboard_path}")
        print("Make sure you're running this from the shanbot directory")
        return

    print("✅ Found dashboard file")
    print("📱 Opening browser with Smart Lead Finder...")
    print("\n" + "="*50)
    print("🎯 TO RUN SMART LEAD FINDER:")
    print("1. Navigate to 'Lead Generation' tab")
    print("2. Click 'Find New Leads' button")
    print("3. Monitor progress in 'Recent Activity'")
    print("="*50 + "\n")

    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            dashboard_path,
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running dashboard: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
