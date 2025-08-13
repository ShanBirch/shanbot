import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
import base64
import logging
from datetime import datetime


class CalendarAnalyzer:
    def __init__(self, gemini_api_key=None):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.gemini_api_key = gemini_api_key
        self.client_name = "Alice Forster"  # Default client name
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

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

        try:
            chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
            logging.info(
                f"Using manually downloaded ChromeDriver: {chromedriver_path}")
            service = ChromeService(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")
        except Exception as e:
            logging.exception(f"Failed to initialize Chrome: {e}")
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
            # Use a shorter wait for popups that may not appear
            block_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(block_button_locator))
            block_button.click()
            logging.info("Clicked 'Block' on the notification popup.")
            time.sleep(1)
            return True
        except Exception:
            logging.warning(
                "Notification popup not found or failed to handle.")
            return False

    def handle_welcome_popup(self):
        try:
            logging.info("Checking for a welcome/introductory popup...")
            # This XPath looks for a button inside a modal dialog that has text like "Close", "Skip", or "Maybe Later"
            close_button_locator = (
                By.XPATH, "//div[contains(@class, 'modal-dialog')]//button[contains(text(), 'Close') or contains(text(), 'Skip') or contains(text(), 'Maybe Later')]")
            close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(close_button_locator))
            logging.info(
                f"Found a popup with close button text: {close_button.text}. Clicking it.")
            close_button.click()
            time.sleep(1)
            return True
        except Exception:
            logging.warning("No welcome/introductory popup was found.")
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
            logging.info("Waiting for the second email field (emailInput)...")
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "emailInput")))
            logging.info("Entering full email on second page...")
            email_field_second = self.driver.find_element(By.ID, "emailInput")
            email_field_second.send_keys(username)
            logging.info("Entering password...")
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.send_keys(password)
            logging.info("Clicking 'Sign In' button...")
            sign_in_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
            self.driver.execute_script("arguments[0].click();", sign_in_button)

            # Let the page settle for a few seconds
            time.sleep(5)

            # Take a screenshot to see what the page looks like after login
            screenshot_path = os.path.join(os.getcwd(), "post_login_page.png")
            self.driver.save_screenshot(screenshot_path)
            logging.info(
                f"Saved a screenshot of the page after login to: {screenshot_path}")

            # After logging in, handle potential popups
            self.handle_welcome_popup()
            self.handle_notification_popup()

            logging.info("Successfully logged in!")
            return True
        except Exception as e:
            logging.exception(f"Error during login: {e}")
            return False

    def navigate_to_client(self, client_name):
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")
            time.sleep(8)
            logging.info("Clicking the 'Clients' link in the sidebar...")
            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
                time.sleep(3)
            except TimeoutException:
                logging.warning(
                    "Could not click clients link, assuming we are on the correct page.")

            logging.info(
                "Entering client name into the search bar on the Clients page...")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            try:
                search_input = self.wait.until(
                    EC.presence_of_element_located(search_input_locator))
                search_input.clear()
                time.sleep(1)
                search_input.send_keys(client_name)
                time.sleep(5)
            except TimeoutException:
                logging.error("Could not find search input")
                return False

            logging.info(
                "Clicking on the client's name in the search results...")
            client_link_locator = (
                By.XPATH, f"//a[translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{client_name.lower()}']")
            try:
                self.wait.until(
                    EC.presence_of_element_located(client_link_locator))
                client_link = self.wait.until(
                    EC.element_to_be_clickable(client_link_locator))
                client_link.click()
                time.sleep(4)
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(
                    f"Could not find or click client link for {client_name}: {e}")
                return False

            logging.info(
                "Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            try:
                open_button = self.wait.until(
                    EC.element_to_be_clickable(open_button_locator))
                open_button.click()
                time.sleep(3)
            except (TimeoutException, NoSuchElementException):
                logging.warning(
                    "'Open' button not found, assuming we are already in the client view.")

            logging.info("Switching to the new tab if it exists...")
            original_window = self.driver.current_window_handle
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.number_of_windows_to_be(2))
                for window_handle in self.driver.window_handles:
                    if window_handle != original_window:
                        self.driver.switch_to.window(window_handle)
                        logging.info("Switched to new tab.")
                        break
            except TimeoutException:
                logging.info(
                    "No new tab opened, continuing in the current tab.")

            time.sleep(2)
            logging.info(
                f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True
        except Exception as e:
            logging.exception(
                f"Error navigating to client {client_name} or switching tabs: {e}")
            return False

    def click_calendar_tab(self):
        """Clicks on the client's calendar tab with robust fallback selectors."""
        try:
            print("Navigating to calendar tab...")

            # Try multiple selectors in order of preference
            calendar_selectors = [
                # Original specific selector
                "//p[@class='tz-p color--gray80 pl8' and text()='Calendar']",
                # More flexible class-based selectors
                "//p[contains(@class, 'tz-p') and text()='Calendar']",
                "//p[contains(@class, 'color--gray80') and text()='Calendar']",
                # Parent element selectors
                "//p[text()='Calendar']/parent::*",
                "//p[text()='Calendar']/parent::a",
                "//p[text()='Calendar']/parent::button",
                "//p[text()='Calendar']/parent::div",
                # Any element with Calendar text
                "//*[text()='Calendar']",
                "//*[contains(text(), 'Calendar')]",
                # Link-based selectors
                "//a[contains(@href, 'calendar')]",
                "//a[contains(text(), 'Calendar')]",
                # Button-based selectors
                "//button[contains(text(), 'Calendar')]",
                # Tab-based selectors
                "//*[@role='tab' and contains(text(), 'Calendar')]",
                "//*[contains(@class, 'tab') and contains(text(), 'Calendar')]",
                # Navigation selectors
                "//nav//*[contains(text(), 'Calendar')]",
                "//ul//*[contains(text(), 'Calendar')]",
                "//li//*[contains(text(), 'Calendar')]"
            ]

            for i, selector in enumerate(calendar_selectors, 1):
                try:
                    print(
                        f"🔍 Trying calendar selector {i}: {selector[:50]}...")

                    # Try to find and click the element
                    calendar_element = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, selector)
                    ))

                    if calendar_element and calendar_element.is_displayed():
                        print(f"✅ Found calendar tab with selector {i}")

                        # Scroll element into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", calendar_element)
                        time.sleep(0.5)

                        # Try regular click first
                        try:
                            calendar_element.click()
                        except:
                            # If regular click fails, use JavaScript click
                            self.driver.execute_script(
                                "arguments[0].click();", calendar_element)

                        print("✅ Successfully clicked on the calendar tab.")

                        # Wait longer for calendar to load and verify it has data
                        print("⏳ Waiting for calendar to fully load with data...")
                        calendar_loaded = self.wait_for_calendar_to_load()

                        if calendar_loaded:
                            print("✅ Calendar loaded successfully with data!")
                            return True
                        else:
                            print(
                                "⚠️ Calendar loaded but no data detected, retrying...")
                            # Try refreshing the page and clicking again
                            time.sleep(3)
                            continue

                except TimeoutException:
                    print(f"❌ Selector {i} timed out")
                    continue
                except Exception as e:
                    print(f"❌ Selector {i} failed: {e}")
                    continue

            # If all selectors failed, try to find any navigation element
            print("🔍 All specific selectors failed, trying to find any navigation...")
            try:
                # Look for any navigation elements and print them for debugging
                nav_elements = self.driver.find_elements(
                    By.XPATH, "//nav//*[text()]")
                print(f"📋 Found {len(nav_elements)} navigation elements:")
                for elem in nav_elements[:10]:  # Show first 10
                    try:
                        print(f"  • {elem.text.strip()}")
                    except:
                        pass

                # Look for any tab-like elements
                tab_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(@class, 'tab') or @role='tab']")
                print(f"📋 Found {len(tab_elements)} tab elements:")
                for elem in tab_elements[:10]:  # Show first 10
                    try:
                        print(f"  • {elem.text.strip()}")
                    except:
                        pass

            except Exception as e:
                print(f"❌ Error exploring navigation: {e}")

            print("❌ Could not find or click the calendar tab with any selector.")
            return False

        except Exception as e:
            print(f"❌ Unexpected error in click_calendar_tab: {e}")
            return False

    def wait_for_calendar_to_load(self, max_attempts=3):
        """Wait for the calendar to fully load with actual data."""
        try:
            print("🔍 Verifying calendar has loaded with data...")

            for attempt in range(1, max_attempts + 1):
                print(f"📊 Verification attempt {attempt}/{max_attempts}...")

                # Wait for basic calendar structure
                time.sleep(5)  # Give it time to load

                # Look for signs that the calendar has data
                data_indicators = [
                    # Look for workout names
                    "//*[contains(text(), 'Chest Day') or contains(text(), 'Core Day') or contains(text(), 'Back Day') or contains(text(), 'Shoulder Day') or contains(text(), 'Leg Day')]",
                    # Look for nutrition data
                    "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                    # Look for walking activities
                    "//*[contains(text(), 'Walking')]",
                    # Look for any calendar entries with data
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Day') or contains(text(), 'Training') or contains(text(), 'Cals')]",
                    # Look for checkmarks or completion indicators
                    "//*[contains(text(), '✓') or contains(@class, 'completed') or contains(@class, 'check')]"
                ]

                data_found = False
                for indicator in data_indicators:
                    try:
                        elements = self.driver.find_elements(
                            By.XPATH, indicator)
                        if elements:
                            visible_elements = [
                                elem for elem in elements if elem.is_displayed()]
                            if visible_elements:
                                print(
                                    f"✅ Found calendar data: {len(visible_elements)} elements with {indicator[:30]}...")
                                # Print some examples
                                for elem in visible_elements[:3]:
                                    try:
                                        text = elem.text.strip()
                                        if text and len(text) < 100:
                                            print(f"  📊 Example: {text}")
                                    except:
                                        pass
                                data_found = True
                                break
                    except:
                        continue

                if data_found:
                    print(
                        f"✅ Calendar data verification successful on attempt {attempt}")
                    return True
                else:
                    print(f"⚠️ No calendar data found on attempt {attempt}")
                    if attempt < max_attempts:
                        print("⏳ Waiting longer for data to load...")
                        time.sleep(8)  # Wait longer between attempts

            print("❌ Calendar data verification failed after all attempts")
            return False

        except Exception as e:
            print(f"❌ Error verifying calendar data: {e}")
            return False

    def take_calendar_screenshot(self, client_name):
        """Takes a focused screenshot of the current week in the calendar."""
        try:
            print("Taking focused current week screenshot...")

            # Don't try to auto-detect current week, just ensure calendar is fully loaded
            print("Ensuring calendar is fully loaded...")
            time.sleep(3)  # Give calendar time to fully render

            # Take the screenshot
            screenshot_path = os.path.join(
                os.getcwd(), f"{client_name.replace(' ', '_')}_calendar_focused.png")
            self.driver.save_screenshot(screenshot_path)
            print(f"Focused screenshot saved to {screenshot_path}")

            # Optional: Try to crop to just the calendar area if we can identify it
            try:
                from PIL import Image

                # Try to find the calendar table/grid element for more precise cropping
                calendar_elements = [
                    "//table[contains(@class, 'calendar')]",
                    "//div[contains(@class, 'calendar-grid')]",
                    "//div[contains(@class, 'week-view')]",
                    "//div[@class='calendar-container']"
                ]

                calendar_element = None
                for selector in calendar_elements:
                    try:
                        calendar_element = self.driver.find_element(
                            By.XPATH, selector)
                        break
                    except:
                        continue

                if calendar_element:
                    # Get the calendar element's location and size
                    location = calendar_element.location
                    size = calendar_element.size

                    # Open the screenshot and crop it
                    img = Image.open(screenshot_path)
                    left = location['x']
                    top = location['y']
                    right = left + size['width']
                    bottom = top + size['height']

                    # Add some padding around the calendar
                    padding = 50
                    left = max(0, left - padding)
                    top = max(0, top - padding)
                    right = min(img.width, right + padding)
                    bottom = min(img.height, bottom + padding)

                    cropped_img = img.crop((left, top, right, bottom))
                    cropped_path = os.path.join(
                        os.getcwd(), f"{client_name.replace(' ', '_')}_calendar_cropped.png")
                    cropped_img.save(cropped_path)
                    print(
                        f"Cropped calendar screenshot saved to {cropped_path}")
                    return cropped_path

            except ImportError:
                print("PIL not available for cropping, using full screenshot")
            except Exception as e:
                print(f"Could not crop screenshot: {e}")

            return screenshot_path

        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return None

    def process_calendar_item(self, item, item_type):
        """Process a single calendar item with stale element handling."""
        try:
            # Wait for the item to be clickable
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(item)
            )

            # Get the item's text before clicking
            item_text = item.text

            # Scroll the item into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", item)
            time.sleep(1)  # Wait for scroll to complete

            # Refresh the element reference before clicking
            try:
                item = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//*[contains(text(), '{item_text}')]"))
                )
                item.click()
            except:
                # If we can't find the exact text, try clicking the original element
                item.click()

            # Wait for the details to load
            time.sleep(2)

            # Extract data based on item type
            if item_type == "workout":
                return self.extract_workout_details()
            elif item_type == "nutrition":
                return self.extract_nutrition_details()
            elif item_type == "walking":
                return self.extract_walking_details()
            elif item_type == "weight":
                return self.extract_weight_details()

        except Exception as e:
            print(f"⚠️ Error processing {item_type}: {str(e)}")
            return None
        finally:
            # Close the details view if it's open
            try:
                close_button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Close']")
                close_button.click()
                time.sleep(1)
            except:
                pass

    def analyze_detailed_calendar_data(self):
        """Analyze detailed NUTRITION, WALKING, and WEIGHT data for the current week ONLY."""
        print("🔍 Analyzing NUTRITION, WALKING & WEIGHT data for current week...")

        # Step 1: Automatically identify current week
        print("🔍 Step 1: Auto-detecting current week (Monday-Sunday)...")
        current_week = self.detect_current_week()
        if current_week:
            print(
                f"📅 Current week auto-detected: {current_week['start']} to {current_week['end']}")
            print(f"📅 Days: {', '.join(current_week['days'])}")
        else:
            print("⚠️ Could not auto-detect current week, using fallback dates")
            current_week = {
                "start": "2025-06-09",
                "end": "2025-06-15",
                "days": ["Monday 9th", "Tuesday 10th", "Wednesday 11th", "Thursday 12th", "Friday 13th", "Saturday 14th", "Sunday 15th"]
            }

        # Step 2: Take a cropped screenshot of JUST the current week
        print("🔍 Step 2: Taking cropped screenshot of current week...")
        current_week_screenshot = self.take_current_week_screenshot()

        # Step 3: Expand all "+More" buttons to reveal hidden items
        print("🔍 Step 3: Expanding ALL '+More' buttons to reveal hidden items...")
        more_buttons_expanded = self.expand_all_more_buttons_comprehensive()
        print(f"✅ Expanded {more_buttons_expanded} '+More' buttons")

        # Step 4: Collect all visible nutrition and walking data (without clicking into details)
        print("🔍 Step 4: Collecting all visible nutrition and walking data...")
        calendar_summary = self.collect_all_visible_calendar_data()

        # Step 5: Take updated screenshot after expanding "+More" buttons
        print("🔍 Step 5: Taking updated screenshot after expansion...")
        expanded_screenshot = self.take_current_week_screenshot()

        # Step 6: Analyze the expanded data with Gemini for comprehensive overview
        print("🔍 Step 6: Analyzing expanded calendar data with AI...")
        ai_analysis = self.analyze_calendar_with_gemini(expanded_screenshot)

        # Initialize results dictionary
        detailed_data = {
            "calendar_summary": calendar_summary,
            "nutrition_entries": calendar_summary.get("nutrition_entries", []),
            "walking_entries": calendar_summary.get("walking_entries", []),
            "weight_entries": calendar_summary.get("weight_entries", []),
            "workout_entries": calendar_summary.get("workout_entries", []),
            "current_week": current_week,
            "screenshot_path": expanded_screenshot,
            "ai_analysis": ai_analysis,
            "more_buttons_expanded": more_buttons_expanded
        }

        # Print summary
        print("\n📊 COMPREHENSIVE CALENDAR ANALYSIS SUMMARY:")
        print(f"  • '+More' buttons expanded: {more_buttons_expanded}")
        print(
            f"  • Nutrition entries found: {len(detailed_data['nutrition_entries'])}")
        print(
            f"  • Walking entries found: {len(detailed_data['walking_entries'])}")
        print(
            f"  • Weight entries found: {len(detailed_data['weight_entries'])}")
        print(
            f"  • Workout entries found: {len(detailed_data['workout_entries'])}")

        return detailed_data

    def collect_all_visible_calendar_data(self):
        """Collect all visible nutrition, walking, weight, and workout data from the calendar without clicking into details."""
        try:
            print("📋 Collecting all visible calendar data...")

            calendar_data = {
                "nutrition_entries": [],
                "walking_entries": [],
                "weight_entries": [],
                "workout_entries": [],
                "daily_summary": {}
            }

            # Wait for page to settle after "+More" expansion
            time.sleep(3)

            # Method 1: Find all calendar day containers
            print("🔍 Finding all calendar day containers...")
            day_containers = []

            # Look for calendar day containers
            container_selectors = [
                "//div[contains(@data-rbd-droppable-id, '')]",
                "//div[contains(@class, 'calendar-day')]",
                "//div[contains(@class, 'day-container')]"
            ]

            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    for container in containers:
                        if container.is_displayed():
                            day_containers.append(container)
                except:
                    continue

            print(f"📋 Found {len(day_containers)} potential day containers")

            # Method 2: Scan for specific data patterns across the entire calendar
            print("🔍 Scanning for nutrition entries...")
            nutrition_patterns = [
                "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                "//*[contains(text(), 'cal') and contains(text(), '/') and contains(text(), 'Meal')]"
            ]

            for pattern in nutrition_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if 'Cals' in text and 'Meal' in text and len(text) < 100:
                                # Try to find the day this belongs to
                                day_info = self.find_day_for_element(element)
                                entry = {
                                    "type": "nutrition",
                                    "text": text,
                                    "day": day_info,
                                    "element_location": element.location
                                }
                                calendar_data["nutrition_entries"].append(
                                    entry)
                                print(
                                    f"📊 Found nutrition: {text} (Day: {day_info})")
                except Exception as e:
                    print(f"⚠️ Error finding nutrition with pattern: {e}")
                    continue

            print("🔍 Scanning for walking entries...")
            walking_patterns = [
                "//*[contains(text(), 'Walking') and not(contains(text(), 'Program'))]",
                "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Walking')]"
            ]

            for pattern in walking_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if 'Walking' in text and len(text) < 100:
                                # Check if it's completed (has checkmark) or planned (empty circle)
                                status = self.check_activity_status(element)
                                day_info = self.find_day_for_element(element)
                                entry = {
                                    "type": "walking",
                                    "text": text,
                                    "status": status,
                                    "day": day_info,
                                    "element_location": element.location
                                }
                                calendar_data["walking_entries"].append(entry)
                                print(
                                    f"🚶 Found walking: {text} ({status}) (Day: {day_info})")
                except Exception as e:
                    print(f"⚠️ Error finding walking with pattern: {e}")
                    continue

            print("🔍 Scanning for weight entries...")
            weight_patterns = [
                "//*[contains(text(), 'kg') and string-length(text()) < 30]",
                "//*[contains(text(), 'Body Stats')]"
            ]

            for pattern in weight_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if ('kg' in text or 'Body Stats' in text) and len(text) < 50:
                                day_info = self.find_day_for_element(element)
                                entry = {
                                    "type": "weight",
                                    "text": text,
                                    "day": day_info,
                                    "element_location": element.location
                                }
                                calendar_data["weight_entries"].append(entry)
                                print(
                                    f"⚖️ Found weight: {text} (Day: {day_info})")
                except Exception as e:
                    print(f"⚠️ Error finding weight with pattern: {e}")
                    continue

            print("🔍 Scanning for workout entries...")
            workout_patterns = [
                "//*[contains(text(), 'Chest Day') or contains(text(), 'Core Day') or contains(text(), 'Back Day') or contains(text(), 'Shoulder Day') or contains(text(), 'Leg Day')]",
                "//*[contains(text(), 'Resistance Training') and not(contains(text(), 'Program'))]"
            ]

            for pattern in workout_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if any(workout_type in text for workout_type in ['Day', 'Training']) and len(text) < 100:
                                status = self.check_activity_status(element)
                                day_info = self.find_day_for_element(element)
                                entry = {
                                    "type": "workout",
                                    "text": text,
                                    "status": status,
                                    "day": day_info,
                                    "element_location": element.location
                                }
                                calendar_data["workout_entries"].append(entry)
                                print(
                                    f"💪 Found workout: {text} ({status}) (Day: {day_info})")
                except Exception as e:
                    print(f"⚠️ Error finding workouts with pattern: {e}")
                    continue

            # Method 3: Organize data by day
            print("🔍 Organizing data by day...")
            self.organize_data_by_day(calendar_data)

            print(f"✅ Calendar data collection complete:")
            print(
                f"  📊 Nutrition entries: {len(calendar_data['nutrition_entries'])}")
            print(
                f"  🚶 Walking entries: {len(calendar_data['walking_entries'])}")
            print(
                f"  ⚖️ Weight entries: {len(calendar_data['weight_entries'])}")
            print(
                f"  💪 Workout entries: {len(calendar_data['workout_entries'])}")

            return calendar_data

        except Exception as e:
            print(f"❌ Error collecting calendar data: {e}")
            return {
                "nutrition_entries": [],
                "walking_entries": [],
                "weight_entries": [],
                "workout_entries": [],
                "daily_summary": {}
            }

    def find_day_for_element(self, element):
        """Try to determine which day an element belongs to."""
        try:
            # Method 1: Look for day numbers in nearby elements
            parent_elements = [element]

            # Get parent elements up to 3 levels
            current = element
            for _ in range(3):
                try:
                    parent = current.find_element(By.XPATH, "./..")
                    parent_elements.append(parent)
                    current = parent
                except:
                    break

            # Look for day numbers in parent elements
            for parent in parent_elements:
                try:
                    parent_text = parent.text
                    # Look for day numbers (9-15 for current week, or other numbers)
                    import re
                    day_matches = re.findall(r'\b(\d{1,2})\b', parent_text)
                    for day_num in day_matches:
                        day_int = int(day_num)
                        if 1 <= day_int <= 31:  # Valid day number
                            return f"Day {day_num}"
                except:
                    continue

            # Method 2: Use element position to estimate day
            try:
                location = element.location
                x_position = location['x']

                # Rough estimation: calendar days are usually arranged horizontally
                # This is a rough approximation and may need adjustment
                if x_position < 200:
                    return "Day 1-2"
                elif x_position < 400:
                    return "Day 3-4"
                elif x_position < 600:
                    return "Day 5-6"
                elif x_position < 800:
                    return "Day 7-8"
                elif x_position < 1000:
                    return "Day 9-10"
                elif x_position < 1200:
                    return "Day 11-12"
                else:
                    return "Day 13+"
            except:
                pass

            return "Unknown Day"

        except Exception as e:
            return f"Error finding day: {e}"

    def check_activity_status(self, element):
        """Check if an activity is completed (✓) or planned (○)."""
        try:
            # Look for checkmarks or completion indicators near the element
            parent_elements = [element]

            # Get parent elements
            current = element
            for _ in range(2):
                try:
                    parent = current.find_element(By.XPATH, "./..")
                    parent_elements.append(parent)
                    current = parent
                except:
                    break

            # Look for completion indicators
            for parent in parent_elements:
                try:
                    parent_text = parent.text
                    if '✓' in parent_text or 'completed' in parent_text.lower():
                        return "Completed ✓"
                    elif '○' in parent_text or 'planned' in parent_text.lower():
                        return "Planned ○"
                except:
                    continue

            # Look for CSS classes that might indicate status
            try:
                element_classes = element.get_attribute('class') or ''
                if 'completed' in element_classes or 'done' in element_classes:
                    return "Completed ✓"
                elif 'planned' in element_classes or 'pending' in element_classes:
                    return "Planned ○"
            except:
                pass

            return "Unknown Status"

        except Exception as e:
            return f"Error checking status: {e}"

    def organize_data_by_day(self, calendar_data):
        """Organize all calendar data by day for easy reporting."""
        try:
            daily_summary = {}

            # Process all entry types
            all_entries = (
                calendar_data["nutrition_entries"] +
                calendar_data["walking_entries"] +
                calendar_data["weight_entries"] +
                calendar_data["workout_entries"]
            )

            for entry in all_entries:
                day = entry.get("day", "Unknown Day")
                if day not in daily_summary:
                    daily_summary[day] = {
                        "nutrition": [],
                        "walking": [],
                        "weight": [],
                        "workouts": []
                    }

                entry_type = entry.get("type", "unknown")
                if entry_type == "nutrition":
                    daily_summary[day]["nutrition"].append(entry["text"])
                elif entry_type == "walking":
                    status = entry.get("status", "")
                    daily_summary[day]["walking"].append(
                        f"{entry['text']} ({status})")
                elif entry_type == "weight":
                    daily_summary[day]["weight"].append(entry["text"])
                elif entry_type == "workout":
                    status = entry.get("status", "")
                    daily_summary[day]["workouts"].append(
                        f"{entry['text']} ({status})")

            calendar_data["daily_summary"] = daily_summary

            # Print daily summary
            print("\n📅 DAILY SUMMARY:")
            for day, data in sorted(daily_summary.items()):
                if any(data.values()):  # Only show days with data
                    print(f"\n**{day}:**")
                    if data["nutrition"]:
                        print(f"  📊 Nutrition: {', '.join(data['nutrition'])}")
                    if data["walking"]:
                        print(f"  🚶 Walking: {', '.join(data['walking'])}")
                    if data["weight"]:
                        print(f"  ⚖️ Weight: {', '.join(data['weight'])}")
                    if data["workouts"]:
                        print(f"  💪 Workouts: {', '.join(data['workouts'])}")

        except Exception as e:
            print(f"❌ Error organizing data by day: {e}")

    def detect_current_week(self):
        """Automatically detect the current week (Monday-Sunday) from the calendar."""
        try:
            print("🔍 Auto-detecting current week from calendar...")

            # Method 1: Look for "Today" indicator or current date highlighting
            today_indicators = [
                "//*[contains(@class, 'today') or contains(@class, 'current')]",
                "//*[contains(text(), 'Today')]",
                "//*[contains(@class, 'active') and contains(@class, 'day')]",
                "//*[contains(@class, 'selected') and contains(@class, 'date')]"
            ]

            current_date_element = None
            for indicator in today_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    for elem in elements:
                        if elem.is_displayed():
                            current_date_element = elem
                            print(
                                f"✅ Found current date indicator: {elem.get_attribute('class')}")
                            break
                    if current_date_element:
                        break
                except:
                    continue

            # Method 2: Use system date to calculate current week
            from datetime import datetime, timedelta
            today = datetime.now()
            print(f"📅 System date: {today.strftime('%Y-%m-%d %A')}")

            # Find Monday of current week (Monday = 0, Sunday = 6)
            days_since_monday = today.weekday()  # Monday = 0
            monday = today - timedelta(days=days_since_monday)
            sunday = monday + timedelta(days=6)

            print(
                f"📅 Calculated current week: {monday.strftime('%A %B %d')} to {sunday.strftime('%A %B %d, %Y')}")

            # Method 3: Try to detect from calendar view by looking for recent activity
            print("🔍 Looking for recent activity patterns in calendar...")

            # Look for nutrition entries with recent dates
            recent_nutrition_patterns = [
                f"//*[contains(text(), 'Cals') and contains(text(), 'Meal')]",
                f"//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Cals')]"
            ]

            nutrition_entries = []
            for pattern in recent_nutrition_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            if 'Cals' in text and 'Meal' in text:
                                nutrition_entries.append(elem)
                except:
                    continue

            print(
                f"🔍 Found {len(nutrition_entries)} nutrition entries in calendar")

            # Method 4: Look for calendar structure and identify week boundaries
            week_data = self.analyze_calendar_structure_for_current_week(
                monday, sunday)

            if week_data:
                return week_data

            # Fallback: Use calculated dates
            current_week = {
                "start": monday.strftime("%Y-%m-%d"),
                "end": sunday.strftime("%Y-%m-%d"),
                "days": [
                    f"{(monday + timedelta(days=i)).strftime('%A')} {(monday + timedelta(days=i)).day}{self.get_ordinal_suffix((monday + timedelta(days=i)).day)}"
                    for i in range(7)
                ],
                "detection_method": "system_date_calculation"
            }

            print(
                f"✅ Using calculated current week: {current_week['start']} to {current_week['end']}")
            return current_week

        except Exception as e:
            print(f"❌ Error detecting current week: {e}")
            return None

    def get_ordinal_suffix(self, day):
        """Get ordinal suffix for day (1st, 2nd, 3rd, 4th, etc.)"""
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return suffix

    def analyze_calendar_structure_for_current_week(self, monday, sunday):
        """Analyze the calendar DOM structure to identify the current week."""
        try:
            print("🔍 Analyzing calendar structure for current week...")

            # Look for calendar grid structure
            calendar_selectors = [
                "//div[contains(@class, 'calendar')]",
                "//div[contains(@class, 'week')]",
                "//div[contains(@data-rbd-droppable-id, '')]"
            ]

            calendar_elements = []
            for selector in calendar_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    calendar_elements.extend(
                        [elem for elem in elements if elem.is_displayed()])
                except:
                    continue

            print(f"🔍 Found {len(calendar_elements)} calendar elements")

            # Look for date patterns in the calendar
            date_patterns = []
            for day_offset in range(7):
                current_day = monday + timedelta(days=day_offset)
                day_num = current_day.day
                month_name = current_day.strftime('%B')
                month_short = current_day.strftime('%b')

                # Add various date format patterns
                date_patterns.extend([
                    str(day_num),
                    f"{day_num}",
                    f"{month_short} {day_num}",
                    f"{month_name} {day_num}",
                    current_day.strftime('%d'),
                    current_day.strftime('%m/%d'),
                    current_day.strftime('%d/%m')
                ])

            # Look for elements containing these date patterns
            found_dates = []
            for pattern in set(date_patterns):  # Remove duplicates
                try:
                    date_elements = self.driver.find_elements(
                        By.XPATH, f"//*[contains(text(), '{pattern}')]")
                    for elem in date_elements:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            if len(text) < 20:  # Avoid long text that just happens to contain the number
                                found_dates.append((pattern, text, elem))
                except:
                    continue

            print(
                f"🔍 Found {len(found_dates)} potential date matches in calendar")

            if len(found_dates) >= 3:  # If we found at least 3 dates from our week
                current_week = {
                    "start": monday.strftime("%Y-%m-%d"),
                    "end": sunday.strftime("%Y-%m-%d"),
                    "days": [
                        f"{(monday + timedelta(days=i)).strftime('%A')} {(monday + timedelta(days=i)).day}{self.get_ordinal_suffix((monday + timedelta(days=i)).day)}"
                        for i in range(7)
                    ],
                    "detection_method": "calendar_structure_analysis",
                    "found_dates": len(found_dates)
                }

                print(
                    f"✅ Current week detected from calendar structure with {len(found_dates)} date matches")
                return current_week

            return None

        except Exception as e:
            print(f"❌ Error analyzing calendar structure: {e}")
            return None

    def extract_workout_details(self):
        """Extract workout details from the current popup."""
        try:
            details = {}

            # Look for workout duration
            try:
                duration_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'minutes') or contains(text(), 'min')]")
                details['duration'] = duration_element.text
            except:
                details['duration'] = "Not found"

            # Look for start time
            try:
                time_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'AM') or contains(text(), 'PM')]")
                details['start_time'] = time_element.text
            except:
                details['start_time'] = "Not found"

            # Look for RPE rating
            try:
                rpe_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'RPE') or contains(text(), 'Rated')]")
                details['rpe'] = rpe_element.text
            except:
                details['rpe'] = "Not found"

            # Look for exercises (sets x reps x weight)
            try:
                exercise_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'sets') or contains(text(), 'Set')]")
                details['exercises'] = [
                    elem.text for elem in exercise_elements[:5]]  # Limit to first 5
            except:
                details['exercises'] = []

            return details

        except Exception as e:
            return {'error': str(e)}

    def extract_nutrition_details(self):
        """Extract nutrition details from the current popup."""
        try:
            details = {}

            # Look for meal breakdown
            try:
                meal_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Breakfast') or contains(text(), 'Lunch') or contains(text(), 'Dinner') or contains(text(), 'Snacks')]")
                details['meals'] = [elem.text for elem in meal_elements]
            except:
                details['meals'] = []

            # Look for macro information
            try:
                macro_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Protein') or contains(text(), 'Carbs') or contains(text(), 'Fat')]")
                details['macros'] = [elem.text for elem in macro_elements]
            except:
                details['macros'] = []

            # Look for calorie goal vs actual
            try:
                goal_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'goal') or contains(text(), 'target')]")
                details['goals'] = [elem.text for elem in goal_elements]
            except:
                details['goals'] = []

            return details

        except Exception as e:
            return {'error': str(e)}

    def extract_walking_details(self):
        """Extract walking details from the current popup."""
        try:
            details = {}

            # Look for distance
            try:
                distance_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'km') or contains(text(), 'mile')]")
                details['distance'] = distance_element.text
            except:
                details['distance'] = "Not found"

            # Look for duration
            try:
                duration_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'min') or contains(text(), 'hour')]")
                details['duration'] = duration_element.text
            except:
                details['duration'] = "Not found"

            # Look for steps
            try:
                steps_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'steps')]")
                details['steps'] = steps_element.text
            except:
                details['steps'] = "Not found"

            return details

        except Exception as e:
            return {'error': str(e)}

    def extract_weight_details(self):
        """Extract weight details from the current popup."""
        try:
            details = {}

            # Look for weight measurement
            try:
                weight_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'kg') or contains(text(), 'lbs')]")
                details['weight'] = weight_element.text
            except:
                details['weight'] = "Not found"

            # Look for body fat
            try:
                bf_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), '%')]")
                details['body_fat'] = bf_element.text
            except:
                details['body_fat'] = "Not found"

            # Look for BMI
            try:
                bmi_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'BMI')]")
                details['bmi'] = bmi_element.text
            except:
                details['bmi'] = "Not found"

            return details

        except Exception as e:
            return {'error': str(e)}

    def find_all_calendar_items(self, item_type):
        """Find ALL calendar items of a specific type (entire calendar, not just current week) - FOCUSED approach."""
        try:
            print(
                f"🔍 Finding ALL {item_type} items in the entire calendar (FOCUSED MODE)...")

            if item_type == 'workout':
                # Focus on actual workout entries that can be clicked
                selectors = [
                    # Specific workout day types
                    "//*[contains(text(), 'Chest Day') or contains(text(), 'Core Day') or contains(text(), 'Back Day') or contains(text(), 'Shoulder Day') or contains(text(), 'Leg Day')]",
                    "//*[contains(text(), 'Resistance Training') and not(contains(text(), 'Program'))]",
                    "//*[contains(text(), 'Functional') and not(contains(text(), 'Training Program'))]",
                    # Look for workout entries in calendar cells
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Day') and not(contains(text(), 'Today') or contains(text(), 'Yesterday'))]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Training') and not(contains(text(), 'Program'))]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Workout')]"
                ]
            elif item_type == 'nutrition':
                selectors = [
                    # Look for nutrition entries with calorie counts
                    "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                    "//*[contains(text(), 'cal') and contains(text(), '/') and contains(text(), 'Meal')]",
                    # Look for specific calorie amounts
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Cals')]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'cal') and string-length(text()) < 50]"
                ]
            elif item_type == 'walking':
                selectors = [
                    "//*[contains(text(), 'Walking') and not(contains(text(), 'Program'))]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Walking')]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Cardio')]"
                ]
            elif item_type == 'weight':
                selectors = [
                    "//*[contains(text(), 'kg') and string-length(text()) < 20]",
                    "//*[contains(text(), 'Body Stats')]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'kg')]"
                ]
            else:
                return []

            all_elements = []

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(
                        f"Found {len(elements)} {item_type} elements with selector: {selector[:50]}...")

                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            if element_text and element.is_displayed() and len(element_text) > 2:
                                # Check if this looks like a calendar item (not just random text)
                                is_calendar_item = (
                                    # Must be in a calendar structure
                                    len(element.find_elements(By.XPATH, "./ancestor::*[contains(@data-rbd-droppable-id, '')]")) > 0 or
                                    # Or be a clickable element
                                    element.tag_name.lower() in ['a', 'button', 'div'] and (
                                        element.get_attribute('onclick') or
                                        'click' in (element.get_attribute('class') or '') or
                                        element.get_attribute('role') in [
                                            'button', 'link']
                                    )
                                )

                                if is_calendar_item:
                                    all_elements.append(element)
                                    print(
                                        f"✅ Found calendar {item_type}: {element_text[:50]}...")

                        except Exception as e:
                            continue

                except Exception as e:
                    print(f"No {item_type} elements found with selector: {e}")

            # Remove duplicates based on element location and text
            unique_elements = []
            seen_items = set()

            for element in all_elements:
                try:
                    # Create a unique identifier based on text and position
                    element_text = element.text.strip()
                    element_location = element.location
                    unique_id = f"{element_text}_{element_location['x']}_{element_location['y']}"

                    if unique_id not in seen_items:
                        unique_elements.append(element)
                        seen_items.add(unique_id)

                except:
                    # If we can't get location, include it anyway
                    unique_elements.append(element)

            print(f"✅ Found {len(unique_elements)} unique {item_type} items")
            return unique_elements

        except Exception as e:
            print(f"❌ Error finding {item_type} items: {e}")
            return []

    def generate_comprehensive_report(self, current_week_data):
        """Generate a comprehensive CALENDAR ANALYSIS report for the current week."""
        try:
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append(
                "📅 COMPREHENSIVE CALENDAR ANALYSIS - ALICE FORSTER")
            report_lines.append("📅 CURRENT WEEK ANALYSIS")
            report_lines.append("=" * 80)

            # Get calendar summary data
            calendar_summary = current_week_data.get('calendar_summary', {})
            daily_summary = calendar_summary.get('daily_summary', {})
            nutrition_entries = current_week_data.get('nutrition_entries', [])
            walking_entries = current_week_data.get('walking_entries', [])
            weight_entries = current_week_data.get('weight_entries', [])
            workout_entries = current_week_data.get('workout_entries', [])
            more_buttons_expanded = current_week_data.get(
                'more_buttons_expanded', 0)

            # Expansion Summary
            report_lines.append(f"\n🔍 DATA COLLECTION SUMMARY:")
            report_lines.append("-" * 60)
            report_lines.append(
                f"📋 '+More' buttons expanded: {more_buttons_expanded}")
            report_lines.append(
                f"📊 Total nutrition entries found: {len(nutrition_entries)}")
            report_lines.append(
                f"🚶 Total walking entries found: {len(walking_entries)}")
            report_lines.append(
                f"⚖️ Total weight entries found: {len(weight_entries)}")
            report_lines.append(
                f"💪 Total workout entries found: {len(workout_entries)}")

            # Daily Breakdown
            if daily_summary:
                report_lines.append(f"\n📅 DAILY BREAKDOWN:")
                report_lines.append("-" * 60)

                for day, data in sorted(daily_summary.items()):
                    if any(data.values()):  # Only show days with data
                        report_lines.append(f"\n**{day}:**")

                        if data.get("nutrition"):
                            report_lines.append(
                                f"  📊 Nutrition: {', '.join(data['nutrition'])}")

                        if data.get("walking"):
                            report_lines.append(
                                f"  🚶 Walking: {', '.join(data['walking'])}")

                        if data.get("weight"):
                            report_lines.append(
                                f"  ⚖️ Weight: {', '.join(data['weight'])}")

                        if data.get("workouts"):
                            report_lines.append(
                                f"  💪 Workouts: {', '.join(data['workouts'])}")

                        if not any([data.get("nutrition"), data.get("walking"), data.get("weight"), data.get("workouts")]):
                            report_lines.append(f"  ❌ No tracked activities")

            # Detailed Analysis by Category
            report_lines.append(f"\n🍎 NUTRITION ANALYSIS:")
            report_lines.append("-" * 60)
            if nutrition_entries:
                nutrition_days = set()
                for entry in nutrition_entries:
                    day = entry.get('day', 'Unknown')
                    nutrition_days.add(day)
                    report_lines.append(
                        f"  📊 {day}: {entry.get('text', 'Unknown')}")

                report_lines.append(f"\n📈 Nutrition Summary:")
                report_lines.append(
                    f"  • Days with nutrition tracking: {len(nutrition_days)}")
                report_lines.append(
                    f"  • Total nutrition entries: {len(nutrition_entries)}")

                # Calculate adherence
                if len(nutrition_days) >= 5:
                    report_lines.append(
                        f"  ✅ EXCELLENT nutrition tracking adherence!")
                elif len(nutrition_days) >= 3:
                    report_lines.append(
                        f"  👍 GOOD nutrition tracking adherence")
                else:
                    report_lines.append(
                        f"  ⚠️ LOW nutrition tracking adherence - needs improvement")
            else:
                report_lines.append("  ❌ No nutrition tracking found")

            report_lines.append(f"\n🚶 WALKING ANALYSIS:")
            report_lines.append("-" * 60)
            if walking_entries:
                completed_walks = 0
                planned_walks = 0
                walking_days = set()

                for entry in walking_entries:
                    day = entry.get('day', 'Unknown')
                    status = entry.get('status', 'Unknown Status')
                    text = entry.get('text', 'Walking')
                    walking_days.add(day)

                    if 'Completed ✓' in status:
                        completed_walks += 1
                        report_lines.append(f"  ✅ {day}: {text} (Completed)")
                    elif 'Planned ○' in status:
                        planned_walks += 1
                        report_lines.append(f"  ○ {day}: {text} (Planned)")
                    else:
                        report_lines.append(f"  🚶 {day}: {text} ({status})")

                report_lines.append(f"\n📈 Walking Summary:")
                report_lines.append(
                    f"  • Days with walking activities: {len(walking_days)}")
                report_lines.append(f"  • Completed walks: {completed_walks}")
                report_lines.append(f"  • Planned walks: {planned_walks}")

                # Calculate adherence
                if completed_walks >= 4:
                    report_lines.append(
                        f"  ✅ EXCELLENT walking activity level!")
                elif completed_walks >= 2:
                    report_lines.append(f"  👍 GOOD walking activity level")
                else:
                    report_lines.append(
                        f"  ⚠️ LOW walking activity level - needs improvement")
            else:
                report_lines.append("  ❌ No walking activities found")

            report_lines.append(f"\n💪 WORKOUT ANALYSIS:")
            report_lines.append("-" * 60)
            if workout_entries:
                completed_workouts = 0
                planned_workouts = 0
                workout_days = set()

                for entry in workout_entries:
                    day = entry.get('day', 'Unknown')
                    status = entry.get('status', 'Unknown Status')
                    text = entry.get('text', 'Workout')
                    workout_days.add(day)

                    if 'Completed ✓' in status:
                        completed_workouts += 1
                        report_lines.append(f"  ✅ {day}: {text} (Completed)")
                    elif 'Planned ○' in status:
                        planned_workouts += 1
                        report_lines.append(f"  ○ {day}: {text} (Planned)")
                    else:
                        report_lines.append(f"  💪 {day}: {text} ({status})")

                report_lines.append(f"\n📈 Workout Summary:")
                report_lines.append(
                    f"  • Days with workouts: {len(workout_days)}")
                report_lines.append(
                    f"  • Completed workouts: {completed_workouts}")
                report_lines.append(
                    f"  • Planned workouts: {planned_workouts}")
            else:
                report_lines.append("  ❌ No workouts found")

            report_lines.append(f"\n⚖️ WEIGHT TRACKING ANALYSIS:")
            report_lines.append("-" * 60)
            if weight_entries:
                weight_days = set()
                for entry in weight_entries:
                    day = entry.get('day', 'Unknown')
                    text = entry.get('text', 'Unknown')
                    weight_days.add(day)
                    report_lines.append(f"  ⚖️ {day}: {text}")

                report_lines.append(f"\n📈 Weight Summary:")
                report_lines.append(
                    f"  • Days with weight tracking: {len(weight_days)}")
                report_lines.append(
                    f"  • Total weight entries: {len(weight_entries)}")
            else:
                report_lines.append("  ❌ No weight tracking found")

            # Overall Summary
            report_lines.append(f"\n📈 OVERALL WEEK SUMMARY:")
            report_lines.append("-" * 40)

            # Count unique days with any activity
            all_active_days = set()
            for entry_list in [nutrition_entries, walking_entries, weight_entries, workout_entries]:
                for entry in entry_list:
                    day = entry.get('day', 'Unknown')
                    if day != 'Unknown Day':
                        all_active_days.add(day)

            report_lines.append(
                f"  📅 Days with tracked activities: {len(all_active_days)}/7")
            report_lines.append(
                f"  📊 Total data points collected: {len(nutrition_entries) + len(walking_entries) + len(weight_entries) + len(workout_entries)}")

            # Add AI analysis if available
            ai_analysis = current_week_data.get('ai_analysis', '')
            if ai_analysis:
                report_lines.append(f"\n🤖 AI ANALYSIS INSIGHTS:")
                report_lines.append("-" * 60)
                # Add first few lines of AI analysis
                ai_lines = ai_analysis.split('\n')[:10]
                for line in ai_lines:
                    if line.strip():
                        report_lines.append(f"  {line.strip()}")
                if len(ai_analysis.split('\n')) > 10:
                    report_lines.append(
                        f"  ... (see full AI analysis in separate section)")

            report_lines.append("=" * 80)

            # Join all lines
            full_report = "\n".join(report_lines)

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"Alice_Forster_comprehensive_calendar_analysis_{timestamp}.txt"

            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(full_report)
                if ai_analysis:
                    f.write(f"\n\n{'='*80}\n")
                    f.write(f"🤖 COMPLETE AI ANALYSIS:\n")
                    f.write(f"{'='*80}\n")
                    f.write(ai_analysis)

            print(full_report)
            print(
                f"\n💾 Comprehensive calendar analysis saved to: {report_filename}")

            return full_report

        except Exception as e:
            print(f"❌ Error generating comprehensive report: {e}")
            return "Error generating report"

    def analyze_calendar_with_gemini(self, screenshot_path):
        """Analyzes the calendar screenshot with Gemini for comprehensive fitness tracking insights."""
        if not self.gemini_api_key:
            print("Gemini API key not configured.")
            return None
        if not screenshot_path or not os.path.exists(screenshot_path):
            print(f"Screenshot not found at {screenshot_path}")
            return None

        print("Analyzing calendar with Gemini...")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            with open(screenshot_path, 'rb') as image_file:
                image_data = image_file.read()

            image_parts = [
                {
                    "mime_type": "image/png",
                    "data": image_data
                }
            ]

            prompt_parts = [
                """Analyze this Trainerize calendar screenshot and focus ONLY on the CURRENT/MOST ACTIVE WEEK. Look for the week with the most recent activity, completed workouts, and tracked data. This is likely the week containing dates around June 9-15, 2025.

IMPORTANT: Look very carefully for small text and numbers. Nutrition data appears as text like "1442.78 Cals / 3 Meals" and workout names like "Chest Day", "Core Day", "Back Day", etc. Walking data may show distances like "2.58 km".

**CURRENT WEEK IDENTIFICATION:**
- Identify which week appears to be the current/most active week (look for completed checkmarks ✓, recent nutrition tracking, and active workout data)
- Focus on the week that has the most completed activities and recent data entries
- State the date range for the week being analyzed

**DETAILED WORKOUT ANALYSIS (Current Week Only):**
- Look for workout names like: "Chest Day", "Core Day", "Back Day", "Shoulder Day", "Leg Day", "Resistance Training", "Functional strength training"
- For COMPLETED workouts (with checkmarks ✓): Provide workout name and exact date
- For INCOMPLETE workouts (empty circles ○): Provide workout name and exact date
- Look for "+More" text which indicates additional hidden workouts

**DETAILED NUTRITION TRACKING (Current Week Only):**
- Look very carefully for calorie text patterns like: "1442.78 Cals / 3 Meals", "1353.15 Cals / 4 Meals", "690.62 Cals / 3 Meals"
- These appear as small text under each day
- For EACH DAY, report the exact calorie/meal data if visible
- If no nutrition data is visible for a day, state "NO NUTRITION TRACKED"

**DETAILED WALKING/CARDIO TRACKING (Current Week Only):**
- Look for "Walking" entries with checkmarks ✓ or empty circles ○
- Look for distance measurements like "2.58 km", "1.6 km" etc.
- For EACH DAY, specify if walking was completed or not

**WEIGHT/BODY METRICS (Current Week Only):**
- Look for weight measurements like "79.1 kg", "90 Cals / 1 Meal"
- Report exact dates and values

**CURRENT WEEK SUMMARY:**
- Count all visible completed vs incomplete items
- Calculate adherence percentages
- Note any patterns or concerns

CRITICAL: Examine the image very carefully for small text and numbers. Don't say "NOT VISIBLE" unless you've thoroughly searched the image. The data is there but may be in small text.""",
                image_parts[0]
            ]

            response = model.generate_content(prompt_parts)
            print("Gemini analysis complete.")
            return response.text

        except Exception as e:
            print(f"An error occurred during Gemini analysis: {e}")
            return None

    def expand_all_more_buttons_comprehensive(self):
        """Expand ALL '+More' buttons in the entire calendar with smart loop prevention."""
        try:
            print("🔍 Expanding ALL '+More' buttons in the entire calendar...")

            total_buttons_clicked = 0
            max_attempts = 2  # Limit to 2 passes
            clicked_buttons = set()  # Track clicked buttons by their text and location

            for attempt in range(1, max_attempts + 1):
                print(f"🔄 Pass {attempt}: Looking for '+More' buttons...")

                # Find all +More buttons
                more_buttons = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), '+ ') and contains(text(), 'More')]"
                )

                if not more_buttons:
                    print(f"✅ No more '+More' buttons found in pass {attempt}")
                    break

                clicked_in_this_pass = 0

                for button in more_buttons:
                    try:
                        button_text = button.text.strip()
                        button_location = button.location
                        button_id = f"{button_text}_{button_location['x']}_{button_location['y']}"

                        if button_id in clicked_buttons:
                            continue

                        if '+ ' in button_text and 'More' in button_text and button.is_displayed():
                            print(f"📋 Clicking '+More' button: {button_text}")
                            self.driver.execute_script(
                                "arguments[0].click();", button)
                            time.sleep(1)
                            clicked_buttons.add(button_id)
                            clicked_in_this_pass += 1
                            total_buttons_clicked += 1

                            if clicked_in_this_pass >= 5:
                                print(
                                    f"⚠️ Reached limit of 5 clicks in pass {attempt}, moving to next pass")
                                break

                    except Exception as e:
                        print(f"⚠️ Error clicking button: {e}")
                        continue

                print(
                    f"✅ Pass {attempt} complete: {clicked_in_this_pass} buttons clicked")

                if clicked_in_this_pass == 0:
                    print("✅ No new buttons found, expansion complete")
                    break

                time.sleep(2)

            print(
                f"✅ '+More' expansion complete. Total buttons clicked: {total_buttons_clicked}")
            return total_buttons_clicked

        except Exception as e:
            print(f"❌ Error in '+More' expansion: {e}")
            return 0

    def is_on_calendar_page(self):
        """Check if we're already on the calendar page."""
        try:
            # Check URL first
            current_url = self.driver.current_url
            print(f"🔍 Current URL: {current_url}")

            if 'calendar' in current_url.lower():
                print("✅ Already on calendar page (URL contains 'calendar')")
                return True

            # Check for calendar-specific elements that are more specific to actual calendar view
            calendar_indicators = [
                # More specific calendar indicators
                "//div[contains(@class, 'calendar-view')]",
                "//div[contains(@class, 'week-view')]",
                "//div[contains(@class, 'calendar-grid')]",
                "//*[contains(@data-rbd-droppable-id, 'calendar')]",
                # Look for actual calendar structure with days
                "//div[contains(@class, 'day') and contains(@class, 'calendar')]",
                # Look for calendar navigation elements
                "//*[contains(text(), 'Previous Week') or contains(text(), 'Next Week')]",
                # Look for actual workout/activity entries in calendar format
                "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Day')]",
                # Look for calendar month/week headers
                "//*[contains(text(), 'June 2025') and contains(@class, 'calendar')]"
            ]

            calendar_found = False
            for selector in calendar_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(
                            f"✅ Found calendar elements with selector: {selector[:50]}...")
                        calendar_found = True
                        break
                except:
                    continue

            if calendar_found:
                print("✅ Already on calendar page (found specific calendar elements)")
                return True

            # If we don't find specific calendar elements, check what page we're actually on
            print("🔍 Not on calendar page. Checking current page content...")

            # Check page title
            try:
                page_title = self.driver.title
                print(f"📄 Page title: {page_title}")
            except:
                pass

            # Look for navigation elements to understand where we are
            try:
                nav_elements = self.driver.find_elements(
                    By.XPATH, "//nav//*[text()]")
                if nav_elements:
                    print("📋 Available navigation options:")
                    for elem in nav_elements[:10]:  # Show first 10
                        try:
                            text = elem.text.strip()
                            if text and len(text) < 50:  # Reasonable length
                                print(f"  • {text}")
                        except:
                            pass
            except:
                pass

            # Look for any clickable elements that might be tabs or navigation
            try:
                clickable_elements = self.driver.find_elements(
                    By.XPATH, "//a[text()] | //button[text()] | //*[@role='tab'][text()]")
                if clickable_elements:
                    print("🔗 Available clickable elements:")
                    for elem in clickable_elements[:15]:  # Show first 15
                        try:
                            text = elem.text.strip()
                            if text and len(text) < 50 and 'calendar' in text.lower():
                                print(f"  • {text} (CALENDAR RELATED)")
                            elif text and len(text) < 50:
                                print(f"  • {text}")
                        except:
                            pass
            except:
                pass

            return False

        except Exception as e:
            print(f"❌ Error checking if on calendar page: {e}")
            return False

    def cleanup(self):
        """Closes the browser session and cleans up temp files."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
        if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
            try:
                shutil.rmtree(self.temp_user_data_dir)
            except Exception as e:
                print(f"Error removing temporary directory: {e}")

    def take_current_week_screenshot(self):
        """Takes a cropped screenshot of JUST the current week (June 9-15, 2025)."""
        try:
            print("📸 Taking cropped screenshot of current week...")

            # Take full calendar screenshot first
            full_screenshot_path = os.path.join(
                os.getcwd(), "full_calendar_temp.png")
            self.driver.save_screenshot(full_screenshot_path)

            try:
                from PIL import Image

                # Try to find the current week area
                # Look for elements that contain the current week dates
                current_week_elements = []
                week_selectors = [
                    "//*[contains(text(), '9') and contains(text(), 'June')]",
                    "//*[contains(text(), '10') and contains(text(), 'June')]",
                    "//*[contains(text(), '11') and contains(text(), 'June')]",
                    "//*[contains(text(), '12') and contains(text(), 'June')]",
                    "//*[contains(text(), '13') and contains(text(), 'June')]",
                    "//*[contains(text(), '14') and contains(text(), 'June')]",
                    "//*[contains(text(), '15') and contains(text(), 'June')]",
                    # Also try just the numbers
                    "//div[contains(@data-rbd-droppable-id, '') and (contains(text(), '9') or contains(text(), '10') or contains(text(), '11') or contains(text(), '12') or contains(text(), '13') or contains(text(), '14') or contains(text(), '15'))]"
                ]

                week_area = None
                for selector in week_selectors:
                    try:
                        elements = self.driver.find_elements(
                            By.XPATH, selector)
                        if elements:
                            current_week_elements.extend(elements)
                    except:
                        continue

                if current_week_elements:
                    # Find the bounding box of all current week elements
                    min_x = min_y = float('inf')
                    max_x = max_y = 0

                    for element in current_week_elements:
                        try:
                            location = element.location
                            size = element.size
                            min_x = min(min_x, location['x'])
                            min_y = min(min_y, location['y'])
                            max_x = max(max_x, location['x'] + size['width'])
                            max_y = max(max_y, location['y'] + size['height'])
                        except:
                            continue

                    if min_x != float('inf'):
                        # Add padding around the week
                        padding = 100
                        img = Image.open(full_screenshot_path)
                        left = max(0, min_x - padding)
                        top = max(0, min_y - padding)
                        right = min(img.width, max_x + padding)
                        bottom = min(img.height, max_y + padding)

                        cropped_img = img.crop((left, top, right, bottom))
                        cropped_path = os.path.join(
                            os.getcwd(), "current_week_cropped.png")
                        cropped_img.save(cropped_path)
                        print(
                            f"✅ Cropped current week screenshot saved: {cropped_path}")

                        # Clean up temp file
                        os.remove(full_screenshot_path)
                        return cropped_path

                print("⚠️ Could not identify current week area, using full screenshot")
                return full_screenshot_path

            except ImportError:
                print("⚠️ PIL not available, using full screenshot")
                return full_screenshot_path
            except Exception as e:
                print(
                    f"⚠️ Error cropping screenshot: {e}, using full screenshot")
                return full_screenshot_path

        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")
            return None

    def analyze_nutrition_from_screenshot(self, screenshot_path):
        """Analyze nutrition tracking from the current week screenshot using Gemini."""
        if not self.gemini_api_key or not screenshot_path:
            return {"tracking_days": [], "analysis": "No screenshot or API key available"}

        try:
            print("🔍 Analyzing nutrition tracking from screenshot...")

            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')

            with open(screenshot_path, 'rb') as image_file:
                image_data = image_file.read()

            image_parts = [{
                "mime_type": "image/png",
                "data": image_data
            }]

            prompt = """Analyze this Trainerize calendar screenshot focusing ONLY on NUTRITION TRACKING.

