import sys
import argparse
import sqlite3
import time
import random
from datetime import datetime, timedelta
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os
import shutil
import tempfile
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Import the DailyFollowBackChecker class
from check_daily_follow_backs import DailyFollowBackChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('missed_dms_improved.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class ImprovedMissedDMSender(DailyFollowBackChecker):
    """Improved version with better error handling and driver restart capabilities"""

    def __init__(self, username="cocos_connected", password="Shannonb3"):
        super().__init__(username, password, analyze_profiles=False)
        self.max_retries_per_user = 3
        self.driver_restart_count = 0
        self.max_driver_restarts = 5

    def restart_driver_with_retry(self):
        """Restart driver with retry logic"""
        for attempt in range(3):
            try:
                logging.info(
                    f"🔄 Restarting driver (attempt {attempt + 1}/3)...")
                self.teardown_driver()
                time.sleep(5)  # Wait before restart
                self.setup_driver()

                if self.login_to_instagram():
                    logging.info(
                        "✅ Driver restarted and logged in successfully")
                    return True
                else:
                    logging.error("❌ Failed to login after driver restart")

            except Exception as e:
                logging.error(
                    f"❌ Driver restart attempt {attempt + 1} failed: {e}")
                time.sleep(10)  # Wait longer before next attempt

        logging.error("❌ All driver restart attempts failed")
        return False

    def is_driver_responsive(self):
        """Check if driver is responsive"""
        try:
            self.driver.current_url
            self.driver.execute_script("return document.readyState;")
            return True
        except Exception:
            return False

    def send_dm_with_retry(self, username, message):
        """Send DM with retry logic and driver restart if needed"""
        for attempt in range(self.max_retries_per_user):
            try:
                logging.info(
                    f"💬 Sending DM to @{username} (attempt {attempt + 1}/{self.max_retries_per_user})")

                # Check driver health before attempting DM
                if not self.is_driver_responsive():
                    logging.warning(
                        f"⚠️ Driver unresponsive, attempting restart...")
                    if not self.restart_driver_with_retry():
                        logging.error(
                            f"❌ Failed to restart driver for @{username}")
                        return False

                # Attempt to send DM
                if self.send_dm_to_user(username, message):
                    logging.info(f"✅ DM sent successfully to @{username}")
                    return True
                else:
                    logging.warning(
                        f"⚠️ DM attempt {attempt + 1} failed for @{username}")

            except Exception as e:
                logging.error(
                    f"❌ Error in DM attempt {attempt + 1} for @{username}: {e}")

                # Check if it's a driver-related error
                if "connection" in str(e).lower() or "webdriver" in str(e).lower():
                    logging.warning(
                        f"🔄 Driver error detected, attempting restart...")
                    if not self.restart_driver_with_retry():
                        logging.error(
                            f"❌ Failed to restart driver for @{username}")
                        return False

            # Wait before retry
            if attempt < self.max_retries_per_user - 1:
                retry_delay = random.uniform(10, 20)
                logging.info(f"⏳ Waiting {retry_delay:.1f}s before retry...")
                time.sleep(retry_delay)

        logging.error(f"❌ All retry attempts failed for @{username}")
        return False

    def get_users_who_followed_back_but_no_dm(self, days_back=7):
        """Get users who followed back but never received their DMs"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, follow_back_checked_at, followed_at, dm_status
            FROM processing_queue 
            WHERE follow_back_status = 'yes' 
            AND (dm_status IS NULL OR dm_status != 'sent')
            AND follow_back_checked_at >= date('now', '-' || ? || ' days')
            ORDER BY follow_back_checked_at DESC
        """, (days_back,))

        users = cursor.fetchall()
        conn.close()

        return {user[0]: {
            'checked_at': user[1],
            'followed_at': user[2],
            'dm_status': user[3]
        } for user in users}

    def run_missed_dm_campaign(self):
        """Send DMs to all users who followed back but never received their DMs"""
        logging.info("🚀 Starting Improved Missed DM Campaign...")

        # Get users who need DMs
        users_needing_dms = self.get_users_who_followed_back_but_no_dm(
            days_back=7)

        if not users_needing_dms:
            logging.info(
                "📭 No users found who followed back but missed their DMs!")
            return

        logging.info(
            f"Found {len(users_needing_dms)} users who followed back but never received their DMs")

        # Setup driver and login
        self.setup_driver()

        try:
            if not self.login_to_instagram():
                logging.error(
                    "❌ Failed to login. Stopping missed DM campaign.")
                return

            # Quick popup dismissal
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Not Now')]"))
                ).click()
                logging.info("Dismissed popup")
            except:
                pass

            time.sleep(2)

            # Determine account mode for DM generation
            account_mode = 'local' if self.username == 'cocos_pt_studio' else 'online'

            dms_sent_count = 0
            failed_count = 0
            processed_count = 0

            for username, user_info in users_needing_dms.items():
                processed_count += 1
                logging.info(
                    f"📊 Processing {processed_count}/{len(users_needing_dms)}: @{username}")

                try:
                    # Generate DM message
                    dm_message = self.generate_dm_message(
                        username, account_mode)

                    # Send DM with retry logic
                    if self.send_dm_with_retry(username, dm_message):
                        # Store DM in conversation history
                        self.store_dm_in_conversation_history(
                            username, dm_message)

                        # Update database
                        self.update_dm_status(username, dm_message, 'sent')
                        dms_sent_count += 1

                        logging.info(
                            f"✅ Missed DM sent successfully to @{username}")

                        # Delay between successful DMs
                        delay = random.uniform(30, 45)
                        logging.info(
                            f"⏳ Waiting {delay:.1f}s before next DM...")
                        time.sleep(delay)

                    else:
                        self.update_dm_status(username, dm_message, 'failed')
                        failed_count += 1
                        logging.warning(
                            f"❌ Failed to send missed DM to @{username}")

                except Exception as e:
                    logging.error(
                        f"❌ Critical error processing @{username}: {e}")
                    self.update_dm_status(username, "", 'failed')
                    failed_count += 1
                    continue

            # Final report
            logging.info("\n" + "="*50)
            logging.info("📋 IMPROVED MISSED DM CAMPAIGN REPORT")
            logging.info("="*50)
            logging.info(f"Total Users Found: {len(users_needing_dms)}")
            logging.info(f"Users Processed: {processed_count}")
            logging.info(f"DMs Sent Successfully: {dms_sent_count}")
            logging.info(f"Failed DMs: {failed_count}")
            logging.info(
                f"Success Rate: {(dms_sent_count/len(users_needing_dms)*100):.1f}%")
            logging.info(f"Driver Restarts: {self.driver_restart_count}")
            logging.info("="*50)

        except Exception as e:
            logging.critical(
                f"Critical error in improved missed DM campaign: {e}")
        finally:
            self.teardown_driver()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send DMs to users who followed back but never received their DMs (Improved Version)')
    parser.add_argument('--account', type=str, choices=['local', 'online'], default='online',
                        help='Account mode: "local" for @cocos_pt_studio, "online" for @cocos_connected')
    args = parser.parse_args()

    # Set credentials based on account mode
    if args.account == 'local':
        username = "cocos_pt_studio"
        print(f"🏠 LOCAL MODE: Sending missed DMs for @{username}")
    else:
        username = "cocos_connected"
        print(f"🌱 ONLINE MODE: Sending missed DMs for @{username}")

    sender = ImprovedMissedDMSender(username=username)
    sender.run_missed_dm_campaign()
