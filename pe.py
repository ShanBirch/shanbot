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


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome...")

        # Updated paths to match the checkin.py script's working paths
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
            # Force the latest version of ChromeDriver
            service = ChromeService()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Chrome initialized successfully!")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

        # Exercise List (moved to class for access within methods)
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
                raise
            time.sleep(2)

            # --- Locate the search input field (UI recently changed) ---
            logging.info("Locating search bar / input field…")

            # Potential search input locators (old + new)
            search_input_locators = [
                # old selector
                (By.CSS_SELECTOR,
                 "input[data-testid='baseGrid-topbar-searchInput']"),
                (By.CSS_SELECTOR, "input[type='search']"),
                (By.XPATH, "//input[contains(@placeholder, 'Search')]"),
            ]

            search_input = None

            # First, try to find the input directly (may already be visible)
            for loc in search_input_locators:
                try:
                    search_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(loc))
                    if search_input:
                        break
                except TimeoutException:
                    continue

            # If not visible, click the search icon/button to reveal it, then retry
            if search_input is None:
                logging.info(
                    "Search input not immediately visible, trying to click search icon…")
                search_icon_locators = [
                    (By.CSS_SELECTOR,
                     "button[data-testid='baseGrid-topbar-searchButton']"),
                    (By.CSS_SELECTOR, "button[aria-label='Search']"),
                    (By.XPATH, "//button[contains(@aria-label, 'Search')]"),
                    (By.CSS_SELECTOR, "svg[name='outline/search']"),
                ]
                for icon_loc in search_icon_locators:
                    try:
                        icon_el = self.driver.find_element(*icon_loc)
                        if icon_el.is_displayed():
                            icon_el.click()
                            time.sleep(0.5)
                            break
                    except Exception:
                        continue

                # Retry finding the input after clicking icon
                for loc in search_input_locators:
                    try:
                        search_input = WebDriverWait(self.driver, 4).until(
                            EC.presence_of_element_located(loc))
                        if search_input:
                            break
                    except TimeoutException:
                        continue

            if search_input is None:
                logging.error(
                    "Search input field not found with any locator – aborting navigate_to_client.")
                return False

            # Clear any existing search term
            try:
                search_input.clear()
            except Exception:
                self.driver.execute_script(
                    "arguments[0].value = ''", search_input)
            time.sleep(1)

            # Get name variations
            name_variations = self.generate_name_variations(client_name)
            client_found = False

            # Try each name variation
            for variation in name_variations:
                logging.info(f"Trying name variation: '{variation}'")

                # Clear and enter search term
                search_input.clear()
                search_input.send_keys(variation)
                time.sleep(2)

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
                    f"//a[contains(., '{variation.split()[0]}')]"
                ]

                for selector in selectors:
                    try:
                        logging.info(f"Trying selector: {selector}")
                        client_link = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector)))

                        # Verify this is the right client before clicking
                        link_text = client_link.text.strip()
                        if any(v.lower() in link_text.lower() for v in name_variations):
                            client_link.click()
                            logging.info(
                                f"Successfully clicked on client link with text: {link_text}")
                            client_found = True
                            break
                    except TimeoutException:
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                        continue

                if client_found:
                    break

            if not client_found:
                logging.error(
                    f"Could not find client with any variation of name: {name_variations}")
                return False

            # Click the Open button
            logging.info(
                "Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(
                EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)

            # Switch to the new tab
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break

            logging.info(
                f"Successfully navigated to client and switched to their profile tab.")
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

    def navigate_to_meal_plan(self):
        """Navigates to the Meal Plan tab from the client profile, with retries and sidebar wait."""
        try:
            logging.info("Navigating to the Meal Plan tab...")
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "nav, .leftNavItem")))
            # Primary locator (old UI)
            meal_plan_link_locator = (
                By.XPATH, "//a[@id='nav_meal_plan' and @data-testid='leftNavMenu-item-mealPlan' and @title='Meal Plan']")

            # Fallback locators for updated UI variations
            meal_plan_fallback_locators = [
                (By.XPATH,
                 "//a[contains(@title, 'Meal') and contains(@href,'meal')]"),
                (By.XPATH,
                 "//a[contains(@title, 'Nutrition') and contains(@href,'nutrition')]"),
                (By.XPATH, "//a[contains(text(), 'Meal Plan')]"),
                (By.XPATH, "//a[contains(text(), 'Nutrition')]"),
                (By.CSS_SELECTOR, "a[data-testid*='mealPlan']"),
                (By.CSS_SELECTOR, "a[data-testid*='nutrition']"),
            ]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Always try to find the Meal Plan tab and click if not active
                    meal_plan_tab = self.driver.find_elements(
                        By.CSS_SELECTOR, "a#nav_meal_plan.leftNavItem")
                    if meal_plan_tab:
                        if 'active' in meal_plan_tab[0].get_attribute('class'):
                            logging.info("Already on the Meal Plan tab.")
                            return True
                        else:
                            logging.info(
                                "Meal Plan tab found but not active. Attempting to click it.")
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", meal_plan_tab[0])
                            time.sleep(0.5)
                            meal_plan_tab[0].click()
                            time.sleep(2)
                            # After click, check if now active
                            if 'active' in meal_plan_tab[0].get_attribute('class'):
                                logging.info(
                                    "Successfully navigated to the Meal Plan tab after click.")
                                return True
                    # Fallback attempt: original locator then broad locators
                    try:
                        meal_plan_link = self.wait.until(
                            EC.element_to_be_clickable(meal_plan_link_locator))
                        meal_plan_link.click()
                    except Exception:
                        # Try each fallback locator until one works
                        for fb_loc in meal_plan_fallback_locators:
                            try:
                                meal_plan_link = self.wait.until(
                                    EC.element_to_be_clickable(fb_loc))
                                meal_plan_link.click()
                                break
                            except Exception:
                                continue
                except Exception as e:
                    logging.warning(
                        f"Attempt {attempt+1} to click Meal Plan tab failed: {e}")
                    time.sleep(2)
            # Debug: print all sidebar link texts
            try:
                sidebar_links = self.driver.find_elements(
                    By.CSS_SELECTOR, "a.leftNavItem")
                logging.error("Meal Plan tab not found. Sidebar links:")
                for link in sidebar_links:
                    logging.error(
                        f"Sidebar link: {link.text} | href: {link.get_attribute('href')}")
            except Exception as e:
                logging.error(f"Error listing sidebar links: {e}")
            return False
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error navigating to the Meal Plan tab: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
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

                return False

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
                return text, 95

            # Use fuzzy matching
            if self.fuzzy_match(target_text, text, threshold):
                # Calculate a rough score based on length difference and common characters
                target_clean = ''.join(
                    c for c in target_text.lower() if c.isalnum())
                text_clean = ''.join(c for c in text.lower() if c.isalnum())
                common_chars = sum(1 for a, b in zip(
                    target_clean, text_clean) if a == b)
                max_length = max(len(target_clean), len(text_clean))
                score = (common_chars / max_length) * \
                    100 if max_length > 0 else 0

                if score > best_score:
                    best_score = score
                    best_match = text

        return best_match, best_score

    def click_program(self, program_week_name):
        """Clicks on a program link with improved fuzzy matching and extra logging."""
        try:
            logging.info(f"Clicking on program: '{program_week_name}'...")

            # First, gather all visible program names
            program_elements = self.driver.find_elements(
                By.XPATH, "//p[contains(@class, 'color--black')]")
            program_names = [
                elem.text for elem in program_elements if elem.text.strip()]
            logging.info(f"[PROGRAMS] Found program names: {program_names}")

            # Find the closest match
            matched_program, score = self.find_closest_match(
                program_week_name, program_names)

            if matched_program:
                logging.info(
                    f"Found matching program: '{matched_program}' (similarity: {score}%)")

                # Create a simpler selector that avoids special characters
                safe_program_name = matched_program.replace("'", "")
                selectors = [
                    f"//a[contains(@class, 'section-link')]//p[contains(., '{safe_program_name}')]",
                    f"//div[contains(@class, 'flex-left')]//p[contains(., '{safe_program_name}')]",
                    f"//p[contains(., '{safe_program_name}')]"
                ]

                for selector in selectors:
                    try:
                        logging.info(f"Trying selector: {selector}")
                        program_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector)))
                        self.driver.execute_script(
                            "arguments[0].click();", program_link)
                        logging.info(
                            f"Successfully clicked on program using selector: {selector}")
                        time.sleep(2)
                        return True
                    except TimeoutException:
                        logging.info(
                            f"Selector {selector} failed, trying next...")
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                        continue

                # If all selectors fail, log page source and take screenshot
                logging.error(
                    f"Could not find program '{program_week_name}' with any selector. Saving page source and screenshot for debugging.")
                debug_dir = os.path.join(os.getcwd(), 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                page_source_path = os.path.join(
                    debug_dir, 'program_not_found.html')
                screenshot_path = os.path.join(
                    debug_dir, 'program_not_found.png')
                with open(page_source_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Saved page source to {page_source_path} and screenshot to {screenshot_path}")
                return False

            else:
                logging.warning(
                    f"Could not find program '{program_week_name}' in the list")
                return False

        except Exception as e:
            logging.error(f"Error clicking program '{program_week_name}': {e}")
            return False

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

    def create_program(self, program_week_name, chest_exercises=None):
        logging.info(
            f"=== ENTERED create_program with program_week_name: {program_week_name} ===")
        try:
            logging.info(
                f"[DEBUG] Arguments: program_week_name={program_week_name}, chest_exercises={chest_exercises}")
            logging.info(
                f"[DEBUG] Current URL before program creation: {self.driver.current_url}")
            logging.info(
                f"[DEBUG] Page title before program creation: {self.driver.title}")

            # Wait for and click '+ Add next' button
            selectors = [
                "p.tz-p.color--blue.clickable",
                "p.color--blue.clickable",
                "p.tz-p.clickable",
                "//p[contains(@class, 'color--blue') and contains(@class, 'clickable')]",
                "//p[contains(text(), '+ Add next')]",
                "//p[text()='+ Add next']",
                "//p[contains(text(), '+') and contains(text(), 'Add') and contains(text(), 'next')]",
                "//a[contains(@class, 'color--blue') and contains(@class, 'clickable')]",
                "//a[contains(text(), '+ Add next')]",
                "//span[contains(text(), '+ Add next')]",
                "//div[contains(@class, 'clickable')]/p[contains(@class, 'color--blue')]"
            ]
            add_next_button = None
            for selector in selectors:
                try:
                    logging.info(
                        f"[DEBUG] Trying to find '+ Add next' button with selector: {selector}")
                    if selector.startswith("//"):
                        add_next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        add_next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, selector))
                        )
                    logging.info(
                        f"[DEBUG] Found '+ Add next' button with selector: {selector}")
                    break
                except Exception as e:
                    logging.info(
                        f"[DEBUG] Selector {selector} failed: {str(e)}")
                    continue
            if not add_next_button:
                logging.error(
                    "Could not find '+ Add next' button with any selector")
                self.driver.save_screenshot(
                    "create_program_button_not_found.png")
                return False
            # Click the '+ Add next' button
            try:
                add_next_button.click()
            except Exception as e:
                logging.warning(
                    f"[DEBUG] Normal click failed: {str(e)}, trying JavaScript click")
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", add_next_button)
                except Exception as js_e:
                    logging.error(
                        f"[DEBUG] JavaScript click also failed: {str(js_e)}")
                    self.driver.save_screenshot(
                        "create_program_click_failed.png")
                    return False
            time.sleep(1)
            self.driver.save_screenshot("after_add_next_click.png")

            # Wait for the Add Next Training Phase modal
            try:
                logging.info(
                    "[DEBUG] Waiting for Add Next Training Phase modal...")
                name_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[data-testid='editTrainingPhase-nameInput']"))
                )
                duration_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[data-testid='editTrainingPhase-durationInput']"))
                )
                save_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"))
                )
                self.driver.save_screenshot("modal_training_phase_open.png")
                # Fill in the name
                name_input.clear()
                name_input.send_keys(program_week_name)
                logging.info(
                    f"[DEBUG] Entered program name: {program_week_name}")
                # Set duration to 6
                duration_input.clear()
                duration_input.send_keys("6")
                logging.info("[DEBUG] Set duration to 6 weeks")
                self.driver.save_screenshot("modal_training_phase_filled.png")
                # Click Save
                save_button.click()
                logging.info("[DEBUG] Clicked Save on training phase modal")
                time.sleep(2)
            except Exception as e:
                logging.error(
                    f"[DEBUG] Failed to fill or save training phase modal: {str(e)}")
                self.driver.save_screenshot("modal_training_phase_error.png")
                return False

            # Wait for modal to close and for the 'New' button to appear
            try:
                logging.info(
                    "[DEBUG] Waiting for 'New' button to create first workout...")
                new_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[title='Create new workout']"))
                )
                self.driver.save_screenshot("before_new_workout_click.png")
                new_button.click()
                logging.info(
                    "[DEBUG] Clicked 'New' button to start building workout")
                time.sleep(2)
            except Exception as e:
                logging.error(
                    f"[DEBUG] Failed to find or click 'New' button: {str(e)}")
                self.driver.save_screenshot("new_button_error.png")
                return False

            # At this point, the workout builder should be open
            logging.info("[DEBUG] Ready to build workouts!")
            return True
        except Exception as e:
            logging.error(f"Exception in create_program: {str(e)}")
            self.driver.save_screenshot("create_program_exception.png")
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

            # Click New workout button with retry and scroll
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to find the New button
                    new_button = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[title='Create new workout']")))

                    # Scroll the button into view
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", new_button)
                    time.sleep(1)  # Wait for scroll to complete

                    # Try to click with JavaScript
                    try:
                        self.driver.execute_script(
                            "arguments[0].click();", new_button)
                        logging.info(
                            "Clicked 'New' workout button with JavaScript.")
                        time.sleep(2)
                        break
                    except Exception as js_error:
                        logging.warning(f"JavaScript click failed: {js_error}")
                        # Try regular click
                        try:
                            new_button.click()
                            logging.info(
                                "Clicked 'New' workout button with regular click.")
                            time.sleep(2)
                            break
                        except Exception as click_error:
                            logging.warning(
                                f"Regular click failed on attempt {attempt + 1}: {click_error}")
                            if attempt == max_retries - 1:
                                raise
                            time.sleep(2)  # Wait before retry
                            continue
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(
                            f"Error clicking 'New' workout button after {max_retries} attempts: {e}")
                        return False
                    time.sleep(2)  # Wait before retry
                    continue

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

    def create_workout_back_day(self, program_week_name, exercises_list, already_in_program=False):
        """Creates a workout named 'Back Day' and adds exercises."""
        return self.create_workout(program_week_name, "Back Day", exercises_list, already_in_program=already_in_program)

    def create_workout_chest_day(self, program_week_name, exercises_list, already_in_program=False):
        """Creates a workout named 'Chest Day' and adds exercises."""
        return self.create_workout(program_week_name, "Chest Day", exercises_list, already_in_program=already_in_program)

    def create_workout_shoulder_day(self, program_week_name, exercises_list, already_in_program=False):
        """Creates a workout named 'Shoulder Day' and adds exercises."""
        return self.create_workout(program_week_name, "Shoulder Day", exercises_list, already_in_program=already_in_program)

    def create_workout_leg_day(self, program_week_name, exercises_list, already_in_program=False):
        """Creates a workout named 'Leg Day' and adds exercises."""
        return self.create_workout(program_week_name, "Leg Day", exercises_list, already_in_program=already_in_program)

    def create_workout_core_day(self, program_week_name, exercises_list, already_in_program=False):
        """Creates a workout named 'Core Day' and adds exercises."""
        return self.create_workout(program_week_name, "Core Day", exercises_list, already_in_program=already_in_program)

    def add_new_client(self, email, first_name, last_name, messaging_type="Full Access 1-way messaging"):
        """Automates adding a new client after logging in."""
        try:
            logging.info("Navigating to Clients tab to add a new client...")
            # Click Clients link in sidebar
            clients_link = self.wait.until(
                EC.element_to_be_clickable((By.ID, "nav_clients")))
            clients_link.click()
            time.sleep(2)

            # Click New button
            new_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "clientGrid__toolbar_addClient")))
            new_button.click()
            time.sleep(1)

            # Fill in email
            email_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='addClientDialog-emailInput']")))
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(0.5)

            # Fill in first name
            first_name_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='addClientDialog-firstNameInput']")))
            first_name_input.clear()
            first_name_input.send_keys(first_name)
            time.sleep(0.5)

            # Fill in last name
            last_name_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='addClientDialog-lastNameInput']")))
            last_name_input.clear()
            last_name_input.send_keys(last_name)
            time.sleep(0.5)

            # Click the messaging type dropdown
            dropdown = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-select-selection__rendered")))
            dropdown.click()
            time.sleep(0.5)

            # Select the desired messaging type
            options = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-select-dropdown-menu-item")))
            found = False
            for option in options:
                if messaging_type.lower() in option.text.lower():
                    option.click()
                    found = True
                    break
            if not found:
                logging.warning(
                    f"Could not find messaging type '{messaging_type}', using default.")
                options[0].click()
            time.sleep(0.5)

            # Click Add and Send Invite button
            add_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']")))
            add_button.click()
            logging.info(
                f"Client '{first_name} {last_name}' with email '{email}' added and invite sent.")
            time.sleep(2)

            # Flag to detect if we successfully opened the client profile tab
            clicked_open = False

            # Click the OPEN CLIENT ACCOUNT button as the final step
            try:
                # Wait up to 15 seconds for the button to appear
                open_account_button = None
                selectors = [
                    # Original SVG-based selector
                    (By.XPATH,
                     "//button[.//span[.//svg[@name='outline/open'] and contains(., 'OPEN CLIENT ACCOUNT')]]"),
                    # Original text-based selector
                    (By.XPATH,
                     "//button[.//span[contains(text(), 'OPEN CLIENT ACCOUNT')]]"),
                    # New variant: button containing exact text (case-insensitive)
                    (By.XPATH, "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'OPEN CLIENT ACCOUNT')]"),
                    # Fallback: any clickable element with 'Open Client Account' text
                    (By.XPATH, "//*[self::button or self::a][contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'OPEN CLIENT ACCOUNT')]"),
                    # Very generic fallback: first 'Open' button after adding client
                    (By.XPATH, "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'OPEN')]")
                ]
                for by, selector in selectors:
                    try:
                        open_account_button = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((by, selector)))
                        if open_account_button:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", open_account_button)
                            time.sleep(0.5)
                            open_account_button.click()
                            logging.info(
                                "Clicked 'OPEN CLIENT ACCOUNT' button.")
                            clicked_open = True
                            time.sleep(3)
                            # Switch to the new tab
                            original_window = self.driver.current_window_handle
                            self.wait.until(EC.number_of_windows_to_be(2))
                            for window_handle in self.driver.window_handles:
                                if window_handle != original_window:
                                    self.driver.switch_to.window(window_handle)
                                    logging.info(
                                        "Switched to the new client tab.")
                                    break
                            break
                    except Exception as e:
                        logging.debug(
                            f"Selector failed for 'OPEN CLIENT ACCOUNT': {selector} | {e}")
                else:
                    logging.warning(
                        "Could not find 'OPEN CLIENT ACCOUNT' button with any selector.")
                # Refresh the page after opening client account (optional, can be removed if not needed)
                self.driver.refresh()
                logging.info(
                    "Refreshed the page after opening client account.")
                time.sleep(3)
            except Exception as e:
                logging.warning(
                    f"Could not click 'OPEN CLIENT ACCOUNT' button: {e}")

            return clicked_open
        except Exception as e:
            logging.error(f"Error adding new client: {e}")
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

    def click_attach_meal_plan_pdf(self, pdf_path=None):
        """Clicks the 'Attach a meal plan PDF' section, then uploads the PDF if a path is provided (no 'LET'S START' click)."""
        try:
            logging.info("Clicking 'Attach a meal plan PDF' section...")
            attach_pdf_xpath = "//div[contains(@class, 'flex-between') and .//p[contains(text(), 'Attach a meal plan PDF')]]"
            attach_pdf_div = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, attach_pdf_xpath)))
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", attach_pdf_div)
            time.sleep(0.5)
            attach_pdf_div.click()
            logging.info("Clicked 'Attach a meal plan PDF' section.")
            time.sleep(1)
            # If a PDF path is provided, upload the file
            if pdf_path:
                try:
                    file_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
                    file_input.send_keys(pdf_path)
                    logging.info(f"Uploaded meal plan PDF: {pdf_path}")
                    time.sleep(2)
                except Exception as e:
                    logging.error(f"Error uploading meal plan PDF: {e}")
                    return False
            return True
        except Exception as e:
            logging.error(
                f"Error clicking 'Attach a meal plan PDF' section: {e}")
            return False

    def upload_meal_plan_pdf(self, pdf_path):
        """Uploads a meal plan PDF after clicking the attach section."""
        try:
            logging.info(f"Uploading meal plan PDF: {pdf_path}")
            # Wait for the file input to appear
            file_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            file_input.send_keys(pdf_path)
            logging.info("Meal plan PDF sent to file input.")
            time.sleep(2)  # Wait for upload to process
            return True
        except Exception as e:
            logging.error(f"Error uploading meal plan PDF: {e}")
            return False

    def confirm_meal_plan_upload(self):
        """Clicks the Confirm button after uploading the meal plan PDF."""
        try:
            logging.info("Clicking Confirm button for meal plan upload...")
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']")))
            confirm_button.click()
            logging.info("Clicked Confirm button.")
            time.sleep(2)
            return True
        except Exception as e:
            logging.error(f"Error clicking Confirm button: {e}")
            return False

    def schedule_workouts_and_cardio(self):
        import traceback
        try:
            logging.info("Starting to schedule workouts and cardio...")
            workout_schedule = [
                ("Chest Day", "Monday"),
                ("Back Day", "Tuesday"),
                ("Shoulder Day", "Wednesday"),
                ("Leg Day", "Thursday"),
                ("Core Day", "Friday"),
            ]
            cardio_days = ["Monday", "Wednesday", "Friday", "Sunday"]
            cardio_activity = "Walking"
            repeat_weeks = "6"

            def click_sidebar_tab_calendar():
                try:
                    calendar_tab = None
                    try:
                        calendar_tab = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#nav_calendar[data-testid='leftNavMenu-item-calendar']")))
                    except Exception:
                        calendar_tab = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[.//svg[@name='outline/calendar/calendar-regular']]")))
                    if calendar_tab:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", calendar_tab)
                        time.sleep(0.5)
                        try:
                            calendar_tab.click()
                        except Exception:
                            self.driver.execute_script(
                                "arguments[0].click();", calendar_tab)
                        time.sleep(1)
                        logging.info("Clicked Calendar tab in sidebar.")
                        return True
                    else:
                        logging.error("Calendar tab not found in sidebar.")
                        return False
                except Exception as e:
                    logging.error(f"Could not click sidebar tab Calendar: {e}")
                    return False
            click_sidebar_tab_calendar()
            for workout_name, day_title in workout_schedule:
                try:
                    logging.info(
                        f"Scheduling workout: {workout_name} on {day_title}")
                    schedule_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                    )))
                    schedule_btn.click()
                    time.sleep(1)
                    workout_menu = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//li[@data-testid='dropdownButton-menuItem-workout']"
                    )))
                    workout_menu.click()
                    time.sleep(1)
                    select_current_program = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//p[contains(@class, 'color--black') and text()='Select from current training program']"
                    )))
                    select_current_program.click()
                    time.sleep(0.5)
                    try:
                        logging.info(
                            "[STEP] Waiting for workout input to be clickable...")
                        try:
                            workout_input = self.wait.until(EC.element_to_be_clickable((
                                By.XPATH, "//div[contains(@class, 'ant-select-selection__placeholder') and contains(text(), 'Type in workout name')]"
                            )))
                            logging.info(
                                "[SUCCESS] Workout input is clickable.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Workout input not clickable: {e}")
                            self.driver.save_screenshot(
                                'fail_workout_input_clickable.png')
                            with open('fail_workout_input_clickable.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        logging.info("[STEP] Clicking workout input...")
                        try:
                            workout_input.click()
                            logging.info("[SUCCESS] Clicked workout input.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Could not click workout input: {e}")
                            self.driver.save_screenshot(
                                'fail_workout_input_click.png')
                            with open('fail_workout_input_click.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        logging.info(
                            "[STEP] Waiting for input box to be present (ant-select-search__field)...")
                        try:
                            input_box = self.wait.until(EC.presence_of_element_located((
                                By.XPATH, "//input[contains(@class, 'ant-select-search__field')]"
                            )))
                            logging.info(
                                "[SUCCESS] Input box (ant-select-search__field) is present.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Input box (ant-select-search__field) not present: {e}")
                            self.driver.save_screenshot(
                                'fail_input_box_present.png')
                            with open('fail_input_box_present.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        # Try normal send_keys
                        logging.info(
                            f"[STEP] Trying input_box.send_keys({workout_name})...")
                        try:
                            input_box.clear()
                            input_box.send_keys(workout_name)
                            time.sleep(0.5)
                            value_after_typing = input_box.get_attribute(
                                'value')
                            logging.info(
                                f"[RESULT] Input box value after send_keys: '{value_after_typing}'")
                        except Exception as e:
                            logging.error(f"[FAIL] send_keys failed: {e}")
                        if value_after_typing.strip().lower() != workout_name.strip().lower():
                            # Try JavaScript set value
                            logging.info(
                                "[STEP] Trying JavaScript value set...")
                            try:
                                self.driver.execute_script(
                                    "arguments[0].value = arguments[1];", input_box, workout_name)
                                time.sleep(0.5)
                                value_after_js = input_box.get_attribute(
                                    'value')
                                logging.info(
                                    f"[RESULT] Input box value after JS set: '{value_after_js}'")
                            except Exception as e:
                                logging.error(
                                    f"[FAIL] JS set value failed: {e}")
                            if value_after_js.strip().lower() != workout_name.strip().lower():
                                # Try click+send_keys again
                                logging.info(
                                    "[STEP] Trying click+send_keys again...")
                                try:
                                    input_box.click()
                                    input_box.send_keys(workout_name)
                                    time.sleep(0.5)
                                    value_after_click = input_box.get_attribute(
                                        'value')
                                    logging.info(
                                        f"[RESULT] Input box value after click+send_keys: '{value_after_click}'")
                                except Exception as e:
                                    logging.error(
                                        f"[FAIL] click+send_keys failed: {e}")
                                if value_after_click.strip().lower() != workout_name.strip().lower():
                                    # Try character by character
                                    logging.info(
                                        "[STEP] Trying character-by-character typing...")
                                    try:
                                        input_box.clear()
                                        for char in workout_name:
                                            input_box.send_keys(char)
                                            time.sleep(0.1)
                                        value_after_chars = input_box.get_attribute(
                                            'value')
                                        logging.info(
                                            f"[RESULT] Input box value after char-by-char: '{value_after_chars}'")
                                    except Exception as e:
                                        logging.error(
                                            f"[FAIL] char-by-char typing failed: {e}")
                                    if value_after_chars.strip().lower() != workout_name.strip().lower():
                                        logging.info(
                                            "[STEP] All typing methods failed, trying to click workout name in dropdown...")
                                        try:
                                            workout_options = self.driver.find_elements(
                                                By.XPATH, "//p[contains(@class, 'tz-lp') and contains(@data-testid, 'workoutGrid-workoutName')]")
                                            logging.info(
                                                f"[RESULT] Found {len(workout_options)} workout options in dropdown.")
                                            for idx, opt in enumerate(workout_options):
                                                logging.info(
                                                    f"[RESULT] Option {idx}: '{opt.text}' (data-testid: {opt.get_attribute('data-testid')})")
                                            workout_option = self.wait.until(EC.element_to_be_clickable((
                                                By.XPATH, f"//p[contains(@class, 'tz-lp') and contains(text(), '{workout_name}')]")
                                            ))
                                            workout_option.click()
                                            logging.info(
                                                f"[SUCCESS] Clicked workout option '{workout_name}' in dropdown.")
                                        except Exception as click_e:
                                            logging.error(
                                                f"[FAIL] Failed to click workout option '{workout_name}': {click_e}")
                                            try:
                                                dropdown_html = self.driver.find_element(
                                                    By.XPATH, "//div[contains(@class, 'ant-select-dropdown')]//div").get_attribute('outerHTML')
                                                logging.error(
                                                    f"[FAIL] Dropdown HTML: {dropdown_html}")
                                            except Exception as html_e:
                                                logging.error(
                                                    f"[FAIL] Could not get dropdown HTML: {html_e}")
                                            self.driver.save_screenshot(
                                                'fail_dropdown_click.png')
                                            with open('fail_dropdown_click.html', 'w', encoding='utf-8') as f:
                                                f.write(
                                                    self.driver.page_source)
                                            raise Exception(
                                                "All typing and clicking methods failed!")
                        try:
                            input_box.send_keys(Keys.ENTER)
                            logging.info(
                                "[STEP] Pressed Enter after typing workout name.")
                            time.sleep(1)
                        except Exception as e:
                            logging.error(f"[FAIL] Pressing Enter failed: {e}")
                    except Exception as e:
                        logging.error(
                            f"[FAIL] Failed to type in workout name: {e}")
                        self.driver.save_screenshot('workout_input_error.png')
                        with open('workout_input_error.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        raise
                    add_activity = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//h2[contains(text(), 'Add Activity')]"
                    )))
                    add_activity.click()
                    time.sleep(1)
                    repeat_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
                    )))
                    repeat_btn.click()
                    time.sleep(1)
                    day_btn = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{day_title}']"
                    )))
                    day_btn.click()
                    time.sleep(0.5)
                    repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
                    )))
                    repeat_dropdown.click()
                    week_option = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-{repeat_weeks}']"
                    )))
                    week_option.click()
                    time.sleep(0.5)
                    apply_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
                    )))
                    apply_btn.click()
                    time.sleep(1)
                    add_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
                    )))
                    add_btn.click()
                    time.sleep(2)
                except Exception as e:
                    logging.error(
                        f"Error scheduling workout {workout_name}: {e}\n{traceback.format_exc()}")
            # Only schedule cardio once, with all repeat days selected
            repeat_days = ["Monday", "Tuesday", "Wednesday",
                           "Thursday", "Friday", "Saturday", "Sunday"]
            logging.info(
                f"Scheduling cardio: {cardio_activity} on {', '.join(repeat_days)}")
            logging.info(
                "[CARDIO] Checking for modal overlays before clicking schedule button...")
            # Try to close modal overlays if present
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[CARDIO] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[CARDIO] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[CARDIO] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[CARDIO] No modal overlay detected.")
            logging.info("[CARDIO] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for cardio menu...")
            cardio_menu = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[.//p[text()='Cardio']]"
            )))
            cardio_menu.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for activity dropdown...")
            activity_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div.ant-select-selection__rendered"
            )))
            activity_dropdown.click()
            logging.info("[CARDIO] Waiting for walking option...")
            walking_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[contains(@data-testid, 'activity-cardio-activitySelectOption-walking')]"
            )))
            walking_option.click()
            time.sleep(0.5)
            # Skip time selection, go straight to custom target
            logging.info("[CARDIO] Clicking <span>Add my own target</span>...")
            add_own_target_span = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//span[text()='Add my own target']"
            )))
            add_own_target_span.click()
            logging.info("[CARDIO] Clicked <span>Add my own target</span>.")
            target_input = self.wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "input[data-testid='multipleActivitiesDialog-activity-cardio-target-textInput']"
            )))
            target_input.clear()
            target_input.send_keys("10,000 Steps")
            logging.info(
                "[CARDIO] Typed '10,000 Steps' into custom target input.")
            time.sleep(0.5)
            logging.info("[CARDIO] Waiting for add activity header...")
            add_activity = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//h2[contains(text(), 'Add Activity')]"
            )))
            add_activity.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            for repeat_day in repeat_days:
                try:
                    logging.info(
                        f"[CARDIO] Selecting repeat day: {repeat_day}")
                    day_btn = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{repeat_day}']"
                    )))
                    day_btn.click()
                except Exception as e:
                    logging.error(
                        f"[CARDIO][FAIL] Could not select repeat day {repeat_day}: {e}")
            time.sleep(0.5)
            # Set repeat weeks to 6
            logging.info("[CARDIO] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[CARDIO] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[CARDIO] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            # Ensure Apply and Add are clicked
            logging.info("[CARDIO] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[CARDIO] Clicked apply button.")
            time.sleep(1)
            logging.info("[CARDIO] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[CARDIO] Clicked add button.")
            time.sleep(2)
            logging.info("Finished scheduling workouts and cardio.")
            time.sleep(30)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_workouts_and_cardio: {e}\n{traceback.format_exc()}")
            return False

    def schedule_body_stats(self):
        import traceback
        try:
            logging.info(
                "Scheduling Body stats on Monday, repeat for 6 weeks.")
            logging.info(
                "[BODY STATS] Checking for modal overlays before clicking schedule button...")
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[BODY STATS] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[BODY STATS] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[BODY STATS] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[BODY STATS] No modal overlay detected.")
            logging.info("[BODY STATS] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            # Click <p class="tz-p">Body stats</p>
            logging.info("[BODY STATS] Clicking Body stats <p> element...")
            body_stats_p = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//p[contains(@class, 'tz-p') and text()='Body stats']"
            )))
            body_stats_p.click()
            logging.info("[BODY STATS] Clicked Body stats <p> element.")
            time.sleep(0.5)
            # Set up repeat
            logging.info("[BODY STATS] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            logging.info("[BODY STATS] Selecting repeat day: Monday")
            day_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@data-testid and @title='Monday']"
            )))
            day_btn.click()
            time.sleep(0.5)
            logging.info("[BODY STATS] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[BODY STATS] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[BODY STATS] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            logging.info("[BODY STATS] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[BODY STATS] Clicked apply button.")
            time.sleep(1)
            logging.info("[BODY STATS] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[BODY STATS] Clicked add button.")
            time.sleep(15)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_body_stats: {e}\n{traceback.format_exc()}")
            return False

    def schedule_progress_photos(self):
        import traceback
        try:
            logging.info(
                "Scheduling Progress Photos on Monday, repeat for 6 weeks.")
            logging.info(
                "[PHOTOS] Checking for modal overlays before clicking schedule button...")
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[PHOTOS] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[PHOTOS] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[PHOTOS] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[PHOTOS] No modal overlay detected.")
            logging.info("[PHOTOS] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            # Click <p class="tz-p">Photos</p>
            logging.info("[PHOTOS] Clicking Photos <p> element...")
            photos_p = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//p[contains(@class, 'tz-p') and text()='Photos']"
            )))
            photos_p.click()
            logging.info("[PHOTOS] Clicked Photos <p> element.")
            time.sleep(0.5)
            # Set up repeat
            logging.info("[PHOTOS] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            logging.info("[PHOTOS] Selecting repeat day: Monday")
            day_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@data-testid and @title='Monday']"
            )))
            day_btn.click()
            time.sleep(0.5)
            logging.info("[PHOTOS] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[PHOTOS] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[PHOTOS] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            logging.info("[PHOTOS] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[PHOTOS] Clicked apply button.")
            time.sleep(1)
            logging.info("[PHOTOS] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[PHOTOS] Clicked add button.")
            time.sleep(15)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_progress_photos: {e}\n{traceback.format_exc()}")
            return False


def load_workout_program_from_analytics(ig_username):
    analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
    import json
    try:
        with open(analytics_file_path, "r") as f:
            analytics_data = json.load(f)
        for uid, user_data in analytics_data.get("conversations", {}).items():
            metrics = user_data.get("metrics", {})
            if metrics.get("ig_username", "").lower() == ig_username.lower():
                return metrics.get("workout_program")
    except Exception as e:
        print(f"Error loading workout program: {e}")
    return None


if __name__ == '__main__':
    import sys
    import json
    # Added for more robust error handling
    import traceback

    # Initialize success flags
    client_added_successfully = False
    meal_plan_uploaded_successfully = False
    workout_program_built_successfully = False

    # If arguments are provided, use them; otherwise, run the demo/test code
    if len(sys.argv) >= 3:
        try:
            client_data = json.loads(sys.argv[1])
            meal_plan_pdf_path = sys.argv[2]
            # Print and log all received arguments and client_data
            print("\n=== pe.py STARTUP: ARGUMENTS RECEIVED ===")
            print(
                f"sys.argv[1] (client_data): {sys.argv[1][:500]}{'...' if len(sys.argv[1]) > 500 else ''}")
            print(f"sys.argv[2] (meal_plan_pdf_path): {meal_plan_pdf_path}")
            print("\n=== Parsed client_data (pretty-printed) ===")
            import pprint
            pprint.pprint(client_data)
            print("=== END ARGUMENTS ===\n")
            logging.info(
                f"pe.py received client_data: {json.dumps(client_data, indent=2)[:1000]}{'...' if len(json.dumps(client_data)) > 1000 else ''}")
            logging.info(
                f"pe.py received meal_plan_pdf_path: {meal_plan_pdf_path}")
            # Extract info from client_data
            username = client_data.get(
                "coach_email", "Shannonbirch@cocospersonaltraining.com")
            password = client_data.get("coach_password", "cyywp7nyk2")

            # --- Start: Enhanced Name and Email Extraction ---
            email = client_data.get("email", "")
            first_name = client_data.get("first_name", "")
            last_name = client_data.get("last_name", "")

            # Fallback to personal_info if primary fields are empty
            if (not email or not first_name or not last_name) and "personal_info" in client_data:
                personal_info = client_data["personal_info"]
                if not email and "email" in personal_info:
                    email = personal_info["email"].get("value", "")

                # Prioritize explicit first_name, last_name from personal_info
                if not first_name and "first_name" in personal_info:
                    first_name = personal_info["first_name"].get("value", "")
                if not last_name and "last_name" in personal_info:
                    last_name = personal_info["last_name"].get("value", "")

                # Fallback to parsing full_name if first_name/last_name still empty
                if (not first_name or not last_name) and "full_name" in personal_info:
                    full_name_from_info = personal_info["full_name"].get(
                        "value", "")
                    if full_name_from_info:
                        parts = full_name_from_info.split(
                            ' ', 1)  # Split on first space
                        if not first_name and len(parts) > 0:
                            first_name = parts[0]
                        if not last_name and len(parts) > 1:
                            last_name = parts[1]

            # Ensure ig_username has a value, prioritize explicit ig_username then email, then a fallback
            ig_username = client_data.get(
                "ig_username", "") or email or f"{first_name}_{last_name}".strip("_") or "unknown_user"
            # --- End: Enhanced Name and Email Extraction ---

            program_name = client_data.get("program_name", "Program")
            training_days = client_data.get("training_days", "")

            # --- MODIFIED WORKOUT PROGRAM SOURCING ---
            workout_program = None
            # 1. Try to get workout_program from client_data (passed via command line)
            if (isinstance(client_data.get("workout_program"), dict) and
                    client_data["workout_program"].get("workout_definitions")):
                workout_program = client_data["workout_program"]
                logging.info(
                    "Using workout_program directly from client_data (command line).")

            # 2. If not found in client_data, try loading from analytics
            if not workout_program:
                logging.info(
                    "Workout_program not found in client_data, attempting to load from analytics...")
                workout_program = load_workout_program_from_analytics(
                    ig_username)
                if workout_program:
                    logging.info(
                        "Successfully loaded workout_program from analytics.")
            # --- END MODIFIED WORKOUT PROGRAM SOURCING ---

            if not (isinstance(workout_program, dict) and "workout_definitions" in workout_program and workout_program["workout_definitions"]):
                logging.warning(
                    "No valid workout_program found from client_data or analytics. Using default fallback workout program.")
                workout_program = {
                    "workout_definitions": [
                        {"day_type": "chest", "exercises_list": [
                            {"name": "Barbell Bench Press",
                                "sets": "3", "reps": "10"},
                            {"name": "Incline Dumbbell Press",
                                "sets": "3", "reps": "10"}
                        ]},
                        {"day_type": "back", "exercises_list": [
                            {"name": "Pull Ups", "sets": "3", "reps": "8"},
                            {"name": "Seated Row", "sets": "3", "reps": "12"}
                        ]},
                        {"day_type": "shoulders", "exercises_list": [
                            {"name": "Shoulder Press", "sets": "3", "reps": "10"},
                            {"name": "Lateral Raise", "sets": "3", "reps": "12"}
                        ]},
                        {"day_type": "legs", "exercises_list": [
                            {"name": "Squats", "sets": "4", "reps": "8"},
                            {"name": "Leg Curl", "sets": "3", "reps": "12"}
                        ]},
                        {"day_type": "core", "exercises_list": [
                            {"name": "Plank", "sets": "3", "reps": "30"},
                            {"name": "Cable Crunch", "sets": "3", "reps": "15"}
                        ]}
                    ]
                }
            logging.info(
                f"Final workout_program to be used: {workout_program}")
            # Print the full workout program to the terminal for visibility
            print("\n=== WORKOUT PROGRAM TO BE BUILT ===")
            import pprint
            pprint.pprint(workout_program.get(
                "workout_definitions", workout_program))
            print("=== END WORKOUT PROGRAM ===\n")
            # Fallbacks for exercises
            chest_exercises = []
            back_exercises = []
            shoulder_exercises = []
            leg_exercises = []
            core_exercises = []
            if isinstance(workout_program, dict) and "workout_definitions" in workout_program:
                for defn in workout_program["workout_definitions"]:
                    day_type = defn.get("day_type", "").lower()
                    exercises = defn.get("exercises_list", [])
                    if day_type == "chest":
                        chest_exercises = exercises
                    elif day_type == "back":
                        back_exercises = exercises
                    elif day_type == "shoulders":
                        shoulder_exercises = exercises
                    elif day_type == "legs":
                        leg_exercises = exercises
                    elif day_type == "core":
                        core_exercises = exercises
                    elif day_type == "arms":
                        pass
                    elif day_type == "full_body":
                        chest_exercises = exercises
            logging.info(f"chest_exercises: {chest_exercises}")
            logging.info(f"back_exercises: {back_exercises}")
            logging.info(f"shoulder_exercises: {shoulder_exercises}")
            logging.info(f"leg_exercises: {leg_exercises}")
            logging.info(f"core_exercises: {core_exercises}")
            trainerize_bot = TrainerizeAutomation()
            try:
                if trainerize_bot.login(username, password):
                    trainerize_bot.handle_notification_popup()
                    # Attempt to add new client (returns True only if profile tab opened)
                    profile_opened = trainerize_bot.add_new_client(
                        email, first_name, last_name)
                    if profile_opened:
                        client_added_successfully = True
                        print(
                            f"Successfully added/opened client: {first_name} {last_name} ({email})")
                    else:
                        logging.info(
                            "Add-new-client flow did not open profile – attempting to locate existing client via search…")
                        if trainerize_bot.navigate_to_client(f"{first_name} {last_name}"):
                            trainerize_bot.handle_notification_popup()
                            profile_opened = True
                        else:
                            logging.error(
                                "Could not locate existing client via search.")

                    if profile_opened:
                        # Upload meal plan PDF
                        if not trainerize_bot.navigate_to_meal_plan():
                            logging.info(
                                "Initial Meal Plan tab nav failed – trying to open client profile then retry…")
                            if trainerize_bot.navigate_to_client(f"{first_name} {last_name}"):
                                trainerize_bot.handle_notification_popup()
                                time.sleep(1)
                                trainerize_bot.navigate_to_meal_plan()

                        if trainerize_bot.navigate_to_meal_plan():
                            if trainerize_bot.click_attach_meal_plan_pdf(meal_plan_pdf_path):
                                if trainerize_bot.confirm_meal_plan_upload():
                                    meal_plan_uploaded_successfully = True
                                    print(
                                        "Meal plan uploaded and confirmed.")
                                else:
                                    print(
                                        "Failed to confirm meal plan upload.")
                            else:
                                print(
                                    "Failed to click attach meal plan section or upload PDF.")
                        else:
                            print(
                                "Failed to navigate to the meal plan tab, even after retry.")
                        # Build workout program if possible
                        if trainerize_bot.navigate_to_training_program():
                            print("Skipping current program check as requested.")
                            result = trainerize_bot.create_program(
                                program_name)
                            logging.info(f"create_program returned: {result}")
                            logging.info(f"chest_exercises: {chest_exercises}")
                            logging.info(f"back_exercises: {back_exercises}")
                            logging.info(
                                f"shoulder_exercises: {shoulder_exercises}")
                            logging.info(f"leg_exercises: {leg_exercises}")
                            logging.info(f"core_exercises: {core_exercises}")
                            if result:
                                try:
                                    logging.info(
                                        "=== ABOUT TO BUILD WORKOUTS ===")
                                    if chest_exercises:
                                        logging.info("Building Chest Day...")
                                        trainerize_bot.create_workout_chest_day(
                                            program_name, chest_exercises, already_in_program=True)
                                    if back_exercises:
                                        logging.info("Building Back Day...")
                                        trainerize_bot.create_workout_back_day(
                                            program_name, back_exercises, already_in_program=True)
                                    if shoulder_exercises:
                                        logging.info(
                                            "Building Shoulder Day...")
                                        trainerize_bot.create_workout_shoulder_day(
                                            program_name, shoulder_exercises, already_in_program=True)
                                    if leg_exercises:
                                        logging.info("Building Leg Day...")
                                        trainerize_bot.create_workout_leg_day(
                                            program_name, leg_exercises, already_in_program=True)
                                    if core_exercises:
                                        logging.info("Building Core Day...")
                                        trainerize_bot.create_workout_core_day(
                                            program_name, core_exercises, already_in_program=True)
                                    logging.info(
                                        "=== WORKOUTS BUILT, NOW SCHEDULING ===")
                                    trainerize_bot.schedule_workouts_and_cardio()
                                    trainerize_bot.schedule_body_stats()
                                    trainerize_bot.schedule_progress_photos()
                                    workout_program_built_successfully = True
                                except Exception as e:
                                    logging.error(
                                        f"Exception during workout program build/schedule: {e}\n{traceback.format_exc()}")
                            else:
                                logging.error(
                                    "create_program returned False or None, skipping workout build.")
                        else:
                            print(
                                f"Failed to navigate to the 'Training Program' tab.")
                    else:
                        print(
                            f"Failed to open client profile for {first_name} {last_name} – aborting workflow.")
                else:
                    print("Login failed.")
            except Exception as e:
                import logging
                logging.error(
                    f"An error occurred during Trainerize automation: {e}\n{traceback.format_exc()}")
            finally:
                if 'trainerize_bot' in locals() and trainerize_bot.driver:  # Check if driver exists before quitting
                    trainerize_bot.cleanup()
                # Print final status flags for the calling process to capture
                print(f"CLIENT_ADDED_SUCCESS: {client_added_successfully}")
                print(
                    f"MEAL_PLAN_UPLOAD_SUCCESS: {meal_plan_uploaded_successfully}")
                print(
                    f"WORKOUT_PROGRAM_BUILD_SUCCESS: {workout_program_built_successfully}")

        except Exception as e:
            import logging
            logging.error(
                f"Error parsing command-line arguments or running automation: {e}\n{traceback.format_exc()}")
            print(f"CLIENT_ADDED_SUCCESS: False")
            print(f"MEAL_PLAN_UPLOAD_SUCCESS: False")
            print(f"WORKOUT_PROGRAM_BUILD_SUCCESS: False")

    else:
        # Fallback: run the original demo/test code
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"
        client_name = "Shannon Birch"

        # Updated program name for Shannon
        program_week_name = "Shannons Program"

        # Define exercises for each day of the 5-day split
        chest_exercises = [
            {'name': 'Barbell Bench Chest Press', 'sets': '3', 'reps': '8'},
            {'name': 'Incline Dumbbell Bench press', 'sets': '3', 'reps': '10'},
            {'name': 'Cable Bench Triceps Push Down', 'sets': '3', 'reps': '12'},
            {'name': 'Dumbbell Skull Crusher', 'sets': '3', 'reps': '12'}
        ]

        back_exercises = [
            {'name': 'Wide Grip Chin Up/ Assisted Chin Up', 'sets': '3', 'reps': '8'},
            {'name': 'Lat Pull Down Wide Grip', 'sets': '3', 'reps': '10'},
            {'name': 'Barbell Bent Over Row Pause', 'sets': '4', 'reps': '8'},
            {'name': 'Seated row', 'sets': '3', 'reps': '12'},
            {'name': 'Alternating Hammer Curls', 'sets': '3', 'reps': '10'},
            {'name': 'Concentrated Bicep Curls', 'sets': '3', 'reps': '10'}
        ]

        shoulder_exercises = [
            {'name': 'Arnold Press Eccentric', 'sets': '3', 'reps': '10'},
            {'name': 'Lateral Raise Pause', 'sets': '3', 'reps': '12'},
            {'name': 'Face Pulls', 'sets': '3', 'reps': '15'},
            {'name': 'Deltoid Lateral Raise', 'sets': '3', 'reps': '12'},
            {'name': 'Standing Shoulder Press', 'sets': '3', 'reps': '10'}
        ]

        leg_exercises = [
            {'name': 'Barbell Back Squat Pause', 'sets': '4', 'reps': '8'},
            {'name': 'Bulgarian Lunge', 'sets': '3', 'reps': '10'},
            {'name': 'Dumbbell Romanian Deadlifts', 'sets': '3', 'reps': '12'},
            {'name': 'Leg Extensions', 'sets': '3', 'reps': '15'},
            {'name': 'Lying Leg Curl', 'sets': '3', 'reps': '15'}
        ]

        core_exercises = [
            {'name': 'Plank', 'sets': '3', 'reps': '30'},
            {'name': 'Cable Crunch', 'sets': '3', 'reps': '15'},
            {'name': 'Hanging knee tucks', 'sets': '3', 'reps': '15'},
            {'name': 'V-sit', 'sets': '3', 'reps': '20'},
            {'name': 'Ab Wheel', 'sets': '3', 'reps': '12'}
        ]

        trainerize_bot = TrainerizeAutomation()
        try:
            if trainerize_bot.login(username, password):
                trainerize_bot.handle_notification_popup()

                # 1. Add a new client for Shannon Birch
                new_client_email = "shannonbrich@live.com"
                new_client_first_name = "Shannon"
                new_client_last_name = "Birch"
                if trainerize_bot.add_new_client(new_client_email, new_client_first_name, new_client_last_name):
                    print(
                        f"Successfully added new client: {new_client_first_name} {new_client_last_name} ({new_client_email})")

                    # 2. After opening client account, go directly to meal plan upload
                    if trainerize_bot.navigate_to_meal_plan():
                        meal_plan_pdf_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\meal plans\Shannon_Birch_meal_plan_20250508_173956.pdf"
                        if trainerize_bot.click_attach_meal_plan_pdf(meal_plan_pdf_path):
                            if trainerize_bot.confirm_meal_plan_upload():
                                print("Meal plan uploaded and confirmed.")
                            else:
                                print("Failed to confirm meal plan upload.")
                        else:
                            print(
                                "Failed to click attach meal plan section or upload PDF.")
                    else:
                        print("Failed to navigate to the meal plan tab.")

                    # 3. Build workout program
                    if trainerize_bot.navigate_to_training_program():
                        print("Skipping current program check as requested.")

                        # CREATE PROGRAM
                        if trainerize_bot.create_program(program_week_name, chest_exercises=chest_exercises):
                            print(
                                f"Successfully created program '{program_week_name}' and first workout 'Chest Day'.")
                            # Now create the rest of the workouts, all with already_in_program=True
                            if trainerize_bot.create_workout_back_day(program_week_name, back_exercises, already_in_program=True):
                                print(
                                    f"Successfully created workout 'Back Day' in '{program_week_name}' program and added exercises.")
                            else:
                                print(
                                    f"Failed to create workout 'Back Day' in '{program_week_name}' program or add exercises.")

                            if trainerize_bot.create_workout_shoulder_day(program_week_name, shoulder_exercises, already_in_program=True):
                                print(
                                    f"Successfully created workout 'Shoulder Day' in '{program_week_name}' program and added exercises.")
                            else:
                                print(
                                    f"Failed to create workout 'Shoulder Day' in '{program_week_name}' program or add exercises.")

                            if trainerize_bot.create_workout_leg_day(program_week_name, leg_exercises, already_in_program=True):
                                print(
                                    f"Successfully created workout 'Leg Day' in '{program_week_name}' program and added exercises.")
                            else:
                                print(
                                    f"Failed to create workout 'Leg Day' in '{program_week_name}' program or add exercises.")

                            if trainerize_bot.create_workout_core_day(program_week_name, core_exercises, already_in_program=True):
                                print(
                                    f"Successfully created workout 'Core Day' in '{program_week_name}' program and added exercises.")
                            else:
                                print(
                                    f"Failed to create workout 'Core Day' in '{program_week_name}' program or add exercises.")

                            # Schedule workouts and cardio
                            if trainerize_bot.schedule_workouts_and_cardio():
                                print("Successfully scheduled workouts and cardio.")
                                trainerize_bot.schedule_body_stats()
                                trainerize_bot.schedule_progress_photos()
                            else:
                                print("Failed to schedule workouts and cardio.")

                        else:
                            print(
                                f"Failed to create program '{program_week_name}'.")
                    else:
                        print(f"Failed to navigate to the 'Training Program' tab.")
                else:
                    print(
                        f"Failed to add new client: {new_client_first_name} {new_client_last_name} ({new_client_email})")
            else:
                print("Login failed.")

            input("Press Enter to close...")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            if 'trainerize_bot' in locals():
                trainerize_bot.cleanup()