CRITICAL: Look very carefully for small text that shows calorie and meal data. The format is typically:
- "1442.78 Cals / 3 Meals"
- "1380.44 Cals / 4 Meals" 
- "1353.15 Cals / 4 Meals"
- "690.62 Cals / 3 Meals"
- "90 Cals / 1 Meal"

This text appears as small text under each day in the calendar. Look at EVERY day visible in the calendar.

For EACH DAY you can see in the calendar (look at the numbers 9, 10, 11, 12, 13, 14, 15), report:
1. The day number
2. Whether nutrition was tracked (YES/NO)
3. If tracked, the EXACT calorie and meal text you see

Be very thorough - examine every single day box in the calendar for small text containing "Cals" and "Meal".

Format your response EXACTLY like this:
**NUTRITION TRACKING FOUND:**
- Day 9: [YES - 1442.78 Cals / 3 Meals] OR [NO - Not tracked]
- Day 10: [YES - 1380.44 Cals / 4 Meals] OR [NO - Not tracked]
- Day 11: [YES - 1353.15 Cals / 4 Meals] OR [NO - Not tracked]
- Day 12: [YES - 690.62 Cals / 3 Meals] OR [NO - Not tracked]
- Day 13: [YES - XXX Cals / X Meals] OR [NO - Not tracked]
- Day 14: [YES - XXX Cals / X Meals] OR [NO - Not tracked]  
- Day 15: [YES - XXX Cals / X Meals] OR [NO - Not tracked]

