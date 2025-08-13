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

# Import our exercise list and memory system
try:
    from trainerize_exercises import TRAINERIZE_EXERCISES, EXERCISE_CATEGORIES, validate_exercise, get_exercises_by_category
except ImportError:
    # Fallback if trainerize_exercises.py is not available
    TRAINERIZE_EXERCISES = []
    EXERCISE_CATEGORIES = {}
    def validate_exercise(exercise): return False
    def get_exercises_by_category(category): return []

try:
    from program_memory import ProgramMemory
except ImportError:
    # Fallback if program_memory.py is not available
    class ProgramMemory:
        def is_program_built(self, *args): return False
        def mark_program_built(self, *args): pass
        def list_built_programs(self): pass


class GlobalWorkoutBuilder:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome for Global Workout Builder...")

        # Chrome setup
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

    def navigate_to_master_programs(self):
        """Navigate to the Master Programs page"""
        try:
            logging.info("Navigating to Master Programs page...")
            master_programs_url = "https://cocosptstudio.trainerize.com/app/programs?accessLevel=mine&tagID=all"
            self.driver.get(master_programs_url)

            # Wait for the page to load
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='masterProgram-newButton']")))
            logging.info("Successfully navigated to Master Programs page")
            return True
        except Exception as e:
            logging.error(f"Error navigating to Master Programs: {e}")
            return False

    def create_new_master_program(self, program_name):
        """Create a new master program or navigate to existing one"""
        try:
            logging.info(f"Creating new master program: {program_name}")

            # Click the "New" dropdown button
            new_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-testid='masterProgram-newButton']")))
            new_button.click()
            time.sleep(1)

            # Click "Build new" from dropdown
            build_new_option = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li[data-testid='dropdownButton-menuItem-buildNew']")))
            build_new_option.click()
            time.sleep(2)

            # Fill in program name
            name_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[data-testid='createMasterProgramDialog-programName']")))
            name_input.clear()
            name_input.send_keys(program_name)
            time.sleep(1)

            # Click Save button
            save_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-testid='masterProgram-save']")))
            save_button.click()
            time.sleep(3)

            # Check if there's an error message about duplicate name
            try:
                error_message = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'There is already a program with the same name')]")
                if error_message:
                    logging.info(
                        f"Program '{program_name}' already exists. Closing dialog and navigating to existing program.")

                    # Close the dialog by clicking outside or finding close button
                    try:
                        # Try to find and click close button
                        close_selectors = [
                            "button[aria-label='Close']",
                            ".ant-modal-close",
                            "//button[contains(@class, 'close')]",
                            "//span[contains(@class, 'close')]"
                        ]

                        for selector in close_selectors:
                            try:
                                if selector.startswith("//"):
                                    close_btn = self.driver.find_element(
                                        By.XPATH, selector)
                                else:
                                    close_btn = self.driver.find_element(
                                        By.CSS_SELECTOR, selector)
                                close_btn.click()
                                logging.info(
                                    "Closed dialog using close button")
                                break
                            except:
                                continue
                        else:
                            # If no close button found, try pressing Escape
                            self.driver.find_element(
                                By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            logging.info("Closed dialog using Escape key")
                    except:
                        # If all else fails, click outside the modal
                        self.driver.execute_script(
                            "document.querySelector('.ant-modal-mask').click();")
                        logging.info("Closed dialog by clicking outside")

                    time.sleep(2)

                    # Now find and click on the existing program
                    return self.navigate_to_existing_program(program_name)

            except:
                # No error message found, program was created successfully
                pass

            logging.info(
                f"Successfully created master program: {program_name}")
            return True
        except Exception as e:
            logging.error(f"Error creating master program: {e}")
            return False

    def navigate_to_existing_program(self, program_name):
        """Navigate to an existing program in the sidebar"""
        try:
            logging.info(f"Looking for existing program: {program_name}")

            # Wait a moment for the page to load
            time.sleep(2)

            # First, let's debug what programs are available
            try:
                all_programs = self.driver.find_elements(
                    By.XPATH, "//a[contains(@class, 'accessLevel-section-link')]//p[contains(@class, 'tz-sp')]")
                logging.info(f"Found {len(all_programs)} programs in sidebar:")
                for i, prog in enumerate(all_programs):
                    title = prog.get_attribute('title') or prog.text
                    logging.info(f"  {i+1}. '{title}'")
            except Exception as e:
                logging.warning(f"Could not debug available programs: {e}")

            # Look for the program in the sidebar using various approaches
            program_selectors = [
                f"//a[contains(@class, 'accessLevel-section-link')]//p[@title='{program_name}']",
                f"//a[contains(@class, 'accessLevel-section-link')]//p[contains(text(), '{program_name}')]",
                f"//a[contains(@class, 'accessLevel-section-link')]//p[normalize-space(text())='{program_name}']",
                f"//p[@title='{program_name}']",
                f"//p[contains(text(), '{program_name}')]",
                f"//p[normalize-space(text())='{program_name}']",
                # Try with case-insensitive matching
                f"//a[contains(@class, 'accessLevel-section-link')]//p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{program_name.lower()}')]",
                # Try finding by href containing program name
                f"//a[contains(@class, 'accessLevel-section-link') and contains(@href, 'programs')]"
            ]

            for selector in program_selectors:
                try:
                    logging.info(f"Trying selector: {selector}")

                    if "contains(@href" in selector:
                        # Special handling for href-based selector
                        program_links = self.driver.find_elements(
                            By.XPATH, selector)
                        for link in program_links:
                            try:
                                link_text_elem = link.find_element(
                                    By.XPATH, ".//p[contains(@class, 'tz-sp')]")
                                link_text = link_text_elem.get_attribute(
                                    'title') or link_text_elem.text
                                logging.info(
                                    f"Checking program: '{link_text}' against '{program_name}'")
                                if program_name.lower() == link_text.lower().strip():
                                    logging.info(
                                        f"Found exact matching program by href: '{link_text}'")
                                    link.click()
                                    logging.info(
                                        f"Successfully clicked on existing program: {program_name}")
                                    time.sleep(3)
                                    return True
                            except Exception as e:
                                logging.debug(
                                    f"Error checking program link: {e}")
                                continue
                    else:
                        program_element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector)))

                        # Click on the program link (might need to click the parent <a> element)
                        try:
                            parent_link = program_element.find_element(
                                By.XPATH, "./ancestor::a[contains(@class, 'accessLevel-section-link')]")
                            parent_link.click()
                        except:
                            # If can't find parent, try clicking the element itself
                            program_element.click()

                        logging.info(
                            f"Successfully clicked on existing program: {program_name}")
                        time.sleep(3)
                        return True

                except Exception as e:
                    logging.debug(f"Selector {selector} failed: {e}")
                    continue

            logging.error(f"Could not find existing program: {program_name}")
            return False

        except Exception as e:
            logging.error(f"Error navigating to existing program: {e}")
            return False

    def fuzzy_match_exercise(self, target_exercise, threshold=60):
        """Find the best matching exercise from Trainerize exercise list"""
        if validate_exercise(target_exercise):
            return target_exercise

        # Try fuzzy matching
        target_lower = target_exercise.lower()
        best_match = None
        best_score = 0

        for exercise in TRAINERIZE_EXERCISES:
            exercise_lower = exercise.lower()

            # Exact match
            if target_lower == exercise_lower:
                return exercise

            # Contains match
            if target_lower in exercise_lower or exercise_lower in target_lower:
                return exercise

            # Word matching
            target_words = set(target_lower.split())
            exercise_words = set(exercise_lower.split())
            common_words = target_words.intersection(exercise_words)

            if len(target_words) > 0:
                score = len(common_words) / len(target_words) * 100
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = exercise

        if best_match:
            logging.info(
                f"Fuzzy matched '{target_exercise}' to '{best_match}' (score: {best_score}%)")
            return best_match

        logging.warning(f"No match found for exercise: {target_exercise}")
        return None

    def click_program(self, program_name):
        """For master programs, we don't need to click a program - we're already in it"""
        logging.info(
            f"Already in master program '{program_name}', no need to click")
        return True

    def add_exercise(self, exercise_name, sets="3", reps="12"):
        """Adds exercise with fuzzy matching support and robust UI handling."""
        try:
            # Click search box and clear previous text
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))
            search_box.click()
            for _ in range(20):
                search_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            search_box.send_keys(exercise_name)
            search_box.send_keys(Keys.ENTER)
            time.sleep(1)

            # Wait for the exercise library container
            container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".exerciseLibrary-container")))
            time.sleep(0.5)
            # Gather all exercise elements and their names
            exercise_elements = container.find_elements(
                By.CSS_SELECTOR, ".exerciseLibrary-exercise")
            exercise_names = []
            for elem in exercise_elements:
                try:
                    name_elem = elem.find_element(
                        By.CSS_SELECTOR, "div.flex-left p")
                    exercise_names.append((elem, name_elem.text.strip()))
                except Exception:
                    continue
            # Fuzzy match to find the best pick
            best_elem = None
            best_score = 0
            for elem, name in exercise_names:
                score = 0
                if exercise_name.lower() == name.lower():
                    score = 100
                elif exercise_name.lower() in name.lower() or name.lower() in exercise_name.lower():
                    score = 90
                else:
                    # Simple fuzzy: count matching words
                    words = set(exercise_name.lower().split())
                    name_words = set(name.lower().split())
                    matches = len(words & name_words)
                    score = matches / max(len(words), 1) * 100
                if score > best_score:
                    best_score = score
                    best_elem = elem
            if best_elem and best_score >= 60:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", best_elem)
                time.sleep(0.5)
                best_elem.click()
                logging.info(
                    f"Clicked on exercise: '{exercise_name}' (best match: '{name}' with score {best_score}%)")
                time.sleep(1)
            else:
                logging.warning(
                    f"Could not find a close match for exercise: '{exercise_name}' (best match: '{name if best_elem else None}' with score {best_score}%)")
                # Clear the search box even if exercise wasn't found
                search_box = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))
                for _ in range(20):
                    search_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
                return False

            # Continue with the rest of the add flow (sets, reps, etc.)
            # Try multiple selectors for Add to Workout button
            add_button_selectors = [
                "button[data-testid='exerciseDetail-addToWorkoutButton']",
                "button.ant-btn.btn--medium.btn--blue.fullWidth",
                "button.gtBtn-blue span:contains('Add to Workout')",
                "button.ant-btn.btn.btn--medium.btn--blue.fullWidth.m8t.gtBtn-blue",
                "button:contains('Add to Workout')"
            ]
            add_button_clicked = False
            for selector in add_button_selectors:
                try:
                    logging.info(
                        f"Trying to find Add to Workout button with selector: {selector}")
                    add_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    self.driver.execute_script(
                        "arguments[0].click();", add_button)
                    logging.info(
                        "Clicked Add to Workout button using JavaScript")
                    add_button_clicked = True
                    time.sleep(2)
                    break
                except TimeoutException:
                    logging.info(
                        f"Selector {selector} not found, trying next...")
                    continue
                except Exception as e:
                    logging.warning(f"Error with selector {selector}: {e}")
                    continue
            if not add_button_clicked:
                logging.error(
                    "Failed to click Add to Workout button with any selector")
                return False

            # Clear the search box after adding exercise
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))
            for _ in range(20):
                search_box.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)

            # Verify exercise was added by checking for sets/reps inputs
            try:
                sets_inputs = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[data-testid='workoutBuilder-exerciseSetInput']")))
                reps_inputs = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[data-testid='workoutBuilder-recordTypeInput']")))
                # Set sets and reps for the last added exercise (assume it's the last input in the list)
                if sets_inputs and reps_inputs:
                    sets_input = sets_inputs[-1]
                    reps_input = reps_inputs[-1]
                    # Clear and set sets
                    sets_input.click()
                    sets_input.send_keys(Keys.CONTROL + "a")
                    sets_input.send_keys(Keys.BACKSPACE)
                    sets_input.send_keys(str(sets))
                    time.sleep(0.2)
                    # Clear and set reps
                    reps_input.click()
                    reps_input.send_keys(Keys.CONTROL + "a")
                    reps_input.send_keys(Keys.BACKSPACE)
                    reps_input.send_keys(str(reps))
                    time.sleep(0.2)
                    logging.info(
                        f"Set sets to {sets} and reps to {reps} for '{exercise_name}'")
                    return True
            except TimeoutException:
                logging.error(
                    "Could not verify exercise was added (sets input not found)")
                return False
        except Exception as e:
            logging.error(f"Error adding exercise: {e}")
            # Attempt to clear search box in case of error
            try:
                search_box = self.driver.find_element(
                    By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")
                for _ in range(20):
                    search_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
            except:
                pass
            return False

    def create_workout(self, program_name, workout_name, exercises, already_in_program=False):
        """Creates a new workout with specified exercises. If already_in_program is True, skips clicking the program."""
        try:
            logging.info(f"Starting workout creation '{workout_name}'...")

            # Click on the program first, unless already in it
            if not already_in_program:
                if not self.click_program(program_name):
                    logging.error(
                        f"Failed to click program '{program_name}'. Cannot create workout.")
                    return False

            # Click New workout button with retry and scroll - try multiple selectors for Master Programs
            max_retries = 3
            new_button_selectors = [
                "button[title='Create new workout']",  # Original selector
                # Master program specific
                "button[data-testid='masterProgram-newWorkoutButton']",
                # Alternative
                "button[data-testid='masterProgram-addWorkoutButton']",
                "//button[contains(text(), 'NEW')]",  # Text-based
                "//button[contains(text(), 'Add')]",  # Alternative text
                "//button[contains(text(), 'Create')]",  # Alternative text
                ".ant-btn:contains('NEW')",  # CSS with text
                "button.ant-btn.btn--blue",  # Generic blue button
            ]

            new_button_clicked = False
            for attempt in range(max_retries):
                for selector in new_button_selectors:
                    try:
                        logging.info(
                            f"Attempt {attempt + 1}: Trying selector: {selector}")

                        if selector.startswith("//"):
                            new_button = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, selector)))
                        else:
                            new_button = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

                        # Scroll the button into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", new_button)
                        time.sleep(1)  # Wait for scroll to complete

                        # Try to click with JavaScript
                        try:
                            self.driver.execute_script(
                                "arguments[0].click();", new_button)
                            logging.info(
                                f"Clicked 'New' workout button with JavaScript using selector: {selector}")
                            new_button_clicked = True
                            time.sleep(2)
                            break
                        except Exception as js_error:
                            logging.warning(
                                f"JavaScript click failed: {js_error}")
                            # Try regular click
                            try:
                                new_button.click()
                                logging.info(
                                    f"Clicked 'New' workout button with regular click using selector: {selector}")
                                new_button_clicked = True
                                time.sleep(2)
                                break
                            except Exception as click_error:
                                logging.warning(
                                    f"Regular click failed: {click_error}")
                                continue

                    except Exception as e:
                        logging.debug(f"Selector {selector} failed: {e}")
                        continue

                if new_button_clicked:
                    break

                if attempt < max_retries - 1:
                    logging.info(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # Wait before retry

            if not new_button_clicked:
                logging.error(
                    f"Error clicking 'New' workout button after {max_retries} attempts with all selectors")
                return False

            # First click the Regular workout type
            try:
                workout_type_selectors = [
                    "label[data-testid='workoutBuilder-regularWorkout']",
                    "label#regular-label",
                    "//label[contains(text(), 'Regular')]"
                ]

                type_clicked = False
                for selector in workout_type_selectors:
                    try:
                        logging.info(
                            f"Trying to click Regular workout type with selector: {selector}")
                        if selector.startswith("//"):
                            type_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            type_button = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                        type_button.click()
                        logging.info(
                            "Successfully clicked Regular workout type")
                        type_clicked = True
                        time.sleep(1)
                        break
                    except Exception as e:
                        logging.warning(
                            f"Failed to click workout type with selector {selector}: {e}")
                        continue

                if not type_clicked:
                    logging.error("Failed to select Regular workout type")
                    return False

            except Exception as e:
                logging.error(f"Error selecting workout type: {e}")
                return False

            # Set workout name
            try:
                name_input_selectors = [
                    "input[placeholder='workout name, like Day 1 Abs']",
                    "input.ant-input[placeholder*='workout name']",
                    "//input[contains(@placeholder, 'workout name')]"
                ]

                name_input = None
                for selector in name_input_selectors:
                    try:
                        if selector.startswith("//"):
                            name_input = self.wait.until(
                                EC.presence_of_element_located((By.XPATH, selector)))
                        else:
                            name_input = self.wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        if name_input:
                            break
                    except:
                        continue

                if not name_input:
                    logging.error("Could not find workout name input field")
                    return False

                # Clear and set the name
                name_input.clear()
                name_input.send_keys(workout_name)
                # Tab out to trigger any validation
                name_input.send_keys(Keys.TAB)
                logging.info(f"Set workout name to '{workout_name}'.")
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error setting workout name: {e}")
                return False

            # Click START BUILDING button
            try:
                start_building_selectors = [
                    "button[data-testid='workoutBuilder-startBuildingButton']",
                    "button#btn_workout_buildNew_startBuilding",
                    "button.gtBtn.gtBtnLarge.gtBtn-blue",
                    "//button[contains(text(), 'START BUILDING')]"
                ]

                start_building_clicked = False
                for selector in start_building_selectors:
                    try:
                        logging.info(
                            f"Trying to click START BUILDING button with selector: {selector}")
                        if selector.startswith("//"):
                            start_building_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            start_building_button = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                        # Try JavaScript click first
                        try:
                            self.driver.execute_script(
                                "arguments[0].click();", start_building_button)
                            logging.info(
                                "Clicked START BUILDING button using JavaScript")
                            start_building_clicked = True
                            time.sleep(3)
                            break
                        except Exception as js_error:
                            logging.warning(
                                f"JavaScript click failed: {js_error}")
                            try:
                                # Try regular click as fallback
                                start_building_button.click()
                                logging.info(
                                    "Clicked START BUILDING button using regular click")
                                start_building_clicked = True
                                time.sleep(3)
                                break
                            except Exception as click_error:
                                logging.error(
                                    f"Regular click failed: {click_error}")
                                continue

                    except TimeoutException:
                        logging.info(
                            f"Selector {selector} not found, trying next...")
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                        continue

                if not start_building_clicked:
                    logging.error(
                        "Failed to click START BUILDING button with any selector")
                    return False

                # Verify we're in the exercise builder
                try:
                    self.wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))
                    logging.info("Successfully entered exercise builder mode")
                except TimeoutException:
                    logging.error(
                        "Could not verify we entered exercise builder mode")
                    return False

            except Exception as e:
                logging.error(f"Error clicking START BUILDING button: {e}")
                return False

            # Add exercises
            failed_exercises = []
            for exercise in exercises:
                exercise_name = exercise.get('name', '')
                sets = exercise.get('sets', '3')
                reps = exercise.get('reps', '12')

                logging.info(
                    f"Adding exercise: '{exercise_name}' with sets: '{sets}' and reps: '{reps}'...")

                try:
                    if not self.add_exercise(exercise_name, sets, reps):
                        logging.warning(
                            f"Failed to add exercise '{exercise_name}'. Continuing with next exercise...")
                        failed_exercises.append(exercise_name)
                        continue
                    logging.info(
                        f"Successfully added exercise '{exercise_name}'.")
                    time.sleep(1)  # Add small delay between exercises
                except Exception as e:
                    logging.error(
                        f"Error adding exercise '{exercise_name}': {e}")
                    failed_exercises.append(exercise_name)
                    continue

            # Save the workout
            try:
                save_button_selectors = [
                    # New primary selector
                    "button[data-testid='workoutBuilder-saveBtn']",
                    "button.ant-btn.btn.btn--small.btn--blue.dsV2",  # Class-based selector
                    "button.ant-btn.btn--blue",  # Fallback selector
                    "//button[contains(text(), 'Save')]"  # XPath fallback
                ]
                save_clicked = False
                for selector in save_button_selectors:
                    try:
                        logging.info(
                            f"Trying to find Save button with selector: {selector}")
                        if selector.startswith("//"):
                            save_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            save_button = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", save_button)
                        time.sleep(1)  # Wait for scroll
                        self.driver.execute_script(
                            "arguments[0].click();", save_button)
                        logging.info("Clicked Save button using JavaScript.")
                        save_clicked = True
                        time.sleep(3)  # Increased wait time after save
                        break
                    except TimeoutException:
                        logging.info(
                            f"Selector {selector} not found, trying next...")
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                        continue
                if not save_clicked:
                    logging.error(
                        "Failed to click Save button with any selector")
                    return False
                # Removed final verification step here
                # Proceed directly to next step
                if failed_exercises:
                    logging.warning(
                        f"Workout '{workout_name}' created with {len(failed_exercises)} failed exercises:")
                    for failed in failed_exercises:
                        logging.warning(f"- Failed to add: {failed}")
                else:
                    logging.info(
                        f"Workout '{workout_name}' created successfully with all exercises.")
                return True
            except Exception as e:
                logging.error(f"Error saving workout: {e}")
                return False

        except Exception as e:
            logging.error(f"Error creating workout '{workout_name}': {e}")
            return False

    def navigate_to_training_phase(self):
        """Navigate to the Week 1-4 training phase in Master Programs"""
        try:
            logging.info("Looking for Week 1-4 training phase...")

            # Wait for the page to load
            time.sleep(3)

            # Look for the Week 1-4 training phase using the structure you provided
            phase_selectors = [
                "//li[@data-testid='masterProgram-trainingPlanSection-week1-4']//a",
                "//li[contains(@class, 'section-trainingPlan')]//p[contains(text(), 'Week 1 - 4')]",
                "//a[contains(@href, 'trainingPhase')]//p[contains(text(), 'Week 1 - 4')]",
                "//p[contains(text(), 'Week 1 - 4')]"
            ]

            for selector in phase_selectors:
                try:
                    logging.info(
                        f"Trying to find Week 1-4 phase with selector: {selector}")
                    phase_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector)))

                    # If we found a <p> element, find its parent <a> element
                    if phase_element.tag_name == 'p':
                        parent_link = phase_element.find_element(
                            By.XPATH, "./ancestor::a")
                        parent_link.click()
                    else:
                        phase_element.click()

                    logging.info(
                        "Successfully clicked on Week 1-4 training phase")
                    time.sleep(3)
                    return True

                except Exception as e:
                    logging.debug(f"Selector {selector} failed: {e}")
                    continue

            logging.error("Could not find Week 1-4 training phase")
            return False

        except Exception as e:
            logging.error(f"Error navigating to training phase: {e}")
            return False

    def navigate_to_training_phase_week_5_8(self):
        """Navigate to the Week 5-8 training phase in Master Programs"""
        try:
            logging.info("Looking for Week 5-8 training phase...")

            # Wait for the page to load
            time.sleep(3)

            # Look for the Week 5-8 training phase
            phase_selectors = [
                "//li[@data-testid='masterProgram-trainingPlanSection-week5-8']//a",
                "//li[contains(@class, 'section-trainingPlan')]//p[contains(text(), 'Week 5 - 8')]",
                "//a[contains(@href, 'trainingPhase')]//p[contains(text(), 'Week 5 - 8')]",
                "//p[contains(text(), 'Week 5 - 8')]",
                "//p[contains(text(), 'Week 5-8')]",
                "//p[contains(text(), '5 - 8')]",
                "//p[contains(text(), '5-8')]"
            ]

            for selector in phase_selectors:
                try:
                    logging.info(
                        f"Trying to find Week 5-8 phase with selector: {selector}")
                    phase_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector)))

                    # If we found a <p> element, find its parent <a> element
                    if phase_element.tag_name == 'p':
                        parent_link = phase_element.find_element(
                            By.XPATH, "./ancestor::a")
                        parent_link.click()
                    else:
                        phase_element.click()

                    logging.info(
                        "Successfully clicked on Week 5-8 training phase")
                    time.sleep(3)
                    return True

                except Exception as e:
                    logging.debug(f"Selector {selector} failed: {e}")
                    continue

            logging.error("Could not find Week 5-8 training phase")
            return False

        except Exception as e:
            logging.error(f"Error navigating to Week 5-8 training phase: {e}")
            return False

    def check_if_workouts_exist(self):
        """Check if workouts are already built in the training phase"""
        try:
            logging.info("Checking if workouts are already built...")

            # Look for existing workouts in the phase
            workout_selectors = [
                "//div[contains(@class, 'workout')]",
                "//li[contains(@class, 'workout')]",
                "//p[contains(text(), 'Chest Day')]",
                "//p[contains(text(), 'Back Day')]",
                "//p[contains(text(), 'Shoulder Day')]",
                "//p[contains(text(), 'Leg Day')]",
                "//p[contains(text(), 'Core Day')]"
            ]

            for selector in workout_selectors:
                try:
                    existing_workouts = self.driver.find_elements(
                        By.XPATH, selector)
                    if existing_workouts:
                        logging.info(
                            f"Found {len(existing_workouts)} existing workouts")
                        return True
                except:
                    continue

            logging.info("No existing workouts found - ready to build")
            return False

        except Exception as e:
            logging.warning(f"Error checking for existing workouts: {e}")
            return False

    def build_cocos_studio_program(self):
        """Build the complete Coco's Studio program with 5 workouts"""

        program_name = "Coco's Studio"

        # Initialize memory system
        memory = ProgramMemory()

        # Define the 5 workouts for Week 5-8 (Monday through Friday) - STRENGTH PHASE
        workouts_week_5_8 = [
            {
                "name": "Chest Day - Strength",  # Monday
                "exercises": [
                    {"name": "Barbell Bench Chest Press",
                        "sets": "5", "reps": "6"},
                    {"name": "Incline Dumbbell Bench press",
                        "sets": "5", "reps": "6"},
                    {"name": "Cable Chest Press", "sets": "5", "reps": "6"},
                    {"name": "Dumbbell Chest Fly", "sets": "5", "reps": "6"},
                    {"name": "Cable Bench Triceps Push Down",
                        "sets": "5", "reps": "6"}
                ]
            },
            {
                "name": "Shoulder Day - Strength",  # Tuesday
                "exercises": [
                    {"name": "Standing Shoulder Press",
                        "sets": "5", "reps": "6"},
                    {"name": "Deltoid Lateral Raise",
                        "sets": "5", "reps": "6"},
                    {"name": "Face Pulls", "sets": "5", "reps": "6"},
                    {"name": "Rope Tricep Pushdown", "sets": "5", "reps": "6"},
                    {"name": "Alternating Hammer Curls",
                        "sets": "5", "reps": "6"}
                ]
            },
            {
                "name": "Leg Day - Strength",  # Wednesday
                "exercises": [
                    {"name": "Barbell Back Squat Pause",
                        "sets": "5", "reps": "6"},
                    {"name": "Dumbbell Romanian Deadlifts",
                        "sets": "5", "reps": "6"},
                    {"name": "Bulgarian Lunge", "sets": "5", "reps": "6"},
                    {"name": "Leg Extensions", "sets": "5", "reps": "6"},
                    {"name": "Standing Calf Raise", "sets": "5", "reps": "6"}
                ]
            },
            {
                "name": "Core Day - Strength",  # Thursday
                "exercises": [
                    {"name": "Plank", "sets": "5", "reps": "60 sec"},
                    {"name": "Cable Crunch", "sets": "5", "reps": "6"},
                    {"name": "Hanging knee tucks", "sets": "5", "reps": "6"},
                    {"name": "Cable Skull Crusher", "sets": "5", "reps": "6"},
                    {"name": "Concentrated Bicep Curls",
                        "sets": "5", "reps": "6"}
                ]
            },
            {
                "name": "Back Day - Strength",  # Friday
                "exercises": [
                    {"name": "Wide Grip Chin Up/ Assisted Chin Up",
                        "sets": "5", "reps": "6"},
                    {"name": "Lat Pull Down Wide Grip",
                        "sets": "5", "reps": "6"},
                    {"name": "Barbell Bent Over Row Pause",
                        "sets": "5", "reps": "6"},
                    {"name": "Bench Dumbbell Rows", "sets": "5", "reps": "6"},
                    {"name": "Cable Hammer Curls",
                        "sets": "5", "reps": "6"}
                ]
            }
        ]

        # Use the Week 5-8 strength program
        workouts = workouts_week_5_8
        training_phase = "Week 5-8"

        # Check if this program has already been built
        program_key = f"{program_name} - {training_phase}"
        if memory.is_program_built(program_key, workouts):
            logging.info(f"🔄 Program '{program_key}' has already been built!")
            print(f"🔄 Program '{program_key}' has already been built!")

            # Show program info
            program_info = memory.get_program_info(program_key)
            if program_info:
                built_date = program_info['built_date'][:19].replace('T', ' ')
                print(f"   📅 Built: {built_date}")
                print(
                    f"   💪 Workouts: {', '.join(program_info['workout_names'])}")
                print(
                    f"   🎯 Total Exercises: {program_info['total_exercises']}")

            print(
                f"\n💡 To rebuild this program, use: force_rebuild_program('{program_key}')")
            return True

        # First navigate to the Week 5-8 training phase
        if not self.navigate_to_training_phase_week_5_8():
            logging.error("Failed to navigate to Week 5-8 training phase")
            return False

        # Check if workouts are already built in Trainerize
        if self.check_if_workouts_exist():
            logging.info("Workouts already exist in this training phase")
            # Mark as built in memory even if we didn't build it this time
            memory.mark_program_built(program_key, workouts, training_phase)
            return True

        # Create each workout
        for workout in workouts:
            if not self.create_workout("Coco's Studio", workout["name"], workout["exercises"], already_in_program=True):
                logging.error(f"Failed to create workout: {workout['name']}")
                return False
            time.sleep(2)  # Brief pause between workouts

        # Mark program as built in memory
        memory.mark_program_built(program_key, workouts, training_phase)

        logging.info(
            "Successfully created all 5 workouts for Coco's Studio program!")
        return True

    def cleanup(self):
        """Clean up resources"""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'):
                self.driver.quit()
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            logging.info("Cleanup completed")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


def main():
    """Main function to run the global workout builder"""
    # Coach credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    program_name = "Coco's Studio"

    builder = None
    try:
        builder = GlobalWorkoutBuilder()

        # Login
        if not builder.login(username, password):
            logging.error("Login failed")
            return

        # Handle notification popup after login
        builder.handle_notification_popup()

        # Navigate to Master Programs
        if not builder.navigate_to_master_programs():
            logging.error("Failed to navigate to Master Programs")
            return

        # Create new master program
        if not builder.create_new_master_program(program_name):
            logging.error("Failed to create master program")
            return

        # Build the complete program
        if not builder.build_cocos_studio_program():
            logging.error("Failed to build complete program")
            return

        logging.info(
            "Global workout program 'Coco's Studio' created successfully!")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if builder:
            builder.cleanup()


if __name__ == "__main__":
    main()
