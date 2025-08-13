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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException, InvalidSessionIdException
import re
import base64
import csv

class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO,
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
        """Gets workout data, processes workout details, NORMALIZED NAME, NO LOOP."""
        try:
            workout_data_list = []
            processed_workouts = set()  # Keep track of processed workout keys (normalized name)
            workout_retry_counts = {}

            self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))

            workout_links = self.driver.find_elements(
                By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
            print(f"Found {len(workout_links)} workout links") # Log - total workout links found


            expected_unprocessed_workouts = set()
            for link in workout_links:
                try:
                    parent_row = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'baseGridRow')]")
                    date_element = parent_row.find_element(
                        By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                    date_str = date_element.text.strip()
                    workout_name = link.text.strip()
                    # Normalize workout name (remove " 2" or similar suffixes for duplication check)
                    normalized_workout_name = re.sub(r'(\s+\d+)?$', '', workout_name).strip() # Remove trailing space and digits
                    workout_key = normalized_workout_name # Use normalized name as key

                    if workout_key not in processed_workouts:
                        expected_unprocessed_workouts.add((workout_name, date_str, workout_key)) # Store original name, date, and normalized key
                    else:
                        print(f"Workout '{workout_name}' with Key '{workout_key}' ALREADY in expected_unprocessed_workouts (Skipping add to expected_unprocessed_workouts)") # Log - Already Expected
                except NoSuchElementException:
                    print(f"Skipping a workout link due to missing date element.")
                    continue

            print(f"Expected Unprocessed Workouts (Names only): {[item[0] for item in expected_unprocessed_workouts]}") # Log expected unprocessed workout names
            print(f"Processed Workouts Set BEFORE Processing Loop: {processed_workouts}") # Log processed_workouts set BEFORE loop


            workouts_to_process_this_iteration = list(expected_unprocessed_workouts) # Create list here for clarity - DEBUG
            print(f"Workouts to Process (Names only): {[item[0] for item in workouts_to_process_this_iteration]}") # Log workouts to process - DEBUG

            for workout_tuple_index, workout_tuple in enumerate(workouts_to_process_this_iteration): # Added tuple index for debugging
                workout_name, date_str, workout_key = workout_tuple
                print(f"\n  Tuple Index {workout_tuple_index}: Processing workout: '{workout_name}', Date: '{date_str}', Normalized Key: '{workout_key}'") # DEBUG - Tuple Index and Workout Info
                print(f"  Tuple Index {workout_tuple_index}: Checking if Normalized Key '{workout_key}' in processed_workouts: {processed_workouts}") # DEBUG - Before Processed Check

                if workout_key in processed_workouts:  # Check against normalized key
                    print(f"  Tuple Index {workout_tuple_index}: Skipping DUPLICATE workout (normalized name already processed): {workout_name} on {date_str}, Normalized Key: {workout_key}")
                    continue
                else:
                    print(f"  Tuple Index {workout_tuple_index}: Workout with Normalized Key '{workout_key}' NOT yet processed. Proceeding to process.") # DEBUG - Not Duplicate

                link_locator = (By.XPATH,
                                f"//div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName' and text()='{workout_name}']/ancestor::div[contains(@class, 'baseGridRow')]//span[@data-testid='clientProgress-workouts-summaryGrid-date' and text()='{date_str}']/ancestor::div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                try:
                    workout_link = self.driver.find_element(*link_locator)
                    print(f"  Tuple Index {workout_tuple_index}: Attempting to process workout link for: {workout_name} on {date_str}, Normalized Key: {workout_key}")
                    workout_data_formatted = self._process_single_workout(workout_link, workout_name, date_str)
                    if workout_data_formatted:
                        workout_data_list.append(workout_data_formatted)
                        processed_workouts.add(workout_key)  # Add normalized key to processed set
                        print(f"  Tuple Index {workout_tuple_index}: Added workout with normalized key '{workout_key}' to processed_workouts set. Current set: {processed_workouts}") # Log addition with normalized key
                        if workout_key in workout_retry_counts:
                            del workout_retry_counts[workout_key]

                except NoSuchElementException:
                    retry_count = workout_retry_counts.get(workout_key, 0)
                    workout_retry_counts[workout_key] = retry_count + 1
                    print(
                        f"  Tuple Index {workout_tuple_index}: Could not find link for {workout_name} on {date_str} - retry count: {retry_count + 1}, Normalized Key: {workout_key}")

                    if retry_count >= 10:
                        print(f"  Tuple Index {workout_tuple_index}: Skipping workout {workout_name} on {date_str} after 10 retries. Normalized Key: {workout_key}")
                        processed_workouts.add(workout_key)
                        expected_unprocessed_workouts.remove(workout_tuple) # Remove tuple
                        continue
                    else:
                        continue
            print(f"Processed workouts set at END: {processed_workouts}") # Log processed set at END

            print("Exiting process_workouts function") # Changed log message
            return workout_data_list

        except Exception as e:
            logging.exception(f"Error during workout processing: {e}")
            return []

    def _process_single_workout(self, workout_link, workout_name, date_str):
        """Helper function to process a single workout link (click, analyze, go back)."""
        try:
            print(f"Processing workout: {workout_name} on {date_str}")

            if workout_name.lower() == "saturday":
                print(f"Skipping details for 'Saturday' workout, counting as completed.")
                return f"{workout_name} - {date_str}\nWorkout Completed (No details scraped)"

            # --- Click the workout name ---
            workout_link.click()
            time.sleep(2)

            # --- Analyze workout details (on the new page, same tab) ---
            formatted_workout_data = self.analyze_workout_details_stripped(workout_name, date_str)

            # --- Go back to the workout list page ---
            print("Going back to previous page")
            self.driver.back()
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))
            print("Back on workout list page")
            return formatted_workout_data

        except Exception as e:
            logging.exception(f"Error processing workout link: {e}")
            return None

    def analyze_workout_details_stripped(self, workout_name, date_str):
        """Extracts workout details and formats them as requested."""
        try: # Added try block here
            logging.info("Starting analyze_workout_details_stripped function...")
            workout_output = f"{workout_name} - {date_str}\n"

            # --- WAIT for the table body element ---
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.ant-table-tbody")))
            logging.info("Table body element found (stripped).")

            rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody.ant-table-tbody > tr.ant-table-row")
            logging.info(f"Number of table rows found (stripped): {len(rows)}")

            current_exercise_name = None
            for row_index, row in enumerate(rows):
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                if not cells or len(cells) < 2: # Ensure there are enough cells
                    continue

                exercise_cells_in_row = row.find_elements(By.CSS_SELECTOR, "td.ant-table-fixed-columns-in-body.clickable.ant-table-row-cell-break-word[rowspan][style*='color: rgb(34, 158, 212)']")
                if exercise_cells_in_row:
                    exercise_cell = exercise_cells_in_row[0]
                    exercise_name = exercise_cell.text.strip()
                    if current_exercise_name: # Add newline if new exercise after previous exercise sets
                        workout_output += "\n"
                    workout_output += f"{exercise_name}\n"
                    current_exercise_name = exercise_name
                elif current_exercise_name:
                    set_cells_in_row = row.find_elements(By.CSS_SELECTOR, "td.ant-table-fixed-columns-in-body.ant-table-row-cell-break-word[style*='text-align: center; font-size: 12px;']")
                    set_cell = set_cells_in_row[0] if set_cells_in_row else None
                    data_cells = cells[2:] if len(cells) > 2 else []

                    if set_cell and "SET" in set_cell.text.upper():
                        set_num_text = set_cell.text.strip()
                        for set_index, data_cell in enumerate(data_cells):
                            set_text = data_cell.text.strip()
                            if not set_text:
                                continue
                            match = re.match(r"(\d+)\s*X\s*([\d.-]*)\s*(?:kg)?", set_text, re.IGNORECASE)
                            if match:
                                reps_str, weight_str = match.groups()
                                try:
                                    reps = int(reps_str)
                                    weight = float(weight_str) if weight_str and weight_str != '-' else 0.0
                                    set_line = f"set {set_index + 1} {reps} {weight}kg\n"
                                    workout_output += set_line
                                except ValueError:
                                    logging.warning(f"ValueError parsing set data (stripped): {set_text}")

            logging.info("Exiting analyze_workout_details_stripped function - Data extraction complete.")
            return workout_output

        except Exception as e: # Added except block here
            logging.exception(f"Error analyzing workout details (stripped): {e}")
            return "Error scraping workout details." # Return error string


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


