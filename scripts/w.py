from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import logging
import tempfile
import shutil
import os
from datetime import datetime, timedelta, date

from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, InvalidSessionIdException
import re
import base64
import csv

# --- Gemini API Imports ---  (REMOVED Gemini API Imports)
# import google.generativeai as genai # REMOVED

class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, # Changed logging level to INFO for less verbose logging
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = "C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
        self.chrome_executable_path = "C:\SeleniumDrivers\chrome-win64\chrome.exe"

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
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")

        except Exception as e:
            logging.exception(f"Failed to initialize Chrome: {e}")
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
            logging.info("Waiting for the second email field (emailInput)...")
            self.wait.until(EC.presence_of_element_located((By.ID, "emailInput")))
            logging.info("Entering full email on second page...")
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
            logging.exception(f"Error during login: {e}")
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
                return False

            time.sleep(2)
            logging.info("Entering client name into the search bar on the Clients page...")
            search_input_locator = (By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(EC.presence_of_element_located(search_input_locator))
            # Clear the search bar before typing the new client name
            search_input.clear()
            search_input.send_keys(client_name)
            time.sleep(2)
            logging.info("Clicking on the client's name in the search results...")
            client_link_locator = (By.XPATH, f"//a[contains(text(), '{client_name}')]")
            try:
                client_link = self.wait.until(EC.element_to_be_clickable(client_link_locator))
                client_link.click()
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Could not find or click client link for {client_name}: {e}")
                return False

            time.sleep(2)
            logging.info("Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            try:
                open_button = self.wait.until(EC.element_to_be_clickable(open_button_locator))
                open_button.click()
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Could not find or click 'Open' button for {client_name}: {e}")
                return False

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
            logging.exception(f"Error navigating to client {client_name} or switching tabs: {e}")
            return False


    def click_progress_tab(self):
        try:
            logging.info("Attempting to click the 'Progress' tab...")
            progress_tab_locator = (By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab = self.wait.until(EC.element_to_be_clickable(progress_tab_locator))
            progress_tab.click()
            logging.info("Successfully clicked the 'Progress' tab.")
            return "Successfully clicked Progress tab"
        except TimeoutException:
            logging.error("TimeoutException: 'Progress' tab not found or not clickable within the timeout.")
            return "Failed to click Progress tab (Timeout)"
        except NoSuchElementException:
            logging.error("NoSuchElementException: 'Progress' tab element not found on the page.")
            return "Failed to click Progress tab (Not Found)"
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return "Failed to click Progress tab (Unknown Error)"


    def click_review_by_workout(self):
        """Clicks the 'Review By Workout' link on the Progress page."""
        try:
            logging.info("Attempting to click the 'Review By Workout' link...")

            # Locate the "Review By Workout" link using XPath.  Target _self is also added.
            review_link_locator = (By.XPATH, "//a[@class='tz-sp section-link text-overflow-none' and contains(@href, '/progress/workout') and @target='_self']")
            review_link = self.wait.until(EC.element_to_be_clickable(review_link_locator))
            review_link.click()
            logging.info("Successfully clicked the 'Review By Workout' link.")
            return "Successfully clicked 'Review By Workout' link"

        except TimeoutException:
            logging.error("TimeoutException: 'Review By Workout' link not found or not clickable within timeout.")
            return "Failed to click 'Review By Workout' link (Timeout)"
        except NoSuchElementException:
            logging.error("NoSuchElementException: 'Review By Workout' link element not found on the page.")
            return "Failed to click 'Review By Workout' link (Not Found)"
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return "Failed to click 'Review By Workout' link (Unknown Error)"
        

    def process_workouts(self):
        """Gets workout data, processes workout details, with IMPROVED NORMALIZATION for numbered workouts."""
        try:
            workout_data_list = []
            processed_workout_keys = set()  # Keep track of processed workout identifiers
            workout_retry_counts = {}

            self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))

            # Scroll to ensure all workouts are visible
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            workout_links = self.driver.find_elements(
                By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
            logging.info(f"Found {len(workout_links)} workout links")
            logging.info(f"Found workout links with names: {[link.text.strip() for link in workout_links]}")

            expected_unprocessed_workouts = set()
            for link in workout_links:
                try:
                    parent_row = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'baseGridRow')]")
                    date_element = parent_row.find_element(
                        By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                    date_str = date_element.text.strip()
                    
                    workout_name = link.text.strip()
                    logging.info(f"Found workout: '{workout_name}' on date: '{date_str}'")

                    original_date_str = date_str  # Store the original date string here

                    # --- Convert date string to 'YYYY-MM-DD' format ---
                    try:
                        date_obj = datetime.strptime(date_str, '%d %b %Y') # Try to parse 'DD Mon YYYY' format
                        date_str_iso = date_obj.strftime('%Y-%m-%d') # Convert to 'YYYY-MM-DD'
                    except ValueError:
                        # If parsing 'DD Mon YYYY' fails, check if it's "Saturday"
                        if date_str.lower() == 'saturday':
                            # Handle "Saturday" - for now, just keep it as "Saturday" string
                            date_str_iso = 'Saturday'
                        else:
                            # If it's not "Saturday" and not 'DD Mon YYYY', keep original
                            date_str_iso = date_str # Keep original if parsing fails

                    date_str = date_str_iso # Use the converted/original date string

                    # IMPROVED: Create a unique workout key that includes the number suffix and date
                    workout_key = f"{workout_name}_{date_str}"

                    if workout_key not in processed_workout_keys:
                        expected_unprocessed_workouts.add((workout_name, original_date_str, workout_key))
                    else:
                        logging.info(f"Workout '{workout_name}' with Key '{workout_key}' ALREADY in expected_unprocessed_workouts (Skipping add to expected_unprocessed_workouts)")
                except NoSuchElementException:
                    logging.info(f"Skipping a workout link due to missing date element.")
                    continue

            workouts_to_process_this_iteration = list(expected_unprocessed_workouts)

            for workout_tuple_index, workout_tuple in enumerate(workouts_to_process_this_iteration):
                workout_name, date_str, workout_key = workout_tuple

                if workout_key in processed_workout_keys:
                    continue

                link_locator = (By.XPATH,
                            f"//div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName' and text()='{workout_name}']/ancestor::div[contains(@class, 'baseGridRow')]//span[@data-testid='clientProgress-workouts-summaryGrid-date' and text()='{date_str}']/ancestor::div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                try:
                    workout_link = self.driver.find_element(*link_locator)
                    workout_data_formatted_list = self._process_single_workout(workout_link, workout_name, date_str)
                    if workout_data_formatted_list:
                        for workout_dict in workout_data_formatted_list:
                            workout_data_list.append(workout_dict)
                        processed_workout_keys.add(workout_key)
                        if workout_key in workout_retry_counts:
                            del workout_retry_counts[workout_key]

                except NoSuchElementException:
                    retry_count = workout_retry_counts.get(workout_key, 0)
                    workout_retry_counts[workout_key] = retry_count + 1

                    if retry_count >= 10:
                        processed_workout_keys.add(workout_key)
                        expected_unprocessed_workouts.remove(workout_tuple)
                        continue
                    else:
                        continue

            # Special case: Check for Core and Arms 2 on Feb 27
            core_arms_2_workout = self.find_workout_on_date("27 Feb", "Core and Arms")
            if core_arms_2_workout:
                logging.info("Found Core and Arms 2 workout on Feb 27 with specific search")
                workout_data_formatted_list = self._process_single_workout(core_arms_2_workout, core_arms_2_workout.text.strip(), "27 Feb 2025")
                if workout_data_formatted_list:
                    for workout_dict in workout_data_formatted_list:
                        workout_data_list.append(workout_dict)

            # Also check for any other workouts we may have missed
            for day in ["26", "27", "28"]:
                any_workout = self.find_workout_on_date(f"{day} Feb")
                if any_workout and any_workout.text.strip() not in [workout["workout_type"] for workout in workout_data_list if workout.get("date", "").startswith(f"{day} Feb")]:
                    logging.info(f"Found additional workout on Feb {day}: {any_workout.text.strip()}")
                    workout_data_formatted_list = self._process_single_workout(any_workout, any_workout.text.strip(), f"{day} Feb 2025")
                    if workout_data_formatted_list:
                        for workout_dict in workout_data_formatted_list:
                            workout_data_list.append(workout_dict)

            logging.info(f"workout_data_list before return in process_workouts: {workout_data_list}")
            logging.info("Exiting process_workouts function")
            return workout_data_list

        except Exception as e:
            logging.exception(f"Error during workout processing: {e}")
            return []-*
    

    def _process_single_workout(self, workout_link, workout_name, date_str):
        """Helper function to process a single workout link, now returns structured data."""
        try:
            logging.info(f"Processing workout: {workout_name} on {date_str}")

            # --- REMOVE OR COMMENT OUT THIS ENTIRE BLOCK - AS PER INSTRUCTION ---
            # if workout_name.lower() == "saturday":
            #     logging.info(f"Skipping details for 'Saturday' workout, counting as completed.")
            #     return [{'date': date_str, 'workout_type': workout_name, 'exercises': [{'name': 'Workout Completed', 'sets': []}]}] # Structure for Saturday - list containing one workout

            # --- Click the workout name ---
            workout_link.click()
            time.sleep(2)

            # --- Analyze workout details (on the new page, same tab) ---
            formatted_workout_data_list = self.analyze_workout_details_stripped(workout_name, date_str) # Now gets a list of workout dictionaries

            # --- Go back to the workout list page ---
            logging.info("Going back to previous page")
            self.driver.back()
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))
            logging.info("Back on workout list page")
            return formatted_workout_data_list # Returns the list of workout dictionaries

        except Exception as e:
            logging.exception(f"Error processing workout link: {e}")
            return None

    def analyze_workout_details_stripped(self, workout_name, date_str):
        return analyze_workout_details_stripped_base(self, workout_name, date_str)


    def navigate_back_to_clients_list(self):
        """Navigates back to the main Clients list tab and closes the dialog."""
        try:
            logging.info("Navigating back to the Clients list tab and closing dialog...")
            try:
                self.driver.close()  # Close the current client's profile tab
                logging.info("Closed client profile tab.")
            except (WebDriverException, InvalidSessionIdException) as e:
                logging.warning(f"Error closing client tab: {e}")

            original_window_handle = self.driver.window_handles[0]
            self.driver.switch_to.window(original_window_handle)
            logging.info("Switched back to the main Clients list tab.")
            time.sleep(2) # small wait for page to settle

            logging.info("Attempting to close client profile dialog if present...")
            close_button_locator = (By.CSS_SELECTOR, "span[data-testid='close-button'].closeButton.clickable")
            try:
                close_button = self.wait.until(EC.element_to_be_clickable(close_button_locator))
                close_button.click()
                logging.info("Client profile dialog closed successfully.")
            except TimeoutException:
                logging.warning("Client profile dialog close button not found or not clickable (may not be present). Continuing anyway.")
            except Exception as close_exception:
                logging.error(f"Error while trying to close client profile dialog: {close_exception}")
            return True
        except Exception as e:
            logging.exception(f"Error navigating back to Clients list: {e}")
            return False

    def cleanup(self):
        """Cleans up resources (removes temp dir, and now closes driver correctly)."""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'): # Check if driver exists before trying to close
                logging.info("Closing webdriver...")
                try:
                    self.driver.close()  # Close the current window (if any)
                except (WebDriverException, InvalidSessionIdException) as e:
                    logging.warning(f"Error closing current window during cleanup: {e}")
                try:
                    self.driver.quit()   # Quit the browser entirely
                except (WebDriverException, InvalidSessionIdException) as e:
                    logging.warning(f"Error quitting webdriver during cleanup: {e}")
                logging.info("Webdriver closed.")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                logging.info(f"Removing temp user data directory: {self.temp_user_data_dir}")
                shutil.rmtree(self.temp_user_data_dir)
                logging.info("Temp directory removed.")
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.exception(f"Error during cleanup: {e}")

    def calculate_workout_stats_for_date_range(self, workout_data_list, start_date, end_date, target_exercises=None):
        """Calculates workout stats within a specific date range and returns workout data and exercise-specific workload."""
        if not workout_data_list:
            return 0, [], 0, 0, 0, [], {} # Return empty workout_data_in_range list and exercise_workload

        workout_count = 0
        workout_names_in_range = []
        total_weight_lifted = 0
        total_reps = 0
        total_sets = 0
        workout_data_in_range = [] # List to store workout data within the date range
        exercise_workload = {} # Dictionary to store workload per exercise

        for workout in workout_data_list:
            date_str = workout['date']
            workout_date_obj = None

            if date_str.lower() == 'saturday':
                saturday_date = start_date + timedelta(days=(5 - start_date.weekday() + 7) % 7)
                workout_date_obj = saturday_date
            else:
                try:
                    workout_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        workout_date_obj = datetime.strptime(date_str, '%d %b %Y').date()
                    except ValueError:
                        continue

            if start_date <= workout_date_obj <= end_date:
                workout_count += 1
                workout_names_in_range.append(workout['workout_type'])
                workout_data_in_range.append(workout) # Add the workout to the list

                for exercise in workout['exercises']:
                    exercise_name = exercise['name'].strip()
                    exercise_total_weight = 0 # Track weight for this exercise in this workout
                    for set_data in exercise['sets']:
                        weight = set_data['weight']
                        reps = set_data['reps']
                        total_weight_lifted += weight * reps
                        total_reps += reps
                        total_sets += 1
                        exercise_total_weight += weight * reps # Accumulate weight for this exercise

                    if target_exercises and exercise_name in target_exercises: # Only store for target exercises
                        exercise_workload.setdefault(exercise_name, 0) # Initialize if not exists
                        exercise_workload[exercise_name] += exercise_total_weight # Add to exercise workload

        return workout_count, workout_names_in_range, total_weight_lifted, total_reps, total_sets, workout_data_in_range, exercise_workload # Return exercise_workload


