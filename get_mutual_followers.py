import time
import random
import sqlite3
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mutual_followers.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class MutualFollowerAnalyzer:
    def __init__(self, username="cocos_pt_studio", password="Shannonb3"):
        self.username = username
        self.password = password
        self.driver = None

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
            "--user-data-dir=C:/Users/Shannon/AppData/Local/Google/Chrome/User Data Automation"
        )
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info("Chrome driver initialized with stealth settings.")

    def handle_post_login_popups(self):
        """Handle the various popups that might appear after login"""
        try:
            popups = [
                {"name": "Save Login Info", "selectors": [
                    "//button[contains(text(), 'Not Now')]", "//button[contains(text(), 'Save Info')]", "//button[contains(text(), 'Not now')]", "//button[contains(@class, 'HoLwm')]"]},
                {"name": "Notifications", "selectors": ["//button[contains(text(), 'Not Now')]", "//button[contains(text(), 'Not now')]",
                                                        "//button[contains(text(), 'Turn on Notifications')]", "//button[contains(@class, '_a9--')]"]},
                {"name": "Add to Home Screen", "selectors": [
                    "//button[contains(text(), 'Cancel')]", "//button[contains(text(), 'Not Now')]"]}
            ]
            for popup in popups:
                for selector in popup["selectors"]:
                    try:
                        element = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector)))
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

            login_button_selectors = [(By.XPATH, "//button[@type='submit']"), (By.XPATH, "//button[contains(text(), 'Log in')]"), (By.XPATH,
                                                                                                                                   "//div[contains(text(), 'Log in')]/parent::button"), (By.XPATH, "//button[contains(text(), 'Log In')]"), (By.XPATH, "//form//button")]
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
                self.handle_post_login_popups()
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

        # Click the Followers/Following link
        try:
            # Look for the link by aria-label or href containing the link_text
            link_selector = f"a[href*='/{self.username}/{link_text.lower()}/']"
            link_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, link_selector))
            )
            count = int(link_element.find_element(
                By.TAG_NAME, 'span').text.replace(',', ''))
            logging.info(f"Found {link_text} link with count: {count}")
            link_element.click()
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
            while True:
                user_elements = scrollable_element.find_elements(
                    By.XPATH, ".//a[contains(@href, '/')]")
                for el in user_elements:
                    href = el.get_attribute('href')
                    # Avoid own profile and post links
                    if href and f"/{self.username}/" not in href and '/p/' not in href and '/explore/' not in href:
                        username = href.strip('/').split('/')[-1]
                        if username and username != "instagram":  # Avoid Instagram official account
                            users.add(username)

                logging.info(
                    f"Collected {len(users)} users so far. Scrolling...")
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
                time.sleep(random.uniform(2, 4))

                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", scrollable_element)
                if new_height == last_height or scroll_attempts >= max_scrolls:
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
            # Try to close the modal by pressing ESC or clicking a close button
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

    def run_analysis(self):
        logging.info("🚀 Starting Mutual Follower Analysis...")
        self.setup_driver()

        try:
            if not self.login_to_instagram():
                logging.error("❌ Failed to login to Instagram. Exiting.")
                return

            following_list = self.scrape_users_from_modal("Following")
            followers_list = self.scrape_users_from_modal("Followers")

            following_set = set(following_list)
            followers_set = set(followers_list)

            mutual_followers = following_set.intersection(followers_set)

            # Filter out own username if it somehow appears
            if self.username in mutual_followers:
                mutual_followers.remove(self.username)

            total_followed_by_us = len(following_set)
            total_followers = len(followers_set)
            num_mutual_followers = len(mutual_followers)

            follow_back_percentage = 0
            if total_followed_by_us > 0:
                follow_back_percentage = (
                    num_mutual_followers / total_followed_by_us) * 100

            logging.info("\n--- Mutual Follower Report ---")
            logging.info(f"Account: @{self.username}")
            logging.info(f"Total Following (by us): {total_followed_by_us}")
            logging.info(f"Total Followers (of us): {total_followers}")
            logging.info(f"Mutual Followers: {num_mutual_followers}")
            logging.info(
                f"Follow-back Percentage: {follow_back_percentage:.2f}%")

            if num_mutual_followers > 0:
                logging.info("\nMutual Followers List:")
                for i, user in enumerate(sorted(list(mutual_followers))):
                    logging.info(f"- @{user}")
            else:
                logging.info("\nNo mutual followers found.")

        except Exception as e:
            logging.critical(f"A critical error occurred during analysis: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("WebDriver closed.")


if __name__ == "__main__":
    analyzer = MutualFollowerAnalyzer()
    analyzer.run_analysis()
