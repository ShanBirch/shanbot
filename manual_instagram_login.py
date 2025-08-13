"""
Manual Instagram Login Helper
Use this when the automated login fails and you need to login manually.
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manual_login")

CHROME_DRIVER_PATH = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"


def manual_login_helper():
    """Open Instagram in a browser for manual login and bio testing"""

    print("🔧 Instagram Manual Login Helper")
    print("="*50)
    print("This will open Instagram in a browser window.")
    print("You can then login manually and test bio fetching.")
    print()

    # Setup browser
    chrome_options = Options()
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Keep browser visible for manual interaction
    chrome_options.add_argument("--window-size=1200,800")

    try:
        service = webdriver.chrome.service.Service(
            executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute stealth script
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
        driver.execute_script(stealth_script)

        # Go to Instagram login
        print("🌐 Opening Instagram login page...")
        driver.get("https://www.instagram.com/accounts/login/")

        print()
        print("👤 MANUAL LOGIN INSTRUCTIONS:")
        print("1. Complete the login process in the browser window")
        print("2. Handle any 2FA if required")
        print("3. Once logged in, press ENTER here to continue")
        print("4. The system will then test bio fetching")
        print()

        # Wait for user to complete login
        input("Press ENTER after you've successfully logged in to Instagram...")

        # Verify login success
        current_url = driver.current_url.lower()
        if "login" not in current_url:
            print("✅ Login appears successful!")

            # Test bio fetching
            test_usernames = ["danielle_emily_ruth",
                              "the.health.formula", "jesslyn_music"]

            print(
                f"\n🧪 Testing bio fetching on {len(test_usernames)} profiles...")

            for username in test_usernames:
                print(f"\n--- Testing: {username} ---")

                try:
                    profile_url = f"https://www.instagram.com/{username}/"
                    driver.get(profile_url)
                    time.sleep(3)

                    # Get basic profile info
                    print(f"URL: {driver.current_url}")

                    try:
                        # Try to get full name
                        name_element = driver.find_element(
                            By.CSS_SELECTOR, "h1")
                        full_name = name_element.text.strip()
                        print(f"Full Name: {full_name}")
                    except:
                        print("Full Name: Not found")

                    try:
                        # Try to get bio
                        bio_elements = driver.find_elements(
                            By.CSS_SELECTOR, "h1 + div, h1 + span")
                        bio_found = False
                        for element in bio_elements:
                            text = element.text.strip()
                            if text and len(text) > 5:
                                print(f"Bio: {text[:100]}...")
                                bio_found = True
                                break
                        if not bio_found:
                            print("Bio: Not found")
                    except:
                        print("Bio: Error accessing")

                    try:
                        # Check if private
                        private_indicators = driver.find_elements(
                            By.XPATH, "//h2[contains(text(), 'Private')]")
                        if private_indicators:
                            print("Status: Private profile")
                        else:
                            print("Status: Public profile")
                    except:
                        print("Status: Unknown")

                except Exception as e:
                    print(f"Error fetching {username}: {e}")

                time.sleep(2)

            print("\n✅ Bio fetching test complete!")

        else:
            print("❌ Login was not successful. Please try again.")

        print("\nPress ENTER to close the browser...")
        input()

    except Exception as e:
        print(f"❌ Error during manual login: {e}")

    finally:
        try:
            driver.quit()
            print("🔒 Browser closed.")
        except:
            pass


if __name__ == "__main__":
    manual_login_helper()