def analyze_workout_details_stripped_base(self, workout_name, date_str):
    """Base analyze_workout_details_stripped for both TrainerizeAutomation and TrainerizeCSVParsing."""
    try:
        logging.info("Starting analyze_workout_details_stripped (revised date-set mapping)...")
        workout_list_for_page = []  # Initialize list to store workout data for each date
        dates = []

        # --- 1. Extract Dates from Header Row ---
        date_header_cells = self.driver.find_elements(By.XPATH,
                                                    "//thead[@class='ant-table-thead']/tr[1]/th[contains(@class, 'bgGray10') and contains(@class, 'colorPrimaryBlue') and contains(@class, 'clickable')]")
        dates = [cell.text.strip() for cell in date_header_cells]
        logging.info(f"Extracted Dates: {dates}")

        # --- 2. Iterate through Dates and then Table Body Rows ---
        for current_date_index, current_date_str in enumerate(dates):  # Iterate through dates
            workout_data = {'date': current_date_str, 'workout_type': workout_name, 'exercises': []}  # Create workout data for EACH date
            current_exercise_data = None

            rows = self.driver.find_elements(By.XPATH,
                                            "//tbody[@class='ant-table-tbody']/tr[@class='ant-table-row ant-table-row-level-0']")
            logging.info(
                f"Processing date: {current_date_str}. Number of table rows found: {len(rows)}")  # DEBUG - keep for general info

            for row_index, row in enumerate(rows):
                cells = row.find_elements(By.XPATH, "./td")
                if not cells or len(cells) < 2:
                    continue

                # --- Check for Exercise Name Cell ---
                exercise_name_cells = row.find_elements(By.XPATH,
                                                        "./td[@class='ant-table-fixed-columns-in-body clickable ant-table-row-cell-break-word' and @rowspan and contains(@style, 'color: rgb(34, 158, 212)')]")
                if exercise_name_cells:
                    exercise_name_cell = exercise_name_cells[0]
                    exercise_name = exercise_name_cell.text.strip()
                    current_exercise_name = exercise_name
                    current_exercise_data = {'name': exercise_name, 'sets': []}  # Initialize exercise data
                    workout_data['exercises'].append(current_exercise_data)  # Add exercise to workout data
                    logging.info(
                        f"  Date: {current_date_str}, Row {row_index}: Exercise Detected - {exercise_name}")  # DEBUG - keep for general info

                # --- Check for Set Data Row (within an exercise) ---
                set_number_cells = row.find_elements(By.XPATH,
                                                      "./td[@class='ant-table-fixed-columns-in-body ant-table-row-cell-break-word' and contains(@style, 'text-align: center; font-size: 12px;') and contains(text(), 'SET')]")
                if set_number_cells and current_exercise_data is not None:  # Check if current_exercise_data is initialized
                    set_number_cell = set_number_cells[0]
                    set_number_text = set_number_cell.text.strip()
                    logging.info(
                        f"  Date: {current_date_str}, Row {row_index}: Set Detected - {set_number_text} for Exercise - {current_exercise_name}")  # DEBUG - keep for general info

                    # --- Extract Set Data for the CURRENT Date Column ---
                    data_cells = cells[2:]  # Data cells start from 3rd cell onwards (index 2)
                    if current_date_index < len(data_cells):
                        data_cell = data_cells[current_date_index]  # Get data cell corresponding to the current date
                        set_text = data_cell.text.strip()
                        logging.info(f"    Date: {current_date_str}, Cell Text for Date Column: '{set_text}'")  # DEBUG - keep for general info
                        if set_text and set_text != "-":  # Ignore empty/placeholder
                            match = re.match(r"(\d+)\s*X\s*([\d.-]*)\s*(?:kg)?", set_text, re.IGNORECASE)
                            if match:
                                reps_str, weight_str = match.groups()
                                try:
                                    reps = int(reps_str)
                                    weight = float(weight_str) if weight_str and weight_str != '-' else 0.0
                                    set_data = {'set': int(set_number_text.split(' ')[1]), 'reps': reps, 'weight': weight,
                                                'date': current_date_str}  # Date is current date
                                    current_exercise_data['sets'].append(
                                        set_data)  # Append set data to current exercise
                                    logging.info(
                                        f"      Date: {current_date_str}, Extracted Set Data: Set {set_number_text.split(' ')[1]}, Reps: {reps}, Weight: {weight}")  # DEBUG - keep for general info
                                except ValueError:
                                    logging.warning(
                                        f"    Date: {current_date_str}, ValueError parsing set data: {set_text}")
                            else:
                                logging.warning(
                                    f"    Date: {current_date_str}, Unparsable set data format: {set_text}")
            if workout_data['exercises']:  # Only add to list if there are exercises for this date
                workout_list_for_page.append(workout_data)  # Add populated workout data to the list

        logging.info(
            "Exiting analyze_workout_details_stripped (revised date-set mapping) - Data extraction complete.")
        return workout_list_for_page  # Return the list of workout dictionaries for all dates on the page

    except Exception as e:  # ADDED EXCEPT BLOCK HERE
        logging.exception(f"Error analyzing workout details (revised date-set mapping): {e}")
        return []


