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
from openai import OpenAI

def print_step(message):
    """Print a step with clear formatting"""
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")

def print_substep(message):
    """Print a substep with clear formatting"""
    print("-"*30)
    print(message)
    print("-"*30)

# Configuration
print_step("INITIALIZING BOT CONFIGURATION")
logging.basicConfig(
    filename='instagram_bot_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Configuration variables
USERNAME = "cocos_pt_studio"
PASSWORD = "Shannonb3"
OPENAI_API_KEY = "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"
CHROMEDRIVER_PATH = "C:/SeleniumDrivers/chromedriver.exe"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize WebDriver
try:
    print_substep("Setting up Chrome WebDriver...")
    service = Service(CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("ChromeDriver initialized successfully")
except WebDriverException as e:
    print(f"❌ Error initializing ChromeDriver: {e}")
    exit(1)

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

def analyze_image_with_gpt(image_path):
    """Analyzes an image using GPT-4V and generates a friendly response."""
    print_step(f"ANALYZING IMAGE WITH GPT-4V")
    try:
        base64_image = encode_image(image_path)
        
        if not base64_image:
            print("❌ Failed to encode image")
            return None

        print_substep("Sending request to GPT-4V...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly assistant that generates engaging questions about Instagram stories. Keep your responses short, friendly, and conversational."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Look at this Instagram story and generate a friendly, engaging question or comment about it."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        friendly_response = response.choices[0].message.content.strip()
        print("✔️ Received response from GPT-4V:")
        print(f"📝 Generated message: {friendly_response}")
        return friendly_response

    except Exception as e:
        print(f"❌ Error analyzing image with GPT: {e}")
        return None

def send_message(driver, reply_box):
    """Attempt to send message using multiple methods."""
    print_substep("Attempting to send message...")
    
    # First try: Enter key
    try:
        print_substep("Method 1: Trying Enter key...")
        webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
        sleep(0.5)
        webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
        print("✔️ Message sent via Enter key")
        return True
    except Exception as e:
        print(f"Enter key method failed: {e}")
    
    # Second try: Send button
    try:
        print_substep("Method 2: Looking for send button...")
        send_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@role='button' and contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w') and contains(text(), 'Send')]"
            ))
        )
        print_substep("Clicking send button...")
        driver.execute_script("arguments[0].click();", send_button)
        print("✔️ Message sent via send button")
        return True
    except Exception as e:
        print(f"Send button method failed: {e}")
    
    return False

def login(driver):
    """Logs into Instagram."""
    print_step("LOGGING INTO INSTAGRAM")
    try:
        print_substep("Opening Instagram...")
        driver.get("https://www.instagram.com")
        
        print_substep("Waiting for login form...")
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        print_substep("Entering credentials...")
        username_input.send_keys(USERNAME)
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(PASSWORD)
        
        print_substep("Clicking login button...")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        sleep(5)

        print_substep("Handling 'Save Login Info' dialog...")
        try:
            not_now_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            print("✔️ Dismissed 'Save Login Info' dialog")
            sleep(2)
        except TimeoutException:
            print("No 'Save Login Info' dialog found")

        print_substep("Handling notifications dialog...")
        try:
            not_now_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            print("✔️ Dismissed notifications dialog")
            sleep(2)
        except TimeoutException:
            print("No notifications dialog found")

        print("✔️ Successfully logged into Instagram")
        return True

    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def navigate_home(driver):
    """Navigates to Instagram home page."""
    print_step("NAVIGATING TO HOME PAGE")
    try:
        print_substep("Looking for home button...")
        home_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a//*[name()='svg' and @aria-label='Home']/ancestor::a"
            ))
        )
        print_substep("Clicking home button...")
        home_button.click()
        sleep(5)
        print("✔️ Successfully navigated to home page")
        return True
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return False

def interact_with_stories(driver, max_stories=5):
    """Interacts with Instagram stories."""
    print_step("STARTING STORY INTERACTION")
    story_count = 0

    try:
        print_substep("Looking for stories...")
        story_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH,
                "//div[@role='presentation']//canvas/ancestor::div[@role='button']"
            ))
        )
        print(f"Found {len(story_elements)} stories")

        # Click the first story to start
        print_substep("Opening first story...")
        driver.execute_script("arguments[0].click();", story_elements[0])
        sleep(3)
        
        while story_count < max_stories:
            try:
                story_count += 1
                print_step(f"PROCESSING STORY #{story_count}")
                
                # Pause the story
                print_substep("Pausing story with spacebar...")
                webdriver.ActionChains(driver).send_keys(Keys.SPACE).perform()
                sleep(2)
                
                # Take screenshot
                screenshot_path = f"story_{story_count}.png"
                print_substep(f"Taking screenshot: {screenshot_path}")
                driver.save_screenshot(screenshot_path)
                print("✔️ Screenshot captured")
                
                # Get GPT analysis
                friendly_response = analyze_image_with_gpt(screenshot_path)
                
                if friendly_response:
                    try:
                        print_substep("Sanitizing response...")
                        sanitized_response = sanitize_message(friendly_response)
                        print(f"Original response: {friendly_response}")
                        print(f"Sanitized response: {sanitized_response}")
                        
                        print_substep("Looking for reply box...")
                        textarea_xpath = "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl') and contains(@class, 'xjbqb8w')]"
                        reply_box = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, textarea_xpath))
                        )
                        
                        print_substep("Clicking reply box...")
                        driver.execute_script("arguments[0].click();", reply_box)
                        sleep(1)
                        
                        print_substep("Typing message...")
                        for char in sanitized_response:
                            reply_box.send_keys(char)
                            sleep(0.05)
                        
                        # Try to send the message using multiple methods
                        if send_message(driver, reply_box):
                            print("✔️ Message sent successfully")
                        else:
                            print("❌ Failed to send message using all available methods")
                        
                        sleep(2)
                        
                    except Exception as e:
                        print(f"❌ Error in message sending process: {e}")
                
                print_substep("Moving to next story (Down Arrow)...")
                webdriver.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                sleep(3)
                
            except StaleElementReferenceException:
                print(f"❌ Story element became stale for #{story_count}, attempting recovery...")
                sleep(2)
                continue
            except Exception as e:
                print(f"❌ Error processing story #{story_count}: {e}")
                try:
                    webdriver.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                    sleep(3)
                except:
                    pass
                continue

    except Exception as e:
        print(f"❌ Error in story interaction: {e}")
    finally:
        print_step("FINISHING STORY INTERACTION")
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            sleep(2)
        except:
            pass

def main():
    try:
        print_step("STARTING INSTAGRAM STORY BOT")
        if login(driver) and navigate_home(driver):
            interact_with_stories(driver)
        print_step("BOT COMPLETED SUCCESSFULLY")
    except KeyboardInterrupt:
        print_step("BOT INTERRUPTED BY USER")
    except Exception as e:
        print_step(f"UNEXPECTED ERROR: {e}")
    finally:
        driver.quit()
        print_step("BROWSER CLOSED")

if __name__ == "__main__":
    main()