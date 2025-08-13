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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, InvalidSessionIdException
from selenium.webdriver.common.keys import Keys
import sys
import sqlite3
import json


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='{asctime} - {levelname} - {message}',
            style='{',
            handlers=[
                logging.StreamHandler(
                    stream=sys.stdout)  # Ensure we are writing to stdout
            ],
            encoding='utf-8'  # Add UTF-8 encoding for handling special characters
        )
        logging.info("Initializing Chrome...")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        # Add options to speed up loading
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-gpu") # Removed: Potentially causing rendering issues
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Temporarily disabled for visual debugging
        # chrome_options.add_argument("--headless")
        # Removed: Blocking images, stylesheets, and fonts can interfere with rendering and element visibility
        # chrome_options.add_experimental_option("prefs", {
        #     "profile.managed_default_content_settings.images": 2,
        #     "profile.managed_default_content_settings.stylesheets": 2,
        #     "profile.managed_default_content_settings.fonts": 2,
        # })

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
            service = Service()
            self.driver = webdriver.Chrome(options=chrome_options)
            # Increased global timeout from 20 to 30 seconds for all waits
            self.wait = WebDriverWait(self.driver, 30)
            logging.info("Chrome initialized successfully!")
            # Initialize to store the original window handle
            self.original_window_handle = None
        except Exception as e:
            logging.error(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

        self.temp_dir = None
        self.original_clients_tab = None  # Store the original clients tab handle

    def handle_cookie_dialog(self):
        """Handle any cookie consent dialog that might appear"""
        try:
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "cookie-accept"))
            )
            cookie_button.click()
            logging.info("Accepted cookies")
            time.sleep(1)  # Added sleep after accepting cookies
        except Exception as e:
            logging.info("No cookie dialog found or error accepting cookies")
            return

    def handle_notification_popup(self):
        """Handle any notification popup that might appear after login"""
        try:
            # Increased wait for notification popup
            notification_button = self.wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "notification-button")))
            if notification_button:
                notification_button.click()
                logging.info("Dismissed notification popup")
                time.sleep(1)  # Added sleep after dismissing popup
        except TimeoutException:
            logging.info("No notification popup found within timeout.")
            return
        except Exception as e:
            logging.info(f"Error dismissing notification popup: {e}")
            return

    def dismiss_any_modal(self, timeout=5):
        """Attempts to dismiss any active modal or overlay.
        Looks for common close buttons or presses ESC.
        """
        logging.info("Attempting to dismiss any active modal...")
        # Try common close button locators
        close_locators = [
            (By.CSS_SELECTOR, "button.modal-close, button.ant-modal-close-x"),
            (By.XPATH,
             "//button[contains(text(), 'Close') or contains(text(), 'Dismiss')]"),
            (By.CSS_SELECTOR,
             "[data-testid*='closeButton'], [data-testid*='cancelButton']")
        ]

        for locator_type, locator_value in close_locators:
            try:
                close_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((locator_type, locator_value)))
                logging.info(
                    f"Found and clicked modal close button using: {locator_type} = {locator_value}")
                close_button.click()
                time.sleep(1)  # Give time for modal to close
                return True
            except TimeoutException:
                continue
            except ElementClickInterceptedException:
                logging.warning(
                    f"Modal close button {locator_type} = {locator_value} was intercepted, trying JS click.")
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", close_button)
                    time.sleep(1)
                    return True
                except Exception as js_e:
                    logging.warning(
                        f"JS click failed for modal close button: {js_e}")
                    continue
            except Exception as e:
                logging.warning(f"Error clicking modal close button: {e}")
                continue

        # If no button found, try pressing ESC
        try:
            logging.info("No explicit close button found, trying ESC key...")
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)  # Give time for modal to close
            # Verify if modal is gone by checking for common modal overlay elements
            modal_overlays = self.driver.find_elements(
                By.CSS_SELECTOR, ".modal-backdrop, .ReactModal__Overlay, .ant-modal-mask, .modal-wrap")
            if not any(o.is_displayed() for o in modal_overlays):  # If no visible overlays
                logging.info("Modal dismissed by ESC key.")
                return True
            else:
                logging.info(
                    "ESC key did not fully dismiss modal or no modal was present.")
                return False
        except Exception as e:
            logging.warning(f"Error sending ESC key: {e}")

        logging.info("No active modal found or could not dismiss it.")
        return False

    def login(self, username: str, password: str) -> bool:
        """Login to Trainerize with the given credentials"""
        try:
            logging.info("Navigating directly to Trainerize login page...")
            self.driver.get("https://www.trainerize.com/login.aspx")
            self.handle_cookie_dialog()

            logging.info("Scrolling down slightly...")
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(2)  # Increased sleep

            logging.info("Waiting for page to load...")
            self.wait.until(EC.presence_of_element_located((By.ID, "t_email")))

            logging.info("Entering initial email...")
            email_field = self.driver.find_element(By.ID, "t_email")
            email_field.clear()
            email_field.send_keys(username)

            logging.info("Clicking 'Find me' button...")
            find_me_button = self.driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(5)  # Increased sleep for page transition

            logging.info("Waiting for the second login page...")
            email_field_second = None
            email_selectors = [
                (By.ID, "emailInput"),
                (By.CSS_SELECTOR, "input[placeholder='Email']"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.XPATH,
                 "//input[contains(@placeholder, 'mail') or contains(@placeholder, 'Email')]"),
                (By.CSS_SELECTOR, "input.ant-input")
            ]

            for selector_type, selector_value in email_selectors:
                try:
                    email_field_second = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    logging.info(
                        f"Found second email field using: {selector_type} = {selector_value}")
                    break
                except TimeoutException:
                    continue

            if email_field_second is None:
                logging.error(
                    "Could not find second email field with any selector")
                return False

            logging.info("Clearing and entering full email on second page...")
            email_field_second.clear()
            time.sleep(1)  # Increased sleep
            email_field_second.send_keys(username)

            logging.info("Finding password field...")
            password_field = None
            password_selectors = [
                (By.ID, "passInput"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[placeholder*='assword']"),
                (By.XPATH, "//input[@type='password']")
            ]

            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(
                        selector_type, selector_value)
                    logging.info(
                        f"Found password field using: {selector_type} = {selector_value}")
                    break
                except NoSuchElementException:
                    continue

            if password_field is None:
                logging.error("Could not find password field")
                return False

            logging.info("Entering password...")
            password_field.clear()
            password_field.send_keys(password)

            logging.info("Looking for 'Sign In' button...")
            sign_in_button = None
            button_selectors = [
                (By.CSS_SELECTOR, "[data-testid='signIn-button']"),
                (By.XPATH, "//button[contains(text(), 'SIGN IN')]"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(@class, 'ant-btn-primary')]")
            ]

            for selector_type, selector_value in button_selectors:
                try:
                    sign_in_button = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    logging.info(
                        f"Found sign in button using: {selector_type} = {selector_value}")
                    break
                except TimeoutException:
                    continue

            if sign_in_button is None:
                logging.error("Could not find sign in button")
                return False

            logging.info("Clicking 'Sign In' button...")
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(10)  # Increased wait for login to complete

            logging.info("Verifying login success...")
            max_wait_time = 40  # Increased total wait for dashboard
            start_time = time.time()
            login_successful = False

            while time.time() - start_time < max_wait_time:
                current_url = self.driver.current_url
                page_title = self.driver.title.lower()

                success_indicators = [
                    "login" not in current_url.lower(),
                    "dashboard" in current_url.lower(),
                    "home" in current_url.lower(),
                    "client" in page_title,
                    "dashboard" in page_title,
                    "trainerize" in page_title and "login" not in page_title,
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='leftNavMenu']"))  # Check for sidebar
                ]

                if any(success_indicators):
                    logging.info(
                        f"Login success detected - URL: {current_url}, Title: {self.driver.title}")
                    # Handle specific notification popup immediately after login
                    self.handle_notification_popup()
                    self.dismiss_any_modal()  # Attempt to dismiss any general modal after login
                    login_successful = True
                    break

                try:  # Check for overlays that might block interaction
                    overlays = self.driver.find_elements(
                        By.CSS_SELECTOR, ".tr-loader, .modal-backdrop, .ReactModal__Overlay, .ant-modal-mask")
                    if any(o.is_displayed() for o in overlays):
                        logging.info(
                            "Loader/modal overlay detected during login verification. Waiting...")
                        time.sleep(2)  # Wait for overlay to disappear
                        continue  # Recheck page after waiting
                except:
                    pass

                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                               ".error, .alert, .warning, [class*='error'], [class*='alert']")
                    if error_elements:
                        error_text = " ".join(
                            [elem.text for elem in error_elements if elem.text])
                        if error_text:
                            logging.error(
                                f"Login error detected: {error_text}")
                            return False
                except:
                    pass

                time.sleep(1)

            if login_successful:
                logging.info("Successfully logged in!")
                # Store the main dashboard window handle after successful login
                self.original_window_handle = self.driver.current_window_handle
                logging.info(
                    f"Stored main dashboard window handle: {self.original_window_handle}")

                # --- NEW ADDITION: Temporary screenshot after successful login ---
                try:
                    screenshot_path = "debug_screenshot_after_login.png"
                    self.driver.save_screenshot(screenshot_path)
                    logging.info(
                        f"Screenshot taken after successful login: {screenshot_path}")
                except Exception as screenshot_e:
                    logging.error(
                        f"Failed to take screenshot after login: {screenshot_e}")
                # --- END NEW ADDITION ---

                return True
            else:
                logging.error(
                    f"Login verification failed after {max_wait_time}s - URL: {self.driver.current_url}")

                try:
                    page_source = self.driver.page_source[:500]
                    logging.debug(f"Page source sample: {page_source}")
                except:
                    pass

                return False

        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def click_element_safely(self, element, use_js=False, timeout=30):
        """Click element with retry logic and increased timeout"""
        def click_attempt():
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()

        try:
            # Wait for element to be clickable with a flexible timeout
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(element))
            return self.retry_on_stale_element(click_attempt)
        except TimeoutException:
            logging.error(f"Element not clickable within {timeout} seconds.")
            return False
        except Exception as e:
            logging.error(f"Error clicking element safely: {e}")
            return False

    def navigate_to_client(self, client_name: str) -> bool:
        """Navigate to a specific client's page with enhanced name matching and robust Open button detection"""
        try:
            display_name = self.transform_client_name(client_name)
            logging.info(
                f"Attempting to navigate to client: {client_name} (display name: {display_name})")

            self.dismiss_any_modal()  # Attempt to dismiss any modal before clicking Clients link

            def click_clients_link():
                logging.info("Clicking the 'Clients' link in the sidebar...")
                clients_link_locator = (
                    By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
                # Increased wait here
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
                time.sleep(5)  # Increased sleep after clicking clients link
                return True

            if not self.retry_on_stale_element(click_clients_link):
                logging.error("Failed to click Clients link")
                return False

            def search_for_client():
                logging.info(f"Searching for client: {display_name}")
                search_input_locator = (
                    By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
                # Increased wait here
                search_input = self.wait.until(
                    EC.presence_of_element_located(search_input_locator))
                search_input.clear()
                search_input.send_keys(display_name)
                time.sleep(5)  # Increased sleep for search results
                return True

            if not self.retry_on_stale_element(search_for_client):
                logging.error("Failed to search for client")
                return False

            client_link = None
            exact_match_selectors = [
                (By.XPATH, f"//a[contains(text(), '{display_name}')]"),
                (By.XPATH,
                 f"//td[contains(text(), '{display_name}')]/parent::tr//a"),
                (By.XPATH,
                 f"//div[contains(text(), '{display_name}')]/ancestor::tr//a"),
            ]

            for selector_type, selector_value in exact_match_selectors:
                try:
                    # Increased wait for exact client link
                    client_link = self.wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value)))
                    logging.info(f"Found exact match using: {selector_type}")
                    break
                except TimeoutException:
                    continue

            if not client_link:
                logging.info("No exact match found, trying fuzzy matching...")
                client_link = self.find_client_fuzzy(display_name)

            if not client_link:
                logging.error(f"Could not find client: {display_name}")
                return False

            def click_client_name():
                client_link.click()
                logging.info(f"Clicked client: {display_name}")
                time.sleep(5)  # Increased sleep after clicking client
                return True

            if not self.retry_on_stale_element(click_client_name):
                logging.error("Failed to click client name")
                return False

            def click_open_button():
                logging.info("Looking for 'Open' button...")
                open_selectors = [
                    (By.CSS_SELECTOR,
                     "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']"),
                    (By.XPATH, "//button[contains(text(), 'Open')]"),
                    (By.XPATH,
                     "//button[contains(@class, 'btn') and contains(text(), 'Open')]"),
                    (By.CSS_SELECTOR, "[data-testid*='switchIntoClient']"),
                    (By.XPATH,
                     "//button[contains(@class, 'ant-btn') and contains(text(), 'Open')]"),
                    (By.XPATH,
                     "//button[@type='button' and contains(text(), 'Open')]"),
                    (By.XPATH,
                     "//div[contains(@class, 'modal')]//button[contains(text(), 'Open')]"),
                    (By.XPATH, "//button[text()='Open']"),
                    (By.XPATH,
                     "//*[contains(text(), 'Open') and contains(@class, 'btn')]"),
                ]

                for i, (selector_type, selector_value) in enumerate(open_selectors, 1):
                    try:
                        logging.info(
                            f"Trying Open button selector {i}: {selector_type} = {selector_value}")
                        # Increased wait for open button
                        open_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((selector_type, selector_value)))
                        open_button.click()
                        logging.info(
                            f"Successfully clicked Open button using selector {i}")
                        time.sleep(5)  # Increased sleep for new tab
                        return True
                    except TimeoutException:
                        logging.info(f"Selector {i} failed, trying next...")
                        continue
                    except Exception as e:
                        logging.warning(f"Error with selector {i}: {e}")
                        continue

                try:
                    logging.info("Trying to find any button in modal...")
                    modal_buttons = self.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'modal')]//button | //div[contains(@class, 'ant-modal')]//button")

                    for button in modal_buttons:
                        button_text = button.text.strip().lower()
                        logging.info(f"Found modal button: '{button_text}'")
                        if 'open' in button_text or 'switch' in button_text:
                            button.click()
                            logging.info(
                                f"Clicked button with text: '{button_text}'")
                            time.sleep(5)
                            return True
                except Exception as e:
                    logging.error(f"Error finding modal buttons: {e}")

                raise Exception(
                    "Could not find clickable Open button with any selector")

            if not self.retry_on_stale_element(click_open_button):
                logging.error("Failed to click Open button")
                return False

            logging.info("Switching to the new tab...")
            # The `original_window` here refers to the window *from which* the new client tab was opened,
            # which should be the main dashboard handle if correctly managed.
            # We'll use `self.original_window_handle` directly for consistency.
            # original_window = self.driver.current_window_handle

            max_wait = 15  # Increased wait for new tab to open
            start_time = time.time()
            while len(self.driver.window_handles) < 2 and time.time() - start_time < max_wait:
                time.sleep(0.5)

            if len(self.driver.window_handles) < 2:
                logging.error("New tab did not open")
                return False

            for window_handle in self.driver.window_handles:
                if window_handle != self.original_window_handle:
                    self.driver.switch_to.window(window_handle)
                    break

            logging.info("Waiting for client dashboard to load...")
            time.sleep(3)  # Give time for the page to start rendering
            self.dismiss_any_modal()  # Dismiss any potential modals that appear after tab switch

            # --- NEW ADDITION: Wait for loaders to disappear ---
            try:
                logging.info(
                    "Waiting for any loading overlays to disappear...")
                WebDriverWait(self.driver, 20).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".tr-loader, .modal-backdrop, .ReactModal__Overlay, .ant-modal-mask, .spinner, .loading-indicator"))
                )
                logging.info("Loading overlays are clear.")
            except TimeoutException:
                logging.warning(
                    "Loading overlays still present after 20 seconds or no overlays found.")
            except Exception as e:
                logging.error(
                    f"Error while waiting for loaders to disappear: {e}")
            # --- END NEW ADDITION ---

            try:
                # Use new helper function here:
                self.find_element_with_refresh_retry(
                    (By.CSS_SELECTOR,
                     "h1.page-title, [data-testid='clientProfile-header'], a[data-testid='leftNavMenu-item-overview'], a[data-testid='leftNavMenu-item-progress']"),
                    timeout=30, retries=2  # Keep these timeouts generous
                )
                logging.info(
                    "Client dashboard loaded successfully (with refresh retry).")
                return True
            except TimeoutException:
                logging.error(
                    f"Client dashboard failed to load for {display_name} after retries. Taking screenshot for debugging.")
                self.driver.save_screenshot(
                    f"debug_screenshot_client_dashboard_fail_{display_name}.png")
                return False
            except Exception as e:
                logging.error(
                    f"Error verifying client dashboard load for {display_name}: {e}. Taking screenshot for debugging.")
                self.driver.save_screenshot(
                    f"debug_screenshot_client_dashboard_fail_{display_name}.png")
                return False

            time.sleep(5)  # Increased sleep after dashboard loads

            # Verify we're on the client page
            current_url = self.driver.current_url
            if "client" in current_url.lower() or any(word in current_url.lower() for word in display_name.lower().split()):
                logging.info(
                    f"Successfully navigated to client: {display_name}")
                return True
            else:
                logging.warning(
                    f"May not be on correct client page. URL: {current_url}")
                return True

        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False

    def navigate_to_training_program(self):
        """Navigates to the 'Training Program' tab with explicit verification."""
        try:
            current_url = self.driver.current_url
            logging.info(
                f"Starting navigation to Training Program from URL: {current_url}")

            time.sleep(10)  # Increased initial sleep

            # --- NEW ADDITION: Screenshot before clicking Training Program ---
            try:
                screenshot_path = "debug_screenshot_before_training_program_click.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Screenshot taken before Training Program click: {screenshot_path}")
            except Exception as screenshot_e:
                logging.error(
                    f"Failed to take screenshot before Training Program click: {screenshot_e}")
            # --- END NEW ADDITION ---

            training_program_selectors = [
                (By.XPATH, "//a[@id='nav_training_program' and @data-testid='leftNavMenu-item-trainingProgram' and @title='Training Program']"),
                (By.XPATH,
                 "//a[@data-testid='leftNavMenu-item-trainingProgram']"),
                (By.XPATH,
                 "//a[contains(@href, 'trainingProgram') and contains(@class, 'nav-link')]"),
                (By.XPATH,
                 "//a[text()='Training Program' or @title='Training Program']"),
            ]

            training_program_clicked = False

            for i, selector in enumerate(training_program_selectors, 1):
                try:
                    logging.info(
                        f"Attempting Training Program selector {i}: {selector}")

                    # Increased wait for training program link
                    training_program_link = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable(selector)
                    )

                    element_text = training_program_link.text or training_program_link.get_attribute(
                        'title') or 'No text'
                    element_href = training_program_link.get_attribute(
                        'href') or 'No href'
                    logging.info(
                        f"Found Training Program element - Text: '{element_text}', Href: '{element_href}'")

                    if ('training' in element_text.lower() and 'program' in element_text.lower()) or 'trainingProgram' in element_href:
                        logging.info(
                            "Verified this is the correct Training Program element")

                        self.driver.execute_script(
                            "arguments[0].scrollIntoView(true);", training_program_link)
                        time.sleep(2)  # Increased sleep after scroll

                        self.driver.execute_script(
                            "arguments[0].click();", training_program_link)
                        training_program_clicked = True
                        logging.info(
                            f"Successfully clicked Training Program tab using selector {i}")
                        break
                    else:
                        logging.warning(
                            f"Element found but doesn't appear to be Training Program: Text='{element_text}', Href='{element_href}'")
                        continue

                except TimeoutException:
                    logging.info(
                        f"Training Program selector {i} timed out, trying next...")
                    continue
                except Exception as e:
                    logging.warning(
                        f"Training Program selector {i} failed: {e}")
                    continue

            if not training_program_clicked:
                logging.error(
                    "Failed to find and click Training Program tab with any selector")
                return False

            time.sleep(8)  # Increased wait for navigation to complete

            new_url = self.driver.current_url
            page_title = self.driver.title
            logging.info(
                f"After clicking Training Program - URL: {new_url}, Title: {page_title}")

            verification_checks = [
                "/trainingProgram" in new_url,
                "training" in new_url.lower(),
                "program" in page_title.lower(),
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid^='grid-row-'], .ant-tabs-tab-active[data-testid*='training-program-tab']"))  # Check for program content
            ]

            if any(verification_checks):
                logging.info(
                    "Successfully navigated to Training Program tab")
                # Try to find expected content elements after navigation
                try:
                    # Use new helper function here:
                    self.find_element_with_refresh_retry(
                        (By.CSS_SELECTOR,
                         "[data-testid^='grid-row-'], .ant-tabs-tab-active[data-testid*='training-program-tab']"),
                        timeout=30, retries=2
                    )
                    logging.info(
                        "Training program content loaded successfully (with refresh retry).")
                    return True
                except TimeoutException:
                    logging.error(
                        "Training program content failed to load after retries.")
                    return False
                except Exception as e:
                    logging.error(
                        f"Error verifying training program content load: {e}")
                    return False
            else:
                logging.error(
                    f"Navigation verification failed - URL: {new_url}, Title: {page_title}")

                try:
                    nav_elements = self.driver.find_elements(
                        By.XPATH, "//nav//a | //div[@class='nav']//a")
                    logging.info("Current navigation elements:")
                    for elem in nav_elements[:10]:
                        elem_text = elem.text or elem.get_attribute(
                            'title') or 'No text'
                        elem_href = elem.get_attribute('href') or 'No href'
                        logging.info(
                            f"  Nav element: '{elem_text}' -> {elem_href}")
                except:
                    pass

                return False

        except Exception as e:
            logging.error(
                f"Unexpected error navigating to Training Program: {e}")
            return False

    def click_workout(self, workout_name: str) -> bool:
        """Finds and clicks a workout by its name in the program view, using robust selectors.
        """
        try:
            logging.info(f"Looking for workout: '{workout_name}'")

            # Wait for workout list to load - use new helper
            try:
                self.find_element_with_refresh_retry(
                    (By.CSS_SELECTOR,
                     "[data-testid^='grid-row-'], .workout-card-wrapper, .ant-table-wrapper"),
                    timeout=30, retries=2
                )
                logging.info(
                    "Workout grid or list container loaded (with refresh retry).")

                # Wait for overlays to disappear - this remains as is
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element_located(
                            (By.CSS_SELECTOR, ".tr-loader, .modal-backdrop, .ReactModal__Overlay, .ant-modal-mask"))
                    )
                    logging.info("Overlays clear.")
                except TimeoutException:
                    logging.info("No overlays found or already cleared.")

            except TimeoutException:
                logging.error(
                    "Workout grid/list did not load within expected time after retries.")
                return False
            except Exception as e:
                logging.error(f"Error loading workout grid/list: {e}")
                return False

            workout_selectors = [
                (By.XPATH,
                 f"//p[contains(@data-testid, 'workoutGrid-workoutName') and text()='{workout_name}']/ancestor::a[1]", "data-testid exact text"),
                (By.XPATH,
                 f"//p[contains(@data-testid, 'workoutGrid-workoutName') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workout_name.lower()}')]/ancestor::a[1]", "data-testid case-insensitive"),
                (By.XPATH,
                 f"//p[contains(@class, 'tz-lp') and contains(@class, 'color--blue') and text()='{workout_name}']/ancestor::a[1]", "tz-lp color-blue exact text"),
                (By.XPATH,
                 f"//p[contains(@class, 'tz-lp') and contains(@class, 'color--blue') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workout_name.lower()}')]/ancestor::a[1]", "tz-lp color-blue case-insensitive"),
                (By.XPATH,
                 f"//a[contains(@href, '/workout/') and .//p[text()='{workout_name}']]", "href workout exact text"),
                (By.XPATH,
                 f"//a[contains(@href, '/workout/') and .//p[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workout_name.lower()}')]]", "href workout case-insensitive"),
                (By.XPATH,
                 f"//a[contains(@class, 'section-link') and .//p[text()='{workout_name}']]", "section-link exact text"),
                (By.XPATH,
                 f"//a[.//p[@class='tz-sp color--black text-overflow-none' and text()='{workout_name}']]", "tz-sp color-black exact text"),
                (By.XPATH,
                 f"//div[contains(@class, 'workout') and .//span[text()='{workout_name}']]//a", "div workout span exact text"),
                (By.XPATH,
                 f"//div[text()='{workout_name}']/ancestor::a[1]", "div exact text ancestor"),
                (By.XPATH,
                 f"//h3[contains(text(), '{workout_name}')]/ancestor::a[1]", "h3 exact text"),
                (By.XPATH,
                 f"//h4[contains(text(), '{workout_name}')]/ancestor::a[1]", "h4 exact text"),
                (By.XPATH,
                 f"//span[contains(text(), '{workout_name}')]/ancestor::a[1]", "span exact text"),
                (By.XPATH,
                 f"//*[self::h3 or self::h4 or self::span][contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workout_name.lower()}')]/ancestor::a[1]", "h3-h4-span case-insensitive"),
                (By.CSS_SELECTOR,
                 f"[data-testid*='workoutGrid-workoutName'][data-testid*='{workout_name.lower().replace(' ', '')}']", "data-testid fuzzy"),
            ]

            for i, (by, selector, desc) in enumerate(workout_selectors, 1):
                try:
                    logging.info(f"Trying selector {i} ({desc}): {selector}")
                    # Use new click helper here:
                    if self.click_element_with_refresh_retry((by, selector), timeout=15, retries=2):
                        logging.info(
                            f"Successfully clicked workout: '{workout_name}' using selector {i} ({desc}) (with refresh retry)")
                        time.sleep(5)  # Increased sleep after clicking workout
                        return True
                    else:
                        logging.info(
                            f"Failed to click workout with selector {i} ({desc}). Trying next.")
                        continue  # Try next selector if click failed after retries
                except Exception as e:
                    logging.warning(
                        f"Error with selector {i} ({desc}): {e}, trying next.")
                    continue

            logging.warning(
                "All selectors failed to find a clickable workout. Looking for any visible workout elements for debugging...")
            try:
                visible_workout_elements = self.driver.find_elements(
                    By.XPATH, "//p[contains(@data-testid, 'workoutGrid-workoutName')] | //p[contains(@class, 'tz-lp')] | //a[contains(@href, '/workout/')] | //div[contains(@class, 'workout-card-wrapper')]")

                if visible_workout_elements:
                    logging.info("Found visible workout elements:")
                    for element in visible_workout_elements[:10]:
                        element_text = element.text.strip()
                        element_tag = element.tag_name
                        element_id = element.get_attribute("id")
                        element_class = element.get_attribute("class")
                        element_testid = element.get_attribute("data-testid")
                        logging.info(
                            f"  - Tag: {element_tag}, Text: '{element_text}', ID: '{element_id}', Class: '{element_class}', Data-testid: '{element_testid}'")

            except Exception as debug_error:
                logging.error(
                    f"Error during debugging fallback: {debug_error}")

            logging.error(f"Could not find workout: '{workout_name}'")
            return False

        except Exception as e:
            logging.error(
                f"An unexpected error occurred while clicking workout '{workout_name}': {e}")
            return False

    def click_edit_workout(self) -> bool:
        """Clicks the edit button for the workout, then clicks 'Workout Builder' from the dropdown.
        """
        try:
            edit_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='workoutDetail-editButton']")

            try:
                # Increased wait for edit button
                edit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(edit_button_locator))
                logging.info("Edit button found and clickable")
            except TimeoutException:
                logging.error(
                    "Edit button not found. Cannot proceed with editing workout.")
                return False

            self.retry_on_stale_element(lambda: edit_button.click())
            logging.info("Clicked main edit workout button")
            time.sleep(3)  # Increased wait for dropdown to appear

            workout_builder_locator = (
                By.CSS_SELECTOR, "li[data-testid='dropdownButton-menuItem-workoutBuilder']")
            # Increased wait for workout builder option
            workout_builder_option = self.wait.until(
                EC.element_to_be_clickable(workout_builder_locator)
            )
            self.retry_on_stale_element(lambda: workout_builder_option.click())
            logging.info("Clicked 'Workout Builder' from dropdown")
            # Increased wait for builder to load and overlays to disappear
            time.sleep(8)

            # Additional check for loader/modal overlay after clicking workout builder
            try:
                WebDriverWait(self.driver, 15).until(EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".tr-loader, .modal-backdrop, .ReactModal__Overlay, .ant-modal-mask")))
                logging.info("Workout builder loaded and overlays clear.")
            except TimeoutException:
                logging.warning(
                    "Loader/modal overlay still present after clicking Workout Builder.")
                # Attempt to escape if still stuck
                try:
                    self.driver.find_element(
                        By.CSS_SELECTOR, "body").send_keys(Keys.ESCAPE)
                    time.sleep(2)
                except:
                    pass

            return True

        except Exception as e:
            logging.error(
                f"Error clicking edit workout button or dropdown option: {e}")
            return False

    def find_closest_exercise(self, target_exercise: str, available_exercises: list) -> str:
        """Find the closest matching exercise name using improved fuzzy matching."""
        def clean_name(name: str) -> str:
            # Remove common words, hyphens, and standardize
            cleaned = name.lower()
            cleaned = cleaned.replace("barbell", "").replace(
                "dumbbell", "").replace("machine", "")
            cleaned = cleaned.replace("-", " ")  # Replace hyphen with space
            # Remove trailing 's' for basic plural handling
            if cleaned.endswith('s'):
                cleaned = cleaned[:-1]
            return cleaned.strip()

        # SAFETY FEATURE: Define commonly confused exercise pairs that need exact matches
        confused_exercise_pairs = [
            ('lat pulldown', 'chin up'),
            ('lat pull down', 'chin up'),
            ('pulldown', 'chin up'),
            ('pull down', 'chin up'),
            ('lat pulldown', 'pull up'),
            ('lat pull down', 'pull up'),
            ('pulldown', 'pull up'),
            ('pull down', 'pull up'),
            ('chest press', 'chest fly'),
            ('bench press', 'chest fly'),
            ('shoulder press', 'lateral raise'),
            ('bicep curl', 'hammer curl'),
            ('squat', 'leg press'),
            ('deadlift', 'romanian deadlift'),
        ]

        target_clean = clean_name(target_exercise)
        best_match = None
        best_ratio = 0

        logging.info(
            f"        Fuzzy matching for: '{target_exercise}' (cleaned: '{target_clean}')")

        # Check if target exercise is in a confused pair
        is_confused_exercise = False
        for pair in confused_exercise_pairs:
            if target_clean in pair:
                is_confused_exercise = True
                logging.info(
                    f"        WARNING: '{target_exercise}' is in confused exercise pair: {pair}")
                break

        for exercise in available_exercises:
            exercise_clean = clean_name(exercise)

            # Check for exact matches first (highest priority)
            if target_clean == exercise_clean:
                logging.info(
                    f"        EXACT MATCH: '{target_exercise}' -> '{exercise}'")
                return exercise

            # SAFETY CHECK: If this is a confused exercise, require higher precision
            if is_confused_exercise:
                # Check if the available exercise is also in a confused pair
                for pair in confused_exercise_pairs:
                    if exercise_clean in pair and target_clean in pair:
                        # Both exercises are in the same confused pair - only allow exact matches
                        logging.info(
                            f"        SAFETY BLOCK: Preventing match between confused exercises '{target_exercise}' and '{exercise}'")
                        continue

            # Check if all words in target are in exercise name
            target_words = set(target_clean.split())
            exercise_words = set(exercise_clean.split())

            # Calculate word intersection ratio
            if len(target_words) > 0:
                word_match_ratio = len(target_words.intersection(
                    exercise_words)) / len(target_words)
            else:
                word_match_ratio = 0

            # Calculate character similarity
            char_match = 0
            for i in range(min(len(target_clean), len(exercise_clean))):
                if target_clean[i] == exercise_clean[i]:
                    char_match += 1
            char_ratio = char_match / max(len(target_clean), len(exercise_clean)) if max(
                len(target_clean), len(exercise_clean)) > 0 else 0

            # IMPROVED: Add length similarity penalty to avoid matching very different length exercises
            length_diff = abs(len(target_clean) - len(exercise_clean))
            max_length = max(len(target_clean), len(exercise_clean))
            length_penalty = length_diff / max_length if max_length > 0 else 1

            # IMPROVED: Combined score with length penalty
            match_ratio = (word_match_ratio * 0.7) + \
                (char_ratio * 0.3) - (length_penalty * 0.2)

            # Log detailed scoring for debugging
            logging.info(
                f"        Comparing '{exercise}' (cleaned: '{exercise_clean}')")
            logging.info(
                f"          Word match: {word_match_ratio:.3f}, Char match: {char_ratio:.3f}, Length penalty: {length_penalty:.3f}")
            logging.info(f"          Final score: {match_ratio:.3f}")

            if match_ratio > best_ratio:
                best_ratio = match_ratio
                best_match = exercise

        # IMPROVED: Use stricter threshold for confused exercises
        threshold = 0.9 if is_confused_exercise else 0.7

        if best_match and best_ratio > threshold:
            logging.info(
                f"        FUZZY MATCH: '{target_exercise}' -> '{best_match}' (score: {best_ratio:.3f}, threshold: {threshold})")
            return best_match
        else:
            logging.info(
                f"        NO SUITABLE MATCH: Best candidate '{best_match}' scored {best_ratio:.3f} (threshold: {threshold})")
            return None

    def update_exercise_goal(self, exercise_name: str, new_goals: str) -> bool:
        """
        Updates the goal of a specific exercise within the currently open workout,
        using fuzzy matching to find the exercise.
        """
        try:
            logging.info(
                f"      Looking for exercise: {exercise_name}")

            available_exercise_elements = self.driver.find_elements(
                By.XPATH, "//div[@class='exerciseList-exercise__name ']")
            available_exercise_names = [elem.get_attribute(
                'title') for elem in available_exercise_elements if elem.is_displayed()]

            if not available_exercise_names:
                logging.error(
                    "        Could not find any exercise names in the UI to match against.")
                return False

            # Log all available exercises for debugging
            logging.info(
                f"        Available exercises: {available_exercise_names}")

            best_match_name = self.find_closest_exercise(
                exercise_name, available_exercise_names)

            if not best_match_name:
                logging.error(
                    f"        Could not find a suitable match for '{exercise_name}' from available exercises: {available_exercise_names}")
                return False

            if best_match_name.lower() != exercise_name.lower():
                logging.info(
                    f"        Fuzzy match found: '{exercise_name}' -> '{best_match_name}'")
            else:
                logging.info(f"        Exact match found: '{best_match_name}'")

            exercise_in_list_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{best_match_name}']/ancestor::div[contains(@class, 'workoutExercise')]")

            try:
                # Increased wait for exercise container
                exercise_container = self.wait.until(
                    EC.presence_of_element_located(exercise_in_list_locator))
                logging.info(
                    f"        Found container for '{best_match_name}'.")
            except TimeoutException:
                logging.error(
                    f"        Could not find container for '{best_match_name}' in the workout list after 20 seconds.")
                return False

            try:
                target_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")

                # CRITICAL FIX: Search within the exercise container, not the entire page
                target_input = exercise_container.find_element(
                    *target_input_locator)

                # Verify the input is interactable
                if not target_input.is_displayed() or not target_input.is_enabled():
                    logging.warning(
                        f"        Found goal input field for {best_match_name} but it is not interactable. Attempting scroll into view.")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", target_input)
                    time.sleep(2)  # Wait for scroll to complete

                    # Re-check if it's now interactable
                    if not target_input.is_displayed() or not target_input.is_enabled():
                        logging.error(
                            f"        Goal input field for {best_match_name} is still not interactable after scroll.")
                        return False

                    logging.info(
                        f"        Goal input field for {best_match_name} is now interactable.")

            except NoSuchElementException:
                logging.error(
                    f"        Failed to find the goal input field for exercise {best_match_name} within its container.")
                return False

            if target_input:
                # Scroll the input into view before interacting
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", target_input)
                time.sleep(1)

                # Highlight the input field for debugging (add visual confirmation)
                self.driver.execute_script(
                    "arguments[0].style.border='3px solid red';", target_input)
                time.sleep(0.5)

                target_input.click()
                time.sleep(1)  # Increased sleep after click
                target_input.send_keys(Keys.CONTROL + "a")
                target_input.send_keys(Keys.DELETE)
                time.sleep(1)  # Increased sleep after clear

                target_input.send_keys(new_goals)

                # Remove highlight after successful update
                self.driver.execute_script(
                    "arguments[0].style.border='';", target_input)

                logging.info(
                    f"        Successfully updated goal for {best_match_name}: {new_goals}")
                time.sleep(0.5)  # Small sleep after sending keys
                return True
            else:
                logging.error(
                    f"        Failed to find the goal input field for exercise {best_match_name}.")
                return False

        except TimeoutException:
            logging.error(
                f"      Timeout while trying to find or interact with {exercise_name} for goal update.")
            return False
        except NoSuchElementException:
            logging.error(
                f"      Could not locate exercise {exercise_name} or its goal input field.")
            return False
        except Exception as e:
            logging.error(
                f"      Error updating exercise {exercise_name} goal: {e}")
            return False

    def discover_workout_names(self):
        """Discovers all visible workout names on the training program page."""
        workout_names = []
        try:
            logging.info("Discovering workouts on the page...")
            # Wait for workout names to be present and visible
            workout_name_elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//p[contains(@data-testid, 'workoutGrid-workoutName')]"))
            )

            if not workout_name_elements:
                logging.warning(
                    "Could not find workout names using the primary selector. Trying fallback.")
                workout_name_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//a[contains(@class, 'section-link')]//p[contains(@class, 'color--blue')]"))
                )

            for element in workout_name_elements:
                if element.is_displayed():
                    workout_name = element.text
                    if workout_name and workout_name not in workout_names:
                        workout_names.append(workout_name)
                        logging.info(f"Discovered workout: {workout_name}")
            time.sleep(2)  # Small sleep after discovering workouts
            return workout_names
        except Exception as e:
            logging.error(f"Error discovering workout names: {e}")
            return []

    def discover_exercise_names(self):
        """Discovers all exercise names within the workout builder."""
        exercise_names = []
        try:
            logging.info("Discovering exercises within the workout...")
            # Wait for exercise elements to be present and visible
            exercise_elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@class='exerciseList-exercise__name ']"))
            )
            for elem in exercise_elements:
                if elem.is_displayed():
                    exercise_name = elem.get_attribute('title')
                    if exercise_name:
                        exercise_names.append(exercise_name)
            logging.info(f"Discovered exercises: {exercise_names}")
            time.sleep(2)  # Small sleep after discovering exercises
            return exercise_names
        except Exception as e:
            logging.error(f"Error discovering exercise names: {e}")
            return []

    def dynamically_update_client_workouts(self, client_name_db_key):
        """
        Logs in, navigates to a client, and dynamically discovers and updates all their workouts.
        """
        performance_history = self.load_performance_history()

        performance_data_key = self.transform_client_name(
            client_name_db_key)
        logging.info(
            f"Looking for performance data using key: '{performance_data_key}'")

        client_performance_data = performance_history.get(
            performance_data_key, {})

        client_latest_performance = {}
        if client_performance_data:
            try:
                latest_entry = max(
                    client_performance_data, key=lambda x: x['date'])
                client_latest_performance = latest_entry.get(
                    'progressions', {})
            except (ValueError, TypeError):
                logging.error(
                    f"Could not determine latest entry for {performance_data_key} due to invalid data.")
                client_latest_performance = {}

        logging.info(
            f"Loaded latest performance data for {performance_data_key} with {len(client_latest_performance)} exercise entries.")

        if not self.navigate_to_client(client_name_db_key):
            logging.error(
                f"Failed to navigate to client {client_name_db_key}. Aborting.")
            return False

        if not self.navigate_to_training_program():
            logging.error(
                f"Failed to navigate to training program for {client_name_db_key}. Aborting.")
            return False

        workout_names = self.discover_workout_names()
        if not workout_names:
            logging.error("No workouts discovered for this client. Aborting.")
            return False
        logging.info(
            f"Found {len(workout_names)} workouts to process: {workout_names}")

        for workout_name in workout_names:
            logging.info(f"\n--- Processing workout: {workout_name} ---")

            if not self.click_workout(workout_name):
                logging.error(
                    f"Could not find or click workout '{workout_name}'. Skipping.")
                self.navigate_to_training_program()  # Try to get back to program list
                continue

            if not self.click_edit_workout():
                logging.error(
                    f"Could not enter edit mode for '{workout_name}'. Skipping.")
                self.driver.back()
                time.sleep(2)
                continue

            exercises_in_workout = self.discover_exercise_names()

            for exercise_name in exercises_in_workout:
                performance_data = client_latest_performance.get(exercise_name)
                new_goals_str = ""

                if performance_data:
                    if 'recommended_reps' in performance_data:
                        new_goals_str = f"GOALS: {performance_data['recommended_reps']}"
                        logging.info(
                            f"Using pre-calculated smart progression for '{exercise_name}': {new_goals_str}")
                    else:
                        current_weight = performance_data.get(
                            'current_weight', 0)
                        current_reps = performance_data.get(
                            'current_reps', '6')
                        next_reps = self.apply_rep_progression_algorithm(
                            current_reps)
                        increase_weight = (
                            next_reps == 6 and int(current_reps) >= 15)
                        next_weight = self.get_next_weight(
                            current_weight, exercise_name, increase_weight)
                        new_goals_str = f"GOALS: S1: {next_weight}kg*{next_reps} | S2: {next_weight}kg*{next_reps} | S3: {next_weight}kg*{next_reps}"
                        logging.info(
                            f"Calculated new progression for '{exercise_name}': {new_goals_str}")
                else:
                    # IMPROVEMENT: Intelligent default goals based on exercise type
                    new_goals_str = self.generate_intelligent_default_goals(
                        exercise_name)
                    logging.info(
                        f"Using INTELLIGENT DEFAULT goals for '{exercise_name}': {new_goals_str}")

                self.update_exercise_goal(exercise_name, new_goals_str)

            logging.info(f"Saving changes for workout '{workout_name}'...")
            save_button_selector = "button[data-testid='workoutBuilder-saveBtn']"
            try:
                save_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, save_button_selector)))
                self.driver.execute_script(
                    "arguments[0].click();", save_button)
                time.sleep(8)  # Increased wait for save and redirect
                logging.info(f"Workout '{workout_name}' saved successfully.")
            except Exception as e:
                logging.error(
                    f"Failed to save workout '{workout_name}': {e}. Attempting to go back.")
                self.driver.back()
                time.sleep(3)

            self.navigate_to_training_program()

        logging.info("All workouts processed for client.")
        return True

    def retry_on_stale_element(self, func, max_retries=3, retry_delay=1):
        """Retry function on StaleElementReferenceException or stack trace errors"""
        for attempt in range(max_retries):
            try:
                return func()
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    logging.warning(
                        f"Stale element, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise
            except Exception as e:
                if "Stacktrace:" in str(e) and attempt < max_retries - 1:
                    logging.warning(
                        f"Stack trace error, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise

    def transform_client_name(self, database_name):
        """Transform database client name to display format"""
        # Convert underscore to space and title case
        # alice_forster -> Alice Forster
        if '_' in database_name:
            parts = database_name.split('_')
            return ' '.join(word.capitalize() for word in parts)
        else:
            return database_name.title()

    def find_client_fuzzy(self, target_name):
        """Find client using fuzzy matching"""
        try:
            # Wait for search results to load
            time.sleep(2)

            # Get all visible client links/names from the main client grid
            client_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@data-testid, 'baseGrid-row')]//a[contains(@href, '/client/')]")

            if not client_elements:
                logging.warning(
                    "No client elements found in the grid for fuzzy matching. Checking for other text elements.")
                # Fallback to a broader search if the specific one fails
                client_elements = self.driver.find_elements(
                    By.XPATH, "//td[contains(@class, 'ant-table-cell')]//a | //div[contains(@data-testid, 'client')]//a")

            if not client_elements:
                logging.error(
                    "Could not find any client elements on the page for fuzzy matching.")
                return None

            best_match = None
            best_score = 0

            for element in client_elements:
                element_text = element.text.strip()
                if not element_text:
                    continue

                # Calculate similarity
                # Simple fuzzy matching based on word overlap
                target_words = set(target_name.lower().split())
                element_words = set(element_text.lower().split())

                if target_words and element_words:
                    intersection = target_words.intersection(element_words)
                    union = target_words.union(element_words)
                    score = len(intersection) / len(union) if union else 0

                    # Also check for partial matches
                    partial_score = 0
                    for target_word in target_words:
                        for element_word in element_words:
                            if target_word in element_word or element_word in target_word:
                                partial_score += 0.5

                    final_score = score + (partial_score * 0.3)

                    logging.info(
                        f"Fuzzy match: '{element_text}' vs '{target_name}' = {final_score:.3f}")

                    if final_score > best_score and final_score > 0.5:  # Minimum threshold
                        best_score = final_score
                        best_match = element
            if best_match:
                logging.info(
                    f"Best fuzzy match found: '{best_match.text}' (score: {best_score:.3f})")
                return best_match
            else:
                logging.warning(
                    f"No suitable fuzzy match found for '{target_name}'")
                return None

        except Exception as e:
            logging.error(f"Error in fuzzy client search: {e}")
            return None

    def load_performance_history(self):
        """Load the performance history data from progression_history.json"""
        try:
            with open('progression_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("progression_history.json not found")
            return {}
        except Exception as e:
            logging.error(f"Error loading progression history: {e}")
            return {}

    def apply_rep_progression_algorithm(self, current_reps):
        """Apply the 6->8->10->12->15 rep progression algorithm"""
        try:
            current_reps = int(current_reps)
        except (ValueError, TypeError):
            logging.warning(
                f"Could not convert current_reps '{current_reps}' to int. Defaulting to 6.")
            current_reps = 6

        if current_reps >= 15:
            return 6
        elif current_reps >= 12:
            return 15
        elif current_reps >= 10:
            return 12
        elif current_reps >= 8:
            return 10
        elif current_reps >= 6:
            return 8
        else:
            return 6

    def get_next_weight(self, current_weight, exercise_name, increase_weight=False):
        """Get the next appropriate weight based on equipment type"""
        dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                            17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        barbell_increments = 2.5

        if not increase_weight:
            return current_weight

        is_dumbbell = any(keyword in exercise_name.lower() for keyword in
                          ['dumbbell', 'd.b', 'db', 'dumbell'])

        if is_dumbbell:
            current_idx = None
            for i, weight in enumerate(dumbbell_weights):
                if weight >= current_weight:
                    current_idx = i
                    break
            if current_idx is not None and current_idx < len(dumbbell_weights) - 1:
                return dumbbell_weights[current_idx + 1]
            else:
                return current_weight + 2.5
        else:
            return current_weight + barbell_increments

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

    def find_element_with_refresh_retry(self, by_locator, timeout=30, retries=2, root_element=None):
        """
        Attempts to find an element, refreshing and retrying on TimeoutException.
        Returns the found element or raises TimeoutException if unsuccessful.
        If root_element is provided, searches within that element.
        """
        driver_or_element = root_element if root_element else self.driver
        for attempt in range(retries + 1):
            try:
                element = WebDriverWait(driver_or_element, timeout).until(
                    EC.visibility_of_element_located(by_locator)
                )
                return element
            except TimeoutException:
                if attempt < retries and not root_element:  # Only refresh if not searching within a specific element
                    logging.warning(
                        f"Element {by_locator} not found. Refreshing page and retrying (attempt {attempt + 1}/{retries})...")
                    self.driver.refresh()
                    time.sleep(5)  # Give time for refresh
                else:
                    logging.error(f"Element {by_locator} not found after {retries} {'refreshes' if not root_element else 'retries'}. Giving up." + (
                        " (within root element)" if root_element else ""))
                    raise  # Re-raise if all retries fail
            except NoSuchElementException:
                logging.error(f"Element {by_locator} not found. This selector might be incorrect or element not present." + (
                    " (within root element)" if root_element else ""))
                # If it's NoSuchElement, refreshing might not help, just re-raise.
                raise

    def click_element_with_refresh_retry(self, by_locator, timeout=30, retries=2):
        """
        Attempts to click an element, refreshing and retrying on TimeoutException or ElementClickInterceptedException.
        """
        for attempt in range(retries + 1):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(by_locator)
                )
                element.click()
                return True
            except (TimeoutException, ElementClickInterceptedException) as e:
                if attempt < retries:
                    logging.warning(f"Error clicking element {by_locator} ({e}). Refreshing page and retrying (attempt {attempt + 1}/{retries})..." + (
                        "\n" + self.driver.current_url if hasattr(self.driver, 'current_url') else ""))  # Log current URL if available
                    self.driver.refresh()
                    time.sleep(5)  # Give time for refresh
                else:
                    logging.error(f"Failed to click element {by_locator} after {retries} refreshes. Giving up." + (
                        "\n" + self.driver.current_url if hasattr(self.driver, 'current_url') else ""))
                    raise  # Re-raise if all retries fail
            except Exception as e:  # Catch other exceptions
                logging.error(f"Unexpected error clicking element {by_locator}: {e}" + (
                    "\n" + self.driver.current_url if hasattr(self.driver, 'current_url') else ""))
                raise

    def return_to_main_dashboard(self):
        """Closes the current tab (client tab) and switches back to the main dashboard tab."""
        try:
            # Check if there's more than one window and the current window is not the main dashboard
            if len(self.driver.window_handles) > 1 and self.driver.current_window_handle != self.original_window_handle:
                logging.info("Closing current client tab...")
                self.driver.close()  # Close the current client tab
                # Switch back to the main dashboard
                self.driver.switch_to.window(self.original_window_handle)
                logging.info("Switched back to main dashboard.")
                # Give some time for the main dashboard to become active
                time.sleep(2)
            else:
                logging.info(
                    "Already on the main dashboard or only one tab open. No need to switch.")
        except Exception as e:
            logging.error(f"Error returning to main dashboard: {e}")

    def process_multiple_clients(self, all_clients_progressions_data):
        """Processes multiple clients by dynamically updating their workouts."""
        results = {}
        for client_name_db_key in all_clients_progressions_data.keys():
            logging.info(
                f"\n{'='*60}\nProcessing client: {self.transform_client_name(client_name_db_key)}\n{'='*60}")
            try:
                success = self.dynamically_update_client_workouts(
                    client_name_db_key)
                if success:
                    results[client_name_db_key] = {'status': 'success'}
                else:
                    results[client_name_db_key] = {
                        'status': 'failed', 'error': 'Failed to update workouts'}
            except Exception as e:
                logging.error(
                    f"Error processing client {client_name_db_key}: {e}")
                results[client_name_db_key] = {
                    'status': 'failed', 'error': str(e)}
            finally:
                # After processing each client, navigate back to the clients list if possible
                try:
                    self.return_to_main_dashboard()
                    # Also handle any popups after returning to the main dashboard
                    self.handle_notification_popup()
                except Exception as e:
                    logging.warning(
                        f"Could not navigate back to clients list after processing {client_name_db_key}: {e}")

        return results

    def add_exercise(self, exercise_name, sets="3", reps="12"):
        """Adds exercise, sets sets/reps, WITHOUT saving workout, using updated selectors and flow."""
        try:
            logging.info(
                f"Adding exercise: {exercise_name} with Sets={sets}, Reps={reps}...")

            # Variable to store the actual name added, defaults to original
            actual_exercise_name_added = exercise_name

            # 1. Find and click the main search input within the builder
            search_input_locator = (
                By.CSS_SELECTOR, "input.ant-input[placeholder='Search for an exercise']")
            # Use new helper for finding and clicking search input
            search_input = self.find_element_with_refresh_retry(
                search_input_locator)
            self.click_element_with_refresh_retry(search_input_locator)
            # Aggressively clear just in case
            search_input.send_keys(Keys.CONTROL + "a")
            search_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            logging.info("Clicked and cleared search input.")

            # 2. Type exercise name
            search_input.send_keys(exercise_name)
            logging.info(f"Typed '{exercise_name}'.")
            # Allow search suggestions to potentially load (though we press Enter)
            time.sleep(1)

            # 3. Press Enter
            search_input.send_keys(Keys.ENTER)
            logging.info("Pressed Enter.")
            time.sleep(5)  # Wait for search results library to load

            # 4. Wait for and Find Exercise in Library (Exact Match First)
            logging.info(
                f"Searching library for exact match: '{exercise_name}'")
            # Construct data-testid dynamically (lowercase, remove spaces)
            processed_name = ''.join(
                filter(str.isalnum, exercise_name)).lower()
            # Adjust dynamic selector based on observed patterns (may need refinement)
            # Let's try a contains approach first as exact dynamic generation is tricky
            exercise_library_locator = (
                By.XPATH, f"//div[contains(@data-testid, 'exerciseLibrary-exercise') and .//p[text()='{exercise_name}']]")

            exercise_element = None
            try:
                # Wait for the container to be present
                self.find_element_with_refresh_retry(
                    (By.CSS_SELECTOR, ".exerciseLibrary-container"), timeout=10, retries=1)
                # Use new helper for finding the specific exercise
                exercise_element = self.find_element_with_refresh_retry(
                    exercise_library_locator, timeout=10, retries=1)
                logging.info(
                    f"Found exact match for '{exercise_name}' in library.")
                # actual_exercise_name_added remains exercise_name
            except TimeoutException:
                logging.warning(
                    f"Exact match for '{exercise_name}' not found or not clickable. Trying fuzzy match...")
                # 5. Fuzzy Match Logic
                try:
                    # Get all available exercise elements
                    available_exercise_elements = self.driver.find_elements(
                        By.XPATH, "//div[contains(@data-testid, 'exerciseLibrary-exercise')]//p")
                    available_exercise_names = [
                        elem.text for elem in available_exercise_elements if elem.text]

                    if not available_exercise_names:
                        logging.error(
                            "Could not find any exercise names in the library for fuzzy matching.")
                        return False

                    closest_match_name = self.find_closest_exercise(
                        exercise_name, available_exercise_names)

                    if closest_match_name:
                        logging.info(
                            f"Closest fuzzy match found: '{closest_match_name}'")
                        # Find the element corresponding to the closest match
                        fuzzy_match_locator = (
                            By.XPATH, f"//div[contains(@data-testid, 'exerciseLibrary-exercise') and .//p[text()='{closest_match_name}']]")
                        # Use new helper for finding fuzzy matched exercise
                        exercise_element = self.find_element_with_refresh_retry(
                            fuzzy_match_locator, timeout=10, retries=1)
                        actual_exercise_name_added = closest_match_name  # Update the name used later
                    else:
                        logging.error(
                            f"Fuzzy match failed for '{exercise_name}'.")
                        return False
                except Exception as fuzzy_e:
                    logging.error(f"Error during fuzzy matching: {fuzzy_e}")
                    return False

            # 6. Click the Found/Closest Exercise
            if exercise_element:
                # Log the name we determined was added
                logging.info(
                    f"Clicking on exercise '{actual_exercise_name_added}' in library.")
                self.click_element_with_refresh_retry(
                    (exercise_element.tag_name, exercise_element.text), timeout=5, retries=1)  # Use helper
                time.sleep(1)
            else:
                # This case should ideally be caught above, but as a safeguard:
                logging.error(
                    "Exercise element was not found after search and fuzzy match.")
                return False

            # 7. Click "Add to Workout" Button
            add_to_workout_button_locator = (
                By.XPATH, "//button[contains(@class, 'btn--blue') and contains(., 'Add to Workout')]")
            # Use new click helper for Add to Workout button
            if not self.click_element_with_refresh_retry(add_to_workout_button_locator, timeout=10, retries=2):
                logging.error(
                    "Failed to click 'Add to Workout' button after retries.")
                return False
            logging.info(
                "Clicked 'Add to Workout' button (with refresh retry).")
            time.sleep(10)  # Wait for exercise to appear in the list below

            # --- Step 8: Locate Added Exercise Container ---
            # Use the actual_exercise_name_added found earlier
            logging.info(
                f"Locating container for '{actual_exercise_name_added}' in the workout list...")
            # Use the actual_exercise_name_added in the XPath
            exercise_in_list_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{actual_exercise_name_added}']/ancestor::div[contains(@class, 'workoutExercise')][1]")

            # Use new helper for finding exercise container
            workout_list_exercise_div = self.find_element_with_refresh_retry(
                exercise_in_list_locator, timeout=20, retries=2)
            logging.info(
                f"Found container for '{actual_exercise_name_added}' (with refresh retry).")

            # 9. Set Sets (relative to the found container)
            try:
                sets_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-exerciseSetInput']")
                # Use new helper to find the sets input
                sets_input = self.find_element_with_refresh_retry(
                    sets_input_locator, timeout=10, retries=2, root_element=workout_list_exercise_div)
                self.click_element_with_refresh_retry(
                    sets_input_locator, timeout=5, retries=1)
                time.sleep(0.2)
                # Clear using backspace (adjust count if needed)
                sets_input.send_keys(Keys.CONTROL + "a")
                sets_input.send_keys(Keys.DELETE)
                time.sleep(0.2)
                sets_input.send_keys(sets)
                # Log with correct name
                logging.info(
                    f"Sets set to: {sets} for {actual_exercise_name_added}")
                time.sleep(0.5)
            except Exception as e:
                # Log with correct name
                logging.error(
                    f"Error setting sets for '{actual_exercise_name_added}': {e}")
                return False

            # 10. Set Reps (relative to the found container)
            try:
                reps_input_locator = (
                    By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")
                # Use new helper to find the reps input
                reps_input = self.find_element_with_refresh_retry(
                    reps_input_locator, timeout=10, retries=2, root_element=workout_list_exercise_div)
                self.click_element_with_refresh_retry(
                    reps_input_locator, timeout=5, retries=1)
                time.sleep(0.2)
                # Clear using backspace (adjust count if needed, placeholder might be there)
                reps_input.send_keys(Keys.BACKSPACE * 30)
                time.sleep(0.2)
                reps_input.send_keys(reps)
                # Log with correct name
                logging.info(
                    f"Reps set to: {reps} for {actual_exercise_name_added}")
                time.sleep(0.5)
            except Exception as e:
                # Log with correct name
                logging.error(
                    f"Error setting reps for '{actual_exercise_name_added}': {e}")
                return False

            logging.info(
                f"Successfully added and configured '{actual_exercise_name_added}'.")
            return True

        except (TimeoutException, NoSuchElementException) as e:
            # Log with original requested name, as the failure might have happened before finding the actual name
            logging.error(f"Error adding exercise '{exercise_name}': {e}")
            return False
        except Exception as e:
            # Log with original requested name
            logging.error(
                f"An unexpected error occurred adding exercise '{exercise_name}': {e}")
            return False

    def save_workout(self) -> bool:
        """Clicks the final 'Save' button in the workout builder."""
        try:
            save_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='workoutBuilder-saveBtn']")
            # Use new click helper for the save button
            if not self.click_element_with_refresh_retry(save_button_locator, timeout=10, retries=2):
                logging.error(
                    "Failed to click the final workout Save button after retries.")
                return False

            logging.info(
                "Clicked the final 'Save' button for the workout (with refresh retry).")
            time.sleep(5)  # Allow time for save and page transition

            # Verify that the page has transitioned back to the workout detail view
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='workoutDetail-name'], h1.page-title"))
                )
                logging.info(
                    "Successfully returned to workout detail page after saving.")
                return True
            except TimeoutException:
                logging.error(
                    "Did not return to workout detail page after saving (timeout). Refreshing and checking again...")
                self.driver.refresh()
                time.sleep(5)  # Wait for refresh
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[data-testid='workoutDetail-name'], h1.page-title"))
                    )
                    logging.info(
                        "Successfully returned to workout detail page after refreshing.")
                    return True
                except TimeoutException:
                    logging.error(
                        "Still could not return to workout detail page after refresh.")
                    return False
            except Exception as e:
                logging.error(
                    f"Error verifying return to workout detail page after save: {e}")
                return False

        except Exception as e:
            logging.error(f"Error clicking the final workout Save button: {e}")
            return False

    def generate_intelligent_default_goals(self, exercise_name):
        """Generate intelligent default goals based on exercise type and current workout structure"""
        try:
            # Check if this is a bodyweight exercise
            is_bodyweight = self.is_bodyweight_exercise(exercise_name)

            # Try to detect current set count from the workout structure
            set_count = self.detect_current_set_count(exercise_name)

            # Default reps for new exercises
            default_reps = 6

            # Generate goals based on exercise type and set count
            goals = []
            for i in range(set_count):
                if is_bodyweight:
                    goals.append(f"S{i+1}: {default_reps}")
                else:
                    # For weighted exercises with no data, use a conservative starting weight
                    default_weight = self.get_default_starting_weight(
                        exercise_name)
                    goals.append(f"S{i+1}: {default_weight}kg*{default_reps}")

            return "GOALS: " + " | ".join(goals)

        except Exception as e:
            logging.warning(
                f"Error generating intelligent defaults for '{exercise_name}': {e}")
            # Fallback to simple default
            return "GOALS: S1: 6 | S2: 6 | S3: 6"

    def is_bodyweight_exercise(self, exercise_name):
        """Determine if an exercise is bodyweight based on name"""
        bodyweight_keywords = [
            'push up', 'pushup', 'pull up', 'pullup', 'chin up', 'chinup',
            'dip', 'plank', 'burpee', 'jumping jack', 'mountain climber',
            'squat jump', 'lunge', 'bodyweight', 'air squat', 'wall sit',
            'calf raise', 'sit up', 'situp', 'crunch', 'leg raise'
        ]

        exercise_lower = exercise_name.lower()
        return any(keyword in exercise_lower for keyword in bodyweight_keywords)

    def detect_current_set_count(self, exercise_name):
        """Try to detect the current number of sets for this exercise from the workout structure"""
        try:
            # Look for the exercise container in the current workout
            exercise_container_locator = (
                By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{exercise_name}']/ancestor::div[contains(@class, 'workoutExercise')]")

            exercise_container = self.driver.find_element(
                *exercise_container_locator)

            # Count the number of set input fields for this exercise
            set_inputs = exercise_container.find_elements(
                By.XPATH, ".//input[@data-testid='workoutBuilder-exerciseSetInput']")

            if set_inputs:
                detected_count = len(set_inputs)
                logging.info(
                    f"Detected {detected_count} sets for '{exercise_name}' from current workout structure")
                return detected_count
            else:
                logging.info(
                    f"Could not detect set count for '{exercise_name}', using default of 3")
                return 3

        except Exception as e:
            logging.info(
                f"Could not detect set count for '{exercise_name}' due to: {e}. Using default of 3")
            return 3

    def get_default_starting_weight(self, exercise_name):
        """Get a reasonable starting weight for new exercises based on exercise type"""
        exercise_lower = exercise_name.lower()

        # Dumbbell exercises - start lighter
        if any(keyword in exercise_lower for keyword in ['dumbbell', 'd.b', 'db']):
            if any(keyword in exercise_lower for keyword in ['curl', 'raise', 'fly']):
                return 5  # Light isolation exercises
            else:
                return 10  # Compound dumbbell exercises

        # Barbell exercises - start heavier
        elif 'barbell' in exercise_lower:
            if any(keyword in exercise_lower for keyword in ['row', 'press', 'curl']):
                return 20  # Barbell exercises
            else:
                return 30  # Heavy barbell compounds

        # Machine exercises - moderate starting weight
        elif 'machine' in exercise_lower or any(keyword in exercise_lower for keyword in ['press', 'pulldown', 'row']):
            return 25

        # Cable exercises
        elif 'cable' in exercise_lower:
            return 15

        # Default for unknown exercises
        else:
            return 10


if __name__ == '__main__':
    pass
