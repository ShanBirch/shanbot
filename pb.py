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


class TrainerizeAutomation:
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
            service = Service()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logging.info("Chrome initialized successfully!")
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

    def handle_notification_popup(self):
        """Handle any notification popup that might appear after login"""
        try:
            notification_button = self.driver.find_element(
                By.CLASS_NAME, "notification-button")
            if notification_button:
                notification_button.click()
                logging.info("Dismissed notification popup")
        except Exception as e:
            logging.info("No notification popup found or error dismissing it")
            return

    def login(self, username: str, password: str) -> bool:
        """Login to Trainerize with the given credentials"""
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
            time.sleep(3)  # Give more time for page transition

            logging.info("Waiting for the second login page...")
            # Try multiple selectors for the second email field
            email_field_second = None
            email_selectors = [
                (By.ID, "emailInput"),  # Original selector
                # Based on screenshot
                (By.CSS_SELECTOR, "input[placeholder='Email']"),
                (By.CSS_SELECTOR, "input[type='email']"),  # Email input type
                # Flexible
                (By.XPATH,
                 "//input[contains(@placeholder, 'mail') or contains(@placeholder, 'Email')]"),
                # Generic input class if needed
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
            # Try multiple selectors for password field
            password_field = None
            password_selectors = [
                (By.ID, "passInput"),  # Original selector
                # Password input type
                (By.CSS_SELECTOR, "input[type='password']"),
                # Contains password
                (By.CSS_SELECTOR, "input[placeholder*='assword']"),
                # XPath for password type
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
            # Try multiple selectors for sign in button
            sign_in_button = None
            button_selectors = [
                (By.CSS_SELECTOR, "[data-testid='signIn-button']"),  # Original
                # Based on screenshot
                (By.XPATH, "//button[contains(text(), 'SIGN IN')]"),
                # Case variation
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),  # Submit button
                # Primary button class
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
            time.sleep(5)  # Wait longer for login to complete

            # Verify login success with multiple checks and longer wait
            logging.info("Verifying login success...")

            # Wait up to 15 seconds for redirect/dashboard load
            max_wait_time = 15
            start_time = time.time()
            login_successful = False

            while time.time() - start_time < max_wait_time:
                current_url = self.driver.current_url
                page_title = self.driver.title.lower()

                # Check multiple success indicators
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

                # Check for potential 2FA or error messages
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                               ".error, .alert, .warning, [class*='error'], [class*='alert']")
                    if error_elements:
                        error_text = " ".join(
                            [elem.text for elem in error_elements if elem.text])
                        if error_text:
                            logging.error(
                                f"Login error detected: {error_text}")
                            return False
                except:
                    pass

                time.sleep(1)  # Wait 1 second before checking again

            if login_successful:
                logging.info("Successfully logged in!")
                return True
            else:
                logging.error(
                    f"Login verification failed after {max_wait_time}s - URL: {self.driver.current_url}")

                # Log page source for debugging (first 500 chars)
                try:
                    page_source = self.driver.page_source[:500]
                    logging.debug(f"Page source sample: {page_source}")
                except:
                    pass

                return False

        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def retry_on_stale_element(self, func, max_retries=3, retry_delay=1):
        """Retry function on StaleElementReferenceException or stack trace errors"""
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

    def click_element_safely(self, element, use_js=False):
        """Click element with retry logic"""
        def click_attempt():
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()

        return self.retry_on_stale_element(click_attempt)

    def navigate_to_client(self, client_name: str) -> bool:
        """Navigate to a specific client's page with stale element handling"""
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")

            # Step 1: Click Clients link with retry logic
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

            # Step 2: Search for client with retry logic
            def search_for_client():
                logging.info("Entering client name into the search bar...")
                search_input_locator = (
                    By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
                search_input = self.wait.until(
                    EC.presence_of_element_located(search_input_locator))
                search_input.clear()
                search_input.send_keys(client_name)
                time.sleep(2)  # Wait for search results
                return True

            if not self.retry_on_stale_element(search_for_client):
                logging.error("Failed to search for client")
                return False

            # Step 3: Click on client name with retry logic
            def click_client_name():
                logging.info(
                    "Clicking on the client's name in search results...")
                # Try multiple selectors for client link
                client_selectors = [
                    (By.XPATH, f"//a[contains(text(), '{client_name}')]"),
                    (By.XPATH,
                     f"//td[contains(text(), '{client_name}')]/parent::tr//a"),
                    (By.XPATH,
                     f"//div[contains(text(), '{client_name}')]/ancestor::tr//a"),
                    (By.CSS_SELECTOR, f"[data-testid*='client'] a")
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
                    f"Could not find clickable client link for {client_name}")

            if not self.retry_on_stale_element(click_client_name):
                logging.error("Failed to click client name")
                return False

            # Step 4: Click Open button with retry logic
            def click_open_button():
                logging.info("Clicking the 'Open' button...")
                # Try multiple selectors for the open button
                open_selectors = [
                    (By.CSS_SELECTOR,
                     "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']"),
                    (By.XPATH, "//button[contains(text(), 'Open')]"),
                    (By.XPATH,
                     "//button[contains(@class, 'btn') and contains(text(), 'Open')]"),
                    (By.CSS_SELECTOR, "[data-testid*='switchIntoClient']")
                ]

                for selector_type, selector_value in open_selectors:
                    try:
                        open_button = self.wait.until(
                            EC.element_to_be_clickable((selector_type, selector_value)))
                        open_button.click()
                        logging.info(
                            f"Clicked open button using: {selector_type}")
                        time.sleep(3)  # Wait for new tab
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

            # Wait for new tab to open
            max_wait = 10
            start_time = time.time()
            while len(self.driver.window_handles) < 2 and time.time() - start_time < max_wait:
                time.sleep(0.5)

            if len(self.driver.window_handles) < 2:
                logging.error("New tab did not open")
                return False

            # Switch to the new tab
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break

            # Wait for client page to load
            time.sleep(3)

            # Verify we're on the client page
            current_url = self.driver.current_url
            if client_name.lower().replace(' ', '').replace("'", "") in current_url.lower() or "client" in current_url.lower():
                logging.info(
                    f"Successfully navigated to client: {client_name}")
                return True
            else:
                logging.warning(
                    f"May not be on correct client page. URL: {current_url}")
                return True  # Continue anyway, might still work

        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False

    def navigate_to_training_program(self):
        """Navigates to the 'Training Program' tab (using pe.py logic)."""
        try:
            logging.info("Navigating to the 'Training Program' tab...")
            # Use the specific XPath from pe.py
            training_program_link_locator = (
                By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']")

            # Wait for clickability and click
            training_program_link = self.wait.until(
                EC.element_to_be_clickable(training_program_link_locator))
            training_program_link.click()

            time.sleep(2)  # Wait for the page to load

            # Verify navigation
            if "/trainingProgram" in self.driver.current_url:
                logging.info(
                    "Successfully navigated to the 'Training Program' tab.")
                return True
            else:
                logging.error(
                    "Navigation verification failed - URL doesn't contain /trainingProgram")
                return False

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"Error navigating to the 'Training Program' tab: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def find_current_workout_program(self):
        """Finds and returns the name of the current workout program, if any."""
        try:
            logging.info("Looking for the current workout program...")
            current_program_indicator_locator = (
                By.CLASS_NAME, "section-userProgramTrainingPhase-current")
            try:
                current_program_indicator = self.wait.until(
                    EC.presence_of_element_located(current_program_indicator_locator))
                logging.info(
                    "Found element with class 'section-userProgramTrainingPhase-current'")
                # Log the outer HTML of the element to inspect its structure
                logging.info(
                    f"HTML of current_program_indicator: {current_program_indicator.get_attribute('outerHTML')}")

                # Go to the parent div, then find the program name WITHIN that div
                program_name_element = current_program_indicator.find_element(
                    By.XPATH, "./preceding-sibling::p[@class='tz-sp color--black text-overflow-none']")
                program_name = program_name_element.text
                logging.info("Current workout program found: %s", program_name)
                return program_name

            except NoSuchElementException as e:
                logging.warning(
                    f"NoSuchElementException while finding program name: Check the XPath to locate the program name element. - {e}")
                logging.warning(
                    "Check the XPath to locate the program name element.")
                return None
            except Exception as e:
                logging.error(f"Error finding program name: {e}")
                logging.error(f"Specific error: {e}")
                return None

        except (TimeoutException, NoSuchElementException) as e:
            logging.info(
                "No current workout program found (Timeout or element not found).")
            return None  # No current program found
        except Exception as e:
            logging.error(f"Error finding current workout program: {e}")
            return None

    def click_workout(self, workout_name: str) -> bool:
        """Click on a specific workout in the training program"""
        try:
            # Try to find and click the workout link
            workout_links = self.driver.find_elements(
                By.XPATH, f"//a[contains(text(), '{workout_name}')]")
            if workout_links:
                workout_links[0].click()
                logging.info(f"Successfully clicked workout: {workout_name}")
                return True
            else:
                logging.error(f"Could not find workout: {workout_name}")
                return False
        except Exception as e:
            logging.error(f"Error clicking workout {workout_name}: {e}")
            return False

    def click_edit_workout(self) -> bool:
        """Clicks the edit button for the workout, then clicks 'Workout Builder' from the dropdown."""
        try:
            # Click the main Edit button
            edit_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='workoutDetail-editButton']")
            edit_button = self.wait.until(
                EC.element_to_be_clickable(edit_button_locator)
            )
            edit_button.click()
            logging.info("Clicked main edit workout button")
            time.sleep(1)  # Wait for dropdown to appear

            # Click the 'Workout Builder' option from the dropdown
            workout_builder_locator = (
                By.CSS_SELECTOR, "li[data-testid='dropdownButton-menuItem-workoutBuilder']")
            workout_builder_option = self.wait.until(
                EC.element_to_be_clickable(workout_builder_locator)
            )
            workout_builder_option.click()
            logging.info("Clicked 'Workout Builder' from dropdown")
            time.sleep(3)  # Wait for builder to load
            return True
        except Exception as e:
            logging.error(
                f"Error clicking edit workout button or dropdown option: {e}")
            return False

    def find_closest_exercise(self, target_exercise: str, available_exercises: list) -> str:
        """Find the closest matching exercise name using fuzzy matching."""
        def clean_name(name: str) -> str:
            # Remove common words, hyphens, and standardize
            cleaned = name.lower()
            cleaned = cleaned.replace("barbell", "").replace(
                "dumbbell", "").replace("machine", "")
            cleaned = cleaned.replace("-", " ")  # Replace hyphen with space
            # Remove trailing 's' for basic plural handling
            if cleaned.endswith('s'):
                cleaned = cleaned[:-1]
            return cleaned.strip()

        target_clean = clean_name(target_exercise)
        best_match = None
        best_ratio = 0

        for exercise in available_exercises:
            exercise_clean = clean_name(exercise)
            # Check for exact matches first
            if target_clean == exercise_clean:
                return exercise

            # Check if all words in target are in exercise name
            target_words = set(target_clean.split())
            exercise_words = set(exercise_clean.split())
            word_match_ratio = len(target_words.intersection(
                exercise_words)) / len(target_words)

            # Calculate character similarity
            char_match = 0
            for i in range(min(len(target_clean), len(exercise_clean))):
                if target_clean[i] == exercise_clean[i]:
                    char_match += 1
            char_ratio = char_match / \
                max(len(target_clean), len(exercise_clean))

            # Combined score
            match_ratio = (word_match_ratio * 0.7) + (char_ratio * 0.3)

            if match_ratio > best_ratio:
                best_ratio = match_ratio
                best_match = exercise

        # Adjusted threshold for better matching
        return best_match if best_ratio > 0.5 else None  # Lowered threshold from 0.6

    def add_exercise(self, exercise_name, sets="3", reps="12"):
        """Adds exercise, sets sets/reps, WITHOUT saving workout, using updated selectors and flow."""
        try:
            logging.info(
                f"Adding exercise: {exercise_name} with Sets={sets}, Reps={reps}...")

            # Variable to store the actual name added, defaults to original
            actual_exercise_name_added = exercise_name

            # 1. Find and click the main search input within the builder
            search_input_locator = (
                By.CSS_SELECTOR, "input.ant-input[placeholder='Search for an exercise']")
            search_input = self.wait.until(
                EC.element_to_be_clickable(search_input_locator))
            search_input.click()
            # Aggressively clear just in case
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            logging.info("Clicked and cleared search input.")

            # 2. Type exercise name
            search_input.send_keys(exercise_name)
            logging.info(f"Typed '{exercise_name}'.")
            # Allow search suggestions to potentially load (though we press Enter)
            time.sleep(1)

            # 3. Press Enter
            search_input.send_keys(Keys.ENTER)
            logging.info("Pressed Enter.")
            time.sleep(5)  # Wait for search results library to load

            # 4. Wait for and Find Exercise in Library (Exact Match First)
            logging.info(
                f"Searching library for exact match: '{exercise_name}'")
            # Construct data-testid dynamically (lowercase, remove spaces)
            processed_name = ''.join(
                filter(str.isalnum, exercise_name)).lower()
            # Adjust dynamic selector based on observed patterns (may need refinement)
            # Example: exerciseLibrary-exercise-latpulldownwidegrip
            # Let's try a contains approach first as exact dynamic generation is tricky
            exercise_library_locator = (
                By.XPATH, f"//div[contains(@data-testid, 'exerciseLibrary-exercise') and .//p[text()='{exercise_name}']]")

            exercise_element = None
            try:
                # Wait for the container to be present
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".exerciseLibrary-container")))
                # Wait for the specific exercise to be clickable
                exercise_element = self.wait.until(
                    EC.element_to_be_clickable(exercise_library_locator))
                logging.info(
                    f"Found exact match for '{exercise_name}' in library.")
                # actual_exercise_name_added remains exercise_name
            except TimeoutException:
                logging.warning(
                    f"Exact match for '{exercise_name}' not found or not clickable. Trying fuzzy match...")
                # 5. Fuzzy Match Logic
                try:
                    # Get all available exercise elements
                    available_exercise_elements = self.driver.find_elements(
                        By.XPATH, "//div[contains(@data-testid, 'exerciseLibrary-exercise')]//p")
                    available_exercise_names = [
                        elem.text for elem in available_exercise_elements if elem.text]

                    if not available_exercise_names:
                        logging.error(
                            "Could not find any exercise names in the library for fuzzy matching.")
                        return False

                    closest_match_name = self.find_closest_exercise(
                        exercise_name, available_exercise_names)

                    if closest_match_name:
                        logging.info(
                            f"Closest fuzzy match found: '{closest_match_name}'")
                        # Find the element corresponding to the closest match
                        fuzzy_match_locator = (
                            By.XPATH, f"//div[contains(@data-testid, 'exerciseLibrary-exercise') and .//p[text()='{closest_match_name}']]")
                        exercise_element = self.wait.until(
                            EC.element_to_be_clickable(fuzzy_match_locator))
                        actual_exercise_name_added = closest_match_name  # Update the name used later
                    else:
                        logging.error(
                            f"Fuzzy match failed for '{exercise_name}'.")
                        return False
                except Exception as fuzzy_e:
                    logging.error(f"Error during fuzzy matching: {fuzzy_e}")
                    return False

            # 6. Click the Found/Closest Exercise
            if exercise_element:
                # Log the name we determined was added
                logging.info(
                    f"Clicking on exercise '{actual_exercise_name_added}' in library.")
                exercise_element.click()
                time.sleep(1)
            else:
                # This case should ideally be caught above, but as a safeguard:
                logging.error(
                    "Exercise element was not found after search and fuzzy match.")
                return False

            # 7. Click "Add to Workout" Button
            add_to_workout_button_locator = (
                By.XPATH, "//button[contains(@class, 'btn--blue') and contains(., 'Add to Workout')]")
            add_to_workout_button = self.wait.until(
                EC.element_to_be_clickable(add_to_workout_button_locator))
            add_to_workout_button.click()
            logging.info("Clicked 'Add to Workout' button.")
            time.sleep(10)  # Wait for exercise to appear in the list below

            # --- Step 8: Locate Added Exercise Container (Reverted to Backup Logic) --- START ---
            # Use the actual_exercise_name_added found earlier
            logging.info(
                f"Locating container for '{actual_exercise_name_added}' in the workout list...")
            # Use the actual_exercise_name_added in the XPath
            exercise_in_list_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{actual_exercise_name_added}']/ancestor::div[contains(@class, 'workoutExercise')]")

            try:
                # Use the default wait (10 seconds) from self.wait
                workout_list_exercise_div = self.wait.until(
                    EC.presence_of_element_located(exercise_in_list_locator))
                logging.info(
                    f"Found container for '{actual_exercise_name_added}'.")
            except TimeoutException:
                logging.error(
                    f"Could not find container for '{actual_exercise_name_added}' in the workout list after adding.")
                return False
            # --- Step 8 --- END ---

            # 9. Set Sets (relative to the found container)
            try:
                sets_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-exerciseSetInput']")
                sets_input = workout_list_exercise_div.find_element(
                    *sets_input_locator)
                sets_input.click()
                time.sleep(0.2)
                # Clear using backspace (adjust count if needed)
                # Increased backspaces slightly
                sets_input.send_keys(Keys.BACKSPACE * 5)
                time.sleep(0.2)
                sets_input.send_keys(sets)
                # Log with correct name
                logging.info(
                    f"Sets set to: {sets} for {actual_exercise_name_added}")
                time.sleep(0.5)
            except Exception as e:
                # Log with correct name
                logging.error(
                    f"Error setting sets for '{actual_exercise_name_added}': {e}")
                # self.driver.save_screenshot(f"error_set_sets_{exercise_name}.png")
                return False

            # 10. Set Reps (relative to the found container)
            try:
                reps_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")
                reps_input = workout_list_exercise_div.find_element(
                    *reps_input_locator)
                reps_input.click()
                time.sleep(0.2)
                # Clear using backspace (adjust count if needed, placeholder might be there)
                # Keep a high number for reps field
                reps_input.send_keys(Keys.BACKSPACE * 30)
                time.sleep(0.2)
                reps_input.send_keys(reps)
                # Log with correct name
                logging.info(
                    f"Reps set to: {reps} for {actual_exercise_name_added}")
                time.sleep(0.5)
            except Exception as e:
                # Log with correct name
                logging.error(
                    f"Error setting reps for '{actual_exercise_name_added}': {e}")
                # self.driver.save_screenshot(f"error_set_reps_{exercise_name}.png")
                return False

            logging.info(
                # Log with correct name
                f"Successfully added and configured '{actual_exercise_name_added}'.")
            return True

        except (TimeoutException, NoSuchElementException) as e:
            # Log with original requested name, as the failure might have happened before finding the actual name
            logging.error(f"Error adding exercise '{exercise_name}': {e}")
            # self.driver.save_screenshot(f"error_add_exercise_{exercise_name}.png") # Optional screenshot
            return False
        except Exception as e:
            # Log with original requested name
            logging.error(
                f"An unexpected error occurred adding exercise '{exercise_name}': {e}")
            # self.driver.save_screenshot(f"unexpected_error_add_exercise_{exercise_name}.png") # Optional screenshot
            return False

    def click_workout_fuzzy(self, workout_type: str) -> bool:
        """Finds and clicks a workout link by using the workout search bar first,
           trying variations if the initial search fails.
        """
        # Convert workout_type to lowercase for consistency
        workout_type_lower = workout_type.lower()

        # --- Define Search Terms --- START ---
        search_terms = [workout_type_lower]  # Start with the original term
        # Add simple variations (e.g., singular for plural)
        if workout_type_lower.endswith('s'):
            search_terms.append(workout_type_lower[:-1])  # Add singular form
        # Add more variations if needed based on common workout names
        # Example: if workout_type_lower == 'chest_tris': search_terms.extend(['chest', 'tris'])
        logging.info(f"Search terms to try: {search_terms}")
        # --- Define Search Terms --- END ---

        # --- Locate Search Bar Once --- START ---
        workout_search_locator = (
            By.CSS_SELECTOR, "input[placeholder*='Search by name, group, tag']")
        search_input = None
        try:
            search_input = self.wait.until(
                EC.element_to_be_clickable(workout_search_locator))
            logging.info("Located workout search bar successfully.")
        except (TimeoutException, NoSuchElementException) as search_err:
            logging.error(
                f"CRITICAL: Could not find the workout search bar: {search_err}")
            return False  # Cannot proceed without the search bar
        # --- Locate Search Bar Once --- END ---

        # --- Loop Through Search Terms --- START ---
        for term_index, search_term in enumerate(search_terms):
            logging.info(
                f"Attempt {term_index + 1}: Searching for workout using term '{search_term}'...")
            try:
                # Clear and type search term
                search_input.click()
                search_input.send_keys(Keys.CONTROL + "a")
                search_input.send_keys(Keys.DELETE)
                time.sleep(0.3)
                search_input.send_keys(search_term)
                logging.info(f"Typed '{search_term}'. Waiting for filter...")
                time.sleep(3)  # Increased wait for filter results to stabilize

                # --- Attempt to Find Link in Filtered List --- START ---
                workout_link_locator = (
                    By.XPATH,
                    f"//div[contains(@data-testid, 'grid-row')]//p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{search_term}') and contains(@data-testid, 'workoutGrid-workoutName')]/ancestor::a[1]"
                )
                try:
                    # Short wait specifically for the link after filtering
                    workout_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(workout_link_locator))
                    logging.info(
                        f"SUCCESS: Found workout link containing '{search_term}'. Clicking...")
                    self.driver.execute_script(
                        "arguments[0].click();", workout_link)
                    time.sleep(3)  # Wait for workout page
                    return True  # Found and clicked!

                except TimeoutException:
                    logging.warning(
                        f"Link containing '{search_term}' not found after searching for '{search_term}'.")
                    # Continue to the next search term if available
                # --- Attempt to Find Link in Filtered List --- END ---

            except Exception as e:
                logging.error(
                    f"Error during search attempt for term '{search_term}': {e}")
                # Optionally continue to next term or break/return false
                # Let's continue for now

        # --- Loop Through Search Terms --- END ---

        # If loop completes without finding the link
        logging.error(
            f"Could not find workout link for '{workout_type_lower}' after trying terms: {search_terms}")
        logging.error(
            f"Current URL at final failure: {self.driver.current_url}")
        # self.driver.save_screenshot(f"error_find_link_failed_all_searches_{workout_type}.png")
        return False

    def click_program(self, program_week_name):
        """Clicks on a program link with a dynamic week name."""
        try:
            logging.info(f"Clicking on program: '{program_week_name}'...")
            program_link_locator = (
                By.XPATH, f"//a[contains(@class, 'section-link') and .//p[@class='tz-sp color--black text-overflow-none' and text()='{program_week_name}']]")
            program_link = self.wait.until(
                EC.element_to_be_clickable(program_link_locator))
            program_link.click()
            logging.info(
                f"Successfully clicked on program: '{program_week_name}'.")
            time.sleep(2)  # Wait for program page to load
            return True
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            logging.error(f"Error clicking program '{program_week_name}': {e}")
            return False
        except Exception as e:
            logging.error(
                f"Unexpected error clicking program '{program_week_name}': {e}")
            return False

    def create_workout_back_day(self, program_week_name):
        """Creates a workout named 'Back Day' within the specified program."""
        try:
            logging.info("Starting workout creation 'Back Day'...")

            # --- Step 1: Click the program (assuming already on Training Program page) ---
            # Use dynamic program name function
            if not self.click_program(program_week_name):
                logging.warning(
                    f"Failed to click program '{program_week_name}', stopping workout creation.")
                return False  # Exit if program click failed
            else:
                logging.info(
                    f"Successfully clicked program '{program_week_name}'. Continuing workout creation.")

            # --- Step 1.5:  Try to dismiss modal by clicking 'Save' again ---
            try:
                save_button_after_program_create = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@data-testid='dialog-defaultFooter-confirm-button']")))
                save_button_after_program_create.click()
                logging.info(
                    "Attempted to dismiss program creation modal by re-clicking 'Save'.")
                time.sleep(1)  # Wait for modal to close
            except (TimeoutException, NoSuchElementException):
                logging.info(
                    "Could not find 'Save' button after program creation, assuming modal is already closed or not present.")
                pass  # Modal might already be gone or not present

            # --- Step 2: Click "New" button ---
            try:
                new_workout_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@title='Create new workout' and contains(@class, 'btn--blue') and .//span[text()='New']]")))
                new_workout_button.click()
                logging.info("Clicked 'New' workout button.")
                time.sleep(1)  # Wait for popup
            except Exception as e:
                logging.error(f"Error clicking 'New' workout button: {e}")
                return False

            # --- Step 3: Click workout name input ---
            try:
                workout_name_input = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "t_workoutname")))
                workout_name_input.click()
                logging.info("Clicked workout name input.")
                time.sleep(0.3)
            except Exception as e:
                logging.error(f"Error clicking workout name input: {e}")
                return False

            # --- Step 4: Type "Back Day" ---
            try:
                workout_name_input = self.driver.find_element(
                    By.ID, "t_workoutname")  # Re-find for staleness
                workout_name_input.send_keys("Back Day")
                logging.info("Typed 'Back Day' into workout name input.")
                time.sleep(0.3)
            except Exception as e:
                logging.error(
                    f"Error typing 'Back Day' into workout name input: {e}")
                return False

            # --- Step 5: Click "START BUILDING" ---
            try:
                start_building_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@id='btn_workout_buildNew_startBuilding' and @data-testid='workoutBuilder-startBuildingButton']")))
                start_building_button.click()
                logging.info("Clicked 'START BUILDING' button.")
                time.sleep(2)  # Wait for workout builder to load
            except Exception as e:
                logging.error(f"Error clicking 'START BUILDING' button: {e}")
                return False

            logging.info("Workout creation 'Back Day' completed successfully.")
            return True

        except Exception as e:
            logging.error(f"Error during workout creation 'Back Day': {e}")
            return False

    def save_workout(self) -> bool:
        """Clicks the final 'Save' button in the workout builder."""
        try:
            save_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='workoutBuilder-saveBtn']")
            save_button = self.wait.until(
                EC.element_to_be_clickable(save_button_locator)
            )
            save_button.click()
            logging.info("Clicked the final 'Save' button for the workout.")
            time.sleep(5)  # Allow time for save and page transition
            return True
        except Exception as e:
            logging.error(f"Error clicking the final workout Save button: {e}")
            return False

    def remove_exercise(self, exercise_name):
        """Removes an exercise from the workout by dragging its hamburger icon, using fuzzy matching first."""
        actual_exercise_name_to_remove = None  # Initialize for error logging
        try:
            logging.info(
                f"Attempting to remove exercise: {exercise_name} using drag-and-drop method..."
            )

            # --- Step 1: Find all visible exercise names --- #
            logging.info("Finding all currently listed exercises...")
            exercise_name_elements = self.driver.find_elements(
                By.XPATH, "//div[@class='exerciseList-exercise__name ']")
            current_exercise_names = [
                elem.text for elem in exercise_name_elements if elem.text and elem.is_displayed()]
            if not current_exercise_names:
                logging.error(
                    "Could not find any exercise names in the current workout list.")
                return False
            logging.info(f"Found exercises: {current_exercise_names}")

            # --- Step 2: Perform Fuzzy Match --- #
            actual_exercise_name_to_remove = self.find_closest_exercise(
                exercise_name, current_exercise_names)

            if not actual_exercise_name_to_remove:
                logging.error(
                    f"Could not find a close match for '{exercise_name}' in the current workout list: {current_exercise_names}. Cannot remove.")
                return False
            elif actual_exercise_name_to_remove != exercise_name:
                logging.info(
                    f"Fuzzy match found: Requested '{exercise_name}', targeting '{actual_exercise_name_to_remove}' for removal.")
            else:
                logging.info(
                    f"Exact match found: '{actual_exercise_name_to_remove}'")

            # --- Step 3: Locate Hamburger using Actual Name --- #
            logging.info(
                f"Locating hamburger icon for exercise: {actual_exercise_name_to_remove}...")
            # Corrected XPath: Find title, go to ancestor div, find hamburger within.
            # Using [1] to be more specific if multiple ancestors match.
            hamburger_locator = (By.XPATH,
                                 f"//div[@class='exerciseList-exercise__name ' and @title='{actual_exercise_name_to_remove}']"
                                 f"/ancestor::div[contains(@class, 'workoutExercise')][1]"
                                 f"//div[@data-testid='workoutBuilder-hamburgerMenu']")

            try:
                # Wait for the hamburger to be clickable
                hamburger = self.wait.until(
                    EC.element_to_be_clickable(hamburger_locator))
                logging.info(
                    f"Found hamburger icon for '{actual_exercise_name_to_remove}'.")
            except TimeoutException:
                logging.warning(
                    f"Hamburger icon for '{actual_exercise_name_to_remove}' not found or clickable. Scrolling might be needed.")
                # Attempt scroll and retry
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                try:
                    hamburger = self.wait.until(
                        EC.element_to_be_clickable(hamburger_locator))
                    logging.info(
                        f"Found hamburger icon for '{actual_exercise_name_to_remove}' after scrolling.")
                except TimeoutException:
                    logging.error(
                        f"Hamburger icon for '{actual_exercise_name_to_remove}' still not found after scroll.")
                    return False

            # --- Step 4: Perform Drag and Drop --- #
            logging.info(
                f"Performing drag and drop action for '{actual_exercise_name_to_remove}'...")
            try:
                actions = ActionChains(self.driver)
                # Drag significantly to the right
                actions.click_and_hold(hamburger).move_by_offset(
                    800, 0).release().perform()
                time.sleep(2)  # Allow time for action and UI update
                logging.info("Drag and drop action performed.")
            except Exception as drag_err:
                logging.error(f"Error during drag and drop action: {drag_err}")
                return False

            # --- Step 5: Verification --- #
            logging.info(
                f"Verifying removal of '{actual_exercise_name_to_remove}'...")
            try:
                # Re-check using the *actual* name locator for the title div
                verification_locator = (By.XPATH,
                                        f"//div[@class='exerciseList-exercise__name ' and @title='{actual_exercise_name_to_remove}']")
                # Wait for a short time to see if it disappears
                WebDriverWait(self.driver, 3).until_not(
                    EC.presence_of_element_located(verification_locator))
                logging.info(
                    f"Successfully removed exercise '{actual_exercise_name_to_remove}' (element no longer found).")
            except TimeoutException:
                # If it's still present after the wait, removal likely failed
                logging.warning(
                    f"Exercise '{actual_exercise_name_to_remove}' still present after drag attempt.")
                # Optionally return False here if strict verification is needed

            return True

        except Exception as e:
            # Use actual_exercise_name_to_remove in the error message if it was determined
            matched_name = actual_exercise_name_to_remove if actual_exercise_name_to_remove else 'N/A'
            logging.error(
                f"An unexpected error occurred while removing '{exercise_name}' (matched as '{matched_name}'): {e}")
            return False

    def modify_exercise_goals(self, exercise_name, weight, reps):
        """Modifies the goals for an existing exercise in the reps field.
        Sets the reps field to format: 'Goals: W(weight), R(reps)'
        Example: 'Goals: W(25), R(10)'
        """
        try:
            logging.info(
                f"Modifying goals for exercise: {exercise_name} to W({weight}), R({reps})")

            # Format the goals string
            goals_text = f"Goals: W({weight}), R({reps})"

            # Find the exercise container in the workout list
            exercise_in_list_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{exercise_name}']/ancestor::div[contains(@class, 'workoutExercise')]")

            try:
                workout_list_exercise_div = self.wait.until(
                    EC.presence_of_element_located(exercise_in_list_locator))
                logging.info(f"Found container for '{exercise_name}'.")
            except TimeoutException:
                logging.error(
                    f"Could not find container for '{exercise_name}' in the workout list.")
                return False

            # Find and modify the reps input field
            try:
                reps_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")
                reps_input = workout_list_exercise_div.find_element(
                    *reps_input_locator)
                reps_input.click()
                time.sleep(0.2)

                # Clear the field completely
                reps_input.send_keys(Keys.CONTROL + "a")
                reps_input.send_keys(Keys.DELETE)
                time.sleep(0.2)

                # Set the new goals text
                reps_input.send_keys(goals_text)
                logging.info(f"Set goals to: {goals_text} for {exercise_name}")
                time.sleep(0.5)
                return True

            except Exception as e:
                logging.error(
                    f"Error setting goals for '{exercise_name}': {e}")
                return False

        except Exception as e:
            logging.error(
                f"Error modifying exercise goals for '{exercise_name}': {e}")
            return False

    def find_and_click_workout_by_name(self, workout_name):
        """Finds and clicks a workout by its exact name in the program view."""
        try:
            logging.info(f"Looking for workout: '{workout_name}'")

            # Wait for the workout list to load
            time.sleep(2)

            # Try multiple selectors based on the actual HTML structure
            workout_selectors = [
                # Using data-testid for workout name (most reliable)
                f"//p[contains(@data-testid, 'workoutGrid-workoutName') and text()='{workout_name}']/ancestor::a[1]",
                # Direct text match in workout name paragraph
                f"//p[contains(@class, 'tz-lp') and contains(@class, 'color--blue') and text()='{workout_name}']/ancestor::a[1]",
                # Case insensitive match
                f"//p[contains(@data-testid, 'workoutGrid-workoutName') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workout_name.lower()}')]/ancestor::a[1]",
                # Generic workout link with text
                f"//a[contains(@href, '/workout/') and .//p[text()='{workout_name}']]",
                # Fallback to original selectors
                f"//a[contains(@class, 'section-link') and .//p[text()='{workout_name}']]",
                f"//a[.//p[@class='tz-sp color--black text-overflow-none' and text()='{workout_name}']]",
                f"//div[contains(@class, 'workout') and .//span[text()='{workout_name}']]//a",
                f"//div[text()='{workout_name}']/ancestor::a[1]"
            ]

            for i, selector in enumerate(workout_selectors, 1):
                try:
                    logging.info(f"Trying selector {i}: {selector}")
                    workout_link = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector)))

                    logging.info(f"Found workout link, attempting to click...")
                    workout_link.click()
                    logging.info(
                        f"Successfully clicked workout: '{workout_name}' using selector {i}")
                    time.sleep(3)  # Wait for workout to load
                    return True
                except TimeoutException as e:
                    logging.info(f"Selector {i} failed: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error with selector {i}: {e}")
                    continue

            # If all selectors fail, try to find any workout elements and log them for debugging
            logging.info(
                "All selectors failed. Looking for any workout elements...")
            try:
                workout_elements = self.driver.find_elements(
                    By.XPATH, "//p[contains(@data-testid, 'workoutGrid-workoutName')]")

                if workout_elements:
                    logging.info("Found workout elements:")
                    for element in workout_elements[:5]:  # Log first 5
                        workout_text = element.text
                        logging.info(
                            f"  - Available workout: '{workout_text}'")

                # Also try to find workout links
                workout_links = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, '/workout/')]")
                logging.info(
                    f"Found {len(workout_links)} workout links in total")

            except Exception as debug_error:
                logging.error(f"Error during debugging: {debug_error}")

            logging.error(f"Could not find workout: '{workout_name}'")
            return False

        except Exception as e:
            logging.error(f"Error clicking workout '{workout_name}': {e}")
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


