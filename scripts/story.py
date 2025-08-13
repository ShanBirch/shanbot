from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
import random
import logging
import time
import base64
import os
from openai import OpenAI


def print_step(message):
    """Print a step with clear formatting"""
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")


def print_substep(message):
    """Print a substep with clear formatting"""
    print("-" * 30)
    print(message)
    print("-" * 30)


def sanitize_message(message):
    """Remove emojis and special characters from the message."""
    return ''.join(char for char in message if ord(char) < 65536)


def encode_image(image_path):
    """Encodes an image file to Base64 format."""
    print_substep(f"Encoding image: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None


class InstagramBot:
    def __init__(self):
        """Initialize the Instagram bot with configuration."""
        print_step("INITIALIZING BOT CONFIGURATION")

        # Setup logging
        logging.basicConfig(
            filename='instagram_bot_debug.log',
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(message)s'
        )

        # Configuration (replace with your credentials)
        self.username = "cocos_connected"
        self.password = "Shannonb3"
        self.openai_api_key = "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"
        self.chromedriver_path = "C:/SeleniumDrivers/chromedriver.exe"

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)

        # Initialize WebDriver
        self.setup_driver()

    def setup_driver(self):
        """Setup and configure the Chrome WebDriver."""
        try:
            print_substep("Setting up Chrome WebDriver...")
            service = Service(self.chromedriver_path)
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            print("ChromeDriver initialized successfully")
        except WebDriverException as e:
            print(f"❌ Error initializing ChromeDriver: {e}")
            raise

    def is_live_story(self, story_element):
        """Check if a story in the story tray is live before clicking it."""
        try:
            # Get all text elements within the story button to check for 'LIVE'
            all_text_elements = story_element.find_elements(By.XPATH, ".//div")
            for element in all_text_elements:
                try:
                    text = element.text.strip().upper()
                    if 'LIVE' in text:
                        print(f"Found LIVE text in element: {text}")
                        return True
                except:
                    continue

            # Additional check for specific live indicators
            live_indicators = story_element.find_elements(
                By.XPATH,
                ".//div[contains(@class, 'x1lq5wgf') or contains(@class, 'x78zum5')]"
            )

            for indicator in live_indicators:
                try:
                    aria_label = indicator.get_attribute('aria-label')
                    if aria_label and 'live' in aria_label.lower():
                        print(f"Found live aria-label: {aria_label}")
                        return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"Error in is_live_story: {e}")
            return False

    def get_first_non_live_story(self):
        """Find the first non-live story in the tray."""
        print_step("SCANNING FOR NON-LIVE STORY")

        try:
            # Wait for and get all story elements using the profile picture class names
            story_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//img[contains(@class, 'x972fbf') and contains(@class, 'xcfux6l')]/ancestor::div[@role='button']"
                ))
            )

            print(f"Found {len(story_elements)} story elements")

            # Check each story
            for idx, story in enumerate(story_elements, 1):
                print(f"\nChecking story {idx}/{len(story_elements)}")
                try:
                    # Look for the live indicator near the profile picture
                    live_indicators = story.find_elements(
                        By.XPATH,
                        ".//div[text()='LIVE' or contains(@class, 'x1lq5wgf')]"
                    )

                    if not live_indicators:
                        print("✅ Found non-live story!")
                        return story
                    else:
                        print("⏭️ Skipping live story...")
                except Exception as e:
                    print(f"Error checking story {idx}: {e}")
                    continue

            print("❌ No non-live stories found")
            return None

        except Exception as e:
            print(f"Error finding stories: {e}")
            return None

    def verify_stories_remaining(self):
        """Verify if there are more stories to process."""
        try:
            # Wait up to 7 seconds for a story container to load
            WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='_aagv']")  # More robust selector
                )
            )
            return True
        except TimeoutException:
            return False

    def analyze_image_with_gpt(self, image_path):
        """Analyzes an image using GPT-4V and generates a friendly response."""
        print_step("ANALYZING IMAGE WITH GPT-4V")
        try:
            base64_image = encode_image(image_path)

            if not base64_image:
                return None

            print_substep("Sending request to GPT-4V...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=250,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a friendly, casual Australian Personal Trainer Instagram user who loves engaging with friends' stories.

Key traits:
- Keep responses VERY short (5-15 words only)
- Use casual Aussie PT slang and expressions
- Focus on motivation and fitness encouragement
- ALWAYS include a brief question

Response format:
[Short comment] + [Brief question]

Common phrases examples (all under 20 words):
- "Looking strong mate! What's your fav exercise?"
- "Killing that form! How long you been training?"
- "Beast mode! What's your post-workout meal?"
- "Gains incoming! What's your next fitness goal?"
- "Smashing it! How's the program going?"

Remember:
- MUST be between 5-20 words total
- ALWAYS include a question
- Keep it super casual and friendly
- One short comment + one short question
- React to both fitness and non-fitness content
"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Look at this Instagram story and generate a friendly response."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ]
            )

            friendly_response = response.choices[0].message.content.strip()

            # Check if response contains error message or is too long
            if "error" in friendly_response.lower() or len(friendly_response.split()) > 20:
                print("⚠️ Using fallback response instead of:", friendly_response)
                friendly_response = "Love this! How have you been? 💪"

            print(f"📝 Generated message: {friendly_response}")
            return friendly_response

        except Exception as e:
            print(f"❌ Error analyzing image with GPT: {e}")
            return "Love this! How have you been? 💪"  # Fallback response

    def login(self):
        """Logs into Instagram."""
        print_step("LOGGING INTO INSTAGRAM")
        try:
            print_substep("Opening Instagram...")
            self.driver.get("https://www.instagram.com")

            print_substep("Waiting for login form...")
            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )

            print_substep("Entering credentials...")
            username_input.send_keys(self.username)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)

            print_substep("Clicking login button...")
            self.driver.find_element(
                By.XPATH, "//button[@type='submit']").click()
            sleep(5)

            # Handle dialogs
            self._handle_dialog("Save Login Info")
            self._handle_dialog("Turn on Notifications")

            print("✔️ Successfully logged into Instagram")
            return True

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def _handle_dialog(self, dialog_type):
        """Handle common Instagram dialogs."""
        try:
            not_now_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            print(f"✔️ Dismissed '{dialog_type}' dialog")
            sleep(2)
        except TimeoutException:
            print(f"No '{dialog_type}' dialog found")

    def navigate_home(self):
        """Navigates to Instagram home page."""
        print_step("NAVIGATING TO HOME PAGE")
        try:
            print_substep("Looking for home button...")
            home_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//a//*[name()='svg' and @aria-label='Home']/ancestor::a"
                ))
            )
            home_button.click()
            sleep(5)
            print("✔️ Successfully navigated to home page")
            return True
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False

    def get_total_stories(self):
        """Gets the total number of available stories."""
        try:
            story_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//div[@role='presentation']//canvas/ancestor::div[@role='button']"
                ))
            )
            return len(story_elements)
        except Exception as e:
            print(f"❌ Error counting stories: {e}")
            return 0

    def process_single_story(self, story_number, total_stories):
        """Process a single story with proper pausing and clear step sequence."""
        screenshot_path = None
        MAX_REPLY_BOX_ATTEMPTS = 3
        success = False

        try:
            print_step(f"PROCESSING STORY {story_number}/{total_stories}")

            # Check if it's a live story
            try:
                live_indicator = self.driver.find_element(
                    By.XPATH, "//div[contains(text(), 'Live')]")
                print("⚠️ Live story detected - skipping...")
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_DOWN).perform()
                return False
            except NoSuchElementException:
                print("✔️ Not a live story - proceeding...")

            # Immediate pause when story starts
            print_substep("Pausing story...")
            sleep(0.2)  # Brief wait for story to begin playing
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            print("✔️ Story paused")
            sleep(1)  # Wait for story to fully load while paused

            # Check for comment box before proceeding
            print_substep("Checking for comment box...")
            try:
                reply_box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]"
                    ))
                )
                print("✔️ Comment box found.")
            except TimeoutException:
                # Check for sponsored label
                try:
                    sponsored_label = self.driver.find_element(
                        By.XPATH, "//span[text()='Sponsored']")
                    print("⚠️ Sponsored ad detected - skipping to next user.")
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.ARROW_DOWN).perform()
                    return False
                except NoSuchElementException:
                    print("❌ Comment box not found - skipping to next user.")
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.ARROW_DOWN).perform()
                    return False

            print_substep("Taking screenshot...")
            screenshot_path = f"story_{story_number}.png"
            self.driver.save_screenshot(screenshot_path)
            print("✔️ Screenshot captured")

            print_substep("Analyzing with GPT...")
            friendly_response = self.analyze_image_with_gpt(screenshot_path)

            if friendly_response:
                print_substep("Processing response...")
                sanitized_response = sanitize_message(friendly_response)
                print(f"Original response: {friendly_response}")
                print(f"Sanitized response: {sanitized_response}")

                reply_box_found = False
                for attempt in range(MAX_REPLY_BOX_ATTEMPTS):
                    print_substep(
                        f"Finding reply box (Attempt {attempt + 1}/{MAX_REPLY_BOX_ATTEMPTS})...")

                    try:
                        reply_box = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]"
                            ))
                        )
                        reply_box_found = True
                        print("✔️ Reply box found")

                        print_substep("Clicking reply box...")
                        self.driver.execute_script(
                            "arguments[0].click();", reply_box)
                        print("✔️ Reply box clicked")
                        sleep(1)

                        print_substep("Typing message...")
                        for char in sanitized_response:
                            reply_box.send_keys(char)
                            sleep(0.05)
                        print("✔️ Message typed")

                        print_substep("Sending message...")
                        if self.send_message(reply_box):
                            print("✔️ Message sent via Enter key")
                            print("✔️ Message sent successfully")
                            success = True
                            break
                        else:
                            print("❌ Failed to send message")

                    except Exception as e:
                        print(
                            f"⚠️ Reply box attempt {attempt + 1} failed: {str(e)}")
                        sleep(1)
                        continue

                    if not reply_box_found:
                        print(
                            "❌ No reply box found after all attempts - skipping to next story")
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.ARROW_DOWN).perform()
                        return False  # Indicate failure to process

            # Move the navigation and success message inside the 'if success' block
            if success:
                print_substep("Moving to next story...")
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_DOWN).perform()
                print("✔️ Navigated to next story")
                print("✔️ Story processed successfully")
                # Immediate pause after moving to next story
                print_substep("Pausing new story...")
                sleep(0.2)  # Brief wait for story transition
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ New story paused")
                sleep(0.5)  # Short wait for next story to stabilize
            else:
                print(
                    "⚠️ Story processing not fully successful, skipping to next story.")
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_DOWN).perform()
                print("✔️ Navigated to next story")
                # Immediate pause after moving to next story
                print_substep("Pausing new story...")
                sleep(0.2)  # Brief wait for story transition
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ New story paused")
                sleep(0.5)  # Short wait for next story to stabilize

        except Exception as e:
            print(f"❌ Error processing story: {e}")
            try:
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.ARROW_DOWN).perform()
                print("➡️ Moved to next story after error")
                # Also try to pause after error recovery
                sleep(0.2)
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("✔️ Next story paused after error")
            except Exception:
                pass

        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                except Exception as remove_err:
                    print(f"Error removing screenshot: {remove_err}")

            return success

    def send_message(self, reply_box):
        """Attempt to send message using multiple methods."""
        methods = [
            (lambda: webdriver.ActionChains(self.driver).send_keys(
                Keys.ENTER).perform(), "Enter key"),
            (lambda: self._click_send_button(), "Send button")
        ]

        for method, name in methods:
            try:
                print_substep(f"Trying {name}...")
                method()
                print(f"✔️ Message sent via {name}")
                return True
            except Exception as e:
                print(f"{name} method failed: {e}")

        return False

    def _click_send_button(self):
        """Helper method to click the send button."""
        send_button = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@role='button' and contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w') and contains(text(), 'Send')]"
            ))
        )
        self.driver.execute_script("arguments[0].click();", send_button)

    def interact_with_stories(self):
        """Interacts with all available Instagram stories."""
        story_count = 0
        successful_comments = 0
        processing = True
        consecutive_failures = 0
        MAX_FAILURES = 5
        last_story_time = time.time()

        try:
            # Find first non-live story
            print_step("FINDING FIRST NON-LIVE STORY")
            first_story = self.get_first_non_live_story()

            if not first_story:
                print("❌ No suitable stories found to process")
                return

            print_step("OPENING FIRST STORY")
            self.driver.execute_script("arguments[0].click();", first_story)
            sleep(3)

            while processing:
                current_time = time.time()
                if current_time - last_story_time < 0.5:
                    sleep(0.5 - (current_time - last_story_time))
                last_story_time = current_time

                story_count += 1
                print_step(f"PROCESSING STORY {story_count}")

                try:
                    # Process the current story
                    if self.process_single_story(story_count, 0):
                        successful_comments += 1
                        consecutive_failures = 0
                        # print("✔️ Story processed successfully") # Removed duplicate
                    else:
                        consecutive_failures += 1
                        print(
                            f"⚠️ Story processing failed (Failure #{consecutive_failures})")

                    # After processing, move to the next story and pause
                    print_substep("Moving to next story and pausing...")
                    logging.debug("Sending Keys.ARROW_DOWN")
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.ARROW_DOWN).perform()
                    sleep(0.5)  # Wait for transition
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.SPACE).perform()
                    print("✔️ Moved to next story and paused")
                    sleep(1)  # Give time to load

                except Exception as e:
                    consecutive_failures += 1
                    print(f"❌ Error processing story {story_count}: {e}")
                    print("➡️ Error occurred during story processing.")

                if consecutive_failures >= MAX_FAILURES:
                    print("❌ Too many consecutive failures - ending processing")
                    processing = False
                else:
                    print_substep("Checking for more stories...")
                    logging.debug("Before calling verify_stories_remaining")
                    has_more_stories = self.verify_stories_remaining()
                    logging.debug(
                        f"verify_stories_remaining returned: {has_more_stories}")
                    logging.debug("After calling verify_stories_remaining")
                    if not has_more_stories:
                        print("⚠️ No more stories detected.")
                        processing = False
                    else:
                        print("🔄 Continuing to the next story.")

                print(
                    f"Progress: {story_count} stories processed, {successful_comments} successful comments")

        except Exception as e:
            print(f"❌ Error in story interaction: {e}")

        finally:
            print_step("STORY INTERACTION SUMMARY")
            print(f"""
Stories Statistics:
------------------
Stories processed: {story_count}
Successful comments: {successful_comments}
Success rate: {(successful_comments/story_count)*100 if story_count > 0 else 0:.2f}%
""")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.driver.quit()
            print_step("BROWSER CLOSED")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")


def main():
    bot = None
    try:
        bot = InstagramBot()
        if bot.login() and bot.navigate_home():
            bot.interact_with_stories()
        print_step("BOT COMPLETED SUCCESSFULLY")
    except KeyboardInterrupt:
        print_step("BOT INTERRUPTED BY USER")
    except Exception as e:
        print_step(f"UNEXPECTED ERROR: {e}")
    finally:
        if bot:
            bot.cleanup()


if __name__ == "__main__":
    main()