**SUMMARY:**
- Total days with nutrition tracking: X
- Days tracked: [list the day numbers]

IMPORTANT: Look very carefully at the small text in each day box. The nutrition data is there but may be small."""

            response = model.generate_content([prompt, image_parts[0]])

            print(f"🔍 Gemini nutrition analysis response: {response.text}")

            # Parse the response to extract tracking days
            tracking_days = []

            # Look for the pattern "Day X: [YES"
            import re
            yes_pattern = r"Day (\d+): \[YES[^\]]*\]"
            matches = re.findall(yes_pattern, response.text)

            for day_num in matches:
                tracking_days.append(f"Day {day_num}")

            print(f"✅ Parsed tracking days: {tracking_days}")

            return {
                "tracking_days": tracking_days,
                "analysis": response.text
            }

        except Exception as e:
            print(f"❌ Error analyzing nutrition from screenshot: {e}")
            return {"tracking_days": [], "analysis": f"Error: {e}"}

    def analyze_detailed_nutrition_entries(self):
        """Find and analyze detailed nutrition entries for the current week ONLY (June 9-15)."""
        try:
            print("🍎 Finding detailed nutrition entries for current week (June 9-15)...")

            # Step 1: First expand any "+More" buttons to reveal hidden nutrition entries
            print("🔍 Step 1: Expanding '+More' buttons to reveal hidden entries...")
            more_buttons_clicked = self.expand_all_more_buttons_comprehensive()
            print(f"✅ Expanded {more_buttons_clicked} '+More' buttons")

            # Step 2: Wait for page to settle after expanding
            time.sleep(3)

            # Step 3: Find all elements that contain calorie information
            print("🔍 Step 2: Finding all nutrition entries...")

            # Look for any nutrition entries with calorie information (dynamic detection)
            current_week_calories = []

            # First, find all nutrition entries in the calendar
            nutrition_selectors = [
                "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Cals')]"
            ]

            for selector in nutrition_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if 'Cals' in text and 'Meal' in text and len(text) < 50:
                                if text not in current_week_calories:
                                    current_week_calories.append(text)
                except:
                    continue

            print(
                f"🔍 Auto-detected {len(current_week_calories)} nutrition entries:")
            for entry in current_week_calories:
                print(f"  📊 {entry}")

            nutrition_entries = []
            all_found_elements = []

            # First, try to find the specific current week entries
            print("🎯 Looking for specific current week nutrition entries...")
            for target_calories in current_week_calories:
                try:
                    # Look for exact matches
                    elements = self.driver.find_elements(
                        By.XPATH, f"//*[contains(text(), '{target_calories}')]")
                    for element in elements:
                        try:
                            if element.is_displayed():
                                element_text = element.text.strip()
                                if target_calories in element_text:
                                    print(
                                        f"🎯 Found target entry: {element_text}")

                                    # Try to find a clickable parent
                                    clickable_element = element
                                    try:
                                        # Check if element itself is clickable
                                        if not (element.is_enabled() and
                                                (element.tag_name.lower() in ['a', 'button'] or
                                                element.get_attribute('onclick') or
                                                'click' in (element.get_attribute('class') or '') or
                                                 element.get_attribute('role') == 'button')):
                                            # Try to find a clickable parent
                                            parent = element.find_element(
                                                By.XPATH, "./..")
                                            if parent.is_enabled():
                                                clickable_element = parent
                                                print(
                                                    f"✅ Using parent as clickable element")
                                    except:
                                        pass

                                    nutrition_entries.append(clickable_element)
                                    all_found_elements.append(element_text)
                                    print(
                                        f"✅ Added current week entry: {element_text}")
                        except Exception as e:
                            print(f"⚠️ Error checking element: {e}")
                            continue
                except Exception as e:
                    print(f"⚠️ Error finding {target_calories}: {e}")
                    continue

            print(
                f"✅ Found {len(nutrition_entries)} current week nutrition entries")
            print(f"📋 Current week entries: {all_found_elements}")

            # If we didn't find the specific entries, fall back to general search
            if len(nutrition_entries) == 0:
                print("🔍 Step 3: No specific entries found, trying general search...")

                nutrition_selectors = [
                    "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                    "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Cals')]",
                    "//a[contains(text(), 'Cals') and contains(text(), 'Meal')]",
                    "//button[contains(text(), 'Cals') and contains(text(), 'Meal')]"
                ]

                for i, selector in enumerate(nutrition_selectors, 1):
                    try:
                        elements = self.driver.find_elements(
                            By.XPATH, selector)
                        print(
                            f"🔍 Selector {i}: Found {len(elements)} elements")

                        for element in elements:
                            try:
                                if element.is_displayed():
                                    element_text = element.text.strip()

                                    # Only include entries that match our current week pattern
                                    if any(target in element_text for target in current_week_calories):
                                        print(
                                            f"📊 Found current week nutrition: '{element_text}'")
                                        nutrition_entries.append(element)
                                        all_found_elements.append(element_text)
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"⚠️ Error with selector {i}: {e}")
                        continue

            detailed_meals = []

            # Step 4: Try to click on nutrition entries and extract details
            print(
                f"🍎 Step 4: Analyzing {len(nutrition_entries)} current week nutrition entries...")

            for i, entry in enumerate(nutrition_entries, 1):
                try:
                    print(
                        f"\n🍎 === Analyzing nutrition entry {i}/{len(nutrition_entries)} ===")

                    # Get the entry text first
                    try:
                        entry_text = entry.text.strip()
                        print(f"📊 Entry: {entry_text}")
                    except:
                        entry_text = f"Entry {i}"
                        print(
                            f"📊 Could not get entry text, using: {entry_text}")

                    # Try to click on the nutrition entry
                    try:
                        print(f"🖱️ Attempting to click nutrition entry...")

                        # Scroll element into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", entry)
                        time.sleep(1)

                        # Try different click methods
                        click_successful = False

                        # Method 1: Regular click
                        try:
                            entry.click()
                            click_successful = True
                            print(f"✅ Regular click successful")
                        except Exception as e1:
                            print(f"⚠️ Regular click failed: {e1}")

                            # Method 2: JavaScript click
                            try:
                                self.driver.execute_script(
                                    "arguments[0].click();", entry)
                                click_successful = True
                                print(f"✅ JavaScript click successful")
                            except Exception as e2:
                                print(f"⚠️ JavaScript click failed: {e2}")

                        if click_successful:
                            print(f"✅ Successfully clicked nutrition entry")
                            time.sleep(4)  # Wait longer for details to load

                            # Skip MyFitnessPal link clicking - analyze popup content directly
                            print(
                                "🔍 Analyzing popup content directly (skipping MyFitnessPal link)...")
                            # Wait for popup content to load
                            time.sleep(3)

                            # Take a screenshot of the popup for debugging
                            popup_screenshot = None
                            try:
                                popup_screenshot = f"nutrition_popup_{i}.png"
                                self.driver.save_screenshot(popup_screenshot)
                                print(
                                    f"📸 Saved popup screenshot: {popup_screenshot}")
                            except:
                                pass

                            # Extract detailed meal information using both methods
                            print(f"🔍 Extracting detailed meal information...")

                            # Method 1: Try programmatic extraction
                            meal_details = self.extract_detailed_meal_info()
                            meal_details['summary'] = entry_text

                            # Method 2: Use Gemini AI to analyze the popup screenshot
                            if popup_screenshot and self.gemini_api_key:
                                print(
                                    f"🤖 Analyzing popup screenshot with Gemini AI...")
                                gemini_meal_details = self.analyze_popup_screenshot_with_gemini(
                                    popup_screenshot)

                                # Merge Gemini results with programmatic results
                                if gemini_meal_details:
                                    # Use Gemini's detailed food items if available
                                    if gemini_meal_details.get('foods_by_meal'):
                                        meal_details['foods_by_meal'] = gemini_meal_details['foods_by_meal']

                                    # Use Gemini's meal details if more complete
                                    if gemini_meal_details.get('detailed_meals'):
                                        meal_details['detailed_meals'] = gemini_meal_details['detailed_meals']

                                    # Use Gemini's total calories if available
                                    if gemini_meal_details.get('total_calories'):
                                        meal_details['total_calories'] = gemini_meal_details['total_calories']

                                    # Use Gemini's date if available
                                    if gemini_meal_details.get('date'):
                                        meal_details['date'] = gemini_meal_details['date']

                                    print(
                                        f"✅ Enhanced meal details with Gemini AI analysis")

                            detailed_meals.append(meal_details)

                            print(
                                f"✅ Successfully extracted meal details for: {entry_text}")
                            print(
                                f"📊 Meals found: {list(meal_details.get('meals', {}).keys())}")

                            # Count total food items from both sources
                            total_food_items = sum(len(foods) for foods in meal_details.get(
                                'foods_by_meal', {}).values())
                            print(
                                f"🥗 Total food items extracted: {total_food_items}")

                            # Print summary of what we found
                            for meal_type, foods in meal_details.get('foods_by_meal', {}).items():
                                print(f"  {meal_type}: {len(foods)} foods")
                                # Show first few food items as examples
                                for food in foods[:2]:
                                    print(f"    • {food}")
                                if len(foods) > 2:
                                    print(
                                        f"    • ... and {len(foods) - 2} more")
                        else:
                            print(f"❌ Could not click nutrition entry")
                            # Still add basic info even if we can't click
                            meal_details = {
                                'summary': entry_text,
                                'meals': {},
                                'macros': {},
                                'foods_by_meal': {},
                                'note': 'Could not access detailed view - click failed'
                            }
                            detailed_meals.append(meal_details)

                    except Exception as click_error:
                        print(
                            f"⚠️ Error clicking nutrition entry: {click_error}")
                        # Still add basic info even if we can't click
                        meal_details = {
                            'summary': entry_text,
                            'meals': {},
                            'macros': {},
                            'foods_by_meal': {},
                            'note': f'Could not access detailed view - error: {click_error}'
                        }
                        detailed_meals.append(meal_details)

                    # Try to close any open details view
                    try:
                        print(f"🔄 Attempting to close details view...")
                        close_buttons = [
                            "//button[contains(@aria-label, 'Close')]",
                            "//button[contains(text(), 'Close')]",
                            "//button[contains(@class, 'close')]",
                            "//*[@role='button' and contains(@aria-label, 'close')]",
                            "//button[contains(@class, 'modal-close')]",
                            "//*[contains(@class, 'close-button')]"
                        ]

                        close_successful = False
                        for close_selector in close_buttons:
                            try:
                                close_button = self.driver.find_element(
                                    By.XPATH, close_selector)
                                if close_button.is_displayed():
                                    close_button.click()
                                    close_successful = True
                                    print(f"✅ Closed details view")
                                    time.sleep(1)
                                    break
                            except:
                                continue

                        if not close_successful:
                            # Try pressing Escape key
                            try:
                                from selenium.webdriver.common.keys import Keys
                                self.driver.find_element(
                                    By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                print(f"✅ Closed details view with Escape key")
                                time.sleep(1)
                            except:
                                print(f"⚠️ Could not close details view")
                    except:
                        pass

                except Exception as e:
                    print(f"⚠️ Error analyzing nutrition entry {i}: {e}")
                    continue

            print(
                f"\n✅ Completed analysis of {len(detailed_meals)} current week nutrition entries")
            return detailed_meals

        except Exception as e:
            print(f"❌ Error analyzing detailed nutrition entries: {e}")
            return []

    def extract_detailed_meal_info(self):
        """Extract detailed meal information from the current nutrition popup."""
        try:
            meal_info = {
                "date": "",
                "total_calories": "",
                "meals": {},
                "macros": {},
                "foods_by_meal": {}
            }

            print("🔍 Looking for detailed meal information in popup...")

            # Wait a moment for the popup to fully load
            time.sleep(2)

            # STEP 1: Scroll within the popup to see all content
            print("📜 Scrolling within popup to see all meal details...")
            try:
                # Try to find the popup container and scroll within it
                popup_containers = [
                    "//div[contains(@class, 'modal')]",
                    "//div[contains(@class, 'popup')]",
                    "//div[contains(@class, 'dialog')]",
                    "//div[contains(@role, 'dialog')]",
                    "//div[contains(@class, 'overlay')]"
                ]

                popup_container = None
                for container_selector in popup_containers:
                    try:
                        containers = self.driver.find_elements(
                            By.XPATH, container_selector)
                        for container in containers:
                            if container.is_displayed():
                                popup_container = container
                                print(
                                    f"✅ Found popup container: {container_selector}")
                                break
                        if popup_container:
                            break
                    except:
                        continue

                # Scroll down within the popup to reveal all content
                if popup_container:
                    for scroll_attempt in range(3):
                        try:
                            self.driver.execute_script(
                                "arguments[0].scrollTop += 300;", popup_container)
                            time.sleep(0.5)
                            print(
                                f"📜 Scrolled in popup (attempt {scroll_attempt + 1})")
                        except:
                            break
                else:
                    # If we can't find popup container, try scrolling the page
                    print("⚠️ Could not find popup container, scrolling page")
                    self.driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Error scrolling in popup: {e}")

            # STEP 2: Debug - show ALL text in the popup
            print("🔍 DEBUG: Showing ALL text visible in popup...")
            try:
                all_text_elements = self.driver.find_elements(
                    By.XPATH, "//*[text()]")
                visible_texts = []
                for elem in all_text_elements:
                    try:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            if text and len(text) > 0 and len(text) < 200:
                                visible_texts.append(text)
                    except:
                        continue

                print(f"📋 Found {len(visible_texts)} text elements in popup:")
                for i, text in enumerate(visible_texts[:20]):  # Show first 20
                    print(f"  {i+1}. '{text}'")
                if len(visible_texts) > 20:
                    print(f"  ... and {len(visible_texts) - 20} more")
            except Exception as e:
                print(f"⚠️ Error getting popup text: {e}")

            # STEP 3: Look for "Individual meal details" section
            print("🔍 Looking for 'Individual meal details' section...")
            try:
                individual_meal_headers = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Individual meal details')]")
                if individual_meal_headers:
                    print("✅ Found 'Individual meal details' section")
                else:
                    print(
                        "⚠️ 'Individual meal details' section not found, looking for meal structure anyway")
            except:
                pass

            # STEP 3: Try to get the date from the popup
            try:
                date_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(text(), 'Jun 2025') or contains(text(), 'June 2025') or contains(text(), '2025')]")
                for elem in date_elements:
                    text = elem.text.strip()
                    if any(month in text for month in ['Jun', 'June']) and '2025' in text:
                        meal_info["date"] = text
                        print(f"📅 Found date: {text}")
                        break
            except:
                pass

            # STEP 4: Look for meal sections - Updated to match the exact structure in the image
            meal_sections = ["Breakfast", "Lunch", "Dinner", "Snacks", "Snack"]

            print("🍽️ Looking for meal sections with exact structure...")
            for meal_type in meal_sections:
                try:
                    print(f"🔍 Searching for {meal_type} section...")

                    # Look for meal headers that show calories (e.g., "Breakfast 362 Cal")
                    meal_header_selectors = [
                        f"//*[contains(text(), '{meal_type}') and contains(text(), 'Cal')]",
                        f"//*[text()='{meal_type}']",
                        f"//h1[contains(text(), '{meal_type}')]",
                        f"//h2[contains(text(), '{meal_type}')]",
                        f"//h3[contains(text(), '{meal_type}')]",
                        f"//h4[contains(text(), '{meal_type}')]",
                        f"//div[contains(text(), '{meal_type}')]",
                        f"//strong[contains(text(), '{meal_type}')]",
                        f"//b[contains(text(), '{meal_type}')]"
                    ]

                    meal_found = False
                    for selector in meal_header_selectors:
                        try:
                            meal_header_elements = self.driver.find_elements(
                                By.XPATH, selector)

                            for header in meal_header_elements:
                                if header.is_displayed():
                                    header_text = header.text.strip()
                                    print(
                                        f"🍽️ Found potential meal header: '{header_text}'")

                                    if meal_type in header_text:
                                        meal_info["meals"][meal_type] = header_text
                                        print(
                                            f"✅ Confirmed {meal_type} header: {header_text}")

                                        # Now find the food items under this meal
                                        foods_for_meal = []

                                        try:
                                            # Get the position of this meal header
                                            header_location = header.location
                                            header_y = header_location['y']

                                            print(
                                                f"🔍 Looking for food items below {meal_type} header...")

                                            # Find all text elements and look for food items positioned below this header
                                            all_elements = self.driver.find_elements(
                                                By.XPATH, "//*[text()]")

                                            for elem in all_elements:
                                                try:
                                                    if elem.is_displayed():
                                                        elem_location = elem.location
                                                        elem_y = elem_location['y']

                                                        # Only consider elements below this meal header (within 200px)
                                                        if elem_y > header_y and elem_y < (header_y + 200):
                                                            text = elem.text.strip()

                                                            # Look for food item patterns like:
                                                            # "Caramel Oreo Weetbix, 1 serving (362 Cal)"
                                                            # "Beef Oyster Blade - Steak, 300 g (403 Cal)"
                                                            if (len(text) > 15 and len(text) < 200 and
                                                                    'Cal' in text and
                                                                    # Food items have commas or dashes
                                                                    (',' in text or '-' in text) and
                                                                    any(food_indicator in text.lower() for food_indicator in [
                                                                        'serving', 'g', 'gram', 'cup', 'slice', 'piece', 'ml', 'oz'
                                                                    ]) and
                                                                    not any(skip_word in text.lower() for skip_word in [
                                                                        'goal', 'remaining', 'total', 'macro', 'protein', 'carb', 'fat',
                                                                        'button', 'close', 'save', 'cancel', 'edit', meal_type.lower()
                                                                    ])):
                                                                foods_for_meal.append(
                                                                    text)
                                                                print(
                                                                    f"  🥗 Found food item: {text}")
                                                except:
                                                    continue

                                            # Also try a more specific approach - look for elements that are siblings or children
                                            try:
                                                # Look for elements that come after this header in the DOM
                                                following_elements = header.find_elements(
                                                    By.XPATH, "./following::*[text()]")

                                                # Limit to next 10 elements
                                                for elem in following_elements[:10]:
                                                    try:
                                                        if elem.is_displayed():
                                                            text = elem.text.strip()

                                                            # Stop if we hit another meal section
                                                            if any(other_meal in text for other_meal in meal_sections if other_meal != meal_type):
                                                                break

                                                            # Look for food patterns
                                                            if (len(text) > 15 and len(text) < 200 and
                                                                    'Cal' in text and
                                                                    (',' in text or '-' in text) and
                                                                    any(food_indicator in text.lower() for food_indicator in [
                                                                        'serving', 'g', 'gram', 'cup', 'slice', 'piece', 'ml', 'oz'
                                                                    ]) and
                                                                    not any(skip_word in text.lower() for skip_word in [
                                                                        'goal', 'remaining', 'total', 'macro', 'protein', 'carb', 'fat',
                                                                        'button', 'close', 'save', 'cancel', 'edit'
                                                                    ])):
                                                                if text not in foods_for_meal:  # Avoid duplicates
                                                                    foods_for_meal.append(
                                                                        text)
                                                                    print(
                                                                        f"  🥗 Found following food: {text}")
                                                    except:
                                                        continue
                                            except:
                                                pass

                                        except Exception as e:
                                            print(
                                                f"⚠️ Error finding foods for {meal_type}: {e}")

                                        # Store the foods for this meal
                                        if foods_for_meal:
                                            # Remove duplicates while preserving order
                                            unique_foods = []
                                            seen = set()
                                            for food in foods_for_meal:
                                                if food.lower() not in seen:
                                                    unique_foods.append(food)
                                                    seen.add(food.lower())

                                            # Limit to 8 items
                                            meal_info["foods_by_meal"][meal_type] = unique_foods[:8]
                                            print(
                                                f"✅ Found {len(unique_foods)} foods for {meal_type}")
                                        else:
                                            print(
                                                f"⚠️ No foods found for {meal_type}")

                                        meal_found = True
                                        break

                            if meal_found:
                                break
                        except Exception as e:
                            print(f"⚠️ Error with selector {selector}: {e}")
                            continue

                    if not meal_found:
                        print(f"⚠️ Could not find {meal_type} section")

                except Exception as e:
                    print(f"⚠️ Error processing meal {meal_type}: {e}")
                    continue

            # STEP 5: Look for macro information (Protein, Carbs, Fat)
            print("📊 Looking for macro information...")
            try:
                macro_patterns = {
                    "protein": ["Protein", "protein"],
                    "carbs": ["Carbs", "Carbohydrates", "carbs"],
                    "fat": ["Fat", "fat"],
                    "calories": ["Calories", "calories", "kcal", "Cal"]
                }

                for macro_name, patterns in macro_patterns.items():
                    for pattern in patterns:
                        try:
                            macro_elements = self.driver.find_elements(
                                By.XPATH, f"//*[contains(text(), '{pattern}') and (contains(text(), 'g') or contains(text(), 'cal'))]")
                            for elem in macro_elements:
                                if elem.is_displayed():
                                    text = elem.text.strip()
                                    if any(char.isdigit() for char in text) and (('g' in text and macro_name != 'calories') or ('cal' in text.lower() and macro_name == 'calories')):
                                        meal_info["macros"][macro_name] = text
                                        print(
                                            f"📊 Found macro: {macro_name} = {text}")
                                        break
                        except:
                            continue
            except:
                pass

            # STEP 6: Try to get total calories from the page
            print("🔥 Looking for total calories...")
            try:
                total_cal_selectors = [
                    "//*[contains(text(), 'Cal') and (contains(text(), 'Total') or contains(text(), 'total'))]",
                    "//*[contains(text(), 'kcal') and (contains(text(), 'Total') or contains(text(), 'total'))]",
                    "//h1[contains(text(), 'Cal')]",
                    "//h2[contains(text(), 'Cal')]"
                ]

                for selector in total_cal_selectors:
                    try:
                        total_cal_elements = self.driver.find_elements(
                            By.XPATH, selector)
                        for elem in total_cal_elements:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                if 'cal' in text.lower() and any(char.isdigit() for char in text):
                                    meal_info["total_calories"] = text
                                    print(f"🔥 Found total calories: {text}")
                                    break
                    except:
                        continue
                    if meal_info["total_calories"]:
                        break
            except:
                pass

            print(
                f"✅ Meal extraction complete. Found {len(meal_info['meals'])} meals, {sum(len(foods) for foods in meal_info['foods_by_meal'].values())} food items")
            return meal_info

        except Exception as e:
            print(f"❌ Error extracting meal info: {e}")
            return {"error": str(e), "meals": {}, "macros": {}, "foods_by_meal": {}}

    def analyze_walking_from_screenshot(self, screenshot_path):
        """Analyze walking activities from the current week screenshot using Gemini."""
        if not self.gemini_api_key or not screenshot_path:
            return {"walking_count": 0, "walking_days": [], "analysis": "No screenshot or API key available"}

        try:
            print("🚶 Analyzing walking activities from screenshot...")

            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')

            with open(screenshot_path, 'rb') as image_file:
                image_data = image_file.read()

            image_parts = [{
                "mime_type": "image/png",
                "data": image_data
            }]

            prompt = """Analyze this Trainerize calendar screenshot focusing ONLY on WALKING ACTIVITIES.

