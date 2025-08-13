# Daily Prospect Manager - Phase 2 of Lead Generation
# Manages prospects from previous day: checks follow-backs, sends DMs, unfollows non-followers

import time
import datetime
import random
import sqlite3
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Script configuration
SQLITE_DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
CHROMEDRIVER_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"

# Instagram credentials
USERNAME = "cocos_connected"
PASSWORD = "Shannonb3"

# Daily limits
DAILY_UNFOLLOW_LIMIT = 75
# No DM limit - we DM everyone who follows back!

# DM Templates based on hashtag categories
DM_TEMPLATES = {
    'vegan_fitness': [
        "Heya! Noticed you're into plant based fitness 🌱 How's your training going?",
        "Hey! Love seeing another plant-based fitness enthusiast 🌱💪 What's your current focus?",
        "Hi! Fellow vegan fitness lover here 🌱 What's your favourite type of training?"
    ],
    'vegan_lifestyle': [
        "Hey! Fellow vegan here 🌱 Been vegetarian since birth myself, how's your journey been?",
        "Heya! Love your plant-based content 🌱 How long have you been vegan?",
        "Hey! Another plant-based soul 🌱 What got you into the vegan lifestyle?"
    ],
    'nutrition': [
        "Hey! Love your approach to nutrition 🌱 What's your biggest focus right now?",
        "Heya! Your food posts look amazing 🌱 Do you meal prep much?",
        "Hey! Fellow nutrition enthusiast here 🌱 What's your go-to healthy meal?"
    ],
    'default': [
        "Heya! Love your content 🌱 Hope you're having a great day!",
        "Hey! Just wanted to say your posts are inspiring 💚",
        "Hi there! Love following your journey 🌱"
    ]
}

# Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option(
    "excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


