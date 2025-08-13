from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class ManyChatBot:
    def __init__(self):
        """Initialize the ManyChat bot."""
        # Setup Chrome options with minimal settings
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the driver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            print("Chrome browser opened successfully.")
        except Exception as e:
            print(f"Error opening Chrome: {str(e)}")
            raise
    
    def open_manychat(self):
        """Open ManyChat website and wait for manual login."""
        try:
            # Open ManyChat
            self.driver.get("https://app.manychat.com/")
            print("ManyChat website opened.")
            
            # Ask user to manually complete the login process
            print("\n========== MANUAL LOGIN PROCESS ==========")
            print("Please manually complete the login process:")
            print("1. Click on 'Log in with Facebook'")
            print("2. Enter your Facebook credentials")
            print("3. Handle any 2FA if required")
            print("4. Wait until you are fully logged into ManyChat")
            
            input("\nPress Enter once you've successfully logged in...\n")
            print("Continuing with the bot...")
            return True
                
        except Exception as e:
            print(f"Error during the login process: {str(e)}")
            return False
    
    def select_page(self):
        """Select the page 'Shan | BUILDING AUSTRALIAS BEST RIGS'"""
        try:
            # Wait for page to load after login
            time.sleep(3)
            
            # Find and click on the specified page
            page_span = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Shan | BUILDING AUSTRALIAS BEST RIGS')]"))
            )
            print("Found page. Clicking on it...")
            page_span.click()
            time.sleep(2)
            print("Successfully selected the page.")
            return True
        except Exception as e:
            print(f"Error selecting page: {str(e)}")
            return False
    
    def navigate_to_contacts(self):
        """Navigate to the contacts section"""
        try:
            print("Attempting to navigate to contacts...")
            
            # Direct navigation to the correct URL
            print("Navigating directly to the subscribers page...")
            self.driver.get("https://app.manychat.com/fb996573/subscribers")
            
            # Wait longer for the page to load
            time.sleep(7)
            
            # Check if URL contains subscribers
            current_url = self.driver.current_url
            if "subscribers" in current_url or "contacts" in current_url:
                print("Successfully navigated to contacts section.")
                return True
                
            # If direct navigation didn't work, try the fallback methods
            print("Direct navigation may not have worked, trying alternative methods...")
            
            attempts = [
                # Try clicking on sidebar menu item by text
                lambda: self.try_click_element(By.XPATH, "//span[text()='Contacts' or contains(text(), 'Contacts')]"),
                
                # Try finding by SVG path in sidebar
                lambda: self.try_click_element(By.XPATH, "//div[.//svg/path[contains(@d, 'M12.076')]]"),
                
                # Try by data attributes
                lambda: self.try_click_element(By.CSS_SELECTOR, "[data-test-id='contacts'], [data-test='contacts']"),
                
                # Try by class name that might contain contacts
                lambda: self.try_click_element(By.CSS_SELECTOR, ".contacts-icon, .contact-menu, .contact-link")
            ]
            
            for attempt_num, attempt_func in enumerate(attempts, 1):
                try:
                    print(f"Attempt {attempt_num} to navigate to contacts...")
                    attempt_func()
                    time.sleep(4)  # Give more time to load
                    
                    # Check if we're on the contacts page by looking for common elements
                    current_url = self.driver.current_url
                    if any([
                        "subscribers" in current_url,
                        "contacts" in current_url,
                        self.element_exists(By.XPATH, "//h1[contains(text(), 'Contacts')]"),
                        self.element_exists(By.XPATH, "//div[contains(text(), 'Subscribers') or contains(text(), 'All Contacts')]"),
                        self.element_exists(By.XPATH, "//input[@type='search' or @id='search-box-input']")
                    ]):
                        print("Successfully navigated to contacts section.")
                        return True
                except Exception as e:
                    print(f"Attempt {attempt_num} failed: {str(e)}")
            
            # Check again if we have a search box on the page - if so, we're probably on the contacts page
            if self.element_exists(By.XPATH, "//input[@type='search' or @id='search-box-input']"):
                print("Search box found, we're on the contacts page.")
                return True
            
            # If all attempts fail, ask the user to navigate manually
            print("\n========== MANUAL NAVIGATION NEEDED ==========")
            print("Could not automatically navigate to contacts.")
            print("Please navigate to the Contacts section manually.")
            input("Press Enter once you've navigated to the Contacts section...\n")
            print("Continuing with the bot...")
            return True
                
        except Exception as e:
            print(f"Error navigating to contacts: {str(e)}")
            return False
            
    def element_exists(self, by, selector):
        """Check if an element exists on the page"""
        try:
            self.driver.find_element(by, selector)
            return True
        except:
            return False
            
    def try_click_element(self, by, selector):
        """Try to find and click an element"""
        element = self.wait.until(EC.element_to_be_clickable((by, selector)))
        element.click()
        return True
    
    def find_and_tag_clients(self, client_list):
        """Find specific clients using search, select them, and add the 'check ins' tag"""
        try:
            print(f"Will search for these clients: {client_list}")
            selected_count = 0
            
            # Wait for contacts list to load
            time.sleep(5)
            
            # For each client in the list
            for client in client_list:
                try:
                    print(f"Searching for client: {client}")
                    
                    # Try multiple selectors for the search input
                    search_selectors = [
                        # Exact selector from your page
                        "//div[contains(@class, 'searchBoxLabel')]//input[@type='search' and @id='search-box-input']",
                        "//input[@id='search-box-input']",
                        "//input[@type='search']",
                        "//input[@role='searchbox']"
                    ]
                    
                    # Try each selector until one works
                    search_box = None
                    for selector in search_selectors:
                        try:
                            print(f"Trying to find search box with: {selector}")
                            search_box = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if search_box:
                                print("Found search box!")
                                break
                        except:
                            continue
                    
                    if not search_box:
                        print("Could not find search box. Please check the page layout.")
                        raise Exception("Search box not found")
                    
                    # Clear any existing search
                    search_box.clear()
                    
                    # Enter client name in search box
                    search_box.click()
                    time.sleep(1)
                    search_box.send_keys(client)
                    time.sleep(1)
                    search_box.send_keys(Keys.ENTER)
                    
                    # Wait for search results
                    print(f"Searching for '{client}'...")
                    time.sleep(3)
                    
                    # Try to find and click the checkbox for this client
                    try:
                        # First try to find by checkbox near client name
                        checkbox_selectors = [
                            f"//div[contains(text(), '{client}')]/ancestor::tr//input[@type='checkbox']",
                            "//input[@type='checkbox' and contains(@class, 'checkboxV2')]",
                            "//input[@type='checkbox']"
                        ]
                        
                        checkbox = None
                        for selector in checkbox_selectors:
                            try:
                                checkbox = self.driver.find_element(By.XPATH, selector)
                                if checkbox:
                                    print(f"Found checkbox for {client} using: {selector}")
                                    break
                            except:
                                continue
                        
                        if checkbox:
                            checkbox.click()
                            print(f"Selected client: {client}")
                            selected_count += 1
                            time.sleep(1)
                        else:
                            print(f"Could not find checkbox for client: {client}")
                    except Exception as e:
                        print(f"Error selecting checkbox for {client}: {str(e)}")
                
                except Exception as e:
                    print(f"Error searching for client {client}: {str(e)}")
            
            print(f"Successfully selected {selected_count} out of {len(client_list)} clients.")
            
            if selected_count > 0:
                # Click on Bulk Actions
                bulk_actions = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Bulk Actions')]"))
                )
                print("Clicking Bulk Actions...")
                bulk_actions.click()
                time.sleep(1)
                
                # Click on Add Tag
                add_tag = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Add Tag')]"))
                )
                print("Clicking Add Tag...")
                add_tag.click()
                time.sleep(1)
                
                # Find the tag input and enter "check ins"
                tag_input = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='text' and @autocomplete='off']"))
                )
                print("Entering tag: check ins")
                tag_input.click()
                tag_input.send_keys("check ins")
                tag_input.send_keys(Keys.ENTER)
                time.sleep(1)
                
                # Click Save
                save_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Save')]"))
                )
                print("Clicking Save...")
                save_button.click()
                time.sleep(1)
                
                # Click Confirm
                confirm_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Confirm')]"))
                )
                print("Clicking Confirm...")
                confirm_button.click()
                time.sleep(1)
                
                # Click Close
                close_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Close')]"))
                )
                print("Clicking Close...")
                close_button.click()
                
                print("Successfully added 'check ins' tag to selected clients.")
            
            return selected_count > 0
            
        except Exception as e:
            print(f"Error in find_and_tag_clients: {str(e)}")
            return False
    
    def close(self):
        """Close the browser."""
        try:
            self.driver.quit()
            print("Browser closed.")
        except:
            print("Browser was already closed or could not be closed.")


if __name__ == "__main__":
    print("Starting ManyChat Client Tagging Bot...")
    bot = None
    
    # List of clients to tag - can be modified as needed
    clients_to_tag = [
        "wegirlsdontcry",
        "Luxcompassion",
        "n_tiwari094",
        "kelstar",
        "Ona.taste_buddies"
    ]
    
    try:
        bot = ManyChatBot()
        
        # Step 1: Open ManyChat and wait for manual login
        if bot.open_manychat():
            
            # Step 2: Select the page
            if bot.select_page():
                
                # Step 3: Navigate to contacts
                if bot.navigate_to_contacts():
                    
                    # Step 4: Find and tag clients
                    success = bot.find_and_tag_clients(clients_to_tag)
                    
                    if success:
                        print("\nAll actions completed successfully!")
                    else:
                        print("\nSome actions could not be completed.")
                
            # Ask if user wants to keep the browser open
            while True:
                action = input("\nType 'exit' to close the browser, or press Enter to keep it open: ")
                if action.lower() == 'exit':
                    break
                print("Browser still running...")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        if bot:
            bot.close()