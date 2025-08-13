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

print("✅ Basic imports successful")

# Gemini AI imports
try:
    import google.generativeai as genai
    import google.api_core.exceptions
    print("✅ Google AI imports successful")
except Exception as e:
    print(f"❌ Google AI import error: {e}")
    exit(1)

# --- NEW: Import Instagram Analysis Functions ---

# Add the script directory to Python path so we can import anaylize_followers
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from anaylize_followers import (
        extract_profile_info,
        analyze_profile,
        analyze_multiple_images_with_gemini,
        has_complete_instagram_analysis_sqlite,
        update_analytics_sqlite,
        analyze_with_gemini,
        generate_profile_bio
    )
    print("✅ Successfully imported Instagram analysis functions")
except ImportError as e:
    print(f"❌ Failed to import Instagram analysis functions: {e}")
    print("📝 Bio analysis will be disabled for this run")
    # Create dummy functions so the script doesn't crash
    def extract_profile_info(*args, **kwargs): return {}
    def analyze_profile(*args, **kwargs): return None
    def analyze_multiple_images_with_gemini(*args, **kwargs): return None
    def has_complete_instagram_analysis_sqlite(*args, **kwargs): return False
    def update_analytics_sqlite(*args, **kwargs): return False
    def analyze_with_gemini(*args, **kwargs): return None
    def generate_profile_bio(*args, **kwargs): return {}
except Exception as e:
    print(f"❌ Unexpected error importing analysis functions: {e}")
    sys.exit(1)

