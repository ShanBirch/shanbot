#!/usr/bin/env python3
"""
Outreach Scheduler - Automated Two-Phase System
Runs follow script, then schedules DM script for 3 hours later.
"""

import subprocess
import time
import schedule
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outreach_scheduler.log'),
        logging.StreamHandler()
    ]
)


class OutreachScheduler:
    def __init__(self):
        self.follow_script = "follow_users.py"
        self.dm_script = "send_delayed_dms.py"

    def run_follow_script(self):
        """Run the follow users script"""
        try:
            logging.info("🚀 Starting follow script...")
            result = subprocess.run(['python', self.follow_script],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("✅ Follow script completed successfully")
                logging.info(f"Output: {result.stdout}")

                # Schedule DM script for 3 hours later
                dm_time = datetime.now() + timedelta(hours=3)
                logging.info(
                    f"📅 DM script scheduled for {dm_time.strftime('%H:%M:%S')}")

                schedule.every().day.at(dm_time.strftime('%H:%M')).do(
                    self.run_dm_script).tag('dm_job')

            else:
                logging.error(f"❌ Follow script failed: {result.stderr}")

        except Exception as e:
            logging.error(f"❌ Error running follow script: {str(e)}")

    def run_dm_script(self):
        """Run the DM script"""
        try:
            logging.info("💬 Starting DM script...")
            result = subprocess.run(['python', self.dm_script],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("✅ DM script completed successfully")
                logging.info(f"Output: {result.stdout}")
            else:
                logging.error(f"❌ DM script failed: {result.stderr}")

            # Clear the scheduled job after running
            schedule.clear('dm_job')

        except Exception as e:
            logging.error(f"❌ Error running DM script: {str(e)}")

    def run_daily_outreach(self):
        """Run the complete daily outreach sequence"""
        logging.info("🎯 Starting daily outreach sequence...")
        self.run_follow_script()

    def start_scheduler(self):
        """Start the automated scheduler"""
        logging.info("⏰ Starting outreach scheduler...")

        # Schedule daily outreach at 10 AM
        schedule.every().day.at("10:00").do(self.run_daily_outreach)

        # Also allow manual trigger
        logging.info("📋 Scheduler commands:")
        logging.info("  - Daily outreach scheduled for 10:00 AM")
        logging.info("  - DM script will auto-run 3 hours after follow script")
        logging.info("  - Press Ctrl+C to stop scheduler")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logging.info("⏹️ Scheduler stopped by user")


if __name__ == "__main__":
    import sys

    scheduler = OutreachScheduler()

    if len(sys.argv) > 1:
        if sys.argv[1] == "follow":
            # Manual follow script run
            scheduler.run_follow_script()
        elif sys.argv[1] == "dm":
            # Manual DM script run
            scheduler.run_dm_script()
        elif sys.argv[1] == "both":
            # Manual full sequence
            scheduler.run_daily_outreach()
        else:
            print("Usage: python outreach_scheduler.py [follow|dm|both]")
    else:
        # Start automated scheduler
        scheduler.start_scheduler()
