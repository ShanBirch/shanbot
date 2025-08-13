import sys
import json
import logging
import time
import os
import shutil  # For cleanup
import tempfile  # For cleanup

# Selenium and related imports from pe.py
from selenium import webdriver
# Added ActionChains, might be used by copied class
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Already Service from selenium.webdriver.chrome.service
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
# Alias to avoid conflict if any
from selenium.webdriver.chrome.service import Service as ChromeService


# Configure logging
logging.basicConfig(
    level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# TrainerizeAutomation class from pe.py
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class TrainerizeAutomation:
    def __init__(self):
        # Logging is configured globally in this script, so no need to reconfigure here
        # unless the class specifically needs its own logger instance/config.
        # For now, assume global logging is sufficient.
        logging.info("Initializing Chrome for TrainerizeAutomation...")

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
        # Ensure this path is correct or make it configurable
        chrome_options.binary_location = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"

        try:
            # Force the latest version of ChromeDriver
            # Using ChromeService from selenium.webdriver.chrome.service as aliased
            # No need to call ChromeDriverManager().install() if webdriver_manager is handling it
            service = ChromeService()
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info(
                "Chrome initialized successfully for TrainerizeAutomation!")
        except Exception as e:
            logging.error(
                f"Failed to initialize Chrome in TrainerizeAutomation: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

        # Exercise List (can be kept if methods rely on it, or removed if not used by this script's focus)
        # For now, keeping it as it's part of the class structure from pe.py
        self.exercise_list = [
            "2 Handed Dumbbell Bent Over Rows", "2 Handed Dumbbell Rear Delt Row", "2 Handed Straight Arm Lat Pull Down", "3 Point Lat Pull Down", "AB roller Crunch", "Ab Wheel", "Alternating Hammer Curls", "Alternating Lat Pull Down", "Arnold Press Eccentric", "Assault Bike", "B.B Back Squat", "B.B Bent Over Row", "Back Squat", "bag elbows", "bag kick", "Band Press", "Band pull apart", "Band Row Pause", "Band Seated Row", "Banded Clam", "Banded Hip Thruster", "Banded Rdls", "Banded Squat", "Banded Yes No", "barbell back squat eccentric", "Barbell Back Squat Pause", "Barbell Bench", "Barbell Bench Chest Press", "Barbell Bent Over Row Pause", "Barbell Box Squat", "Barbell Hip Thruster", "Barbell Squat", "Barbell Squats Concentric", "bench deltoid raise", "Bench Dumbbell Rows", "Bench Dumbbell Rows Eccentric", "Bench Dumbbell Rows Hold", "Bench Easy Curl Bar Bicep Curls", "Bench Easy Curl Bar Eccentrics", "Bench Lateral Raises", "Bench Rows", "Bent Over Single Arm Rear Delt Fly", "Bicep 21's", "Bicep Curl Hold", "Bicep Curls D.B", "Bicycle Kicks", "Bicycle Rocks", "Body Weight Squats", "boxing bag hook", "Boxing Bag Jab", "Bulgarian Lunge", "Bulgarian Lunge Concentric", "Bulgarian Lunge Eccentric", "Bulgarian Lunge Eccentrics", "Bulgarian Lunge Hold", "Burpees", "Cable Bench Triceps Push Down", "Cable Bench Triceps Push Down Concentric", "Cable Bench Triceps Push, halfway hold", "Cable Bent Elbow Rows", "Cable Chest fly", "Cable Chest Fly Eccentric", "Cable chest flys leaning", "Cable Chest Press", "Cable Chest Press Eccentric", "Cable Chest Press Pulse", "Cable Crunch", "Cable Crunch Eccentric", "Cable Crunch Oblique Twist", "Cable front squat", "Cable front squat concentric", "Cable Hammer Curls", "Cable Hammer Curls Eccentric", "Cable Lateral Raises", "Cable push downs", "Cable Skull Crusher", "Cable Skull Crusher Hold", "Cable Standing Lateral Raise", "Cable Y Rows", "Close Grip Barbell Bench Eccentrics", "Close Grip Barbell Bench Pause", "close grip barbell bench press", "Close Grip Bench Pushup", "Close Grip Cable Row", "Close Grip Chin up Hold", "Close Grip Chin Ups", "Close Grip D.B Bench Press", "Close Grip High Seated Rows", "Close Grip Lat Pulldown", "Close Grip Push Ups", "Close Grip Pushups", "Close Grip Seated Row", "close stance leg press", "Commandoes", "Concentrated Bicep Curls", "Concentric Skull Crushers", "Concentric TRX Rows", "Core figure 8", "Crab Kicks", "Crosses handed cable trap rows", "D.B bent over row", "DB Bicep Curl Concentric", "DB Bicep Curl Eccentric", "DB Upright Chest Fly", "Deadlift", "Decline Bench Bottom Pulse", "decline bench eccentric", "Decline Bench Press", "Decline D.B Pulse", "Decline Dumbbell Bench Press", "Decline Dumbbell Chest Fly", "Decline Dumbbell Eccentric Load", "decline under hand chest flys eccentrics", "decline underhand chest flys", "Deltoid Around the Worlds", "Deltoid Lateral Raise", "Deltoid Lateral Raise Eccentric", "Deltoid Lateral Raises Concentric", "Diagonal Jump ins", "Down Bag Elbows", "Dumbbell  Static Lunges", "Dumbbell Arnold Press", "Dumbbell Bicep Alternating Curls Eccentric", "Dumbbell Bicep Curls Alternating", "Dumbbell Bulgarian Lunges", "Dumbbell Chest Fly", "Dumbbell Chest Press", "Dumbbell Inward Triceps extension", "Dumbbell Overhead Push", "Dumbbell Rdl Eccentric Load", "Dumbbell Rdls", "Dumbbell RDLS Eccentric", "Dumbbell Rld", "Dumbbell Romanian Deadlifts", "Dumbbell Seated Press", "Dumbbell Shoulder Press", "Dumbbell Skull Crusher Eccentric", "Dumbbell Trap Shrugs Pause", "Dumbbell Tricep Press", "Dumbbell Triceps kick backs", "Dumbell  Trap Shrugs", "Dumbell Decline Press Concentric", "Easy Curl Bar Bicep Curls", "Easy Curl Bar Bicep Eccentrics", "Easy Curl Bar Bicep Holds", "Eccentric Bulgarian Lunge", "Eccentric Goblet Squat", "Eccentric Static Lunge", "Eccentric Trx Rows", "Eccentrically Load Seated Bicep Curls", "Exercise Ball Bench Press", "Exercise Ball Bent Over Row", "Exercise Ball Bent Over Rows", "Exercise Ball Bicep Curls", "Exercise Ball Chest Flys", "Exercise Ball Close Grip DB Bench", "Exercise Ball DB Rear Delt Flys", "Exercise Ball DB Y Raises", "Exercise ball Hamstring Curl Eccentric", "Exercise Ball Hamstring Raise", "Exercise Ball Incline Press", "Exercise Ball Lap Bicep Curls", "Exercise Ball Over Head Rows", "Exercise Ball Plank", "Exercise Ball Pushups", "Exercise Ball Triceps Kick Back", "Exercise Ball Triceps Press", "Exercise Ball Y Row", "Exercise Band Rear Delt Flys", "Face pull Pause", "Face Pulls", "Floor chest fly", "floor over head rows", "Floor Press", "Floor Skull Crushers", "GHD", "Goblet Curl", "Goblet Squat", "Goblet Squat Concentric", "Goblet Squat Pause", "Hack Squat", "Halfway Bicep Curl Pause", "Hanging Knee Tuck Holds", "Hanging knee tucks", "hanging knee tucks eccentric", "hanging oblique knee holds", "hanging oblique knee tucks", "Hollow Body Hang", "Hollow Body Rock", "Hollow Body Rocks", "Hollow-Body Hold", "Hyper Extension Pause", "Hyperextension", "HyperExtension Eccentric", "Hyperextension Oblique Twists", "Incline Barbell Bench Press", "Incline Dumbbell Bench press", "Incline Dumbbell Chest Fly", "Incline Skull Crusher Eccentric", "Incline Skull Crushers", "Incline Smith Bench Press", "Incline Smith Machine Pushups", "Infinity Leg Raises", "jab hook", "Kettle Bell Push Up", "Kettle Bell Swings", "Knee Pushup", "knee to heel lunge", "Kneeling Single Arm Press", "Kneeling Single Arm rows", "kneeling woodchops", "Lat Pull Down Eccentric Load", "Lat pull down Pause", "Lat Pull Down Wide Grip", "Lateral Raise Concentric", "Lateral Raise Pause", "Laying Lateral Raise", "Laying Leg Raises", "Laying Skull Crushers", "Leg Extensions", "Low to High Cable Chest Fly", "Lunge Jumps", "Lying Leg Curl", "machine lying leg curl pause", "Machine Seated Leg Curl Eccentric", "Machine Seated Leg Extension Pause", "Midfoot Plank Hold", "Military Press", "Oblique Knee Tucks", "Oblique Lean", "Paused Bench Rows", "Pistol Box Squats", "Plank", "plank row pause", "Plank Rows", "Plate Hold", "Posterior Seated Lateral Raise", "Push Up Pause", "Pushup", "Pushup Pause", "Reverse Dumbbell Lunge", "Roller Crunch", "Roller Knee Tuck", "Roller Pike", "Rope Push Down Concentric", "Rope Tricep Pushdown", "Rower", "Runner Man", "Runners Lunge", "s.a standing row", "Scissor Leg Raise", "Seated Bicep Curl", "Seated Bicep Curl Eccentric", "Seated Bicep Curl Tempo", "Seated Bicep Curls", "Seated Calf Raises", "Seated Calf Raises Eccentric", "Seated Db Press", "Seated Lat Pull Down", "Seated Leg Extension", "Seated Leg Extension Eccentric", "seated leg extension hold", "Seated Leg Extension Pyramid Set", "seated row", "Seated row concentric load", "Seated row pause", "Seated Row Pyramid Set", "Seated Row Wide Grip", "seated woodchop", "Seated woodchop eccentric", "Shoulder taps", "Shuriken Lunge", "Side Hyper Wtd", "Single Arm Bicep Bench Curl Eccentric", "Single Arm Cable chest press", "Single Arm Kneeling Cable Press", "Single Arm Kneeling Rows", "Single Arm Lat Pull Down", "Single Arm Lat Pull Down Eccentric", "SIngle Arm Lat Pull Down Halfway Pause", "Single Arm Press", "Single arm Press eccentric", "Single Arm Push through", "Single Arm Rear Delt Fly", "Single Arm Standing Dumbbell Tricep Skull Crusher", "Single Arm Straight Arm Lat Pull Down", "Single Arm Tricep Kick Backs", "Single Leg Barbell Rdl", "Single Leg Hip Thruster Pause", "Single Leg Hip Thrusters", "Single Leg Quad Extension", "Single Leg RDL", "Single leg Standing calf raises", "Skiiers", "Slam Balls", "Smith Bench Press", "Smith Bulgarian Lunges Eccentric", "Smith Machine Bulgarian Lunge Hold", "Smith Machine Bulgarian Lunges", "Smith Machine Concentric", "Smith Machine Front Squat Pause", "Smith Machine Good Mornings", "Smith Machine Squat", "Smith Machine Squat Eccentrics", "smith machine squat hold", "Smith Machine static lunges", "Squat Jumps", "Squat to Step Down", "Squeeze Grip D.B Bench Press", "Standing Calf Raise", "Standing Dumbbell Triceps Skull Crusher", "Standing Shoulder Press", "Standing Shoulder Press Eccentric", "Standing Shoulder Press Eccentric Load", "Standing Shoulder Press pyramid Set", "Standing Single Arm Skull Crusher", "standing two hand rows", "Standing Underhand Cable Chest Fly", "Static Lunge", "Static Woodchop", "Step Ups", "Suspended Trx Body rows", "Suspended Trx Rows", "Suspended Trx rows Eccentric", "Suspended Trx Rows Static Hold", "The Ultimate Warm Up", "Through Legs", "Tricep Dumbbell Press", "Tricep Rope Pushdown Eccentric Load", "Tricep Skull Crushers Eccentric Load", "Trx Body Face Pulls", "TRX Face Pulls", "Trx rows", "Under hand rows", "Under Handed Barbell Row", "V Hold", "V sit", "v snap", "V-sit", "Walk the Box", "Walking Lunges", "Weighted Hyper Extension Pause", "Weighted Hyperextension", "Wide Grip Chin Up Eccentric", "Wide Grip Chin Up/ Assisted Chin Up", "Woodchop", "Woodchop Eccentric Load", "Woodchops", "Wtd Chin Ups", "Y Cable Lateral Raises"
        ]

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

    def generate_name_variations(self, client_name):
        """Generate variations of a client name with different spacing.

        Args:
            client_name: Original client name

        Returns:
            List of name variations
        """
        variations = [
            client_name,  # Original name
            client_name.replace("  ", " "),  # Remove double spaces
            client_name.replace(" ", "  "),  # Add double spaces between words
            " ".join(client_name.split()),  # Normalize spaces
            "  ".join(client_name.split()),  # Double spaces between words
            client_name.strip()  # Remove leading/trailing spaces
        ]
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variations))

    def navigate_to_client(self, client_name):
        """Navigate to a specific client's page with enhanced name variation handling."""
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")

            # Click Clients link
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
                # If client link is not found initially, try refreshing and searching again
                logging.info(
                    "Refreshing page and retrying client navigation...")
                self.driver.refresh()
                time.sleep(3)
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            time.sleep(2)

            # Clear any existing search first
            logging.info("Clearing existing search...")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            # Use JavaScript to clear if normal clear fails
            try:
                search_input.clear()
            except:  # Broad except for any clear issue
                self.driver.execute_script(
                    "arguments[0].value='';", search_input)
            time.sleep(1)

            # Get name variations
            name_variations = self.generate_name_variations(client_name)
            client_found = False

            # Try each name variation
            for variation in name_variations:
                logging.info(f"Trying name variation: '{variation}'")

                # Clear and enter search term
                try:
                    search_input.clear()
                except:  # Broad except for any clear issue
                    self.driver.execute_script(
                        "arguments[0].value='';", search_input)
                search_input.send_keys(variation)
                time.sleep(2)  # Increased wait after sending keys

                # Try multiple selectors for finding the client link
                selectors = [
                    # Exact match with normalized spaces
                    f"//a[normalize-space(.)='{variation}']",
                    # Contains the name variation
                    f"//a[contains(., '{variation}')]",
                    # Title attribute contains
                    f"//a[@title[contains(., '{variation}')]]",
                    # Generic client list entry
                    f"//div[contains(@class, 'client-list')]//a[contains(., '{variation}')]",
                    # Try with first name only as fallback
                    f"//a[contains(., '{variation.split()[0] if variation.split() else ''}')]"
                ]

                for selector in selectors:
                    try:
                        logging.info(f"Trying selector: {selector}")
                        client_link = WebDriverWait(self.driver, 7).until(  # Increased wait for client link
                            EC.element_to_be_clickable((By.XPATH, selector)))

                        link_text = client_link.text.strip()
                        logging.info(
                            f"Found potential client link with text: '{link_text}'")
                        # More robust check if the found link matches the intended client
                        normalized_link_text = " ".join(
                            link_text.lower().split())
                        normalized_variation = " ".join(
                            variation.lower().split())
                        if normalized_variation in normalized_link_text or normalized_link_text in normalized_variation:
                            self.driver.execute_script(
                                "arguments[0].click();", client_link)  # JS click as primary
                            logging.info(
                                f"Successfully clicked on client link with text: {link_text}")
                            client_found = True
                            break
                        else:
                            logging.warning(
                                f"Potential match '{link_text}' does not sufficiently match '{variation}'. Skipping.")
                    except TimeoutException:
                        logging.debug(f"Selector {selector} timed out.")
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                        continue

                if client_found:
                    break

            if not client_found:
                # Attempt a broader search if specific variations fail
                logging.info(
                    f"Specific name variations failed. Trying a broader search for '{client_name.split()[0] if client_name.split() else client_name}'")
                search_input.clear()
                search_input.send_keys(client_name.split()[0] if client_name.split(
                ) else client_name)  # Search by first name
                time.sleep(2)
                try:
                    # Look for any client link and take the first one if it's a reasonable match
                    client_links = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, "//div[contains(@class, 'client-list')]//a[@title]"))
                    )
                    if client_links:
                        for link in client_links:
                            link_text = link.get_attribute("title").strip()
                            if client_name.lower().split()[0] in link_text.lower():
                                logging.info(
                                    f"Broad search found: '{link_text}'. Clicking.")
                                self.driver.execute_script(
                                    "arguments[0].click();", link)
                                client_found = True
                                break
                except TimeoutException:
                    logging.error(
                        f"Broad search for '{client_name.split()[0]}' also failed to find any clients.")

            if not client_found:
                logging.error(
                    f"Could not find client with any variation of name: {client_name}. Variations tried: {name_variations}")
                # self.driver.save_screenshot("client_not_found.png") # Optional: save screenshot
                return False

            # Click the Open button
            logging.info(
                "Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(
                EC.element_to_be_clickable(open_button_locator))
            # Using JS click for reliability
            self.driver.execute_script("arguments[0].click();", open_button)
            time.sleep(3)  # Increased wait after open button

            # Switch to the new tab
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            WebDriverWait(self.driver, 10).until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    logging.info(f"Switched to window: {self.driver.title}")
                    break
            # If loop completes without break (should not happen if number_of_windows_to_be(2) passed)
            else:
                logging.error(
                    "Failed to switch to new window after opening client profile.")
                return False

            logging.info(
                f"Successfully navigated to client and switched to their profile tab: {self.driver.current_url}")
            return True

        except Exception as e:
            logging.error(
                f"Error navigating to client or switching tabs: {e}", exc_info=True)
            # self.driver.save_screenshot("navigate_to_client_error.png") # Optional
            return False

    def navigate_to_training_program(self):
        """Navigates to the 'Training Program' tab (Simplified to match pe.py's direct approach)."""
        try:
            logging.info(
                "Navigating to the 'Training Program' tab (simplified approach)...")

            training_program_link_locator = (
                By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']")

            logging.info(
                "Locating and clicking Training Program link directly.")
            training_program_link = self.wait.until(
                EC.element_to_be_clickable(training_program_link_locator))
            training_program_link.click()  # Direct click, as in pe.py

            time.sleep(3)  # Generous fixed wait, slightly more than pe.py

            # No explicit verification via URL or element presence here, similar to pe.py.
            # We assume navigation is successful if no immediate error on click.
            # Subsequent methods will fail if navigation was truly unsuccessful.
            logging.info(
                "Assumed successful navigation to the 'Training Program' tab after click and sleep.")
            return True

        # Matching pe.py's exception handling for this part
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"Error navigating to the 'Training Program' tab (Timeout or NoSuchElement): {e}")
            # self.driver.save_screenshot("navigate_training_program_simplified_fail.png")
            return False
        except Exception as e:
            logging.error(
                f"An unexpected error occurred while navigating to Training Program (simplified): {e}", exc_info=True)
            # self.driver.save_screenshot("navigate_training_program_simplified_error.png")
            return False

    def navigate_to_meal_plan(self):
        """Navigates to the Meal Plan tab from the client profile, with retries and sidebar wait."""
        try:
            logging.info("Navigating to the Meal Plan tab...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.ID, "leftNavMenu"))  # Wait for sidebar
            )
            meal_plan_link_locator = (
                By.XPATH, "//a[@id='nav_meal_plan' and @data-testid='leftNavMenu-item-mealPlan' and @title='Meal Plan']")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    meal_plan_tab_element = self.wait.until(
                        EC.element_to_be_clickable(meal_plan_link_locator))
                    if 'active' in meal_plan_tab_element.get_attribute('class'):
                        logging.info("Already on the Meal Plan tab.")
                        return True

                    self.driver.execute_script(
                        "arguments[0].click();", meal_plan_tab_element)  # JS click
                    time.sleep(2)  # Wait for the page to load

                    # Verify navigation by checking if the tab is now active or URL changed
                    # Re-fetch element to check its class after click
                    meal_plan_tab_element_after_click = self.driver.find_element(
                        *meal_plan_link_locator)
                    if 'active' in meal_plan_tab_element_after_click.get_attribute('class') or "mealplan/clientdashboard" in self.driver.current_url:
                        logging.info(
                            "Successfully navigated to the Meal Plan tab after click.")
                        return True
                    else:
                        logging.warning(
                            f"Meal plan tab not active after click attempt {attempt + 1}. Retrying if possible.")
                        if attempt == max_retries - 1:
                            break  # Break if last attempt

                except Exception as e:
                    logging.warning(
                        f"Attempt {attempt+1} to click Meal Plan tab failed: {e}")
                    if attempt == max_retries - 1:
                        logging.error(
                            "Max retries reached for Meal Plan tab navigation.")
                        break  # Break if last attempt
                    time.sleep(2)  # Wait before next retry

            # If loop finishes without returning True
            logging.error(
                "Failed to navigate to Meal Plan tab after all retries.")
            # self.driver.save_screenshot("navigate_meal_plan_error.png") # Optional
            return False
        except Exception as e:
            logging.error(
                f"An unexpected error occurred while navigating to Meal Plan: {e}", exc_info=True)
            # self.driver.save_screenshot("navigate_meal_plan_unexpected_error.png") # Optional
            return False

    def fuzzy_match(self, target_text, actual_text, threshold=60):  # Lowered threshold
        """General fuzzy matching function that handles various text matching scenarios.

        Args:
            target_text (str): The text we're looking for
            actual_text (str): The text we're comparing against
            threshold (int): Minimum similarity score (0-100) to consider a match

        Returns:
            bool: Whether the texts match according to fuzzy logic
        """
        if not target_text or not actual_text:
            return False

        # Convert both to lowercase for comparison
        target = target_text.lower()
        actual = actual_text.lower()

        # Direct matches
        if target == actual:
            return True
        if target in actual or actual in target:
            return True

        # Remove special characters and extra spaces
        target_clean = ''.join(
            c for c in target if c.isalnum() or c.isspace()).strip()
        actual_clean = ''.join(
            c for c in actual if c.isalnum() or c.isspace()).strip()

        # Split into words and remove common words that might interfere with matching
        common_words = {'the', 'and', 'or', 'with',
                        'without', 'in', 'on', 'at', 'to', 'for'}
        target_words = set(word for word in target_clean.split()
                           if word.lower() not in common_words)
        actual_words = set(word for word in actual_clean.split()
                           if word.lower() not in common_words)

        # Check if key words match (more lenient)
        key_words_target = set(word for word in target_words if len(
            word) > 3)  # Only consider significant words
        key_words_actual = set(word for word in actual_words if len(word) > 3)

        if key_words_target and key_words_actual:
            matching_key_words = len(
                key_words_target.intersection(key_words_actual))
            total_key_words = len(key_words_target)
            if total_key_words > 0:
                key_word_match_ratio = (
                    matching_key_words / total_key_words) * 100
                if key_word_match_ratio >= threshold:
                    return True

        # Check for partial word matches
        for target_word in target_words:
            if any(target_word[:4] in actual_word or actual_word[:4] in target_word
                   for actual_word in actual_words if len(actual_word) >= 4):
                return True

        # Calculate word match ratio
        matching_words = len(target_words.intersection(actual_words))
        total_words = len(target_words)
        if total_words > 0:
            word_match_ratio = (matching_words / total_words) * 100
            if word_match_ratio >= threshold:
                return True

        # Calculate character similarity for short terms
        if len(target_clean) < 12 or len(actual_clean) < 12:
            char_matches = sum(1 for a, b in zip(
                target_clean, actual_clean) if a == b)
            max_length = max(len(target_clean), len(actual_clean))
            if max_length > 0:
                char_ratio = (char_matches / max_length) * 100
                if char_ratio >= threshold:
                    return True
        # If all checks fail
        return False  # Added this line, was missing before

    def find_closest_match(self, target_text, text_list, threshold=80):
        """Find the closest matching text from a list of options.

        Args:
            target_text (str): The text to find a match for
            text_list (list): List of possible matches
            threshold (int): Minimum similarity score to consider a match

        Returns:
            tuple: (best_match, score) or (None, 0) if no match found
        """
        best_match = None
        best_score = 0

        for text in text_list:
            # Try exact match first
            if target_text.lower() == text.lower():
                return text, 100

            # Check if target is completely contained
            if target_text.lower() in text.lower():
                # Score based on how much of the text is the target
                score = (len(target_text) / len(text)) * \
                    100 if len(text) > 0 else 0
                if score > best_score:
                    best_score = score
                    best_match = text
                if score == 100:
                    return text, 100  # if it is a perfect containment match
                # Continue to check other matches which might be better fuzzy matches

            # Use fuzzy matching
            if self.fuzzy_match(target_text, text, threshold):
                # Calculate a rough score based on length difference and common characters
                target_clean = ''.join(
                    c for c in target_text.lower() if c.isalnum())
                text_clean = ''.join(c for c in text.lower() if c.isalnum())
                common_chars = sum(1 for a, b in zip(
                    target_clean, text_clean) if a == b)
                max_len = max(len(target_clean), len(text_clean))
                score = (common_chars / max_len) * 100 if max_len > 0 else 0

                if score > best_score:
                    best_score = score
                    best_match = text

        # Ensure a match is above threshold before returning it
        if best_match and best_score >= threshold:
            return best_match, best_score
        else:
            return None, 0

    def click_program(self, program_week_name):
        """Clicks on a program link with improved fuzzy matching and extra logging."""
        try:
            logging.info(
                f"Attempting to click on program/training phase: '{program_week_name}'...")

            # Wait for program list to be populated
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'trainingPlanGrid-phaseName') or contains(@class, 'section-link')]//p"))
            )

            program_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'trainingPlanGrid-phaseName') or contains(@class, 'section-link')]//p[normalize-space(.)]")
            program_names = [
                elem.text.strip() for elem in program_elements if elem.text.strip()]
            logging.info(
                f"[PROGRAMS] Found program/phase names on page: {program_names}")

            if not program_names:
                logging.warning(
                    "No program names found on the page. Cannot click.")
                return False

            matched_program, score = self.find_closest_match(
                program_week_name, program_names, threshold=70)  # Slightly lower threshold for clicking

            if matched_program:
                logging.info(
                    f"Found matching program/phase: '{matched_program}' (similarity: {score}%). Attempting to click.")

                # Try to click the specific element that matched
                clicked = False
                for elem in program_elements:
                    if elem.text.strip() == matched_program:
                        try:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", elem)
                            time.sleep(0.5)
                            elem.click()  # Try direct click on the <p> or its parent if it's a link
                            logging.info(
                                f"Successfully clicked on program/phase '{matched_program}' (direct element). Element tag: {elem.tag_name}")
                            clicked = True
                            break
                        except ElementClickInterceptedException:
                            logging.warning(
                                f"Direct click on '{matched_program}' was intercepted. Trying parent link or JS click.")
                            try:  # Try clicking parent if it's an <a> tag
                                parent_link = elem.find_element(
                                    By.XPATH, "./ancestor-or-self::a")
                                self.driver.execute_script(
                                    "arguments[0].click();", parent_link)
                                logging.info(
                                    f"Clicked parent link of '{matched_program}' using JS.")
                                clicked = True
                                break
                            except:
                                pass  # Continue to JS click on element itself
                        except Exception as e_click:
                            logging.warning(
                                f"Direct click on '{matched_program}' failed: {e_click}. Trying JS click.")

                        # Fallback to JS click on the element itself if other methods failed
                        if not clicked:
                            try:
                                self.driver.execute_script(
                                    "arguments[0].click();", elem)
                                logging.info(
                                    f"Clicked '{matched_program}' using JavaScript on the <p> element.")
                                clicked = True
                                break
                            except Exception as e_js_click:
                                logging.error(
                                    f"JS click on '{matched_program}' also failed: {e_js_click}")

                if not clicked:
                    logging.error(
                        f"Found match '{matched_program}' but failed to click it through various methods.")
                    return False

                time.sleep(2)  # General wait after click
                # Add verification step: check if URL changed or a new expected element appeared
                # For example, wait for the "New" workout button to appear after clicking a phase
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "button[title='Create new workout']"))
                    )
                    logging.info(
                        "Verified navigation into program/phase (found 'New workout' button).")
                except TimeoutException:
                    logging.warning(
                        "Could not verify navigation into program/phase by presence of 'New workout' button. Proceeding with caution.")
                return True
            else:
                logging.warning(
                    f"Could not find a close match for program/phase '{program_week_name}' in the list: {program_names}")
                # self.driver.save_screenshot("program_not_found_click.png") # Optional
                return False

        except Exception as e:
            logging.error(
                f"Error clicking program/phase '{program_week_name}': {e}", exc_info=True)
            # self.driver.save_screenshot("click_program_error.png") # Optional
            return False

    def add_exercise(self, exercise_name_from_program, sets="3", reps="12"):
        """Adds exercise with fuzzy matching support and robust UI handling,
        including pre-matching against a known exercise list."""
        try:
            logging.info(
                f"Attempting to add exercise (from program): '{exercise_name_from_program}' (Sets: {sets}, Reps: {reps})")

            # Step 1: Pre-match exercise_name_from_program against self.exercise_list
            best_known_exercise_name, known_match_score = self.find_closest_match(
                exercise_name_from_program, self.exercise_list, threshold=70  # Lowered threshold
            )

            search_term_for_ui_initial = exercise_name_from_program

            if best_known_exercise_name:
                logging.info(
                    f"Pre-matched '{exercise_name_from_program}' to known exercise: '{best_known_exercise_name}' (Score: {known_match_score}%). Using this for primary UI search.")
                search_term_for_ui_initial = best_known_exercise_name  # Use exact known name
            else:
                logging.info(
                    f"No strong pre-match found for '{exercise_name_from_program}' in known exercise list. Using original/simplified name for UI search.")
                if "(" in search_term_for_ui_initial:
                    search_term_for_ui_initial = search_term_for_ui_initial.split("(", 1)[
                        0].strip()
                if len(search_term_for_ui_initial) > 30:
                    search_term_for_ui_initial = search_term_for_ui_initial[:30]

            search_box_locator = (
                By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")
            search_box = self.wait.until(
                EC.element_to_be_clickable(search_box_locator))

            def _search_and_get_ui_results(term_to_search):
                # (omitting unchanged inner function for brevity in this diff explanation)
                # ... (aggressive clear, search, get UI names) ...
                logging.info(
                    f"Aggressively clearing search box before typing '{term_to_search}'...")
                self.driver.execute_script(
                    "arguments[0].value = '';", search_box)
                for _ in range(40):
                    search_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)
                logging.info(f"Searching UI with term: '{term_to_search}'")
                search_box.send_keys(term_to_search)
                time.sleep(2)
                try:
                    exercise_library_container_locator = (
                        By.CSS_SELECTOR, ".exerciseLibrary-container")
                    self.wait.until(EC.visibility_of_element_located(
                        exercise_library_container_locator))
                    ui_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, ".exerciseLibrary-exercise div.flex-left p")
                    ui_names = [elem.text.strip()
                                for elem in ui_elements if elem.text.strip()]
                    logging.info(
                        f"Exercises found in UI for '{term_to_search}': {ui_names}")
                    return ui_names
                except TimeoutException:
                    logging.warning(
                        f"Timeout waiting for exercise library for term '{term_to_search}'. No results.")
                    return []
                except Exception as e_search_ui:
                    logging.error(
                        f"Error during UI search for '{term_to_search}': {e_search_ui}")
                    return []

            exercise_names_from_ui = _search_and_get_ui_results(
                search_term_for_ui_initial)
            final_search_term_used_for_match_selection = search_term_for_ui_initial

            if not exercise_names_from_ui and best_known_exercise_name and search_term_for_ui_initial == best_known_exercise_name:
                logging.warning(
                    f"No exercises found in UI for pre-matched term '{best_known_exercise_name}'. "
                    f"Falling back to original program name (simplified): '{exercise_name_from_program}'")
                fallback_search_term = exercise_name_from_program
                if "(" in fallback_search_term:
                    fallback_search_term = fallback_search_term.split("(", 1)[
                        0].strip()
                if len(fallback_search_term) > 30:
                    fallback_search_term = fallback_search_term[:30]
                if fallback_search_term != best_known_exercise_name:  # Avoid re-searching same term
                    exercise_names_from_ui = _search_and_get_ui_results(
                        fallback_search_term)
                    final_search_term_used_for_match_selection = fallback_search_term

            if not exercise_names_from_ui:
                logging.error(
                    f"No exercises found in UI for '{final_search_term_used_for_match_selection}'. Cannot add '{exercise_name_from_program}'.")
                try:
                    self.driver.execute_script(
                        "arguments[0].value = '';", search_box)
                    for _ in range(40):
                        search_box.send_keys(Keys.BACKSPACE)
                except:
                    pass
                return False

            clickable_exercise_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".exerciseLibrary-exercise")
            exercise_element_map = {}
            for el_card in clickable_exercise_elements:
                try:
                    name_p = el_card.find_element(
                        By.CSS_SELECTOR, "div.flex-left p")
                    exercise_element_map[name_p.text.strip()] = el_card
                except NoSuchElementException:
                    continue

            # Determine the target name for matching against UI results.
            # If a known exercise was used for search, prioritize that known name for selection.
            # Otherwise, use the original program name.
            target_for_ui_selection = best_known_exercise_name if best_known_exercise_name else exercise_name_from_program

            best_match_name_from_ui, ui_score = self.find_closest_match(
                target_for_ui_selection,
                list(exercise_element_map.keys()),
                threshold=55  # Lowered threshold
            )

            if best_match_name_from_ui and best_match_name_from_ui in exercise_element_map:
                best_elem_to_click = exercise_element_map[best_match_name_from_ui]
                logging.info(
                    f"Best UI match for target '{target_for_ui_selection}' is '{best_match_name_from_ui}' (Score: {ui_score}%). Clicking it.")
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", best_elem_to_click)
                    time.sleep(0.5)
                    best_elem_to_click.click()
                except ElementClickInterceptedException:
                    logging.warning(
                        f"Direct click on '{best_match_name_from_ui}' intercepted. Trying JS click.")
                    self.driver.execute_script(
                        "arguments[0].click();", best_elem_to_click)
                time.sleep(1.5)
            else:
                logging.warning(
                    f"Could not find a sufficiently close UI match for target '{target_for_ui_selection}' (Best: '{best_match_name_from_ui}', Score: {ui_score}%). "
                    f"Searched with '{final_search_term_used_for_match_selection}'. UI List: {list(exercise_element_map.keys())}")
                try:
                    self.driver.execute_script(
                        "arguments[0].value = '';", search_box)
                    for _ in range(40):
                        search_box.send_keys(Keys.BACKSPACE)
                except:
                    pass
                return False

            # ... (Rest of the method: add_button_selectors, sets/reps, final clear - unchanged)

            add_button_selectors = [
                "button[data-testid='exerciseDetail-addToWorkoutButton']",
                "//button[.//span[contains(text(), 'Add to Workout')]]",
                "//button[contains(text(), 'Add to Workout')]"
            ]
            add_button_clicked = False
            for selector_str in add_button_selectors:
                try:
                    logging.info(
                        f"Trying to find 'Add to Workout' button with: {selector_str}")
                    if selector_str.startswith("//"):
                        add_button = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, selector_str)))
                    else:
                        add_button = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector_str)))
                    self.driver.execute_script(
                        "arguments[0].click();", add_button)
                    logging.info("Clicked 'Add to Workout' button.")
                    add_button_clicked = True
                    time.sleep(2)
                    break
                except TimeoutException:
                    logging.debug(
                        f"'Add to Workout' selector timed out: {selector_str}")
                except Exception as e_add_btn:
                    logging.warning(
                        f"Error with 'Add to Workout' selector {selector_str}: {e_add_btn}")

            if not add_button_clicked:
                logging.error(
                    "Failed to click 'Add to Workout' button with any selector.")
                # Aggressively clear search box on error
                try:
                    self.driver.execute_script(
                        "arguments[0].value = '';", search_box)
                    for _ in range(40):
                        search_box.send_keys(Keys.BACKSPACE)
                except:
                    pass
                return False

            # Aggressively clear search box after adding an exercise
            try:
                search_box_after_add = self.wait.until(
                    EC.element_to_be_clickable(search_box_locator))
                logging.info(
                    "Aggressively clearing search box after adding exercise...")
                self.driver.execute_script(
                    "arguments[0].value = '';", search_box_after_add)
                for _ in range(40):
                    search_box_after_add.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)
            except Exception as e_clear:
                logging.warning(
                    f"Could not clear search box after adding exercise: {e_clear}")

            try:
                all_sets_inputs = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[data-testid='workoutBuilder-exerciseSetInput']")))
                all_reps_inputs = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[data-testid='workoutBuilder-recordTypeInput']")))

                if not all_sets_inputs or not all_reps_inputs:
                    logging.error(
                        "Could not find sets/reps input fields after adding exercise.")
                    return False  # Should ideally clear search box here too

                last_sets_input = all_sets_inputs[-1]
                last_reps_input = all_reps_inputs[-1]

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", last_sets_input)
                time.sleep(0.3)
                last_sets_input.click()
                last_sets_input.send_keys(Keys.CONTROL + "a")
                last_sets_input.send_keys(Keys.DELETE)
                last_sets_input.send_keys(str(sets))
                time.sleep(0.2)

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", last_reps_input)
                time.sleep(0.3)
                last_reps_input.click()
                last_reps_input.send_keys(Keys.CONTROL + "a")
                last_reps_input.send_keys(Keys.DELETE)
                last_reps_input.send_keys(str(reps))
                time.sleep(0.2)
                try:  # Click workout title to remove focus from input
                    workout_title_element = self.driver.find_element(
                        By.CSS_SELECTOR, "input[placeholder*='workout name']")
                    workout_title_element.click()
                except:
                    pass

                logging.info(
                    f"Successfully set Sets='{sets}' and Reps='{reps}' for '{best_match_name_from_ui}' (original: '{exercise_name_from_program}').")
                return True
            except TimeoutException:
                logging.error(
                    f"Timeout finding sets/reps fields for '{best_match_name_from_ui}'. Exercise might have been added, but sets/reps not set.")
                return False  # Clear search box
            except Exception as e_set_reps:
                logging.error(
                    f"Error setting sets/reps for '{best_match_name_from_ui}': {e_set_reps}", exc_info=True)
                return False  # Clear search box

        except Exception as e:
            logging.error(
                f"Major error in add_exercise for '{exercise_name_from_program}': {e}", exc_info=True)
            try:  # Attempt to clear search box even in major error
                search_box_on_error = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))  # Re-define search_box_locator if not in scope
                self.driver.execute_script(
                    "arguments[0].value = '';", search_box_on_error)
                for _ in range(40):
                    search_box_on_error.send_keys(Keys.BACKSPACE)
            except:
                pass
            return False

    # chest_exercises is a legacy param, not directly used for phase creation
    def create_program(self, program_week_name, chest_exercises=None):
        logging.info(
            f"=== Entered create_program (create new Training Phase) with name: {program_week_name} ===")
        try:
            logging.info(f"Target Training Phase name: {program_week_name}")
            logging.info(
                f"Current URL before Training Phase creation: {self.driver.current_url}")

            # Click '+ Add next' (or similar for creating a new phase)
            # This button is usually for adding a new *phase* to an existing client program plan.
            add_next_phase_selectors = [
                "//p[contains(text(), '+ Add next')]",  # From pe.py
                # More generic for phase
                "//button[contains(., 'Add New Phase') or contains(., 'Add Phase')]",
                # Specific test ID if available
                "//button[@data-testid='trainingPlanGrid-addPhaseButton']"
            ]
            add_next_button = None
            for selector in add_next_phase_selectors:
                try:
                    logging.info(
                        f"Trying to find 'Add Next Phase' button with selector: {selector}")
                    add_next_button = WebDriverWait(self.driver, 7).until(
                        # Assuming XPATH for these general ones
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logging.info(
                        f"Found 'Add Next Phase' button with selector: {selector}")
                    break
                except TimeoutException:
                    logging.debug(
                        f"'Add Next Phase' selector {selector} timed out.")
                except Exception as e_sel:
                    logging.warning(
                        f"Error with 'Add Next Phase' selector {selector}: {e_sel}")

            if not add_next_button:
                logging.error(
                    "Could not find 'Add Next Phase' (or '+ Add next') button with any selector.")
                # self.driver.save_screenshot("add_phase_button_not_found.png") # Optional
                return False

            self.driver.execute_script(
                "arguments[0].click();", add_next_button)
            time.sleep(1)
            logging.info("Clicked 'Add Next Phase' button.")
            # self.driver.save_screenshot("after_add_next_phase_click.png") # Optional

            # Modal for Training Phase Name and Duration
            try:
                logging.info(
                    "Waiting for 'Add Next Training Phase' modal to appear...")
                # Ensure modal is fully loaded by waiting for a known element like the name input
                name_input_locator = (
                    By.CSS_SELECTOR, "input[data-testid='editTrainingPhase-nameInput']")
                name_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(name_input_locator))

                duration_input = self.driver.find_element(
                    By.CSS_SELECTOR, "input[data-testid='editTrainingPhase-durationInput']")
                save_button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']")
                # self.driver.save_screenshot("training_phase_modal_open.png") # Optional

                name_input.clear()
                # This is the Training Phase name
                name_input.send_keys(program_week_name)
                logging.info(
                    f"Entered Training Phase name: {program_week_name}")

                duration_input.clear()
                # Default duration, can be parameterized if needed
                duration_input.send_keys("6")
                logging.info("Set duration to 6 weeks for the phase.")
                # self.driver.save_screenshot("training_phase_modal_filled.png") # Optional

                save_button.click()
                logging.info("Clicked Save on Training Phase modal.")
                time.sleep(2)  # Wait for modal to close and UI to update
            except Exception as e_modal:
                logging.error(
                    f"Failed to fill or save Training Phase modal: {e_modal}", exc_info=True)
                # self.driver.save_screenshot("training_phase_modal_error.png") # Optional
                return False

            # After creating the phase, Trainerize usually selects it and is ready for the first workout.
            # We need to ensure the UI is in the state where clicking "New" (workout) is possible within this new phase.
            # This might involve clicking on the newly created phase if it's not auto-selected.
            # For now, assume Trainerize auto-selects the new phase.

            logging.info(
                f"Training Phase '{program_week_name}' created. Ready for first workout.")
            # The old create_program from pe.py used to click "New" workout here.
            # This responsibility is now shifted to the start of create_workout for better modularity.
            return True
        except Exception as e:
            logging.error(
                f"Exception in create_program (Training Phase creation): {e}", exc_info=True)
            # self.driver.save_screenshot("create_program_phase_exception.png") # Optional
            return False

    def create_workout(self, program_name, workout_name, exercises, already_in_program=False):
        """Creates a new workout with specified exercises. 
        If already_in_program is True, it assumes the correct Training Phase (program_name) is already selected.
        This method will click the 'New' button to start a new workout within that phase.
        """
        try:
            logging.info(
                f"Starting workout creation: '{workout_name}' within phase '{program_name}'")

            # If not already in the specific program/phase context, click on it.
            # For this script's flow, create_program handles getting into the new phase context initially.
            # Subsequent calls to create_workout for the same phase pass already_in_program=True.
            if not already_in_program:
                # program_name here is the Training Phase name
                if not self.click_program(program_name):
                    logging.error(
                        f"Failed to click/select Training Phase '{program_name}'. Cannot create workout '{workout_name}'.")
                    return False
            else:
                logging.info(
                    f"Already in program/phase '{program_name}'. Proceeding to create workout '{workout_name}'.")

            # Click "New" workout button (specific to adding a workout to the currently selected phase)
            new_workout_button_locators = [
                (By.CSS_SELECTOR, "button[title='Create new workout']"),
                # General New button for workout
                (By.XPATH,
                 "//button[contains(., 'New Workout') or contains(., 'New') and not(contains(.,'Phase'))]")
            ]
            new_button_clicked = False
            for loc_type, selector in new_workout_button_locators:
                try:
                    logging.info(
                        f"Trying to click 'New Workout' button with {loc_type}: {selector}")
                    new_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((loc_type, selector)))
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", new_button)
                    time.sleep(0.5)
                    new_button.click()
                    logging.info("Clicked 'New Workout' button.")
                    new_button_clicked = True
                    time.sleep(2)  # Wait for workout type selection to appear
                    break
                except TimeoutException:
                    logging.debug(
                        f"'New Workout' button not found with {loc_type}: {selector}. Trying next.")
                except Exception as e_new_btn:
                    logging.warning(
                        f"Error clicking 'New Workout' button with {loc_type}: {selector} - {e_new_btn}")

            if not new_button_clicked:
                logging.error(
                    "Failed to click 'New Workout' button with any locator.")
                # self.driver.save_screenshot(f"new_workout_button_fail_{workout_name.replace(' ','_')}.png") # Optional
                return False

            # Select "Regular" workout type
            try:
                workout_type_selectors = [
                    "label[data-testid='workoutBuilder-regularWorkout']",
                    "label#regular-label",
                    # More robust XPath
                    "//label[.//div[contains(text(),'Regular')]]"
                ]
                type_clicked = False
                for selector in workout_type_selectors:
                    try:
                        logging.info(
                            f"Trying to click Regular workout type with selector: {selector}")
                        type_button = WebDriverWait(self.driver, 7).until(
                            EC.element_to_be_clickable(
                                (By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector))
                        )
                        type_button.click()
                        logging.info(
                            "Successfully clicked Regular workout type.")
                        type_clicked = True
                        time.sleep(1)
                        break
                    except Exception as e_type:
                        logging.debug(
                            f"Failed to click workout type with selector {selector}: {e_type}")
                if not type_clicked:
                    logging.error(
                        "Failed to select Regular workout type after trying all selectors.")
                    return False
            except Exception as e_type_major:
                logging.error(
                    f"Major error selecting workout type: {e_type_major}", exc_info=True)
                return False

            # Set workout name
            try:
                name_input_selectors = [
                    "input[placeholder='workout name, like Day 1 Abs']",
                    # XPath for reliability
                    "//input[contains(@class, 'ant-input') and contains(@placeholder, 'workout name')]"
                ]
                name_input = None
                for selector in name_input_selectors:
                    try:
                        name_input = WebDriverWait(self.driver, 7).until(
                            EC.presence_of_element_located(
                                (By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector))
                        )
                        if name_input:
                            break
                    except TimeoutException:
                        logging.debug(
                            f"Workout name input not found with selector: {selector}")

                if not name_input:
                    logging.error(
                        "Could not find workout name input field with any selector.")
                    return False

                name_input.clear()
                name_input.send_keys(workout_name)
                # Tab out to help ensure value is registered
                name_input.send_keys(Keys.TAB)
                logging.info(f"Set workout name to '{workout_name}'.")
                time.sleep(1)
            except Exception as e_name:
                logging.error(
                    f"Error setting workout name '{workout_name}': {e_name}", exc_info=True)
                return False

            # Click "START BUILDING" button
            try:
                start_building_selectors = [
                    "button[data-testid='workoutBuilder-startBuildingButton']",
                    # Robust XPath
                    "//button[.//span[contains(text(),'START BUILDING')] or contains(text(),'START BUILDING')]"
                ]
                start_building_clicked = False
                for selector in start_building_selectors:
                    try:
                        logging.info(
                            f"Trying to click START BUILDING button with selector: {selector}")
                        start_building_button = WebDriverWait(self.driver, 7).until(
                            EC.element_to_be_clickable(
                                (By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector))
                        )
                        self.driver.execute_script(
                            "arguments[0].click();", start_building_button)
                        logging.info("Clicked START BUILDING button.")
                        start_building_clicked = True
                        time.sleep(3)  # Wait for exercise search area to load
                        break
                    except TimeoutException:
                        logging.debug(
                            f"START BUILDING selector timed out: {selector}")
                    except Exception as e_start_build:
                        logging.warning(
                            f"Error with START BUILDING selector {selector}: {e_start_build}")

                if not start_building_clicked:
                    logging.error(
                        "Failed to click START BUILDING button with any selector.")
                    return False

                # Verify entry into exercise builder mode
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search for an exercise']")))
                logging.info(
                    "Successfully entered exercise builder mode for workout.")
            except Exception as e_start_build_major:
                logging.error(
                    f"Error clicking START BUILDING or verifying entry: {e_start_build_major}", exc_info=True)
                return False

            # Add exercises
            failed_exercises = []
            for exercise_detail in exercises:
                ex_name = exercise_detail.get('name', '')
                ex_sets = exercise_detail.get(
                    'sets', '3')  # Default if not provided
                ex_reps = exercise_detail.get(
                    'reps', '12')  # Default if not provided

                if not ex_name:
                    logging.warning("Skipping exercise with no name.")
                    continue

                if not self.add_exercise(ex_name, ex_sets, ex_reps):
                    logging.warning(
                        f"Failed to add exercise '{ex_name}'. Continuing with next exercise...")
                    failed_exercises.append(ex_name)
                else:
                    logging.info(
                        f"Successfully added and configured exercise '{ex_name}'.")
                time.sleep(0.5)  # Small pause between adding exercises

            if failed_exercises:
                logging.warning(
                    f"Workout '{workout_name}' built, but {len(failed_exercises)} exercises failed to add: {', '.join(failed_exercises)}")
            else:
                logging.info(
                    f"All exercises for workout '{workout_name}' added successfully.")

            # Save the workout
            try:
                save_workout_selectors = [
                    "button[data-testid='workoutBuilder-saveBtn']",
                    # Save button, not for phase
                    "//button[.//span[contains(text(),'Save')] and not(contains(.,'Phase'))]"
                ]
                save_clicked = False
                for selector in save_workout_selectors:
                    try:
                        logging.info(
                            f"Trying to find Save Workout button with selector: {selector}")
                        if selector.startswith("//"):
                            save_button = WebDriverWait(self.driver, 7).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                        else:
                            save_button = WebDriverWait(self.driver, 7).until(
                                EC.element_to_be_clickable(
                                    (By.CSS_SELECTOR, selector))
                            )
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", save_button)
                        time.sleep(0.5)
                        self.driver.execute_script(
                            "arguments[0].click();", save_button)
                        logging.info("Clicked Save Workout button.")
                        save_clicked = True
                        # Wait for save and UI update (e.g., back to phase view)
                        time.sleep(3)
                        break
                    except TimeoutException:
                        logging.debug(
                            f"Save Workout selector timed out: {selector}")
                    except Exception as e_save_btn:
                        logging.warning(
                            f"Error with Save Workout selector {selector}: {e_save_btn}")

                if not save_clicked:
                    logging.error("Failed to click Save Workout button.")
                    return False

                # Verify return to the training phase view (e.g., by checking for phase name or add workout button)
                # Construct the XPath carefully to handle apostrophes in program_name

                # Basic XPath part for program name, works if no apostrophes or if outer quotes handle it.
                # Using double quotes for the text() argument to allow single quotes within program_name.
                program_name_xpath_part = f'//p[contains(text(),"{program_name}")]'

                # If program_name contains an apostrophe, build a more robust concat() XPath
                if "'" in program_name:
                    parts = program_name.split("'")
                    concat_argument_parts = []
                    for i, part in enumerate(parts):
                        # Enclose each part in single quotes for XPath string literal
                        concat_argument_parts.append(f"'{part}'")
                        if i < len(parts) - 1:
                            # Add the apostrophe itself, as an XPath string literal: "'"
                            concat_argument_parts.append('"\'"')
                    concat_argument = ",".join(concat_argument_parts)
                    program_name_xpath_part = f"//p[contains(text(),concat({concat_argument}))]"

                verification_xpath = f"{program_name_xpath_part} | //button[@title='Create new workout']"
                logging.info(f"Using verification XPath: {verification_xpath}")

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, verification_xpath))
                )
                logging.info(
                    f"Workout '{workout_name}' saved successfully and returned to phase view.")
                return True
            except Exception as e_save_workout:
                logging.error(
                    f"Error saving workout '{workout_name}' or verifying return: {e_save_workout}", exc_info=True)
                return False

        except Exception as e_create_workout:
            logging.error(
                f"Major error creating workout '{workout_name}': {e_create_workout}", exc_info=True)
            # self.driver.save_screenshot(f"create_workout_error_{workout_name.replace(' ','_')}.png") # Optional
            return False

    def cleanup(self):
        """Cleans up resources (removes temp dir, and closes driver)."""
        try:
            logging.info("Cleaning up TrainerizeAutomation resources...")
            if hasattr(self, 'driver') and self.driver:
                logging.info("Closing webdriver...")
                self.driver.quit()  # Quit closes all windows and exits driver gracefully
                self.driver = None
                logging.info("Webdriver closed.")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                logging.info(
                    f"Removing temp user data directory: {self.temp_user_data_dir}")
                try:
                    shutil.rmtree(self.temp_user_data_dir)
                    logging.info("Temp directory removed.")
                except Exception as e_rmtree:
                    logging.error(
                        f"Error removing temp directory {self.temp_user_data_dir}: {e_rmtree}")
            logging.info("Cleanup completed.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def _click_sidebar_tab_calendar(self):
        try:
            logging.info(
                f"Attempting to click Calendar tab. Current URL: {self.driver.current_url}")
            calendar_tab_locators = [
                (By.CSS_SELECTOR,
                 "a#nav_calendar[data-testid='leftNavMenu-item-calendar']"),
                (By.XPATH,
                 "//a[@title='Calendar' and .//svg[@name='outline/calendar/calendar-regular']]"),
                (By.XPATH, "//a[.//span[contains(text(),'Calendar')]]")
            ]
            calendar_tab = None
            selected_locator_info = ""

            for loc_type, selector in calendar_tab_locators:
                try:
                    calendar_tab = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((loc_type, selector)))
                    if calendar_tab:
                        selected_locator_info = f"{loc_type}: {selector}"
                        logging.info(
                            f"Calendar tab found with: {selected_locator_info}")
                        break
                except TimeoutException:
                    logging.debug(
                        f"Calendar tab not found with {loc_type}: {selector}")
                    continue

            if not calendar_tab:
                logging.error(
                    "Calendar tab not found in sidebar with any selector.")
                return False

            # Attempt to click multiple times if needed
            max_click_attempts = 3
            for attempt in range(max_click_attempts):
                logging.info(
                    f"Attempt {attempt + 1}/{max_click_attempts} to click Calendar tab ({selected_locator_info}).")
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", calendar_tab)
                    time.sleep(0.5)
                    calendar_tab.click()
                    logging.info(
                        f"Clicked Calendar tab. Waiting for URL to contain 'calendar/view'. Post-click URL: {self.driver.current_url}")
                    time.sleep(3)  # Increased explicit wait after click
                    WebDriverWait(self.driver, 15).until(  # Increased wait for URL verification
                        EC.url_contains("calendar/view"))
                    logging.info(
                        "Successfully navigated to Calendar (URL verified).")
                    return True
                except ElementClickInterceptedException as eci:
                    logging.warning(
                        f"Calendar tab click intercepted (Attempt {attempt + 1}): {eci}. Retrying if possible.")
                    if attempt == max_click_attempts - 1:
                        logging.error(
                            "Calendar tab click intercepted on final attempt.")
                        return False
                    time.sleep(1)  # Wait before retrying click
                except TimeoutException as te_url:
                    logging.warning(
                        f"URL did not contain 'calendar/view' after click (Attempt {attempt + 1}). Current URL: {self.driver.current_url}. Error: {te_url}")
                    # Re-fetch element in case it went stale, before next attempt
                    try:
                        loc_type_orig, selector_orig = calendar_tab_locators[calendar_tab_locators.index(
                            (loc_type, selector))]
                        calendar_tab = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((loc_type_orig, selector_orig)))
                    except:
                        logging.error(
                            "Failed to re-fetch calendar tab element before retry.")
                        return False  # If element cannot be re-fetched, stop.
                    if attempt == max_click_attempts - 1:
                        logging.error(
                            "Failed to verify calendar navigation after max attempts.")
                        return False
                    # No explicit time.sleep here, next loop iteration will have one if it's not the last
                except Exception as e_click_generic:
                    logging.error(
                        f"Generic error clicking calendar tab (Attempt {attempt + 1}): {e_click_generic}")
                    if attempt == max_click_attempts - 1:
                        return False
                    time.sleep(1)
            return False  # Should be unreachable if loop logic is correct, but as a safeguard

        except Exception as e_cal:
            logging.error(
                f"Overall error in _click_sidebar_tab_calendar: {e_cal}", exc_info=True)
            return False

    def schedule_workouts_and_cardio(self):
        import traceback  # Ensure traceback is imported if used
        try:
            logging.info("Starting to schedule workouts and cardio...")
            # This method might need adjustment if Elena's program has different workout names
            # than the default "Chest Day", "Back Day" etc. hardcoded here.
            # For now, assuming it needs to be generalized or the workout_schedule here
            # should be dynamically built based on Elena's program workout_definitions.

            # ---- TODO: Generalize workout_schedule based on program_to_build ----
            # Example: iterate through ELENA_GREEN_WORKOUT_PROGRAM["workout_definitions"]
            # and map them to days if a specific schedule is desired.
            # For now, using the default schedule from pe.py for structure, but this needs review.
            workout_schedule_from_program = []
            days_of_week = ["Monday", "Tuesday", "Wednesday",
                            "Thursday", "Friday", "Saturday", "Sunday"]
            current_day_index = 0
            for wd in ELENA_GREEN_WORKOUT_PROGRAM.get("workout_definitions", []):
                # This is Elena's workout name
                workout_name_from_def = wd.get("day_type")
                if workout_name_from_def and current_day_index < len(days_of_week):
                    workout_schedule_from_program.append(
                        (workout_name_from_def, days_of_week[current_day_index]))
                    # Cycle through days
                    current_day_index = (
                        current_day_index + 1) % len(days_of_week)
                if current_day_index >= 4:  # Stop after 4 days for Elena as it is a 4 day program
                    break

            if not workout_schedule_from_program:
                logging.warning(
                    "Could not dynamically create workout_schedule. Using pe.py default. This might not match Elena's program.")
                workout_schedule_from_program = [
                    ("Day 1: Upper Body Push + Handstand & Core", "Monday"),
                    ("Day 2: Lower Body Strength + Kettlebell Focus", "Tuesday"),
                    ("Day 3: Upper Body Pull + Chin-up & Core", "Wednesday"),
                    ("Day 4: Full Body Strength & Splits Practice", "Thursday"),
                ]
            else:
                logging.info(
                    f"Dynamically created workout schedule: {workout_schedule_from_program}")

            # Default cardio and repeat settings from pe.py, can be customized
            cardio_days = ["Monday", "Wednesday",
                           "Friday"]  # Example: 3 days cardio
            cardio_activity = "Walking"
            repeat_weeks = "6"

            # The local definition of click_sidebar_tab_calendar (previously lines 1265-1289) is removed.
            # Its functionality is now in self._click_sidebar_tab_calendar()

            if not self._click_sidebar_tab_calendar():  # MODIFIED call
                return False

            for workout_name, day_title in workout_schedule_from_program:
                try:
                    logging.info(
                        f"Scheduling workout: '{workout_name}' on {day_title}")

                    # Click "Schedule" or "+" button on calendar for the target day
                    # This part needs to be adapted to how Trainerize calendar allows scheduling.
                    # For now, using the modal approach from pe.py
                    schedule_btn_main_page = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                        # This is from program view, may not exist in calendar view
                        By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                        # TODO: Find correct button on Calendar page to schedule an activity
                        # For now, let's assume it opens a similar modal flow
                    )))
                    schedule_btn_main_page.click()
                    time.sleep(1)

                    workout_menu_item = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        # More general
                        By.XPATH, "//li[@data-testid='dropdownButton-menuItem-workout'] | //li[.//p[text()='Workout']]"
                    )))
                    workout_menu_item.click()
                    time.sleep(1)

                    # "Select from current training program" - this implies we are selecting from a list of workouts already CREATED.
                    select_from_program_text = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.XPATH, "//p[contains(@class, 'color--black') and (contains(text(),'Select from current training program') or contains(text(),'Choose a workout'))]"
                    )))
                    select_from_program_text.click()
                    time.sleep(0.5)

                    # Type in workout name
                    workout_input_placeholder = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.XPATH, "//div[contains(@class, 'ant-select-selection__placeholder') and (contains(text(), 'Type in workout name') or contains(text(),'Select Workout'))]"
                    )))
                    workout_input_placeholder.click()

                    input_box_actual = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
                        By.XPATH, "//input[contains(@class, 'ant-select-search__field')]"
                    )))
                    input_box_actual.clear()
                    input_box_actual.send_keys(workout_name)
                    time.sleep(1)  # Let dropdown populate

                    # Click the matching workout from dropdown
                    workout_option_in_dropdown = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        # Using a more specific XPath to find the workout by its name in the dropdown results
                        By.XPATH, f"//div[contains(@class, 'ant-select-dropdown')]//li[contains(normalize-space(), '{workout_name}')] | //div[contains(@class, 'ant-select-dropdown')]//p[contains(normalize-space(), '{workout_name}')]"
                    )))
                    workout_option_in_dropdown.click()
                    time.sleep(0.5)

                    # Click the main area of the dialog to ensure dropdown closes (if needed)
                    # add_activity_header = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((
                    #     By.XPATH, "//h2[contains(text(), 'Add Activity')] | //div[contains(@class,'modal-title') and contains(.,'Add Activity') ]"
                    # )))
                    # add_activity_header.click()
                    # time.sleep(1)

                    # Setup Repeat
                    repeat_setup_btn = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
                    )))
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", repeat_setup_btn)
                    time.sleep(0.3)
                    repeat_setup_btn.click()
                    time.sleep(1)

                    day_button_to_click = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{day_title}']"
                    )))
                    day_button_to_click.click()
                    time.sleep(0.5)

                    repeat_for_dropdown = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
                    )))
                    repeat_for_dropdown.click()

                    weeks_option = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-{repeat_weeks}']"
                    )))
                    weeks_option.click()
                    time.sleep(0.5)

                    apply_repeat_btn = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
                    )))
                    apply_repeat_btn.click()
                    time.sleep(1)

                    add_activity_final_btn = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
                    )))
                    add_activity_final_btn.click()
                    # Wait for activity to be added and modal to close
                    time.sleep(3)
                    logging.info(
                        f"Successfully scheduled workout '{workout_name}' for {day_title} repeating for {repeat_weeks} weeks.")
                except Exception as e_sch_wk:
                    logging.error(
                        f"Error scheduling workout '{workout_name}': {e_sch_wk}\n{traceback.format_exc()}")
                    # self.driver.save_screenshot(f"schedule_workout_fail_{workout_name.replace(' ','_')}.png") # Optional
                    # Try to close modal if it's stuck
                    try:
                        cancel_btn = self.driver.find_element(
                            By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-cancel-button']")
                        cancel_btn.click()
                        time.sleep(1)
                    except:
                        pass

            # Schedule Cardio
            logging.info(
                f"Scheduling cardio: {cardio_activity} on {', '.join(cardio_days)} for {repeat_weeks} weeks")
            try:
                # Similar flow as scheduling a workout, but select Cardio type
                schedule_btn_main_page_cardio = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                    # TODO: Find correct button on Calendar page to schedule an activity
                )))
                schedule_btn_main_page_cardio.click()
                time.sleep(1)

                cardio_menu_item = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.XPATH, "//li[.//p[text()='Cardio']] | //li[@data-testid='dropdownButton-menuItem-cardio']"
                )))
                cardio_menu_item.click()
                time.sleep(1)

                activity_dropdown_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    # This is generic, might need to be more specific
                    By.CSS_SELECTOR, "div.ant-select-selection__rendered"
                    # Consider XPATH like: "//label[contains(text(),'Activity')]/following-sibling::div//div[contains(@class,'ant-select-selection__rendered')]"
                )))
                activity_dropdown_cardio.click()
                time.sleep(0.5)

                walking_option_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.XPATH, f"//li[contains(@data-testid, 'activity-cardio-activitySelectOption-{cardio_activity.lower()}')] | //li[contains(text(),'{cardio_activity}')]"
                )))
                walking_option_cardio.click()
                time.sleep(0.5)

                add_own_target_span_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.XPATH, "//span[text()='Add my own target']"
                )))
                add_own_target_span_cardio.click()
                time.sleep(0.5)

                target_input_cardio = WebDriverWait(self.driver, 7).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, "input[data-testid='multipleActivitiesDialog-activity-cardio-target-textInput']"
                )))
                target_input_cardio.clear()
                target_input_cardio.send_keys("10,000 Steps")  # Example target
                time.sleep(0.5)

                # Setup Repeat for Cardio
                repeat_setup_btn_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
                )))
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", repeat_setup_btn_cardio)
                time.sleep(0.3)
                repeat_setup_btn_cardio.click()
                time.sleep(1)

                for day_title_cardio in cardio_days:
                    day_button_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{day_title_cardio}']"
                    )))
                    # Ensure it's not already selected before clicking, to toggle if needed
                    if "selected" not in day_button_cardio.get_attribute("class"):
                        day_button_cardio.click()
                    time.sleep(0.2)
                time.sleep(0.5)

                repeat_for_dropdown_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
                )))
                repeat_for_dropdown_cardio.click()

                weeks_option_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-{repeat_weeks}']"
                )))
                weeks_option_cardio.click()
                time.sleep(0.5)

                apply_repeat_btn_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
                )))
                apply_repeat_btn_cardio.click()
                time.sleep(1)

                add_activity_final_btn_cardio = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
                )))
                add_activity_final_btn_cardio.click()
                time.sleep(3)
                logging.info(
                    f"Successfully scheduled cardio '{cardio_activity}' for specified days.")
            except Exception as e_sch_cardio:
                logging.error(
                    f"Error scheduling cardio: {e_sch_cardio}\n{traceback.format_exc()}")
                # self.driver.save_screenshot("schedule_cardio_fail.png") # Optional

            logging.info("Finished attempt to schedule workouts and cardio.")
            time.sleep(5)  # Longer pause after all scheduling
            return True  # Return true even if some parts had minor issues but didn't crash
        except Exception as e_main_sch:
            logging.error(
                f"Major error in schedule_workouts_and_cardio: {e_main_sch}\n{traceback.format_exc()}")
            # self.driver.save_screenshot("schedule_workouts_cardio_major_error.png") # Optional
            return False

    def schedule_body_stats(self):
        import traceback
        try:
            logging.info(
                "Scheduling Body stats on Monday, repeat for 6 weeks.")
            # Ensure we are on calendar
            if not self.driver.current_url.endswith("calendar/view"):
                # Re-navigate if not on calendar
                if not self._click_sidebar_tab_calendar():  # MODIFIED call
                    logging.error(
                        "Failed to navigate to calendar in schedule_body_stats. Aborting scheduling body stats.")
                    return False

            schedule_btn_main_page_bs = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                # TODO: Find correct button on Calendar page to schedule an activity
            )))
            schedule_btn_main_page_bs.click()
            time.sleep(1)

            body_stats_menu_item = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, "//li[.//p[text()='Body stats']] | //li[@data-testid='dropdownButton-menuItem-bodyStats']"
            )))
            body_stats_menu_item.click()
            time.sleep(1)

            # Setup Repeat for Body Stats
            repeat_setup_btn_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", repeat_setup_btn_bs)
            time.sleep(0.3)
            repeat_setup_btn_bs.click()
            time.sleep(1)

            day_button_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, f"//button[@data-testid and @title='Monday']"
            )))
            if "selected" not in day_button_bs.get_attribute("class"):
                day_button_bs.click()
            time.sleep(0.5)

            repeat_for_dropdown_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_for_dropdown_bs.click()

            weeks_option_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            weeks_option_bs.click()
            time.sleep(0.5)

            apply_repeat_btn_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_repeat_btn_bs.click()
            time.sleep(1)

            add_activity_final_btn_bs = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_activity_final_btn_bs.click()
            time.sleep(3)
            logging.info("Successfully scheduled Body Stats.")
            return True
        except Exception as e_bs:
            logging.error(
                f"Error in schedule_body_stats: {e_bs}\n{traceback.format_exc()}")
            # self.driver.save_screenshot("schedule_body_stats_error.png") # Optional
            return False

    def schedule_progress_photos(self):
        import traceback
        try:
            logging.info(
                "Scheduling Progress Photos on Monday, repeat for 6 weeks.")
            # Ensure we are on calendar
            if not self.driver.current_url.endswith("calendar/view"):
                if not self._click_sidebar_tab_calendar():  # MODIFIED call
                    logging.error(
                        "Failed to navigate to calendar in schedule_progress_photos. Aborting scheduling progress photos.")
                    return False

            schedule_btn_main_page_ph = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                # TODO: Find correct button on Calendar page to schedule an activity
            )))
            schedule_btn_main_page_ph.click()
            time.sleep(1)

            photos_menu_item = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, "//li[.//p[text()='Photos']] | //li[@data-testid='dropdownButton-menuItem-photos']"
            )))
            photos_menu_item.click()
            time.sleep(1)

            # Setup Repeat for Progress Photos
            repeat_setup_btn_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", repeat_setup_btn_ph)
            time.sleep(0.3)
            repeat_setup_btn_ph.click()
            time.sleep(1)

            day_button_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, f"//button[@data-testid and @title='Monday']"
            )))
            if "selected" not in day_button_ph.get_attribute("class"):
                day_button_ph.click()
            time.sleep(0.5)

            repeat_for_dropdown_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_for_dropdown_ph.click()

            weeks_option_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            weeks_option_ph.click()
            time.sleep(0.5)

            apply_repeat_btn_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_repeat_btn_ph.click()
            time.sleep(1)

            add_activity_final_btn_ph = WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_activity_final_btn_ph.click()
            time.sleep(3)
            logging.info("Successfully scheduled Progress Photos.")
            return True
        except Exception as e_ph:
            logging.error(
                f"Error in schedule_progress_photos: {e_ph}\n{traceback.format_exc()}")
            # self.driver.save_screenshot("schedule_photos_error.png") # Optional
            return False

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# End of TrainerizeAutomation class
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# Elena Green's 4-Day Custom Workout Program (Hardcoded for this script)
ELENA_GREEN_WORKOUT_PROGRAM = {
    "client_name": "Elena Green",  # This will be confirmed by the script argument
    # Name of the training phase
    "program_name": "Elena Green's 4-Day Home Strength & Skills",
    "workout_definitions": [
        {
            # This will be the workout name
            "day_type": "Day 1: Upper Body Push + Handstand & Core",
            "exercises_list": [
                {"name": "Handstand Practice (Wall Holds or Pike Push-ups on paralettes)",
                 "sets": "3-5", "reps": "15-60s holds or 6-12 reps"},
                {"name": "Dumbbell Bench Press (or Floor Press)",
                 "sets": "3-4", "reps": "8-12"},
                {"name": "Ring Push-ups (or DB/Paralette Push-ups)",
                 "sets": "3", "reps": "RPE 8-9"},
                {"name": "Dumbbell Shoulder Press",
                    "sets": "3-4", "reps": "10-15"},
                {"name": "Dumbbell Lateral Raises", "sets": "3", "reps": "12-18"},
                {"name": "Ring Dips (or Bench Dips/Band-Assisted Dips)",
                 "sets": "3", "reps": "RPE 8-9"},
                {"name": "Core: L-Sit/Tuck Sit Practice (paralettes/rings)",
                 "sets": "3", "reps": "10-30s holds"},
                {"name": "Core: Plank", "sets": "3", "reps": "30-60s holds"}
            ]
        },
        {
            "day_type": "Day 2: Lower Body Strength + Kettlebell Focus",
            "exercises_list": [
                {"name": "Kettlebell Goblet Squats", "sets": "4", "reps": "10-15"},
                {"name": "Dumbbell Romanian Deadlifts (RDLs)",
                 "sets": "3-4", "reps": "10-15"},
                {"name": "Kettlebell Swings (Two-Handed)",
                 "sets": "4", "reps": "15-20"},
                {"name": "Walking Lunges (DBs or KB goblet style)",
                 "sets": "3", "reps": "10-12/leg"},
                {"name": "Single-Leg Kettlebell Deadlifts (or DB)",
                 "sets": "3", "reps": "8-12/leg"},
                {"name": "Glute Bridges (banded or weighted)",
                 "sets": "3", "reps": "15-20"},
                {"name": "Calf Raises (with Dumbbells)",
                 "sets": "3", "reps": "15-25"}
            ]
        },
        {
            "day_type": "Day 3: Upper Body Pull + Chin-up & Core",
            "exercises_list": [
                {"name": "Chin-up/Pull-up Practice (Attempts/Negatives/Band-Assisted)",
                 "sets": "3-5", "reps": "AMRAP/3-5 neg/5-10 asst"},
                {"name": "Ring Rows (or DB Rows/Inverted Rows)",
                 "sets": "3-4", "reps": "8-15"},
                {"name": "Single Arm Dumbbell Rows",
                    "sets": "3", "reps": "10-15/arm"},
                {"name": "Band Pull-Aparts", "sets": "3", "reps": "15-20"},
                {"name": "Dumbbell Bicep Curls", "sets": "3", "reps": "10-15"},
                {"name": "Face Pulls (with Bands)",
                 "sets": "3", "reps": "15-20"},
                {"name": "Core: Hanging Knee Raises (or Leg Raises)",
                 "sets": "3", "reps": "RPE 8-9"},
                {"name": "Core: Russian Twists (DB or KB)",
                 "sets": "3", "reps": "15-20/side"}
            ]
        },
        {
            "day_type": "Day 4: Full Body Strength & Splits Practice",
            "exercises_list": [
                {"name": "Splits Practice (Dynamic & Static holds for front/middle splits)",
                 "sets": "3-5", "reps": "30-60s holds/pos"},
                {"name": "Kettlebell Deadlifts (or DB Deadlifts)",
                 "sets": "1x5 (warm-up), 3x5-8", "reps": "5-8"},
                {"name": "Dumbbell Thrusters (Squat to Overhead Press)",
                 "sets": "3", "reps": "10-15"},
                {"name": "Paralette Shoot-Throughs (or Plank to Pike Jumps)",
                 "sets": "3", "reps": "8-12"},
                {"name": "Kettlebell Farmer's Carry",
                    "sets": "3", "reps": "30-60s walk"},
                {"name": "Band-Resisted Glute Kickbacks",
                    "sets": "3", "reps": "15-20/leg"},
                {"name": "Project Goal Exercise (Client's Choice)",
                 "sets": "2-3", "reps": "Variable"}
            ]
        }
    ]
}


