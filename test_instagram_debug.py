#!/usr/bin/env python3
"""
Test script to debug Instagram automation and take screenshots
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """Set up Chrome driver with debugging options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Don't run headless so we can see what's happening
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def take_screenshot(driver, filename):
    """Take a screenshot and save it"""
    try:
        driver.save_screenshot(f"debug_{filename}.png")
        logger.info(f"📸 Screenshot saved: debug_{filename}.png")
    except Exception as e:
        logger.error(f"❌ Failed to take screenshot: {e}")


def test_instagram_dm():
    """Test Instagram DM functionality"""
    driver = None
    try:
        logger.info("🚀 Starting Instagram DM test...")

        # Setup driver
        driver = setup_driver()

        # Navigate to Instagram login
        logger.info("🔐 Navigating to Instagram login...")
        driver.get("https://www.instagram.com/accounts/login/")
        take_screenshot(driver, "01_login_page")

        # Wait for login form
        time.sleep(3)

        # Find and fill username
        logger.info("👤 Entering username...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.send_keys("cocos_connected")
        take_screenshot(driver, "02_username_entered")

        # Find and fill password
        logger.info("🔑 Entering password...")
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("Shannonb3")
        take_screenshot(driver, "03_password_entered")

        # Click login button
        logger.info("🔘 Clicking login button...")
        login_button = driver.find_element(
            By.XPATH, "//button[@type='submit']")
        login_button.click()
        take_screenshot(driver, "04_login_clicked")

        # Wait for login to complete
        time.sleep(10)
        take_screenshot(driver, "05_after_login")

        # Navigate to a test user's profile
        test_username = "cocos_pt_studio"
        logger.info(f"👤 Navigating to @{test_username} profile...")
        driver.get(f"https://www.instagram.com/{test_username}/")
        time.sleep(5)
        take_screenshot(driver, "06_profile_page")

        # Look for Message button
        logger.info("🔍 Looking for Message button...")
        message_selectors = [
            "//button[contains(text(), 'Message')]",
            "//div[contains(text(), 'Message')][@role='button']",
            "//span[contains(text(), 'Message')]/ancestor::div[@role='button']",
            "//svg[@aria-label='Direct messages']/ancestor::div[@role='button']",
            "//div[@role='button' and contains(@class, 'x1i10hfl')]//span[text()='Messages']/..",
            "//div[@role='button' and contains(@class, 'x1i10hfl')]//svg[@aria-label='Direct messages']/.."
        ]

        message_button = None
        for i, selector in enumerate(message_selectors):
            try:
                logger.info(f"🔍 Trying selector {i+1}: {selector}")
                message_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if message_button and message_button.is_displayed():
                    logger.info(f"✅ Found Message button using selector {i+1}")
                    take_screenshot(driver, "07_message_button_found")
                    break
            except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f"❌ Selector {i+1} failed: {e}")
                continue

        if not message_button:
            logger.error("❌ Could not find Message button")
            take_screenshot(driver, "08_no_message_button")
            return False

        # Click Message button
        logger.info("🔘 Clicking Message button...")
        message_button.click()
        time.sleep(5)
        take_screenshot(driver, "09_after_message_click")

        # Look for message input
        logger.info("🔍 Looking for message input...")
        input_selectors = [
            "//div[@contenteditable='true'][@role='textbox']",
            "//textarea[@placeholder='Message...']",
            "//div[contains(@aria-label, 'Message')][@contenteditable='true']",
            "//div[@contenteditable='true']",
            "//textarea[contains(@placeholder, 'Message')]",
            "//div[@role='textbox'][@contenteditable='true']"
        ]

        message_input = None
        for i, selector in enumerate(input_selectors):
            try:
                logger.info(f"🔍 Trying input selector {i+1}: {selector}")
                message_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if message_input and message_input.is_displayed():
                    logger.info(f"✅ Found message input using selector {i+1}")
                    take_screenshot(driver, "10_message_input_found")
                    break
            except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f"❌ Input selector {i+1} failed: {e}")
                continue

        if not message_input:
            logger.error("❌ Could not find message input")
            take_screenshot(driver, "11_no_message_input")
            return False

        # Type test message
        logger.info("✍️ Typing test message...")
        test_message = "Hey! This is a test message from the automation."
        message_input.clear()
        time.sleep(1)
        message_input.send_keys(test_message)
        time.sleep(2)
        take_screenshot(driver, "12_message_typed")

        # Send message
        logger.info("📤 Sending message...")
        from selenium.webdriver.common.keys import Keys
        message_input.send_keys(Keys.RETURN)
        time.sleep(3)
        take_screenshot(driver, "13_message_sent")

        logger.info("✅ Test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        if driver:
            take_screenshot(driver, "14_error_state")
        return False

    finally:
        if driver:
            logger.info("🧹 Cleaning up driver...")
            driver.quit()


if __name__ == "__main__":
    logger.info("🎯 Starting Instagram automation debug test...")
    success = test_instagram_dm()
    if success:
        logger.info("✅ Test completed successfully!")
    else:
        logger.error("❌ Test failed!")
