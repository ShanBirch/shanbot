import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
INSTAGRAM_USERNAME = "cocos_connected"
INSTAGRAM_PASSWORD = "Shannonb3"
LOGIN_URL = "https://www.instagram.com/accounts/login/"
CHROME_DRIVER_PATH = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"


def setup_driver():
    """Setup Chrome driver for testing"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_experimental_option("detach", True)

    # Try manual path first
    if os.path.exists(CHROME_DRIVER_PATH):
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Using manual ChromeDriver path")
    else:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Using system ChromeDriver")

    return driver


def analyze_login_page(driver):
    """Analyze the current Instagram login page structure"""
    logger.info("Analyzing login page elements...")

    # Navigate to login page
    driver.get(LOGIN_URL)
    time.sleep(5)

    # Find all form elements
    try:
        # Find all inputs
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(all_inputs)} input elements:")
        for i, inp in enumerate(all_inputs):
            name = inp.get_attribute("name") or "No name"
            placeholder = inp.get_attribute("placeholder") or "No placeholder"
            input_type = inp.get_attribute("type") or "No type"
            aria_label = inp.get_attribute("aria-label") or "No aria-label"
            logger.info(
                f"  Input {i}: name='{name}', type='{input_type}', placeholder='{placeholder}', aria-label='{aria_label}'")

        # Find all buttons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(all_buttons)} button elements:")
        for i, btn in enumerate(all_buttons):
            text = btn.text.strip() or "No text"
            button_type = btn.get_attribute("type") or "No type"
            classes = btn.get_attribute("class") or "No classes"
            logger.info(
                f"  Button {i}: text='{text}', type='{button_type}', classes='{classes[:100]}'")

        # Find divs with role=button
        div_buttons = driver.find_elements(
            By.CSS_SELECTOR, "div[role='button']")
        logger.info(
            f"Found {len(div_buttons)} div elements with role='button':")
        for i, div in enumerate(div_buttons):
            text = div.text.strip() or "No text"
            classes = div.get_attribute("class") or "No classes"
            logger.info(
                f"  Div button {i}: text='{text}', classes='{classes[:100]}'")

    except Exception as e:
        logger.error(f"Error analyzing page: {e}")


def test_login_with_various_selectors(driver):
    """Test login with various button selectors"""
    logger.info("Testing login with various selectors...")

    # Navigate to login page
    driver.get(LOGIN_URL)
    time.sleep(5)

    # Fill username
    try:
        username_field = driver.find_element(By.NAME, "username")
        username_field.clear()
        username_field.send_keys(INSTAGRAM_USERNAME)
        logger.info("Username entered successfully")
    except Exception as e:
        logger.error(f"Could not enter username: {e}")
        return False

    # Fill password
    try:
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(INSTAGRAM_PASSWORD)
        logger.info("Password entered successfully")
    except Exception as e:
        logger.error(f"Could not enter password: {e}")
        return False

    time.sleep(2)

    # Try different login button selectors
    login_selectors = [
        ("XPATH", "//button[@type='submit']"),
        ("XPATH", "//button[contains(text(), 'Log in')]"),
        ("XPATH", "//button[contains(text(), 'Log In')]"),
        ("XPATH", "//div[text()='Log in']"),
        ("XPATH", "//div[text()='Log In']"),
        ("CSS", "button[type='submit']"),
        ("CSS", "div[role='button']"),
        ("XPATH", "//form//button[1]"),
        ("XPATH", "//button[contains(@class, 'L3NKy')]"),
        ("XPATH", "//button[contains(@class, '_acan')]"),
        ("XPATH", "//button[contains(@class, '_acap')]"),
    ]

    for selector_type, selector in login_selectors:
        try:
            logger.info(f"Trying selector: {selector_type} = {selector}")

            if selector_type == "XPATH":
                elements = driver.find_elements(By.XPATH, selector)
            else:  # CSS
                elements = driver.find_elements(By.CSS_SELECTOR, selector)

            logger.info(f"Found {len(elements)} elements with this selector")

            for i, element in enumerate(elements):
                if element.is_displayed():
                    logger.info(f"Element {i} is visible, attempting click...")
                    try:
                        element.click()
                        logger.info(
                            "Click successful! Waiting for page change...")
                        time.sleep(8)

                        current_url = driver.current_url
                        logger.info(f"Current URL after click: {current_url}")

                        if "/accounts/login" not in current_url:
                            logger.info("🎉 LOGIN SUCCESSFUL!")
                            return True
                        else:
                            logger.warning(
                                "Still on login page, trying next selector...")
                            # Navigate back to login page for next attempt
                            driver.get(LOGIN_URL)
                            time.sleep(3)
                            # Re-fill credentials
                            username_field = driver.find_element(
                                By.NAME, "username")
                            username_field.clear()
                            username_field.send_keys(INSTAGRAM_USERNAME)
                            password_field = driver.find_element(
                                By.NAME, "password")
                            password_field.clear()
                            password_field.send_keys(INSTAGRAM_PASSWORD)
                            time.sleep(2)
                            break
                    except Exception as click_err:
                        logger.error(f"Click failed: {click_err}")
                        continue
                else:
                    logger.info(f"Element {i} is not visible")

        except Exception as e:
            logger.error(f"Selector {selector} failed: {e}")
            continue

    # Try Enter key as final fallback
    logger.info("Trying Enter key on password field as final fallback...")
    try:
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(Keys.RETURN)
        time.sleep(8)

        current_url = driver.current_url
        if "/accounts/login" not in current_url:
            logger.info("🎉 LOGIN SUCCESSFUL with Enter key!")
            return True
        else:
            logger.error("❌ All login attempts failed")
            return False
    except Exception as e:
        logger.error(f"Enter key fallback failed: {e}")
        return False


def main():
    """Main test function"""
    logger.info("Starting Instagram login test...")

    driver = setup_driver()
    if not driver:
        logger.error("Could not setup driver")
        return

    try:
        # First analyze the page structure
        analyze_login_page(driver)

        # Wait for user to review the analysis
        input("\nPress Enter to continue with login test...")

        # Then test login
        success = test_login_with_various_selectors(driver)

        if success:
            logger.info("✅ Test completed successfully - login working!")
        else:
            logger.error("❌ Test failed - could not log in")

        input("\nPress Enter to close browser...")

    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
