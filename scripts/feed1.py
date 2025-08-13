from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
import random
import logging
import base64
import os
from openai import OpenAI
from PIL import Image
import io


def print_step(message):
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


def print_substep(message):
    print("-" * 30)
    print(message)
    print("-" * 30)


def encode_image_from_selenium(driver, element):
    """Captures an element's screenshot and encodes it to base64"""
    try:
        location = element.location
        size = element.size
        png = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(png))

        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        image = image.crop((left, top, right, bottom))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
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
        self.username = "myfitness_shanbot"
        self.password = "cyywp7nyk"
        self.openai_api_key = "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"
        self.chromedriver_path = "C:/SeleniumDrivers/chromedriver.exe"
        self.interaction_pattern = ['comment', 'skip', 'like', 'skip',
                                    'comment', 'comment', 'skip', 'like', 'comment', 'like']

        self.client = OpenAI(api_key=self.openai_api_key)
        self.setup_driver()
        self.posts_processed = 0
        self.max_posts = 50  # Maximum number of posts to comment on
        self.processed_post_ids = set()  # Track posts we've already processed
        self.pattern_index = 0  # Track the pattern index
        self.current_post = None  # Track the current post

    def setup_driver(self):
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
        except WebDriverException as e:
            print(f"❌ Error initializing ChromeDriver: {e}")
            raise

    def login(self):
        print_step("LOGGING INTO INSTAGRAM")
        try:
            self.driver.get("https://www.instagram.com")

            username_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )

            username_input.send_keys(self.username)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)

            self.driver.find_element(
                By.XPATH, "//button[@type='submit']").click()
            sleep(5)

            self._handle_dialog("Save Login Info")
            self._handle_dialog("Turn on Notifications")

            return True
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def _handle_dialog(self, dialog_type):
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

    def analyze_image_with_gpt(self, image_str):
        print_step("ANALYZING IMAGE WITH GPT-4V")
        try:
            if not image_str:
                return None

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=250,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a friendly, casual Australian Personal Trainer Instagram user who loves engaging with friends' posts.

    Key traits:
    - Keep responses VERY short (10-25 words only)
    - Use casual Aussie PT slang and expressions
    - Focus on motivation and positivity
    - Avoid generic comments
    - Make specific observations about the image

    Response format:
    [Friendly observation + encouragement]

    Example responses:
    - "Those deadlift gains are showing mate! Keep crushing those PBs! 💙"
    - "Love the healthy meal prep setup! Your dedication is inspiring! 🍀"
    - "Beautiful morning run view! Nothing beats starting the day active! 🌟"
    - "Form looking perfect on those squats! Hard work pays off! 💙"

    Remember:
    - MUST be between 10-25 words total
    - Keep it super casual and friendly
    - Make specific references to what you see
    - No questions needed for feed comments
    """
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Look at this Instagram post and generate an encouraging comment."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_str}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ]
            )

            comment = response.choices[0].message.content.strip()

            if "error" in comment.lower() or len(comment.split()) > 25:
                print("⚠️ Using fallback response")
                comment = "Amazing work! Keep inspiring others with your dedication! 💪"

            print(f"📝 Generated comment: {comment}")
            return comment

        except Exception as e:
            print(f"❌ Error analyzing image with GPT: {e}")
            return "Amazing work! Keep inspiring others with your dedication! 💪"

    def get_post_identifier(self):
        """Get a unique identifier for the current post"""
        try:
            # Try to get post timestamp or other unique identifier
            timestamp = self.current_post.get_attribute("data-timestamp")
            if timestamp:
                return timestamp

            # Fallback to post text content + position
            # First 100 chars of post content
            post_content = self.current_post.text[:100]
            post_position = self.driver.execute_script(
                "return arguments[0].getBoundingClientRect().top;", self.current_post)
            return f"{post_content}_{post_position}"
        except:
            # Last resort: use post HTML
            # First 200 chars of HTML
            return self.current_post.get_attribute("outerHTML")[:200]

    def _find_next_post(self):
        """Finds the next post in the feed using tab navigation."""

        if self.current_post is None:
            # First post, tab into the feed
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.TAB)
            sleep(0.5)  # Initial delay for the first tab to find the feed

        max_attempts = 1000
        attempts = 0
        while attempts < max_attempts:
            try:
                active_element = self.driver.switch_to.active_element

                # Check if the active element is a post by looking for the role="article"
                if active_element.get_attribute('role') == "article":
                    # Check if there is a video or image in the post
                    media_element = active_element.find_elements(
                        By.XPATH, ".//*[self::img or self::video]")
                    if media_element:
                        self.current_post = active_element
                        return True  # Next post was found.

                active_element.send_keys(Keys.TAB)
                sleep(0.2)
                attempts += 1

            except Exception as e:
                print(f"❌ Error while tabbing {e}")

        print("❌ could not find next post after multiple attempts, ending...")
        return False

    def scroll_feed(self):
        print_step("NAVIGATING THROUGH FEED USING TAB")
        try:
            while self.posts_processed < self.max_posts:
                if not self._find_next_post():
                    break  # exit loop if no more posts can be found

                # Get unique identifier for this post
                post_id = self.get_post_identifier()

                # Skip if we've already processed this post
                if post_id in self.processed_post_ids:
                    print(
                        f"Skipping post due to being already processed, post_id:{post_id}")
                    continue

                action = self.interaction_pattern[self.pattern_index % len(
                    self.interaction_pattern)]
                print(
                    f"Processing post {self.posts_processed + 1}/{self.max_posts} | Action: {action.upper()}")

                try:

                    # Find the media element (img or video)
                    try:
                        media_element = self.current_post.find_element(
                            By.XPATH, ".//*[self::img or self::video]")
                        image_str = encode_image_from_selenium(
                            self.driver, media_element)
                    except Exception as e:
                        print(
                            f"❌ Error finding and screenshotting media element {e}")
                        continue

                    if action == 'comment' or action == 'like':

                        # Find the comment box (aria-label "Add a comment...")
                        try:
                            comment_box = self.current_post.find_element(
                                By.XPATH, ".//textarea[@aria-label='Add a comment…']")
                        except Exception as e:
                            print(f"❌ Could not find comment box: {e}")
                            continue

                        if action == 'comment':
                            comment = self.analyze_image_with_gpt(image_str)

                            if comment:
                                # Type and send comment
                                try:
                                    # Filter out any non-BMP characters and keep only basic emojis
                                    filtered_comment = ''.join(
                                        char for char in comment if ord(char) < 0xFFFF)
                                    # Replace common emojis with simpler alternatives
                                    emoji_replacements = {
                                        '🎨': '🎭',
                                        '✨': '✰',
                                        '💪': '💙',
                                        '🌅': '🌟',
                                        '🥗': '🍀',
                                        '🏋️': '💙'
                                    }
                                    for old_emoji, new_emoji in emoji_replacements.items():
                                        filtered_comment = filtered_comment.replace(
                                            old_emoji, new_emoji)

                                    comment_box.click()
                                    comment_box.send_keys(filtered_comment)
                                    sleep(2)
                                    comment_box.send_keys(Keys.ENTER)
                                    sleep(2)

                                    print(
                                        f"✔️ Commented on post: {filtered_comment}")
                                except Exception as e:
                                    print(f"❌ Error typing comment: {e}")
                                    continue
                            else:
                                print("❌ Could not generate comment, skipping...")

                        if action == 'like':
                            # Find the like button
                            try:
                                # Find the like button within the post
                                like_button = self.current_post.find_element(
                                    By.XPATH, ".//div[@class='x6s0dn4 x78zum5 xdt5ytf xl56j7k']//svg[@aria-label='Like']")

                                # Select the parent and then click
                                parent = like_button.find_element(
                                    By.XPATH, "./..")
                                parent.click()
                                print("✔️ Post liked")
                                sleep(2)
                            except Exception as e:
                                print(f"❌ Error liking post: {e}")
                                continue

                    self.posts_processed += 1
                    self.processed_post_ids.add(post_id)
                    self.pattern_index += 1
                    sleep(random.uniform(3, 7))  # Random delay between actions

                except Exception as e:
                    print(f"❌ Error processing post: {e}")
                    continue

        except Exception as e:
            print(f"❌ Error navigating through feed using tab: {e}")

    def cleanup(self):
        try:
            self.driver.quit()
            print_step("BROWSER CLOSED")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")


def main():
    bot = None
    try:
        bot = InstagramFeedBot()
        if bot.login() and bot.navigate_home():
            bot.scroll_feed()
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
