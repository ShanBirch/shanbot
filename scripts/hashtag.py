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

def print_step(message):
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")

def print_substep(message):
    print("-"*30)
    print(message)
    print("-"*30)

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None

class InstagramHashtagBot:
    def __init__(self):
        print_step("INITIALIZING BOT CONFIGURATION")
        
        # Setup logging
        logging.basicConfig(
            filename='instagram_hashtag_bot.log',
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(message)s'
        )
        
        # Configuration
        self.username = "cocos_connected"
        self.password = "Shannonb3"
        self.openai_api_key = "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"
        self.chromedriver_path = "C:/SeleniumDrivers/chromedriver.exe"
        self.hashtag = "#hamptonstreet"
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.setup_driver()
        self.posts_commented = 0
        self.max_posts = 100  # Maximum number of posts to comment on
        self.processed_posts = set()  # Track posts we've already processed
        self.last_scroll_position = 0  # Track scroll position

    def setup_driver(self):
        try:
            print_substep("Setting up Chrome WebDriver...")
            service = Service(self.chromedriver_path)
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
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
            
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
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
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            print(f"✔️ Dismissed '{dialog_type}' dialog")
            sleep(2)
        except TimeoutException:
            print(f"No '{dialog_type}' dialog found")

    def navigate_to_hashtag(self):
        print_step(f"NAVIGATING TO HASHTAG: {self.hashtag}")
        try:
            # Method 1: Try direct URL navigation
            try:
                hashtag_without_hash = self.hashtag.replace("#", "")
                self.driver.get(f"https://www.instagram.com/explore/tags/{hashtag_without_hash}/")
                sleep(5)
                return True
            except Exception as e:
                print(f"Direct URL navigation failed: {e}")

            # Method 2: Try search functionality
            try:
                # First try to find the search button and click it
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Search']"))
                )
                search_button.click()
                sleep(2)

                # Then find and use the search input
                search_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search'], input[aria-label='Search input']"))
                )
                
                # Clear existing text and send new search term
                search_input.clear()
                sleep(1)
                search_input.send_keys(self.hashtag)
                sleep(2)
                
                # Wait for search results and click the first hashtag result
                hashtag_results = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/explore/tags/']"))
                )
                
                if hashtag_results:
                    hashtag_results[0].click()
                    sleep(5)
                    return True
                
            except Exception as e:
                print(f"Search navigation failed: {e}")

            # Method 3: Try JavaScript navigation
            try:
                hashtag_without_hash = self.hashtag.replace("#", "")
                self.driver.execute_script(f"window.location.href = 'https://www.instagram.com/explore/tags/{hashtag_without_hash}/'")
                sleep(5)
                return True
            except Exception as e:
                print(f"JavaScript navigation failed: {e}")

            raise Exception("All navigation methods failed")
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False

    def analyze_image_with_gpt(self, image_path):
        print_step("ANALYZING IMAGE WITH GPT-4V")
        try:
            base64_image = encode_image(image_path)
            
            if not base64_image:
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
                                    "url": f"data:image/jpeg;base64,{base64_image}",
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

    def close_post_modal(self):
        """Helper method to close the post modal using multiple fallback approaches"""
        methods_tried = 0
        max_attempts = 3
        
        while methods_tried < max_attempts:
            try:
                # Method 1: Try finding and clicking the close button
                close_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//*[@aria-label='Close' or contains(@aria-label, 'Close')]"
                )
                
                if close_buttons:
                    for button in close_buttons:
                        try:
                            button.click()
                            sleep(1)
                            return True
                        except:
                            try:
                                self.driver.execute_script("arguments[0].click();", button)
                                sleep(1)
                                return True
                            except:
                                continue

                # Method 2: Try pressing ESC key
                actions = webdriver.ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                sleep(1)

                # Method 3: Try clicking outside the modal
                body = self.driver.find_element(By.TAG_NAME, "body")
                actions = webdriver.ActionChains(self.driver)
                actions.move_to_element_with_offset(body, 0, 0).click().perform()
                sleep(1)

                methods_tried += 1
            except Exception as e:
                print(f"❌ Error in close attempt {methods_tried + 1}: {e}")
                methods_tried += 1

        return False

    def scroll_hashtag_feed(self):
        print_step("SCROLLING HASHTAG FEED")
        last_post_count = 0
        no_new_posts_count = 0
        
        # Wait for the feed to load
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article, div[role='menuitem'], a[href*='/p/']"))
            )
            print("✔️ Feed loaded successfully")
        except TimeoutException:
            print("⚠️ Feed load timeout - attempting to continue")
            
        while self.posts_commented < self.max_posts:
            # Try multiple selectors to find posts
            posts = []
            selectors = [
                "article",  # Traditional article posts
                "div[role='menuitem']",  # Some post containers
                "a[href*='/p/']",  # Post links
                "div[class*='_aagv']"  # Instagram's dynamic class for post containers
            ]
            
            for selector in selectors:
                try:
                    found_posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_posts:
                        posts.extend(found_posts)
                        print(f"✔️ Found {len(found_posts)} posts using selector: {selector}")
                except Exception as e:
                    print(f"⚠️ Error finding posts with selector {selector}: {e}")
                    
            # Remove duplicates by href attribute
            unique_posts = []
            seen_hrefs = set()
            for post in posts:
                try:
                    href = post.get_attribute('href')
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique_posts.append(post)
                except:
                    unique_posts.append(post)
                    
            posts = unique_posts
            current_post_count = len(posts)
            print(f"✔️ Found total of {current_post_count} unique posts")
                    
            # Check if we're finding new posts
            if current_post_count <= last_post_count:
                no_new_posts_count += 1
                print(f"⚠️ No new posts found (attempt {no_new_posts_count}/3)")
                if no_new_posts_count >= 3:
                    print("❌ No new posts after 3 attempts, ending script")
                    break
            else:
                no_new_posts_count = 0  # Reset counter if we found new posts
                    
            last_post_count = current_post_count
                
            for post in posts:
                if self.posts_commented >= self.max_posts:
                    break
                        
                try:
                    # Scroll post into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
                    sleep(2)

                    # Click on the post to open it
                    try:
                        post.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", post)
                    
                    print("✔️ Opened post")
                    sleep(3)

                    # Take screenshot of post
                    screenshot_path = f"post_{self.posts_commented}.png"
                    self.driver.save_screenshot(screenshot_path)

                    # Generate comment
                    comment = self.analyze_image_with_gpt(screenshot_path)

                    # Find and post comment first
                    comment_box_found = False
                    comment_posted = False
                    
                    # Reset focus to top of modal
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.TAB)
                    except:
                        pass

                    # Find comment box
                    comment_box_found = False
                    for i in range(500):
                        active_element = self.driver.switch_to.active_element
                        
                        if (active_element.get_attribute("aria-label") == "Add a comment…" or
                            active_element.get_attribute("placeholder") == "Add a comment…"):
                            comment_box = active_element
                            print(f"✔️ Found comment box using Tab navigation (attempt {i+1})")
                            comment_box_found = True
                            
                            try:
                                # Filter and clean comment
                                filtered_comment = ''.join(char for char in comment if ord(char) < 0xFFFF)
                                emoji_replacements = {
                                    '🎨': '🎭',
                                    '✨': '✰',
                                    '💪': '💙',
                                    '🌅': '🌟',
                                    '🥗': '🍀',
                                    '🏋️': '💙'
                                }
                                for old_emoji, new_emoji in emoji_replacements.items():
                                    filtered_comment = filtered_comment.replace(old_emoji, new_emoji)
                                
                                comment_box.click()
                                comment_box.send_keys(filtered_comment)
                                sleep(2)
                                
                                # Try multiple methods to send the comment
                                try:
                                    comment_box.send_keys(Keys.ENTER)
                                    sleep(1)
                                except:
                                    try:
                                        webdriver.ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                                        sleep(1)
                                    except:
                                        try:
                                            self.driver.execute_script("arguments[0].parentElement.submit();", comment_box)
                                            sleep(1)
                                        except:
                                            try:
                                                post_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Post')]")
                                                post_button.click()
                                            except:
                                                print("❌ Could not send comment using any method")
                                                raise Exception("Failed to send comment")
                                
                                print(f"✔️ Commented on post {self.posts_commented + 1}: {filtered_comment}")
                                self.posts_commented += 1
                                comment_posted = True
                                sleep(2)

                                # After successful comment, try to follow user
                                if comment_posted:
                                    try:
                                        # Tab through elements to find Follow button
                                        max_tab_attempts = 20
                                        follow_button_found = False
                                        
                                        for _ in range(max_tab_attempts):
                                            active_element = self.driver.switch_to.active_element
                                            element_text = active_element.text.lower()
                                            
                                            if element_text == "follow" and active_element.is_enabled():
                                                active_element.click()
                                                print("✔️ Successfully followed user")
                                                follow_button_found = True
                                                sleep(2)
                                                break
                                                
                                            active_element.send_keys(Keys.TAB)
                                            sleep(0.5)
                                            
                                        if not follow_button_found:
                                            print("⚠️ Could not find follow button after tabbing")
                                            
                                    except Exception as e:
                                        print(f"❌ Error during follow attempt: {e}")

                                if not self.close_post_modal():
                                    print("⚠️ Warning: Could not close post modal, attempting to continue...")
                                    self.driver.execute_script("window.scrollBy(0, 500);")
                                    sleep(3)
                                
                            except Exception as e:
                                print(f"❌ Error typing comment: {e}")
                            break
                        
                        active_element.send_keys(Keys.TAB)
                        sleep(0.5)
                    
                    if not comment_box_found:
                        print("❌ Could not find comment box after 500 tab attempts")
                        
                    # Remove screenshot
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                            
                    # Random delay between comments
                    sleep(random.uniform(30, 60))
                    
                except Exception as e:
                    print(f"❌ Error processing post: {e}")
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                    continue
            
            # Scroll down by a fixed amount
            try:
                self.driver.execute_script("window.scrollBy(0, 1000);")
                sleep(3)  # Wait for new posts to load
            except Exception as e:
                print(f"❌ Error scrolling: {e}")

    def cleanup(self):
        """Clean up resources and close the browser"""
        try:
            self.driver.quit()
            print_step("BROWSER CLOSED")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def main():
    bot = None
    try:
        bot = InstagramHashtagBot()
        if bot.login() and bot.navigate_to_hashtag():
            bot.scroll_hashtag_feed()
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