Look very carefully for:
- Text that says "Walking" 
- Checkmarks ✓ next to walking entries (completed)
- Empty circles ○ next to walking entries (planned but not completed)
- Any distance measurements like "2.58 km", "1.6 km"

Examine EACH DAY in the calendar (look at day numbers 9, 10, 11, 12, 13, 14, 15) for walking activities.

Format your response EXACTLY like this:
**WALKING ACTIVITIES FOUND:**
- Day 9: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 10: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 11: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 12: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 13: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 14: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]
- Day 15: [COMPLETED ✓] OR [PLANNED ○] OR [NO WALKING]

**SUMMARY:**
- Total completed walks: X
- Total planned walks: X
- Days with completed walking: [list day numbers]

IMPORTANT: Look carefully for the word "Walking" in each day box and check if it has a checkmark ✓ or empty circle ○."""

            response = model.generate_content([prompt, image_parts[0]])

            print(f"🔍 Gemini walking analysis response: {response.text}")

            # Parse the response to count walking activities
            walking_days = []
            walking_count = 0

            # Look for completed walks
            import re
            completed_pattern = r"Day (\d+): \[COMPLETED ✓\]"
            planned_pattern = r"Day (\d+): \[PLANNED ○\]"

            completed_matches = re.findall(completed_pattern, response.text)
            planned_matches = re.findall(planned_pattern, response.text)

            for day_num in completed_matches:
                walking_days.append(f"Day {day_num} (Completed)")
                walking_count += 1

            for day_num in planned_matches:
                walking_days.append(f"Day {day_num} (Planned)")

            print(
                f"✅ Parsed walking data: {walking_count} completed, {len(planned_matches)} planned")

            return {
                "walking_count": walking_count,
                "walking_days": walking_days,
                "analysis": response.text
            }

        except Exception as e:
            print(f"❌ Error analyzing walking from screenshot: {e}")
            return {"walking_count": 0, "walking_days": [], "analysis": f"Error: {e}"}

    def analyze_weight_from_screenshot(self, screenshot_path):
        """Analyze weight entries from the current week screenshot using Gemini."""
        if not self.gemini_api_key or not screenshot_path:
            return {"weight_entries": [], "analysis": "No screenshot or API key available"}

        try:
            print("⚖️ Analyzing weight entries from screenshot...")

            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')

            with open(screenshot_path, 'rb') as image_file:
                image_data = image_file.read()

            image_parts = [{
                "mime_type": "image/png",
                "data": image_data
            }]

            prompt = """Analyze this Trainerize calendar screenshot focusing ONLY on WEIGHT/BODY MEASUREMENTS.

