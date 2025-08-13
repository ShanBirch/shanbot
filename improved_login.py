"""
IMPROVED INSTAGRAM LOGIN - Updated for current Instagram interface
This addresses common login issues with the story1.py script
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import os


def setup_improved_driver():
    """Setup Chrome driver with enhanced anti-detection measures"""
    service = Service(
        executable_path=r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe")
    chrome_options = Options()

    # Enhanced anti-detection measures
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en-US")

    # Use a more realistic user agent
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Window size to avoid mobile layout
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Advanced anti-detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        window.chrome = {
            runtime: {}
        };
        """
    })

    return driver


def find_login_field_improved(driver, field_type):
    """Find login fields with updated selectors for current Instagram"""

    if field_type == "username":
        # Updated selectors for username field (Dec 2024)
        selectors = [
            "//input[@name='username']",
            "//input[@aria-label='Phone number, username, or email']",
            "//input[@placeholder='Phone number, username, or email']",
            "//input[@autocomplete='username']",
            "//input[@type='text' and contains(@class, '_aa4b')]",
            "//input[@type='text' and contains(@class, 'x1i10hfl')]",
            "//form//input[@type='text'][1]",
            "//article//input[@type='text']",
            "//div[@role='main']//input[@type='text']",
            "//input[contains(@class, '_2hvTZ')]",  # Updated class
            "//input[contains(@class, 'pexuQ')]",   # Updated class
        ]
    else:  # password
        # Updated selectors for password field (Dec 2024)
        selectors = [
            "//input[@name='password']",
            "//input[@aria-label='Password']",
            "//input[@type='password']",
            "//input[@type='password' and contains(@class, '_aa4b')]",
            "//input[@type='password' and contains(@class, 'x1i10hfl')]",
            "//form//input[@type='password']",
            "//article//input[@type='password']",
            "//div[@role='main']//input[@type='password']",
            # Updated class
            "//input[contains(@class, '_2hvTZ') and @type='password']",
            # Updated class
            "//input[contains(@class, 'pexuQ') and @type='password']",
        ]

    print(f"Looking for {field_type} field with {len(selectors)} selectors...")

    for i, selector in enumerate(selectors, 1):
        try:
            print(f"  Trying selector {i}: {selector}")
            elements = driver.find_elements(By.XPATH, selector)

            if elements:
                print(f"    Found {len(elements)} element(s)")
                for j, element in enumerate(elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            print(
                                f"    ✅ Element {j+1} is visible and enabled")
                            return element
                        else:
                            print(f"    ❌ Element {j+1} not visible/enabled")
                    except Exception as e:
                        print(f"    ❌ Error checking element {j+1}: {e}")
            else:
                print(f"    ❌ No elements found")

        except Exception as e:
            print(f"    ❌ Selector {i} failed: {e}")

    return None


def find_login_button_improved(driver):
    """Find login button with updated selectors"""

    # Updated selectors for login button (Dec 2024)
    selectors = [
        "//button[@type='submit']",
        "//button[contains(text(), 'Log in')]",
        "//button[contains(text(), 'Log In')]",
        "//button[contains(text(), 'LOGIN')]",
        "//button[contains(@class, '_acan')]",
        "//button[contains(@class, '_acap')]",
        "//div[@role='button' and contains(text(), 'Log in')]",
        "//input[@type='submit']",
        "//form//button[contains(@class, '_a9_')]",
        "//form//button[contains(@class, 'sqdOP')]",
        "//button[contains(@class, 'L3NKy')]",
        "//form//button[last()]",
        "//article//button[@type='submit']",
        # New class combo
        "//button[contains(@class, '_acan') and contains(@class, '_acao')]",
        # New class
        "//button[contains(@class, 'x1i10hfl') and @type='submit']",
        # New container class
        "//div[contains(@class, '_ac69')]//button",
    ]

    print(f"Looking for login button with {len(selectors)} selectors...")

    for i, selector in enumerate(selectors, 1):
        try:
            print(f"  Trying selector {i}: {selector}")
            elements = driver.find_elements(By.XPATH, selector)

            if elements:
                print(f"    Found {len(elements)} element(s)")
                for j, element in enumerate(elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            print(f"    ✅ Button {j+1} is visible and enabled")
                            return element
                        else:
                            print(f"    ❌ Button {j+1} not visible/enabled")
                    except Exception as e:
                        print(f"    ❌ Error checking button {j+1}: {e}")
            else:
                print(f"    ❌ No buttons found")

        except Exception as e:
            print(f"    ❌ Selector {i} failed: {e}")

    return None


def check_if_logged_in_improved(driver):
    """Check if already logged in with updated indicators"""

    # Updated indicators for being logged in (Dec 2024)
    indicators = [
        "//a[@href='/']",
        "//div[@role='tablist']",
        "//svg[@aria-label='Home']",
        "//a[contains(@href, '/direct/')]",
        "//span[text()='Home']",
        "//nav//a[@href='/']",
        "//header//a[@href='/']",
        "//div[contains(@class, 'x1iyjqo2')]//a[@href='/']",
        "//svg[@aria-label='New post']",  # Create post icon
        "//svg[@aria-label='Activity feed']",  # Notifications icon
        "//div[contains(@class, '_ac8k')]",  # New nav class
        "//div[contains(@class, '_ab8w')]",  # New nav container
    ]

    print("Checking if already logged in...")

    for i, indicator in enumerate(indicators, 1):
        try:
            elements = driver.find_elements(By.XPATH, indicator)
            if elements and any(el.is_displayed() for el in elements):
                print(f"✅ Found login indicator {i}: {indicator}")
                return True
        except:
            continue

    # Also check URL
    current_url = driver.current_url.lower()
    if 'login' not in current_url and 'accounts' not in current_url and 'instagram.com' in current_url:
        print("✅ URL indicates logged in status")
        return True

    print("❌ Not logged in")
    return False


def check_for_errors_improved(driver):
    """Check for login errors with updated selectors"""

    error_selectors = [
        "//div[contains(@class, 'piCib')]",
        "//p[contains(@class, 'piCib')]",
        "//div[contains(text(), 'incorrect') or contains(text(), 'wrong')]",
        "//div[contains(text(), 'Sorry')]",
        "//div[@role='alert']",
        "//div[contains(@class, '_ab2z')]",  # New error class
        "//div[contains(@class, '_ac69') and contains(text(), 'Sorry')]",
        "//span[contains(text(), 'try again')]",
        "//div[contains(@id, 'loginForm')]//div[contains(@class, 'error')]",
    ]

    for selector in error_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    error_text = element.text.strip()
                    if error_text and any(keyword in error_text.lower()
                                          for keyword in ['incorrect', 'wrong', 'error', 'sorry', 'try again']):
                        print(f"❌ Login error detected: {error_text}")
                        return True
        except:
            continue

    return False


def improved_instagram_login(username, password):
    """Improved Instagram login with better error handling"""

    driver = setup_improved_driver()
    max_attempts = 3

    try:
        for attempt in range(max_attempts):
            print(f"\n🔐 LOGIN ATTEMPT {attempt + 1}/{max_attempts}")
            print("=" * 50)

            # Step 1: Navigate to login page
            print("1. Navigating to Instagram login page...")
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(random.uniform(3, 5))

            # Take screenshot for debugging
            driver.save_screenshot(
                f"login_attempt_{attempt+1}_page_loaded.png")
            print(
                f"   📸 Screenshot: login_attempt_{attempt+1}_page_loaded.png")

            # Step 2: Check if already logged in
            if check_if_logged_in_improved(driver):
                print("✅ Already logged in!")
                return driver, True

            # Step 3: Handle cookies/privacy notices
            try:
                cookie_buttons = [
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Accept All')]",
                    "//button[contains(text(), 'Allow')]",
                    "//button[contains(text(), 'OK')]",
                ]

                for cookie_selector in cookie_buttons:
                    try:
                        cookie_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, cookie_selector))
                        )
                        if cookie_btn.is_displayed():
                            cookie_btn.click()
                            print("✅ Handled cookie/privacy notice")
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                pass

            # Step 4: Find username field
            print("\n2. Finding username field...")
            username_field = find_login_field_improved(driver, "username")

            if not username_field:
                print("❌ Could not find username field")
                driver.save_screenshot(
                    f"login_attempt_{attempt+1}_no_username.png")
                if attempt < max_attempts - 1:
                    continue
                return driver, False

            # Step 5: Find password field
            print("\n3. Finding password field...")
            password_field = find_login_field_improved(driver, "password")

            if not password_field:
                print("❌ Could not find password field")
                driver.save_screenshot(
                    f"login_attempt_{attempt+1}_no_password.png")
                if attempt < max_attempts - 1:
                    continue
                return driver, False

            # Step 6: Find login button
            print("\n4. Finding login button...")
            login_button = find_login_button_improved(driver)

            if not login_button:
                print("❌ Could not find login button")
                driver.save_screenshot(
                    f"login_attempt_{attempt+1}_no_button.png")
                if attempt < max_attempts - 1:
                    continue
                return driver, False

            # Step 7: Fill credentials
            print("\n5. Filling credentials...")

            # Clear and fill username with human-like typing
            username_field.clear()
            time.sleep(random.uniform(0.5, 1.0))

            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(random.uniform(0.8, 1.5))

            # Clear and fill password
            password_field.clear()
            time.sleep(random.uniform(0.5, 1.0))

            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(random.uniform(1.0, 2.0))

            # Step 8: Click login button
            print("\n6. Clicking login button...")

            # Try different click methods
            click_success = False
            click_methods = [
                lambda: login_button.click(),
                lambda: driver.execute_script(
                    "arguments[0].click();", login_button),
                lambda: ActionChains(driver).move_to_element(
                    login_button).click().perform()
            ]

            for i, click_method in enumerate(click_methods, 1):
                try:
                    print(f"   Trying click method {i}...")
                    click_method()
                    click_success = True
                    break
                except Exception as e:
                    print(f"   Click method {i} failed: {e}")

            if not click_success:
                print("❌ All click methods failed")
                if attempt < max_attempts - 1:
                    continue
                return driver, False

            # Step 9: Wait for response
            print("\n7. Waiting for login response...")
            time.sleep(random.uniform(3, 5))

            # Check for immediate errors
            if check_for_errors_improved(driver):
                print("❌ Login error detected immediately")
                driver.save_screenshot(f"login_attempt_{attempt+1}_error.png")
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(3, 5))
                    continue
                return driver, False

            # Step 10: Wait for login completion
            print("8. Checking login status...")
            max_wait = 30
            start_time = time.time()

            while time.time() - start_time < max_wait:
                if check_if_logged_in_improved(driver):
                    print("✅ LOGIN SUCCESSFUL!")
                    driver.save_screenshot(f"login_success_{attempt+1}.png")

                    # Handle post-login dialogs
                    try:
                        post_login_dialogs = [
                            "//button[contains(text(), 'Not Now')]",
                            "//button[contains(text(), 'Save Info')]//following-sibling::button",
                            "//button[contains(text(), 'Turn on Notifications')]//following-sibling::button"
                        ]

                        for dialog_selector in post_login_dialogs:
                            try:
                                dialog_btn = WebDriverWait(driver, 2).until(
                                    EC.element_to_be_clickable(
                                        (By.XPATH, dialog_selector))
                                )
                                if dialog_btn.is_displayed():
                                    dialog_btn.click()
                                    print("✅ Handled post-login dialog")
                                    time.sleep(1)
                            except:
                                continue
                    except:
                        pass

                    return driver, True

                # Check for errors during wait
                if check_for_errors_improved(driver):
                    print("❌ Login error during wait")
                    break

                time.sleep(1)

            print(f"❌ Login timeout on attempt {attempt + 1}")
            driver.save_screenshot(f"login_timeout_{attempt+1}.png")

            if attempt < max_attempts - 1:
                time.sleep(random.uniform(2, 4))

        print("❌ All login attempts failed")
        return driver, False

    except Exception as e:
        print(f"❌ Critical error during login: {e}")
        driver.save_screenshot("login_critical_error.png")
        return driver, False


def test_improved_login():
    """Test the improved login function"""

    # REPLACE THESE WITH YOUR ACTUAL CREDENTIALS
    USERNAME = "cocos_pt_studio"  # Your Instagram username
    PASSWORD = "Shannonb3"        # Your Instagram password

    print("🚀 TESTING IMPROVED INSTAGRAM LOGIN")
    print("=" * 60)

    driver, success = improved_instagram_login(USERNAME, PASSWORD)

    if success:
        print("\n✅ LOGIN TEST SUCCESSFUL!")
        print("You can now integrate this improved login into your story1.py")

        # Wait for user to see result
        input("\nPress Enter to close browser...")
    else:
        print("\n❌ LOGIN TEST FAILED")
        print("Check the screenshots for debugging information:")
        for f in os.listdir("."):
            if f.startswith("login_") and f.endswith(".png"):
                print(f"  - {f}")

    driver.quit()


if __name__ == "__main__":
    test_improved_login()
