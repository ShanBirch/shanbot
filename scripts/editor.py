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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='{asctime} - {levelname} - {message}', style='{')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"

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

    def navigate_to_training_program(self):
        """Navigates to the 'Training Program' tab."""
        try:
            logging.info("Navigating to the 'Training Program' tab...")
            training_program_link_locator = (By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']")
            training_program_link = self.wait.until(EC.element_to_be_clickable(training_program_link_locator))
            training_program_link.click()
            time.sleep(2)  # Wait for the page to load
            logging.info("Successfully navigated to the 'Training Program' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error navigating to the 'Training Program' tab: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def find_current_workout_program(self):
        """Finds and returns the name of the current workout program, if any."""
        try:
            logging.info("Looking for the current workout program...")
            current_program_indicator_locator = (By.CLASS_NAME, "section-userProgramTrainingPhase-current")
            try:
                current_program_indicator = self.wait.until(EC.presence_of_element_located(current_program_indicator_locator))
                logging.info("Found element with class 'section-userProgramTrainingPhase-current'")
                # Log the outer HTML of the element to inspect its structure
                logging.info(f"HTML of current_program_indicator: {current_program_indicator.get_attribute('outerHTML')}")

                # Go to the parent div, then find the program name WITHIN that div
                program_name_element = current_program_indicator.find_element(By.XPATH, "./preceding-sibling::p[@class='tz-sp color--black text-overflow-none']")
                program_name = program_name_element.text
                logging.info("Current workout program found: %s", program_name)
                return program_name

            except NoSuchElementException as e:
                logging.warning(f"NoSuchElementException while finding program name: Check the XPath to locate the program name element. - {e}")
                logging.warning("Check the XPath to locate the program name element.")
                return None
            except Exception as e:
                logging.error(f"Error finding program name: {e}")
                logging.error(f"Specific error: {e}")
                return None

        except (TimeoutException, NoSuchElementException) as e:
            logging.info("No current workout program found (Timeout or element not found).")
            return None  # No current program found
        except Exception as e:
            logging.error(f"Error finding current workout program: {e}")
            return None

    def click_workout(self, workout_name):
        """Clicks on a workout with the specified name."""
        try:
            logging.info(f"Clicking on workout: {workout_name}")
            # The key is to target the *link* (<a> tag) that contains the <p> tag with the workout name.
            workout_locator = (By.XPATH, f"//a[.//p[@class='tz-lp color--blue pr8' and @data-testid='workoutGrid-workoutName-backAndTriceps' and text()='{workout_name}']]")

            workout_element = self.wait.until(EC.element_to_be_clickable(workout_locator))
            workout_element.click()
            time.sleep(2)
            logging.info("Successfully clicked on workout: {workout_name}")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error clicking on workout '{workout_name}': {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def click_edit_workout(self):
        """Clicks the 'Edit workout' button and then selects 'Workout Builder' from the dropdown."""
        try:
            logging.info("Clicking the 'Edit workout' button...")
            edit_button_locator = (By.XPATH, "//button[@title='Edit workout' and @data-testid='workoutDetail-editButton']")
            edit_button = self.wait.until(EC.element_to_be_clickable(edit_button_locator))
            edit_button.click()
            time.sleep(1)  # Wait for the dropdown to appear

            logging.info("Selecting 'Workout Builder' from the dropdown...")
            workout_builder_locator = (By.XPATH, "//li[@data-testid='dropdownButton-menuItem-workoutBuilder' and @role='menuitem']//p[text()='Workout Builder']")
            workout_builder_link = self.wait.until(EC.element_to_be_clickable(workout_builder_locator))
            workout_builder_link.click()
            time.sleep(2)

            logging.info("Successfully clicked the 'Edit workout' button and selected 'Workout Builder'.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error clicking the 'Edit workout' button or selecting 'Workout Builder': {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def remove_exercise(self, exercise_name):
        """Removes an exercise with the specified name from the workout by dragging the hamburger off-screen."""
        try:
            logging.info(f"Removing exercise: {exercise_name} by dragging...")

            # Scroll to the exercise within the scrollable container
            logging.info(f"Scrolling to exercise: {exercise_name}...")
            scroll_to_exercise_script = """
            const exerciseName = arguments[0];
            const scrollContainer = document.querySelector('.exerciseList.fullContent.flex-left.flex-column'); //scrollable div

            if (scrollContainer) {
                const exerciseDivs = scrollContainer.querySelectorAll('.workoutExercise.flex-left.flex-row.flex-align-center.flex-noShrink.fullWidth');
                let targetDiv = null;

                // Find the *last* div with the matching title
                for (let i = exerciseDivs.length - 1; i >= 0; i--) {
                    const titleDiv = exerciseDivs[i].querySelector('.exerciseList-exercise__name');
                    if (titleDiv && titleDiv.title === exerciseName) {
                        targetDiv = exerciseDivs[i];
                        break;
                    }
                }

                if (targetDiv) {
                   // Check if element is already visible.
                   if (targetDiv.getBoundingClientRect().top >= 0 &&
                       targetDiv.getBoundingClientRect().bottom <= (window.innerHeight || document.documentElement.clientHeight)) {
                       console.log("Element is already visible.");
                   } else {
                        targetDiv.scrollIntoView({behavior: "smooth", block: "center"});
                   }

                } else {
                    console.error("Element with matching exercise name was not found.")
                }
            } else {
                console.error("Scrollable container not found!");
            }
            """
            self.driver.execute_script(scroll_to_exercise_script, exercise_name)
            time.sleep(2)  # Allow time to scroll
            logging.info(f"Scrolled to exercise: {exercise_name}.")

            # Locate the hamburger icon for the specified exercise
            hamburger_locator = (By.XPATH, f"//div[@class='exerciseList-exercise__name ' and @title='{exercise_name}']"
                                            f"/ancestor::div[@class='workoutExercise flex-left flex-row flex-align-center flex-noShrink fullWidth']"
                                            f"//div[@data-testid='workoutBuilder-hamburgerMenu']")

            try:
                hamburger = self.wait.until(EC.element_to_be_clickable(hamburger_locator))
            except TimeoutException as e:
                logging.warning(f"Hamburger icon for '{exercise_name}' not found after scrolling.  It may not exist: {e}")
                return False  # Exercise not found, so cannot remove it

            # Perform the drag-and-drop action
            actions = ActionChains(self.driver)
            actions.click_and_hold(hamburger).move_by_offset(500, 0).release().perform()  # Drag 500 pixels to the right

            time.sleep(2)  # Allow time for the action to complete

            logging.info("Successfully removed exercise: {exercise_name} by dragging.")
            return True

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error removing exercise '{exercise_name}' by dragging: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while dragging: {e}")
            return False

    def add_exercise(self, exercise_name, sets="5", reps="12"):
        """Adds an exercise to the workout and sets the sets/reps."""
        try:
            logging.info(f"Adding exercise: {exercise_name}...")

            # Click the search bar
            search_bar_locator = (By.XPATH, "//span[@class='component__searchInput flex-left flex-align-center ant-input-affix-wrapper']")
            search_bar = self.wait.until(EC.element_to_be_clickable(search_bar_locator))
            search_bar.click()
            logging.info("Clicked the exercise search bar.")

            # Enter the exercise name in the search bar
            search_input_locator = (By.XPATH, "//span[@class='component__searchInput flex-left flex-align-center ant-input-affix-wrapper']/input")
            search_input = self.wait.until(EC.element_to_be_clickable(search_input_locator))
            search_input.send_keys(exercise_name)
            logging.info(f"Entered '{exercise_name}' in the search bar.")
            time.sleep(1)  # Give it time to register the input

            # Press Enter
            search_input.send_keys(Keys.ENTER)
            logging.info("Pressed Enter in the search bar.")
            time.sleep(5)  # Give it a LONGER time to load search results.  Important!

            # Dismiss the search tips popup by clicking on the instruction section
            instructions_locator = (By.XPATH, "//textarea[@data-testid='workoutBuilder-instructionTextarea']")
            instructions_section = self.wait.until(EC.element_to_be_clickable(instructions_locator))
            instructions_section.click()
            logging.info("Dismissed the search tips popup by clicking on the instruction section.")
            time.sleep(1)

            # Locate the exercise library container.
            library_container_locator = (By.XPATH, "//div[@class='exerciseLibrary-container flex-left fullWidth']")
            library_container = self.wait.until(EC.presence_of_element_located(library_container_locator))

            # Construct the XPath to find the specific exercise within the container
            exercise_locator = (By.XPATH, f"//div[@class='exerciseLibrary-container flex-left fullWidth']//div[@data-testid='exerciseLibrary-exercise-ropeTricepPushdown']")
            # Find the element with the data-testid
            try:
                exercise_element = self.wait.until(EC.element_to_be_clickable(exercise_locator))
                exercise_element.click()
                logging.info(f"Clicked on exercise 'Rope Tricep Pushdown'.")
            except TimeoutException:
                logging.error(f"Exercise 'Rope Tricep Pushdown' not found in the exercise library.")
                return False

            # Click 'Add to Workout' button
            add_to_workout_button_locator = (By.XPATH, "//button[@type='button' and contains(@class, 'gtBtn-blue') and contains(., 'Add to Workout')]")
            add_to_workout_button = self.wait.until(EC.element_to_be_clickable(add_to_workout_button_locator))
            add_to_workout_button.click()
            logging.info("Clicked 'Add to Workout' button.")
            time.sleep(2)

            # Find the newly added exercise in the workout list.
            workout_list_exercise_locator = (By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='Rope Tricep Pushdown']/ancestor::div[@class='workoutExercise flex-left flex-row flex-align-center flex-noShrink fullWidth']")

            try:
                workout_list_exercise = self.wait.until(EC.presence_of_element_located(workout_list_exercise_locator))
                logging.info("Found the added exercise in the workout list.")
            except TimeoutException:
                logging.error("Could not find the added exercise in the workout list.")
                return False

            #Set sets.
            sets_input_locator = (By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='Rope Tricep Pushdown']/ancestor::div[@class='workoutExercise flex-left flex-row flex-align-center flex-noShrink fullWidth']//input[@data-testid='workoutBuilder-exerciseSetInput']")

            sets_input = self.wait.until(EC.element_to_be_clickable(sets_input_locator))
            sets_input.click() # Click field
            sets_input.send_keys(Keys.BACKSPACE) # Clear field using BACKSPACE
            sets_input.send_keys(Keys.BACKSPACE) # Clear field using BACKSPACE again for robustness
            sets_input.send_keys(sets) # Enter value
            logging.info(f"Sets set to: {sets}")
            time.sleep(1)


            # Set reps.
            reps_input_locator = (By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='Rope Tricep Pushdown']/ancestor::div[@class='workoutExercise flex-left flex-row flex-align-center flex-noShrink fullWidth']//input[@data-testid='workoutBuilder-recordTypeInput']")
            reps_input = self.wait.until(EC.element_to_be_clickable(reps_input_locator))
            reps_input.click()
            reps_input.send_keys(Keys.BACKSPACE) # Clear field using BACKSPACE
            reps_input.send_keys(Keys.BACKSPACE) # Clear field using BACKSPACE again for robustness
            reps_input.send_keys(reps)
            logging.info(f"Reps set to: {reps}")
            time.sleep(1)


            #Click Save button.
            save_button_locator = (By.XPATH, "//button[@data-testid='workoutBuilder-saveBtn']")
            save_button = self.wait.until(EC.element_to_be_clickable(save_button_locator))
            save_button.click()
            logging.info("Clicked Save button.")
            time.sleep(3)

            return True

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error adding exercise '{exercise_name}': {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while adding exercise: {e}")
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

if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"  # Replace with your username
    password = "cyywp7nyk"  # Replace with your password
    client_name = "Shannon Birch"  # Replace with the client's name
    workout_name = "Back and Triceps"  # The workout to edit
    exercise_to_remove = "Rope Tricep Pushdown"  # The exercise to remove
    exercise_to_add = "Rope Tricep Pushdown"  #Exercise to add
    sets = "5"
    reps = "12"

    trainerize_bot = TrainerizeAutomation()
    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()

            if trainerize_bot.navigate_to_client(client_name):
                if trainerize_bot.navigate_to_training_program():
                    current_program = trainerize_bot.find_current_workout_program()
                    if current_program:
                        print(f"The current workout program is: {current_program}")
                    else:
                        print("No current workout program assigned.")
                    if trainerize_bot.click_workout(workout_name):
                        if trainerize_bot.click_edit_workout():

                            #REMOVE EXERCISE
                            if trainerize_bot.remove_exercise(exercise_to_remove):
                                print(f"Successfully removed exercise '{exercise_to_remove}' from workout '{workout_name}'.")
                            else:
                                print(f"Failed to remove exercise '{exercise_to_remove}' from workout '{workout_name}'. It may not exist in the workout or XPath is wrong.")

                            #ADD EXERCISE
                            if trainerize_bot.add_exercise(exercise_to_add, sets, reps):
                                print(f"Successfully added exercise '{exercise_to_add}' to workout '{workout_name}'.")
                            else:
                                print(f"Failed to add exercise '{exercise_to_add}' to workout '{workout_name}'.")

                        else:
                            print("Failed to click the 'Edit workout' button.")
                    else:
                        print(f"Failed to click on workout: {workout_name}")
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