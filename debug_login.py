from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random


def setup_debug_driver():
    """Setup Chrome driver with debugging enabled"""
    service = Service(
        executable_path=r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe")
    chrome_options = Options()

    # Add debugging flags
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--lang=en-US")

    # Keep browser window visible for debugging
    # chrome_options.add_argument("--headless")  # Comment this out to see what's happening

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Anti-detection script
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    })

    return driver


def debug_instagram_login():
    """Debug Instagram login process step by step"""
    driver = setup_debug_driver()

    try:
        print("🔍 DEBUGGING INSTAGRAM LOGIN")
        print("=" * 50)

        # Step 1: Navigate to Instagram
        print("1. Navigating to Instagram login page...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        print(f"   Current URL: {driver.current_url}")
        print(f"   Page title: {driver.title}")

        # Step 2: Take screenshot to see what's on screen
        driver.save_screenshot("debug_step1_page_loaded.png")
        print("   📸 Screenshot saved: debug_step1_page_loaded.png")

        # Step 3: Look for username field
        print("\n2. Looking for username field...")
        username_selectors = [
            "//input[@name='username']",
            "//input[@aria-label='Phone number, username, or email']",
            "//input[@placeholder='Phone number, username, or email']",
            "//input[@placeholder='Username']",
            "//input[@type='text' and contains(@class, '_aa4b')]",
            "//input[contains(@class, '_aa4b') and @type='text']",
            "//input[@autocomplete='username']",
            "//form//input[@type='text'][1]"
        ]

        username_field = None
        for i, selector in enumerate(username_selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    username_field = elements[0]
                    print(
                        f"   ✅ Found username field with selector #{i+1}: {selector}")
                    break
                else:
                    print(
                        f"   ❌ Selector #{i+1} found {len(elements)} elements but none visible")
            except Exception as e:
                print(f"   ❌ Selector #{i+1} failed: {e}")

        if not username_field:
            print("   🚨 NO USERNAME FIELD FOUND!")
            driver.save_screenshot("debug_no_username_field.png")
            print("   📸 Screenshot saved: debug_no_username_field.png")

            # Print page source for debugging
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("   📝 Page source saved: debug_page_source.html")
            return

        # Step 4: Look for password field
        print("\n3. Looking for password field...")
        password_selectors = [
            "//input[@name='password']",
            "//input[@aria-label='Password']",
            "//input[@placeholder='Password']",
            "//input[@type='password']",
            "//input[contains(@class, '_aa4b') and @type='password']",
            "//form//input[@type='password']"
        ]

        password_field = None
        for i, selector in enumerate(password_selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    password_field = elements[0]
                    print(
                        f"   ✅ Found password field with selector #{i+1}: {selector}")
                    break
                else:
                    print(
                        f"   ❌ Selector #{i+1} found {len(elements)} elements but none visible")
            except Exception as e:
                print(f"   ❌ Selector #{i+1} failed: {e}")

        if not password_field:
            print("   🚨 NO PASSWORD FIELD FOUND!")
            driver.save_screenshot("debug_no_password_field.png")
            return

        # Step 5: Look for login button
        print("\n4. Looking for login button...")
        button_selectors = [
            "//button[@type='submit']",
            "//button[contains(text(), 'Log in') or contains(text(), 'Log In') or contains(text(), 'LOGIN')]",
            "//button[contains(@class, '_acan') and contains(@class, '_acap')]",
            "//button[contains(@class, '_acan')]",
            "//div[@role='button' and contains(text(), 'Log in')]",
            "//input[@type='submit']",
            "//form//button[contains(@class, '_a9_')]",
            "//form//button[last()]"
        ]

        login_button = None
        for i, selector in enumerate(button_selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    login_button = elements[0]
                    print(
                        f"   ✅ Found login button with selector #{i+1}: {selector}")
                    break
                else:
                    print(
                        f"   ❌ Selector #{i+1} found {len(elements)} elements but none visible")
            except Exception as e:
                print(f"   ❌ Selector #{i+1} failed: {e}")

        if not login_button:
            print("   🚨 NO LOGIN BUTTON FOUND!")
            driver.save_screenshot("debug_no_login_button.png")
            return

        # Step 6: Test filling in credentials (use dummy data for testing)
        print("\n5. Testing credential input...")
        test_username = "test_user"  # Replace with your actual username for real test
        test_password = "test_pass"  # Replace with your actual password for real test

        print("   📝 Note: Using dummy credentials for testing. Replace with real ones.")
        print("   Would you like to continue with real credentials? (y/n)")

        # For debugging, we'll stop here to avoid actual login attempts
        print("\n✅ FIELD DETECTION COMPLETE!")
        print("   - Username field: FOUND")
        print("   - Password field: FOUND")
        print("   - Login button: FOUND")
        print(
            "\nTo complete login test, update the credentials in the script and run again.")

        driver.save_screenshot("debug_fields_found.png")
        print("📸 Final screenshot saved: debug_fields_found.png")

    except Exception as e:
        print(f"🚨 ERROR: {e}")
        driver.save_screenshot("debug_error.png")
        print("📸 Error screenshot saved: debug_error.png")

    finally:
        print("\nPress Enter to close browser...")
        input()
        driver.quit()


if __name__ == "__main__":
    debug_instagram_login()