# Configure Gemini for DM generation
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini models for fallback
gemini_models = [
    ('gemini-2.0-flash', genai.GenerativeModel('gemini-2.0-flash')),
    ('gemini-2.0-flash-lite', genai.GenerativeModel('gemini-2.0-flash-lite')),
    ('gemini-2.0-flash-thinking-exp-01-21',
     genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21'))
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_follow_backs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Add imports for conversation history integration
try:
    import sys
    import os
    # Add the app directory to path to import dashboard functions
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    dashboard_modules_dir = os.path.join(
        os.path.dirname(__file__), 'app', 'dashboard_modules')
    if app_dir not in sys.path:
        sys.path.append(app_dir)
    if dashboard_modules_dir not in sys.path:
        sys.path.append(dashboard_modules_dir)

    from dashboard_sqlite_utils import add_message_to_history
    print("✅ Successfully imported conversation history functions")
    CONVERSATION_HISTORY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Could not import conversation history functions: {e}")
    print("📝 DM messages will not be stored in conversation history")
    CONVERSATION_HISTORY_AVAILABLE = False
    # Create dummy function so script doesn't crash
    def add_message_to_history(*args, **kwargs): return False


class DailyFollowBackChecker:
    def __init__(self, username="cocos_connected", password="Shannonb3", analyze_profiles=True):
        self.username = username
        self.password = password
        self.driver = None
        self.temp_user_data_dir = None
        self.daily_unfollow_limit = 50  # Set a daily limit for unfollowing
        self.analyze_profiles = analyze_profiles  # NEW: Control bio analysis

    def setup_driver(self):
        """Initialize Chrome driver with enhanced stability and crash prevention"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Disabled headless mode so you can watch
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Enhanced memory and stability improvements
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument(
            "--max_old_space_size=8192")  # Increased memory limit
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=TranslateUI")

        # Additional stability options
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-domain-reliability")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-breakpad")
        chrome_options.add_argument("--disable-crash-reporter")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")  # Suppress most logging

        # Performance optimizations
        chrome_options.add_argument("--enable-features=VaapiVideoDecoder")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--enable-gpu-rasterization")
        chrome_options.add_argument("--enable-zero-copy")

        # Create a temporary directory for user data to avoid conflicts
        self.temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(
            f"--user-data-dir={self.temp_user_data_dir}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Set conservative timeouts to prevent hanging
        self.driver.set_page_load_timeout(45)  # Increased timeout
        self.driver.implicitly_wait(8)  # Reduced implicit wait

        logging.info(
            "Chrome driver initialized with enhanced stability and crash prevention.")

    def check_driver_health(self):
        """Check if the WebDriver is still responsive and functional"""
        try:
            # Simple test - get current URL
            current_url = self.driver.current_url
            # Try a simple JavaScript execution
            self.driver.execute_script("return document.readyState;")
            return True
        except Exception as e:
            logging.error(f"❌ Driver health check failed: {e}")
            return False

    def restart_driver_if_needed(self):
        """Restart the driver if it's unresponsive"""
        if not self.check_driver_health():
            logging.warning(
                "🔄 Driver appears unhealthy, attempting restart...")
            try:
                self.teardown_driver()
                time.sleep(5)
                self.setup_driver()
                return self.login_to_instagram()
            except Exception as e:
                logging.error(f"❌ Failed to restart driver: {e}")
                return False
        return True

    def handle_dm_interface_popups(self):
        """Handle specific popups that appear when DM interface opens"""
        logging.debug("🚪 Checking for DM interface popups...")

        dm_popups = [
            {
                "name": "Turn on Notifications",
                "selectors": [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Turn On')]//following-sibling::button",
                    "//div[contains(text(), 'Turn on notifications')]//ancestor::div[@role='dialog']//button[contains(text(), 'Not Now')]",
                    "//button[@aria-label='Not Now']",
                    "//button[contains(@class, '_a9--') and contains(text(), 'Not Now')]"
                ]
            },
            {
                "name": "Instagram Direct Message Info",
                "selectors": [
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'Got it')]",
                    "//button[contains(text(), 'Dismiss')]",
                    "//div[contains(text(), 'Direct')]//ancestor::div[@role='dialog']//button"
                ]
            },
            {
                "name": "Message Requests Info",
                "selectors": [
                    "//button[contains(text(), 'Not Now')]",
                    "//button[contains(text(), 'Skip')]",
                    "//div[contains(text(), 'message request')]//ancestor::div[@role='dialog']//button[contains(text(), 'Not Now')]"
                ]
            },
            {
                "name": "Safety Notice",
                "selectors": [
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'I Understand')]",
                    "//div[contains(text(), 'safety')]//ancestor::div[@role='dialog']//button"
                ]
            }
        ]

        popups_found = 0
        for popup in dm_popups:
            for selector in popup["selectors"]:
                try:
                    # Use shorter timeout for DM popups
                    element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if element.is_displayed():
                        # Try JavaScript click first for reliability
                        self.driver.execute_script(
                            "arguments[0].click();", element)
                        logging.info(
                            f"✅ Dismissed {popup['name']} popup in DM interface")
                        time.sleep(1)
                        popups_found += 1
                        break  # Move to next popup type
                except (TimeoutException, NoSuchElementException, WebDriverException):
                    continue

        if popups_found > 0:
            logging.info(f"🧹 Dismissed {popups_found} DM interface popup(s)")
            time.sleep(1)  # Brief pause after popup dismissal

        return popups_found > 0

    def teardown_driver(self):
        """Quits the driver and cleans up the temporary user data directory."""
        if self.driver:
            self.driver.quit()
            logging.info("WebDriver closed.")
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                shutil.rmtree(self.temp_user_data_dir)
                logging.info(
                    f"Cleaned up temporary user data directory: {self.temp_user_data_dir}")
            except Exception as e:
                logging.warning(
                    f"Failed to remove temporary directory {self.temp_user_data_dir}: {e}")

    def handle_post_login_popups(self):
        """Handle the various popups that might appear after login"""
        try:
            popups = [
                {"name": "Save Login Info", "selectors": [
                    "//button[contains(text(), 'Not Now')]", "//button[contains(text(), 'Save Info')]", "//button[contains(text(), 'Not now')]", "//button[contains(@class, 'HoLwm')]",
                    # More general for role=button
                    "//button[@role='button'][contains(., 'Not Now')]",
                    # For buttons with tabindex
                    "//button[@tabindex='0'][contains(., 'Not Now')]"

                ]},
                {"name": "Notifications", "selectors": ["//button[contains(text(), 'Not Now')]", "//button[contains(text(), 'Not now')]",
                                                        "//button[contains(text(), 'Turn on Notifications')]", "//button[contains(@class, '_a9--')]",
                                                        "//button[@role='button'][contains(., 'Not Now')]",
                                                        "//button[@tabindex='0'][contains(., 'Not Now')]"]},
                {"name": "Add to Home Screen", "selectors": [
                    "//button[contains(text(), 'Cancel')]", "//button[contains(text(), 'Not Now')]",
                    "//button[@role='button'][contains(., 'Cancel')]"

                ]},
                {"name": "Generic Dismiss", "selectors": [
                    "//button[contains(text(), 'Dismiss')]",
                    # For close buttons that are divs with aria-label
                    "//div[@aria-label='Close']",
                    # For close buttons that are buttons with aria-label
                    "//button[@aria-label='Close']",
                    # General interactive button not login/signup
                    "//div[@role='button'][contains(@tabindex, '0') and not(contains(text(), 'Log in')) and not(contains(text(), 'Sign up'))]"
                ]}
            ]

            for popup in popups:
                logging.debug(
                    f"Attempting to dismiss {popup['name']} popups...")
                for selector in popup["selectors"]:
                    try:
                        # Use presence_of_element_located combined with element_to_be_clickable
                        element = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located(
                                (By.XPATH, selector))
                        )
                        if element.is_displayed() and element.is_enabled():
                            logging.info(
                                f"Attempting click on {popup['name']} via {selector}")
                            # Use JS click for reliability
                            self.driver.execute_script(
                                "arguments[0].click();", element)
                            logging.info(
                                f"✅ Dismissed {popup['name']} popup via JS click")
                            time.sleep(1)  # Short pause after dismissal
                            break  # Break inner loop, move to next popup type
                    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
                        logging.debug(
                            f"Selector {selector} for {popup['name']} not found or clickable: {e}")
                        continue

        except Exception as e:
            logging.debug(f"Error handling popups: {e}")

    def wait_for_page_to_load_and_dismiss_overlays(self, timeout=15):
        """Waits for the page to load and aggressively tries to dismiss common overlays.
        This is crucial before attempting to click primary page elements.
        """
        logging.info(
            "Waiting for page to load and dismissing potential overlays...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.close_any_modal():  # Aggressively try to close anything, and continue if something was closed
                time.sleep(1.5)  # Longer pause if a modal was just closed
            else:
                time.sleep(0.5)  # Shorter pause if no modal was closed

            # Check if any part of the main content is visible, indicating overlays might be gone
            try:
                # Look for the main content area (e.g., the profile header or post section)
                WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//main[@role='main'] | //header[@role='banner'] | //article"))
                )
                logging.debug("Main content appears visible.")
                return True  # Assumed page loaded and overlays dismissed
            except (TimeoutException, NoSuchElementException):
                logging.debug(
                    "Main content not yet fully visible or still covered by overlay.")
                continue
        logging.warning(
            "Timed out waiting for page to load and dismiss overlays.")
        return False

    def get_db_connection(self):
        """Get database connection - tries different paths"""
        db_paths = [
            # Standard shanbot database path
            r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite",
            # Alternative path if script is run from different location
            os.path.join(os.path.dirname(__file__), 'app',
                         'analytics_data_good.sqlite'),
            # Local path relative to script
            'analytics_data_good.sqlite'
        ]

        for db_path in db_paths:
            if os.path.exists(db_path):
                logging.debug(f"Using database at: {db_path}")
                return sqlite3.connect(db_path)

        # If no existing database found, create one in the shanbot directory
        default_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
        logging.info(f"Creating new database at: {default_path}")
        return sqlite3.connect(default_path)

    def ensure_fresh_lead_column(self):
        """Ensure the fresh_lead column exists in the processing_queue table"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Check if fresh_lead column exists
            cursor.execute("PRAGMA table_info(processing_queue)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'fresh_lead' not in columns:
                logging.info(
                    "🔧 Adding fresh_lead column to processing_queue table...")
                cursor.execute(
                    "ALTER TABLE processing_queue ADD COLUMN fresh_lead INTEGER DEFAULT 0")
                conn.commit()
                logging.info("✅ fresh_lead column added successfully")
            else:
                logging.debug("✅ fresh_lead column already exists")

        except Exception as e:
            logging.error(f"❌ Error ensuring fresh_lead column: {e}")
        finally:
            if conn:
                conn.close()

    def ensure_direct_approach_columns(self):
        """Ensure the direct approach columns exist in the processing_queue table"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Check if direct_approach_tagged column exists
            cursor.execute("PRAGMA table_info(processing_queue)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'direct_approach_tagged' not in columns:
                logging.info(
                    "🔧 Adding direct_approach_tagged column to processing_queue table...")
                cursor.execute(
                    "ALTER TABLE processing_queue ADD COLUMN direct_approach_tagged INTEGER DEFAULT 0")
                conn.commit()
                logging.info(
                    "✅ direct_approach_tagged column added successfully")
            else:
                logging.debug("✅ direct_approach_tagged column already exists")

            if 'direct_approach_tagged_at' not in columns:
                logging.info(
                    "🔧 Adding direct_approach_tagged_at column to processing_queue table...")
                cursor.execute(
                    "ALTER TABLE processing_queue ADD COLUMN direct_approach_tagged_at TEXT")
                conn.commit()
                logging.info(
                    "✅ direct_approach_tagged_at column added successfully")
            else:
                logging.debug(
                    "✅ direct_approach_tagged_at column already exists")

        except Exception as e:
            logging.error(f"❌ Error ensuring direct approach columns: {e}")
        finally:
            if conn:
                conn.close()

    def mark_user_as_fresh_lead(self, username):
        """Mark a user as a fresh lead in the database"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE processing_queue
                SET fresh_lead = 1
                WHERE username = ?
            """, (username,))

            conn.commit()
            logging.info(f"✅ Marked @{username} as fresh lead for A/B testing")
            return True

        except Exception as e:
            logging.error(f"❌ Error marking @{username} as fresh lead: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def store_dm_in_conversation_history(self, username, dm_message):
        """Store the sent DM in conversation history for future AI context"""
        if not CONVERSATION_HISTORY_AVAILABLE:
            logging.debug(
                f"⏭️ Conversation history not available, skipping storage for @{username}")
            return False

        try:
            # Store as AI message in conversation history
            success = add_message_to_history(
                ig_username=username,
                message_type='ai',
                message_text=dm_message,
                message_timestamp=None  # Uses current timestamp
            )

            if success:
                logging.info(
                    f"📝 Stored DM in conversation history for @{username}")
                return True
            else:
                logging.warning(
                    f"⚠️ Failed to store DM in conversation history for @{username}")
                return False

        except Exception as e:
            logging.error(
                f"❌ Error storing DM in conversation history for @{username}: {e}")
            return False

    def check_if_following_me_back(self, target_username):
        """OPTIMIZED: Fast follow-back check with aggressive timeouts and early bailouts.
           Returns True if self.username is found, False otherwise.
           MAX TIME: 60 seconds total per user
        """
        import time
        start_time = time.time()
        MAX_CHECK_TIME = 60  # 60 second absolute limit per user

        logging.info(
            f"Checking if @{target_username} is following back @{self.username}...")
        profile_url = f"https://www.instagram.com/{target_username}/"
        self.driver.get(profile_url)
        time.sleep(random.uniform(1, 2))  # Reduced from 3-5s

        # OPTIMIZED: Minimal page load wait
        time.sleep(1)  # Reduced from 2s

        try:
            # OPTIMIZED: Faster following link detection with reduced timeout
            following_link_selectors = [
                # Most direct - click on the span containing "following" text
                "//span[contains(text(), 'following')]",
                # Click on the parent link of following span
                "//span[contains(text(), 'following')]/ancestor::a",
                # Look for the link with following in href
                f"//a[contains(@href, '/{target_username}/following/')]",
                "//a[contains(@href, '/following/')]",
                # Based on your HTML - look for the specific span classes
                "//span[contains(@class, 'x1lliihq') and contains(text(), 'following')]",
                # Click the whole following count area
                "//a[.//span[contains(text(), 'following')]]"
            ]

            following_link = None
            for selector in following_link_selectors:
                # Check time limit
                if time.time() - start_time > MAX_CHECK_TIME:
                    logging.warning(
                        f"⏰ Follow-back check timeout for @{target_username} - aborting")
                    return False

                try:
                    following_link = WebDriverWait(self.driver, 3).until(  # Reduced from 10s to 3s
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if following_link:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue

            if not following_link:
                logging.warning(
                    f"⚠️ Could not find following link for @{target_username} - skipping")
                return False

            logging.info(
                f"🎯 Found following link, clicking to open following list...")

            try:
                # Try direct click first
                following_link.click()
                logging.info(
                    f"✅ Successfully clicked following link for @{target_username}")
            except WebDriverException as e:
                logging.warning(
                    f"Direct click failed, trying JavaScript click: {e}")
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", following_link)
                    logging.info(
                        f"✅ JavaScript click successful for @{target_username}")
                except Exception as js_e:
                    logging.error(
                        f"❌ Both click methods failed for @{target_username}: {js_e}")
                    return False

            # OPTIMIZED: Reduced modal wait
            logging.info(f"⏳ Waiting for following modal to load...")
            time.sleep(1)  # Reduced from 2s

            # OPTIMIZED: Faster modal detection with shorter timeout
            modal_selector = (
                # New common class for modal content
                "//div[@role='dialog']//div[contains(@class, 'x1i10hfl')] | "
                "//div[@role='dialog']//div[contains(@class, '_aano')] | "
                "//div[@role='dialog']//div[contains(@style, 'overflow-y: scroll')] | "
                "//div[@role='dialog']//div[contains(@style, 'overflow-y: auto')] | "
                "//div[@role='dialog']//div[@aria-label='Followers'] | "
                "//div[@role='dialog']//div[contains(@class, 'x1dm5mii')]"
            )

            try:
                scrollable_element = WebDriverWait(self.driver, 5).until(  # Reduced from 10s to 5s
                    EC.presence_of_element_located((By.XPATH, modal_selector))
                )
                logging.info("Found scrollable modal for followers.")
            except TimeoutException:
                logging.warning(
                    "Could not find standard scrollable modal for followers, trying alternative.")
                try:
                    scrollable_element = WebDriverWait(self.driver, 5).until(  # Reduced from 10s to 5s
                        EC.presence_of_element_located((
                            By.XPATH,
                            # More specific path for user list
                            "//div[@role='dialog']/div/div/div/div[2] | "
                            "//div[@role='dialog']/div/div[2] | "
                            "//div[@role='dialog']/div[2]/div/div/div"
                        ))
                    )
                    logging.info("Found alternative scrollable modal.")
                except TimeoutException:
                    logging.error(
                        f"❌ Could not find any modal for @{target_username} - skipping")
                    return False

            last_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", scrollable_element)
            scroll_attempts = 0
            # OPTIMIZED: Reduced max scrolls for faster processing
            max_scrolls = 15  # Reduced from 20

            while scroll_attempts < max_scrolls:
                # Check time limit on each scroll
                if time.time() - start_time > MAX_CHECK_TIME:
                    logging.warning(
                        f"⏰ Follow-back check timeout during scroll for @{target_username}")
                    return False

                # Look for your username specifically with faster timeout
                try:
                    self_username_element = WebDriverWait(scrollable_element, 1).until(  # Reduced from 2s to 1s
                        EC.presence_of_element_located((
                            By.XPATH,
                            f".//a[contains(@href, '{self.username}/') and @role='link'] | "
                            f".//span[text()='{self.username}'] | "
                            f".//div[contains(., '{self.username}')]"
                        ))
                    )
                    if self_username_element.is_displayed():
                        logging.info(
                            f"✅ @{self.username} found in @{target_username}'s followers list.")
                        return True  # Found it!
                except (TimeoutException, NoSuchElementException):
                    pass  # Not found in current view, continue scrolling

                logging.debug(
                    f"🔍 Scrolling @{target_username}'s followers... ({scroll_attempts+1}/{max_scrolls})")
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                # OPTIMIZED: Much faster scroll delay
                time.sleep(random.uniform(0.3, 0.7))  # Reduced from 1-2s

                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", scrollable_element)
                if new_height == last_height:
                    logging.debug("Reached end of scroll in followers modal.")
                    break  # Reached the bottom
                last_height = new_height
                scroll_attempts += 1

            logging.info(
                f"❌ @{self.username} not found in @{target_username}'s followers after {scroll_attempts} scrolls.")
            return False

        except Exception as e:
            logging.error(
                f"❌ Error checking @{target_username}'s followers: {e}")
            return False

        finally:
            # OPTIMIZED: Fast modal closing with timeout awareness
            if time.time() - start_time < MAX_CHECK_TIME:
                self.close_any_modal()
                time.sleep(0.3)  # Reduced from 0.5s
            else:
                logging.warning(
                    f"⏰ Skipping modal close for @{target_username} - time limit exceeded")
                # Emergency ESC only
                try:
                    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(0.2)
                except:
                    pass

            total_time = time.time() - start_time
            logging.info(
                f"🕒 Follow-back check for @{target_username} took {total_time:.1f}s")

    def close_any_modal(self):
        """OPTIMIZED: Fast modal closing with aggressive timeouts and emergency bailouts.
           Returns True if a modal was likely dismissed, False otherwise.
           MAX TIME: 10 seconds total
        """
        import time
        start_time = time.time()
        MAX_MODAL_CLOSE_TIME = 10  # 10 second absolute limit

        logging.debug("🚪 Fast modal closing...")
        modal_dismissed = False

        # PRIORITY: Try ESC key first (fastest method)
        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            logging.info("📤 ESC key sent")
            time.sleep(0.3)  # Reduced from 0.5s
            modal_dismissed = True
        except Exception as e:
            logging.debug(f"ESC key failed: {e}")

        # EMERGENCY: Check time limit
        if time.time() - start_time > MAX_MODAL_CLOSE_TIME:
            logging.warning("⏰ Modal close timeout - forcing exit")
            return modal_dismissed

        # FALLBACK: Try a few quick close button clicks (with individual timeouts)
        quick_selectors = [
            "//button[@aria-label='Close']",
            "//div[@role='dialog']//button[contains(@aria-label, 'Close')]",
            "//button[contains(text(), 'Close')]",
            "//button[contains(text(), 'Not Now')]",  # Common DM popup
            "//button[contains(text(), 'OK')]",       # Common DM popup
            "//button[contains(text(), 'Dismiss')]",  # Common DM popup
            "//div[@role='dialog']//button[contains(text(), 'Not Now')]"
        ]

        for selector in quick_selectors:
            # Check time limit before each attempt
            if time.time() - start_time > MAX_MODAL_CLOSE_TIME:
                logging.warning(
                    "⏰ Modal close timeout - stopping selector attempts")
                break

            try:
                element = WebDriverWait(self.driver, 1).until(  # 1 second max per selector
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f"🎯 Clicked close button: {selector}")
                time.sleep(0.2)  # Reduced from 0.3s
                modal_dismissed = True
                break
            except (TimeoutException, NoSuchElementException, WebDriverException):
                continue

        # EMERGENCY: Click outside modal area if still open (with timeout)
        if not modal_dismissed and time.time() - start_time < MAX_MODAL_CLOSE_TIME:
            try:
                # Click on the page background to close modal
                self.driver.execute_script("document.body.click();")
                logging.info("🖱️ Clicked page background")
                time.sleep(0.2)  # Reduced from 0.3s
                modal_dismissed = True
            except Exception as e:
                logging.debug(f"Background click failed: {e}")

        # Final ESC attempt if nothing worked (and time allows)
        if not modal_dismissed and time.time() - start_time < MAX_MODAL_CLOSE_TIME:
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                ActionChains(self.driver).send_keys(
                    Keys.ESCAPE).perform()  # Double ESC
                logging.info("📤📤 Double ESC sent as final attempt")
                time.sleep(0.3)  # Reduced from 0.5s
                modal_dismissed = True
            except Exception as e:
                logging.debug(f"Final ESC failed: {e}")

        total_time = time.time() - start_time
        logging.info(
            f"✅ Modal closing complete (dismissed: {modal_dismissed}) - took {total_time:.1f}s")

        # ABSOLUTE EMERGENCY: If somehow still over time limit, force return
        if total_time > MAX_MODAL_CLOSE_TIME:
            logging.warning(
                f"⚠️ Modal close exceeded {MAX_MODAL_CLOSE_TIME}s limit - forcing exit")

        return modal_dismissed

    def login_to_instagram(self):
        """Login to Instagram using provided credentials with robust error handling."""
        try:
            logging.info("🔐 Navigating to login page...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)  # Wait for page to load

            if "instagram.com/accounts/login" not in self.driver.current_url:
                logging.info("✅ Already logged in to Instagram")
                return True

            logging.info("Attempting login...")
            username_field_selectors = [(By.NAME, "username"), (By.XPATH, "//input[@name='username']"), (By.XPATH, "//input[@aria-label='Phone number, username, or email']"), (By.XPATH,
                                                                                                                                                                                "//input[@placeholder='Phone number, username, or email']"), (By.XPATH, "//input[contains(@placeholder, 'username')]"), (By.XPATH, "//input[contains(@placeholder, 'email')]"), (By.XPATH, "//form//input[1]")]
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
            username_field.clear()
            username_field.send_keys(self.username)
            logging.info(f"Entered username: {self.username}")
            time.sleep(random.uniform(1, 2))

            password_field_selectors = [(By.NAME, "password"), (By.XPATH, "//input[@name='password']"), (By.XPATH, "//input[@aria-label='Password']"),
                                        (By.XPATH, "//input[@placeholder='Password']"), (By.XPATH, "//input[@type='password']"), (By.XPATH, "//form//input[2]")]
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
            password_field.clear()
            password_field.send_keys(self.password)
            logging.info("Entered password")
            time.sleep(random.uniform(1, 2))

            login_button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//div[contains(text(), 'Log in')]/parent::button"),
                (By.XPATH, "//form//button"),
                (By.XPATH,
                 "//button[contains(@class, '_acan') and contains(@class, '_acap')]"),
                (By.XPATH, "//button[contains(@class, '_acan')]"),
                (By.XPATH,
                 "//div[@role='button'][contains(text(), 'Log in')]"),
                (By.XPATH, "//button[@role='button' and @type='submit']"),
                (By.XPATH,
                 "//button[contains(@class, 'x1i10hfl')][@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "form button"),
                (By.XPATH, "//form/div/button"),
                (By.XPATH, "//form/div/div/button"),
                (By.XPATH, "//button[.//div[contains(text(), 'Log in')]]"),
                (By.XPATH, "//button[normalize-space()='Log in']"),
                (By.XPATH, "//button[normalize-space()='Log In']")
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
                # Debug: Show what buttons are available
                try:
                    all_buttons = self.driver.find_elements(
                        By.TAG_NAME, "button")
                    logging.info(f"Found {len(all_buttons)} buttons on page:")
                    for i, btn in enumerate(all_buttons[:5]):  # Show first 5
                        try:
                            btn_text = btn.text.strip()
                            btn_type = btn.get_attribute("type")
                            btn_class = btn.get_attribute("class")
                            logging.info(
                                f"  Button {i+1}: text='{btn_text}', type='{btn_type}', class='{btn_class[:50]}...'")
                        except:
                            pass
                except:
                    pass

                logging.error(
                    "❌ Could not find login button with any selector")
                return False

            login_successful = False
            try:
                logging.info("Attempting standard click on login button...")
                time.sleep(1)
                login_button.click()
                time.sleep(8)
                if "/accounts/login" not in self.driver.current_url:
                    logging.info("✅ Login successful after standard click.")
                    login_successful = True
                else:
                    logging.warning(
                        "Still on login page after standard click. Trying JS click...")
            except Exception as click_err:
                logging.warning(
                    f"Standard click failed: {click_err}. Trying JS click...")

            if not login_successful:
                try:
                    logging.info(
                        "Attempting JavaScript click on login button...")
                    self.driver.execute_script(
                        "arguments[0].click();", login_button)
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

            if login_successful:
                logging.info("✅ Login successful! Navigating to main feed...")
                # Navigate to main feed instead of handling popups extensively
                self.driver.get("https://www.instagram.com/")
                time.sleep(3)
                # Quick popup dismissal only
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Not Now')]"))
                    ).click()
                    logging.info("Dismissed 'Not Now' popup")
                except:
                    pass  # Ignore if no popup

                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Cancel')]"))
                    ).click()
                    logging.info("Dismissed 'Cancel' popup")
                except:
                    pass  # Ignore if no popup

                return True
            else:
                logging.error("❌ Login failed overall.")
                return False

        except Exception as e:
            logging.error(f"❌ Error during login: {e}")
            return False

    def scrape_users_from_modal(self, link_text, max_scrolls=100):
        """
        Navigates to the current user's profile, clicks on the specified link (Followers/Following),
        and scrapes usernames from the modal that appears.
        """
        users = set()
        logging.info(f"🔍 Attempting to scrape {link_text}...")

        # Navigate to own profile
        profile_url = f"https://www.instagram.com/{self.username}/"
        self.driver.get(profile_url)
        time.sleep(random.uniform(3, 5))

        # Re-attempt popup handling after navigating to profile
        self.handle_post_login_popups()
        time.sleep(random.uniform(1, 2))

        # Click the Followers/Following link
        try:
            # Look for the link by aria-label or href containing the link_text
            link_selector = f"a[href*='/{self.username}/{link_text.lower()}/']"

            # Wait until the element is clickable
            link_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, link_selector))
            )

            count_text = link_element.find_element(By.TAG_NAME, 'span').text
            # Clean count_text to remove commas and non-numeric chars before converting to int
            count = int(''.join(filter(str.isdigit, count_text)))

            logging.info(f"Found {link_text} link with count: {count}")

            try:
                link_element.click()
            except WebDriverException as e:
                logging.warning(
                    f"Direct click failed, attempting JavaScript click: {e}")
                self.driver.execute_script(
                    "arguments[0].click();", link_element)

            time.sleep(random.uniform(3, 5))  # Wait for modal to open

            # Find the scrollable modal
            modal_selector = "//div[@role='dialog']//div[contains(@style, 'overflow-y: scroll') or contains(@style, 'overflow-y: auto')]"
            try:
                scrollable_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, modal_selector))
                )
                logging.info("Found scrollable modal.")
            except TimeoutException:
                logging.warning(
                    "Could not find standard scrollable modal, trying alternative.")
                # Fallback for modal content if main scrollable div not found
                scrollable_element = WebDriverWait(self.driver, 10).until(
                    # Common alternative for follower/following list
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@role='dialog']/div/div[2]"))
                )

            last_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", scrollable_element)

            scroll_attempts = 0
            # Calculate max_scrolls based on the count, assuming ~10 users per scroll
            # Add a buffer for safety
            estimated_scrolls = (count // 10) + 5  # 5 is a buffer
            actual_max_scrolls = min(max_scrolls, estimated_scrolls)
            logging.info(
                f"Estimated scrolls: {estimated_scrolls}, Capped at: {actual_max_scrolls}")

            while len(users) < count and scroll_attempts < actual_max_scrolls:
                # Added alternative selector for username links
                user_elements = scrollable_element.find_elements(
                    By.XPATH, ".//a[contains(@href, '/')] | .//div[@role='button']/div/div/span/a")
                for el in user_elements:
                    href = el.get_attribute('href')
                    # Avoid own profile and post links
                    if href and f"/{self.username}/" not in href and '/p/' not in href and '/explore/' not in href:
                        username = href.strip('/').split('/')[-1]
                        # Avoid Instagram internal links
                        if username and username != "instagram" and username not in ['settings', 'about', 'help', 'privacy', 'terms']:
                            users.add(username)

                logging.info(
                    f"Collected {len(users)}/{count} users so far. Scrolling... (Attempt {scroll_attempts+1}/{actual_max_scrolls})")
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                time.sleep(random.uniform(2, 4))

                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", scrollable_element)
                if new_height == last_height or scroll_attempts >= actual_max_scrolls:  # Check again with updated max_scrolls
                    logging.info(
                        "Reached end of scroll or max scroll attempts.")
                    break
                last_height = new_height
                scroll_attempts += 1

        except TimeoutException:
            logging.error(
                f"❌ Timed out waiting for {link_text} link or modal for {self.username}.")
        except NoSuchElementException:
            logging.error(
                f"❌ Could not find {link_text} link or modal elements for {self.username}.")
        except Exception as e:
            logging.error(
                f"❌ An error occurred while scraping {link_text}: {e}")
        finally:
            try:
                close_button = self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Close']")
                close_button.click()
                time.sleep(1)
            except:
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(
                        webdriver.common.keys.Keys.ESCAPE)
                    time.sleep(1)
                except:
                    pass
        logging.info(
            f"✅ Finished scraping {link_text}. Found {len(users)} users.")
        return list(users)

    def unfollow_user(self, username):
        """OPTIMIZED: Fast unfollow with aggressive timeouts and early bailouts.
           MAX TIME: 30 seconds total per user
        """
        import time
        start_time = time.time()
        MAX_UNFOLLOW_TIME = 30  # 30 second absolute limit per unfollow

        logging.info(f"Attempting to unfollow @{username}...")
        profile_url = f"https://www.instagram.com/{username}/"
        self.driver.get(profile_url)
        time.sleep(random.uniform(1, 2))  # Reduced from 3-5s

        # OPTIMIZED: Minimal page load wait
        time.sleep(1)  # Reduced from 2s

        try:
            # OPTIMIZED: Faster following button detection with reduced timeout
            following_button_selectors = [
                # Most direct selectors first
                "//div[text()='Following']",
                "//button[contains(., 'Following')]",
                "//div[@role='button' and contains(., 'Following')]",
                "//span[contains(text(), 'Following')]/ancestor::button",
                "//span[contains(text(), 'Following')]/ancestor::div[@role='button']",
                # Fallback selectors
                "//div[contains(@class, '_ap3a') and text()='Following']",
                "//button[contains(., 'Following') and @aria-label='Following']"
            ]

            following_button = None
            for selector in following_button_selectors:
                # Check time limit
                if time.time() - start_time > MAX_UNFOLLOW_TIME:
                    logging.warning(
                        f"⏰ Unfollow timeout for @{username} - aborting")
                    return False

                try:
                    following_button = WebDriverWait(self.driver, 3).until(  # Reduced from 20s to 3s
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if following_button:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue

            if not following_button:
                logging.warning(
                    f"⚠️ Could not find 'Following' button for @{username}. Possibly already unfollowed or not following.")
                return False

            # Ready to click Following button
            logging.info(
                f"🎯 Found Following button, clicking to unfollow @{username}...")

            try:
                following_button.click()
                logging.info(f"Clicked 'Following' button for @{username}.")
            except WebDriverException as e:
                logging.warning(
                    f"Direct click on 'Following' button failed, attempting JavaScript click: {e}")
                self.driver.execute_script(
                    "arguments[0].click();", following_button)

            # OPTIMIZED: Reduced wait after clicking Following
            time.sleep(random.uniform(1, 2))  # Reduced from 2.5-4s

            # Check time limit before confirmation
            if time.time() - start_time > MAX_UNFOLLOW_TIME:
                logging.warning(
                    f"⏰ Unfollow timeout after Following click for @{username}")
                return False

            # OPTIMIZED: Faster confirmation button detection
            confirm_unfollow_button_selectors = [
                # Most direct selectors first
                "//span[text()='Unfollow']/ancestor::div[@role='button']",
                "//button[contains(text(), 'Unfollow')]",
                "//div[@role='button' and contains(., 'Unfollow')]",
                "//span[contains(text(), 'Unfollow')]/ancestor::button",
                # Fallback selectors
                "//span[contains(@class, 'x1lliihq') and contains(text(), 'Unfollow')]",
                "//div[@role='dialog']//button[contains(text(), 'Unfollow')]"
            ]

            confirm_button = None
            for selector in confirm_unfollow_button_selectors:
                # Check time limit
                if time.time() - start_time > MAX_UNFOLLOW_TIME:
                    logging.warning(
                        f"⏰ Unfollow timeout during confirmation for @{username}")
                    return False

                try:
                    confirm_button = WebDriverWait(self.driver, 3).until(  # Reduced from 15s to 3s
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if confirm_button:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue

            if not confirm_button:
                logging.warning(
                    f"⚠️ Could not find 'Unfollow' confirmation button for @{username}. Unfollow might have failed or not prompted.")
                return False

            # Ready to click Unfollow confirmation
            logging.info(
                f"🎯 Found Unfollow button, confirming unfollow for @{username}...")

            try:
                confirm_button.click()
                logging.info(f"✅ Successfully unfollowed @{username}.")
                # OPTIMIZED: Reduced wait after unfollow
                time.sleep(random.uniform(1, 2))  # Reduced from 3-5s
                return True
            except WebDriverException as e:
                logging.error(
                    f"❌ Direct click on 'Unfollow' confirmation button failed for @{username}, attempting JavaScript click: {e}")
                self.driver.execute_script(
                    "arguments[0].click();", confirm_button)
                # OPTIMIZED: Reduced wait after JS click
                time.sleep(random.uniform(1, 2))  # Reduced from 3-5s
                logging.info(
                    f"✅ Successfully unfollowed @{username} via JS click.")
                return True

        except Exception as e:
            logging.error(f"❌ Error unfollowing @{username}: {e}")
            return False
        finally:
            # OPTIMIZED: Minimal pause after unfollow attempt
            time.sleep(0.5)  # Reduced from 1s

            total_time = time.time() - start_time
            logging.info(
                f"🕒 Unfollow attempt for @{username} took {total_time:.1f}s")

    def get_users_followed_on_date(self, target_date_str):
        """Fetches users followed on a specific date from the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Get users from processing_queue that were followed on the target date
        # and haven't been checked for follow-back yet AND haven't been sent a DM yet
        cursor.execute("""
            SELECT username, followed_at FROM processing_queue
            WHERE DATE(followed_at) = ?
            AND (follow_back_status IS NULL OR follow_back_status = 'pending')
            AND (dm_status IS NULL OR dm_status != 'sent')
            ORDER BY followed_at ASC
        """, (target_date_str,))
        users = cursor.fetchall()
        conn.close()
        # Return as a set for efficient lookup
        return {user[0] for user in users}

    def get_all_unchecked_users(self, days_back=7, limit=150):
        """Fetches ALL users who haven't been checked for follow-back yet from the last N days, excluding today's follows."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Get all users from processing_queue that haven't been checked for follow-back yet
        # AND haven't been sent a DM yet, limited to last N days to avoid very old follows
        # EXCLUDE today's follows to give people time to follow back
        # LIMIT to specified number for controlled processing
        cursor.execute("""
            SELECT username, followed_at FROM processing_queue
            WHERE (follow_back_status IS NULL OR follow_back_status = 'pending')
            AND (dm_status IS NULL OR dm_status != 'sent')
            AND followed_at >= DATE('now', '-' || ? || ' days')
            AND followed_at < DATE('now', 'start of day')
            ORDER BY followed_at ASC
            LIMIT ?
        """, (days_back, limit))
        users = cursor.fetchall()
        conn.close()
        # Return as a dictionary with username and followed_at info
        return {user[0]: user[1] for user in users}

    def update_follow_back_status(self, username, status, checked_at):
        """Updates the follow_back_status and follow_back_checked_at for a user."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE processing_queue
            SET follow_back_status = ?, follow_back_checked_at = ?
            WHERE username = ?
        """, (status, checked_at, username))
        conn.commit()
        conn.close()

    def update_follow_status(self, username, status):
        """Updates the follow_status for a user."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE processing_queue
            SET follow_status = ?
            WHERE username = ?
        """, (status, username))
        conn.commit()
        conn.close()

    def update_dm_status(self, username, dm_message, dm_status):
        """Update the DM status for a user in the database."""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE processing_queue SET dm_message = ?, dm_status = ? WHERE username = ?",
                (dm_message, dm_status, username)
            )
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error updating DM status for {username}: {e}")
        finally:
            if conn:
                conn.close()

    def analyze_user_profile(self, username):
        """
        OPTIMIZED: Analyze a user's Instagram profile for bio information with timeout protection.
        This runs after we confirm they followed back but before sending DM.
        Returns True if analysis was successful or already exists, False otherwise.
        MAX TIME: 180 seconds (3 minutes) per user
        """
        import time
        start_time = time.time()
        # 2 minute absolute limit per analysis (reduced to prevent DM timeouts)
        MAX_ANALYSIS_TIME = 120

        try:
            logging.info(f"🔍 Checking bio analysis status for @{username}...")

            # Check if analysis functions are available (imports succeeded)
            if not hasattr(has_complete_instagram_analysis_sqlite, '__call__'):
                logging.warning(
                    f"⚠️ Bio analysis functions not available, skipping analysis for @{username}")
                return False

            # Check if user already has complete Instagram analysis
            if has_complete_instagram_analysis_sqlite(username):
                logging.info(
                    f"✅ @{username} already has complete bio analysis, skipping")
                return True

            # Check timeout before starting analysis
            if time.time() - start_time > MAX_ANALYSIS_TIME:
                logging.warning(
                    f"⏰ Analysis timeout for @{username} - aborting before start")
                return False

            logging.info(f"🚀 Starting bio analysis for @{username}...")

            # Run the Instagram profile analysis using the same driver session
            # This is where the long delay was happening - add our own timeout wrapper
            try:
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("Bio analysis exceeded time limit")

                # Set alarm for timeout (only on Unix-like systems)
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(MAX_ANALYSIS_TIME -
                                 int(time.time() - start_time))

                analysis_result = analyze_profile(self.driver, username)

                # Cancel alarm if we finish early
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)

            except TimeoutError:
                logging.warning(
                    f"⏰ Bio analysis timeout for @{username} after {MAX_ANALYSIS_TIME}s")
                return False
            except Exception as analysis_error:
                # Cancel alarm on error too
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                raise analysis_error

            total_time = time.time() - start_time
            if analysis_result:
                logging.info(
                    f"✅ Successfully analyzed profile for @{username} (took {total_time:.1f}s)")
                return True
            else:
                logging.warning(
                    f"⚠️ Bio analysis failed for @{username} (private profile or error, took {total_time:.1f}s)")
                return False

        except Exception as e:
            total_time = time.time() - start_time
            logging.error(
                f"❌ Error during bio analysis for @{username}: {e} (took {total_time:.1f}s)")
            return False

    def tag_user_for_direct_approach(self, username):
        """Tag a user for the direct approach flow in the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.now().isoformat()
            cursor.execute("""
                UPDATE processing_queue
                SET direct_approach_tagged = ?, direct_approach_tagged_at = ?
                WHERE username = ?
            """, (True, current_time, username))
            conn.commit()
            logging.info(f"🏷️ Tagged @{username} for direct approach flow")
            return True
        except Exception as e:
            logging.error(
                f"❌ Error tagging @{username} for direct approach: {e}")
            return False
        finally:
            conn.close()

    def is_user_tagged_for_direct_approach(self, username):
        """Check if a user is already tagged for direct approach."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT direct_approach_tagged FROM processing_queue
                WHERE username = ?
            """, (username,))
            result = cursor.fetchone()
            return result[0] if result else False
        except Exception as e:
            logging.error(
                f"❌ Error checking direct approach tag for @{username}: {e}")
            return False
        finally:
            conn.close()

    def generate_direct_approach_message(self, username, conversation_history=None):
        """Generate the opening message for the direct approach flow."""
        try:
            # Import the direct approach prompt template
            from app.prompts import DIRECT_APPROACH_PROMPT_TEMPLATE

            # Get current Melbourne time
            from datetime import datetime
            import pytz
            melbourne_tz = pytz.timezone('Australia/Melbourne')
            current_melbourne_time = datetime.now(melbourne_tz)
            current_melbourne_time_str = current_melbourne_time.strftime(
                '%Y-%m-%d %H:%M:%S')

            # Get profile insights (if available)
            profile_insights = self.get_profile_insights(username)

            # Format conversation history
            conversation_text = ""
            if conversation_history:
                for msg in conversation_history:
                    sender = 'User' if msg.get('type') == 'user' else 'Shannon'
                    text = msg.get('text', '')
                    conversation_text += f"{sender}: {text}\n"

            # Create the prompt with all required fields
            prompt = DIRECT_APPROACH_PROMPT_TEMPLATE.format(
                conversation_history=conversation_text,
                profile_insights=profile_insights,
                response_guidelines="Keep responses short and conversational. Use Shannon's casual Australian tone.",
                extra_information_on_shannon="Shannon is a 32-year-old Australian fitness coach who runs Coco's Connected online coaching.",
                current_melbourne_time_str=current_melbourne_time_str
            )

            # Try each Gemini model until one works
            for model_name, model in gemini_models:
                try:
                    response = model.generate_content(prompt)
                    if response and response.text:
                        message = response.text.strip()
                        # Remove quotes if the AI wrapped the message in them
                        if message.startswith('"') and message.endswith('"'):
                            message = message[1:-1]
                        if message.startswith("'") and message.endswith("'"):
                            message = message[1:-1]
                        logging.info(
                            f"Generated direct approach message using {model_name}: {message}")
                        return message
                except Exception as e:
                    logging.warning(f"Model {model_name} failed: {e}")
                    continue

            # Fallback message
            fallback_message = "Hey! How long have you been vegan for?"
            logging.warning(
                "All Gemini models failed, using fallback direct approach message")
            return fallback_message

        except Exception as e:
            logging.error(f"Error generating direct approach message: {e}")
            return "Hey! How long have you been vegan for?"

    def get_profile_insights(self, username):
        """Get profile insights for the user (placeholder for now)."""
        # This would integrate with your existing profile analysis system
        # For now, return a basic structure
        return f"User: @{username}\nInterests: Vegan/plant-based lifestyle\nFitness: Unknown\n"

    def generate_dm_message(self, username, account_mode):
        """Generate a personalized DM message using Gemini AI."""
        try:
            # Check if user is tagged for direct approach
            if self.is_user_tagged_for_direct_approach(username):
                logging.info(f"🎯 Using direct approach for @{username}")
                return self.generate_direct_approach_message(username)

            # Otherwise use the existing DM generation logic
            if account_mode == 'local':
                prompt = f"""
