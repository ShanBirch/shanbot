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
import google.generativeai as genai # Changed import here

class TrainerizeAutomation:
    def __init__(self, openai_api_key): # still using openai_api_key for consistency, but it's the Gemini API key
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = "C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
        self.chrome_executable_path = "C:\SeleniumDrivers\chrome-win64\chrome.exe"
        self.openai_api_key = openai_api_key

        genai.configure(api_key=self.openai_api_key) # Configure Gemini API with the key
        self.model = genai.GenerativeModel('gemini-2.0-flash') # Initialize Gemini Flash Model - using gemini-2.0-flash now

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
            logging.exception(f"Failed to initialize Chrome or Gemini API: {e}") # Updated log message to include exception details
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
            logging.exception(f"Error during login: {e}") # Updated log message to include exception details
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
                return False # Return False if cannot click client link

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
                return False # Return False if client link not found or clickable

            time.sleep(2)
            logging.info("Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            try:
                open_button = self.wait.until(EC.element_to_be_clickable(open_button_locator))
                open_button.click()
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(f"Could not find or click 'Open' button for {client_name}: {e}")
                return False # Return False if Open button not found or clickable

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
            logging.exception(f"Error navigating to client {client_name} or switching tabs: {e}") # Updated log message to include exception details
            return False

    def click_progress_photos_tab(self):
        """Clicks the 'Progress Photos' tab using a more robust XPath."""
        try:
            logging.info("Attempting to click the 'Progress Photos' tab...")
            # Use XPath to find the link containing "Progress Photos" and the correct href
            progress_photos_tab_locator = (By.XPATH, "//a[contains(@class, 'section-link') and contains(@href, '/progress/photo') and contains(., 'Progress Photos')]")
            progress_photos_tab = self.wait.until(EC.element_to_be_clickable(progress_photos_tab_locator))
            progress_photos_tab.click()
            logging.info("Successfully clicked the 'Progress Photos' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"'Progress Photos' tab not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred while clicking 'Progress Photos': {e}") # Updated log message to include exception details
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
            logging.exception(f"An unexpected error occurred: {e}") # Updated log message to include exception details
            return "Failed to click Progress tab (Unknown Error)"

    def click_biometrics(self):
        try:
            logging.info("Attempting to click the 'Biometrics' link...")
            self.wait.until(EC.presence_of_element_located((By.ID, "nav_progress")))
            time.sleep(1)
            biometrics_locator = (By.XPATH, "//a[@class='tz-sp section-link' and contains(@href, '/progress/bodyweight')]")
            biometrics_link = self.wait.until(EC.element_to_be_clickable(biometrics_locator))
            self.driver.execute_script("arguments[0].click();", biometrics_link)
            logging.info("Successfully clicked the 'Biometrics' link.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"'Biometrics' link not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}") # Updated log message to include exception details
            return False

    def click_cardio_activities(self):
        """Clicks the 'Cardio activities' link using keyboard navigation."""
        try:
            logging.info("Navigating to 'Cardio activities' using keyboard...")
            self.wait.until(EC.presence_of_element_located((By.ID, "nav_progress")))

            # Find a focusable element (e.g., the Progress tab)
            progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab.send_keys(Keys.TAB)
            time.sleep(0.5)
            active_element = self.driver.switch_to.active_element

            for _ in range(100):  # try tab up to 100 times
                try:
                    href = active_element.get_attribute("href")
                    # Check if href is not None and contains the target
                    if href and "activities" in href:
                        active_element.send_keys(Keys.ENTER)
                        logging.info("Successfully navigated to 'Cardio activities' using keyboard.")
                        return True
                except StaleElementReferenceException:  # Handle potential stale element
                    logging.warning("StaleElementReferenceException while getting href. Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

                active_element.send_keys(Keys.TAB)
                time.sleep(0.5)  # small delay between TABS

                try:  # Handle potetntial StaleElement when reaquiring active_element
                    active_element = self.driver.switch_to.active_element
                except StaleElementReferenceException:
                    logging.warning("StaleElementReferenceException.  Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)  # Start tabbing again.
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

            logging.error("'Cardio activities' link not found via keyboard navigation.")
            return False
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error navigating to 'Cardio activities' with keyboard: {e}")
            return False

        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}") # Updated log message to include exception details
            return False

    def click_walking_graph(self):
        """Clicks the 'Walking' link within Cardio Activities using XPath."""

        pass # Add pass to avoid syntax error if function is empty

    def navigate_to_goals_and_habits_tab(self):
        """Clicks the 'Goals and Habits' tab directly using its ID."""
        try:
            logging.info("Attempting to click the 'Goals and Habits' tab...")
            goals_tab_locator = (By.ID, "nav_goals_and habits")  # ID from HTML
            goals_tab = self.wait.until(EC.element_to_be_clickable(goals_tab_locator))
            goals_tab.click()
            logging.info("Successfully clicked the 'Goals and Habits' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"'Goals and Habits' tab not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred while clicking 'Goals and Habits' tab: {e}") # Updated log message to include exception details
            return False

    def get_current_weight_goal(self):
        """Retrieves the text of the current weight goal from the Goals and Habits tab."""
        try:
            logging.info("Attempting to get current weight goal...")
            weight_goal_locator = (By.XPATH, "//div[@class='goalTile__header flex-left']//label[@class='tz-label--large  goalTile__title']")
            weight_goal_label = self.wait.until(EC.presence_of_element_located(weight_goal_locator))
            weight_goal_text = weight_goal_label.text
            logging.info(f"Successfully retrieved weight goal: {weight_goal_text}")
            return weight_goal_text
        except NoSuchElementException:
            return "No weight goal found."
        except TimeoutException:
            return "No weight goal found (Timeout)."
        except Exception as e:
            logging.exception(f"Error retrieving weight goal: {e}") # Updated log message to include exception details
            return f"Error retrieving weight goal: {e}"

    def _navigate_to_graph(self, target_href_contains):
        """Generic function for navigating to graphs using keyboard."""
        try:
            logging.info(f"Navigating to graph containing '{target_href_contains}' using keyboard...")
            self.wait.until(EC.presence_of_element_located((By.ID, "nav_progress")))
            progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab.send_keys(Keys.TAB)
            time.sleep(0.5)
            active_element = self.driver.switch_to.active_element

            for _ in range(100):  # Up to 100 tabs
                try:
                    href = active_element.get_attribute("href")
                    if href and target_href_contains in href:
                        active_element.send_keys(Keys.ENTER)
                        logging.info(f"Successfully navigated to graph: {target_href_contains}")
                        return True
                except StaleElementReferenceException:
                    logging.warning("StaleElementReferenceException. Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

                active_element.send_keys(Keys.TAB)
                time.sleep(0.5)
                try:
                    active_element = self.driver.switch_to.active_element  # Re-acquire in case of DOM changes
                except StaleElementReferenceException:
                     logging.warning("StaleElementReferenceException. Re-finding Progress tab.")
                     progress_tab = self.driver.find_element(By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                     progress_tab.send_keys(Keys.TAB)
                     time.sleep(0.5)
                     active_element = self.driver.switch_to.active_element


            logging.error(f"Graph link containing '{target_href_contains}' not found via keyboard navigation.")
            return False

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error navigating to graph with keyboard: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}") # Updated log message to include exception details
            return False

    def navigate_to_nutrition_graphs(self):
        return self._navigate_to_graph("caloriesintake")

    def navigate_to_sleep_graphs(self):
        return self._navigate_to_graph("sleep")

    def navigate_to_steps_graphs(self):
        return self._navigate_to_graph("steps")

    def analyze_bodyweight_graph(self):
        try:
            logging.info("Analyzing bodyweight graph with gemini-2.0-flash...") # Updated model name in log
            # Wait for the graph element to be present or for a timeout to occur.
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)  # Wait for the graph to potentially load fully
            screenshot_path = "bodyweight_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": """
                        Analyze this bodyweight graph from a personal training app compare this weeks weight in to the previous months. Provide a comprehensive analysis, including:

                        heres an example: Loving the donward trend of this graph! Latest weigh in at 94 kilos, down from

                        

                        
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png", # Assuming screenshot is PNG, adjust if needed (image/jpeg)
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Bodyweight Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text']) # Print the text part of the prompt

            response = self.model.generate_content(
                contents=prompt_parts, # Using contents instead of messages
                generation_config=genai.GenerationConfig(max_output_tokens=1000) # Generation config for Gemini
            )
            analysis = response.text # Accessing text from response

            print("\n--- Gemini Response (Bodyweight Analysis) ---")
            print(analysis) # Print Gemini's response

            return analysis

        except TimeoutException:
            return "No bodyweight data available."

        except Exception as e:
            logging.exception(f"Error analyzing graph with gemini-2.0-flash: {e}") # Updated log message to include exception details
            return f"Error: {e}"

    def analyze_nutrition_graph(self):
        try:
            logging.info("Analyzing nutrition graph with gemini-2.0-flash...") # Updated model name in log
            # Wait for the graph element to be present or for a timeout.
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "nutrition_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": """
                        Analyze this nutrition graph from a personal training app comparing the current week to the previous month. Provide a comprehensive analysis, including:
                        an example
                        Really good to see you hit your target goal of 2700 cals consistantly this weel. Sunday was a little bit over but thats just the weekend!

                     
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png", # Assuming screenshot is PNG, adjust if needed (image/jpeg)
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Nutrition Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text']) # Print the text part of the prompt

            response = self.model.generate_content(
                contents=prompt_parts, # Using contents instead of messages
                generation_config=genai.GenerationConfig(max_output_tokens=1000) # Generation config for Gemini
            )
            analysis = response.text

            print("\n--- Gemini Response (Nutrition Analysis) ---")
            print(analysis) # Print Gemini's response

            print(analysis)
            return analysis

        except TimeoutException:
            return "No nutrition data available."
        except Exception as e:
            logging.exception(f"Error analyzing nutrition graph with gemini-2.0-flash: {e}") # Updated log message to include exception details
            return f"Error: {e}"

    def analyze_sleep_graph(self):
        """Analyzes the sleep graph using gemini-2.0-flash.""" # Updated model name in docstring
        try:
            logging.info("Analyzing sleep graph with gemini-2.0-flash...") # Updated model name in log
            # Wait for the graph element to be present or for a timeout
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "sleep_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": """
                        Analyze this sleep graph from a personal training app. Analyze the current week to the rest of the month
                         example

                        Looks like you've up your sleep game this week, really happy to see you getitng 8 hours every night. Sleeps so important for gains!

                    
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png", # Assuming screenshot is PNG, adjust if needed (image/jpeg)
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Sleep Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text']) # Print the text part of the prompt

            response = self.model.generate_content(
                contents=prompt_parts, # Using contents instead of messages
                generation_config=genai.GenerationConfig(max_output_tokens=1000) # Generation config for Gemini
            )
            analysis = response.text

            print("\n--- Gemini Response (Sleep Analysis) ---")
            print(analysis) # Print Gemini's response

            print(analysis)
            return analysis
        except TimeoutException:
            return "No sleep data available."

        except Exception as e:
            logging.exception(f"Error analyzing sleep graph: {e}") # Updated log message to include exception details
            return f"Error: {e}"

    def analyze_steps_graph(self):
        """Analyzes the steps graph using gemini-2.0-flash.""" # Updated model name in docstring
        try:
            logging.info("Analyzing steps graph with gemini-2.0-flash...") # Updated model name in log
            # Wait for the graph element to be present or for a timeout
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "steps_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": """
                        Analyze this steps graph from a personal training app.  heres an example analysis


                        *   Averaging out at bout 8k steps/day, love it. lets try to make it 10k this week!

                            Good Stuff! Seriously, getting those walks in is awesome! Just keep doing what you're doing!

                        Format:

                        **Analysis of Steps Graph**

                        *   **Trend:** [Trend]
                        *   **Consistency:** [Consistency]
                        *   **Activity Level:** [Activity level assessment]
                        *   **Data Quality:** [Data quality]
                        *   **Recommendations:**
                            *   [Recommendation 1]
                            *   [Recommendation 2]
                            *   [Recommendation 3]
                        *   **Summary:** [Summary]
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png", # Assuming screenshot is PNG, adjust if needed (image/jpeg)
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Steps Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text']) # Print the text part of the prompt

            response = self.model.generate_content(
                contents=prompt_parts, # Using contents instead of messages
                generation_config=genai.GenerationConfig(max_output_tokens=1000) # Generation config for Gemini
            )
            analysis = response.text

            print("\n--- Gemini Response (Steps Analysis) ---")
            print(analysis) # Print Gemini's response

            print(analysis)
            return analysis
        except TimeoutException:
            return "No steps data available."
        except Exception as e:
            logging.exception(f"Error analyzing steps graph: {e}") # Updated log message to include exception details
            return f"Error: {e}"

    def analyze_progress_photos(self):
        """Analyzes progress photos using gemini-2.0-flash if they exist.""" # Updated model name in docstring
        try:
            logging.info("Analyzing progress photos with gemini-2.0-flash...") # Updated model name in log
            # Wait for some element on the progress photos page to be present.

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.photo-comparison-image")))

            time.sleep(2)  # Give images time to load
            screenshot_path = "progress_photos.png"
            self.driver.save_screenshot(screenshot_path) #take screenshot of whole screen
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": """
                        Analyze these progress photos from a personal training app. Just check if they are upto date. If they are give them a compliments, (looking strong, getting fitter day by day) 
                        if they arnt, just encourage them to keep them updated. 

                        * *
                    {
                        "inline_data": {
                            "mime_type": "image/png", # Assuming screenshot is PNG, adjust if needed (image/jpeg)
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Progress Photos Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text']) # Print the text part of the prompt

            response = self.model.generate_content(
                contents=prompt_parts, # Using contents instead of messages
                generation_config=genai.GenerationConfig(max_output_tokens=1000) # Generation config for Gemini
            )

            analysis = response.text

            print("\n--- Gemini Response (Progress Photos Analysis) ---")
            print(analysis) # Print Gemini's response

            print(analysis)
            return analysis

        except TimeoutException:
           return "No progress photos available."
        except Exception as e:
            logging.exception(f"Error analyzing progress photos: {e}") # Updated log message to include exception details
            return f"Error: {e}"


    
    
    
    def generate_check_in_review(self, client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis, steps_analysis, photos_analysis, weight_goal, weekly_summary_data, exercise_recommendation,
                                  workouts_completed_analysis, total_workout_stats_analysis, workload_increase_analysis, specific_exercises_analysis):
        """Generates a check-in review using Gemini, with workout analysis done by Gemini - REVISED PROMPT (FORCEFUL)."""
        review_text = "Default Review Text"
        try:
            logging.info("Generating check-in review with Gemini (data-driven analysis) - REVISED PROMPT (FORCEFUL)...")

            recommendations = []

            if exercise_recommendation:
                recommendations.append(exercise_recommendation)

            if "No sleep data available" in sleep_analysis:
                recommendations.append("I noticed there's no sleep data available this week. Tracking your sleep can be really helpful...")
            elif "Data Quality: Missing data" in sleep_analysis:
                 recommendations.append("It looks like there might be some missing sleep data this week...")
            if "Data Completeness: Missing data" in nutrition_analysis or "Data Completeness: Days are missed" in nutrition_analysis:
                 recommendations.append("I see a few days are missing from your calorie tracking this week...")
            elif "No nutrition data available" in nutrition_analysis:
                recommendations.append("It seems there's no nutrition data for this week. Tracking your nutrition is essential...")


            prompt_recommendation_section = ""
            if recommendations:
                prompt_recommendation_section = "\n**Focus Areas:**\n\n" + "\n".join([f"* {rec}" for rec in recommendations])


            prompt = f"""
            You are an Shannon Birch writing client check-in reviews.
            Analyze the following data for {client_name}'s weekly progress and provide a comprehensive and encouraging review.

            **Progression Photos Analysis:**
            {photos_analysis}

            **Bodyweight Analysis:**
            {bodyweight_analysis}

            **Nutrition Analysis:**
            {nutrition_analysis}

            **Steps Analysis:**
            {steps_analysis}

            **Workout Analysis:**

            **1. Workouts Completed This Week:**
            {workouts_completed_analysis}

            **2. Workload Increase (Current vs Previous Week):**
            {workload_increase_analysis}

            **3. Total Workout Stats (All Weeks):**
            {total_workout_stats_analysis}

            **4. Specific Exercise Analysis:**
            {specific_exercises_analysis}

            
            {weight_goal}


            Use the EXAMPLE reviews below for structural guidance. Keep it to exact format plz. 


    Example 1
    Hey (first name) Here's your review for the week! :) 
            
Photos: Didn't see any new progress pics this week. No worries, but if you can, snapping some regularly is super helpful to see how far you've come visually!

Weight: Weight's still trending down nicely, which is awesome! 2 kilos down already, v nice progress! Keep doing what you're doing!

Food: Looks like calories crept up a bit on the weekend there. Totally normal, but maybe think about trying to even things out a bit more across the week. Love that you're tracking your food – that's the biggest step!

Steps: Steps are up and down a bit, but some days you're crushing it! How about trying to aim for 10k every day? Really impressed with those high step days, keep that energy going!

Sleep: Loving the consistent sleep tracking! That's amazing. Let's shoot for around 8 hours of sleep each night if you can and try to make it a routine, bed at the same time and up at the same time everyday, this will help keep your internal body clock happy! 
         
         
Workout Summary 

Total workouts for week of 24/02/2025-02/03/2025: 5
Workouts completed week of 24/02/2025-02/03/2025:
- Saturday
- Back and Triceps
- Core and Arms 2
- Chest and Biceps
- Lower

--- Totals for week of 24/02/2025-02/03/2025: ---
Total Weight Lifted: 21827.00 kg
Total Reps Done: 461
Total Sets Done: 49


--- Total Workload Change comparing previous week to current week:
Workload change vs previous week: 25.30%

Love this see this increase in overall workload! Keep it coming!

--- Exercise: Barbell Bench Chest Press ---

**Week of 24/02/2025-02/03/2025:**
  Workout - 28 Feb 2025
  Exercise - Barbell Bench Chest Press
    Set 1: 6 reps, 60.00 kg
    Set 2: 4 reps, 100.00 kg
    Set 3: 5 reps, 100.00 kg

**Week of 17/02/2025-23/02/2025:**
  Workout - 17 Feb 2025
  Exercise - Barbell Bench Chest Press
    Set 1: 10 reps, 60.00 kg
    Set 2: 6 reps, 100.00 kg
    Set 3: 6 reps, 110.00 kg
    Set 4: 5 reps, 120.00 kg
    Set 5: 6 reps, 100.00 kg
    
    Barbell Bench Chest Press: Workload change vs previous week: -58.82%
    
    Slight decrease in total worload, this will happen a lot! Amaazing work for turnning up!

--- Exercise: B.B Back Squat ---

**Week of 24/02/2025-02/03/2025:**
  Workout - 25 Feb 2025
  Exercise - B.B Back Squat
    Set 1: 5 reps, 60.00 kg
    Set 2: 4 reps, 80.00 kg
    Set 3: 3 reps, 100.00 kg
    Set 4: 3 reps, 120.00 kg
    Set 5: 100 reps, 60.00 kg

**Week of 17/02/2025-23/02/2025:**
  Not performed in week of 17/02/2025-23/02/2025
  
  B.B Back Squat: Workload change vs previous week: 
  
  Missed a week of squats! Proabably needed the rest? Listening to your body is alwasy the best idea!

--- Exercise: Lat Pull Down Wide Grip ---

**Week of 24/02/2025-02/03/2025:**
  Workout - 24 Feb 2025
  Exercise - Lat Pull Down Wide Grip
    Set 1: 10 reps, 75.00 kg
    Set 2: 10 reps, 75.00 kg
    Set 3: 8 reps, 75.00 kg
    Set 4: 7 reps, 75.00 kg
    Set 5: 6 reps, 75.00 kg

**Week of 17/02/2025-23/02/2025:**
  Workout - 19 Feb 2025
  Exercise - Lat Pull Down Wide Grip
    Set 1: 10 reps, 75.00 kg
    Set 2: 10 reps, 75.00 kg
    Set 3: 8 reps, 75.00 kg
    Set 4: 6 reps, 75.00 kg
    Set 5: 6 reps, 75.00 kg
    
    Lat Pull Down Wide Grip: Workload change vs previous week: 2.50%
    
    Lat Pull down coming up nicely!
    
    Summary - Another great week! really happy with the progress! 
    
    

    Keep Moving - Coach Shan
    
    Check in review notes for gpt
            Always stay positive with the client
            For information that is missing enocurage the client to provide it next week, as kindly as possible
            Offer scientific advice to help motivate the client achieve their goals.
            """



            

            print("\n--- Gemini Check-in Review Prompt ---")
            print(prompt) # Print the check-in review prompt

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(max_output_tokens=2000) # Increased max tokens
            )
            review_text = response.text

            print("\n--- Gemini Check-in Review Response ---")
            print(review_text) # Print Gemini's check-in review response


        except Exception as e:
            logging.exception(f"Error generating check-in review: {e}")
            review_text = "Error generating check-in review. Please check the logs for details."
        finally:
            logging.info("Exiting generate_check_in_review function.")
            return review_text

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

    @staticmethod
    def encode_image(image_path):
        """Encodes an image file to Base64 format."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            logging.error(f"Error: Image file not found at path: {image_path}")
            return None  # or raise the exception if you prefer
        except Exception as e:
            logging.exception(f"Error encoding image: {e}")
            return None

    

if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk" #replace with your actual password
    openai_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k" #replace with your actual api key - Gemini API key now

    client_names = [
        "Shannon Birch", # Only process Shannon Birch
    ]

    trainerize_bot = TrainerizeAutomation(openai_api_key)
    all_reviews = [] # List to store reviews for all clients

    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()

            for client_name in client_names:
                print(f"\n--- Starting check-in for {client_name} ---")
                bodyweight_analysis = "No analysis yet."
                nutrition_analysis = "No analysis yet."
                sleep_analysis = "No analysis yet."
                steps_analysis = "No analysis yet."
                photos_analysis = "No analysis yet."
                weight_goal_text = "No weight goal found."
                workout_review_text_output = "No workout review generated yet."
                gpt_workout_analysis_output = "No GPT workout analysis yet." # Initialize GPT workout analysis output
                exercise_improvement_recommendation = None # Initialize exercise improvement recommendation
                weekly_workout_data_all_weeks = [] # Store all weekly workout data scraped in this run.
                current_week_workout_data = [] # Store current week workout data
                weekly_summary_data_for_review = {} # Initialize weekly_summary_data_for_review

                workouts_completed_analysis_output = "No analysis yet."
                total_workout_stats_analysis_output = "No analysis yet."
                workload_increase_analysis_output = "No analysis yet."
                specific_exercises_analysis_output = "No analysis yet."


                if trainerize_bot.navigate_to_client(client_name):
                    print("Navigated to client") # ADDED PRINT STATEMENT
                    if trainerize_bot.click_progress_tab():
                        print("Clicked progress tab") # ADDED PRINT STATEMENT
                        # Analyze Bodyweight Graph
                        if trainerize_bot.click_biometrics():
                            print("Clicked biometrics") # ADDED PRINT STATEMENT
                            bodyweight_analysis = trainerize_bot.analyze_bodyweight_graph()
                            print(f"\n--- {client_name} - Bodyweight Graph Analysis ---")
                            print(bodyweight_analysis)

                        # Navigate to and analyze Nutrition Graph
                        if trainerize_bot.navigate_to_nutrition_graphs():
                            print("Navigated to nutrition graphs") # ADDED PRINT STATEMENT
                            nutrition_analysis = trainerize_bot.analyze_nutrition_graph()
                            print(f"\n--- {client_name} - Nutrition Graph Analysis ---")
                            print(nutrition_analysis)

                        # Navigate to and analyze Sleep Graph
                        if trainerize_bot.navigate_to_sleep_graphs():
                            print("Navigated to sleep graphs") # ADDED PRINT STATEMENT
                            sleep_analysis = trainerize_bot.analyze_sleep_graph()
                            print(f"\n--- {client_name} - Sleep Graph Analysis ---")
                            print(sleep_analysis)

                        # Navigate to and analyze Steps Graph
                        if trainerize_bot.navigate_to_steps_graphs():
                            print("Navigated to steps graphs") # ADDED PRINT STATEMENT
                            steps_analysis = trainerize_bot.analyze_steps_graph()
                            print(f"\n--- {client_name} - Steps Graph Analysis ---")
                            print(steps_analysis)

                        # Click Review By Workout and process workout data
                        if trainerize_bot.click_review_by_workout().startswith("Successfully"):
                            print("Clicked review by workout") # ADDED PRINT STATEMENT
                            weekly_workout_data_all_weeks, current_week_workout_data = trainerize_bot.process_workouts() # Get both lists
                            weekly_summary_data_for_review = trainerize_bot._group_workout_data_by_week(weekly_workout_data_all_weeks) # Group data for review
                            print("\n--- Weekly Workout Summary Data ---") # Print weekly summary data
                            print(weekly_summary_data_for_review) # Print weekly summary data

                            # Gemini Workout Analysis Calls
                            workouts_completed_analysis_output = trainerize_bot.analyze_workouts_completed_this_week(weekly_summary_data_for_review)
                            total_workout_stats_analysis_output = trainerize_bot.analyze_total_workout_stats(weekly_summary_data_for_review)
                            workload_increase_analysis_output = trainerize_bot.analyze_workload_increase(weekly_summary_data_for_review)
                            specific_exercises_analysis_output = trainerize_bot.analyze_specific_exercises(weekly_summary_data_for_review)


                            print("Processed workouts and performed Gemini workout analysis") # ADDED PRINT STATEMENT


                    # Click Progress Photos tab and analyze
                    if trainerize_bot.click_progress_photos_tab():
                        print("Clicked progress photos tab") # ADDED PRINT STATEMENT
                        photos_analysis = trainerize_bot.analyze_progress_photos()
                        print(f"\n--- {client_name} - Progress Photos Analysis ---")
                        print(photos_analysis)

                    # Navigate to Goals and Habits tab and get weight goal
                    if trainerize_bot.navigate_to_goals_and_habits_tab():
                        print("Navigated to goals and habits tab") # ADDED PRINT STATEMENT
                        weight_goal_text = trainerize_bot.get_current_weight_goal()
                        print(f"\n--- {client_name} - Current Weight Goal ---")
                        print(weight_goal_text)

                    # Generate and Print Check-in Review
                    print("Generating check-in review") # ADDED PRINT STATEMENT
                    check_in_review = trainerize_bot.generate_check_in_review(client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis, steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data_for_review, exercise_improvement_recommendation,
                                                                                workouts_completed_analysis_output, total_workout_stats_analysis_output, workload_increase_analysis_output, specific_exercises_analysis_output) # Pass weekly_summary_data and all workout analyses
                    print(f"\n--- {client_name} - Check-in Review from Gemini ---") # Updated log message
                    print(check_in_review)
                    all_reviews.append(f"\n--- Review for {client_name} ---\n{check_in_review}") # Store review for output
                    print("Check-in review generated and stored") # ADDED PRINT STATEMENT

                else:
                    logging.warning(f"Could not navigate to client: {client_name}. Moving to the next client.")
                    all_reviews.append(f"\n--- Review for {client_name} ---\nError: Could not navigate to client profile.") # Store error message
                    print("Could not navigate to client profile") # ADDED PRINT STATEMENT
                    continue # Move to the next client if navigation fails

                if not trainerize_bot.navigate_back_to_clients_list(): # Navigate back to clients list
                    logging.error(f"Could not navigate back to clients list after processing {client_name}. Stopping client processing.")
                    all_reviews.append(f"\n--- Review for {client_name} ---\nError: Could not navigate back to clients list for next client.")
                    print("Could not navigate back to clients list") # ADDED PRINT STATEMENT
                    break # Stop processing if navigation fails, to avoid issues with next client
                else:
                    print("Navigated back to clients list") # ADDED PRINT STATEMENT

        else:
            print("Login failed. Script aborted.")

    except Exception as e:
        logging.exception(f"An error occurred: {e}") # Updated log message to include exception details
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()

    if all_reviews:
        print("\n\n--- ALL CLIENT REVIEWS ---")
        for review in all_reviews:
            print(review)
            print("-" * 50) # Separator between client reviews

    input("Press Enter to close...")