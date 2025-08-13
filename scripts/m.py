from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Define your Instagram login credentials
username = "cocos_pt_studio"
password = "Shannonb3"

# Configure mobile emulation for Chrome
mobile_emulation = {"deviceName": "iPhone X"}
chrome_options = Options()
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Open Instagram login page
    print("Opening Instagram login page...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    # Locate and fill login fields
    print("Logging in...")
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "password"))
    )
    username_input.send_keys(username)
    password_input.send_keys(password)

    login_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
    )
    login_button.click()
    time.sleep(10)

    # Navigate to the Instagram feed
    print("Navigating to feed...")
    driver.get("https://www.instagram.com/")
    time.sleep(5)

    # Scroll and comment on posts
    print("Starting to scroll and comment...")
    for _ in range(5):  # Adjust the range to control how many scrolls
        # Locate posts
        posts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//article//a"))
        )
        
        for post in posts:
            try:
                # Open the post
                post.click()
                time.sleep(5)

                # Locate comment box and add a comment
                print("Adding a comment...")
                comment_box = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//textarea[contains(@aria-label, 'Add a comment')]"))
                )
                comment_box.click()
                comment_box.send_keys("Awesome post! 👏 Keep it up! 💪")
                time.sleep(2)

                # Post the comment
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Post']"))
                )
                post_button.click()
                print("Comment added successfully!")
                time.sleep(5)

                # Close the post
                close_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Close')]"))
                )
                close_button.click()
                time.sleep(3)

            except Exception as e:
                print(f"Skipping post due to error: {e}")
                # Close the post if it fails
                close_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Close')]")
                close_button.click()
                time.sleep(3)

        # Scroll down to load more posts
        print("Scrolling down...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    input("Press Enter to close the browser...")
    driver.quit()
