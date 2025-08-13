import logging
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime, timedelta
import random
import time
import sqlite3
"""
Follow Users Script - Phase 1 of Outreach System
Follows users from the potential clients database and logs them for delayed DM sending.
"""


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('follow_users.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class UserFollower:
    def __init__(self):
        self.driver = None
        self.daily_follow_limit = 25
        self.follows_today = 0
        self.run_id = None  # To store the ID of the current run log

    def setup_driver(self):
        """Initialize Chrome driver with stealth settings"""
        chrome_options = Options()

        # Run in headless mode for dashboard integration
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Stealth settings
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
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")

        # User agent for headless mode
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def handle_post_login_popups(self):
        """Handle the various popups that might appear after login"""
        try:
            # List of common popups and their dismiss button selectors
            popups = [
                {
                    "name": "Save Login Info",
                    "selectors": [
                        "//button[contains(text(), 'Not Now')]",
                        "//button[contains(text(), 'Save Info')]",
                        "//button[contains(text(), 'Not now')]",
                        # Class sometimes used for "Not Now"
                        "//button[contains(@class, 'HoLwm')]"
                    ]
                },
                {
                    "name": "Notifications",
                    "selectors": [
                        "//button[contains(text(), 'Not Now')]",
                        "//button[contains(text(), 'Not now')]",
                        "//button[contains(text(), 'Turn on Notifications')]",
                        # Common class for notification buttons
                        "//button[contains(@class, '_a9--')]"
                    ]
                },
                {
                    "name": "Add to Home Screen",
                    "selectors": [
                        "//button[contains(text(), 'Cancel')]",
                        "//button[contains(text(), 'Not Now')]"
                    ]
                }
            ]

            for popup in popups:
                for selector in popup["selectors"]:
                    try:
                        element = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            element.click()
                            logging.info(f"✅ Dismissed {popup['name']} popup")
                            time.sleep(2)
                            break
                    except (TimeoutException, NoSuchElementException):
                        continue

        except Exception as e:
            logging.debug(f"No popups to handle or error handling popups: {e}")

    def login_to_instagram(self):
        """Login to Instagram using provided credentials with robust error handling."""
        try:
            # Navigate to Instagram login page
            logging.info("🔐 Navigating to login page...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)  # Wait for page to load

            # Check if already logged in
            if "instagram.com/accounts/login" not in self.driver.current_url:
                logging.info("✅ Already logged in to Instagram")
                return True

            logging.info("Attempting login...")

            # Try multiple selectors for username field
            username_field_selectors = [
                (By.NAME, "username"),
                (By.XPATH, "//input[@name='username']"),
                (By.XPATH,
                 "//input[@aria-label='Phone number, username, or email']"),
                (By.XPATH,
                 "//input[@placeholder='Phone number, username, or email']"),
                (By.XPATH, "//input[contains(@placeholder, 'username')]"),
                (By.XPATH, "//input[contains(@placeholder, 'email')]"),
                # Often the first input in a form is username
                (By.XPATH, "//form//input[1]"),
            ]

            username_field = None
            for selector_type, selector_value in username_field_selectors:
                try:
                    elements = self.driver.find_elements(
                        selector_type, selector_value)
                    for element in elements:
                        if element.is_displayed():
                            username_field = element
                            logging.info(
                                f"Found username field with selector: {selector_type}={selector_value}")
                            break
                    if username_field:
                        break
                except Exception as e:
                    logging.debug(
                        f"Selector {selector_type}={selector_value} failed: {e}")
                    continue

            if not username_field:
                logging.error(
                    "❌ Could not find username field with any selector")
                return False

            # Enter username
            username_field.clear()
            username_field.send_keys("cocos_connected")
            logging.info("Entered username: cocos_connected")
            time.sleep(random.uniform(1, 2))

            # Try multiple selectors for password field
            password_field_selectors = [
                (By.NAME, "password"),
                (By.XPATH, "//input[@name='password']"),
                (By.XPATH, "//input[@aria-label='Password']"),
                (By.XPATH, "//input[@placeholder='Password']"),
                (By.XPATH, "//input[@type='password']"),
                # Often the second input in a form is password
                (By.XPATH, "//form//input[2]"),
            ]

            password_field = None
            for selector_type, selector_value in password_field_selectors:
                try:
                    elements = self.driver.find_elements(
                        selector_type, selector_value)
                    for element in elements:
                        if element.is_displayed():
                            password_field = element
                            logging.info(
                                f"Found password field with selector: {selector_type}={selector_value}")
                            break
                    if password_field:
                        break
                except Exception:
                    continue

            if not password_field:
                logging.error(
                    "❌ Could not find password field with any selector")
                return False

            # Enter password
            password_field.clear()
            password_field.send_keys("Shannonb3")
            logging.info("Entered password")
            time.sleep(random.uniform(1, 2))

            # Try multiple selectors for login button
            login_button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//div[contains(text(), 'Log in')]/parent::button"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//form//button"),  # Generic - any button in a form
            ]

            login_button = None
            for selector_type, selector_value in login_button_selectors:
                try:
                    elements = self.driver.find_elements(
                        selector_type, selector_value)
                    for element in elements:
                        if element.is_displayed():
                            login_button = element
                            logging.info(
                                f"Found login button with selector: {selector_type}={selector_value}")
                            break
                    if login_button:
                        break
                except Exception:
                    continue

            if not login_button:
                logging.error(
                    "❌ Could not find login button with any selector")
                return False

            # Try multiple login click approaches
            login_successful = False

            # First attempt: standard click
            try:
                logging.info("Attempting standard click on login button...")
                time.sleep(1)
                login_button.click()
                logging.info("Standard click executed.")
                time.sleep(8)  # Wait for potential page change

                if "/accounts/login" not in self.driver.current_url:
                    logging.info("✅ Login successful after standard click.")
                    login_successful = True
                else:
                    logging.warning(
                        "Still on login page after standard click. Trying JS click...")
            except Exception as click_err:
                logging.warning(
                    f"Standard click failed: {click_err}. Trying JS click...")

            # Second attempt: JavaScript click
            if not login_successful:
                try:
                    logging.info(
                        "Attempting JavaScript click on login button...")
                    self.driver.execute_script(
                        "arguments[0].click();", login_button)
                    logging.info("JavaScript click executed.")
                    time.sleep(8)

                    if "/accounts/login" not in self.driver.current_url:
                        logging.info(
                            "✅ Login successful after JavaScript click.")
                        login_successful = True
                    else:
                        logging.error(
                            "❌ Still on login page after JavaScript click.")
                except Exception as js_err:
                    logging.error(f"JavaScript click failed: {js_err}")

            # Final check and handle popups if login was successful
            if login_successful:
                logging.info("✅ Login successful overall.")
                self.handle_post_login_popups()
                return True
            else:
                logging.error("❌ Login failed overall.")
                return False

        except Exception as e:
            logging.error(f"❌ Error during login: {e}")
            return False

    def get_db_connection(self):
        """Establishes a connection to the SQLite database. Centralized for reuse."""
        return sqlite3.connect('app/analytics_data_good.sqlite')

    def _create_follow_runs_table(self):
        """Creates the follow_users_runs table if it doesn't exist."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follow_users_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL, -- 'started', 'completed', 'failed'
                    users_followed INTEGER,
                    error_message TEXT
                )
            """
                           )
            conn.commit()
            logging.info("✅ Ensured follow_users_runs table exists.")
        finally:
            conn.close()

    def _log_follow_run(self, status, users_followed=0, error_message=None):
        """Logs the start, completion, or failure of a follow_users.py run."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.now().isoformat()

            if status == 'started':
                cursor.execute("""
                    INSERT INTO follow_users_runs (run_timestamp, status, users_followed, error_message)
                    VALUES (?, ?, ?, ?)
                """, (current_time, status, users_followed, error_message))
                self.run_id = cursor.lastrowid  # Store the ID for updates
                logging.info(
                    f"📈 Logged new follow session start (ID: {self.run_id}).")
            elif self.run_id is not None:
                cursor.execute("""
                    UPDATE follow_users_runs
                    SET status = ?, users_followed = ?, error_message = ?
                    WHERE id = ?
                """, (status, users_followed, error_message, self.run_id))
                logging.info(
                    f"📈 Updated follow session ID {self.run_id} to '{status}' with {users_followed} users.")
            else:
                # Fallback for logging if run_id somehow wasn't set (shouldn't happen if 'started' is logged first)
                cursor.execute("""
                    INSERT INTO follow_users_runs (run_timestamp, status, users_followed, error_message)
                    VALUES (?, ?, ?, ?)
                """, (current_time, status, users_followed, error_message))
                logging.warning(
                    f"⚠️ Logged follow session status '{status}' without a run_id.")

            conn.commit()
        finally:
            conn.close()

    def get_unfollowed_users(self):
        """Get users from database who haven't been followed yet"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Add follow tracking columns if they don't exist
            self.add_follow_columns_to_new_leads()

            # Get users who haven't been followed yet from new_leads table
            cursor.execute("""
                SELECT username, hashtag_found, interests, lifestyle_indicators 
                FROM new_leads 
                WHERE followed_at IS NULL 
                AND status = 'new'
                ORDER BY created_at DESC
                LIMIT ?
            """, (self.daily_follow_limit,))

            users = cursor.fetchall()
            return users
        finally:
            conn.close()

    def check_daily_follows(self):
        """Check how many users we've followed today"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) FROM new_leads 
                WHERE DATE(followed_at) = ?
            """, (today,))

            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()

    def update_follow_status(self, username, status_result: str):
        """Update database with follow status and timestamp"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_timestamp = datetime.now().isoformat()

            cursor.execute("""
                UPDATE new_leads 
                SET followed_at = ?, follow_status = ?
                WHERE username = ?
            """, (current_timestamp, status_result, username))

            conn.commit()
        finally:
            conn.close()

    def add_follow_columns_to_new_leads(self):
        """Add follow tracking columns to new_leads table if they don't exist"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            try:
                cursor.execute(
                    "ALTER TABLE new_leads ADD COLUMN followed_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute(
                    "ALTER TABLE new_leads ADD COLUMN follow_status TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute(
                    "ALTER TABLE new_leads ADD COLUMN dm_sent_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

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

            try:
                cursor.execute(
                    "ALTER TABLE new_leads ADD COLUMN follow_back_status TEXT DEFAULT 'pending'")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute(
                    "ALTER TABLE new_leads ADD COLUMN follow_back_checked_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()
        finally:
            conn.close()

    def add_follow_columns_if_needed(self):
        """Legacy method - now calls new_leads version"""
        self.add_follow_columns_to_new_leads()

    def run_follow_session(self):
        """Main function to run a follow session"""
        logging.info("[START] Starting follow session...")

        # Create the run log table if it doesn't exist
        self._create_follow_runs_table()
        # Log the start of the session
        self._log_follow_run('started')

        # Add database columns if needed
        self.add_follow_columns_if_needed()

        # Check daily limit
        follows_today = self.check_daily_follows()
        remaining_follows = self.daily_follow_limit - follows_today

        if remaining_follows <= 0:
            logging.info(
                f"✋ Daily follow limit reached ({self.daily_follow_limit}). Stopping.")
            return

        logging.info(
            f"📊 Follows today: {follows_today}/{self.daily_follow_limit}")
        logging.info(f"🎯 Can follow {remaining_follows} more users today")

        # Get users to follow
        users_to_follow = self.get_unfollowed_users()
        # Respect daily limit
        users_to_follow = users_to_follow[:remaining_follows]

        if not users_to_follow:
            logging.info("📭 No new users to follow")
            return

        logging.info(f"👥 Found {len(users_to_follow)} users to follow")

        # Setup browser
        self.setup_driver()

        try:
            # Login to Instagram
            if not self.login_to_instagram():
                logging.error("❌ Failed to login. Stopping follow session.")
                self._log_follow_run(
                    'failed', error_message="Failed to login to Instagram")
                return

            successful_follows = 0

            for username, hashtag_found, interests, lifestyle_indicators in users_to_follow:
                try:
                    logging.info(
                        f"🔄 Processing @{username} (found via #{hashtag_found})")

                    result = self.follow_user(username)
                    self.update_follow_status(username, result)

                    if result != "failed_exception":
                        successful_follows += 1

                    # Random delay between follows (30-90 seconds)
                    delay = random.uniform(30, 90)
                    logging.info(
                        f"⏳ Waiting {delay:.1f} seconds before next follow...")
                    time.sleep(delay)

                except Exception as e:
                    logging.error(f"❌ Error processing @{username}: {str(e)}")
                    self.update_follow_status(username, "failed_exception")
                    continue

            logging.info(
                f"✅ Follow session complete! Successfully followed {successful_follows}/{len(users_to_follow)} users")

            self._log_follow_run('completed', successful_follows)

        except Exception as e:
            logging.error(f"❌ Critical error in follow session: {str(e)}")
            self._log_follow_run('failed', successful_follows, str(e))

        finally:
            if self.driver:
                self.driver.quit()

    def follow_user(self, username):
        """Follow a specific user on Instagram"""
        try:
            # Navigate to user profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)

            # Wait for page to load
            time.sleep(random.uniform(3, 6))

            # Look for follow button
            follow_selectors = [
                "//button[text()='Follow']",
                "//button[contains(text(), 'Follow')]",
                "//div[text()='Follow']",
                "//span[text()='Follow']",
                "[aria-label='Follow']",
                "button[type='button']"
            ]

            found_button = False
            for selector in follow_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        follow_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS selector
                        follow_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, selector))
                        )

                    # Check if button text is actually "Follow" (not "Following" or "Requested")
                    button_text = follow_button.text.lower()
                    if 'follow' in button_text and 'following' not in button_text and 'requested' not in button_text:
                        follow_button.click()
                        logging.info(f"✅ Successfully followed @{username}")
                        return "followed"
                    elif 'following' in button_text or 'requested' in button_text:
                        logging.warning(
                            f"⚠️ Already following or requested @{username}")
                        return "already_followed"
                    else:
                        # This case means a button was found, but its text was not 'Follow', 'Following', or 'Requested'
                        logging.warning(
                            f"⚠️ Unexpected button text for @{username}: {button_text}")
                        return "failed_unexpected_button_text"

                except (TimeoutException, NoSuchElementException):
                    continue

            if not found_button:
                logging.warning(
                    f"⚠️ Could not find a recognizable follow button for @{username}")
                return "failed_no_button"

        except Exception as e:
            logging.error(f"❌ Error following @{username}: {str(e)}")
            return "failed_exception"


if __name__ == "__main__":
    follower = UserFollower()
    follower.run_follow_session()