def main(client_full_name: str):
    logging.info(
        f"Starting workout build process for client: {client_full_name}")

    # Hardcoded coach credentials for this script
    coach_username = "Shannonbirch@cocospersonaltraining.com"
    coach_password = "cyywp7nyk2"

    # Use Elena's specific program details
    program_to_build = ELENA_GREEN_WORKOUT_PROGRAM
    # e.g., "Elena Green's 4-Day Home Strength & Skills"
    training_phase_name = program_to_build["program_name"]
    workout_definitions = program_to_build["workout_definitions"]

    if client_full_name.lower() != program_to_build["client_name"].lower():
        logging.warning(
            f"Script called for '{client_full_name}' but using hardcoded program for '{program_to_build['client_name']}'. Ensure this is intended.")

    trainerize_bot = None  # Initialize to ensure it's in scope for finally block
    try:
        trainerize_bot = TrainerizeAutomation()

        if not trainerize_bot.login(coach_username, coach_password):
            logging.error("Login failed. Exiting.")
            return

        trainerize_bot.handle_notification_popup()

        if not trainerize_bot.navigate_to_client(client_full_name):
            logging.error(
                f"Failed to navigate to client: {client_full_name}. Exiting.")
            return

        if not trainerize_bot.navigate_to_training_program():
            logging.error(
                "Failed to navigate to training program tab. Exiting.")
            return

        phase_successfully_selected_or_created = False
        logging.info(
            f"Checking if training phase '{training_phase_name}' already exists and attempting to select it...")

        # Attempt to click/select the phase if it exists.
        # click_program returns True if it finds, clicks the program, and verifies entry.
        if trainerize_bot.click_program(program_week_name=training_phase_name):
            logging.info(
                f"Successfully selected existing training phase '{training_phase_name}'.")
            phase_successfully_selected_or_created = True
        else:
            logging.info(
                f"Training phase '{training_phase_name}' not found or could not be selected. Attempting to create it.")
            # The second argument to create_program in pe.py (chest_exercises) is vestigial for phase creation.
            if trainerize_bot.create_program(program_week_name=training_phase_name, chest_exercises=None):
                logging.info(
                    f"Successfully created new training phase '{training_phase_name}'.")
                phase_successfully_selected_or_created = True
            else:
                logging.error(
                    f"Failed to create new training phase '{training_phase_name}'. Exiting.")
                # No return here, finally block will handle cleanup.

        if not phase_successfully_selected_or_created:
            logging.error(
                f"Could not select or create the training phase '{training_phase_name}'. Exiting.")
            return  # Exit if phase handling failed

        logging.info(
            f"Proceeding to add/update workouts in phase '{training_phase_name}'.")

        # Loop through the workout definitions and create each one
        for i, workout_def in enumerate(workout_definitions):
            workout_name = workout_def["day_type"]
            exercises = workout_def["exercises_list"]

            logging.info(f"Building workout: '{workout_name}'...")

            # Since we've either selected or created the phase, we are now "in" it.
            # The create_workout method will handle clicking "New Workout" within this phase.
            if not trainerize_bot.create_workout(
                program_name=training_phase_name,  # This is the training phase name
                workout_name=workout_name,
                exercises=exercises,
                already_in_program=True  # We are in the context of the phase.
            ):
                logging.error(
                    f"Failed to create workout '{workout_name}'. Attempting to continue with next workout...")
            else:
                logging.info(f"Successfully created workout '{workout_name}'.")

        logging.info(
            "All workouts defined in the program have been processed.")

        logging.info(
            "Now scheduling all activities (workouts, cardio, body stats, photos)...")
        if trainerize_bot.schedule_workouts_and_cardio():
            logging.info("Successfully scheduled workouts and cardio.")
        else:
            logging.warning("Failed to schedule workouts and cardio.")

        if trainerize_bot.schedule_body_stats():
            logging.info("Successfully scheduled body stats.")
        else:
            logging.warning("Failed to schedule body stats.")

        if trainerize_bot.schedule_progress_photos():
            logging.info("Successfully scheduled progress photos.")
        else:
            logging.warning("Failed to schedule progress photos.")

        logging.info(
            f"Workout program build process completed for {client_full_name}.")

    except NotImplementedError:  # Should not happen if class is copied correctly
        logging.error(
            "Script run before TrainerizeAutomation class was fully implemented.")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred in main: {e}", exc_info=True)
    finally:
        if trainerize_bot:
            logging.info("Cleaning up TrainerizeAutomation instance...")
            trainerize_bot.cleanup()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python build_trainerize_workout.py \"Client Full Name\"")
        # Example for Elena, if no arg provided.
        # In a real scenario, always expect the argument.
        logging.warning(
            "No client name provided. Running with default 'Elena Green' for example purposes.")
        client_name_arg = "Elena Green"
        # sys.exit(1) # Uncomment to make client name mandatory
    else:
        client_name_arg = sys.argv[1]

    main(client_name_arg)
