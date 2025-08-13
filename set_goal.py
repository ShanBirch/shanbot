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


class TrainerizeGoalSetting:
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

    def navigate_to_client(self, client_name):
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")
            logging.info("Clicking the 'Clients' link in the sidebar...")
            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            except TimeoutException as te:
                logging.error(
                    f"TimeoutException while waiting for Clients link: {te.msg}")
                raise
            time.sleep(2)
            logging.info(
                "Entering client name into the search bar on the Clients page...")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            search_input.send_keys(client_name)
            time.sleep(1)
            logging.info(
                "Clicking on the client's name in the search results...")
            client_link_locator = (
                By.XPATH, f"//a[contains(text(), '{client_name}')]")
            client_link = self.wait.until(
                EC.element_to_be_clickable(client_link_locator))
            client_link.click()
            time.sleep(2)
            logging.info(
                "Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(
                EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            logging.info(
                f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True
        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False

    def navigate_to_goals(self):
        """Navigate to the Goals and Habits section"""
        try:
            logging.info("Navigating to Goals and Habits section...")
            goals_link_locator = (
                By.XPATH, "//a[@id='nav_goals_and habits' and @data-testid='leftNavMenu-item-goalsAndHabits']")
            goals_link = self.wait.until(
                EC.element_to_be_clickable(goals_link_locator))
            goals_link.click()
            logging.info("Clicked Goals and Habits link")
            time.sleep(2)
            return True
        except Exception as e:
            logging.error(f"Error navigating to Goals and Habits: {e}")
            return False

    def set_body_weight_goal(self, goal_weight: float, current_weight: float):
        """Set a body weight goal"""
        try:
            logging.info(
                f"Setting body weight goal: {goal_weight} (current: {current_weight})")

            # Click New button
            new_button_locator = (
                By.XPATH, "//button[contains(@class, 'btn--blue') and .//span[contains(., 'New')]]")
            new_button = self.wait.until(
                EC.element_to_be_clickable(new_button_locator))
            new_button.click()
            logging.info("Clicked New button")
            time.sleep(1)

            # Click Fitness Goal
            fitness_goal_locator = (
                By.XPATH, "//p[contains(@class, 'tz-sp') and text()='Fitness Goal']")
            fitness_goal = self.wait.until(
                EC.element_to_be_clickable(fitness_goal_locator))
            fitness_goal.click()
            logging.info("Clicked Fitness Goal")
            time.sleep(1)

            # Click Body Weight Goal
            body_weight_goal_locator = (
                By.XPATH, "//p[contains(@class, 'tz-sp') and text()='Body Weight Goal']")
            body_weight_goal = self.wait.until(
                EC.element_to_be_clickable(body_weight_goal_locator))
            body_weight_goal.click()
            logging.info("Clicked Body Weight Goal")
            time.sleep(1)

            # Enter goal weight
            goal_weight_input_locator = (
                By.ID, "weightGoal__input")
            goal_weight_input = self.wait.until(
                EC.presence_of_element_located(goal_weight_input_locator))
            goal_weight_input.clear()
            goal_weight_input.send_keys(str(goal_weight))
            logging.info(f"Entered goal weight: {goal_weight}")
            time.sleep(1)

            # Enter current weight
            current_weight_input_locator = (
                By.ID, "currentWeight__input")
            current_weight_input = self.wait.until(
                EC.presence_of_element_located(current_weight_input_locator))
            current_weight_input.clear()
            current_weight_input.send_keys(str(current_weight))
            logging.info(f"Entered current weight: {current_weight}")
            time.sleep(1)

            # Click Save Goal button
            save_button_locator = (
                By.XPATH, "//button[@data-testid='dialog-defaultFooter-confirm-button']")
            save_button = self.wait.until(
                EC.element_to_be_clickable(save_button_locator))
            save_button.click()
            logging.info("Clicked Save Goal button")
            time.sleep(2)

            return True
        except Exception as e:
            logging.error(f"Error setting body weight goal: {e}")
            return False

    def set_nutrition_goal(self, target_calories: int):
        """Set a nutrition goal with target calories"""
        try:
            logging.info(
                f"Setting nutrition goal with target calories: {target_calories}")

            # Click New button
            new_button_locator = (
                By.XPATH, "//button[contains(@class, 'btn--blue') and .//span[contains(., 'New')]]")
            new_button = self.wait.until(
                EC.element_to_be_clickable(new_button_locator))
            new_button.click()
            logging.info("Clicked New button")
            time.sleep(1)

            # Click Daily Nutrition Goal
            nutrition_goal_locator = (
                By.XPATH, "//p[contains(@class, 'tz-sp') and text()='Daily Nutrition Goal']")
            nutrition_goal = self.wait.until(
                EC.element_to_be_clickable(nutrition_goal_locator))
            nutrition_goal.click()
            logging.info("Clicked Daily Nutrition Goal")
            time.sleep(1)

            # Enter target calories
            calories_input_locator = (
                By.ID, "mealPlanGoal_calorie_amount")
            calories_input = self.wait.until(
                EC.presence_of_element_located(calories_input_locator))
            calories_input.clear()
            calories_input.send_keys(str(target_calories))
            logging.info(f"Entered target calories: {target_calories}")
            time.sleep(1)

            # Click Calories and Full Macros
            full_macros_locator = (
                By.XPATH, "//label[@for='mealPlanGoal_option_caloriesFullMacro']")
            full_macros = self.wait.until(
                EC.element_to_be_clickable(full_macros_locator))
            full_macros.click()
            logging.info("Selected Calories and Full Macros")
            time.sleep(1)

            # Click tracking option dropdown
            tracking_dropdown_locator = (
                By.ID, "nutrition_track_option_btnElem")
            tracking_dropdown = self.wait.until(
                EC.element_to_be_clickable(tracking_dropdown_locator))
            tracking_dropdown.click()
            logging.info("Clicked tracking option dropdown")
            time.sleep(1)

            # Select In App tracking
            in_app_option_locator = (
                By.ID, "nutrition_in_app_option")
            in_app_option = self.wait.until(
                EC.element_to_be_clickable(in_app_option_locator))
            in_app_option.click()
            logging.info("Selected In App tracking")
            time.sleep(1)

            # Click Save button
            save_button_locator = (
                By.ID, "mealPlanGoal_Save")
            save_button = self.wait.until(
                EC.element_to_be_clickable(save_button_locator))
            save_button.click()
            logging.info("Clicked Save button")
            time.sleep(2)

            return True
        except Exception as e:
            logging.error(f"Error setting nutrition goal: {e}")
            return False

    def verify_body_weight_goal(self, goal_weight: float, current_weight: float) -> bool:
        """Verify that the body weight goal was set correctly"""
        try:
            logging.info(
                f"Verifying body weight goal: {goal_weight}kg (current: {current_weight}kg)")

            # Wait for goals list to load
            time.sleep(2)

            # Look for the weight goal card
            weight_goal_locator = (
                By.XPATH, f"//div[contains(@class, 'goalCard')]//div[contains(text(), 'Body Weight Goal')]")
            weight_goal_card = self.wait.until(
                EC.presence_of_element_located(weight_goal_locator))

            # Find the goal details within the card
            card_content = weight_goal_card.find_element(
                By.XPATH, "./ancestor::div[contains(@class, 'goalCard')]")

            # Get the text content
            card_text = card_content.text
            logging.info(f"Found goal card text: {card_text}")

            # Verify goal weight and current weight are present
            goal_weight_str = str(goal_weight).rstrip('0').rstrip('.')
            current_weight_str = str(current_weight).rstrip('0').rstrip('.')

            if goal_weight_str in card_text and current_weight_str in card_text:
                logging.info("Body weight goal verified successfully")
                return True
            else:
                logging.error(
                    f"Goal verification failed. Expected goal: {goal_weight_str}kg, current: {current_weight_str}kg")
                logging.error(f"Card text: {card_text}")
                return False

        except Exception as e:
            logging.error(f"Error verifying body weight goal: {e}")
            return False

    def verify_nutrition_goal(self, target_calories: int) -> bool:
        """Verify that the nutrition goal was set correctly"""
        try:
            logging.info(
                f"Verifying nutrition goal: {target_calories} calories")

            # Wait for goals list to load
            time.sleep(2)

            # Look for the nutrition goal card
            nutrition_goal_locator = (
                By.XPATH, f"//div[contains(@class, 'goalCard')]//div[contains(text(), 'Daily Nutrition Goal')]")
            nutrition_goal_card = self.wait.until(
                EC.presence_of_element_located(nutrition_goal_locator))

            # Find the goal details within the card
            card_content = nutrition_goal_card.find_element(
                By.XPATH, "./ancestor::div[contains(@class, 'goalCard')]")

            # Get the text content
            card_text = card_content.text
            logging.info(f"Found goal card text: {card_text}")

            # Verify target calories and tracking method
            if str(target_calories) in card_text and "In App" in card_text:
                logging.info("Nutrition goal verified successfully")
                return True
            else:
                logging.error(
                    f"Goal verification failed. Expected calories: {target_calories}, tracking: In App")
                logging.error(f"Card text: {card_text}")
                return False

        except Exception as e:
            logging.error(f"Error verifying nutrition goal: {e}")
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
    client_name = "Shannon Birch"  # Test client name

    # Test goal values
    goal_weight = 65.0  # in kg
    current_weight = 70.0  # in kg
    target_calories = 2400

    goal_setter = TrainerizeGoalSetting()
    try:
        if goal_setter.login(username, password):
            goal_setter.handle_notification_popup()

            if goal_setter.navigate_to_client(client_name):
                print(f"Successfully navigated to client: {client_name}")

                if goal_setter.navigate_to_goals():
                    print("Successfully navigated to Goals section")

                    # Set and verify body weight goal
                    if goal_setter.set_body_weight_goal(goal_weight, current_weight):
                        print(f"Body weight goal set. Verifying...")
                        if goal_setter.verify_body_weight_goal(goal_weight, current_weight):
                            print(
                                f"✓ Body weight goal verified: {goal_weight}kg (current: {current_weight}kg)")
                        else:
                            print("✗ Body weight goal verification failed")
                    else:
                        print("Failed to set body weight goal")

                    # Set and verify nutrition goal
                    if goal_setter.set_nutrition_goal(target_calories):
                        print(f"Nutrition goal set. Verifying...")
                        if goal_setter.verify_nutrition_goal(target_calories):
                            print(
                                f"✓ Nutrition goal verified: {target_calories} calories")
                        else:
                            print("✗ Nutrition goal verification failed")
                    else:
                        print("Failed to set nutrition goal")
                else:
                    print("Failed to navigate to Goals section")
            else:
                print(f"Failed to navigate to client: {client_name}")
        else:
            print("Login failed.")

        input("Press Enter to close...")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'goal_setter' in locals():
            goal_setter.cleanup()