if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"  # replace with your actual username
    password = "cyywp7nyk"  # replace with your actual password

    client_names = [
        "Shannon Birch",  # Only process Shannon Birch
    ]

    trainerize_bot = TrainerizeAutomation()
    all_workout_data = []

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
                            workout_data_list = trainerize_bot.process_workouts()
                            if workout_data_list:
                                all_workout_data.extend(workout_data_list)
                                print("\n--- Workout Data Scraped ---")
                                for workout_string in workout_data_list:
                                    print(workout_string)
                                    print("-" * 20) # Separator between workouts

                                # --- Calculate workouts completed in the latest week ---
                                if workout_data_list:
                                    latest_week_start_date = None
                                    workouts_this_week_count = 0

                                    # Assuming date is always in YYYY-MM-DD format in workout_data_list strings
                                    for workout_string in workout_data_list:
                                        match = re.search(r'- (\d{4}-\d{2}-\d{2})', workout_string)
                                        if match:
                                            workout_date_str = match.group(1)
                                            workout_date = datetime.strptime(workout_date_str, "%Y-%m-%d").date()

                                            if latest_week_start_date is None:
                                                latest_week_start_date = workout_date - timedelta(days=workout_date.weekday())

                                            week_start_date = workout_date - timedelta(days=workout_date.weekday())
                                            if week_start_date == latest_week_start_date:
                                                workouts_this_week_count += 1

                                    if latest_week_start_date:
                                        print(f"\nWorkouts completed in the week starting {latest_week_start_date.strftime('%Y-%m-%d')}: {workouts_this_week_count}")
                                    else:
                                        print("\nNo workout dates found to determine the latest week.")
                                else:
                                    print("\nNo workout data scraped.")

                            else:
                                print("No workout data scraped.")
                        else:
                            print("Failed to click 'Review By Workout'")
                    else:
                        print("Failed to click 'Progress' tab")
                    trainerize_bot.navigate_back_to_clients_list() # Navigate back after processing client
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