You are Shannon, a 32-year-old casual Australian fitness coach who runs Coco's PT studio in Hampton, Melbourne. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these EXACT examples:

SHANNON'S ACTUAL STYLE EXAMPLES:
- "Heya! appreciate the follow! i saw that you were local to bayside? Been Around here for long?"
- "Hey! Thanks for the follow back! Noticed you're around Bayside too?"
- "Heya! Cheers for following back! Saw you're local to the area?"

SHANNON'S VOICE:
- Very casual and conversational
- Uses "Heya!" or "Hey!" to start
- Says "appreciate the follow" or "thanks for the follow back"
- Mentions what he "saw" or "noticed" about them
- References being "local to bayside" or "around the area"
- Asks simple follow-up questions like "Been around here for long?"
- Uses lowercase for casual words like "i" instead of "I"
- Australian but not overly so

TARGET AUDIENCE: Bayside Melbourne mums and locals

CRITICAL RULES:
- Must be 8-15 words total
- Reference that they're "local to bayside" or "around the area"
- Ask a simple question like "Been around here for long?" or "How long you been in the area?"
- Sound natural and conversational, not scripted
- Use Shannon's exact casual language patterns

Generate ONE casual DM message exactly like Shannon's style:
"""
            else:  # online mode
                prompt = f"""