Look very carefully for:
- Weight measurements like "79.1 kg", "78.5 kg", "80.2 kg"
- Body stats entries
- Any text containing "kg" or weight-related information
- Photos or body measurement entries

Examine EACH DAY in the calendar (look at day numbers 9, 10, 11, 12, 13, 14, 15) for weight entries.

Format your response EXACTLY like this:
**WEIGHT ENTRIES FOUND:**
- Day 9: [79.1 kg] OR [NO WEIGHT ENTRY]
- Day 10: [78.5 kg] OR [NO WEIGHT ENTRY]
- Day 11: [80.2 kg] OR [NO WEIGHT ENTRY]
- Day 12: [XX.X kg] OR [NO WEIGHT ENTRY]
- Day 13: [XX.X kg] OR [NO WEIGHT ENTRY]
- Day 14: [XX.X kg] OR [NO WEIGHT ENTRY]
- Day 15: [XX.X kg] OR [NO WEIGHT ENTRY]

**SUMMARY:**
- Total weight entries: X
- Days with weight tracking: [list the day numbers]

IMPORTANT: Look carefully for any text containing "kg" or weight measurements in each day box."""

            response = model.generate_content([prompt, image_parts[0]])

            print(f"🔍 Gemini weight analysis response: {response.text}")

            # Parse the response to extract weight entries
            weight_entries = []

            # Look for the pattern "Day X: [XX.X kg]"
            import re
            weight_pattern = r"Day (\d+): \[([0-9.]+\s*kg)\]"
            matches = re.findall(weight_pattern, response.text)

            for day_num, weight_value in matches:
                weight_entries.append(f"Day {day_num}: {weight_value}")

            print(f"✅ Parsed weight entries: {weight_entries}")

            return {
                "weight_entries": weight_entries,
                "analysis": response.text
            }

        except Exception as e:
            print(f"❌ Error analyzing weight from screenshot: {e}")
            return {"weight_entries": [], "analysis": f"Error: {e}"}

    def analyze_popup_screenshot_with_gemini(self, screenshot_path):
        """Analyze a nutrition popup screenshot with Gemini to extract detailed meal information."""
        if not self.gemini_api_key:
            print("⚠️ Gemini API key not configured for popup analysis.")
            return None
        if not screenshot_path or not os.path.exists(screenshot_path):
            print(f"⚠️ Screenshot not found at {screenshot_path}")
            return None

        try:
            print(
                f"🔍 Analyzing nutrition popup with Gemini: {screenshot_path}")

            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')

            with open(screenshot_path, 'rb') as image_file:
                image_data = image_file.read()

            image_parts = [{
                "mime_type": "image/png",
                "data": image_data
            }]

            prompt = """Analyze this Trainerize nutrition popup screenshot and extract ALL detailed meal information.

