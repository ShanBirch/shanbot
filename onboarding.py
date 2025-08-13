from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging
import tempfile
import shutil
import os
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService


class TrainerizeOnboarding:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome...")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(
            f"--user-data-dir={self.temp_user_data_dir}")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.binary_location = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"

        try:
            service = ChromeService()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Chrome initialized successfully!")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def handle_cookie_dialog(self):
        logging.info(
            "Cookie dialog handling (placeholder - not clicking Accept).")
        time.sleep(2)

    def handle_notification_popup(self):
        try:
            logging.info(
                "Checking for and handling 'Get notifications?' popup...")
            block_button_locator = (
                By.XPATH, "//button[contains(text(), 'Block')]")
            block_button = self.wait.until(
                EC.element_to_be_clickable(block_button_locator))
            block_button.click()
            logging.info("Clicked 'Block' on the notification popup.")
            time.sleep(1)
            return True
        except Exception as e:
            logging.warning(
                f"Notification popup not found or failed to handle: {e}")
            return False

    def login(self, username, password):
        try:
            logging.info("Navigating directly to Trainerize login page...")
            self.driver.get("https://www.trainerize.com/login.aspx")
            self.handle_cookie_dialog()
            logging.info("Scrolling down slightly...")
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
            logging.info("Waiting for page to load...")
            self.wait.until(EC.presence_of_element_located((By.ID, "t_email")))
            logging.info("Entering initial email...")
            email_field = self.driver.find_element(By.ID, "t_email")
            email_field.send_keys(username)
            logging.info("Clicking 'Find me' button...")
            find_me_button = self.driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(2)
            logging.info(
                "Waiting for the *second* email field (emailInput)...")
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "emailInput")))
            logging.info("Entering *full* email on second page...")
            email_field_second = self.driver.find_element(By.ID, "emailInput")
            email_field_second.send_keys(username)
            logging.info("Entering password...")
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.send_keys(password)
            logging.info("Clicking 'Sign In' button...")
            sign_in_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            logging.info("Successfully logged in!")
            return True
        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def navigate_to_add_client(self):
        """Navigate to the Add Client page"""
        try:
            logging.info("Attempting to navigate to Clients page...")
            # Click the Clients link in sidebar
            clients_link_locator = (
                By.XPATH, "//a[@id='nav_clients' and @data-testid='leftNavMenu-item-clients']")
            clients_link = self.wait.until(
                EC.element_to_be_clickable(clients_link_locator))
            clients_link.click()
            logging.info("Clicked Clients link")
            time.sleep(2)

            # Click the New button
            new_button_locator = (
                By.XPATH, "//button[@id='clientGrid__toolbar_addClient' and @data-testid='clientGrid-toolbar-addClient']")
            new_button = self.wait.until(
                EC.element_to_be_clickable(new_button_locator))
            new_button.click()
            logging.info("Clicked New button")
            time.sleep(2)
            return True
        except Exception as e:
            logging.error(f"Error navigating to Add Client page: {e}")
            return False

    def add_new_client(self, email: str, first_name: str, last_name: str):
        """Add a new client with the specified details"""
        try:
            logging.info(
                f"Adding new client: {first_name} {last_name} ({email})")

            # Enter email address
            email_input_locator = (
                By.XPATH, "//input[@data-testid='addClientDialog-emailInput']")
            email_input = self.wait.until(
                EC.presence_of_element_located(email_input_locator))
            email_input.clear()
            email_input.send_keys(email)
            logging.info("Entered email address")
            time.sleep(1)

            # Enter first name
            first_name_input_locator = (
                By.XPATH, "//input[@data-testid='addClientDialog-firstNameInput']")
            first_name_input = self.wait.until(
                EC.presence_of_element_located(first_name_input_locator))
            first_name_input.clear()
            first_name_input.send_keys(first_name)
            logging.info("Entered first name")
            time.sleep(1)

            # Enter last name
            last_name_input_locator = (
                By.XPATH, "//input[@data-testid='addClientDialog-lastNameInput']")
            last_name_input = self.wait.until(
                EC.presence_of_element_located(last_name_input_locator))
            last_name_input.clear()
            last_name_input.send_keys(last_name)
            logging.info("Entered last name")
            time.sleep(1)

            # Click messaging dropdown
            dropdown_locator = (
                By.XPATH, "//span[contains(@class, 'ant-select-arrow')]")
            dropdown = self.wait.until(
                EC.element_to_be_clickable(dropdown_locator))
            dropdown.click()
            logging.info("Clicked messaging dropdown")
            time.sleep(1)

            # Select one-way messaging
            one_way_option_locator = (
                By.XPATH, "//li[contains(text(), 'Full Access 1-way messaging')]")
            one_way_option = self.wait.until(
                EC.element_to_be_clickable(one_way_option_locator))
            one_way_option.click()
            logging.info("Selected one-way messaging")
            time.sleep(1)

            # Click Add and Send Invite button
            add_button_locator = (
                By.XPATH, "//button[@data-testid='dialog-defaultFooter-confirm-button']")
            add_button = self.wait.until(
                EC.element_to_be_clickable(add_button_locator))
            add_button.click()
            logging.info("Clicked Add and Send Invite button")
            time.sleep(2)

            logging.info(
                f"Successfully added new client: {first_name} {last_name}")
            return True

        except Exception as e:
            logging.error(f"Error adding new client: {e}")
            return False

    def verify_client_added(self, email: str, first_name: str, last_name: str) -> bool:
        """Verify that a client was successfully added by checking the clients list"""
        try:
            logging.info(
                f"Verifying client was added: {first_name} {last_name}")

            # Wait for success message first (if still on add client page)
            try:
                success_message_locator = (
                    By.XPATH, "//div[contains(@class, 'ant-message-success')]")
                self.wait.until(
                    EC.presence_of_element_located(success_message_locator))
                logging.info("Success message found")
            except:
                logging.info(
                    "No success message found, continuing verification")

            # Navigate to clients list if not already there
            clients_link_locator = (
                By.XPATH, "//a[@id='nav_clients' and @data-testid='leftNavMenu-item-clients']")
            clients_link = self.wait.until(
                EC.element_to_be_clickable(clients_link_locator))
            clients_link.click()
            logging.info("Navigated to clients list")
            time.sleep(2)

            # Search for the client
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            search_input.clear()
            search_input.send_keys(email)  # Search by email as it's unique
            logging.info(f"Searching for client with email: {email}")
            time.sleep(2)

            # Check if client appears in search results
            client_row_locator = (
                By.XPATH, f"//div[contains(@class, 'clientList')]//a[contains(text(), '{first_name}') and contains(text(), '{last_name}')]")
            try:
                client_row = self.wait.until(
                    EC.presence_of_element_located(client_row_locator))
                logging.info(f"Found client: {first_name} {last_name}")

                # Verify email is also correct
                email_cell = self.driver.find_element(
                    By.XPATH, f"//div[contains(text(), '{email}')]")
                if email_cell:
                    logging.info("Email verified")
                    return True
                else:
                    logging.warning("Email verification failed")
                    return False

            except TimeoutException:
                logging.error(
                    f"Client not found in list: {first_name} {last_name}")
                return False

        except Exception as e:
            logging.error(f"Error verifying client was added: {e}")
            return False

    def cleanup(self):
        """Cleans up resources (removes temp dir, and closes driver)."""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'):
                logging.info("Closing webdriver...")
                self.driver.close()
                self.driver.quit()
                logging.info("Webdriver closed.")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                logging.info(
                    f"Removing temp user data directory: {self.temp_user_data_dir}")
                shutil.rmtree(self.temp_user_data_dir)
                logging.info("Temp directory removed.")
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    # Test client details
    test_client = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }

    onboarding = TrainerizeOnboarding()
    try:
        if onboarding.login(username, password):
            onboarding.handle_notification_popup()

            if onboarding.navigate_to_add_client():
                if onboarding.add_new_client(
                    test_client["email"],
                    test_client["first_name"],
                    test_client["last_name"]
                ):
                    print(f"Client addition attempted. Verifying...")
                    if onboarding.verify_client_added(
                        test_client["email"],
                        test_client["first_name"],
                        test_client["last_name"]
                    ):
                        print(
                            f"Successfully verified client was added: {test_client['first_name']} {test_client['last_name']}")
                    else:
                        print("Failed to verify client was added")
                else:
                    print("Failed to add new client")
            else:
                print("Failed to navigate to add client page")
        else:
            print("Login failed.")

        input("Press Enter to close...")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'onboarding' in locals():
            onboarding.cleanup()