def print_exercise_details(workout_data_current_week, workout_data_previous_week, target_exercises, date_range_str_prompt, previous_date_range_str_prompt):
    """Prints details for specified exercises for current and previous weeks."""
    for exercise_name in target_exercises:
        print(f"\n--- Exercise: {exercise_name} ---")

        print(f"\n**Week of {date_range_str_prompt}:**")
        found_in_current_week = False
        for workout in workout_data_current_week:
            workout_date_str = workout['date'] # Date is already in string format from parsing
            for exercise in workout['exercises']:
                if exercise['name'].strip() == exercise_name:
                    found_in_current_week = True
                    print(f"  Workout - {workout_date_str}")
                    print(f"  Exercise - {exercise['name']}")
                    for set_data in exercise['sets']:
                        print(f"    Set {set_data['set']}: {set_data['reps']} reps, {set_data['weight']:.2f} kg")
        if not found_in_current_week:
            print(f"  Not performed in week of {date_range_str_prompt}")

        print(f"\n**Week of {previous_date_range_str_prompt}:**")
        found_in_previous_week = False
        for workout in workout_data_previous_week:
            workout_date_str = workout['date'] # Date is already in string format from parsing
            for exercise in workout['exercises']:
                if exercise['name'].strip() == exercise_name:
                    found_in_previous_week = True
                    print(f"  Workout - {workout_date_str}")
                    print(f"  Exercise - {exercise['name']}")
                    for set_data in exercise['sets']:
                        print(f"    Set {set_data['set']}: {set_data['reps']} reps, {set_data['weight']:.2f} kg")
        if not found_in_previous_week:
            print(f"  Not performed in week of {previous_date_range_str_prompt}")