CRITICAL: Look very carefully for meal sections and food items. The format typically shows:

**MEAL SECTIONS** (like "Breakfast", "Lunch", "Dinner", "Snacks"):
- Each meal section shows total calories for that meal
- Under each meal are individual food items with their calories

**FOOD ITEMS** (like):
- "thick bacon - Bacon, 2 slices (90 Cal)"
- "Sourdough - Sourdough, 100 g (222 Cal)" 
- "Caramel Oreo Weetbix, 1 serving (362 Cal)"
- "Beef Oyster Blade - Steak, 300 g (403 Cal)"
- "SHDLCK - Whey Protein Isolate Chocolate, 35 gram (135 Cal)"
- "Rolled Oats Home Brand - Oats, 40 gram (155 Cal)"

**MACRO INFORMATION**:
- Look for Protein, Carbs, Fat values (like "Protein 105g", "Carbs 140g", "Fat 47g")

**TOTAL CALORIES**:
- Look for total daily calories

Please extract and format the information EXACTLY like this:

**DATE:** [Date if visible]

**TOTAL CALORIES:** [Total calories for the day]

**MACROS:**
- Protein: [X]g
- Carbs: [X]g  
- Fat: [X]g

**DETAILED MEALS:**

**BREAKFAST ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**LUNCH ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**DINNER ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

