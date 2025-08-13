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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, InvalidSessionIdException
from selenium.webdriver.common.keys import Keys
import sys
import sqlite3
import json


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='{asctime} - {levelname} - {message}',
            style='{',
            handlers=[
                logging.StreamHandler(stream=sys.stdout)
            ],
            encoding='utf-8'
        )
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
            service = Service()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")
            self.original_window_handle = None
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def handle_cookie_dialog(self):
        """Handle any cookie consent dialog that might appear"""
        try:
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "cookie-accept"))
            )
            cookie_button.click()
            logging.info("Accepted cookies")
        except Exception as e:
            logging.info("No cookie dialog found or error accepting cookies")
            return

    def login(self, username: str, password: str) -> bool:
        """Login to Trainerize with the given credentials - using pb.py working version"""
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
            email_field.clear()
            email_field.send_keys(username)

            logging.info("Clicking 'Find me' button...")
            find_me_button = self.driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(3)

            logging.info("Waiting for the second login page...")
            email_field_second = None
            email_selectors = [
                (By.ID, "emailInput"),
                (By.CSS_SELECTOR, "input[placeholder='Email']"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH,
                 "//input[contains(@placeholder, 'mail') or contains(@placeholder, 'Email')]"),
                (By.CSS_SELECTOR, "input.ant-input")
            ]

            for selector_type, selector_value in email_selectors:
                try:
                    email_field_second = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    logging.info(
                        f"Found second email field using: {selector_type} = {selector_value}")
                    break
                except TimeoutException:
                    continue

            if email_field_second is None:
                logging.error(
                    "Could not find second email field with any selector")
                return False

            logging.info("Clearing and entering full email on second page...")
            email_field_second.clear()
            time.sleep(0.5)
            email_field_second.send_keys(username)

            logging.info("Finding password field...")
            password_field = None
            password_selectors = [
                (By.ID, "passInput"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[placeholder*='assword']"),
                (By.XPATH, "//input[@type='password']")
            ]

            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(
                        selector_type, selector_value)
                    logging.info(
                        f"Found password field using: {selector_type} = {selector_value}")
                    break
                except NoSuchElementException:
                    continue

            if password_field is None:
                logging.error("Could not find password field")
                return False

            logging.info("Entering password...")
            password_field.clear()
            password_field.send_keys(password)

            logging.info("Looking for 'Sign In' button...")
            sign_in_button = None
            button_selectors = [
                (By.CSS_SELECTOR, "[data-testid='signIn-button']"),
                (By.XPATH, "//button[contains(text(), 'SIGN IN')]"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(@class, 'ant-btn-primary')]")
            ]

            for selector_type, selector_value in button_selectors:
                try:
                    sign_in_button = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    logging.info(
                        f"Found sign in button using: {selector_type} = {selector_value}")
                    break
                except TimeoutException:
                    continue

            if sign_in_button is None:
                logging.error("Could not find sign in button")
                return False

            logging.info("Clicking 'Sign In' button...")
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(8)

            # Verify login success
            logging.info("Verifying login success...")
            max_wait_time = 30
            start_time = time.time()
            login_successful = False

            while time.time() - start_time < max_wait_time:
                current_url = self.driver.current_url
                page_title = self.driver.title.lower()

                success_indicators = [
                    "login" not in current_url.lower(),
                    "dashboard" in current_url.lower(),
                    "home" in current_url.lower(),
                    "client" in page_title,
                    "dashboard" in page_title,
                    "trainerize" in page_title and "login" not in page_title
                ]

                if any(success_indicators):
                    logging.info(
                        f"Login success detected - URL: {current_url}, Title: {self.driver.title}")
                    login_successful = True
                    break

                time.sleep(1)

            if login_successful:
                logging.info("Successfully logged in!")
                return True
            else:
                logging.error(
                    f"Login verification failed after {max_wait_time}s - URL: {self.driver.current_url}")
                return False

        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def retry_on_stale_element(self, func, max_retries=3, retry_delay=1):
        """Retry function on StaleElementReferenceException"""
        for attempt in range(max_retries):
            try:
                return func()
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    logging.warning(
                        f"Stale element, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise
            except Exception as e:
                if "Stacktrace:" in str(e) and attempt < max_retries - 1:
                    logging.warning(
                        f"Stack trace error, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise

    def transform_client_name(self, database_name):
        """Transform database client name to display format"""
        if '_' in database_name:
            parts = database_name.split('_')
            return ' '.join(word.capitalize() for word in parts)
        else:
            return database_name.title()

    def navigate_to_client(self, client_name: str) -> bool:
        """Navigate to a specific client's page - using pb.py working version"""
        try:
            display_name = self.transform_client_name(client_name)
            logging.info(
                f"Attempting to navigate to client: {client_name} (display name: {display_name})")

            # Step 1: Click Clients link
            def click_clients_link():
                logging.info("Clicking the 'Clients' link in the sidebar...")
                clients_link_locator = (
                    By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
                time.sleep(2)
                return True

            if not self.retry_on_stale_element(click_clients_link):
                logging.error("Failed to click Clients link")
                return False

            # Step 2: Search for client
            def search_for_client():
                logging.info("Entering client name into the search bar...")
                search_input_locator = (
                    By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
                search_input = self.wait.until(
                    EC.presence_of_element_located(search_input_locator))
                search_input.clear()
                search_input.send_keys(display_name)
                time.sleep(2)
                return True

            if not self.retry_on_stale_element(search_for_client):
                logging.error("Failed to search for client")
                return False

            # Step 3: Click on client name
            def click_client_name():
                logging.info(
                    "Clicking on the client's name in search results...")
                client_selectors = [
                    (By.XPATH, f"//a[contains(text(), '{display_name}')]"),
                    (By.XPATH,
                     f"//td[contains(text(), '{display_name}')]/parent::tr//a"),
                    (By.XPATH,
                     f"//div[contains(text(), '{display_name}')]/ancestor::tr//a")
                ]

                for selector_type, selector_value in client_selectors:
                    try:
                        client_link = self.wait.until(
                            EC.element_to_be_clickable((selector_type, selector_value)))
                        client_link.click()
                        logging.info(
                            f"Clicked client using selector: {selector_type}")
                        time.sleep(2)
                        return True
                    except TimeoutException:
                        continue

                raise Exception(
                    f"Could not find clickable client link for {display_name}")

            if not self.retry_on_stale_element(click_client_name):
                logging.error("Failed to click client name")
                return False

            # Step 4: Click Open button
            def click_open_button():
                logging.info("Clicking the 'Open' button...")
                open_selectors = [
                    (By.CSS_SELECTOR,
                     "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']"),
                    (By.XPATH, "//button[contains(text(), 'Open')]"),
                    (By.CSS_SELECTOR, "[data-testid*='switchIntoClient']")
                ]

                for selector_type, selector_value in open_selectors:
                    try:
                        open_button = self.wait.until(
                            EC.element_to_be_clickable((selector_type, selector_value)))
                        open_button.click()
                        logging.info(
                            f"Clicked open button using: {selector_type}")
                        time.sleep(3)
                        return True
                    except TimeoutException:
                        continue

                raise Exception("Could not find clickable Open button")

            if not self.retry_on_stale_element(click_open_button):
                logging.error("Failed to click Open button")
                return False

            # Step 5: Switch to new tab
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle

            max_wait = 10
            start_time = time.time()
            while len(self.driver.window_handles) < 2 and time.time() - start_time < max_wait:
                time.sleep(0.5)

            if len(self.driver.window_handles) < 2:
                logging.error("New tab did not open")
                return False

            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break

            time.sleep(3)
            logging.info(f"Successfully navigated to client: {display_name}")
            return True

        except Exception as e:
            logging.error(f"Error navigating to client: {e}")
            return False

    def navigate_to_training_program(self):
        """Navigate to the 'Training Program' tab - using pb.py working version"""
        try:
            logging.info("Navigating to the 'Training Program' tab...")
            training_program_link_locator = (
                By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']")

            training_program_link = self.wait.until(
                EC.element_to_be_clickable(training_program_link_locator))
            training_program_link.click()
            time.sleep(5)

            if "/trainingProgram" in self.driver.current_url:
                logging.info(
                    "Successfully navigated to the 'Training Program' tab.")
                return True
            else:
                logging.error(
                    "Navigation verification failed - URL doesn't contain /trainingProgram")
                return False

        except Exception as e:
            logging.error(
                f"Error navigating to the 'Training Program' tab: {e}")
            return False

    def find_and_click_workout_by_name(self, workout_name):
        """Find and click a workout by its name with modal dismissal and fuzzy matching"""
        try:
            logging.info(f"Looking for workout: '{workout_name}'")

            # First, dismiss any modals that might be blocking interactions
            self.dismiss_any_modals()

            # Wait for page to load
            time.sleep(2)

            # DEBUG: See what workouts are actually available
            available_workouts = self.debug_available_workouts()

            # Try to find the best matching workout name
            actual_workout_name = self.find_closest_workout_name(
                workout_name, available_workouts)
            if actual_workout_name and actual_workout_name != workout_name:
                logging.info(
                    f"Using fuzzy match: '{actual_workout_name}' for requested '{workout_name}'")
                target_workout = actual_workout_name
            else:
                target_workout = workout_name

            workout_selectors = [
                f"//p[contains(@data-testid, 'workoutGrid-workoutName') and text()='{target_workout}']/ancestor::a[1]",
                f"//p[contains(@class, 'tz-lp') and contains(@class, 'color--blue') and text()='{target_workout}']/ancestor::a[1]",
                f"//a[contains(@href, '/workout/') and .//p[text()='{target_workout}']]",
                f"//a[contains(@class, 'section-link') and .//p[text()='{target_workout}']]"
            ]

            for i, selector in enumerate(workout_selectors, 1):
                try:
                    # Dismiss modal before each attempt
                    self.dismiss_any_modals()

                    logging.info(f"Trying selector {i}: {selector}")
                    workout_link = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector)))

                    # Try JavaScript click first as it's more reliable with modals
                    try:
                        self.driver.execute_script(
                            "arguments[0].click();", workout_link)
                        logging.info(
                            f"Successfully clicked workout: '{target_workout}' using JavaScript click")
                    except:
                        # Fallback to regular click
                        workout_link.click()
                        logging.info(
                            f"Successfully clicked workout: '{target_workout}' using regular click")

                    time.sleep(3)
                    return True

                except TimeoutException:
                    logging.info(f"Selector {i} failed, trying next...")
                    continue
                except ElementClickInterceptedException as e:
                    logging.warning(f"Click intercepted for selector {i}: {e}")
                    # Try to dismiss modal and continue
                    self.dismiss_any_modals()
                    continue
                except Exception as e:
                    logging.warning(f"Error with selector {i}: {e}")
                    continue

            logging.error(
                f"Could not find or click workout: '{workout_name}' (tried as '{target_workout}')")
            return False

        except Exception as e:
            logging.error(f"Error clicking workout '{workout_name}': {e}")
            return False

    def click_edit_workout(self) -> bool:
        """Click the edit button for the workout - using pb.py working version"""
        try:
            edit_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='workoutDetail-editButton']")
            edit_button = self.wait.until(
                EC.element_to_be_clickable(edit_button_locator))
            edit_button.click()
            logging.info("Clicked main edit workout button")
            time.sleep(2)

            workout_builder_locator = (
                By.CSS_SELECTOR, "li[data-testid='dropdownButton-menuItem-workoutBuilder']")
            workout_builder_option = self.wait.until(
                EC.element_to_be_clickable(workout_builder_locator))
            workout_builder_option.click()
            logging.info("Clicked 'Workout Builder' from dropdown")
            time.sleep(5)
            return True
        except Exception as e:
            logging.error(f"Error clicking edit workout button: {e}")
            return False

    def update_exercise_goal(self, exercise_name: str, new_goals: str) -> bool:
        """Update the goal of a specific exercise within the currently open workout"""
        try:
            logging.info(f"Looking for exercise: {exercise_name}")

            # Find the exercise container using pb.py working locator
            exercise_in_list_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{exercise_name}']/ancestor::div[contains(@class, 'workoutExercise')]")

            try:
                exercise_container = self.wait.until(
                    EC.presence_of_element_located(exercise_in_list_locator))
                logging.info(f"Found container for '{exercise_name}'.")
            except TimeoutException:
                logging.error(
                    f"Could not find container for '{exercise_name}' in the workout list after 20 seconds.")
                return False

            # Find the goals input field within that container - using pb.py working locator
            try:
                target_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")
                target_input = exercise_container.find_element(
                    *target_input_locator)

                if not target_input.is_displayed() or not target_input.is_enabled():
                    logging.warning(
                        f"Goal input field for {exercise_name} is not interactable. Attempting scroll into view.")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", target_input)
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(target_input_locator))

            except NoSuchElementException:
                logging.error(
                    f"Failed to find the goal input field for exercise {exercise_name}.")
                return False

            if target_input:
                target_input.click()
                time.sleep(0.5)
                target_input.send_keys(Keys.CONTROL + "a")
                target_input.send_keys(Keys.DELETE)
                time.sleep(0.5)
                target_input.send_keys(new_goals)
                logging.info(f"Successfully updated goal for {exercise_name}.")
                return True
            else:
                logging.error(
                    f"Failed to find the goal input field for exercise {exercise_name}.")
                return False

        except Exception as e:
            logging.error(f"Error updating exercise {exercise_name} goal: {e}")
            return False

    def close_all_other_tabs(self):
        """Close all tabs except the current one"""
        if len(self.driver.window_handles) > 1:
            for window_handle in self.driver.window_handles:
                if window_handle != self.driver.current_window_handle:
                    self.driver.switch_to.window(window_handle)
                    self.driver.close()
            self.driver.switch_to.window(self.driver.current_window_handle)
            logging.info("Closed all other tabs.")

    def process_multiple_clients(self, progressions_data: dict) -> dict:
        """Process multiple clients to update their workout programs based on progression data"""
        results = {}
        self.original_window_handle = self.driver.current_window_handle

        for client_name, workouts_data in progressions_data.items():
            logging.info(
                f"\n{'='*10} Processing client: {client_name} {'='*10}")
            try:
                # Ensure we are on the original window before navigating to clients
                self.driver.switch_to.window(self.original_window_handle)
                self.close_all_other_tabs()

                if not self.navigate_to_client(client_name):
                    logging.error(
                        f"Failed to navigate to client {client_name}. Skipping.")
                    results[client_name] = {
                        'status': 'failed', 'error': 'Failed to navigate to client'}
                    continue

                if not self.navigate_to_training_program():
                    logging.error(
                        f"Failed to navigate to training program for {client_name}. Skipping.")
                    results[client_name] = {
                        'status': 'failed', 'error': 'Failed to navigate to training program'}
                    continue

                # Process each workout for this client
                for workout_name, exercises_data in workouts_data.items():
                    logging.info(f"  Processing workout: {workout_name}")
                    processed_exercises_in_workout = set()

                    try:
                        if not self.find_and_click_workout_by_name(workout_name):
                            logging.error(
                                f"    Failed to click workout {workout_name}. Skipping exercises for this workout.")
                            continue

                        if not self.click_edit_workout():
                            logging.error(
                                f"    Failed to enter edit mode for workout {workout_name}. Skipping exercises for this workout.")
                            continue

                        # Update each exercise in the current workout
                        for exercise_data in exercises_data:
                            exercise_name = exercise_data['exercise_name']

                            # Check for duplicates before processing
                            if exercise_name in processed_exercises_in_workout:
                                logging.info(
                                    f"      Skipping duplicate exercise: {exercise_name}")
                                continue

                            # This contains the formatted GOALS string
                            new_goals = exercise_data['reps']
                            logging.info(
                                f"      Updating exercise: {exercise_name} with goals: {new_goals}")

                            if not self.update_exercise_goal(exercise_name, new_goals):
                                logging.warning(
                                    f"        Failed to update exercise {exercise_name} for {client_name}.")
                            else:
                                processed_exercises_in_workout.add(
                                    exercise_name)

                        # Save the workout changes
                        logging.info("    Saving workout changes...")
                        save_button_selector = "button[data-testid='workoutBuilder-saveBtn']"
                        try:
                            save_button = self.wait.until(EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, save_button_selector)))
                            self.driver.execute_script(
                                "arguments[0].click();", save_button)
                            time.sleep(3)
                            logging.info("    Workout saved successfully.")
                        except TimeoutException:
                            logging.error(
                                "    Save button not found or not clickable.")

                        # Go back to the program overview
                        logging.info(
                            "    Navigating back to training program overview.")
                        self.driver.back()
                        time.sleep(2)

                    except Exception as e:
                        logging.error(
                            f"  Error processing workout {workout_name} for {client_name}: {e}")
                        # Try to get back to a known state
                        try:
                            self.navigate_to_training_program()
                        except:
                            logging.warning(
                                "Could not navigate back to training program.")

                results[client_name] = {'status': 'success'}

            except Exception as e:
                logging.error(f"Error processing client {client_name}: {e}")
                results[client_name] = {'status': 'failed', 'error': str(e)}
                # Try to return to a stable state
                try:
                    self.driver.switch_to.window(self.original_window_handle)
                    self.driver.get(
                        "https://cocosptstudio.trainerize.com/app/overview")
                    time.sleep(5)
                except Exception as ex:
                    logging.error(
                        f"Failed to recover to dashboard after error with {client_name}: {ex}")

        return results

    def cleanup(self):
        """Clean up resources"""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'):
                self.driver.quit()
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def dismiss_any_modals(self):
        """Dismiss any modal overlays that might be blocking interactions"""
        try:
            # Look for common modal close buttons and overlays
            modal_dismiss_selectors = [
                (By.CSS_SELECTOR, ".reactModal-overlay"),
                (By.CSS_SELECTOR, ".modal-overlay"),
                (By.CSS_SELECTOR,
                 "[data-testid*='modal'] button[data-testid*='close']"),
                (By.CSS_SELECTOR, "[data-testid*='modal'] .close"),
                (By.CSS_SELECTOR, ".ant-modal-close"),
                (By.CSS_SELECTOR, ".modal-close"),
                (By.XPATH, "//button[contains(@class, 'close')]"),
                (By.XPATH,
                 "//div[contains(@class, 'modal')]//button[contains(text(), 'Close')]")
            ]

            for selector_type, selector_value in modal_dismiss_selectors:
                try:
                    modal_elements = self.driver.find_elements(
                        selector_type, selector_value)
                    for element in modal_elements:
                        if element.is_displayed():
                            # Try clicking the modal element to dismiss it
                            if "overlay" in selector_value.lower():
                                # For overlays, click them to dismiss
                                self.driver.execute_script(
                                    "arguments[0].click();", element)
                                logging.info(
                                    f"Clicked modal overlay to dismiss: {selector_value}")
                            else:
                                # For buttons, click normally
                                element.click()
                                logging.info(
                                    f"Clicked modal close button: {selector_value}")
                            time.sleep(1)
                            return True
                except Exception as e:
                    continue

            # Also try pressing Escape key
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(
                    By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                logging.info("Pressed Escape key to dismiss modal")
                time.sleep(1)
                return True
            except:
                pass

            return False
        except Exception as e:
            logging.warning(f"Error dismissing modals: {e}")
            return False

    def debug_available_workouts(self):
        """Debug function to see what workout names are actually available"""
        try:
            logging.info(
                "DEBUG: Looking for all available workout elements...")

            # Wait a moment for page to load
            time.sleep(3)

            # Try different selectors to find workout elements
            workout_element_selectors = [
                (By.XPATH,
                 "//p[contains(@data-testid, 'workoutGrid-workoutName')]"),
                (By.XPATH,
                 "//p[contains(@class, 'tz-lp') and contains(@class, 'color--blue')]"),
                (By.XPATH, "//a[contains(@href, '/workout/')]//p"),
                (By.CSS_SELECTOR, "[data-testid*='workoutGrid'] p"),
                (By.XPATH, "//div[contains(@class, 'workout')]//p")
            ]

            all_found_workouts = set()

            for i, (selector_type, selector_value) in enumerate(workout_element_selectors, 1):
                try:
                    elements = self.driver.find_elements(
                        selector_type, selector_value)
                    logging.info(
                        f"DEBUG: Selector {i} found {len(elements)} elements")

                    for element in elements:
                        try:
                            text = element.text.strip()
                            # Filter out empty or very short text
                            if text and len(text) > 2:
                                all_found_workouts.add(text)
                                logging.info(
                                    f"DEBUG:   Found workout text: '{text}'")
                        except:
                            continue

                except Exception as e:
                    logging.info(f"DEBUG: Selector {i} failed: {e}")
                    continue

            logging.info(
                f"DEBUG: All unique workout names found: {sorted(all_found_workouts)}")
            return sorted(all_found_workouts)

        except Exception as e:
            logging.error(f"DEBUG: Error finding available workouts: {e}")
            return []

    def find_closest_workout_name(self, target_workout, available_workouts):
        """Find the closest matching workout name using fuzzy matching"""
        if not available_workouts:
            return None

        target_lower = target_workout.lower()

        # Check for exact match first
        for workout in available_workouts:
            if workout.lower() == target_lower:
                logging.info(
                    f"Found exact match: '{workout}' for '{target_workout}'")
                return workout

        # Check for partial matches
        best_matches = []
        for workout in available_workouts:
            workout_lower = workout.lower()

            # Check if target is contained in workout name
            if target_lower in workout_lower:
                best_matches.append(workout)
                logging.info(
                    f"Found partial match: '{workout}' contains '{target_workout}'")

            # Check if workout name is contained in target
            elif workout_lower in target_lower:
                best_matches.append(workout)
                logging.info(
                    f"Found partial match: '{target_workout}' contains '{workout}'")

            # Check for word overlap
            target_words = set(target_lower.split())
            workout_words = set(workout_lower.split())
            common_words = target_words.intersection(workout_words)

            if common_words and len(common_words) >= 1:
                best_matches.append(workout)
                logging.info(
                    f"Found word match: '{workout}' shares words {common_words} with '{target_workout}'")

        if best_matches:
            # Return the first best match
            chosen_match = best_matches[0]
            logging.info(
                f"Choosing best match: '{chosen_match}' for '{target_workout}'")
            return chosen_match

        logging.warning(
            f"No suitable match found for '{target_workout}' in available workouts")
        return None


# Test script to verify functionality
if __name__ == "__main__":
    # Test with a simple case first
    automation = TrainerizeAutomation()

    try:
        # Login credentials from memory
        username = "shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        print("Testing login...")
        if automation.login(username, password):
            print("✅ Login successful!")

            # Test navigation to a client
            test_client = "alice_forster"  # Use one of your clients
            print(f"Testing navigation to client: {test_client}")

            if automation.navigate_to_client(test_client):
                print("✅ Client navigation successful!")

                if automation.navigate_to_training_program():
                    print("✅ Training program navigation successful!")
                    print("\n🎉 Basic navigation tests passed!")
                    print(
                        "The fixed script should now work with your progression data.")
                else:
                    print("❌ Training program navigation failed")
            else:
                print("❌ Client navigation failed")
        else:
            print("❌ Login failed")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        automation.cleanup()
