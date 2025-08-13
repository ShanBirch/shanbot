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
import json
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys


class TrainerizeAutomation:
    def __init__(self, chrome_driver_path=None, chrome_executable_path=None):
        logging.basicConfig(
            level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome...")

        # Default paths - can be overridden
        self.chromedriver_path = chrome_driver_path or "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = chrome_executable_path or "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"

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
        chrome_options.binary_location = self.chrome_executable_path

        try:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Chrome initialized successfully!")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

        # Load exercise list from file if it exists, otherwise use the default list
        self.load_exercise_list()

    def load_exercise_list(self, file_path="exercises.json"):
        """Load exercise list from a JSON file if it exists, otherwise use the default list"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.exercise_list = json.load(f)
                logging.info(
                    f"Loaded {len(self.exercise_list)} exercises from {file_path}")
            else:
                # Default exercise list (using the one from the original script)
                self.exercise_list = [
                    "2 Handed Dumbbell Bent Over Rows", "2 Handed Dumbbell Rear Delt Row",
                    # ... (rest of the default exercise list)
                    "Barbell Bench Chest Press", "B.B Bent Over Row", "Back Squat",
                    "Cable Bench Triceps Push Down", "Incline Dumbbell Bench press",
                    "Lat Pull Down Wide Grip", "Barbell Bent Over Row Pause", "Seated row",
                    "Alternating Hammer Curls", "Concentrated Bicep Curls",
                    "Arnold Press Eccentric", "Lateral Raise Pause", "Face Pulls", "Plank", "Cable Crunch",
                    "Barbell Back Squat Pause", "Bulgarian Lunge", "Dumbbell Romanian Deadlifts",
                    "Leg Extensions", "Lying Leg Curl",
                    "Bench Easy Curl Bar Bicep Curls", "Cable Hammer Curls", "Close Grip Barbell Bench Press",
                    "Cable push downs", "Hanging knee tucks"
                ]
                # Save the default exercise list to a file for future use
                with open(file_path, 'w') as f:
                    json.dump(self.exercise_list, f, indent=2)
                logging.info(
                    f"Created default exercise list with {len(self.exercise_list)} exercises in {file_path}")
        except Exception as e:
            logging.error(f"Error loading exercise list: {e}")
            self.exercise_list = []

    def save_exercise_list(self, file_path="exercises.json"):
        """Save the current exercise list to a JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.exercise_list, f, indent=2)
            logging.info(
                f"Saved {len(self.exercise_list)} exercises to {file_path}")
        except Exception as e:
            logging.error(f"Error saving exercise list: {e}")

    def add_exercise_to_list(self, exercise_name):
        """Add an exercise to the exercise list if it doesn't exist"""
        if exercise_name not in self.exercise_list:
            self.exercise_list.append(exercise_name)
            logging.info(f"Added exercise '{exercise_name}' to exercise list")
            self.save_exercise_list()
            return True
        return False

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

    def navigate_to_training_program(self):
        """Navigates to the 'Training Program' tab."""
        try:
            logging.info("Navigating to the 'Training Program' tab...")
            training_program_link_locator = (
                By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']")
            training_program_link = self.wait.until(
                EC.element_to_be_clickable(training_program_link_locator))
            training_program_link.click()
            time.sleep(2)  # Wait for the page to load
            logging.info(
                "Successfully navigated to the 'Training Program' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"Error navigating to the 'Training Program' tab: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def add_exercise(self, exercise_name, sets="3", reps="10"):
        """
        Add exercise implementation that uses the 'Load More' button approach
        based on the actual interface structure.
        """
        try:
            logging.info(f"Adding exercise: {exercise_name}...")

            # Wait for the exercise library to load
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".exerciseLibrary-wrap")))
                time.sleep(1)  # Short wait for visual elements to render
                logging.info("Exercise library loaded")
            except TimeoutException:
                logging.error("Exercise library not found!")
                self.driver.save_screenshot("library_not_found.png")
                return False

            # Step 1: First reset any existing search
            search_input = None
            try:
                search_input = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                     "input[placeholder='Search for an exercise']")
                ))

                # Clear any existing search
                search_input.click()
                search_input.clear()
                search_input.send_keys(Keys.CONTROL + "a")
                search_input.send_keys(Keys.DELETE)
                time.sleep(0.5)

                # Verify it's cleared
                current_value = search_input.get_attribute("value")
                if current_value:
                    logging.warning(
                        f"Search input still contains: '{current_value}', trying backup clear")
                    # Try JavaScript clear
                    self.driver.execute_script(
                        "arguments[0].value = '';", search_input)

                logging.info("Cleared previous search")
            except Exception as e:
                logging.warning(f"Error clearing previous search: {e}")
                # Continue anyway

            # Step 2: Now search for the current exercise
            try:
                if not search_input:
                    search_input = self.wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         "input[placeholder='Search for an exercise']")
                    ))

                logging.info("Found search input field")

                # Click and focus
                search_input.click()
                time.sleep(0.5)

                # Type the exercise name character by character
                for char in exercise_name:
                    search_input.send_keys(char)
                    time.sleep(0.05)

                logging.info(f"Searching for: {exercise_name}")
                time.sleep(1)  # Short wait for search to start

                # CRITICAL FIX: Dismiss the search popup by clicking on the instructions textarea
                try:
                    logging.info(
                        "Attempting to dismiss search popup by clicking on instructions textarea...")

                    # Find the instructions textarea and click it to dismiss the popup
                    instructions_textarea = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "textarea.ant-input.workoutBuilder__instructions"
                    )

                    # Take screenshot before clicking
                    self.driver.save_screenshot("before_dismiss_popup.png")

                    # Click the textarea to dismiss popup
                    instructions_textarea.click()
                    logging.info(
                        "Clicked on instructions textarea to dismiss popup")

                    # Take screenshot after clicking
                    time.sleep(1)
                    self.driver.save_screenshot("after_dismiss_popup.png")
                except Exception as e:
                    logging.warning(
                        f"Failed to dismiss popup via textarea: {e}")
                    # Try alternative method - click anywhere else
                    try:
                        # Click on a safe area (like the page background)
                        body_element = self.driver.find_element(
                            By.TAG_NAME, "body")
                        action = ActionChains(self.driver)
                        action.move_to_element_with_offset(
                            body_element, 100, 100).click().perform()
                        logging.info(
                            "Used alternative method to dismiss popup")
                    except Exception as e2:
                        logging.warning(
                            f"Alternative popup dismiss also failed: {e2}")

                # Wait for search results after dismissing popup
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Couldn't use search: {e}")
                # Continue with the Load More approach

            # Step 3: Look through visible exercises
            matched_exercise = None
            load_more_attempts = 0
            max_load_more_attempts = 20
            previously_seen_exercises = set()

            while load_more_attempts < max_load_more_attempts and not matched_exercise:
                # Get all currently visible exercise cards
                exercise_cards = self.driver.find_elements(
                    By.CSS_SELECTOR, ".exerciseLibrary-exercise")
                new_cards_count = 0

                logging.info(
                    f"Found {len(exercise_cards)} visible exercise cards")

                # Check each card for a match
                for card in exercise_cards:
                    try:
                        # Extract the exercise name from the card
                        card_text = card.find_element(
                            By.CSS_SELECTOR, "p").text.strip()

                        # Skip if we've already seen this card
                        if card_text in previously_seen_exercises:
                            continue

                        # Mark as seen
                        previously_seen_exercises.add(card_text)
                        new_cards_count += 1

                        # Check if this is our target exercise
                        if exercise_name.lower() in card_text.lower():
                            matched_exercise = card
                            logging.info(
                                f"Found matching exercise: '{card_text}'")
                            break
                    except Exception as e:
                        logging.warning(
                            f"Error extracting text from card: {e}")

                # If we found a match, break the loop
                if matched_exercise:
                    break

                # If no new cards were found (already loaded everything)
                if new_cards_count == 0 and load_more_attempts > 0:
                    logging.info(
                        "No new exercises loaded, reached end of list")
                    break

                # Click "Load More" button if not found
                try:
                    load_more_button = self.driver.find_element(
                        By.XPATH, "//span[contains(@class, 'blueLink') and text()='Load More']")
                    load_more_button.click()
                    logging.info(
                        f"Clicked 'Load More' button (attempt {load_more_attempts + 1})")
                    time.sleep(2)  # Wait for more exercises to load
                    load_more_attempts += 1
                except Exception as e:
                    logging.warning(
                        f"Could not find or click 'Load More' button: {e}")
                    break

            # If we didn't find the exercise, try a fuzzy match on what we've seen
            if not matched_exercise and previously_seen_exercises:
                logging.info(
                    "Exercise not found with exact match, trying fuzzy matching...")

                # Find the closest match using similarity
                best_match = None
                best_score = 0
                target = exercise_name.lower()

                for seen_exercise in previously_seen_exercises:
                    # Simple similarity - count matching words
                    target_words = set(target.split())
                    seen_words = set(seen_exercise.lower().split())
                    common_words = target_words.intersection(seen_words)

                    if common_words:
                        score = len(common_words) / \
                            max(len(target_words), len(seen_words))
                        if score > best_score:
                            best_score = score
                            best_match = seen_exercise

                if best_match and best_score > 0.5:  # Threshold for similarity
                    logging.info(
                        f"Using fuzzy match: '{best_match}' (similarity: {best_score:.2f})")

                    # Now find this card
                    for card in self.driver.find_elements(By.CSS_SELECTOR, ".exerciseLibrary-exercise"):
                        try:
                            if card.find_element(By.CSS_SELECTOR, "p").text.strip() == best_match:
                                matched_exercise = card
                                break
                        except:
                            pass
                else:
                    logging.warning("No suitable fuzzy match found")

            # If we still don't have a match, try to pick a visible exercise that's similar
            if not matched_exercise:
                logging.warning(
                    f"Exercise '{exercise_name}' not found after {load_more_attempts} 'Load More' attempts")

                # Get existing categories in the name
                categories = ['Push', 'Pull', 'Squat', 'Bench',
                              'Press', 'Row', 'Curl', 'Extension', 'Raise']
                target_categories = [
                    c for c in categories if c.lower() in exercise_name.lower()]

                # Try to find any exercise matching the categories
                if target_categories:
                    logging.info(
                        f"Looking for alternative exercise with categories: {target_categories}")

                    for card in self.driver.find_elements(By.CSS_SELECTOR, ".exerciseLibrary-exercise"):
                        try:
                            card_text = card.find_element(
                                By.CSS_SELECTOR, "p").text.strip()
                            for category in target_categories:
                                if category.lower() in card_text.lower():
                                    matched_exercise = card
                                    logging.info(
                                        f"Selected alternative exercise: '{card_text}'")
                                    break
                            if matched_exercise:
                                break
                        except:
                            pass

                if not matched_exercise:
                    logging.error(
                        f"Could not find exercise '{exercise_name}' or suitable alternative")
                    self.driver.save_screenshot("exercise_not_found.png")
                    return False

            # Click on the matched exercise
            try:
                logging.info("Clicking matched exercise...")

                # Scroll to the element to make sure it's visible
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", matched_exercise)
                time.sleep(1)

                # Get the exercise name (for later use)
                exercise_text = ""
                try:
                    exercise_text = matched_exercise.find_element(
                        By.CSS_SELECTOR, "p").text.strip()
                except:
                    pass

                # Try standard click
                try:
                    matched_exercise.click()
                    logging.info("Standard click successful")
                except Exception as e:
                    logging.warning(f"Standard click failed: {e}")
                    # Try JavaScript click
                    try:
                        self.driver.execute_script(
                            "arguments[0].click();", matched_exercise)
                        logging.info("JavaScript click successful")
                    except Exception as e2:
                        logging.error(f"JavaScript click also failed: {e2}")
                        return False

                # Wait for the "Add to Workout" button to appear and click it
                logging.info("Looking for 'Add to Workout' button...")

                # Take a screenshot to see what's being displayed
                self.driver.save_screenshot("before_add_button.png")

                # Try multiple button locators
                add_button = None
                add_button_locators = [
                    (By.XPATH, "//button[contains(., 'Add to Workout')]"),
                    (By.XPATH, "//button[.//span[text()='Add to Workout']]"),
                    (By.XPATH, "//button[contains(@class, 'gtBtn-blue')]"),
                    (By.CSS_SELECTOR, "button.btn--blue"),
                    (By.CSS_SELECTOR, "button.ant-btn.btn.btn--medium.btn--blue"),
                    (By.XPATH, "//button[@style='min-width: 70px;']")
                ]

                for locator in add_button_locators:
                    try:
                        add_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(locator))
                        logging.info(
                            f"Found 'Add to Workout' button with locator: {locator}")
                        break
                    except:
                        pass

                if not add_button:
                    logging.error("Could not find 'Add to Workout' button")
                    self.driver.save_screenshot("add_button_not_found.png")
                    return False

                # Click the Add to Workout button
                try:
                    # Save button HTML for debugging
                    button_html = add_button.get_attribute('outerHTML')
                    logging.info(f"Add button HTML: {button_html}")

                    # Try direct click
                    add_button.click()
                    logging.info(
                        "Clicked 'Add to Workout' button successfully")
                except Exception as e:
                    logging.warning(
                        f"Standard click on add button failed: {e}")
                    try:
                        # Try JavaScript click
                        self.driver.execute_script(
                            "arguments[0].click();", add_button)
                        logging.info(
                            "Clicked 'Add to Workout' button with JavaScript")
                    except Exception as e2:
                        logging.error(
                            f"All methods to click add button failed: {e2}")
                        self.driver.save_screenshot(
                            "add_button_click_failed.png")
                        return False

                # Wait for the exercise to be added to the workout list
                time.sleep(2)

            except Exception as e:
                logging.error(
                    f"Error during exercise selection or adding: {e}")
                self.driver.save_screenshot("selection_error.png")
                return False

            # Find the exercise in the workout list and set sets/reps
            try:
                # Find the added exercise row in the workout list (left side panel)
                logging.info(
                    "Looking for exercise in the left-side workout list...")

                # Take a screenshot to see the state after adding the exercise
                self.driver.save_screenshot("after_adding_exercise.png")

                # First try to find the most recently added exercise (usually last in the list)
                # Several strategies to find the exercise list items
                exercise_locators = [
                    # Try to find all exercises in the list
                    (By.CSS_SELECTOR, "div.exerciseList-exercise"),
                    (By.CSS_SELECTOR, "div.workoutExercise"),
                    (By.XPATH,
                     "//div[contains(@class, 'exerciseList')]/div[contains(@class, 'workoutExercise')]"),
                    # More general selectors as fallback
                    (By.XPATH,
                     "//div[contains(@class, 'exerciseList-exercise__name')]"),
                ]

                # Try each locator strategy
                exercise_items = []
                for locator in exercise_locators:
                    try:
                        items = self.driver.find_elements(*locator)
                        if items:
                            exercise_items = items
                            logging.info(
                                f"Found {len(items)} exercise items with locator: {locator}")
                            break
                    except:
                        continue

                if not exercise_items:
                    logging.warning("Could not find any exercises in the list")
                    self.driver.save_screenshot("no_exercises_found.png")
                    return False

                # Get the last exercise item (most recently added)
                last_exercise = exercise_items[-1]
                logging.info(
                    f"Selected the last exercise in the list (total: {len(exercise_items)})")

                # Find sets input within this exercise item
                try:
                    # First try to find by data-testid within the exercise
                    sets_input = None
                    try:
                        # Try to find directly within the exercise item
                        sets_input = last_exercise.find_element(
                            By.CSS_SELECTOR, "input[data-testid='workoutBuilder-exerciseSetInput']")
                    except:
                        # Try to find in the entire document but focus on the most recent
                        all_set_inputs = self.driver.find_elements(
                            By.CSS_SELECTOR, "input[data-testid='workoutBuilder-exerciseSetInput']")
                        if all_set_inputs:
                            # Get the last one (most recently added)
                            sets_input = all_set_inputs[-1]

                    if not sets_input:
                        raise Exception("Sets input not found")

                    # Set the sets value
                    logging.info("Setting sets value...")
                    sets_input.click()
                    time.sleep(0.5)
                    # Clear using multiple methods for reliability
                    sets_input.clear()
                    time.sleep(0.3)
                    sets_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.3)
                    sets_input.send_keys(Keys.DELETE)
                    time.sleep(0.3)
                    # Type new value
                    sets_input.send_keys(sets)
                    logging.info(f"Sets value set to: {sets}")
                    time.sleep(0.5)
                except Exception as e:
                    logging.error(f"Error setting sets value: {e}")
                    self.driver.save_screenshot("sets_input_error.png")

                # Find reps input within this exercise item
                try:
                    # First try to find by data-testid within the exercise
                    reps_input = None
                    try:
                        # Try to find directly within the exercise item
                        reps_input = last_exercise.find_element(
                            By.CSS_SELECTOR, "input[data-testid='workoutBuilder-recordTypeInput']")
                    except:
                        # Try to find in the entire document but focus on the most recent
                        all_rep_inputs = self.driver.find_elements(
                            By.CSS_SELECTOR, "input[data-testid='workoutBuilder-recordTypeInput']")
                        if all_rep_inputs:
                            # Get the last one (most recently added)
                            reps_input = all_rep_inputs[-1]

                    if not reps_input:
                        raise Exception("Reps input not found")

                    # Set the reps value
                    logging.info("Setting reps value...")
                    reps_input.click()
                    time.sleep(0.5)
                    # Clear using multiple methods for reliability
                    reps_input.clear()
                    time.sleep(0.3)
                    reps_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.3)
                    reps_input.send_keys(Keys.DELETE)
                    time.sleep(0.3)
                    # Type new value
                    reps_input.send_keys(reps)
                    logging.info(f"Reps value set to: {reps}")
                    time.sleep(0.5)
                except Exception as e:
                    logging.error(f"Error setting reps value: {e}")
                    self.driver.save_screenshot("reps_input_error.png")

                # Success if we got this far
                logging.info(
                    f"Exercise added successfully with {sets} sets and {reps} reps.")
                return True

            except Exception as e:
                logging.error(f"Error setting sets/reps for exercise: {e}")
                self.driver.save_screenshot("sets_reps_error.png")
                # Consider it partly successful if it was added to the workout
                return True

        except Exception as e:
            logging.error(
                f"Unexpected error adding exercise '{exercise_name}': {e}")
            self.driver.save_screenshot(
                f"unexpected_error_{exercise_name.replace(' ', '_')}.png")
            return False

    def create_program(self, program_week_name, weeks=8):
        """Creates a program with a specified name and number of weeks."""
        try:
            logging.info(f"Starting program creation '{program_week_name}'...")
            add_next_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "p.tz-p.color--blue.clickable")))
            add_next_button.click()
            logging.info("Clicked '+ Add next' button.")
            time.sleep(1)
            name_input = self.wait.until(
                EC.element_to_be_clickable((By.ID, "t_workoutplan_name")))
            name_input.click()
            logging.info("Clicked 'Training phase name' input.")
            time.sleep(0.5)
            name_input = self.driver.find_element(By.ID, "t_workoutplan_name")
            name_input.send_keys(program_week_name)
            logging.info(f"Typed '{program_week_name}' into the name input.")
            time.sleep(0.5)
            number_box = self.wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "ant-input-number-input")))
            number_box.click()
            logging.info("Clicked the number input box.")
            time.sleep(0.3)
            number_box.send_keys(Keys.BACKSPACE)
            logging.info("Pressed backspace in number box.")
            time.sleep(0.3)
            number_box.send_keys(str(weeks))
            logging.info(f"Typed '{weeks}' in number box.")
            time.sleep(0.3)
            save_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-testid='dialog-defaultFooter-confirm-button']")))
            save_button.click()
            logging.info("Clicked 'Save' button.")
            time.sleep(2)
            logging.info(
                f"Program creation '{program_week_name}' completed successfully.")
            return True

        except Exception as e:
            logging.error(
                f"Error during program creation '{program_week_name}': {e}")
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

    def create_workout(self, program_name, workout_name, exercises_list):
        """
        Generic method to create any workout with custom name and exercises.

        Args:
            program_name (str): The name of the program to add the workout to
            workout_name (str): The name of the workout to create
            exercises_list (list): List of dictionaries with exercise details 
                                  [{'name': 'Exercise Name', 'sets': '3', 'reps': '10'}, ...]

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logging.info(f"Starting workout creation '{workout_name}'...")

            # Click on the program
            if not self.click_program(program_name):
                logging.warning(
                    f"Failed to click program '{program_name}', stopping workout creation.")
                return False
            else:
                logging.info(
                    f"Successfully clicked program '{program_name}'. Continuing workout creation.")

            # Try to dismiss any dialogs that might be open
            try:
                save_button_after_program_create = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[@data-testid='dialog-defaultFooter-confirm-button']")
                ))
                save_button_after_program_create.click()
                logging.info(
                    "Attempted to dismiss program creation modal by re-clicking 'Save'.")
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                logging.info("No modal dialog found to dismiss.")
                pass

            # Click "New" workout button
            try:
                new_workout_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[@title='Create new workout' and contains(@class, 'btn--blue') and .//span[text()='New']]")
                ))
                new_workout_button.click()
                logging.info("Clicked 'New' workout button.")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error clicking 'New' workout button: {e}")
                return False

            # Enter workout name
            try:
                workout_name_input = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "t_workoutname")))
                workout_name_input.click()
                workout_name_input.send_keys(workout_name)
                logging.info(f"Named workout '{workout_name}'.")
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Error naming workout: {e}")
                return False

            # Click "START BUILDING" button
            try:
                start_building_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[@id='btn_workout_buildNew_startBuilding' and @data-testid='workoutBuilder-startBuildingButton']")
                ))
                start_building_button.click()
                logging.info("Clicked 'START BUILDING' button.")
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error clicking 'START BUILDING' button: {e}")
                return False

            logging.info(
                f"Workout builder loaded for '{workout_name}'. Now adding exercises...")

            # Add each exercise
            for exercise_details in exercises_list:
                exercise_name = exercise_details['name']
                sets = exercise_details.get('sets', "3")
                reps = exercise_details.get('reps', "10")

                logging.info(
                    f"Adding exercise: '{exercise_name}' with sets: '{sets}' and reps: '{reps}'...")
                if not self.add_exercise(exercise_name, sets, reps):
                    logging.error(
                        f"Failed to add exercise '{exercise_name}'. Workout creation may be incomplete.")
                else:
                    logging.info(
                        f"Successfully added exercise '{exercise_name}'.")

            # Save the workout
            save_workout_button_locator = (
                By.XPATH, "//button[@data-testid='workoutBuilder-saveBtn']")
            try:
                save_workout_button = self.wait.until(
                    EC.element_to_be_clickable(save_workout_button_locator))
                save_workout_button.click()
                logging.info("Clicked 'Save Workout' button.")
                time.sleep(3)  # Wait for save to complete
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as save_e:
                logging.error(
                    f"Error clicking 'Save Workout' button: {save_e}")
                return False

            logging.info(
                f"Workout creation '{workout_name}' with exercises completed and workout saved.")
            return True

        except Exception as e:
            logging.error(
                f"Error during workout creation '{workout_name}': {e}")
            return False

    def create_workout_program(self, client_name, program_config, recovery_file="workout_progress.json"):
        """
        Create a complete workout program based on a configuration dictionary with recovery capabilities.

        Args:
            client_name (str): Name of the client
            program_config (dict): Configuration dictionary with program details
            recovery_file (str): Path to file for saving/restoring progress

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load progress if it exists
            progress = self.load_progress(recovery_file)

            # Check if we're resuming or starting fresh
            if progress and progress.get('client') == client_name and progress.get('program') == program_config.get('program_name'):
                logging.info(
                    f"Resuming workout program creation for {client_name}, program: {progress.get('program')}")
                is_resuming = True
                completed_workouts = progress.get('completed_workouts', [])
                program_created = progress.get('program_created', False)
            else:
                logging.info(
                    f"Starting new workout program creation for {client_name}")
                is_resuming = False
                completed_workouts = []
                program_created = False

                # Reset progress file for new program
                self.save_progress(recovery_file, {
                    'client': client_name,
                    'program': program_config.get('program_name'),
                    'completed_workouts': [],
                    'program_created': False
                })

            # Navigate to client if we're not resuming or program not created yet
            if not is_resuming or not program_created:
                # First navigate to client
                for attempt in range(3):  # Try up to 3 times
                    if self.navigate_to_client(client_name):
                        break
                    else:
                        logging.warning(
                            f"Failed to navigate to client (attempt {attempt+1}/3). Retrying...")
                        self.reload_page()
                        time.sleep(3)
                else:  # If all attempts failed
                    logging.error(
                        f"Failed to navigate to client: {client_name} after multiple attempts")
                    return False

                # Navigate to Training Program tab
                for attempt in range(3):  # Try up to 3 times
                    if self.navigate_to_training_program():
                        break
                    else:
                        logging.warning(
                            f"Failed to navigate to Training Program tab (attempt {attempt+1}/3). Retrying...")
                        self.reload_page()
                        time.sleep(3)
                else:  # If all attempts failed
                    logging.error(
                        "Failed to navigate to Training Program tab after multiple attempts")
                    return False

            # Create the program if it hasn't been created yet
            program_name = program_config.get(
                'program_name', 'New Workout Program')
            weeks = program_config.get('weeks', 8)

            if not program_created:
                for attempt in range(3):  # Try up to 3 times
                    if self.create_program(program_name, weeks):
                        program_created = True
                        # Update progress
                        self.save_progress(recovery_file, {
                            'client': client_name,
                            'program': program_name,
                            'completed_workouts': completed_workouts,
                            'program_created': True
                        })
                        break
                    else:
                        logging.warning(
                            f"Failed to create program (attempt {attempt+1}/3). Retrying...")
                        self.reload_page()
                        time.sleep(3)
                        # Navigate again if needed
                        self.navigate_to_training_program()
                else:  # If all attempts failed
                    logging.error(
                        f"Failed to create program: {program_name} after multiple attempts")
                    return False

            # Create each workout - we're already in the program view
            workouts = program_config.get('workouts', [])
            for i, workout in enumerate(workouts):
                workout_name = workout.get('name', 'New Workout')

                # Skip workouts that have already been completed
                if workout_name in completed_workouts:
                    logging.info(
                        f"Skipping workout '{workout_name}' (already completed)")
                    continue

                logging.info(
                    f"Working on workout {i+1}/{len(workouts)}: '{workout_name}'")
                exercises = workout.get('exercises', [])

                # Try creating the workout with retries
                for attempt in range(3):  # Try up to 3 times
                    if self.create_workout(program_name, workout_name, exercises):
                        # Success - add to completed workouts
                        completed_workouts.append(workout_name)
                        # Update progress
                        self.save_progress(recovery_file, {
                            'client': client_name,
                            'program': program_name,
                            'completed_workouts': completed_workouts,
                            'program_created': True
                        })
                        break
                    else:
                        logging.warning(
                            f"Failed to create workout '{workout_name}' (attempt {attempt+1}/3). Retrying...")
                        # Reload and try to get back to the program
                        self.handle_workout_failure(client_name, program_name)
                else:  # If all attempts failed
                    logging.error(
                        f"Failed to create workout: {workout_name} after multiple attempts")
                    # Continue with other workouts

            # Check if all workouts were completed
            if len(completed_workouts) == len(workouts):
                logging.info(
                    f"Successfully created all workouts for program: {program_name}")
                # Clear progress file on success
                if os.path.exists(recovery_file):
                    os.remove(recovery_file)
                return True
            else:
                logging.warning(
                    f"Some workouts were not created. Created {len(completed_workouts)}/{len(workouts)}")
                return False

        except Exception as e:
            logging.error(f"Error creating workout program: {e}")
            self.driver.save_screenshot("program_creation_error.png")
            return False

    def load_progress(self, file_path):
        """Load progress from a JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    progress = json.load(f)
                logging.info(f"Loaded progress from {file_path}")
                return progress
        except Exception as e:
            logging.warning(f"Error loading progress: {e}")
        return None

    def save_progress(self, file_path, progress_data):
        """Save progress to a JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(progress_data, f, indent=2)
            logging.info(f"Saved progress to {file_path}")
        except Exception as e:
            logging.warning(f"Error saving progress: {e}")

    def reload_page(self):
        """Reload the current page"""
        try:
            logging.info("Reloading page...")
            self.driver.refresh()
            time.sleep(5)  # Wait for page to load
            logging.info("Page reloaded")
            return True
        except Exception as e:
            logging.error(f"Error reloading page: {e}")
            return False

    def handle_workout_failure(self, client_name, program_name):
        """Handle workout failure by reloading and navigating back to the program"""
        try:
            logging.info("Handling workout failure...")

            # First try a simple reload
            self.reload_page()
            time.sleep(3)

            # Check if we're still in the program view by looking for the "New" button
            try:
                new_button = self.driver.find_element(
                    By.XPATH, "//button[.//span[text()='New']]")
                logging.info("Still in program view, no navigation needed")
                return True
            except:
                logging.info("Not in program view, need to navigate back")

            # Try to navigate back to client
            if self.navigate_to_client(client_name):
                # Navigate to Training Program tab
                if self.navigate_to_training_program():
                    # Try to click on the program
                    try:
                        program_link_locator = (
                            By.XPATH, f"//a[contains(@class, 'section-link') and .//p[contains(@class, 'color--black') and text()='{program_name}']]")
                        program_link = self.wait.until(
                            EC.element_to_be_clickable(program_link_locator))
                        program_link.click()
                        logging.info(
                            f"Navigated back to program: '{program_name}'")
                        time.sleep(2)
                        return True
                    except Exception as e:
                        logging.error(f"Error clicking program: {e}")

            logging.error("Failed to recover from workout failure")
            return False
        except Exception as e:
            logging.error(f"Error handling workout failure: {e}")
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


