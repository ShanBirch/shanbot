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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import re
import base64
from openai import OpenAI


class TrainerizeAutomation:
    def __init__(self, openai_api_key):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"
        self.openai_api_key = openai_api_key

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
            self.client = OpenAI(api_key=self.openai_api_key)
        except Exception as e:
            logging.error(f"Failed to initialize Chrome or OpenAI: {e}")
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
            logging.error(f"An unexpected error occurred while clicking 'Progress Photos': {e}")
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
            logging.error(f"An unexpected error occurred: {e}")
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
            logging.error(f"An unexpected error occurred: {e}")
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
          logging.error(f"An unexpected error occurred: {e}")
          return False

    def click_walking_graph(self):
      """Clicks the 'Walking' link within Cardio Activities using XPath."""
      # No longer needed - removing this method

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
            logging.error(f"An unexpected error occurred while clicking 'Goals and Habits' tab: {e}")
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
            logging.error(f"Error retrieving weight goal: {e}")
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
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def navigate_to_nutrition_graphs(self):
        return self._navigate_to_graph("caloriesintake")

    def navigate_to_sleep_graphs(self):
        return self._navigate_to_graph("sleep")

    def navigate_to_steps_graphs(self):
        return self._navigate_to_graph("steps")


    def analyze_bodyweight_graph(self):
        try:
            logging.info("Analyzing bodyweight graph with GPT-4o...")
            # Wait for the graph element to be present *or* for a timeout to occur.
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)  # Wait for the graph to potentially load fully
            screenshot_path = "bodyweight_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this bodyweight graph from a personal training app. Provide a comprehensive analysis, including:

            *   **Trend:** Describe the overall trend (increasing, decreasing, stable, fluctuating, etc.). Be specific.
            *   **Consistency:** Assess the consistency of the data. Are there large variations, or is it relatively stable?
            *   **Adherence:**  Infer the client's likely adherence to their weight management goals. Use terms like "Excellent," "Good," "Fair," "Poor," or "Inconsistent." Justify.
            *   **Data Quality:** Is there missing data? Any anomalies or outliers?
            *   **Specific Values:** Extract and mention *specific* weight values for at least three different dates, including the start, end, and a midpoint.
            *   **Recommendations:** Give 2-3 brief, actionable recommendations.
            *   **Positive Reinforcement:** Start with something positive.
            *   **Concise Summary:** Give a very short (one sentence) overall summary.

            Format the output as follows:

            **Analysis of Bodyweight Graph**

            *   **Trend:** [Trend description]
            *   **Consistency:** [Consistency description]
            *   **Adherence:** [Adherence assessment and justification]
            *   **Data Quality:** [Missing data, anomalies, etc.]
            *   **Specific Values:**
                * [Date 1]: [Weight Value 1]
                * [Date 2]: [Weight Value 2]
                * [Date 3]: [Weight Value 3]
            *   **Recommendations:**
                *   [Recommendation 1]
                *   [Recommendation 2]
                *   [Recommendation 3]
            *   **Summary:** [One-sentence overall summary]
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            analysis = response.choices[0].message.content
            return analysis

        except TimeoutException:
            return "No bodyweight data available."

        except Exception as e:
            logging.error(f"Error analyzing graph with GPT-4o: {e}")
            return f"Error: {e}"

    def analyze_nutrition_graph(self):
        try:
            logging.info("Analyzing nutrition graph with GPT-4o...")
             # Wait for the graph element to be present *or* for a timeout.
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "nutrition_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this nutrition graph from a personal training app. Provide a comprehensive analysis, including:

            *   **Trend:**  Describe the overall trend of caloric intake (increasing, decreasing, stable, fluctuating, etc.). Be specific.
            *   **Consistency:**  Assess the consistency of the data.  Are there large variations day-to-day, or is it relatively stable?
            *   **Adherence:** Based on the trend and consistency, infer the client's likely adherence to their nutrition plan. Use terms like "Excellent," "Good," "Fair," "Poor," or "Inconsistent."  Justify your assessment.
            * **Data Quality:** Is there missing data? Are there any anomalies or outliers?
            *   **Specific Values:** If possible, extract and mention *specific* calorie values for at least three different days, including the start, end and a mid point. If it is a range, provide the range
            *   **Recommendations:**  Give 2-3 brief, actionable recommendations based on the analysis. Focus on what the client can do to improve or maintain their progress.
            *   **Positive Reinforcement:** Start with something positive. Find *something* good to say, even if it's just acknowledging that data is being tracked.
            *   **Concise Summary:**  Give a very short (one sentence) overall summary.

            Format the output as follows:

            **Analysis of Caloric Intake Graph**

            *   **Trend:** [Trend description]
            *   **Consistency:** [Consistency description]
            *   **Adherence:** [Adherence assessment and justification]
            * **Data Quality:** [Missing data, anomalies, etc.]
            * **Specific Values:**
                * [Date 1]: [Calorie Value/Range 1]
                * [Date 2]: [Calorie Value/Range 2]
                * [Date 3]: [Calorie Value/Range 3]
            *   **Recommendations:**
                *   [Recommendation 1]
                *   [Recommendation 2]
                *   [Recommendation 3]
            *   **Summary:** [One-sentence overall summary]
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            analysis = response.choices[0].message.content
            print(analysis)
            return analysis

        except TimeoutException:
            return "No nutrition data available."
        except Exception as e:
            logging.error(f"Error analyzing nutrition graph with GPT-4o: {e}")
            return f"Error: {e}"
    def analyze_sleep_graph(self):
        """Analyzes the sleep graph using GPT-4o."""
        try:
            logging.info("Analyzing sleep graph with GPT-4o...")
             # Wait for the graph element to be present *or* for a timeout
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "sleep_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this sleep graph from a personal training app. Provide a comprehensive analysis:

            *   **Trend:** Overall trend (increasing, decreasing, stable, fluctuating).
            *   **Consistency:** Consistency of sleep duration.
            *   **Adequacy:**  Is the client generally getting enough sleep (e.g., 7-9 hours for most adults)?
            *   **Data Quality:** Missing data? Anomalies?
            *   **Specific Values:** Extract at least three specific sleep duration values and dates.
            *   **Recommendations:** 2-3 actionable recommendations.
            *   **Positive Reinforcement:** Start with something positive.
            *   **Concise Summary:** One-sentence overall summary.

            Format:

            **Analysis of Sleep Graph**

            *   **Trend:** [Trend description]
            *   **Consistency:** [Consistency]
            *   **Adequacy:** [Adequacy assessment]
            *   **Data Quality:** [Data quality]
            *   **Specific Values:**
                * [Date 1]: [Hours of Sleep 1]
                * [Date 2]: [Hours of Sleep 2]
                * [Date 3]: [Hours of Sleep 3]
            *   **Recommendations:**
                *   [Recommendation 1]
                *   [Recommendation 2]
                *   [Recommendation 3]
            *   **Summary:** [Summary]
            """
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            analysis = response.choices[0].message.content
            print(analysis)
            return analysis
        except TimeoutException:
            return "No sleep data available."

        except Exception as e:
            logging.error(f"Error analyzing sleep graph: {e}")
            return f"Error: {e}"

    def analyze_steps_graph(self):
        """Analyzes the steps graph using GPT-4o."""
        try:
            logging.info("Analyzing steps graph with GPT-4o...")
            # Wait for the graph element to be present *or* for a timeout
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "steps_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this steps graph from a personal training app.  Provide a comprehensive analysis:

            *   **Trend:** Overall trend (increasing, decreasing, stable, fluctuating).
            *   **Consistency:**  Day-to-day consistency.
            *   **Activity Level:**  Is the client generally active (e.g., meeting a 10,000 step goal)?
            *   **Data Quality:** Missing data? Anomalies?
            *   **Specific Values:** Extract at least three specific step count values and dates.
            *   **Recommendations:** 2-3 actionable recommendations.
            *   **Positive Reinforcement:** Start with something positive.
            *   **Concise Summary:** One-sentence summary.

            Format:

            **Analysis of Steps Graph**

            *   **Trend:** [Trend]
            *   **Consistency:** [Consistency]
            *   **Activity Level:** [Activity level assessment]
            *   **Data Quality:** [Data quality]
            *   **Specific Values:**
                * [Date 1]: [Step Count 1]
                * [Date 2]: [Step Count 2]
                * [Date 3]: [Step Count 3]
            *   **Recommendations:**
                *   [Recommendation 1]
                *   [Recommendation 2]
                *   [Recommendation 3]
            *   **Summary:** [Summary]
            """
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            analysis = response.choices[0].message.content
            print(analysis)
            return analysis
        except TimeoutException:
            return "No steps data available."
        except Exception as e:
            logging.error(f"Error analyzing steps graph: {e}")
            return f"Error: {e}"

    def analyze_progress_photos(self):
        """Analyzes progress photos using GPT-4o if they exist."""
        try:
            logging.info("Analyzing progress photos with GPT-4o...")
            # Wait for some element on the progress photos page to be present.

            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.photo-comparison-image")))

            time.sleep(2)  # Give images time to load
            screenshot_path = "progress_photos.png"
            self.driver.save_screenshot(screenshot_path) #take screenshot of whole screen
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze these progress photos from a personal training app. Provide a comprehensive analysis, focusing on visible changes over time. Consider the following:

            * **Overall Physique Changes:** Describe any noticeable changes in body composition, muscle definition, posture, etc. Be specific.
            * **Specific Body Areas:**  Note any changes in specific areas (e.g., arms, legs, abdomen, back).
            * **Positive Changes:** Highlight positive progress.
            * **Areas for Improvement:**  (Optional) If appropriate, *constructively* suggest areas that might need more focus.
            * **Consistency of Posing:** Comment on whether the posing is consistent across photos, as this affects comparison accuracy.
            * **Lighting and Image Quality:** Note any significant differences in lighting or image quality that might affect the assessment.
            * **Recommendations:**  Give 1-2 brief, actionable recommendations based on the observed changes (or lack thereof).
            * **Concise Summary:** Give a very short (one sentence) overall summary.

            Format:

            **Analysis of Progress Photos**

            * **Overall Physique Changes:** [Description]
            * **Specific Body Areas:** [Description]
            * **Positive Changes:** [Description]
            * **Areas for Improvement (Optional):** [Description]
            * **Consistency of Posing:** [Description]
            * **Lighting and Image Quality:** [Description]
            * **Recommendations:**
                * [Recommendation 1]
                * [Recommendation 2]
            * **Summary:** [Summary]
            """
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )

            analysis = response.choices[0].message.content
            print(analysis)
            return analysis

        except TimeoutException:
           return "No progress photos available."
        except Exception as e:
            logging.error(f"Error analyzing progress photos: {e}")
            return f"Error: {e}"

    def analyze_walking_graph(self):
        """Analyzes the walking graph using GPT-4o."""
        try:
            logging.info("Analyzing walking graph with GPT-4o...")
            # Explicitly wait for the canvas element to appear
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)  # Give the graph time to load.
            screenshot_path = "walking_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")

            base64_image = encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this walking graph from a personal training app. Provide a comprehensive analysis, including:

            *   **Trend:** Describe the overall trend in walking activity (increasing, decreasing, stable, fluctuating).
            *   **Consistency:** Assess the consistency of the walking activity.  Are there regular walks, or are they sporadic?
            *   **Duration/Distance:** If possible, estimate or extract specific durations or distances walked on at least three different days.
            *   **Data Quality:** Is there any missing data? Are there any anomalies or outliers?
            *   **Recommendations:** Provide 2-3 brief, actionable recommendations to the client based on the analysis.
            *   **Positive Reinforcement:** Start with something positive about their walking activity.
            *   **Concise Summary:** Give a very short (one-sentence) overall summary.

            Format your response as follows:

            **Analysis of Walking Graph**

            *   **Trend:** [Trend description]
            *   **Consistency:** [Consistency description]
            *   **Duration/Distance:**
                *   [Date 1]: [Duration/Distance 1]
                *   [Date 2]: [Duration/Distance 2]
                *   [Date 3]: [Duration/Distance 3]
            *   **Data Quality:** [Data quality description]
            *   **Recommendations:**
                *   [Recommendation 1]
                *   [Recommendation 2]
                *   [Recommendation 3]
            *   **Summary:** [One-sentence summary]
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,  # Increased for potentially longer descriptions
            )
            analysis = response.choices[0].message.content
            print(analysis)
            return analysis

        except TimeoutException:
            return "No walking data available."
        except Exception as e:
            logging.error(f"Error analyzing walking graph: {e}")
            return f"Error: {e}"


    def cleanup(self):
       """Cleans up resources (removes temp dir, and *now* closes driver correctly)."""
       try:
           logging.info("Cleaning up...")
           if hasattr(self, 'driver'): # Check if driver exists before trying to close
               logging.info("Closing webdriver...")
               self.driver.close()  # Close the current window (if any)
               self.driver.quit()   # Quit the browser entirely
               logging.info("Webdriver closed.")
           if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
               logging.info(f"Removing temp user data directory: {self.temp_user_data_dir}")
               shutil.rmtree(self.temp_user_data_dir)
               logging.info("Temp directory removed.")
           logging.info("Cleanup completed successfully.")
       except Exception as e:
           logging.error(f"Error during cleanup: {e}")


def encode_image(image_path):
    """Encodes an image file to Base64 format."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
            logging.error(f"Error: Image file not found at path: {image_path}")
            return None  # or raise the exception if you prefer
    except Exception as e:
        logging.error(f"Error encoding image: {e}")
        return None