**SNACKS ([X] Cal):**
- [Food item 1 with calories]
- [Food item 2 with calories]
- [etc...]

IMPORTANT: 
- Extract EVERY food item you can see, even if the text is small
- Include the exact calorie amounts for each food item
- If you can't see a meal section, write "NOT VISIBLE"
- Be very thorough - this is detailed nutrition tracking data"""

            response = model.generate_content([prompt, image_parts[0]])

            if response and response.text:
                print("✅ Gemini popup analysis complete.")

                # Parse the Gemini response to extract structured data
                parsed_data = self.parse_gemini_nutrition_response(
                    response.text)
                return parsed_data
            else:
                print("⚠️ No response from Gemini")
                return None

        except Exception as e:
            print(f"❌ Error during Gemini popup analysis: {e}")
            return None

    def parse_gemini_nutrition_response(self, gemini_text):
        """Parse Gemini's nutrition analysis response into structured data."""
        try:
            parsed_data = {
                "date": "",
                "total_calories": "",
                "foods_by_meal": {},
                "detailed_meals": {},
                "macros": {}
            }

            lines = gemini_text.split('\n')
            current_meal = None

            for line in lines:
                line = line.strip()

                # Extract date
                if 'DATE:' in line.upper() or ('Jun' in line and '2025' in line):
                    parsed_data["date"] = line.replace(
                        '**DATE:**', '').replace('*', '').strip()

                # Extract total calories
                if 'TOTAL CALORIES:' in line.upper():
                    parsed_data["total_calories"] = line.replace(
                        '**TOTAL CALORIES:**', '').replace('*', '').strip()

                # Extract macros
                if 'Protein:' in line and 'g' in line:
                    parsed_data["macros"]["protein"] = line.replace(
                        '-', '').strip()
                elif 'Carbs:' in line and 'g' in line:
                    parsed_data["macros"]["carbs"] = line.replace(
                        '-', '').strip()
                elif 'Fat:' in line and 'g' in line:
                    parsed_data["macros"]["fat"] = line.replace(
                        '-', '').strip()

                # Detect meal sections
                if line.upper().startswith('**BREAKFAST'):
                    current_meal = 'Breakfast'
                    parsed_data["foods_by_meal"][current_meal] = []
                    parsed_data["detailed_meals"][current_meal] = line.replace(
                        '*', '').strip()
                elif line.upper().startswith('**LUNCH'):
                    current_meal = 'Lunch'
                    parsed_data["foods_by_meal"][current_meal] = []
                    parsed_data["detailed_meals"][current_meal] = line.replace(
                        '*', '').strip()
                elif line.upper().startswith('**DINNER'):
                    current_meal = 'Dinner'
                    parsed_data["foods_by_meal"][current_meal] = []
                    parsed_data["detailed_meals"][current_meal] = line.replace(
                        '*', '').strip()
                elif line.upper().startswith('**SNACKS'):
                    current_meal = 'Snacks'
                    parsed_data["foods_by_meal"][current_meal] = []
                    parsed_data["detailed_meals"][current_meal] = line.replace(
                        '*', '').strip()

                # Extract food items (lines starting with -)
                elif line.startswith('-') and current_meal and 'Cal' in line:
                    food_item = line[1:].strip()  # Remove the leading dash
                    if len(food_item) > 10 and 'NOT VISIBLE' not in food_item.upper():
                        parsed_data["foods_by_meal"][current_meal].append(
                            food_item)

            # Clean up empty meals
            parsed_data["foods_by_meal"] = {
                k: v for k, v in parsed_data["foods_by_meal"].items() if v}

            print(
                f"📊 Parsed Gemini data: {len(parsed_data['foods_by_meal'])} meals with {sum(len(foods) for foods in parsed_data['foods_by_meal'].values())} food items")

            return parsed_data

        except Exception as e:
            print(f"❌ Error parsing Gemini response: {e}")
            return None


