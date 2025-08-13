from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
import random
import logging
import base64
import os
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import time


def print_step(message):
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


def print_substep(message):
    print("-" * 30)
    print(message)
    print("-" * 30)


def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None


class InstagramFeedBot:
    def __init__(self):
        print_step("INITIALIZING BOT CONFIGURATION")

        # Setup logging
        logging.basicConfig(
            filename='instagram_feed_bot.log',
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(message)s'
        )

        # Configuration
        self.username = "cocos_pt_studio"  # Updated username
        self.password = "Shannonb3"  # Updated password
        # Hardcoded API key - not recommended
        self.gemini_api_key = "AIzaSyA3bMRGd2KfTrf_G6YuUIDiq7F94w1EDFw"
        genai.configure(api_key=self.gemini_api_key)
        # Path to geckodriver
        self.geckodriver_path = "C:\\Users\\Shannon\\Downloads\\geckodriver-v0.35.0-win64\\geckodriver.exe"
        # path to firefox
        self.firefox_binary_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
        # Changed model to gemini-2.0-flash-thinking-exp-1219
        self.client = genai.GenerativeModel(
            'gemini-2.0-flash-thinking-exp-1219')
        self.setup_driver()
        self.posts_commented = 0
        self.max_posts = 50  # Maximum number of posts to comment on
        self.processed_posts = set()  # Track posts we've already processed
        self.last_scroll_position = 0  # Track scroll position
        self.post_counter = 0
        # Added variables for comment pattern
        # comment x1, skip x3, comment x2, skip x3, comment x2
        self.comment_pattern = [1, 0, 0, 0, 2, 2, 0, 0, 0, 2, 2]
        self.pattern_index = 0
        self.skipped_posts = 0
        self.iteration_count = 0

    def setup_driver(self):
        try:
            print_substep("Setting up Firefox WebDriver...")
            logging.debug("Setting up Firefox WebDriver...")
            start_time = time.time()
            service = FirefoxService(self.geckodriver_path)
            firefox_options = Options()
            firefox_options.add_argument("--start-maximized")
            firefox_options.add_argument("--disable-notifications")
            firefox_options.add_argument("--disable-infobars")
            firefox_options.add_argument("--disable-extensions")
            firefox_options.binary_location = self.firefox_binary_path  # Set the binary location
            self.driver = webdriver.Firefox(
                service=service, options=firefox_options)
            end_time = time.time()
            logging.debug(
                f"FirefoxDriver set up successfully, took {end_time - start_time:.2f} seconds")
        except WebDriverException as e:
            logging.exception(f"❌ Error initializing FirefoxDriver: {e}")
            print(f"❌ Error initializing FirefoxDriver: {e}")
            raise

    def _verify_element_presence(self, locator, timeout=10, message="Element verification"):
        """Verifies that an element is present after an action."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            logging.debug(f"✔️ {message} successful")
            return True
        except TimeoutException:
            logging.error(f"❌ {message} failed: Element not found")
            print(f"❌ {message} failed: Element not found")
            return False

    def login(self):
        print_step("LOGGING INTO INSTAGRAM")
        logging.debug("Attempting to log into Instagram")
        try:
            start_time = time.time()
            self.driver.get("https://www.instagram.com")
            if not self._verify_element_presence((By.NAME, "username"), message="Login page loaded"):
                return False
            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )

            username_input.send_keys(self.username)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)

            self.driver.find_element(
                By.XPATH, "//button[@type='submit']").click()
            sleep(2)  # Reduced sleep time
            if not self._verify_element_presence((By.TAG_NAME, "article"), timeout=30, message="Login submission"):
                return False

            self._handle_dialog("Save Login Info")
            self._handle_dialog("Turn on Notifications")
            end_time = time.time()
            logging.debug(
                f"Successfully logged into instagram, took {end_time - start_time:.2f} seconds")
            return True
        except Exception as e:
            logging.exception(f"❌ Login error: {e}")
            print(f"❌ Login error: {e}")
            return False

    def _handle_dialog(self, dialog_type):
        try:
            logging.debug(f"Attempting to handle '{dialog_type}' dialog")
            start_time = time.time()
            not_now_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            print(f"✔️ Dismissed '{dialog_type}' dialog")
            if not self._verify_element_presence((By.XPATH, "//div[contains(text(), 'home')]"), message="Dialog dismissal"):
                return False
            end_time = time.time()
            logging.debug(
                f"Successfully dismissed '{dialog_type}' dialog, took {end_time - start_time:.2f} seconds")
            sleep(1)  # Reduced sleep time
            return True
        except TimeoutException:
            logging.debug(f"No '{dialog_type}' dialog found")
            print(f"No '{dialog_type}' dialog found")
            return True  # Returning True because its ok if the element isnt found, since its optional

    def navigate_home(self):
        """Navigates to Instagram home page."""
        print_step("NAVIGATING TO HOME PAGE")
        logging.debug("Attempting to navigate to home page")
        try:
            start_time = time.time()
            print_substep("Looking for home button...")
            logging.debug("Looking for home button...")
            home_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//a//*[name()='svg' and @aria-label='Home']/ancestor::a"
                ))
            )
            home_button.click()
            if not self._verify_element_presence((By.TAG_NAME, "article"), message="Navigated to home page"):
                return False
            sleep(2)  # Reduced sleep time
            end_time = time.time()
            print("✔️ Successfully navigated to home page")
            logging.debug(
                f"Successfully navigated to home page, took {end_time - start_time:.2f} seconds")
            return True
        except Exception as e:
            logging.exception(f"❌ Navigation error: {e}")
            print(f"❌ Navigation error: {e}")
            return False

    def _capture_post_screenshot(self, post):
        """Captures a screenshot of a post and returns the encoded image."""
        try:
            logging.debug("Attempting to capture post screenshot")
            start_time = time.time()
            # Get the location and size of the post
            location = post.location
            size = post.size

            # Capture the entire screenshot
            png = self.driver.get_screenshot_as_png()

            # Open the screenshot with PIL
            screenshot = Image.open(BytesIO(png))

            # Crop the image to the bounds of the element
            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']

            cropped_screenshot = screenshot.crop((left, top, right, bottom))

            # Save the cropped image to memory
            buffered = BytesIO()
            cropped_screenshot.save(buffered, format="PNG")
            encoded_image = base64.b64encode(
                buffered.getvalue()).decode('utf-8')
            end_time = time.time()
            logging.debug(
                f"Successfully captured post screenshot, took {end_time - start_time:.2f} seconds")
            return encoded_image
        except Exception as e:
            logging.exception(f"❌ Error capturing screenshot: {e}")
            print(f"❌ Error capturing screenshot: {e}")
            return None

    def _extract_post_text(self, post):
        """Extracts the text content of a post"""
        try:
            logging.debug("Attempting to extract post text")
            start_time = time.time()
            # Find the element with the post text
            text_element = post.find_element(
                By.XPATH, ".//div[contains(@class, 'x9f619') and contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]")
            end_time = time.time()
            logging.debug(
                f"Successfully extracted post text, took {end_time - start_time:.2f} seconds")
            return text_element.text
        except Exception as e:
            logging.exception(f"❌ Error extracting post text: {e}")
            print(f"❌ Error extracting post text: {e}")
            return None

    def generate_comment(self, post_image, post_text):
        """Generates a comment using Gemini Pro Vision."""
        try:
            print_substep("Generating comment using Gemini Pro Vision...")
            logging.debug("Generating comment using Gemini Pro Vision...")
            start_time = time.time()
            prompt = "Generate a single concise and engaging comment about this image and the following text for an Instagram post: " + \
                post_text if post_text else "Generate a single concise and engaging comment about this image for an Instagram post."

            if not post_image:
                logging.debug("❌ No image to provide to Gemini.")
                print("❌ No image to provide to Gemini.")
                return None

            response = self.client.generate_content(
                [prompt,
                 {"mime_type": "image/png", "data": post_image}]
            )
            response.resolve()

            if response.text:
                comment = response.text.strip()
                print(f"✔️ Gemini Generated Comment: {comment}")
                logging.debug(f"✔️ Gemini Generated Comment: {comment}")
                end_time = time.time()
                logging.debug(
                    f"Successfully generated comment from Gemini, took {end_time - start_time:.2f} seconds")
                return comment
            else:
                logging.debug("❌ Gemini returned an empty response.")
                print("❌ Gemini returned an empty response.")
                return None
        except Exception as e:
            logging.exception(f"❌ Error generating comment: {e}")
            print(f"❌ Error generating comment: {e}")
            return None

    def post_comment(self, post, comment_text):
        """Posts a comment on the given post."""
        try:
            print_substep("Posting comment...")
            logging.debug("Posting comment...")
            start_time = time.time()
            # Use a more specific xpath locator for the comment button
            comment_button = None
            # Try multiple options to find the comment button
            try:
                comment_button = WebDriverWait(post, 20).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, ".//div[@aria-label='Comment']"))
                )
            except TimeoutException:
                try:
                    comment_button = WebDriverWait(post, 20).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, ".//span[text()='Comment']"))
                    )
                except TimeoutException:
                    logging.error("❌ Could not locate comment button")
                    print("❌ Could not locate comment button")
                    return False
            comment_button.click()
            sleep(1)

            # Try to tab through and find the comment box
            comment_box = None
            for _ in range(10):  # Try a maximum of 10 tabs
                try:
                    actions = webdriver.ActionChains(self.driver)
                    actions.send_keys(Keys.TAB)
                    actions.perform()
                    sleep(0.5)
                    comment_box = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((
                            By.XPATH,
                            "//textarea[@aria-label='Add a comment...']"
                        ))
                    )
                    if comment_box:
                        break

                except Exception:
                    continue

            if not comment_box:
                logging.error("❌ Could not locate comment box using tab key")
                print("❌ Could not locate comment box using tab key")
                return False

            # Type comment text into the box
            try:
                comment_box.send_keys(comment_text)
                sleep(1)
            except Exception as e:
                logging.error(f"❌ Error typing comment in comment box: {e}")
                print(f"❌ Error typing comment in comment box: {e}")
                return False

            # Find the "Post" button and click it
            post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[text()='Post']"
                ))
            )
            post_button.click()
            sleep(1)
            if not self._verify_element_presence((By.XPATH, "//div[contains(@aria-label, 'Comment')]"), timeout=15, message="Post Button Clicked"):
                return False
            end_time = time.time()
            print("✔️ Comment posted successfully")
            logging.debug(
                f"✔️ Comment posted successfully, took {end_time - start_time:.2f} seconds")
            sleep(1)  # Reduced sleep time
            return True
        except Exception as e:
            logging.exception(f"❌ Error posting comment: {e}")
            print(f"❌ Error posting comment: {e}")
            return False

    def comment_on_post(self, post):
        """Handles the entire comment process for a single post."""
        try:
            logging.debug("Attempting to comment on post")
            start_time = time.time()

            # Capture a screenshot of the post
            post_image = self._capture_post_screenshot(post)
            sleep(1)
            # Extract text content
            post_text = self._extract_post_text(post)
            sleep(1)

            if post_image:
                # Generate comment using Gemini
                comment = self.generate_comment(post_image, post_text)
                sleep(1)
                if comment:
                    # Post the comment on the post
                    retry = 0
                    while retry < 3:
                        if self.post_comment(post, comment):
                            end_time = time.time()
                            logging.debug(
                                f"Successfully commented on post, took {end_time - start_time:.2f} seconds")
                            return True
                        else:
                            retry += 1
                            logging.debug(
                                f"❌ Could not comment on post, retry {retry}...")
                            print(
                                f"❌ Could not comment on post, retry {retry}...")
                    return False
            else:
                logging.debug("❌ Could not get post image.")
                print("❌ Could not get post image.")
                return False
        except Exception as e:
            logging.exception(f"❌ Error during the post commment process: {e}")
            print(f"❌ Error during the post commment process: {e}")
            return False

    def scroll_feed(self):
        print_step("NAVIGATING THROUGH FEED USING TAB")
        logging.debug("Starting tab navigation through feed")
        try:
            # Wait for feed to load
            start_time = time.time()
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            end_time = time.time()
            logging.debug(
                f"Feed loaded successfully, took {end_time - start_time:.2f} seconds")

            # find the first post
            posts = self.driver.find_elements(By.TAG_NAME, "article")
            if not posts:
                logging.debug("⚠️ No posts found")
                print("⚠️ No posts found")
                return False

            tab_element = posts[0]
            tab_element.click()

            while self.posts_commented < self.max_posts:

                for _ in range(100):  # Try a maximum of 100 tabs
                    try:
                        actions = webdriver.ActionChains(self.driver)
                        actions.send_keys(Keys.TAB)
                        actions.perform()
                        sleep(0.5)
                        tab_element = self.driver.switch_to.active_element

                        # check if we are in a post, check for a comment button
                        comment_button = None
                        try:
                            comment_button = tab_element.find_element(
                                By.XPATH, ".//div[@aria-label='Comment']")
                        except:
                            try:
                                comment_button = tab_element.find_element(
                                    By.XPATH, ".//span[text()='Comment']")
                            except:
                                continue  # no comment button, skip

                        # check if the comment button is on the tab element
                        if comment_button == tab_element:
                            post = tab_element.find_element(
                                By.XPATH, './ancestor::article')
                            # Check if the post is already processed
                            post_id = post.id
                            if post_id in self.processed_posts:
                                continue  # skip if we already processed it
                            else:
                                self.processed_posts.add(post_id)

                                # Only process if the post is not sponsored
                                if not self._is_sponsored(post):
                                    logging.debug(
                                        f"ℹ️  Attempting to comment on a post {self.posts_commented + 1}")
                                    print(
                                        f"ℹ️  Attempting to comment on a post {self.posts_commented + 1}")
                                    try:
                                        if self.comment_on_post(post):
                                            self.posts_commented += 1
                                            self.post_counter += 1
                                            if self.comment_pattern[self.pattern_index] == 2:
                                                if self.comment_on_post(post):
                                                    self.posts_commented += 1
                                                    self.post_counter += 1
                                                    print(
                                                        "ℹ️ Second comment added")
                                                    logging.debug(
                                                        "ℹ️ Second comment added")
                                                else:
                                                    logging.debug(
                                                        "❌ Could not add second comment.")
                                                    print(
                                                        "❌ Could not add second comment.")
                                        else:
                                            logging.debug(
                                                "❌ Could not comment on post.")
                                            print(
                                                "❌ Could not comment on post.")
                                    except Exception as e:
                                        logging.exception(
                                            f"❌ Error in comment_on_post: {e}")
                                        print(
                                            f"❌ Error during comment_on_post, please see logs: {e}")

                                else:
                                    print("ℹ️  Skipping sponsored post")
                                    logging.debug(
                                        "ℹ️  Skipping sponsored post")
                                    self.skipped_posts += 1

                            # Increment pattern index, looping back to 0 if needed
                            self.pattern_index = (
                                self.pattern_index + 1) % len(self.comment_pattern)
                            break

                    except Exception:
                        continue

                # check if we need to restart driver
                if self.post_counter >= 10:
                    self.cleanup()
                    self.setup_driver()
                    self.navigate_home()
                    self.post_counter = 0
                    logging.debug("Restarting driver")
                    print("Restarting driver")

                if self.posts_commented >= self.max_posts:
                    logging.debug("ℹ️ Reached maximum posts")
                    print("ℹ️ Reached maximum posts")
                    break
        except Exception as e:
            logging.exception(f"❌ Error during tab navigation: {e}")
            print(f"❌ Error during tab navigation: {e}")
            return False

    def _is_sponsored(self, post):
        """Checks if the given post is a sponsored post."""
        try:
            logging.debug("Checking if post is sponsored")
            sponsored_element = post.find_elements(
                By.XPATH,
                ".//*[contains(text(), 'Sponsored')]"
            )
            return bool(sponsored_element)
        except Exception:
            logging.debug("Could not check if post is sponsored")
            return False

    def cleanup(self):
        try:
            self.driver.quit()
            print_step("BROWSER CLOSED")
            logging.debug("BROWSER CLOSED")
        except Exception as e:
            logging.exception(f"❌ Error during cleanup: {e}")
            print(f"❌ Error during cleanup: {e}")


def main():
    bot = None
    iteration = 0
    try:
        bot = InstagramFeedBot()
        if bot.login() and bot.navigate_home():
            while bot.posts_commented < bot.max_posts:
                iteration += 1
                print_step(f"STARTING ITERATION {iteration}")
                logging.debug(f"STARTING ITERATION {iteration}")
                bot.scroll_feed()
                if bot.posts_commented < bot.max_posts:
                    print("ℹ️ Posts remain, re-iterating...")
                    logging.debug("ℹ️ Posts remain, re-iterating...")
                else:
                    print("ℹ️ Max posts reached, ending script")
                    logging.debug("ℹ️ Max posts reached, ending script")
        print_step("BOT COMPLETED SUCCESSFULLY")
        logging.debug("BOT COMPLETED SUCCESSFULLY")
    except KeyboardInterrupt:
        print_step("BOT INTERRUPTED BY USER")
        logging.debug("BOT INTERRUPTED BY USER")
    except Exception as e:
        # Log full traceback
        logging.exception(f"UNEXPECTED ERROR IN FEED.PY: {e}")
        print_step(f"UNEXPECTED ERROR IN FEED.PY, please see logs: {e}")
    finally:
        if bot:
            bot.cleanup()


if __name__ == "__main__":
    main()