class DailyProspectManager:
    def __init__(self):
        self.driver = None
        self.run_id = None
        self.follow_backs_found = 0
        self.dms_sent = 0
        self.unfollows_completed = 0

    def get_db_connection(self):
        """Get database connection."""
        return sqlite3.connect(SQLITE_DB_PATH)

    def log_run(self, status, error_message=None):
        """Log run status to database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.datetime.now().isoformat()

            if status == 'started':
                cursor.execute("""
                    INSERT INTO lead_generation_runs 
                    (run_type, run_timestamp, status, leads_found, leads_followed, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ('manage_prospects', current_time, status, 0, 0, error_message))
                self.run_id = cursor.lastrowid
                print(
                    f"📈 Started daily prospect management (ID: {self.run_id})")
            elif self.run_id:
                cursor.execute("""
                    UPDATE lead_generation_runs
                    SET status = ?, leads_found = ?, leads_followed = ?, error_message = ?
                    WHERE id = ?
                """, (status, self.follow_backs_found, self.dms_sent, error_message, self.run_id))
                print(f"📈 Updated session {self.run_id}: {status}")

            conn.commit()
        finally:
            conn.close()

    def get_prospects_to_check(self):
        """Get prospects that need follow-back checking."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Get users followed 24+ hours ago that haven't been checked yet
            check_date = (datetime.datetime.now() -
                          datetime.timedelta(days=1)).isoformat()
            cursor.execute("""
                SELECT username, hashtag_found, followed_at 
                FROM processing_queue 
                WHERE check_after_date <= ? 
                AND follow_back_status = 'pending'
                ORDER BY followed_at DESC
                LIMIT 100
            """, (check_date,))

            prospects = cursor.fetchall()
            return prospects
        finally:
            conn.close()

    def get_daily_dm_count(self):
        """Get today's DM count for statistics only."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT COUNT(*) FROM processing_queue WHERE DATE(dm_sent_at) = ?", (today,))
            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()

    def setup_driver(self):
        """Initialize Chrome driver."""
        try:
            service = webdriver.chrome.service.Service(
                executable_path=CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Chrome driver initialized in headless mode")
            return True
        except Exception as e:
            print(f"❌ Failed to setup driver: {e}")
            return False

    def login_to_instagram(self):
        """Login to Instagram."""
        try:
            print("🔐 Logging into Instagram...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            time.sleep(random.uniform(1, 2))

            # Password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(PASSWORD)
            time.sleep(random.uniform(1, 2))

            # Login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            time.sleep(10)

            # Check if login successful
            if "instagram.com/accounts/login" not in self.driver.current_url:
                print("✅ Successfully logged into Instagram")
                self.handle_post_login_popups()
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False

    def handle_post_login_popups(self):
        """Handle popups after login."""
        try:
            time.sleep(3)
            # Handle "Save Login Info" and notifications popups
            for _ in range(2):
                try:
                    not_now_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Not Now')]")
                    not_now_button.click()
                    time.sleep(2)
                except:
                    break
        except Exception as e:
            print(f"Note: No popups to handle")

    def check_if_following_back(self, username):
        """Check if a user is following us back."""
        try:
            print(f"🔍 Checking if @{username} follows back...")

            # Navigate to their profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 6))

            # Check for "Follows you" indicator
            try:
                follows_you_element = self.driver.find_element(
                    By.XPATH, "//span[contains(text(), 'Follows you')]")
                if follows_you_element.is_displayed():
                    print(f"✅ @{username} follows back!")
                    return True
            except NoSuchElementException:
                pass

            # Check button text - if it's "Following" and there's no "Follows you", they don't follow back
            try:
                button_elements = self.driver.find_elements(
                    By.XPATH, "//button[contains(text(), 'Following') or contains(text(), 'Follow')]")
                for button in button_elements:
                    if button.is_displayed():
                        button_text = button.text.lower()
                        if 'following' in button_text:
                            # We're following them, but no "Follows you" indicator
                            print(f"❌ @{username} does not follow back")
                            return False
            except:
                pass

            print(f"⚠️ Could not determine follow-back status for @{username}")
            return None

        except Exception as e:
            print(f"❌ Error checking follow-back for @{username}: {e}")
            return None

    def categorize_hashtag(self, hashtag):
        """Categorize hashtag for appropriate DM template."""
        hashtag = hashtag.lower()

        if any(term in hashtag for term in ['fitness', 'training', 'workout', 'gym', 'strength']):
            return 'vegan_fitness'
        elif any(term in hashtag for term in ['recipe', 'food', 'meal', 'nutrition', 'cooking']):
            return 'nutrition'
        elif any(term in hashtag for term in ['vegan', 'plantbased', 'community', 'lifestyle', 'life']):
            return 'vegan_lifestyle'
        else:
            return 'default'

    def get_dm_message(self, hashtag_found):
        """Get appropriate DM message based on hashtag category."""
        category = self.categorize_hashtag(hashtag_found)
        templates = DM_TEMPLATES.get(category, DM_TEMPLATES['default'])
        return random.choice(templates)

    def send_dm(self, username, message):
        """Send a DM to a user."""
        try:
            print(f"💬 Sending DM to @{username}...")

            # Navigate to DM page
            dm_url = f"https://www.instagram.com/direct/new/"
            self.driver.get(dm_url)
            time.sleep(random.uniform(3, 5))

            # Search for username
            try:
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@placeholder='Search...']"))
                )
                search_box.clear()
                search_box.send_keys(username)
                time.sleep(random.uniform(2, 3))

                # Click on the user from search results
                user_result = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//span[contains(text(), '{username}')]"))
                )
                user_result.click()
                time.sleep(random.uniform(1, 2))

                # Click Chat button
                chat_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Chat')]"))
                )
                chat_button.click()
                time.sleep(random.uniform(2, 3))

            except TimeoutException:
                # Alternative method - direct message URL
                print(f"   Trying direct message approach...")
                dm_url = f"https://www.instagram.com/direct/t/{username}/"
                self.driver.get(dm_url)
                time.sleep(random.uniform(3, 5))

            # Type and send message
            try:
                message_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//textarea[@placeholder='Message...']"))
                )
                message_box.clear()

                # Type message character by character for human-like behavior
                for char in message:
                    message_box.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                time.sleep(random.uniform(1, 2))

                # Send message
                send_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Send')]"))
                )
                send_button.click()
                time.sleep(random.uniform(2, 3))

                print(f"✅ DM sent to @{username}: {message[:50]}...")
                self.dms_sent += 1
                return True

            except TimeoutException:
                print(
                    f"❌ Could not send DM to @{username} - message box not found")
                return False

        except Exception as e:
            print(f"❌ Error sending DM to @{username}: {e}")
            return False

    def unfollow_user(self, username):
        """Unfollow a user."""
        try:
            print(f"❌ Unfollowing @{username}...")

            # Navigate to their profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 6))

            # Find Following button and click it
            try:
                following_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Following')]"))
                )
                following_button.click()
                time.sleep(random.uniform(1, 2))

                # Confirm unfollow
                unfollow_confirm = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Unfollow')]"))
                )
                unfollow_confirm.click()
                time.sleep(random.uniform(2, 3))

                print(f"✅ Successfully unfollowed @{username}")
                self.unfollows_completed += 1
                return True

            except TimeoutException:
                print(f"⚠️ Could not find Following button for @{username}")
                return False

        except Exception as e:
            print(f"❌ Error unfollowing @{username}: {e}")
            return False

    def update_prospect_status(self, username, follow_back_status, dm_message=None):
        """Update prospect status in database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.datetime.now().isoformat()

            if dm_message:
                cursor.execute("""
                    UPDATE processing_queue 
                    SET follow_back_status = ?, follow_back_checked_at = ?, 
                        dm_sent_at = ?, dm_message = ?, dm_status = 'sent'
                    WHERE username = ?
                """, (follow_back_status, current_time, current_time, dm_message, username))
            else:
                cursor.execute("""
                    UPDATE processing_queue 
                    SET follow_back_status = ?, follow_back_checked_at = ?
                    WHERE username = ?
                """, (follow_back_status, current_time, username))

            conn.commit()
            print(f"📊 Updated status for @{username}: {follow_back_status}")
        except Exception as e:
            print(f"❌ Error updating status for @{username}: {e}")
        finally:
            conn.close()

    def run_prospect_management(self):
        """Main function to manage daily prospects."""
        print("🚀 Starting Daily Prospect Manager...")

        # Log session start
        self.log_run('started')

        try:
            # Get prospects to check
            prospects = self.get_prospects_to_check()

            if not prospects:
                print("📭 No prospects ready for follow-back checking")
                self.log_run('completed')
                return

            print(f"👥 Found {len(prospects)} prospects to check")

            # Get daily DM count for statistics
            daily_dms = self.get_daily_dm_count()
            print(f"📊 Daily DMs sent so far: {daily_dms}")

            # Setup browser
            if not self.setup_driver():
                self.log_run('failed', 'Failed to setup browser')
                return

            # Login
            if not self.login_to_instagram():
                self.log_run('failed', 'Failed to login to Instagram')
                return

            # Process each prospect
            for username, hashtag_found, followed_at in prospects:
                try:
                    print(
                        f"\n🔄 Processing @{username} (followed from #{hashtag_found})")

                    # Check if they follow back
                    follows_back = self.check_if_following_back(username)

                    if follows_back is True:
                        # They follow back - ALWAYS send DM (no limit!)
                        print(f"✅ @{username} follows back! Sending DM...")
                        message = self.get_dm_message(hashtag_found)
                        if self.send_dm(username, message):
                            self.update_prospect_status(
                                username, 'follows_back', message)
                            self.follow_backs_found += 1

                            # Delay between DMs
                            delay = random.uniform(60, 120)
                            print(
                                f"⏳ Waiting {delay:.1f}s before next action...")
                            time.sleep(delay)
                        else:
                            self.update_prospect_status(
                                username, 'follows_back')

                    elif follows_back is False:
                        # They don't follow back - unfollow them
                        if self.unfollow_user(username):
                            self.update_prospect_status(
                                username, 'no_follow_back')

                        # Delay between unfollows
                        delay = random.uniform(30, 60)
                        print(f"⏳ Waiting {delay:.1f}s before next action...")
                        time.sleep(delay)

                    else:
                        # Could not determine status
                        self.update_prospect_status(username, 'unknown')
                        print(
                            f"⚠️ Could not determine follow-back status for @{username}")

                except Exception as e:
                    print(f"❌ Error processing @{username}: {e}")
                    continue

            print(f"\n🎉 Prospect management complete!")
            print(f"📊 Final stats:")
            print(f"   - Follow-backs found: {self.follow_backs_found}")
            print(f"   - DMs sent: {self.dms_sent}")
            print(f"   - Unfollows completed: {self.unfollows_completed}")

            self.log_run('completed')

        except Exception as e:
            print(f"❌ Critical error: {e}")
            self.log_run('failed', str(e))

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("✅ Browser closed")
                except:
                    pass


if __name__ == "__main__":
    manager = DailyProspectManager()
    manager.run_prospect_management()
