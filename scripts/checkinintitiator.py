from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import getpass
import configparser
import os

class ManyChatLoginBot:
    def __init__(self, headless=False):
        """Initialize the ManyChat login bot."""
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def load_credentials(self):
        """This method is no longer used as we wait for manual credential entry."""
        return None, None
        
    def login_to_manychat(self):
        """Navigate to ManyChat and initiate Facebook login."""
        try:
            # Open ManyChat
            self.driver.get("https://app.manychat.com/")
            print("Opening ManyChat...")
            
            # Click on the Facebook login button
            fb_login_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in with Facebook')]"))
            )
            fb_login_btn.click()
            print("Initiating Facebook login...")
            
            # Switch to Facebook login window if needed
            windows = self.driver.window_handles
            if len(windows) > 1:
                self.driver.switch_to.window(windows[1])
            
            # Find email and password fields to confirm the page is loaded
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "pass"))
            )
            
            # Prompt user to enter credentials manually
            print("\n========== MANUAL CREDENTIAL ENTRY ==========")
            print("Please enter your email and password in the browser window.")
            print("You have 60 seconds to enter your credentials and click the login button...")
            
            # Wait for the user to manually enter credentials and click login
            max_wait = 60
            wait_interval = 5
            waited = 0
            
            while waited < max_wait:
                # Check if we've left the login page
                if "login" not in self.driver.current_url:
                    print("Login button clicked. Moving forward...")
                    break
                
                time.sleep(wait_interval)
                waited += wait_interval
                remaining = max_wait - waited
                if remaining > 0:
                    print(f"{remaining} seconds remaining to enter credentials...")
            
            print("Facebook login process continuing...")
            
            # Wait for 2FA prompt if it appears
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'approvals_code')]"))
                )
                print("\n2FA Authentication Required!")
                print("Please check your authentication app or SMS and enter the code below.")
                
                # Give user time to enter 2FA code manually
                print("You have 60 seconds to enter your 2FA code in the browser window...")
                
                # Wait for 2FA completion - either redirection or continuation button
                time.sleep(10)  # Give initial time for user to see dialog
                
                max_wait = 60  # Maximum wait time in seconds
                wait_interval = 5  # Check every 5 seconds
                waited = 0
                
                while waited < max_wait:
                    # Check if we've been redirected to ManyChat already
                    if "manychat.com" in self.driver.current_url and "facebook.com" not in self.driver.current_url:
                        print("Successfully logged in to ManyChat!")
                        break
                    
                    # Check if there's a "Continue" button after 2FA entry
                    try:
                        continue_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue')]")
                        if continue_btn.is_displayed():
                            print("2FA code accepted. Continuing...")
                            continue_btn.click()
                            break
                    except:
                        pass
                    
                    time.sleep(wait_interval)
                    waited += wait_interval
                    remaining = max_wait - waited
                    if remaining > 0:
                        print(f"{remaining} seconds remaining to enter 2FA code...")
            
            except TimeoutException:
                print("No 2FA prompt detected, continuing...")
            
            # Switch back to original window if needed
            if len(windows) > 1:
                self.driver.switch_to.window(windows[0])
            
            # Wait for successful ManyChat login
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard') or contains(@class, 'main-page')]"))
            )
            print("Successfully logged in to ManyChat!")
            return True
            
        except Exception as e:
            print(f"Error during login process: {str(e)}")
            return False
            
    def close(self):
        """Close the browser."""
        self.driver.quit()
        print("Browser closed.")


if __name__ == "__main__":
    bot = ManyChatLoginBot(headless=False)
    try:
        success = bot.login_to_manychat()
        if success:
            print("Login successful! Bot is now ready.")
            input("Press Enter to close the browser when you're done...")
    finally:
        bot.close()