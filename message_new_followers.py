#!/usr/bin/env python3
"""
Message New Followers Script - Send DMs to users who followed back but haven't been messaged
"""

import os
import sys
import sqlite3
import time
import argparse
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('message_new_followers.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NewFollowerMessenger:
    def __init__(self, username="cocos_connected", password="Shannonb3", dry_run=False, limit=50):
        """Initialize the messenger for contacting new followers"""
        self.username = username
        self.password = password
        self.dry_run = dry_run
        self.limit = limit
        self.driver = None
        self.db_path = os.path.join(os.path.dirname(
            __file__), 'app', 'analytics_data_good.sqlite')

        # The specific message to send
        self.message_template = "Heya :) Love your content! How long have you been vegan for?"

        # Results tracking
        self.results = {
            'found_users': 0,
            'messages_sent': 0,
            'errors': 0,
            'already_messaged': 0,
            'users_processed': []
        }

    def setup_driver(self):
        """Set up Chrome driver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            # Use existing profile for faster login
            profile_path = os.path.join(
                os.path.dirname(__file__), "chrome_profile")
            if os.path.exists(profile_path):
                chrome_options.add_argument(f"--user-data-dir={profile_path}")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)

            logger.info("✅ Chrome driver setup successful")
            return True

        except Exception as e:
            logger.error(f"❌ Error setting up Chrome driver: {e}")
            return False

    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None

    def get_unmessaged_followers(self):
        """Get list of users who followed back but haven't been messaged yet"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []

            cursor = conn.cursor()

            # Find users who followed back but haven't been messaged
            query = """
            SELECT DISTINCT username, followed_at, follow_back_checked_at
            FROM processing_queue 
            WHERE follow_back_status = 'yes'
            AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
            AND DATE(followed_at) >= DATE('now', '-14 days')
            ORDER BY follow_back_checked_at DESC
            LIMIT ?
            """

            cursor.execute(query, (self.limit * 2,))
            users = cursor.fetchall()

            logger.info(
                f"Found {len(users)} users who followed back but haven't been messaged")

            # Also check conversation_history to make sure they really haven't been messaged
            filtered_users = []
            for username, followed_at, checked_at in users:
                cursor.execute("""
                    SELECT COUNT(*) FROM conversation_history 
                    WHERE ig_username = ? AND message_type = 'ai'
                """, (username,))

                ai_message_count = cursor.fetchone()[0]

                if ai_message_count == 0:
                    filtered_users.append({
                        'username': username,
                        'followed_at': followed_at,
                        'checked_at': checked_at
                    })
                else:
                    logger.info(
                        f"Skipping {username} - already has {ai_message_count} AI messages")
                    self.results['already_messaged'] += 1

            conn.close()

            self.results['found_users'] = len(filtered_users)
            logger.info(
                f"After filtering: {len(filtered_users)} users need messaging")

            return filtered_users[:self.limit]

        except Exception as e:
            logger.error(f"Error getting unmessaged followers: {e}")
            return []

    def login_to_instagram(self):
        """Login to Instagram"""
        try:
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)

            # Check if already logged in
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "nav[role='navigation']"))
                )
                logger.info("✅ Already logged in to Instagram")
                return True
            except TimeoutException:
                pass

            # Need to login
            logger.info("🔑 Logging into Instagram...")

            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.clear()
            username_input.send_keys(self.username)

            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "nav[role='navigation']"))
            )

            logger.info("✅ Successfully logged into Instagram")
            time.sleep(3)

            # Handle post-login popups
            self.handle_post_login_popups()

            return True

        except Exception as e:
            logger.error(f"❌ Error logging into Instagram: {e}")
            return False

    def handle_post_login_popups(self):
        """Handle common popups after login"""
        try:
            # Handle "Not Now" buttons
            for _ in range(2):
                try:
                    not_now_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[text()='Not Now' or text()='Not now']"))
                    )
                    not_now_btn.click()
                    logger.info("Dismissed popup")
                    time.sleep(2)
                except TimeoutException:
                    break

        except Exception as e:
            logger.info(f"Post-login popup handling: {e}")

    def send_dm_to_user(self, username):
        """Send a DM to a specific user"""
        try:
            logger.info(f"📤 Sending DM to @{username}")

            if self.dry_run:
                logger.info(
                    f"🔥 DRY RUN: Would send to @{username}: '{self.message_template}'")
                return True

            # Navigate to user's DM
            dm_url = f"https://www.instagram.com/direct/t/{username}/"
            self.driver.get(dm_url)
            time.sleep(3)

            # Find message input
            try:
                message_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[@contenteditable='true'][@role='textbox'] | "
                        "//textarea[@placeholder='Message...'] | "
                        "//div[contains(@aria-label, 'Message')][@contenteditable='true']"
                    ))
                )
            except TimeoutException:
                logger.error(f"Could not find message input for @{username}")
                return False

            # Send message
            message_input.clear()
            message_input.send_keys(self.message_template)
            time.sleep(1)
            message_input.send_keys(Keys.RETURN)
            time.sleep(2)

            logger.info(f"✅ Message sent to @{username}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending DM to @{username}: {e}")
            return False

    def update_dm_status(self, username, status, message=None):
        """Update the dm_status in the database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            if message:
                cursor.execute("""
                    UPDATE processing_queue 
                    SET dm_status = ?, dm_message = ?, dm_sent_at = ?
                    WHERE username = ?
                """, (status, message, datetime.now().isoformat(), username))
            else:
                cursor.execute("""
                    UPDATE processing_queue 
                    SET dm_status = ?
                    WHERE username = ?
                """, (status, username))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error updating DM status for {username}: {e}")
            return False

    def add_to_conversation_history(self, username, message):
        """Add the sent message to conversation history using unified messages table"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # Get subscriber_id for this user if available
            cursor.execute(
                "SELECT subscriber_id FROM users WHERE ig_username = ?", (username,))
            user_result = cursor.fetchone()
            subscriber_id = user_result[0] if user_result else None

            cursor.execute("""
                INSERT INTO messages 
                (ig_username, subscriber_id, message_type, message_text, timestamp)
                VALUES (?, ?, 'ai', ?, ?)
            """, (username, subscriber_id, message, datetime.now().isoformat()))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(
                f"Error adding to conversation history for {username}: {e}")
            return False

    def process_users(self, users_to_message):
        """Process the list of users and send them messages"""
        if not users_to_message:
            logger.info("No users to message")
            return

        logger.info(f"🚀 Starting to process {len(users_to_message)} users...")

        for i, user_info in enumerate(users_to_message, 1):
            username = user_info['username']

            logger.info(
                f"📝 Processing {i}/{len(users_to_message)}: @{username}")

            try:
                success = self.send_dm_to_user(username)

                if success:
                    self.results['messages_sent'] += 1

                    if not self.dry_run:
                        self.update_dm_status(
                            username, 'sent', self.message_template)
                        self.add_to_conversation_history(
                            username, self.message_template)

                    self.results['users_processed'].append({
                        'username': username,
                        'status': 'sent',
                        'followed_at': user_info['followed_at'],
                        'checked_at': user_info['checked_at']
                    })

                else:
                    self.results['errors'] += 1
                    if not self.dry_run:
                        self.update_dm_status(username, 'failed')

                    self.results['users_processed'].append({
                        'username': username,
                        'status': 'failed',
                        'followed_at': user_info['followed_at'],
                        'checked_at': user_info['checked_at']
                    })

                # Wait between messages
                if i < len(users_to_message):
                    wait_time = 15 if not self.dry_run else 1
                    logger.info(f"⏱️ Waiting {wait_time} seconds...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"❌ Error processing @{username}: {e}")
                self.results['errors'] += 1

                if not self.dry_run:
                    self.update_dm_status(username, 'error')

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 Chrome driver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

    def print_summary(self):
        """Print a summary of the results"""
        print("\n" + "="*60)
        print("📊 NEW FOLLOWER MESSAGING SUMMARY")
        print("="*60)
        print(f"👥 Found users needing messages: {self.results['found_users']}")
        print(f"✅ Messages sent successfully: {self.results['messages_sent']}")
        print(f"❌ Errors encountered: {self.results['errors']}")
        print(
            f"🔄 Already messaged (skipped): {self.results['already_messaged']}")

        if self.dry_run:
            print(f"\n🔥 DRY RUN MODE - No actual messages were sent")

        if self.results['users_processed']:
            print(f"\n📋 PROCESSED USERS:")
            for user in self.results['users_processed']:
                status_emoji = "✅" if user['status'] == 'sent' else "❌"
                print(
                    f"  {status_emoji} @{user['username']} - {user['status']}")

        print("="*60)

    def run(self):
        """Main execution method"""
        try:
            logger.info("🚀 Starting New Follower Messaging Script")

            if self.dry_run:
                logger.info("🔥 Running in DRY RUN mode")

            # Get users who need messaging
            users_to_message = self.get_unmessaged_followers()

            if not users_to_message:
                logger.info("✨ No users found who need messaging!")
                return

            logger.info(
                f"📝 Found {len(users_to_message)} users who need messaging")

            # Show preview
            print(f"\n📋 USERS TO MESSAGE:")
            for user in users_to_message:
                print(
                    f"  • @{user['username']} (followed back: {user['checked_at']})")

            print(f"\n💬 Message to send: '{self.message_template}'")

            if not self.dry_run:
                confirm = input(
                    f"\n🤔 Send messages to {len(users_to_message)} users? (y/N): ")
                if confirm.lower() != 'y':
                    logger.info("❌ Cancelled by user")
                    return

            # Setup browser
            if not self.setup_driver():
                logger.error("❌ Failed to setup browser")
                return

            # Login to Instagram
            if not self.login_to_instagram():
                logger.error("❌ Failed to login to Instagram")
                return

            # Process users
            self.process_users(users_to_message)

            # Show summary
            self.print_summary()

        except KeyboardInterrupt:
            logger.info("⚠️ Script interrupted by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description='Send messages to new followers who followed back')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without actually sending messages')
    parser.add_argument('--limit', type=int, default=50,
                        help='Maximum number of messages to send (default: 50)')

    args = parser.parse_args()

    messenger = NewFollowerMessenger(
        dry_run=args.dry_run,
        limit=args.limit
    )

    messenger.run()


if __name__ == "__main__":
    main()