def calculate_exercise_workload_change(current_week_exercise_workload, previous_week_exercise_workload, target_exercises):
    """Calculates and prints workload change for specified exercises."""
    print("\n--- Exercise Workload Change ---")
    for exercise_name in target_exercises:
        current_workload = current_week_exercise_workload.get(exercise_name, 0)
        previous_workload = previous_week_exercise_workload.get(exercise_name, 0)

        if previous_workload > 0:
            workload_change_percentage = ((current_workload - previous_workload) / previous_workload) * 100
            print(f"{exercise_name}: Workload change vs previous week: {workload_change_percentage:.2f}%")
            if workload_change_percentage > 0:
                print(f"  (Workload Increased)")
            elif workload_change_percentage < 0:
                print(f"  (Workload Decreased)")
            else:
                print(f"  (Workload Unchanged)")
        else:
            if current_workload > 0:
                print(f"{exercise_name}: Workload change vs previous week: Increase from 0 kg to {current_workload:.2f} kg (Percentage change: N/A - Previous week workload was 0)")
            else:
                print(f"{exercise_name}: Workload change vs previous week: No workload data for either week to compare.")


if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k" # Replace with your actual Gemini API key # REMOVED - not needed

    client_names = [
        "Shannon Birch",
    ]

    trainerize_bot = TrainerizeAutomation()
    all_workout_data = []

    # --- Date Range for Prompt ---  (RE-INTRODUCED Date Range)
    start_date_range = date(2025, 2, 24)  # Monday, February 24, 2025
    end_date_range = date(2025, 3, 2)    # Sunday, March 2, 2025
    date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}" # For display in print statements - DD/MM/YYYY
    date_range_start_prompt = start_date_range
    date_range_end_prompt = end_date_range

    # --- Previous Week Date Range ---
    previous_start_date_range = start_date_range - timedelta(weeks=1)
    previous_end_date_range = end_date_range - timedelta(weeks=1)
    previous_date_range_str_prompt = f"{previous_start_date_range.strftime('%d/%m/%Y')}-{previous_end_date_range.strftime('%d/%m/%Y')}"

    target_exercises = [
        "Barbell Bench Chest Press",
        "B.B Back Squat",
        "Lat Pull Down Wide Grip"
    ]


    # --- Set logging level to INFO ---
    logging.getLogger().setLevel(logging.INFO) # Set logging level to INFO for normal operation, no longer DEBUG


    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()

            for client_name in client_names:
                print(f"\n--- Starting workout data scrape for {client_name} ---")

                if trainerize_bot.navigate_to_client(client_name):
                    print("Navigated to client")
                    if trainerize_bot.click_progress_tab():
                        print("Clicked progress tab")
                        if trainerize_bot.click_review_by_workout().startswith("Successfully"):
                            print("Clicked review by workout")
                            workout_data_list_all = trainerize_bot.process_workouts()  # Get all workout data

                            # --- Calculate stats for current week and get workout data + exercise workload ---
                            current_week_workout_count, current_week_workout_names, current_week_weight, current_week_reps, current_week_sets, current_week_workout_data, current_week_exercise_workload = trainerize_bot.calculate_workout_stats_for_date_range(workout_data_list_all, date_range_start_prompt, date_range_end_prompt, target_exercises)

                            # --- Calculate stats for previous week and get workout data + exercise workload ---
                            previous_week_workout_count, previous_week_workout_names, previous_week_weight, previous_week_reps, previous_week_sets, previous_week_workout_data, previous_week_exercise_workload = trainerize_bot.calculate_workout_stats_for_date_range(workout_data_list_all, previous_start_date_range, previous_end_date_range, target_exercises)


                            print(f"\n--- Workout Summary (Selenium - Week of {date_range_str_prompt}): ---") # Updated print statement
                            print(f"Total workouts for week of {date_range_str_prompt}: {current_week_workout_count}")
                            if current_week_workout_names:
                                print(f"Workouts completed week of {date_range_str_prompt}:")
                                for workout_name in current_week_workout_names:
                                    print(f"- {workout_name}")
                            else:
                                print(f"No workouts completed for week of {date_range_str_prompt}.")

                            print(f"\n--- Totals for week of {date_range_str_prompt}: ---") # Updated print statement
                            print(f"Total Weight Lifted: {current_week_weight:.2f} kg") # Display weight with 2 decimal places
                            print(f"Total Reps Done: {current_week_reps}")
                            print(f"Total Sets Done: {current_week_sets}")

                            print(f"\n--- Workout Summary (Selenium - Week of {previous_date_range_str_prompt}): ---") # Previous week summary
                            print(f"Total workouts for week of {previous_date_range_str_prompt}: {previous_week_workout_count}")
                            print(f"\n--- Totals for week of {previous_date_range_str_prompt}: ---")
                            print(f"Total Weight Lifted: {previous_week_weight:.2f} kg")
                            print(f"Total Reps Done: {previous_week_reps}")
                            print(f"Total Sets Done: {previous_week_sets}")


                            # --- Calculate Workload Change (Weight Lifted) ---
                            if previous_week_weight > 0:
                                workload_change_percentage = ((current_week_weight - previous_week_weight) / previous_week_weight) * 100
                                print(f"\n--- Total Workload Change (Weight Lifted)---")
                                print(f"Workload change vs previous week: {workload_change_percentage:.2f}%")
                                if workload_change_percentage > 0:
                                    print("(Workload Increased)")
                                elif workload_change_percentage < 0:
                                    print("(Workload Decreased)")
                                else:
                                    print("(Workload Unchanged)")
                            else:
                                if current_week_weight > 0:
                                    print(f"\n--- Total Workload Change (Weight Lifted)---")
                                    print("Workload change vs previous week: Increase from 0 kg to {:.2f} kg (Percentage change: N/A - Previous week workload was 0)".format(current_week_weight))
                                else:
                                    print(f"\n--- Total Workload Change (Weight Lifted)---")
                                    print("Workload change vs previous week: No workload data for either week to compare.")

                            # --- Print Exercise Details ---
                            print_exercise_details(current_week_workout_data, previous_week_workout_data, target_exercises, date_range_str_prompt, previous_date_range_str_prompt)

                            # --- Calculate and Print Exercise Workload Change ---
                            calculate_exercise_workload_change(current_week_exercise_workload, previous_week_exercise_workload, target_exercises)


                        else:
                            print("Failed to click 'Review By Workout'")
                    else:
                        print("Failed to click 'Progress' tab")
                    trainerize_bot.navigate_back_to_clients_list()
                else:
                    print(f"Could not navigate to client: {client_name}")

        else:
            print("Login failed. Script aborted.")

    except Exception as e:
        logging.exception(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()


    input("Press Enter to close...")