if __name__ == '__main__':
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk"
    client_name = "Shannon Birch"
    openai_api_key = "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"

    trainerize_bot = TrainerizeAutomation(openai_api_key)
    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()
            if trainerize_bot.navigate_to_client(client_name):
                if trainerize_bot.click_progress_tab():
                    # Analyze Bodyweight Graph
                    if trainerize_bot.click_biometrics():
                        bodyweight_analysis = trainerize_bot.analyze_bodyweight_graph()
                        print("\n--- Bodyweight Graph Analysis ---")
                        print(bodyweight_analysis)

                    # Navigate to and analyze Nutrition Graph
                    if trainerize_bot.navigate_to_nutrition_graphs():
                        nutrition_analysis = trainerize_bot.analyze_nutrition_graph()
                        print("\n--- Nutrition Graph Analysis ---")
                        print(nutrition_analysis)

                    # Navigate to and analyze Sleep Graph
                    if trainerize_bot.navigate_to_sleep_graphs():
                        sleep_analysis = trainerize_bot.analyze_sleep_graph()
                        print("\n--- Sleep Graph Analysis ---")
                        print(sleep_analysis)

                    # Navigate to and analyze Steps Graph
                    if trainerize_bot.navigate_to_steps_graphs():
                        steps_analysis = trainerize_bot.analyze_steps_graph()
                        print("\n--- Steps Graph Analysis ---")
                        print(steps_analysis)
                # Click Progress Photos tab and analyze
                if trainerize_bot.click_progress_photos_tab():
                    photos_analysis = trainerize_bot.analyze_progress_photos()
                    print("\n--- Progress Photos Analysis ---")
                    print(photos_analysis)

                # Navigate to Goals and Habits tab and get weight goal
                if trainerize_bot.navigate_to_goals_and_habits_tab():
                    weight_goal = trainerize_bot.get_current_weight_goal()
                    print("\n--- Current Weight Goal ---")
                    print(weight_goal)


            input("Press Enter to close...")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()