You are Shannon, a casual Australian fitness coach who runs Coco's Connected online coaching. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these EXACT examples:

SHANNON'S ACTUAL STYLE EXAMPLES:
- "Heya! Appreciate the follow! Saw your Plant Based? Awesome! How long for?"
- "Hey! Thanks for the follow back! Noticed you're vegan too? How long?"
- "Heya! Cheers for following back! Saw you're plant based, awesome!"

SHANNON'S VOICE:
- Very casual and conversational
- Uses "Heya!" or "Hey!" to start
- Says "appreciate the follow" or "thanks for the follow back"
- Mentions what he "saw" or "noticed" about them
- References being "plant based" or "vegan"
- Shows enthusiasm with "Awesome!" or "Nice!"
- Asks simple questions like "How long for?" or "How long?"
- Uses lowercase casually

TARGET AUDIENCE: Vegan/plant-based people interested in fitness

CRITICAL RULES:
- Must be 8-15 words total
- Reference that they're "plant based" or "vegan"
- Ask a simple question like "How long for?" or "How long you been at it?"
- Sound natural and conversational, not scripted
- Use Shannon's exact casual language patterns
- Show enthusiasm but keep it chill

Generate ONE casual DM message exactly like Shannon's style:
"""

            # Try each Gemini model until one works
            for model_name, model in gemini_models:
                try:
                    response = model.generate_content(prompt)
                    if response and response.text:
                        # Clean up the response
                        message = response.text.strip()
                        # Remove quotes if the AI wrapped the message in them
                        if message.startswith('"') and message.endswith('"'):
                            message = message[1:-1]
                        if message.startswith("'") and message.endswith("'"):
                            message = message[1:-1]
                        logging.info(
                            f"Generated DM using {model_name}: {message}")
                        return message
                except Exception as e:
                    logging.warning(f"Model {model_name} failed: {e}")
                    continue

            # Fallback message if AI fails
            fallback_messages = {
                'local': "Heya! appreciate the follow! i saw you were local to bayside?",
                'online': "Heya! Appreciate the follow! Saw your Plant Based? Awesome!"
            }
            logging.warning("All Gemini models failed, using fallback message")
            return fallback_messages.get(account_mode, "Heya! Thanks for the follow back!")

        except Exception as e:
            logging.error(f"Error generating DM message: {e}")
            return "Hey! Thanks for the follow back!"

    def send_dm_to_user(self, username, message):
        """Send a DM to a user using direct DM URL approach."""
        max_retries = 2
        MAX_DM_TIME = 180

        for retry_attempt in range(max_retries):
            try:
                start_time = time.time()
                logging.info(
                    f"💬 Sending DM to @{username} (attempt {retry_attempt + 1}/{max_retries})")

                # Quick driver health check
                try:
                    current_url = self.driver.current_url
                    logging.debug(f"Current URL before DM: {current_url}")
                except Exception as driver_error:
                    logging.error(
                        f"❌ Driver appears unresponsive: {driver_error}")
                    return False

                # Navigate to profile and use traditional method (direct DM URL no longer works)
                profile_url = f"https://www.instagram.com/{username}/"
                try:
                    self.driver.get(profile_url)
                    time.sleep(random.uniform(3, 5))
                    logging.info(f"✅ Navigated to profile: {profile_url}")

                    # Wait for page to load and check if it's actually loaded
                    page_load_timeout = 30
                    start_page_load = time.time()

                    while time.time() - start_page_load < page_load_timeout:
                        try:
                            # Check if page has loaded by looking for any Instagram content
                            page_source = self.driver.page_source
                            if "instagram" in page_source.lower() and len(page_source) > 1000:
                                logging.info(
                                    "✅ Page appears to have loaded properly")
                                break
                            elif time.time() - start_page_load > 10:
                                logging.warning(
                                    "⚠️ Page taking longer than expected to load, continuing anyway")
                                break
                            else:
                                time.sleep(1)
                        except Exception as e:
                            logging.debug(f"Error checking page load: {e}")
                            time.sleep(1)

                    # Additional wait for Instagram to fully render
                    time.sleep(random.uniform(5, 8))

                except Exception as nav_error:
                    logging.error(
                        f"❌ Navigation error for @{username}: {nav_error}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Close any existing modals
                for cleanup_attempt in range(3):
                    if time.time() - start_time > MAX_DM_TIME:
                        break
                    try:
                        self.close_any_modal()
                        time.sleep(1)
                    except Exception:
                        pass

                # Try to find Message button
                message_button_selectors = [
                    # Working selector from debug test
                    "//div[contains(text(), 'Message')][@role='button']",
                    # Fallback selectors
                    "//button[contains(text(), 'Message')]",
                    "//span[contains(text(), 'Message')]/ancestor::div[@role='button']",
                    "//svg[@aria-label='Direct messages']/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(@class, 'x1i10hfl')]//span[text()='Messages']/..",
                    "//div[@role='button' and contains(@class, 'x1i10hfl')]//svg[@aria-label='Direct messages']/.."
                ]

                message_button = None
                for selector in message_button_selectors:
                        try:
                            message_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            if message_button and message_button.is_displayed():
                                logging.info(
                                    f"✅ Found Message button using selector: {selector}")
                                break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if message_button:
                    try:
                            message_button.click()
                        time.sleep(random.uniform(3, 5))
                        logging.info("✅ Clicked Message button")
                    except Exception as click_error:
                        logging.error(
                            f"❌ Error clicking Message button: {click_error}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False
                else:
                    logging.error(
                        f"❌ Could not find Message button for @{username}")
                        if retry_attempt < max_retries - 1:
                            continue
                        return False

                # Find message input with multiple selectors
                message_input = None
                input_selectors = [
                    # Working selector from debug test
                    "//div[@contenteditable='true'][@role='textbox']",
                    # Fallback selectors
                    "//textarea[@placeholder='Message...']",
                    "//div[contains(@aria-label, 'Message')][@contenteditable='true']",
                    "//div[@contenteditable='true']",
                    "//textarea[contains(@placeholder, 'Message')]",
                    "//div[@role='textbox'][@contenteditable='true']"
                ]

                for selector in input_selectors:
                    try:
                        message_input = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.XPATH, selector))
                                )
                        if message_input and message_input.is_displayed():
                                    logging.info(
                                f"✅ Found message input using selector: {selector}")
                                    break
                    except (TimeoutException, NoSuchElementException):
                                continue

                if not message_input:
                    logging.error(
                        f"❌ Could not find message input for @{username}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Send message
                try:
                    # Clear any existing text
                                message_input.clear()
                            time.sleep(1)

                    # Type the message
                    message_input.send_keys(message)
                        time.sleep(1)

                    # Send the message using Enter key
                    message_input.send_keys(Keys.RETURN)
                    time.sleep(2)

                    logging.info(f"✅ Message sent to @{username}: '{message}'")
                    return True

                except Exception as send_error:
                    logging.error(
                        f"❌ Error sending message to @{username}: {send_error}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

            except Exception as e:
                logging.error(
                    f"❌ Unexpected error sending DM to @{username}: {e}")
                if retry_attempt < max_retries - 1:
                    continue
                return False

        logging.error(f"❌ All retry attempts failed for @{username}")
        return False

    def run_analysis(self, target_date_str=None):
        logging.info("🚀 Starting Follow-Back Analysis...")

        # Initialize fresh lead database schema
        self.ensure_fresh_lead_column()
        self.ensure_direct_approach_columns()

        self.setup_driver()

        # Choose analysis method based on whether a specific date was provided
        if target_date_str:
            # Legacy mode: check only specific date
            check_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            check_date_str = check_date.strftime('%Y-%m-%d')
            logging.info(
                f"📊 LEGACY MODE: Analyzing follow-backs for users followed on specific date: {check_date_str}")

            # Get users from specific date
            users_to_check_dict = {}
            users_from_date = self.get_users_followed_on_date(check_date_str)
            for username in users_from_date:
                # Use the specific date
                users_to_check_dict[username] = check_date_str

            analysis_mode = f"specific_date_{check_date_str}"
        else:
            # New comprehensive mode: check ALL unchecked users from last 7 days (excluding today)
            logging.info(
                f"📊 COMPREHENSIVE MODE: Analyzing ALL unchecked follow-backs from the last 7 days (excluding today's follows)...")

            # Get all unchecked users
            users_to_check_dict = self.get_all_unchecked_users(days_back=7)
            analysis_mode = "comprehensive_all_unchecked"

        logging.info(
            f"Found {len(users_to_check_dict)} users to check for follow-back status.")

        if not users_to_check_dict:
            if target_date_str:
                logging.info(
                    f"📭 No users were followed on {check_date_str} or all have been checked. Nothing to analyze.")
            else:
                logging.info(
                    f"📭 No unchecked users found in the last 7 days (excluding today). All recent follows have been processed or need more time!")

            self._log_follow_run(
                'completed', users_followed=0, error_message="No users to analyze")
            return

        try:
            if not self.login_to_instagram():
                logging.error("❌ Failed to login. Stopping follow session.")
                self._log_follow_run(
                    'failed', error_message="Failed to login to Instagram")
                return

            # Quick popup check only - don't spend too much time on this
            logging.info("📋 Checking for any remaining popups...")
            try:
                # Quick check for common popups - max 5 seconds total
                WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Not Now')]"))
                ).click()
                logging.info("Dismissed additional 'Not Now' popup")
            except:
                pass

            time.sleep(1)  # Short pause before proceeding to user checking

            followed_back_count = 0
            followed_back_list = []
            not_followed_back_list = []
            unfollowed_count = 0
            dms_sent_count = 0
            checked_at = datetime.now().isoformat()

            # Determine account mode for DM generation
            account_mode = 'local' if self.username == 'cocos_pt_studio' else 'online'

            # Process all users to check (could be from specific date or all unchecked)
            for username_followed in users_to_check_dict.keys():
                # FIXED: Reasonable timeout per user (10 minutes max)
                user_start_time = time.time()
                # 10 minutes absolute limit per user (increased from 5 minutes)
                MAX_USER_PROCESSING_TIME = 600

                logging.info(
                    f"🔄 Processing @{username_followed} for follow-back status...")

                # Check driver health before processing each user
                if not self.restart_driver_if_needed():
                    logging.error(
                        f"❌ Driver restart failed, skipping @{username_followed}")
                    continue

                try:
                    # Perform the new per-user follow-back check with error handling
                    follow_back_result = None
                    try:
                        # Check timeout before follow-back check
                        if time.time() - user_start_time > MAX_USER_PROCESSING_TIME:
                            logging.warning(
                                f"⏰ User processing timeout for @{username_followed} - skipping")
                            continue

                        follow_back_result = self.check_if_following_me_back(
                            username_followed)
                    except Exception as modal_error:
                        logging.error(
                            f"❌ Error checking @{username_followed}'s followers: {modal_error}")
                        # Try driver restart for critical errors
                        if "chrome" in str(modal_error).lower() or "webdriver" in str(modal_error).lower():
                            logging.warning(
                                f"🔄 Attempting driver restart due to WebDriver error...")
                            if not self.restart_driver_if_needed():
                                logging.error(
                                    f"❌ Driver restart failed after WebDriver error")
                                continue
                        # Skip this user and continue with the next one
                        logging.info(
                            f"⏭️ Skipping @{username_followed} due to check error, will try again later")
                        continue

                    if follow_back_result:
                        followed_back_count += 1
                        followed_back_list.append(username_followed)
                        self.update_follow_back_status(
                            username_followed, 'yes', checked_at)
                        logging.info(
                            f"✅ @{username_followed} followed back. Status updated.")

                        # 🎯 NEW: Mark user as fresh lead for A/B testing
                        self.mark_user_as_fresh_lead(username_followed)

                        # 🏷️ NEW: Tag user for direct approach flow
                        self.tag_user_for_direct_approach(username_followed)

                        # Generate and send DM to user who followed back FIRST (prioritize DM over bio analysis)
                        try:
                            # Check timeout before DM - allow more time for DM since it's critical
                            dm_timeout_limit = MAX_USER_PROCESSING_TIME + 300  # Extra 5 minutes for DM
                            if time.time() - user_start_time > dm_timeout_limit:
                                logging.warning(
                                    f"⏰ Skipping DM for @{username_followed} - extended timeout limit reached")
                                self.update_dm_status(
                                    username_followed, "", 'failed_timeout')
                                continue

                            # Check driver health before DM attempt
                            if not self.restart_driver_if_needed():
                                logging.error(
                                    f"❌ Driver unhealthy before DM to @{username_followed}, skipping DM")
                                self.update_dm_status(
                                    username_followed, "", 'failed_driver_error')
                                continue

                            logging.info(
                                f"💬 Generating DM for @{username_followed}...")
                            dm_message = self.generate_dm_message(
                                username_followed, account_mode)

                            if self.send_dm_to_user(username_followed, dm_message):
                                # 📝 NEW: Store DM in conversation history for AI context
                                self.store_dm_in_conversation_history(
                                    username_followed, dm_message)

                                self.update_dm_status(
                                    username_followed, dm_message, 'sent')
                                dms_sent_count += 1
                                logging.info(
                                    f"✅ DM sent successfully to @{username_followed}")

                                # NOW do bio analysis AFTER successful DM (lower priority)
                                if self.analyze_profiles:
                                    # Check timeout before bio analysis with shorter limit
                                    if time.time() - user_start_time < MAX_USER_PROCESSING_TIME + 600:  # Extra 10 minutes for bio
                                        logging.info(
                                            f"🔍 Starting bio analysis for @{username_followed} after successful DM...")
                                        bio_analysis_success = self.analyze_user_profile(
                                            username_followed)
                                        if bio_analysis_success:
                                            logging.info(
                                                f"📊 Bio analysis completed for @{username_followed}")
                                        else:
                                            logging.warning(
                                                f"⚠️ Bio analysis failed for @{username_followed}, but DM was sent successfully")
                                    else:
                                        logging.warning(
                                            f"⏰ Skipping bio analysis for @{username_followed} - DM sent but no time for bio analysis")
                                else:
                                    logging.info(
                                        f"⏭️ Bio analysis disabled for @{username_followed}")

                                # OPTIMIZED: Reduced delay between DMs
                                # Reduced from 45-75s
                                delay = random.uniform(30, 45)
                                logging.info(
                                    f"⏳ Waiting {delay:.1f}s before next action...")
                                time.sleep(delay)
                            else:
                                self.update_dm_status(
                                    username_followed, dm_message, 'failed')
                                logging.warning(
                                    f"❌ Failed to send DM to @{username_followed}")

                                # Still do bio analysis even if DM failed (data collection)
                                if self.analyze_profiles:
                                    if time.time() - user_start_time < MAX_USER_PROCESSING_TIME + 300:  # Extra 5 minutes
                                        logging.info(
                                            f"🔍 Doing bio analysis for @{username_followed} despite DM failure...")
                                        bio_analysis_success = self.analyze_user_profile(
                                            username_followed)
                                        if bio_analysis_success:
                                            logging.info(
                                                f"📊 Bio analysis completed for @{username_followed}")
                                    else:
                                        logging.warning(
                                            f"⏰ No time for bio analysis for @{username_followed}")
                        except Exception as dm_error:
                            logging.error(
                                f"❌ Error processing DM for @{username_followed}: {dm_error}")
                            # Check if it's a driver crash
                            if "chrome" in str(dm_error).lower() or "webdriver" in str(dm_error).lower():
                                logging.warning(
                                    f"🔄 DM error appears to be driver-related, attempting restart...")
                                if self.restart_driver_if_needed():
                                    logging.info(
                                        f"✅ Driver restarted successfully after DM error")
                                else:
                                    logging.error(
                                        f"❌ Driver restart failed after DM error")
                                self.update_dm_status(
                                    username_followed, "", 'failed_driver_crash')
                            else:
                                self.update_dm_status(
                                    username_followed, "", 'failed')

                    else:
                        not_followed_back_list.append(username_followed)
                        logging.info(
                            f"❌ @{username_followed} has NOT followed back.")

                        if unfollowed_count < self.daily_unfollow_limit:
                            try:
                                # Check timeout before unfollow
                                if time.time() - user_start_time > MAX_USER_PROCESSING_TIME:
                                    logging.warning(
                                        f"⏰ Skipping unfollow for @{username_followed} - timeout limit reached")
                                    self.update_follow_back_status(
                                        username_followed, 'no_timeout', checked_at)
                                    continue

                                if self.unfollow_user(username_followed):
                                    self.update_follow_back_status(
                                        username_followed, 'no', checked_at)
                                    # Update follow_status in new_leads
                                    self.update_follow_status(
                                        username_followed, 'unfollowed_by_us')
                                    unfollowed_count += 1
                                    logging.info(
                                        f"➡ Unfollowed @{username_followed}. Unfollows today: {unfollowed_count}/{self.daily_unfollow_limit}")
                                else:
                                    self.update_follow_back_status(
                                        username_followed, 'no_unfollow_failed', checked_at)
                                    logging.warning(
                                        f"⚠️ Failed to unfollow @{username_followed}. Status updated to 'no_unfollow_failed'.")
                            except Exception as unfollow_error:
                                logging.error(
                                    f"❌ Error unfollowing @{username_followed}: {unfollow_error}")
                                self.update_follow_back_status(
                                    username_followed, 'no_unfollow_failed', checked_at)
                        else:
                            self.update_follow_back_status(
                                username_followed, 'no_unfollow_limit_reached', checked_at)
                            logging.warning(
                                f"⚠️ Skipped unfollowing @{username_followed} due to daily limit. Status updated to 'no_unfollow_limit_reached'.")

                except Exception as user_error:
                    logging.error(
                        f"❌ Critical error processing @{username_followed}: {user_error}")
                    # Continue with next user instead of crashing
                    continue

                # OPTIMIZED: Log processing time and add shorter delay between users
                user_total_time = time.time() - user_start_time
                logging.info(
                    f"🕒 Processing @{username_followed} took {user_total_time:.1f}s")

                # Shorter delay between users
                time.sleep(random.uniform(3, 6))  # Reduced from 5-10s

            total_users_checked = len(users_to_check_dict)
            follow_back_percentage = 0
            if total_users_checked > 0:
                follow_back_percentage = (
                    followed_back_count / total_users_checked) * 100

            # Generate appropriate report based on analysis mode
            if target_date_str:
                # Legacy mode report
                logging.info("\n--- Follow-Back Report (Specific Date) ---")
                logging.info(f"Analysis Date: {check_date_str}")
                logging.info(
                    f"Total Users Checked from {check_date_str}: {total_users_checked}")
                analysis_description = f"Specific date: {check_date_str}"
            else:
                # Comprehensive mode report
                logging.info("\n--- Follow-Back Report (Comprehensive) ---")
                if users_to_check_dict:
                    # Get date range from the users
                    follow_dates = list(users_to_check_dict.values())
                    earliest_date = min(follow_dates)
                    latest_date = max(follow_dates)
                    logging.info(
                        f"Date Range Processed: {earliest_date} to {latest_date}")
                logging.info(
                    f"Total Unchecked Users Processed: {total_users_checked}")
                analysis_description = f"Comprehensive (last 7 days)"

            logging.info(f"Users Who Followed Back: {followed_back_count}")
            logging.info(
                f"Users Marked as Fresh Leads: {followed_back_count}")
            logging.info(f"Users Unfollowed This Session: {unfollowed_count}")
            logging.info(f"DMs Sent This Session: {dms_sent_count}")
            logging.info(
                f"DMs Stored in Conversation History: {dms_sent_count if CONVERSATION_HISTORY_AVAILABLE else 0}")
            logging.info(
                f"Follow-back Percentage: {follow_back_percentage:.2f}%")

            # Save results to JSON file for dashboard display
            self._save_results_to_file({
                'timestamp': datetime.now().isoformat(),
                'analysis_date': check_date_str if target_date_str else 'comprehensive',
                'analysis_mode': analysis_mode,
                'analysis_description': analysis_description,
                'account_mode': 'local' if self.username == 'cocos_pt_studio' else 'online',
                'account_username': self.username,
                'total_followed_on_date': total_users_checked,  # Renamed for clarity
                'followed_back_count': followed_back_count,
                'unfollowed_count': unfollowed_count,
                'dms_sent_count': dms_sent_count,
                'follow_back_percentage': follow_back_percentage,
                'status': 'completed',
                'followed_back_usernames': followed_back_list,
                'unfollowed_usernames': [user for user in not_followed_back_list
                                       if self.get_user_follow_status(user) == 'unfollowed_by_us']
            })

            if followed_back_count > 0:
                logging.info("\nUsers Who Followed Back (and received DMs):")
                for i, user in enumerate(sorted(followed_back_list)):
                    logging.info(f"- @{user} ✅ (Fresh Lead for A/B Testing)")
            else:
                if target_date_str:
                    logging.info(
                        f"\nNo users followed back from {check_date_str}.")
                else:
                    logging.info(
                        "\nNo users followed back from this session's processed users.")

            if unfollowed_count > 0:
                logging.info("\nUsers Unfollowed This Session:")
                for i, user in enumerate(sorted(not_followed_back_list)):
                    if self.get_user_follow_status(user) == 'unfollowed_by_us':
                        logging.info(f"- @{user}")
            else:
                logging.info("\nNo users were unfollowed this session.")

        except Exception as e:
            logging.critical(
                f"A critical error occurred during daily follow-back analysis: {e}")
        finally:
            self.teardown_driver()

    def get_user_follow_status(self, username):
        """Helper to get current follow_status from database."""
        conn = None  # Initialize conn outside try block
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT follow_status FROM processing_queue WHERE username = ?", (username,))
            status = cursor.fetchone()
            return status[0] if status else None
        finally:
            if conn:
                conn.close()

    def _log_follow_run(self, status, users_followed=0, error_message=None):
        """Log the follow run results to database (placeholder method)."""
        # This method can be implemented later to track follow session statistics
        logging.info(
            f"Follow run completed with status: {status}, users_followed: {users_followed}")
        if error_message:
            logging.info(f"Error message: {error_message}")

    def _save_results_to_file(self, results):
        """Save follow-back analysis results to JSON file for dashboard display."""
        try:
            import json
            results_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\followback_results.json"

            # Load existing results if file exists
            existing_results = []
            if os.path.exists(results_file):
                try:
                    with open(results_file, 'r') as f:
                        existing_results = json.load(f)
                except json.JSONDecodeError:
                    logging.warning(
                        "Could not parse existing results file, starting fresh")
                    existing_results = []

            # Add new result to the beginning of the list
            existing_results.insert(0, results)

            # Keep only the last 10 results to prevent file from growing too large
            existing_results = existing_results[:10]

            # Save back to file
            with open(results_file, 'w') as f:
                json.dump(existing_results, f, indent=2)

            logging.info(f"Results saved to {results_file}")

        except Exception as e:
            logging.error(
                f"Failed to save results to file: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check daily Instagram follow-back rates.')
    parser.add_argument(
        '--date', type=str, help='Date to check follow-backs for (YYYY-MM-DD). Defaults to yesterday.')
    parser.add_argument(
        '--account', type=str, choices=['local', 'online'], default='online',
        help='Account mode: "local" for @cocos_pt_studio, "online" for @cocos_connected')
    parser.add_argument(
        '--analyze-profiles', action='store_true', default=True,
        help='Analyze Instagram profiles for bio information before sending DMs (default: True)')
    parser.add_argument(
        '--no-analyze-profiles', action='store_true',
        help='Skip profile analysis and send DMs without bio analysis')
    args = parser.parse_args()

    # Set credentials based on account mode
    if args.account == 'local':
        username = "cocos_pt_studio"
        print(f"🏠 LOCAL MODE: Checking follow-backs for @{username}")
    else:
        username = "cocos_connected"
        print(f"🌱 ONLINE MODE: Checking follow-backs for @{username}")

    # Determine if profile analysis should be enabled
    analyze_profiles = args.analyze_profiles and not args.no_analyze_profiles
    if analyze_profiles:
        print(f"🔍 PROFILE ANALYSIS: ENABLED - Will analyze bio information for users who follow back")
    else:
        print(f"⏭️ PROFILE ANALYSIS: DISABLED - Will skip bio analysis and send DMs immediately")

    checker = DailyFollowBackChecker(
        username=username, analyze_profiles=analyze_profiles)
    checker.run_analysis(args.date)
