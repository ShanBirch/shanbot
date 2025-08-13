#!/usr/bin/env python3
"""
Send messages to specific clients
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """Set up Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def login_to_instagram(driver):
    """Login to Instagram"""
    try:
        logger.info("🔐 Logging into Instagram...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        # Enter username
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.send_keys("cocos_connected")

        # Enter password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("Shannonb3")

        # Click login
        login_button = driver.find_element(
            By.XPATH, "//button[@type='submit']")
        login_button.click()

        # Wait for login
        time.sleep(10)
        logger.info("✅ Logged into Instagram")
        return True

    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        return False


def send_dm_to_user(driver, username, message):
    """Send DM to a user"""
    try:
        logger.info(f"💬 Sending DM to @{username}")

        # Navigate to profile
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(5)

        # Find and click Message button
        message_button_selectors = [
            "//div[contains(text(), 'Message')][@role='button']",
            "//button[contains(text(), 'Message')]",
            "//span[contains(text(), 'Message')]/ancestor::div[@role='button']"
        ]

        message_button = None
        for selector in message_button_selectors:
            try:
                message_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if message_button and message_button.is_displayed():
                    logger.info(f"✅ Found Message button")
                    break
            except:
                continue

        if not message_button:
            logger.error(f"❌ Could not find Message button for {username}")
            return False

        # Click Message button
        message_button.click()
        time.sleep(5)

        # Find message input
        input_selectors = [
            "//div[@contenteditable='true'][@role='textbox']",
            "//textarea[@placeholder='Message...']",
            "//div[@contenteditable='true']"
        ]

        message_input = None
        for selector in input_selectors:
            try:
                message_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if message_input and message_input.is_displayed():
                    logger.info(f"✅ Found message input")
                    break
            except:
                continue

        if not message_input:
            logger.error(f"❌ Could not find message input for {username}")
            return False

        # Type and send message
        message_input.clear()
        time.sleep(1)
        message_input.send_keys(message)
        time.sleep(2)
        message_input.send_keys(Keys.RETURN)
        time.sleep(3)

        logger.info(f"✅ Message sent to {username}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send message to {username}: {e}")
        return False


def main():
    """Main function to send messages"""

    # Client groups and messages
    new_challenge_clients = [
        ("aussiepotter", "Good Morning!! The Challenge Begins today, you should see in Coco's App youve been entered into it. Exciting times! Any questions shoot them through. What days have you set aside to train this week?"),
        ("blissedlia", "Good Morning!! The Challenge Begins today, you should see in Coco's App youve been entered into it. Exciting times! Any questions shoot them through. What days have you set aside to train this week?"),
        ("burcherella", "Good Morning!! The Challenge Begins today, you should see in Coco's App youve been entered into it. Exciting times! Any questions shoot them through. What days have you set aside to train this week?"),
        ("hannahjanedevlin", "Good Morning!! The Challenge Begins today, you should see in Coco's App youve been entered into it. Exciting times! Any questions shoot them through. What days have you set aside to train this week?")
    ]

    existing_clients = [
        ("kristyleecoop", "Monday Morning!! Lets go!! What sessions you making it to this week?"),
        ("shaneminehan", "Monday Morning!! Lets go!! What sessions you making it to this week?"),
        ("rebeccadangelo01",
         "Monday Morning!! Lets go!! What sessions you making it to this week?")
    ]

    driver = None
    try:
        # Setup and login
        driver = setup_driver()
        if not login_to_instagram(driver):
            return

        # Send messages to new challenge clients
        logger.info("🎯 Sending messages to new challenge clients...")
        for username, message in new_challenge_clients:
            success = send_dm_to_user(driver, username, message)
            if success:
                logger.info(f"✅ Sent challenge message to {username}")
            else:
                logger.error(
                    f"❌ Failed to send challenge message to {username}")
            time.sleep(10)  # Wait between messages

        # Send messages to existing clients
        logger.info("🎯 Sending messages to existing clients...")
        for username, message in existing_clients:
            success = send_dm_to_user(driver, username, message)
            if success:
                logger.info(f"✅ Sent existing client message to {username}")
            else:
                logger.error(
                    f"❌ Failed to send existing client message to {username}")
            time.sleep(10)  # Wait between messages

        logger.info("✅ All messages sent!")

    except Exception as e:
        logger.error(f"❌ Error in main: {e}")

    finally:
        if driver:
            logger.info("🧹 Cleaning up...")
            driver.quit()


if __name__ == "__main__":
    main()