def main():
    """Main function to run the calendar analysis."""
    print("🚀 DEBUG: Starting main() function")
    print("🚀 DEBUG: About to set credentials")

    # Credentials are now hardcoded here.
    # IMPORTANT: Replace these placeholders with your actual credentials.
    username = "shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
    client_name = "Alice Forster"

    print("🚀 DEBUG: Credentials set, about to print startup messages")
    print("🚀 Calendar Analysis Script Started")
    print("=" * 50)

    print("🚀 DEBUG: About to check credentials")
    if not username or not password or username == "your_trainerize_email@example.com":
        print("🛑 Critical Error: Please replace the placeholder username and password in the script.")
        return

    if not gemini_api_key or gemini_api_key == "your_gemini_api_key":
        print(
            "🛑 Critical Error: Please replace the placeholder gemini_api_key in the script.")
        return

    print("🚀 DEBUG: Credentials validated, about to start analysis")
    print(f"📋 Analyzing calendar for client: {client_name}")

    print("🚀 DEBUG: About to create CalendarAnalyzer instance")
    analyzer = None
    try:
        analyzer = CalendarAnalyzer(gemini_api_key=gemini_api_key)
        print("🚀 DEBUG: CalendarAnalyzer created successfully")

        print("🔐 Logging into Trainerize...")
        if analyzer.login(username, password):
            print("✅ Login successful!")

            print(f"🎯 Navigating to client: {client_name}")
            if analyzer.navigate_to_client(client_name):
                print("✅ Client navigation successful!")

                print("📅 Opening calendar tab...")
                # Check if we're already on the calendar page
                if analyzer.is_on_calendar_page():
                    print("✅ Already on calendar page!")
                    calendar_opened = True
                else:
                    calendar_opened = analyzer.click_calendar_tab()
                    if calendar_opened:
                        print("✅ Calendar tab opened!")

                if calendar_opened:
                    print("📸 Taking calendar screenshot...")
                    screenshot = analyzer.take_calendar_screenshot(client_name)
                    if screenshot:
                        print(f"✅ Screenshot saved: {screenshot}")

                        print("🔍 Analyzing detailed workout and nutrition data...")
                        current_week_data = analyzer.analyze_detailed_calendar_data()

                        # Check if we got meaningful data
                        has_meaningful_data = (
                            current_week_data and (
                                len(current_week_data.get('nutrition_tracking_days', [])) > 0 or
                                current_week_data.get('walking_activities', 0) > 0 or
                                len(current_week_data.get('weight_entries', [])) > 0 or
                                len(current_week_data.get(
                                    'detailed_meals', [])) > 0
                            )
                        )

                        if has_meaningful_data:
                            print("📊 Generating comprehensive detailed report...")
                            comprehensive_report = analyzer.generate_comprehensive_report(
                                current_week_data)
                            analysis_result = comprehensive_report
                        else:
                            print(
                                "❌ No meaningful data found, trying calendar reload...")

                            # Try to reload the calendar and retry once
                            print("🔄 Attempting to reload calendar...")
                            analyzer.driver.refresh()
                            time.sleep(5)

                            # Navigate back to calendar
                            if analyzer.click_calendar_tab():
                                print("✅ Calendar reloaded, retrying analysis...")
                                time.sleep(3)

                                # Take new screenshot
                                screenshot = analyzer.take_calendar_screenshot(
                                    client_name)
                                if screenshot:
                                    # Retry analysis
                                    current_week_data = analyzer.analyze_detailed_calendar_data()

                                    # Check again for meaningful data
                                    has_meaningful_data = (
                                        current_week_data and (
                                            len(current_week_data.get('nutrition_tracking_days', [])) > 0 or
                                            current_week_data.get('walking_activities', 0) > 0 or
                                            len(current_week_data.get('weight_entries', [])) > 0 or
                                            len(current_week_data.get(
                                                'detailed_meals', [])) > 0
                                        )
                                    )

                                    if has_meaningful_data:
                                        print(
                                            "📊 Generating comprehensive detailed report (retry)...")
                                        comprehensive_report = analyzer.generate_comprehensive_report(
                                            current_week_data)
                                        analysis_result = comprehensive_report
                                    else:
                                        print(
                                            "❌ Still no meaningful data after retry, falling back to AI analysis...")
                                        print("🤖 Analyzing calendar with AI...")
                                        analysis_result = analyzer.analyze_calendar_with_gemini(
                                            screenshot)
                                else:
                                    print(
                                        "❌ Screenshot failed on retry, falling back to AI analysis...")
                                    print("🤖 Analyzing calendar with AI...")
                                    analysis_result = analyzer.analyze_calendar_with_gemini(
                                        screenshot)
                            else:
                                print(
                                    "❌ Could not reload calendar, falling back to AI analysis...")
                                print("🤖 Analyzing calendar with AI...")
                                analysis_result = analyzer.analyze_calendar_with_gemini(
                                    screenshot)

                        if analysis_result:
                            print("\n" + "=" * 60)
                            print(
                                f"📊 COMPREHENSIVE CALENDAR ANALYSIS - {client_name.upper()}")
                            print("=" * 60)
                            print(analysis_result)
                            print("=" * 60)

                            # Save analysis to file
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            analysis_filename = f"{client_name.replace(' ', '_')}_calendar_analysis_{timestamp}.txt"

                            try:
                                with open(analysis_filename, 'w', encoding='utf-8') as f:
                                    f.write(
                                        f"Calendar Analysis for {client_name}\n")
                                    f.write(
                                        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    f.write("=" * 60 + "\n\n")
                                    f.write(analysis_result)
                                print(
                                    f"💾 Analysis saved to: {analysis_filename}")
                            except Exception as e:
                                print(f"⚠️ Could not save analysis file: {e}")
                        else:
                            print("❌ All analysis methods failed")
                    else:
                        print("❌ Screenshot failed")
                else:
                    print("❌ Could not open calendar tab")
            else:
                print("❌ Could not navigate to client")
        else:
            print("❌ Login failed")

    except Exception as e:
        print(f"💥 Critical error occurred: {e}")
        logging.error(f"A critical error occurred in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🚀 DEBUG: Entering finally block")
        if analyzer:
            print("🧹 Cleaning up...")
            analyzer.cleanup()
            print("✅ Script finished successfully!")
        else:
            print("❌ Script finished with errors")
        print("🚀 DEBUG: Exiting main() function")


if __name__ == "__main__":
    main()
