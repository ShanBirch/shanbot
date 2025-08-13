#!/usr/bin/env python3
"""
Send Delayed DMs Script - Phase 2 of Outreach System
Sends personalized DMs to users who were followed 2-4 hours ago.
"""

import sqlite3
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('send_dms.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class DMSender:
    def __init__(self):
        self.driver = None
        self.daily_dm_limit = 20

        # Your current clients for mutual connection messages
        self.your_clients = [
            'kristyleecoop', 'le_greenies', 'rebeccadangelo01',
            'payneinthenix', 'simonetindallrealestate'
        ]

        # Famous influencers for community messages
        self.famous_influencers = [
            'nimai_delgado', 'plantyou', 'pickuplimes', 'earthyandy',
            'fullyrawkristina', 'the_buddhist_chef', 'vegan_bodybuilding'
        ]

    def setup_driver(self):
        """Initialize Chrome driver with stealth settings"""
        chrome_options = Options()
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Use a separate profile for automation to avoid conflicts
        chrome_options.add_argument(
            "--user-data-dir=C:/Users/Shannon/AppData/Local/Google/Chrome/User Data Automation")
        chrome_options.add_argument("--profile-directory=Default")

        # Additional options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def login_to_instagram(self):
        """Login to Instagram with cocos_connected account"""
        try:
            logging.info("🔐 Attempting to login to Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Check if already logged in
            if "instagram.com/accounts/login" not in self.driver.current_url:
                logging.info("✅ Already logged in to Instagram")
                return True

            # Find username field with multiple selectors
            username_input = None
            username_selectors = [
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.CSS_SELECTOR,
                 "input[aria-label='Phone number, username, or email']")
            ]

            for selector_type, selector in username_selectors:
                try:
                    username_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (selector_type, selector))
                    )
                    break
                except:
                    continue

            if not username_input:
                logging.error("❌ Could not find username field")
                return False

            username_input.clear()
            username_input.send_keys("cocos_connected")
            time.sleep(2)

            # Find password field
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys("Shannonb3")
            time.sleep(2)

            # Click login button
            login_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Log in')]")
            ]

            login_clicked = False
            for selector_type, selector in login_selectors:
                try:
                    login_button = self.driver.find_element(
                        selector_type, selector)
                    login_button.click()
                    login_clicked = True
                    break
                except:
                    continue

            if not login_clicked:
                logging.error("❌ Could not find login button")
                return False

            time.sleep(8)  # Wait longer for login to process

            # Check if login was successful
            current_url = self.driver.current_url
            if "instagram.com/accounts/login" not in current_url and "challenge" not in current_url:
                logging.info("✅ Successfully logged in to Instagram")
                return True
            else:
                logging.error(f"❌ Login failed. Current URL: {current_url}")
                return False

        except Exception as e:
            logging.error(f"❌ Error during login: {str(e)}")
            return False

    def get_users_ready_for_dm(self):
        """Get users who were followed 2-4 hours ago and haven't been DMed yet"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Calculate time window (2-4 hours ago)
        now = datetime.now()
        min_time = now - timedelta(hours=4)
        max_time = now - timedelta(hours=2)

        cursor.execute("""
            SELECT username, hashtag_found, interests, lifestyle_indicators, followed_at
            FROM new_leads 
            WHERE followed_at IS NOT NULL 
            AND dm_sent_at IS NULL
            AND datetime(followed_at) BETWEEN ? AND ?
            AND follow_status = 'followed'
            ORDER BY followed_at ASC
            LIMIT ?
        """, (min_time.isoformat(), max_time.isoformat(), self.daily_dm_limit))

        users = cursor.fetchall()
        conn.close()
        return users

    def check_daily_dms(self):
        """Check how many DMs we've sent today"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM new_leads 
            WHERE DATE(dm_sent_at) = ?
        """, (today,))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def generate_message(self, username, hashtag_found, interests, lifestyle_indicators):
        """Generate personalized message based on source and bio"""

        # Determine message type based on hashtag source
        # For now, default to community approach since we're using hashtag data
        message_type = "community"

        # Generate message based on type
        if message_type == "mutual_connection":
            messages = [
                f"Hey! Noticed you follow {source_account} - love connecting with people in the same circles! How's your week going?",
                f"Hey! Saw you're connected to {source_account} - always cool meeting people through mutual connections! Hope you're well :)",
                f"Hey! I see you follow {source_account} too - small world! How's things going?",
                f"Hey! Noticed we both follow {source_account} - love making connections through mutual friends! How's your day?"
            ]
        else:  # community approach
            messages = [
                "Hey! Noticed you're into the plant based fitness scene - always cool meeting like minded people! Hope you're well :)",
                "Hey! Saw you follow some of the same plant based accounts I do - love connecting with people in the community! How's things?",
                "Hey! Noticed you're plant based too - always nice connecting with people who share similar values! How's your week going?",
                "Hey! Saw you're into plant based living - love meeting people in the community! Hope you're having a good week :)"
            ]

        return random.choice(messages)

    def send_dm(self, username, message):
        """Send a DM to a specific user"""
        try:
            # Navigate to user's profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 6))

            # Look for message button
            message_selectors = [
                "//button[contains(text(), 'Message')]",
                "[aria-label='Message']",
                "button:contains('Message')",
                "//div[contains(text(), 'Message')]",
                "//a[contains(@href, '/direct/')]"
            ]

            message_button_found = False
            for selector in message_selectors:
                try:
                    if selector.startswith("//"):
                        message_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        message_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, selector))
                        )

                    message_button.click()
                    message_button_found = True
                    break

                except (TimeoutException, NoSuchElementException):
                    continue

            if not message_button_found:
                logging.warning(
                    f"⚠️ Could not find message button for @{username}")
                return False

            # Wait for message input to appear
            time.sleep(random.uniform(2, 4))

            # Find message input field
            input_selectors = [
                "textarea[placeholder*='Message']",
                "div[contenteditable='true']",
                "textarea[aria-label*='Message']",
                "//textarea[contains(@placeholder, 'Message')]",
                "//div[@contenteditable='true']"
            ]

            message_sent = False
            for selector in input_selectors:
                try:
                    if selector.startswith("//"):
                        message_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, selector))
                        )
                    else:
                        message_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, selector))
                        )

                    # Clear and type message
                    message_input.clear()
                    time.sleep(1)
                    message_input.send_keys(message)
                    time.sleep(random.uniform(1, 3))

                    # Look for send button
                    send_selectors = [
                        "button[type='submit']",
                        "//button[contains(text(), 'Send')]",
                        "[aria-label='Send message']",
                        "//div[contains(text(), 'Send')]"
                    ]

                    for send_selector in send_selectors:
                        try:
                            if send_selector.startswith("//"):
                                send_button = self.driver.find_element(
                                    By.XPATH, send_selector)
                            else:
                                send_button = self.driver.find_element(
                                    By.CSS_SELECTOR, send_selector)

                            send_button.click()
                            message_sent = True
                            logging.info(
                                f"✅ Successfully sent DM to @{username}")
                            break

                        except NoSuchElementException:
                            continue

                    if message_sent:
                        break

                except (TimeoutException, NoSuchElementException):
                    continue

            if not message_sent:
                logging.warning(f"⚠️ Could not send message to @{username}")
                return False

            # Random delay after sending
            time.sleep(random.uniform(3, 7))
            return True

        except Exception as e:
            logging.error(f"❌ Error sending DM to @{username}: {str(e)}")
            return False

    def update_dm_status(self, username, message, success=True):
        """Update database with DM status and timestamp"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        if success:
            cursor.execute("""
                UPDATE new_leads 
                SET dm_sent_at = ?, dm_message = ?, dm_status = 'sent'
                WHERE username = ?
            """, (datetime.now().isoformat(), message, username))
        else:
            cursor.execute("""
                UPDATE new_leads 
                SET dm_status = 'failed'
                WHERE username = ?
            """, (username,))

        conn.commit()
        conn.close()

    def add_dm_columns_if_needed(self):
        """Add DM tracking columns to database if they don't exist"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        try:
            cursor.execute(
                "ALTER TABLE new_leads ADD COLUMN dm_message TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute(
                "ALTER TABLE new_leads ADD COLUMN dm_status TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        conn.close()

    def run_dm_session(self):
        """Main function to run a DM session"""
        logging.info("💬 Starting DM session...")

        # Add database columns if needed
        self.add_dm_columns_if_needed()

        # Check daily limit
        dms_today = self.check_daily_dms()
        remaining_dms = self.daily_dm_limit - dms_today

        if remaining_dms <= 0:
            logging.info(
                f"✋ Daily DM limit reached ({self.daily_dm_limit}). Stopping.")
            return

        logging.info(f"📊 DMs sent today: {dms_today}/{self.daily_dm_limit}")
        logging.info(f"🎯 Can send {remaining_dms} more DMs today")

        # Get users ready for DMs
        users_for_dm = self.get_users_ready_for_dm()
        users_for_dm = users_for_dm[:remaining_dms]  # Respect daily limit

        if not users_for_dm:
            logging.info(
                "📭 No users ready for DMs (need to wait 2-4 hours after following)")
            return

        logging.info(f"👥 Found {len(users_for_dm)} users ready for DMs")

        # Setup browser
        self.setup_driver()

        try:
            # Login to Instagram
            if not self.login_to_instagram():
                logging.error("❌ Failed to login. Stopping DM session.")
                return

            successful_dms = 0

            for username, hashtag_found, interests, lifestyle_indicators, followed_at in users_for_dm:
                try:
                    logging.info(
                        f"💬 Sending DM to @{username} (found via #{hashtag_found})")

                    # Generate personalized message
                    message = self.generate_message(
                        username, hashtag_found, interests, lifestyle_indicators)
                    logging.info(f"📝 Message: {message}")

                    success = self.send_dm(username, message)
                    self.update_dm_status(username, message, success)

                    if success:
                        successful_dms += 1

                    # Random delay between DMs (60-120 seconds)
                    delay = random.uniform(60, 120)
                    logging.info(
                        f"⏳ Waiting {delay:.1f} seconds before next DM...")
                    time.sleep(delay)

                except Exception as e:
                    logging.error(
                        f"❌ Error processing DM to @{username}: {str(e)}")
                    self.update_dm_status(username, "", False)
                    continue

            logging.info(
                f"✅ DM session complete! Successfully sent {successful_dms}/{len(users_for_dm)} DMs")

        except Exception as e:
            logging.error(f"❌ Critical error in DM session: {str(e)}")

        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    dm_sender = DMSender()
    dm_sender.run_dm_session()
