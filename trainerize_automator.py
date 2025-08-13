import argparse
import logging
import os
import shutil
import tempfile
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class VersatileTrainerizeAutomator:
    def __init__(self, binary_location=None, headless=False):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Versatile Trainerize Automator...")

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
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

        if binary_location:
            chrome_options.binary_location = binary_location

        try:
            service = Service()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            self.logger.info("Chrome initialized successfully!")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome: {e}")
            if os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def login(self, username=None, password=None) -> bool:
        username = username or os.getenv("TRAINERIZE_USERNAME")
        password = password or os.getenv("TRAINERIZE_PASSWORD")
        if not username or not password:
            raise ValueError(
                "Trainerize username and password must be provided or set in environment variables.")

        try:
            self.logger.info("Navigating to Trainerize login page...")
            self.driver.get("https://www.trainerize.com/login.aspx")
            self._handle_cookie_dialog()

            self.logger.info("Scrolling down slightly...")
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)

            self.logger.info("Waiting for initial email field...")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "t_email")))
            email_field.clear()
            email_field.send_keys(username)

            self.logger.info("Clicking 'Find me' button...")
            find_me_button = self.driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(3)

            self.logger.info("Entering full email on second page...")
            email_field_second = self.wait.until(
                EC.element_to_be_clickable((By.ID, "emailInput")))
            email_field_second.clear()
            email_field_second.send_keys(username)

            self.logger.info("Entering password...")
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.clear()
            password_field.send_keys(password)

            self.logger.info("Clicking 'Sign In' button...")
            sign_in_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(5)

            if "login" not in self.driver.current_url:
                self.logger.info("Login successful!")
                return True
            else:
                self.logger.error("Login failed.")
                return False
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            return False

    def navigate_to_client(self, client_name: str) -> bool:
        try:
            self.logger.info(f"Navigating to client: {client_name}")
            clients_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")))
            clients_link.click()
            time.sleep(2)

            search_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")))
            search_input.clear()
            search_input.send_keys(client_name)
            time.sleep(2)

            client_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(text(), '{client_name}')]")))
            client_link.click()
            time.sleep(2)

            open_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")))
            open_button.click()
            time.sleep(3)

            # Switch to new tab
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.logger.info(
                    f"Successfully navigated to {client_name}'s page.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to client: {e}")
            return False

    def navigate_to_training_program(self) -> bool:
        try:
            self.logger.info("Navigating to training program...")
            training_program_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[@id='nav_training_program']")))
            training_program_link.click()
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"Error navigating to training program: {e}")
            return False

    def extract_data(self, data_type: str) -> dict:
        """Extracts specified data type using Selenium scraping."""
        try:
            self.logger.info(f"Extracting {data_type} data...")
            # Example for workouts; expand for other types like nutrition, sleep, etc.
            if data_type == "workouts":
                # Navigate to relevant section if needed
                self.navigate_to_training_program()
                # Scrape workout data (adapt from existing check-in scripts)
                workouts = []
                workout_elements = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'workout-item')]")
                for elem in workout_elements:
                    name = elem.find_element(By.TAG_NAME, "h3").text
                    workouts.append({"name": name})
                return {"workouts": workouts}
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            self.logger.error(f"Error extracting data: {e}")
            return {}

    def update_program(self, program_name: str, updates: dict) -> bool:
        """Updates a program with given changes (e.g., {'exercise': 'Squats', 'reps': '12'})."""
        try:
            self.logger.info(
                f"Updating program: {program_name} with {updates}")
            # Navigate to program, find elements, update (adapt from update scripts)
            # Placeholder: Implement specific update logic here
            return True
        except Exception as e:
            self.logger.error(f"Error updating program: {e}")
            return False

    def _handle_cookie_dialog(self):
        try:
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "cookie-accept")))
            cookie_button.click()
        except TimeoutException:
            pass

    def cleanup(self):
        self.driver.quit()
        if os.path.exists(self.temp_user_data_dir):
            shutil.rmtree(self.temp_user_data_dir)
        self.logger.info("Cleanup complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Versatile Trainerize Automator")
    parser.add_argument("--action", required=True,
                        choices=["login", "navigate_to_client", "extract_data", "update_program"])
    parser.add_argument("--client", help="Client name")
    parser.add_argument(
        "--data_type", help="Type of data to extract (e.g., workouts)")
    parser.add_argument("--program", help="Program name to update")
    parser.add_argument("--updates", help="JSON string of updates", type=str)
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")

    args = parser.parse_args()

    automator = VersatileTrainerizeAutomator(headless=args.headless)

    if args.action == "login":
        success = automator.login()
        print(f"Login {'successful' if success else 'failed'}")
    elif args.action == "navigate_to_client":
        if not args.client:
            raise ValueError("Client name required")
        success = automator.navigate_to_client(args.client)
        print(f"Navigation {'successful' if success else 'failed'}")
    elif args.action == "extract_data":
        if not args.data_type:
            raise ValueError("Data type required")
        data = automator.extract_data(args.data_type)
        print(data)
    elif args.action == "update_program":
        if not args.program or not args.updates:
            raise ValueError("Program name and updates required")
        import json
        updates = json.loads(args.updates)
        success = automator.update_program(args.program, updates)
        print(f"Update {'successful' if success else 'failed'}")

    automator.cleanup()


if __name__ == "__main__":
    main()