# Example usage
if __name__ == '__main__':
    # Login credentials
    USERNAME = "Shannonbirch@cocospersonaltraining.com"
    PASSWORD = "cyywp7nyk"
    CLIENT_NAME = "Rick Preston"

    # Define a sample workout program
    program_config = {
        'program_name': 'Cable & Machine Workout Program',
        'weeks': 6,
        'workouts': [
            {
                'name': 'Full Body Cable Workout',
                'exercises': [
                    {'name': 'Cable Chest Press', 'sets': '4', 'reps': '10-10-10-4',
                     'instructions': 'Set 1: 20kg, Set 2: 30kg, Set 3: 35kg, Set 4: 40kg'},
                    {'name': 'Cable Rear Delt Row', 'sets': '3',
                     'reps': '10-8-8', 'instructions': 'All sets with 8kg'},
                    {'name': 'Seated Leg Extension', 'sets': '4', 'reps': '15-15-12-12',
                     'instructions': 'Set 1: 30kg, Set 2: 40kg, Sets 3-4: 50kg'},
                    {'name': 'Hyperextension', 'sets': '3',
                     'reps': '10', 'instructions': 'Bodyweight only'},
                    {'name': 'Hyperextension Oblique Twists', 'sets': '3',
                     'reps': '10-11-11', 'instructions': 'Bodyweight only'}
                ]
            }
        ]
    }
    # Initialize the automation bot
    trainerize_bot = TrainerizeAutomation()

    try:
        # Login
        if trainerize_bot.login(USERNAME, PASSWORD):
            trainerize_bot.handle_notification_popup()

            # Create the workout program
            if trainerize_bot.create_workout_program(CLIENT_NAME, program_config):
                print(
                    f"Successfully created '{program_config['program_name']}' for {CLIENT_NAME}")
            else:
                print(f"Failed to create workout program")
        else:
            print("Login failed.")

        # Wait for user to review
        input("Press Enter to close the browser and exit...")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()