if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    client_name = "Shannon Birch"
    # Renamed variable to reflect fuzzy search intent
    target_workout_type = "Back"  # e.g., "Back", "Chest", "Leg"

    # --- Define list of actions to perform sequentially ---
    actions_to_perform = [
        # Example: Remove one, add another
        {'action': 'remove', 'exercise_name': 'Barbell Bent Over Row'},
        {'action': 'add', 'exercise_name': 'Seated Bicep Curl',
            'sets': '3', 'reps': '12'}
        # Add more action dictionaries here if needed
    ]
    # -----------------------------------------------------

    trainerize_bot = TrainerizeAutomation()
    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()

            if trainerize_bot.navigate_to_client(client_name):
                if trainerize_bot.navigate_to_training_program():
                    current_program_name = trainerize_bot.find_current_workout_program()
                    if current_program_name:
                        print(f"Found current program: {current_program_name}")
                        if trainerize_bot.click_program(current_program_name):
                            print(
                                f"Successfully clicked on program: {current_program_name}")
                            if trainerize_bot.click_workout_fuzzy(target_workout_type):
                                print(
                                    f"Successfully clicked on workout containing '{target_workout_type}'")
                                if trainerize_bot.click_edit_workout():
                                    print("Entered workout edit mode.")
                                    all_actions_successful = True  # Track overall success

                                    # --- Loop through actions ---
                                    for action_item in actions_to_perform:
                                        action_type = action_item.get('action')
                                        exercise_name = action_item.get(
                                            'exercise_name')

                                        if not action_type or not exercise_name:
                                            logging.warning(
                                                f"Skipping invalid action item: {action_item}")
                                            all_actions_successful = False
                                            continue  # Skip to next action

                                        action_successful_this_time = False
                                        print(
                                            f"--- Performing action: {action_type.upper()} '{exercise_name}' ---")

                                        if action_type == "add":
                                            sets = action_item.get(
                                                'sets', '3')  # Default sets
                                            reps = action_item.get(
                                                'reps', '12')  # Default reps
                                            if trainerize_bot.add_exercise(exercise_name, sets, reps):
                                                action_successful_this_time = True
                                                print(
                                                    f"Successfully added '{exercise_name}'.")
                                            else:
                                                print(
                                                    f"Failed to add '{exercise_name}'.")
                                                all_actions_successful = False
                                        elif action_type == "remove":
                                            if trainerize_bot.remove_exercise(exercise_name):
                                                action_successful_this_time = True
                                                print(
                                                    f"Successfully removed '{exercise_name}'.")
                                            else:
                                                print(
                                                    f"Failed to remove '{exercise_name}'.")
                                                all_actions_successful = False
                                        else:
                                            print(
                                                f"Unknown action type: {action_type} for exercise {exercise_name}")
                                            all_actions_successful = False

                                        if not action_successful_this_time:
                                            print(
                                                f"Action '{action_type}' for exercise '{exercise_name}' failed. Continuing with next action...")
                                            # Decide if you want to stop all actions if one fails:
                                            # break

                                    # --- Save after attempting all actions ---
                                    print(
                                        "--- Finished all actions. Attempting to save... ---")
                                    if trainerize_bot.save_workout():
                                        if all_actions_successful:
                                            print(
                                                "Workout saved successfully after all actions completed.")
                                        else:
                                            print(
                                                "Workout saved, but one or more actions may have failed.")
                                    else:
                                        print(
                                            "Failed to save the workout after completing actions.")
                                    # -----------------------------------------
                                else:
                                    print(
                                        "Failed to click the 'Edit workout' button.")
                            else:
                                print(
                                    f"Failed to click on workout containing '{target_workout_type}'")
                        else:
                            print(
                                f"Failed to click on program: {current_program_name}")
                    else:
                        print("Could not find the current workout program.")
                else:
                    print(f"Failed to navigate to the 'Training Program' tab.")
            else:
                print(f"Failed to navigate to client: {client_name}")
        else:
            print("Login failed.")

        input("Press Enter to close...")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()
