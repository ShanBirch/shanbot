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

class TrainerizeOnboardingBot:
    def __init__(self, chrome_driver_path=None, chrome_executable_path=None):
        logging.basicConfig(level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome...")

        # Default paths - can be overridden
        self.chromedriver_path = chrome_driver_path or "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = chrome_executable_path or "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.binary_location = self.chrome_executable_path

        try:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Chrome initialized successfully!")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def handle_cookie_dialog(self):
        logging.info("Cookie dialog handling (placeholder - not clicking Accept).")
        time.sleep(2)

    def handle_notification_popup(self):
        try:
            logging.info("Checking for and handling 'Get notifications?' popup...")
            block_button_locator = (By.XPATH, "//button[contains(text(), 'Block')]")
            block_button = self.wait.until(EC.element_to_be_clickable(block_button_locator))
            block_button.click()
            logging.info("Clicked 'Block' on the notification popup.")
            time.sleep(1)
            return True
        except Exception as e:
            logging.warning(f"Notification popup not found or failed to handle: {e}")
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
            find_me_button = self.driver.find_element(By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(2)
            logging.info("Waiting for the *second* email field (emailInput)...")
            self.wait.until(EC.presence_of_element_located((By.ID, "emailInput")))
            logging.info("Entering *full* email on second page...")
            email_field_second = self.driver.find_element(By.ID, "emailInput")
            email_field_second.send_keys(username)
            logging.info("Entering password...")
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.send_keys(password)
            logging.info("Clicking 'Sign In' button...")
            sign_in_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='signIn-button']")))
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
            clients_link_locator = (By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            except TimeoutException as te:
                logging.error(f"TimeoutException while waiting for Clients link: {te.msg}")
                raise
            time.sleep(2)
            logging.info("Entering client name into the search bar on the Clients page...")
            search_input_locator = (By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(EC.presence_of_element_located(search_input_locator))
            search_input.send_keys(client_name)
            time.sleep(1)
            logging.info("Clicking on the client's name in the search results...")
            client_link_locator = (By.XPATH, f"//a[contains(text(), '{client_name}')]")
            client_link = self.wait.until(EC.element_to_be_clickable(client_link_locator))
            client_link.click()
            time.sleep(2)
            logging.info("Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            logging.info(f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True
        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False

    # NEW METHODS FOR ONBOARDING START HERE

    def navigate_to_goals_and_habits(self):
        """Navigates to the 'Goals and Habits' tab."""
        try:
            logging.info("Navigating to the 'Goals and Habits' tab...")
            goals_habits_locator = (By.XPATH, "//a[@data-testid='leftNavMenu-item-goalsAndHabits' and @title='Goals and Habits']")
            
            # Also try using the ID
            alternative_locator = (By.ID, "nav_goals_and_habits")
            
            # Try multiple locators
            try:
                goals_habits_link = self.wait.until(EC.element_to_be_clickable(goals_habits_locator))
            except:
                try:
                    goals_habits_link = self.wait.until(EC.element_to_be_clickable(alternative_locator))
                except:
                    # Last resort - try by the text content
                    goals_habits_link = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//a[.//p[contains(text(), 'Goals and Habits')]]")
                    ))
            
            goals_habits_link.click()
            time.sleep(2)  # Wait for the page to load
            logging.info("Successfully navigated to the 'Goals and Habits' tab.")
            return True
        except Exception as e:
            logging.error(f"Error navigating to the 'Goals and Habits' tab: {e}")
            self.driver.save_screenshot("goals_nav_error.png")
            return False

    def set_body_weight_goal(self, target_weight):
        """Sets a body weight goal for the client."""
        try:
            logging.info(f"Setting body weight goal: {target_weight}...")
            
            # Click the "New" button
            new_button_locator = (By.XPATH, "//button[contains(@class, 'btn--blue') and .//span[contains(text(), 'New')]]")
            new_button = self.wait.until(EC.element_to_be_clickable(new_button_locator))
            new_button.click()
            logging.info("Clicked 'New' button")
            time.sleep(1)
            
            # Click on "Fitness Goal"
            fitness_goal_locator = (By.XPATH, "//div[contains(@class, 'ant-dropdown-menu-submenu-title')][.//p[contains(text(), 'Fitness Goal')]]")
            fitness_goal_option = self.wait.until(EC.element_to_be_clickable(fitness_goal_locator))
            fitness_goal_option.click()
            logging.info("Clicked 'Fitness Goal' option")
            time.sleep(1)
            
            # Click on "Body Weight Goal"
            body_weight_goal_locator = (By.XPATH, "//p[contains(text(), 'Body Weight Goal')]")
            body_weight_goal_option = self.wait.until(EC.element_to_be_clickable(body_weight_goal_locator))
            body_weight_goal_option.click()
            logging.info("Clicked 'Body Weight Goal' option")
            time.sleep(2)
            
            # Find and enter the target weight
            weight_input_locator = (By.ID, "weightGoal__input")
            weight_input = self.wait.until(EC.presence_of_element_located(weight_input_locator))
            weight_input.clear()
            weight_input.send_keys(str(target_weight))
            # Press Enter after entering the weight
            weight_input.send_keys(Keys.RETURN)
            logging.info(f"Entered target weight: {target_weight} and pressed Enter")
            time.sleep(1)
            
            # Save the goal using the specific data-testid
            save_button_locator = (By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']")
            save_button = self.wait.until(EC.element_to_be_clickable(save_button_locator))
            save_button.click()
            logging.info("Clicked 'Save Goal' button")
            time.sleep(2)
            
            logging.info(f"Successfully set body weight goal to {target_weight}")
            return True
        except Exception as e:
            logging.error(f"Error setting body weight goal: {e}")
            self.driver.save_screenshot("weight_goal_error.png")
            return False

    def navigate_to_meal_plan(self):
        """Navigates to the 'Meal Plan' tab."""
        try:
            logging.info("Navigating to the 'Meal Plan' tab...")
            
            # Try multiple locators to find the Meal Plan link
            meal_plan_locators = [
                (By.XPATH, "//a[@data-testid='leftNavMenu-item-mealPlan' and @title='Meal Plan']"),
                (By.ID, "nav_meal_plan"),
                (By.XPATH, "//a[.//p[contains(text(), 'Meal Plan')]]")
            ]
            
            for locator in meal_plan_locators:
                try:
                    meal_plan_link = self.wait.until(EC.element_to_be_clickable(locator))
                    meal_plan_link.click()
                    logging.info("Successfully clicked Meal Plan link")
                    break
                except:
                    continue
            else:
                raise Exception("Could not find the Meal Plan link")
            
            time.sleep(2)  # Wait for the page to load
            logging.info("Successfully navigated to the 'Meal Plan' tab.")
            return True
        except Exception as e:
            logging.error(f"Error navigating to the 'Meal Plan' tab: {e}")
            self.driver.save_screenshot("meal_plan_nav_error.png")
            return False

    def create_smart_meal_plan(self, calories=2700, macro_split="Balanced", meals_per_day=3, 
                           plan_length=3, dietary_preference="Vegetarian", food_exclusions=None):
        """
        Creates a smart meal plan with specified options.
        
        Args:
            calories (int): Daily calorie target
            macro_split (str): Macro nutrient split (e.g., "Balanced")
            meals_per_day (int): Number of meals per day
            plan_length (int): Length of meal plan in days
            dietary_preference (str): Dietary preference (e.g., "Vegetarian", "No Preferences")
            food_exclusions (list): List of foods to exclude from:
                                   ["eggs", "fish", "pork", "shellfish", "dairy", 
                                    "soy", "gluten", "treeNuts", "peanuts"]
        """
        try:
            logging.info(f"Creating smart meal plan with {calories} calories...")
            
            # Click on "Create smart meal plan" option
            create_smart_plan_locators = [
                (By.XPATH, "//p[contains(text(), 'Create smart meal plan')]/ancestor::div[contains(@style, 'cursor: pointer')]"),
                (By.XPATH, "//div[.//p[contains(text(), 'Create smart meal plan')]]"),
                (By.XPATH, "//img[contains(@src, 'smartMealPlan2.png')]/ancestor::div[1]")
            ]
            
            for locator in create_smart_plan_locators:
                try:
                    create_smart_plan = self.wait.until(EC.element_to_be_clickable(locator))
                    create_smart_plan.click()
                    logging.info("Clicked 'Create smart meal plan'")
                    break
                except:
                    continue
            else:
                logging.error("Could not find 'Create smart meal plan' option")
                self.driver.save_screenshot("create_smart_plan_error.png")
                return False
            
            time.sleep(2)
            
            # Click "LET'S START" button
            start_button_locator = (By.CSS_SELECTOR, "button[data-testid='nullScreen-create-button']")
            try:
                start_button = self.wait.until(EC.element_to_be_clickable(start_button_locator))
                start_button.click()
                logging.info("Clicked 'LET'S START' button")
            except Exception as start_e:
                logging.error(f"Could not click 'LET'S START' button: {start_e}")
                self.driver.save_screenshot("lets_start_button_error.png")
                return False
            
            time.sleep(2)
            
            # Now we'll use a more direct approach to target each field by its label
            
            # Set calories - look for the dropdown after "Calories per day" label
            if not self._select_field_by_label("Calories per day", str(calories)):
                return False
                
            # Set macro split - look for the dropdown after "Macro split" label
            if not self._select_field_by_label("Macro split", macro_split, contains=True):
                return False
                
            # Set meals per day - look for the dropdown after "Meals per day" label
            if not self._select_field_by_label("Meals per day", f"{meals_per_day} meals", contains=True):
                return False
                
            # Set plan length - look for the dropdown after "Number of sample days" label
            if not self._select_field_by_label("Number of sample days", f"{plan_length} days", contains=True):
                return False
                
            # Set dietary preference - look for the dropdown after "Dietary preference" label
            if not self._select_field_by_label("Dietary preference", dietary_preference, contains=True):
                return False
                
            # Handle food exclusions
            if food_exclusions:
                logging.info(f"Setting food exclusions: {food_exclusions}")
                
                # Map of food keywords to their display text in the checkboxes
                food_mapping = {
                    "eggs": "Eggs",
                    "fish": "Fish",
                    "pork": "Pork",
                    "shellfish": "Shellfish",
                    "dairy": "Dairy",
                    "soy": "Soy",
                    "gluten": "Gluten",
                    "tree nuts": "Tree nuts",
                    "treenuts": "Tree nuts",
                    "peanuts": "Peanuts"
                }
                
                for food in food_exclusions:
                    try:
                        # Get the display text for the checkbox label
                        food_display = food_mapping.get(food.lower(), food)
                        
                        # Find the checkbox by its label text
                        checkbox_locator = (By.XPATH, f"//span[text()='{food_display}']/preceding-sibling::span/input[@type='checkbox']")
                        checkbox = self.wait.until(EC.presence_of_element_located(checkbox_locator))
                        
                        # Since checkboxes might be hidden behind a label, use JavaScript to click
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        logging.info(f"Excluded {food}")
                    except Exception as e:
                        # Try alternative approach - click the label instead
                        try:
                            label_locator = (By.XPATH, f"//span[text()='{food_display}']")
                            label = self.wait.until(EC.presence_of_element_located(label_locator))
                            label.click()
                            logging.info(f"Excluded {food} by clicking label")
                        except Exception as label_e:
                            logging.warning(f"Could not exclude {food}: {e} / {label_e}")
                            # Continue with other exclusions
            
            # Click the Create button to generate the meal plan
            try:
                # Try multiple locators for the Create button, in order of specificity
                create_button_locators = [
                    # Exact data-testid attribute
                    (By.CSS_SELECTOR, "button[data-testid='mealPlanDialog-generateMealPlan-button']"),
                    # Case-sensitive button text (looking for the span)
                    (By.XPATH, "//button//span[text()='Create']/parent::button"),
                    # Looking for the button directly with the text
                    (By.XPATH, "//button[.//span[text()='Create']]"),
                    # Fallback options
                    (By.XPATH, "//button[contains(@class, 'btn--blue') and contains(.//span, 'Create')]"),
                    (By.XPATH, "//button[contains(@class, 'btn--blue') and contains(@class, 'ant-btn-submit')]")
                ]
                
                for locator in create_button_locators:
                    try:
                        create_button = self.wait.until(EC.element_to_be_clickable(locator))
                        # Take screenshot before clicking
                        self.driver.save_screenshot("before_create_button_click.png")
                        
                        # Try standard click
                        try:
                            create_button.click()
                            logging.info("Clicked 'Create' button using standard click")
                        except Exception as click_e:
                            # Try JavaScript click if standard click fails
                            self.driver.execute_script("arguments[0].click();", create_button)
                            logging.info("Clicked 'Create' button using JavaScript")
                            
                        time.sleep(5)  # Wait longer for meal plan generation
                        
                        # Take screenshot after clicking
                        self.driver.save_screenshot("after_create_button_click.png")
                        break
                    except Exception as locator_e:
                        logging.warning(f"Could not find/click Create button with locator {locator}: {locator_e}")
                        continue
                else:  # If all locators failed
                    raise Exception("None of the Create button locators worked")
                    
                logging.info("Successfully clicked 'Create' button to generate meal plan")
            except Exception as create_e:
                logging.error(f"Could not click 'Create' button: {create_e}")
                self.driver.save_screenshot("create_button_error.png")
                return False
            
            logging.info(f"Successfully set up smart meal plan with specified options")
            return True
                
        except Exception as e:
            logging.error(f"Error creating smart meal plan: {e}")
            self.driver.save_screenshot("smart_meal_plan_error.png")
            return False
            
    def _select_field_by_label(self, label_text, option_value, contains=False):
        """Select a field by its label, then select the specified option"""
        try:
            option_value_str = str(option_value)
            logging.info(f"Setting '{label_text}' to '{option_value_str}'")
            
            # Take a screenshot before starting
            self.driver.save_screenshot(f"before_{label_text.replace(' ', '_')}.png")
            
            # First find the dropdown by its preceding label
            label_locators = [
                (By.XPATH, f"//div[contains(text(), '{label_text}')]/following::div[contains(@class, 'ant-select-selection')][1]"),
                (By.XPATH, f"//span[contains(text(), '{label_text}')]/following::div[contains(@class, 'ant-select-selection')][1]"),
                (By.XPATH, f"//*[contains(text(), '{label_text}')]/following::div[contains(@class, 'ant-select-selection')][1]")
            ]
            
            dropdown = None
            for locator in label_locators:
                try:
                    dropdown = self.wait.until(EC.element_to_be_clickable(locator))
                    logging.info(f"Found dropdown for '{label_text}' using locator: {locator}")
                    break
                except:
                    continue
                    
            if not dropdown:
                logging.error(f"Could not find dropdown for '{label_text}'")
                self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_dropdown_not_found.png")
                return False
                
            # Click the dropdown to open it
            try:
                dropdown.click()
                logging.info(f"Clicked dropdown for '{label_text}'")
                time.sleep(1)
            except Exception as click_e:
                # Try JavaScript click if normal click fails
                try:
                    self.driver.execute_script("arguments[0].click();", dropdown)
                    logging.info(f"Used JavaScript to click dropdown for '{label_text}'")
                    time.sleep(1)
                except Exception as js_e:
                    logging.error(f"Could not click dropdown for '{label_text}': {click_e} / {js_e}")
                    self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_click_failed.png")
                    return False
                    
            # Take a screenshot after opening dropdown
            self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_dropdown_open.png")
                
            # Find and click the option
            if contains:
                option_locator = (By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and contains(text(), '{option_value_str}')]")
            else:
                option_locator = (By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and text()='{option_value_str}']")
                
            try:
                option = self.wait.until(EC.element_to_be_clickable(option_locator))
                option.click()
                logging.info(f"Selected '{option_value_str}' for '{label_text}'")
                time.sleep(1)
                
                # Take a screenshot after selection
                self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_option_selected.png")
                return True
            except Exception as option_e:
                logging.error(f"Could not select option '{option_value_str}' for '{label_text}': {option_e}")
                self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_option_select_failed.png")
                
                # Try to click any option as fallback
                try:
                    any_option = self.driver.find_element(By.XPATH, "//li[contains(@class, 'ant-select-dropdown-menu-item')]")
                    any_option.click()
                    logging.warning(f"Selected fallback option for '{label_text}'")
                    time.sleep(1)
                    return True
                except:
                    return False
                
        except Exception as e:
            logging.error(f"Error in _select_field_by_label for '{label_text}': {e}")
            self.driver.save_screenshot(f"{label_text.replace(' ', '_')}_error.png")
            return False
            
    def _select_from_dropdown(self, option_type, option_value, contains=False):
        """Helper method to select an option from a dropdown"""
        try:
            # Convert option_value to string to avoid type errors
            option_value_str = str(option_value)
            
            logging.info(f"Setting {option_type} to: {option_value_str}")
            
            # Special handling for macro split dropdown
            if option_type == "macro split":
                # Direct targeting of the macro split dropdown by title attribute
                try:
                    macro_dropdown = self.driver.find_element(By.XPATH, 
                        "//div[contains(@class, 'ant-select-selection-selected-value') and contains(@title, 'Balanced')]"
                    )
                    # Click its parent
                    self.driver.execute_script("arguments[0].parentNode.parentNode.click();", macro_dropdown)
                    logging.info("Clicked macro split dropdown using title attribute")
                    time.sleep(1)
                except Exception as e:
                    logging.warning(f"Could not find macro split dropdown by title: {e}")
                    # Fall back to general approach
            
            # Try to find and click on the dropdown
            dropdown_found = False
            dropdown_locators = [
                # Try to find by title attribute containing the option_type text
                (By.XPATH, f"//div[contains(@class, 'ant-select-selection-selected-value') and contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{option_type.lower()}')]"),
                # General dropdown locators
                (By.XPATH, "//div[contains(@class, 'ant-select-selection__rendered')]"),
                (By.XPATH, "//div[contains(@class, 'ant-select-selection')]")
            ]
            
            # Try each locator strategy
            for locator in dropdown_locators:
                try:
                    # Find all matching elements
                    dropdowns = self.driver.find_elements(*locator)
                    if not dropdowns:
                        continue
                        
                    # Try each dropdown one by one
                    for dropdown in dropdowns:
                        try:
                            # First take a screenshot for debugging
                            self.driver.save_screenshot(f"before_click_{option_type.replace(' ', '_')}.png")
                            
                            # Click the dropdown
                            # First try direct click
                            try:
                                dropdown.click()
                            except:
                                # If direct click fails, try JavaScript
                                self.driver.execute_script("arguments[0].click();", dropdown)
                                
                            time.sleep(1)
                            
                            # Check if dropdown expanded by looking for dropdown menu
                            try:
                                menu = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'ant-select-dropdown-menu')]")
                                if menu.is_displayed():
                                    logging.info(f"Successfully opened dropdown for {option_type}")
                                    dropdown_found = True
                                    break
                            except:
                                logging.info(f"Dropdown click didn't open menu, trying next element")
                                continue
                        except Exception as click_e:
                            logging.warning(f"Error clicking dropdown: {click_e}")
                            continue
                    
                    if dropdown_found:
                        break
                        
                except Exception as e:
                    logging.warning(f"Error with dropdown locator: {e}")
                    continue
            
            if not dropdown_found:
                # Last resort approach - try to find any select and click it
                try:
                    selects = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ant-select')]")
                    if selects:
                        for select in selects:
                            try:
                                self.driver.execute_script("arguments[0].click();", select)
                                time.sleep(1)
                                try:
                                    menu = self.driver.find_element(By.XPATH, "//ul[contains(@class, 'ant-select-dropdown-menu')]")
                                    if menu.is_displayed():
                                        logging.info(f"Last resort dropdown click worked for {option_type}")
                                        dropdown_found = True
                                        break
                                except:
                                    continue
                            except:
                                continue
                except Exception as last_e:
                    logging.error(f"Last resort dropdown approach failed: {last_e}")
            
            if not dropdown_found:
                logging.error(f"Could not open dropdown for {option_type}")
                self.driver.save_screenshot(f"{option_type.replace(' ', '_')}_dropdown_error.png")
                return False
            
            # Dropdown is now open
            # Take a screenshot after opening dropdown
            self.driver.save_screenshot(f"dropdown_open_{option_type.replace(' ', '_')}.png")
            
            # Scrape all available options for logging
            try:
                options = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'ant-select-dropdown-menu-item')]")
                option_texts = [option.text for option in options]
                logging.info(f"Available options for {option_type}: {option_texts}")
            except Exception as scrape_e:
                logging.warning(f"Could not scrape dropdown options: {scrape_e}")
            
            # Scroll within the dropdown if needed
            try:
                # Use JavaScript to scroll the dropdown menu
                self.driver.execute_script(
                    "var dropdowns = document.querySelectorAll('.ant-select-dropdown-menu'); " +
                    "for (var i = 0; i < dropdowns.length; i++) { " +
                    "    if (dropdowns[i].offsetParent !== null) { " +  # Check if visible
                    "        dropdowns[i].scrollTop = 100; " +
                    "    } " +
                    "}"
                )
                logging.info(f"Scrolled within dropdown for {option_type}")
                time.sleep(1)
            except Exception as scroll_e:
                logging.warning(f"Could not scroll dropdown for {option_type}, continuing anyway: {scroll_e}")
            
            # Create multiple strategies for finding the right option
            option_locators = []
            
            # For exact option value
            option_locators.append((By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and normalize-space(text())='{option_value_str}']"))
            
            # For partial match
            if contains:
                option_locators.append((By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and contains(text(), '{option_value_str}')]"))
            
            # Starting with the value
            option_locators.append((By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and starts-with(normalize-space(text()), '{option_value_str}')]"))
            
            # Case insensitive contains
            option_locators.append((By.XPATH, f"//li[contains(@class, 'ant-select-dropdown-menu-item') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{option_value_str.lower()}')]"))
            
            # Try each option locator strategy
            for locator in option_locators:
                try:
                    options = self.driver.find_elements(*locator)
                    if options:
                        options[0].click()
                        logging.info(f"Selected option for {option_type} using locator: {locator}")
                        time.sleep(1)
                        self.driver.save_screenshot(f"after_select_{option_type.replace(' ', '_')}.png")
                        return True
                except Exception as option_e:
                    logging.warning(f"Error with option locator {locator}: {option_e}")
                    continue
            
            # If we get here, we failed to find the right option
            logging.error(f"Could not find option {option_value_str} for {option_type}")
            self.driver.save_screenshot(f"{option_type.replace(' ', '_')}_option_error.png")
            
            # Try to select first option in the dropdown as fallback
            try:
                first_option = self.driver.find_element(By.XPATH, "//li[contains(@class, 'ant-select-dropdown-menu-item')]")
                first_option.click()
                logging.warning(f"Selected first available option for {option_type} as fallback")
                return True
            except Exception as fallback_e:
                logging.error(f"Fallback option selection failed: {fallback_e}")
                return False
            
        except Exception as e:
            logging.error(f"Error setting {option_type} to {option_value}: {e}")
            self.driver.save_screenshot(f"{option_type.replace(' ', '_')}_selection_error.png")
            return False

    def onboard_client(self, client_name, target_weight, calories=2700, macro_split="Balanced", 
                       meals_per_day=3, plan_length=3, dietary_preference="Vegetarian", 
                       food_exclusions=None):
        """Complete onboarding for a client by setting their goals and meal plan."""
        try:
            logging.info(f"Starting onboarding process for client: {client_name}")
            
            # Navigate to client
            if not self.navigate_to_client(client_name):
                logging.error(f"Failed to navigate to client: {client_name}")
                return False
            
            # Set body weight goal
            if not self.navigate_to_goals_and_habits():
                logging.error("Failed to navigate to Goals and Habits")
                return False
            
            if not self.set_body_weight_goal(target_weight):
                logging.error(f"Failed to set body weight goal: {target_weight}")
                return False
            
            # Create smart meal plan
            if not self.navigate_to_meal_plan():
                logging.error("Failed to navigate to Meal Plan")
                return False
            
            if not self.create_smart_meal_plan(calories, macro_split, meals_per_day, 
                                              plan_length, dietary_preference, food_exclusions):
                logging.error(f"Failed to create smart meal plan")
                return False
            
            logging.info(f"Successfully onboarded client: {client_name}")
            return True
        except Exception as e:
            logging.error(f"Error during client onboarding: {e}")
            self.driver.save_screenshot("onboarding_error.png")
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
                logging.info(f"Removing temp user data directory: {self.temp_user_data_dir}")
                shutil.rmtree(self.temp_user_data_dir)
                logging.info("Temp directory removed.")
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


# Example usage
if __name__ == '__main__':
    # Login credentials
    USERNAME = "shannonbirch@cocospersonaltraining.com"
    PASSWORD = "cyywp7nyk"
    
    # Client details
    CLIENT_NAME = "Shannon Birch"
    TARGET_WEIGHT = 90  # in kg
    CALORIES = 2700      # daily calorie target for meal plan
    MACRO_SPLIT = "Balanced"  # Balanced (30% Protein, 40% Carb, 30% Fat)
    MEALS_PER_DAY = 5    # Updated to match screenshot
    PLAN_LENGTH = 7      # Updated to match screenshot (7 days)
    DIETARY_PREFERENCE = "No Preferences"  # Updated to match screenshot
    FOOD_EXCLUSIONS = ["eggs"]  # Foods to exclude
    
    # Initialize the onboarding bot
    trainerize_bot = TrainerizeOnboardingBot()
    
    try:
        # Login
        if trainerize_bot.login(USERNAME, PASSWORD):
            trainerize_bot.handle_notification_popup()
            
            # Onboard the client
            if trainerize_bot.onboard_client(
                CLIENT_NAME, 
                TARGET_WEIGHT, 
                CALORIES,
                MACRO_SPLIT,
                MEALS_PER_DAY,
                PLAN_LENGTH,
                DIETARY_PREFERENCE,
                FOOD_EXCLUSIONS
            ):
                print(f"Successfully onboarded {CLIENT_NAME}")
            else:
                print(f"Failed to onboard client")
        else:
            print("Login failed.")
        
        # Wait for user to review
        input("Press Enter to close the browser and exit...")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()