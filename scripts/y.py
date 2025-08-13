from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from time import sleep
import random
import logging
import os

# Configure logging
logging.basicConfig(
    filename='instagram_bot.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Instagram credentials
USERNAME = "cocos_pt_studio"
PASSWORD = "Shannonb3"

# ChromeDriver path
CHROMEDRIVER_PATH = "/mnt/c/SeleniumDrivers/chromedriver-win64/chromedriver.exe"

# Validate ChromeDriver path
if not os.path.isfile(CHROMEDRIVER_PATH):
    print(f"Error: ChromeDriver not found at {CHROMEDRIVER_PATH}")
    logging.error(f"ChromeDriver not found at {CHROMEDRIVER_PATH}. Please verify the path.")
    exit("Exiting script due to missing ChromeDriver.")

# Initialize ChromeDriver
try:
    print(f"Initializing ChromeDriver at: {CHROMEDRIVER_PATH}")
    service = Service(CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("ChromeDriver initialized successfully.")
except WebDriverException as e:
    print(f"Error initializing ChromeDriver: {e}")
    logging.error(f"Error initializing ChromeDriver: {e}")
    exit("Exiting script due to ChromeDriver initialization error.")

def login(driver, username, password):
    """Logs into Instagram using the provided credentials."""
    try:
        driver.get("https://www.instagram.com")
        print("Opening Instagram...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        print("Logging in...")
        sleep(5)

        # Dismiss "Save Your Login Info?" dialog
        try:
            not_now_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn.click()
            sleep(2)
        except TimeoutException:
            pass

        # Dismiss "Turn on Notifications?" dialog
        try:
            not_now_btn_2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_btn_2.click()
            sleep(2)
        except TimeoutException:
            pass

    except TimeoutException:
        print("Error: Login failed.")
        logging.error("Login failed due to timeout.")
        driver.quit()
        exit("Exiting script due to login failure.")

def navigate_to_followers(driver):
    """Navigates to the user's followers list."""
    try:
        # Add your logic for navigating to the followers list
        pass
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Error navigating to followers: {e}")
        driver.quit()
        exit("Exiting script due to navigation error.")

def main():
    print("Step 1: Logging in...")
    login(driver, USERNAME, PASSWORD)

    print("Step 2: Navigating to Followers...")
    navigate_to_followers(driver)

    print("Script finished. Press Enter to close the browser...")
    input()
    driver.quit()

if __name__ == "__main__":
    main()
