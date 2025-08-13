from selenium import webdriver
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
from datetime import datetime, timedelta
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import csv
import re


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        # Correct paths to executables
        self.chromedriver_path = "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")

        # Temporary User Data Directory
        self.temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")

        # Standard Options
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Set Chrome executable location
        chrome_options.binary_location = self.chrome_executable_path

        try:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")

        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def handle_cookie_dialog(self):
        # Placeholder for cookie dialog handling (we're not actively clicking anything now)
        logging.info("Cookie dialog handling (placeholder - not clicking Accept).")
        time.sleep(2)  # Wait a bit for the dialog to appear

    def handle_notification_popup(self):
        """Handles the 'Get notifications?' popup by clicking 'Block'."""
        try:
            logging.info("Checking for and handling 'Get notifications?' popup...")
            # Find the 'Block' button and click it
            block_button_locator = (By.XPATH, "//button[contains(text(), 'Block')]")
            block_button = self.wait.until(EC.element_to_be_clickable(block_button_locator))
            block_button.click()
            logging.info("Clicked 'Block' on the notification popup.")
            time.sleep(1)  # Give the page a moment to update
            return True
        except Exception as e:
            logging.warning(f"Notification popup not found or failed to handle: {e}")
            return False  # It's okay if it's not found, we don't want to crash

    def login(self, username, password):
        """Logs into Trainerize, navigating directly to the login page."""
        try:
            logging.info("Navigating directly to Trainerize login page...")
            self.driver.get("https://www.trainerize.com/login.aspx")

            # Handle cookie dialog (just wait, no clicking)
            self.handle_cookie_dialog()

            # Scroll down slightly to move the "Find Me" button below the cookie popup
            logging.info("Scrolling down slightly to avoid cookie popup...")
            self.driver.execute_script("window.scrollBy(0, 200);")  # Scroll down 200 pixels
            time.sleep(1)  # Wait for the scrolling to complete

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
        """Navigates to the specified client's page, clicks 'Open', and switches to the new tab."""
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")

            # 1. Click the "Clients" link in the sidebar
            logging.info("Clicking the 'Clients' link in the sidebar...")
            clients_link_locator = (By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")  # Robust XPath
            try:
                clients_link = self.wait.until(EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            except TimeoutException as te:
                logging.error(f"TimeoutException while waiting for Clients link: {te.msg}")  # More informative message
                raise  # Re-raise the exception to stop execution

            time.sleep(2)

            # 2. Enter the client's name into the search bar on the Clients page
            logging.info("Entering client name into the search bar on the Clients page...")
            search_input_locator = (By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(EC.presence_of_element_located(search_input_locator))
            search_input.send_keys(client_name)
            time.sleep(1)  # Wait for the search results to load. Adjust if needed.

            # 3. Click on the client's name in the search results.
            logging.info("Clicking on the client's name in the search results...")
            client_link_locator = (By.XPATH, f"//a[contains(text(), '{client_name}')]")  # Find link by text
            client_link = self.wait.until(EC.element_to_be_clickable(client_link_locator))
            client_link.click()
            time.sleep(2)

            # 4. Click the "Open" button to switch into the client profile
            logging.info("Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)

            # Switch to the new tab
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle #Getting current window
            self.wait.until(EC.number_of_windows_to_be(2)) #Waiting for 2 windows
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break

            logging.info(f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True

        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False

    def click_progress_tab(self):
        """Clicks the 'Progress' tab on the client's page."""
        try:
            logging.info("Attempting to click the 'Progress' tab...")

            # Locate the Progress tab using XPath
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
            logging.error(f"An unexpected error occurred: {e}")
            return "Failed to click Progress tab (Unknown Error)"

    def click_review_by_workout(self):
        """Clicks the 'Review By Workout' link on the Progress page."""
        try:
            logging.info("Attempting to click the 'Review By Workout' link...")

            # Locate the "Review By Workout" link using XPath.  Target _self is also added.
            review_link_locator = (By.XPATH, "//a[@class='tz-sp section-link text-overflow-none' and @href='/app/client/7500641/progress/workout' and @target='_self']")
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
            logging.error(f"An unexpected error occurred: {e}")
            return "Failed to click 'Review By Workout' link (Unknown Error)"

    def process_workouts(self):
        """Gets workout data, clicks each workout, and processes details."""
        try:
            weekly_totals = []  # List to store data.
            processed_workouts = set()  # Keep track of processed workout keys (name, date)


            # --- Initial wait for the workout links ---
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))

            while True:  # Loop until no more *visible* workouts
                # --- Re-find workout links INSIDE the loop ---
                workout_links = self.driver.find_elements(By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                print(f"Found {len(workout_links)} workout links in this iteration")

                # --- Create a set of expected workout keys ONLY for unprocessed workouts ---
                expected_unprocessed_workouts = set()
                for link in workout_links:
                    try:
                        parent_row = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'baseGridRow')]")
                        date_element = parent_row.find_element(By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                        date_str = date_element.text.strip()
                        workout_name = link.text.strip()
                        workout_key = (workout_name, date_str)

                        # Only add to expected_unprocessed_workouts if NOT already processed
                        if workout_key not in processed_workouts:
                            expected_unprocessed_workouts.add(workout_key)
                    except NoSuchElementException:
                        print(f"Skipping a workout link due to missing date element.")
                        continue

                if not expected_unprocessed_workouts:
                    print("No more workouts to process in this iteration.")
                    break  # All *currently visible* workouts are processed


                for workout_name, date_str in expected_unprocessed_workouts:
                     # --- Find the link *again* using XPath, based on name and date ---
                    link_locator = (By.XPATH, f"//div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName' and text()='{workout_name}']/ancestor::div[contains(@class, 'baseGridRow')]//span[@data-testid='clientProgress-workouts-summaryGrid-date' and text()='{date_str}']/ancestor::div[contains(@class, 'baseGridRow')]//a[@data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                    try:
                        workout_link = self.driver.find_element(*link_locator)
                        print(f"Attempting to process: {workout_name} on {date_str}")
                        workout_data = self._process_single_workout(workout_link, workout_name, date_str)
                        if workout_data:
                            weekly_totals.append(workout_data)
                            processed_workouts.add((workout_name, date_str))  # Mark as processed

                    except NoSuchElementException:
                        print(f"Could not find link for {workout_name} on {date_str} - skipping (it might have been hidden).")
                        continue  # Move on to the next workout


            print("Exiting process_workouts loop")
            return weekly_totals

        except Exception as e:
            logging.error(f"Error during workout processing: {e}")
            return []

    def _process_single_workout(self, workout_link, workout_name, date_str):
        """Helper function to process a single workout link (click, analyze, go back)."""
        try:
            print(f"Processing workout: {workout_name} on {date_str}")


            # --- Calculate Week Start Date based on workout date ---
            try:
                workout_date = datetime.strptime(date_str, "%Y-%m-%d")
                week_start_date = workout_date - timedelta(days=workout_date.weekday())
                week_start_date_str = week_start_date.strftime("%Y-%m-%d")  # For consistency
            except ValueError:
                print(f"Invalid date format: {date_str}, using current week start.")
                today = datetime.today()
                week_start_date = today - timedelta(days=today.weekday())
                week_start_date_str = week_start_date.strftime("%Y-%m-%d")

            # --- Skip "Saturday" workout ---
            if workout_name.lower() == "saturday":
                print("Skipping details for 'Saturday' workout, counting as completed.")
                return {
                    "WeekStartDate": week_start_date.date(),  # Use date object
                    "Workout": workout_name,
                    "TotalWeight": 0,
                    "TotalReps": 0,
                    "TotalSets": 0,
                    "Completed": 1,
                    'Exercises': {} #Added the exercise section
                }

            # --- Click the workout name ---
            workout_link.click()

            # --- Analyze workout details (on the new page, same tab) ---
            workout_totals = self.analyze_workout_details()
            workout_totals["WeekStartDate"] = week_start_date.date()  # Use date object
            workout_totals["Workout"] = workout_name
            workout_totals["Completed"] = 1

            # --- Go back to the workout list page ---
            print("Going back to previous page")
            self.driver.back()
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))
            print("Back on workout list page")
            return workout_totals

        except Exception as e:
            logging.error(f"Error processing workout link: {e}")
            return None

    def analyze_workout_details(self):
        """Extracts and processes workout details, including individual exercise data."""
        try:
            # --- WAIT for a key element ---
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.commentsHeader")))

            # --- Get the dates from the header row ---
            date_headers = self.driver.find_elements(By.CSS_SELECTOR,
                                                     "thead.ant-table-thead th.ant-table-align-center span.ant-table-column-title")
            dates = [date_header.text.strip() for date_header in date_headers]

            # --- Initialize totals and exercise data ---
            total_weight = 0
            total_reps = 0
            total_sets = 0
            exercises_data = {}  # Dictionary to store per-exercise data

            # --- Find all exercise name cells ---
            exercise_name_cells = self.driver.find_elements(By.CSS_SELECTOR,
                                                             "td.ant-table-row-cell-break-word[rowspan][style*='color: rgb(34, 158, 212)']")

            for exercise_index, exercise_cell in enumerate(exercise_name_cells):
                exercise_name = exercise_cell.text.strip()
                print(f"Processing exercise: {exercise_name}")

                rowspan = int(exercise_cell.get_attribute("rowspan"))
                current_row = exercise_cell.find_element(By.XPATH, "./ancestor::tr")

                # Initialize exercise entry if not already present
                if exercise_name not in exercises_data:
                    exercises_data[exercise_name] = {
                        'sets': [],  # List to store individual set data
                        'TotalWeight': 0, #Adding Total Weight Count
                        'TotalReps': 0 #Adding Total Reps Count
                    }


                for set_num in range(rowspan):
                    if current_row is None:
                        break

                    set_entries_in_row = current_row.find_elements(By.CSS_SELECTOR, "td.commentsHeader")

                    for date_index, set_entry in enumerate(set_entries_in_row):
                        set_text = set_entry.text.strip()

                        match = re.match(r"(\d+)\s*X\s*([\d.-]*)\s*kg", set_text, re.IGNORECASE)
                        if match:
                            reps_str, weight_str = match.groups()
                            try:
                                reps = int(reps_str)
                                weight = float(weight_str) if weight_str else 0.0
                                total_weight += weight * reps
                                total_reps += reps
                                total_sets += 1

                                current_date = dates[date_index % len(dates)] if dates else "No Date"
                                print(f"    Set: {set_num + 1}, Reps: {reps}, Weight: {weight}, Date: {current_date}")

                                # Store set data for the exercise
                                exercises_data[exercise_name]['sets'].append({'reps': reps, 'weight': weight, 'date': current_date})
                                exercises_data[exercise_name]['TotalWeight'] += weight * reps #Adding to the total
                                exercises_data[exercise_name]['TotalReps'] += reps #Adding to the total

                            except ValueError:
                                print(f"    Could not parse reps or weight: {set_text}")
                        elif set_text and "SET" not in set_text.upper():
                            print(f"    Skipping unparsable data: '{set_text}'")

                    try:
                        exercise_row_again = exercise_cell.find_element(By.XPATH, "./ancestor::tr")
                        current_row = exercise_row_again.find_element(By.XPATH, "./following-sibling::tr")
                    except NoSuchElementException:
                        current_row = None
                        break

            return {
                "TotalWeight": total_weight,
                "TotalReps": total_reps,
                "TotalSets": total_sets,
                "Exercises": exercises_data  # Include exercise data
            }

        except Exception as e:
            logging.error(f"Error analyzing workout details: {e}")
            return {"TotalWeight": 0, "TotalReps": 0, "TotalSets": 0, "Exercises": {}}

    def cleanup(self):
        """Cleans up resources (removes temp dir, but doesn't close driver)."""
        try:
            # Do NOT close the driver here.
            #if hasattr(self, 'driver') and self.driver.quit()
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            logging.info("Cleanup completed successfully (except driver).")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

def read_workout_data_from_csv(filename="workout_data.csv"):
    """Reads weekly workout totals and exercise data from a CSV file."""
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = []
            for row in reader:
                try:
                    week_start_date = datetime.strptime(row['WeekStartDate'], "%Y-%m-%d").date()
                    total_weight = float(row["TotalWeight"])
                    total_reps = int(row["TotalReps"])
                    total_sets = int(row["TotalSets"])
                    completed = int(row.get("Completed", 0))

                    # Read exercise data (stored as a string representation of a dictionary)
                    exercises_str = row.get("Exercises", "{}")
                    try:
                        exercises = eval(exercises_str)  # Safely evaluate the string as a dictionary
                    except Exception as e:
                        print(f"Error parsing exercises data: {e}, using empty dict.")
                        exercises = {}


                    data.append({
                        "WeekStartDate": week_start_date,
                        "TotalWeight": total_weight,
                        "TotalReps": total_reps,
                        "TotalSets": total_sets,
                        "Completed": completed,
                        "Exercises" : exercises #Added the exercise part
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error processing row in CSV: {row}, {e}")
                    continue
            print(f"CSV Data Read: {data}")
            return data

    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

def write_workout_data_to_csv(data, filename="workout_data.csv"):
    """Writes weekly workout totals and exercise data to a CSV file."""
    if not data:
        return

    fieldnames = ["WeekStartDate", "TotalWeight", "TotalReps", "TotalSets", "Completed", "Exercises"] #Added exercises
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                row_copy = row.copy()
                row_copy['WeekStartDate'] = row_copy['WeekStartDate'].strftime("%Y-%m-%d")
                # Convert exercises data to string representation before writing
                row_copy['Exercises'] = str(row_copy.get('Exercises', {}))
                writer.writerow(row_copy)
        print("CSV Data Updated")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == '__main__':
    username = "shannonbirch@cocospersonaltraining.com"  # Replace with your username
    password = "cyywp7nyk"  # Replace with your password
    client_name = "Shannon Birch"  # Make sure this is the EXACT name as it appears

    trainerize_bot = TrainerizeAutomation()
    try:
        if trainerize_bot.login(username, password):
            logging.info("Login successful.")
            trainerize_bot.handle_notification_popup()

            logging.info("Now navigating to client...")
            if trainerize_bot.navigate_to_client(client_name):

                progress_status = trainerize_bot.click_progress_tab()
                logging.info(progress_status)

                if progress_status.startswith("Successfully"):
                    review_status = trainerize_bot.click_review_by_workout()
                    logging.info(review_status)

                    if review_status.startswith("Successfully"):
                        # Process workouts (click, extract details)
                        weekly_data = trainerize_bot.process_workouts()

                        if weekly_data:
                            # --- Group workout data by week ---
                            weekly_totals_by_week = {}
                            for workout in weekly_data:
                                week_start = workout["WeekStartDate"]
                                if week_start not in weekly_totals_by_week:
                                    weekly_totals_by_week[week_start] = {
                                        "WeekStartDate": week_start,
                                        "TotalWeight": 0,
                                        "TotalReps": 0,
                                        "TotalSets": 0,
                                        "Completed": 0,
                                        "Exercises": {}  # Initialize exercise data
                                    }
                                weekly_totals_by_week[week_start]["TotalWeight"] += workout.get("TotalWeight", 0)
                                weekly_totals_by_week[week_start]["TotalReps"] += workout.get("TotalReps", 0)
                                weekly_totals_by_week[week_start]["TotalSets"] += workout.get("TotalSets", 0)
                                weekly_totals_by_week[week_start]["Completed"] += workout.get("Completed", 0)

                                # Combine exercise data, handling duplicates within the week
                                for exercise_name, exercise_data in workout.get("Exercises", {}).items():
                                    if exercise_name not in weekly_totals_by_week[week_start]["Exercises"]:
                                         weekly_totals_by_week[week_start]["Exercises"][exercise_name] = {
                                            'sets': [],
                                            'TotalWeight': 0,
                                            'TotalReps': 0
                                        }
                                     # Add the sets to the weekly total
                                    weekly_totals_by_week[week_start]["Exercises"][exercise_name]['sets'].extend(exercise_data['sets'])
                                    weekly_totals_by_week[week_start]["Exercises"][exercise_name]['TotalWeight'] += exercise_data['TotalWeight']
                                    weekly_totals_by_week[week_start]["Exercises"][exercise_name]['TotalReps'] += exercise_data['TotalReps']


                            # --- Convert the dictionary to a list of dictionaries ---
                            grouped_weekly_data = list(weekly_totals_by_week.values())

                            # --- Read previous week's data from CSV ---
                            previous_weeks_data = read_workout_data_from_csv()
                            print(f"Previous Weeks Data BEFORE COMBINE: {previous_weeks_data}") # DEBUG PRINT

                            # --- Combine with existing data, handling duplicates ---
                            for week_data in grouped_weekly_data:
                                # Check if the week already exists in the CSV data
                                existing_week = next((item for item in previous_weeks_data if item["WeekStartDate"] == week_data["WeekStartDate"]), None)
                                if existing_week:
                                    # Update the existing week's data
                                    existing_week.update(week_data)
                                else:
                                    # Add the new week's data
                                    previous_weeks_data.append(week_data)

                            print(f"Previous Weeks Data AFTER COMBINE: {previous_weeks_data}") # DEBUG PRINT


                            # --- Sort by date ---
                            previous_weeks_data.sort(key=lambda x: x["WeekStartDate"])
                            print(f"Previous Weeks Data AFTER SORT: {previous_weeks_data}") # DEBUG PRINT


                            # --- Write ALL data to CSV ---
                            write_workout_data_to_csv(previous_weeks_data)
                            print("CSV Data Updated")

                            # --- Define week start dates for comparison ---
                            current_week_start_date = datetime(2025, 2, 17).date()
                            previous_week_start_date = datetime(2025, 2, 10).date()
                            current_week_end_date = current_week_start_date + timedelta(days=6)
                            previous_week_end_date = previous_week_start_date + timedelta(days=6)

                            # --- Filter data for the target week for "Completed Workouts" count ---
                            target_week_start = datetime(2025, 2, 17).date()
                            target_week_end = datetime(2025, 2, 23).date()
                            filtered_weekly_data_for_count = [
                                week_entry for week_entry in grouped_weekly_data
                                if target_week_start <= week_entry['WeekStartDate'] <= target_week_end
                            ]

                            # --- Calculate total completed workouts for the target week ---
                            total_workouts_target_week = sum(week_entry['Completed'] for week_entry in filtered_weekly_data_for_count)


                            # --- Find week entries by date ---
                            current_week_entry = None
                            previous_week_entry = None

                            for week_entry in previous_weeks_data:
                                print(f"Checking week: {week_entry['WeekStartDate']}") # DEBUG PRINT
                                if week_entry['WeekStartDate'] == current_week_start_date:
                                    current_week_entry = week_entry
                                    print(f"  Found Current Week Entry: {current_week_entry['WeekStartDate']}") # DEBUG PRINT
                                elif week_entry['WeekStartDate'] == previous_week_start_date:
                                    previous_week_entry = week_entry
                                    print(f"  Found Previous Week Entry: {previous_week_entry['WeekStartDate']}") # DEBUG PRINT

                            # --- Find and compare with the PREVIOUS week ---
                            if current_week_entry and previous_week_entry:


                                # --- Calculate Best Exercise ---
                                best_exercise = None
                                for exercise_name, exercise_data in current_week_entry['Exercises'].items():
                                    prev_exercise_data = previous_week_entry['Exercises'].get(exercise_name)
                                    if prev_exercise_data:
                                        weight_diff = exercise_data['TotalWeight'] - prev_exercise_data['TotalWeight']
                                        print(f"Exercise: {exercise_name}, Weight Diff: {weight_diff}") # Debug print
                                        if weight_diff > 0: # Check for WEIGHT INCREASE, not overall score
                                            best_exercise = (exercise_name, weight_diff, exercise_data['TotalWeight'], prev_exercise_data['TotalWeight']) # Store weight values for output
                                            break # Stop after finding the first exercise with weight increase


                                # --- Dot-Point Analysis Output ---
                                print("\n--- Weekly Workout Analysis ---")
                                print(f"Comparing Week: {current_week_start_date.strftime('%d-%b')} to {current_week_end_date.strftime('%d-%b')} VS Week: {previous_week_start_date.strftime('%d-%b')} to {previous_week_end_date.strftime('%d-%b')}") # Date Labels Added

                                print(f"  * **Total Weight Lifted:**")
                                if current_week_entry['TotalWeight'] > previous_week_entry['TotalWeight']:
                                    print(f"    ⬆️ Increased by {current_week_entry['TotalWeight'] - previous_week_entry['TotalWeight']:.2f} kg ({current_week_entry['TotalWeight']:.2f} kg vs. {previous_week_entry['TotalWeight']:.2f} kg) - *Focus: Strength Gains!*")
                                elif current_week_entry['TotalWeight'] < previous_week_entry['TotalWeight']:
                                    print(f"    ⬇️ Decreased by {previous_week_entry['TotalWeight'] - current_week_entry['TotalWeight']:.2f} kg ({current_week_entry['TotalWeight']:.2f} kg vs. {previous_week_entry['TotalWeight']:.2f} kg) - *Focus: Consistency & Form.*")
                                else:
                                    print(f"    ↔️ Remained consistent ({current_week_entry['TotalWeight']:.2f} kg) - *Focus: Maintenance, Technique Refinement.*")


                                print(f"  * **Total Reps:**")
                                if current_week_entry['TotalReps'] > previous_week_entry['TotalReps']:
                                    print(f"    ⬆️ Increased by {current_week_entry['TotalReps'] - previous_week_entry['TotalReps']} reps ({current_week_entry['TotalReps']} vs. {previous_week_entry['TotalReps']}) - *Focus: Endurance Improvement!*")
                                elif current_week_entry['TotalReps'] < previous_week_entry['TotalReps']:
                                    print(f"    ⬇️ Decreased by {previous_week_entry['TotalReps'] - current_week_entry['TotalReps']} reps ({current_week_entry['TotalReps']} vs. {previous_week_entry['TotalReps']}) - *Focus: Form & Controlled Movements.*")
                                else:
                                    print(f"    ↔️ Remained consistent ({current_week_entry['TotalReps']} reps) - *Focus: Maintaining Effort, Weight Progression.*")

                                print(f"  * **Total Sets:**")
                                if current_week_entry['TotalSets'] > previous_week_entry['TotalSets']:
                                    print(f"    ⬆️ Increased by {current_week_entry['TotalSets'] - previous_week_entry['TotalSets']} sets ({current_week_entry['TotalSets']} vs. {previous_week_entry['TotalSets']}) - *Focus: Increased Training Volume!*")
                                elif current_week_entry['TotalSets'] < previous_week_entry['TotalSets']:
                                    print(f"    ⬇️ Decreased by {previous_week_entry['TotalSets'] - current_week_entry['TotalSets']} sets ({current_week_entry['TotalSets']} vs. {previous_week_entry['TotalSets']}) - *Focus: Quality over Quantity, Intensity.*")
                                else:
                                    print(f"    ↔️ Remained consistent ({current_week_entry['TotalSets']} sets) - *Focus: Maintaining Volume, Form Perfection.*")

                                print(f"  * **Completed Workouts (17th-23rd Feb 2025):**") # Updated section title
                                print(f"    {total_workouts_target_week} Workouts Completed - *Focus: Commitment & Consistency!*") # Display filtered count


                                print(f"\n  * **Long Term Trends:**")
                                if len(previous_weeks_data) > 3: # Changed condition to > 3
                                     three_weeks_ago_start_date = current_week_start_date - timedelta(weeks=3)
                                     three_weeks_ago_entry = None
                                     for week_entry in previous_weeks_data:
                                        if week_entry['WeekStartDate'] == three_weeks_ago_start_date:
                                            three_weeks_ago_entry = week_entry
                                            break
                                     if three_weeks_ago_entry:
                                        print(f"      Compared to Week of {three_weeks_ago_start_date.strftime('%d-%b')}: Total Weight {'⬆️ Increased' if current_week_entry['TotalWeight'] > three_weeks_ago_entry['TotalWeight'] else '⬇️ Decreased' if current_week_entry['TotalWeight'] < three_weeks_ago_entry['TotalWeight'] else '↔️ Maintained'} | Reps {'⬆️ Increased' if current_week_entry['TotalReps'] > three_weeks_ago_entry['TotalReps'] else '⬇️ Decreased' if current_week_entry['TotalReps'] < three_weeks_ago_entry['TotalReps'] else '↔️ Maintained' }") # Updated text to "3 weeks ago"
                                     else:
                                        print("        Collecting More Data for long term trends (3 weeks ago data not found)")

                                else:
                                    print("        Collecting More Data for long term trends")


                                # Best Exercise Output
                                if best_exercise:
                                    print("\n  * **Most Improved Exercise:**")
                                    print(f"    - {best_exercise[0]}: Weight Increased by {best_exercise[1]:.2f} kg ({best_exercise[2]:.2f} kg vs. {best_exercise[3]:.2f} kg)") # Updated output to show weight increase and values
                                else:
                                    print("\n  * **Most Improved Exercise:** No significant improvement this week.  Focus on consistent effort!")

                            else:
                                print("Not enough data to compare with a previous week (or data for one of the weeks is missing).")
                                if current_week_entry:
                                  print(f"This Week ({current_week_entry['WeekStartDate'].strftime('%Y-%m-%d')}):")
                                  print(f"  Total Weight: {current_week_entry['TotalWeight']} kg")
                                  print(f"  Total Reps: {current_week_entry['TotalReps']}")
                                  print(f"  Total Sets: {current_week_entry['TotalSets']}")
                                  print(f"  Total Completed: {current_week_entry['Completed']}")
                        else:
                            print("Could not retrieve workout data from HTML.")
                else:
                    logging.error("Cannot proceed to 'Review By Workout' without clicking 'Progress'.")
            else:
                logging.error("Failed to navigate to client.")
            input("Press Enter to close the browser...")  # Keep browser open
        else:
            logging.error("Login failed.  Cannot proceed to client navigation.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # trainerize_bot.cleanup()  # Ensure cleanup always happens - REMOVED to keep it open.
        logging.info("Script complete.")