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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, InvalidSessionIdException, NoSuchWindowException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Imports for YouTube API
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from datetime import datetime, timedelta  # Added for Monday calculation

# --- Function to find available ChromeDriver ---


def find_chromedriver():
    """Find a valid ChromeDriver executable from multiple common locations"""

    # List of potential ChromeDriver locations
    potential_paths = [
        # Central location we established
        r"C:\SeleniumDrivers\chromedriver.exe",
        # Original path from this script
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
        # Common Windows locations
        r"C:\chromedriver.exe",
        r"C:\chromedriver\chromedriver.exe",
        r"C:\WebDrivers\chromedriver.exe",
        # Program Files locations
        r"C:\Program Files\ChromeDriver\chromedriver.exe",
        r"C:\Program Files (x86)\ChromeDriver\chromedriver.exe",
        # User directory locations
        os.path.join(os.path.expanduser("~"), "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "chromedriver.exe"),
        os.path.join(os.path.expanduser("~"), "Desktop", "chromedriver.exe"),
        # Current directory
        os.path.join(os.getcwd(), "chromedriver.exe"),
        # Search in .cache/selenium directory
        os.path.join(os.path.expanduser("~"), ".cache",
                     "selenium", "chromedriver"),
    ]

    # Check for the chromedriver in PATH environment variable
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for path_dir in path_dirs:
        potential_paths.append(os.path.join(path_dir, "chromedriver.exe"))
        potential_paths.append(os.path.join(path_dir, "chromedriver"))

    # Check if any of these paths exist
    for path in potential_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            print(f"Found ChromeDriver at: {path}")
            return path
        # If not executable but exists, check subdirectories
        elif os.path.exists(path) and os.path.isdir(path):
            # Search recursively in this directory (up to depth 2)
            for root, dirs, files in os.walk(path, topdown=True, followlinks=False):
                # Limit depth to 2 levels
                if root.count(os.sep) - path.count(os.sep) > 2:
                    dirs[:] = []  # Don't go deeper
                    continue

                for file in files:
                    if file == "chromedriver.exe" or file == "chromedriver":
                        full_path = os.path.join(root, file)
                        if os.access(full_path, os.X_OK):
                            print(f"Found ChromeDriver at: {full_path}")
                            return full_path

    # If we get here, no ChromeDriver was found
    print("WARNING: Could not find ChromeDriver in any of the expected locations.")
    print("Please install ChromeDriver and ensure it matches your Chrome version.")
    print("Download from: https://chromedriver.chromium.org/downloads")
    print("\nAvailable options:")
    print("1. Place chromedriver.exe in one of these locations:")
    for path in potential_paths[:5]:  # Show first 5 paths
        print(f"   - {path}")
    print("2. Add chromedriver to your PATH environment variable")
    return None


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        # Deprecated: Hardcoded paths
        # self.chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
        # self.chrome_executable_path = r"C:\SeleniumDrivers\chrome-win64\chrome.exe"

        # Preferred: Find chrome executable path
        self.chrome_executable_path = self._find_chrome_executable()

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

        if self.chrome_executable_path:
            chrome_options.binary_location = self.chrome_executable_path
        else:
            logging.warning(
                "Could not find Chrome executable. Selenium might use the default installation.")

        try:
            # Find ChromeDriver
            chromedriver_path = find_chromedriver()

            if chromedriver_path:
                print(f"Using ChromeDriver: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(
                    service=service, options=chrome_options)
            else:
                # Fall back to webdriver-manager if no ChromeDriver found
                print("No ChromeDriver found. Falling back to webdriver-manager...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(
                    service=service, options=chrome_options)

            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")

        except Exception as e:
            logging.exception(f"Failed to initialize Chrome: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def _find_chrome_executable(self):
        """Find the Chrome executable in common locations."""
        potential_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         "Google\Chrome\Application\chrome.exe"),
            os.path.join(os.environ.get("ProgramW6432", ""),
                         "Google\Chrome\Application\chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""),
                         "Google\Chrome\Application\chrome.exe")
        ]
        for path in potential_paths:
            if path and os.path.exists(path):
                logging.info(f"Found Chrome executable at: {path}")
                return path
        logging.warning("Could not automatically find Chrome executable path.")
        return None

    def _get_youtube_credentials(self):
        """Gets valid user credentials from storage or runs the OAuth2 flow."""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # YOU MUST HAVE client_secret.json IN THE SAME DIRECTORY AS THIS SCRIPT
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json',
                    scopes=['https://www.googleapis.com/auth/youtube.upload']
                )
                # Run the flow using a local server.
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def upload_to_youtube(self, video_path, client_name):
        """
        Uploads the video to YouTube and returns the video URL.
        Handles both regular videos and Shorts based on duration.
        """
        logging.info(
            f"Attempting to upload {video_path} to YouTube for {client_name}.")
        if not os.path.exists(video_path):
            logging.error(
                f"Video path {video_path} does not exist. Cannot upload to YouTube.")
            return None

        try:
            # Check video duration to determine if it should be a Short
            import subprocess
            try:
                # Get video duration using ffprobe
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-show_entries',
                    'format=duration', '-of', 'csv=p=0', video_path
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    is_short = duration <= 60  # 60 seconds or less = Short
                    logging.info(
                        f"Video duration: {duration:.1f}s, treating as {'Short' if is_short else 'regular video'}")
                else:
                    logging.warning(
                        "Could not determine video duration, defaulting to regular video")
                    is_short = False
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
                logging.warning(
                    f"Error checking video duration: {e}, defaulting to regular video")
                is_short = False

            credentials = self._get_youtube_credentials()
            youtube = build('youtube', 'v3', credentials=credentials)

            first_name = self.get_first_name(client_name)

            # Adjust title and description based on video type
            if is_short:
                video_title = f"{first_name}'s Weekly Check-in #Shorts"
                video_description = f"Your personalized weekly check-in video, {first_name}! Keep up the great work! #Shorts #Fitness #CheckIn"
                tags = ['fitness', 'check-in', 'personalized coaching',
                        client_name, 'shorts', 'fitnessshorts']
            else:
                video_title = f"{first_name}'s Weekly Check-in Video"
                video_description = f"Your personalized weekly check-in video, {first_name}. Keep up the great work!"
                tags = ['fitness', 'check-in',
                        'personalized coaching', client_name]

            request_body = {
                'snippet': {
                    'title': video_title,
                    'description': video_description,
                    'tags': tags,
                    # People & Blogs. You can find other category IDs if needed.
                    'categoryId': '22'
                },
                'status': {
                    # Options: 'public', 'private', 'unlisted'
                    'privacyStatus': 'unlisted',
                    'selfDeclaredMadeForKids': False
                }
            }

            media_file = MediaFileUpload(video_path,
                                         mimetype='video/mp4',
                                         resumable=True)

            logging.info(
                f"Uploading '{video_title}' to YouTube as {'Short' if is_short else 'regular video'}...")
            response_upload = youtube.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=media_file
            ).execute()

            video_id = response_upload.get('id')
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            logging.info(
                f"Video uploaded successfully! Video ID: {video_id}, URL: {youtube_url}")
            return youtube_url

        except Exception as e:
            logging.exception(
                f"Failed to upload video {video_path} to YouTube for {client_name}: {e}")
            return None

    def _navigate_to_client_dashboard(self, client_name):
        """Navigates to the specific client's dashboard/profile area."""
        try:
            logging.info(f"Navigating to client dashboard for: {client_name}")

            # Click the 'Clients' link in the sidebar
            logging.info("Attempting to click 'Clients' link in sidebar...")
            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
                logging.info(
                    "Clicked 'Clients' link. Waiting for client list page...")
                time.sleep(5)  # Wait for client list to load
            except TimeoutException:
                logging.error(
                    "Timeout while waiting for 'Clients' link. Trying direct navigation.")
                self.driver.get(
                    "https://www.trainerize.com/app/clients")  # Fallback
                time.sleep(5)

            # Enter client name into the search bar
            logging.info(f"Searching for client: {client_name}")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            search_input.clear()
            search_input.send_keys(client_name)
            logging.info("Waiting for search results...")
            time.sleep(5)

            # Click on the client's name in the search results
            client_link_locator = (
                By.XPATH, f"//a[translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{client_name.lower()}']")
            client_link = self.wait.until(
                EC.element_to_be_clickable(client_link_locator))
            client_link.click()
            logging.info(
                f"Clicked on client '{client_name}'. Waiting for profile dialog...")
            time.sleep(4)

            # Click the 'Open' button to switch into the client profile
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(
                EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            logging.info(
                "Clicked 'Open' to switch into client profile. Waiting for new tab...")
            time.sleep(5)

            # Switch to the new tab
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    logging.info(
                        f"Switched to new window: {self.driver.title}")
                    break
            time.sleep(3)

            logging.info(
                f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True

        except TimeoutException as te:
            logging.error(
                f"TimeoutException during client navigation for {client_name}: {te.msg}")
            try:
                screenshot_path = f"debug_nav_timeout_{client_name.replace(' ', '_')}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Saved navigation timeout screenshot to {screenshot_path}")
            except Exception as e_ss:
                logging.error(
                    f"Could not save screenshot on navigation timeout: {e_ss}")
            return False
        except Exception as e:
            logging.exception(
                f"Error navigating to client {client_name}'s dashboard: {e}")
            try:
                screenshot_path = f"debug_nav_error_{client_name.replace(' ', '_')}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Saved navigation error screenshot to {screenshot_path}")
            except Exception as e_ss:
                logging.error(
                    f"Could not save screenshot on navigation error: {e_ss}")
            return False

    def add_video_link_to_schedule(self, client_name, youtube_url, message_text):
        """
        Navigates to the client's schedule in Trainerize and adds a message
        with the YouTube video link for the upcoming Monday.
        """
        try:
            logging.info(
                f"Attempting to add YouTube link {youtube_url} to {client_name}'s schedule.")

            # Step 1: Navigate to the client's dashboard area
            # Note: _navigate_to_client_dashboard already switches to the client's tab.
            if not self._navigate_to_client_dashboard(client_name):
                logging.error(
                    f"Failed to navigate to {client_name}'s dashboard. Aborting schedule update.")
                # Ensure we are back on the main window if a new tab was opened and navigation failed partially
                if len(self.driver.window_handles) > 1:
                    # Attempt to close the new tab and switch back
                    all_windows = self.driver.window_handles
                    current_window = self.driver.current_window_handle
                    for window in all_windows:
                        if window != current_window:  # Assuming the main window is the one not current
                            self.driver.switch_to.window(window)
                            break  # Switched to a presumed main/other tab
                    if self.driver.current_window_handle != current_window:  # If switch happened
                        self.driver.close()  # Close the new tab we were on
                        # Switch to the very first tab as main
                        self.driver.switch_to.window(all_windows[0])
                    # If switch didn't happen (e.g. only one window left or error)
                    else:
                        self.driver.switch_to.window(
                            all_windows[0])  # Go to first tab
                return False

            logging.info(
                f"Successfully on {client_name}'s dashboard. Current URL: {self.driver.current_url}")
            time.sleep(3)  # Allow page to settle

            # Step 2: Click "Calendar"
            logging.info("Clicking on 'Calendar'...")
            calendar_locators = [
                (By.XPATH, "//a[contains(@href, 'calendar') and (.//p[contains(text(), 'Calendar')] or contains(text(), 'Calendar'))]"),
                (By.XPATH,
                 "//p[contains(@class, 'color--gray80') and contains(text(), 'Calendar')]/ancestor::a[1]"),
                (By.XPATH,
                 "//div[contains(@class, 'clickable') and .//p[contains(text(), 'Calendar')]]"),
                (By.ID, "nav_calendar"),
                (By.XPATH, "//a[@data-testid='leftNavMenu-item-calendar']")
            ]
            calendar_link = None
            for i, (by, val) in enumerate(calendar_locators):
                try:
                    logging.info(
                        f"Trying Calendar locator strategy {i+1}: {by} = {val}")
                    element = self.wait.until(
                        EC.element_to_be_clickable((by, val)))
                    calendar_link = element
                    logging.info("Found clickable 'Calendar' element.")
                    break
                except TimeoutException:
                    logging.warning(f"Calendar locator strategy {i+1} failed.")
                    continue

            if not calendar_link:
                logging.error("Could not find or click 'Calendar' link.")
                self._close_client_tab_and_return()
                return False

            self.driver.execute_script("arguments[0].click();", calendar_link)
            logging.info("Clicked 'Calendar'. Waiting for calendar page...")
            time.sleep(5)

            # Step 3: Click "Schedule" button then "Auto messages"
            logging.info("Clicking 'Schedule' button...")
            schedule_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']")
            schedule_button = self.wait.until(
                EC.element_to_be_clickable(schedule_button_locator))
            schedule_button.click()
            logging.info("Clicked 'Schedule' button. Waiting for dropdown...")
            time.sleep(2)

            logging.info("Clicking 'Auto messages' from dropdown...")
            auto_messages_locators = [
                (By.XPATH, "//li[.//p[contains(text(), 'Auto messages')]]"),
                (By.XPATH, "//a[.//p[contains(text(), 'Auto messages')]]"),
                (By.XPATH,
                 "//div[contains(@class, 'ant-dropdown-menu-item') and contains(., 'Auto messages')]"),
                # More specific antd item
                (By.XPATH, "//span[contains(@class, 'ant-dropdown-menu-title-content') and contains(text(), 'Auto Message')]/ancestor::li[1]")
            ]
            auto_message_option = None
            for i, (by, val) in enumerate(auto_messages_locators):
                try:
                    logging.info(
                        f"Trying Auto Message locator strategy {i+1}: {by} = {val}")
                    element = self.wait.until(
                        EC.element_to_be_clickable((by, val)))
                    auto_message_option = element
                    logging.info("Found clickable 'Auto messages' option.")
                    break
                except TimeoutException:
                    logging.warning(
                        f"Auto Message locator strategy {i+1} failed.")
                    continue

            if not auto_message_option:
                logging.error(
                    "Could not find or click 'Auto messages' option.")
                self._close_client_tab_and_return()
                return False

            auto_message_option.click()
            logging.info("Clicked 'Auto messages'. Waiting for popup...")
            time.sleep(3)

            # Step 4: Fill in Auto Message details
            logging.info("Filling in Auto Message title...")
            title_input_locator = (By.ID, "input_dailyMessage_title")
            title_input = self.wait.until(
                EC.visibility_of_element_located(title_input_locator))
            title_input.send_keys("CHECK IT OUT - YOUR WEEK WRAPPED!")
            time.sleep(1)

            logging.info("Typing message (with YouTube link)...")
            message_textarea_locator = (By.ID, "messages_input")
            message_textarea = self.wait.until(
                EC.visibility_of_element_located(message_textarea_locator))
            # message_text is already formatted
            message_textarea.send_keys(message_text)
            logging.info(f"Entered message: {message_text}")
            time.sleep(1)

            # Step 5: Click "Add" button first
            logging.info("Clicking 'Add' button...")
            add_button_locator = (By.ID, "btn__messages_autoMessage_add")
            add_button = self.wait.until(
                EC.element_to_be_clickable(add_button_locator))
            add_button.click()
            logging.info("Clicked 'Add' button. Waiting for next dialog...")
            time.sleep(2)

            # Step 6: Click "Schedule" button in the popup
            logging.info("Clicking 'Schedule' button...")
            schedule_popup_button_locator = (
                By.ID, "btn_dailyMessage_dialog_save")
            schedule_popup_button = self.wait.until(
                EC.element_to_be_clickable(schedule_popup_button_locator))
            schedule_popup_button.click()
            logging.info(
                "Clicked 'Schedule' in popup. Waiting for date selection dialog...")
            time.sleep(3)

            # Step 7: Select the date (upcoming Monday)
            logging.info("Selecting date (upcoming Monday)...")

            # Calculate next Monday
            today = datetime.today()
            days_until_monday = (0 - today.weekday() + 7) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            upcoming_monday = today + timedelta(days=days_until_monday)
            monday_day_str = str(upcoming_monday.day)
            logging.info(
                f"Calculated upcoming Monday: {upcoming_monday.strftime('%Y-%m-%d')}, day to click: {monday_day_str}")

            # Click the date picker input
            date_picker_input_locator = (
                By.CSS_SELECTOR, "input[placeholder='Select date'][data-testid='multipleActivitiesDialog-dateSelect-clientCalendarSelect']")

            # Wait for any overlays to disappear and element to be clickable
            time.sleep(2)

            try:
                date_picker_input = self.wait.until(
                    EC.element_to_be_clickable(date_picker_input_locator))

                # Scroll element into view if needed
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", date_picker_input)
                time.sleep(1)

                # Try JavaScript click first as it's more reliable
                self.driver.execute_script(
                    "arguments[0].click();", date_picker_input)
                logging.info("Clicked date picker input using JavaScript")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Error clicking date picker: {e}")
                # Try alternative selectors
                alternative_selectors = [
                    "input[placeholder='Select date']",
                    "input.ant-calendar-picker-input",
                    "[data-testid='multipleActivitiesDialog-dateSelect-clientCalendarSelect']"
                ]

                for selector in alternative_selectors:
                    try:
                        logging.info(
                            f"Trying alternative date picker selector: {selector}")
                        alt_input = self.driver.find_element(
                            By.CSS_SELECTOR, selector)
                        if alt_input.is_displayed():
                            self.driver.execute_script(
                                "arguments[0].click();", alt_input)
                            logging.info(
                                f"Successfully clicked date picker using selector: {selector}")
                            time.sleep(2)
                            break
                    except Exception as alt_e:
                        logging.info(
                            f"Alternative selector {selector} failed: {alt_e}")
                        continue
                else:
                    raise Exception(
                        "Could not click date picker with any selector")

                    # Debug: Let's see what calendar elements are actually available
            logging.info("Debugging calendar structure...")
            try:
                # Look for any elements containing the day number
                all_day_elements = self.driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{monday_day_str}')]")
                logging.info(
                    f"Found {len(all_day_elements)} elements containing '{monday_day_str}'")

                # Check first 5
                for i, elem in enumerate(all_day_elements[:5]):
                    try:
                        tag = elem.tag_name
                        classes = elem.get_attribute("class") or "no-class"
                        text = elem.text
                        displayed = elem.is_displayed()
                        enabled = elem.is_enabled()
                        logging.info(
                            f"Element {i+1}: tag={tag}, class='{classes}', text='{text}', displayed={displayed}, enabled={enabled}")
                    except Exception as e:
                        logging.info(f"Error inspecting element {i+1}: {e}")
            except Exception as e:
                logging.info(f"Error during calendar debugging: {e}")

            # Try multiple selectors to find the day
            day_selectors = [
                f"//div[text()='{monday_day_str}']",
                f"//*[text()='{monday_day_str}']",
                f"//td[contains(@class, 'ant-calendar-cell')]//div[text()='{monday_day_str}']",
                f"//div[contains(@class, 'ant-calendar-date') and text()='{monday_day_str}']",
                f"//span[text()='{monday_day_str}']",
                f"//a[text()='{monday_day_str}']",
                f"//*[contains(@class, 'calendar') and text()='{monday_day_str}']"
            ]

            monday_clicked = False
            for i, selector in enumerate(day_selectors, 1):
                try:
                    logging.info(f"Trying day selector {i}: {selector}")
                    monday_elements = self.driver.find_elements(
                        By.XPATH, selector)
                    logging.info(
                        f"Found {len(monday_elements)} elements with selector {i}")

                    for j, element in enumerate(monday_elements):
                        try:
                            tag = element.tag_name
                            classes = element.get_attribute(
                                "class") or "no-class"
                            displayed = element.is_displayed()
                            enabled = element.is_enabled()
                            logging.info(
                                f"  Element {j+1}: tag={tag}, class='{classes}', displayed={displayed}, enabled={enabled}")

                            if displayed and enabled:
                                # Check if it's not disabled or from another month
                                if "disabled" not in classes.lower() and "next-month" not in classes.lower() and "prev-month" not in classes.lower():
                                    logging.info(
                                        f"Attempting to click day {monday_day_str} using selector {i}, element {j+1}")
                                    self.driver.execute_script(
                                        "arguments[0].click();", element)
                                    monday_clicked = True
                                    logging.info(
                                        f"Successfully clicked on day {monday_day_str}")
                                    break
                                else:
                                    logging.info(
                                        f"  Skipping element {j+1} due to disabled/wrong-month classes: {classes}")
                        except Exception as e:
                            logging.info(
                                f"Error clicking element {j+1} with selector {i}: {e}")
                            continue

                    if monday_clicked:
                        break

                except Exception as e:
                    logging.info(f"Day selector {i} failed: {e}")
                    continue

            if not monday_clicked:
                logging.error(
                    f"Could not find or click day {monday_day_str} with any selector")
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"debug_calendar_{client_name.replace(' ', '_')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logging.info(
                        f"Saved calendar debug screenshot to {screenshot_path}")
                except:
                    pass
                raise Exception(f"Failed to select day {monday_day_str}")

            time.sleep(1)

            # Step 8: Click "Add" button
            # Wait for any backdrop/overlay to disappear after date selection
            time.sleep(3)

            # Try to close any date picker backdrop first
            try:
                backdrop_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, ".datePicker__backdrop, .ant-calendar-picker-container")
                for backdrop in backdrop_elements:
                    if backdrop.is_displayed():
                        logging.info(
                            "Found date picker backdrop, clicking to close it")
                        self.driver.execute_script(
                            "arguments[0].click();", backdrop)
                        time.sleep(1)
                        break
            except Exception as e:
                logging.info(f"No backdrop to close or error closing: {e}")

            # Try pressing Escape to close any overlays
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                logging.info("Pressed Escape to close any overlays")
                time.sleep(2)
            except Exception as e:
                logging.info(f"Error pressing Escape: {e}")

            add_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']")

            # Wait for the button to be clickable and try multiple click methods
            try:
                add_button = self.wait.until(
                    EC.element_to_be_clickable(add_button_locator))

                # Scroll button into view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", add_button)
                time.sleep(1)

                # Try JavaScript click first (more reliable with overlays)
                self.driver.execute_script("arguments[0].click();", add_button)
                logging.info(
                    "Clicked 'Add' button using JavaScript. Waiting for confirmation/dialog close...")

            except Exception as e:
                logging.error(
                    f"Error clicking Add button with JavaScript: {e}")
                # Fallback to regular click
                try:
                    add_button = self.driver.find_element(*add_button_locator)
                    add_button.click()
                    logging.info(
                        "Clicked 'Add' button using regular click. Waiting for confirmation/dialog close...")
                except Exception as e2:
                    logging.error(f"Error with regular click too: {e2}")
                    raise

            time.sleep(5)

            logging.info(
                f"Successfully scheduled message for {client_name} for upcoming Monday.")

            # Wait a moment for the action to complete
            time.sleep(2)

            # Helper to close current tab and switch to main
            self._close_client_tab_and_return()
            return True

        except TimeoutException as te:
            logging.error(
                f"TimeoutException during scheduling for {client_name}: {te.msg}")
            try:
                screenshot_path = f"debug_schedule_timeout_{client_name.replace(' ', '_')}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Saved schedule timeout screenshot to {screenshot_path}")
            except Exception as e_ss:
                logging.error(
                    f"Could not save screenshot on schedule timeout: {e_ss}")
            self._close_client_tab_and_return()
            return False
        except Exception as e:
            logging.exception(
                f"Error adding video link to schedule for {client_name}: {e}")
            try:
                screenshot_path = f"debug_schedule_error_{client_name.replace(' ', '_')}.png"
                self.driver.save_screenshot(screenshot_path)
                logging.info(
                    f"Saved schedule error screenshot to {screenshot_path}")
            except Exception as e_ss:
                logging.error(
                    f"Could not save screenshot on schedule error: {e_ss}")
            self._close_client_tab_and_return()
            return False

    def _navigate_calendar_to_date(self, target_date):
        """ Helper to navigate ant-design calendar to the month and year of target_date. """
        try:
            # Get current displayed month and year on the calendar
            # These selectors might need to be more robust if they are not consistently ant-select-selection-selected-value
            current_month_text = self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".ant-calendar-month-select .ant-select-selection-selected-value"))).text.strip()
            # Convert month name (e.g., "May") to number
            current_month_on_calendar = datetime.strptime(
                current_month_text, "%b").month if current_month_text.isalpha() else int(current_month_text)
            current_year_on_calendar = int(self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".ant-calendar-year-select .ant-select-selection-selected-value"))).text.strip())
            logging.info(
                f"Calendar currently shows: {current_month_on_calendar}/{current_year_on_calendar}. Target: {target_date.month}/{target_date.year}")

            # Navigate years
            while target_date.year > current_year_on_calendar:
                logging.info("Navigating to next year in calendar...")
                self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-next-year-btn").click()
                time.sleep(0.3)
                current_year_on_calendar = int(self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-year-select .ant-select-selection-selected-value").text.strip())
            while target_date.year < current_year_on_calendar:
                logging.info("Navigating to previous year in calendar...")
                self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-prev-year-btn").click()
                time.sleep(0.3)
                current_year_on_calendar = int(self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-year-select .ant-select-selection-selected-value").text.strip())

            # Navigate months
            current_month_text = self.driver.find_element(
                By.CSS_SELECTOR, ".ant-calendar-month-select .ant-select-selection-selected-value").text.strip()
            current_month_on_calendar = datetime.strptime(
                current_month_text, "%b").month if current_month_text.isalpha() else int(current_month_text)

            while target_date.month > current_month_on_calendar:
                logging.info("Navigating to next month in calendar...")
                self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-next-month-btn").click()
                time.sleep(0.3)
                current_month_text = self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-month-select .ant-select-selection-selected-value").text.strip()
                current_month_on_calendar = datetime.strptime(
                    current_month_text, "%b").month if current_month_text.isalpha() else int(current_month_text)
            while target_date.month < current_month_on_calendar:
                logging.info("Navigating to previous month in calendar...")
                self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-prev-month-btn").click()
                time.sleep(0.3)
                current_month_text = self.driver.find_element(
                    By.CSS_SELECTOR, ".ant-calendar-month-select .ant-select-selection-selected-value").text.strip()
                current_month_on_calendar = datetime.strptime(
                    current_month_text, "%b").month if current_month_text.isalpha() else int(current_month_text)
            logging.info(
                f"Calendar now shows: {current_month_on_calendar}/{current_year_on_calendar}")
        except Exception as e:
            logging.error(
                f"Error navigating calendar to target date {target_date.strftime('%Y-%m-%d')}: {e}")
            # Optionally re-raise or handle as critical error if calendar navigation is essential
            raise  # Re-raise to be caught by the calling function

    def _close_client_tab_and_return(self):
        """Closes the current tab (assumed to be client's) and switches to the first window handle."""
        try:
            logging.info(
                "Attempting to close client tab and return to main window...")
            if len(self.driver.window_handles) > 1:
                current_window = self.driver.current_window_handle
                all_windows = self.driver.window_handles
                self.driver.close()  # Close current tab
                # Switch to the first window in the list, assuming it's the main one
                # or the one we want to return to.
                remaining_windows = [
                    win for win in all_windows if win != current_window]
                if remaining_windows:
                    self.driver.switch_to.window(remaining_windows[0])
                else:  # Should not happen if len > 1 initially, but as a fallback
                    self.driver.switch_to.window(self.driver.window_handles[0])
                logging.info(
                    f"Closed tab. Switched to window: {self.driver.title}")
                time.sleep(1)
                # Attempt to close any lingering client profile dialog on the main page
                try:
                    close_dialog_button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR,
                         "span[data-testid='close-button'].closeButton.clickable")
                    ))
                    if close_dialog_button.is_displayed():
                        close_dialog_button.click()
                        logging.info(
                            "Closed lingering client profile dialog on main page.")
                        time.sleep(0.5)
                except TimeoutException:
                    logging.info(
                        "No lingering client profile dialog to close on main page.")
                except Exception as e_dialog_close:
                    logging.warning(
                        f"Exception closing lingering dialog: {e_dialog_close}")
            elif len(self.driver.window_handles) == 1:
                logging.info(
                    "Already on the only open window. Ensuring it's the clients list or dashboard.")
                # Optionally navigate to a known safe page if not already there
                if "clients" not in self.driver.current_url.lower() and "dashboard" not in self.driver.current_url.lower():
                    self.driver.get("https://www.trainerize.com/app/clients")
                    time.sleep(2)
            else:  # No windows open, should not happen
                logging.warning(
                    "No windows open during _close_client_tab_and_return call.")

        except NoSuchWindowException:
            logging.warning(
                "NoSuchWindowException: Window already closed or not found during _close_client_tab_and_return.")
            if self.driver.window_handles:  # If some windows still exist, switch to the first one
                try:
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    logging.info(
                        f"Switched to first available window: {self.driver.title}")
                except Exception as e_switch_fallback:
                    logging.error(
                        f"Error switching to fallback window: {e_switch_fallback}")
            else:
                logging.error(
                    "No windows available to switch to after NoSuchWindowException.")
        except Exception as e:
            logging.exception(f"Error in _close_client_tab_and_return: {e}")

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
            logging.info("Successfully logged in!")
            return True
        except Exception as e:
            logging.exception(f"Error during login: {e}")
            return False

    def click_messages(self):
        """Clicks on the Messages link in the left navigation menu."""
        try:
            logging.info("Attempting to click on the Messages link...")
            messages_link_locator = (By.ID, "nav_messages")
            messages_link = self.wait.until(
                EC.element_to_be_clickable(messages_link_locator))
            messages_link.click()
            logging.info("Successfully clicked on Messages link.")
            time.sleep(2)  # Wait for messages page to load
            return True
        except Exception as e:
            logging.exception(f"Error clicking on Messages link: {e}")
            return False

    def click_member_in_messages(self, member_name):
        """Finds and clicks on a member in the messages list."""
        try:
            logging.info(
                f"Looking for member: {member_name} in messages list...")
            # Using XPath to find the paragraph element with the exact text and class
            member_locator = (
                By.XPATH, f"//p[contains(@class, 'tz-sp') and contains(@class, 'color--black') and contains(@class, 'm2b') and text()='{member_name}']")

            # Wait for the element to be clickable
            try:
                member_element = self.wait.until(
                    EC.element_to_be_clickable(member_locator))

                # Click on the member
                member_element.click()
                logging.info(f"Successfully clicked on member: {member_name}")
                time.sleep(2)  # Wait for the conversation to load
                return True, True  # Return (success, found_in_inbox)
            except TimeoutException:
                logging.info(
                    f"Could not find member: {member_name} in the messages list. Will try to start a new conversation.")
                success = self.start_new_conversation(member_name)
                return success, False  # Return (success, found_in_inbox=False)
        except Exception as e:
            logging.exception(f"Error clicking on member {member_name}: {e}")
            return False, False

    def start_new_conversation(self, client_name):
        """Start a new conversation with a client when they are not found in the inbox."""
        try:
            logging.info(f"Starting a new conversation with {client_name}...")
            # Find and click the NEW button
            new_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '[data-testid="add_new_message_button"]'))
            )
            new_button.click()
            logging.info("Clicked on NEW button")
            time.sleep(2)  # Wait for popup to appear

            # First look for the placeholder div that contains "Enter one or more people"
            found_input = False
            try:
                # Find the placeholder div first
                placeholder_div = self.wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".ant-select-selection__placeholder"))
                )
                if "Enter one or more people" in placeholder_div.text:
                    logging.info(
                        f"Found the placeholder div: {placeholder_div.text}")

                    # Click on the parent selection component rather than the placeholder itself
                    parent_selector = self.driver.find_element(
                        By.CSS_SELECTOR, ".ant-select-selection")
                    self.driver.execute_script(
                        "arguments[0].click();", parent_selector)
                    logging.info("Clicked on the selection component")
                    time.sleep(1)

                    # Now look for the actual input that appears
                    input_field = self.wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "input.ant-select-search__field"))
                    )

                    # Type the client name
                    input_field.clear()
                    input_field.send_keys(client_name)
                    logging.info(f"Typed client name: {client_name}")
                    time.sleep(2)  # Wait for autocomplete

                    # Press Enter to select the name
                    input_field.send_keys(Keys.ENTER)
                    logging.info("Pressed ENTER to select the client name")
                    found_input = True

                    # Wait for the conversation to load
                    # Increased wait time to ensure conversation loads
                    time.sleep(8)

                    # Verify that we're in the conversation view by checking for message composer or conversation container
                    try:
                        # Check for message composer or conversation container
                        self.driver.find_element(
                            By.CSS_SELECTOR, '.message-composer, .conversation-container, .messageComposer__wrapper, [role="combobox"][contenteditable="true"]')
                        logging.info(
                            "Conversation view has loaded successfully")
                        return True
                    except:
                        logging.warning(
                            "Could not verify that conversation has loaded after selecting client")
                        return False
            except Exception as e:
                logging.info(f"Could not find ant-select placeholder: {e}")

            # If the above method failed, try the alternative approach with input fields
            if not found_input:
                # Try with more generic selectors as fallback
                selectors = [
                    '[placeholder="Enter name"]',
                    '[data-testid="client-search"]',
                    'input.conversation-selector',
                    'input[type="text"]',
                    '.ant-select-selection input'
                ]

                name_input = None
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                name_input = element
                                logging.info(
                                    f"Found name input field with selector: {selector}")
                                break
                        if name_input:
                            break
                    except:
                        continue

                if not name_input:
                    logging.error(
                        "Could not find the name input field in the new message dialog")
                    return False

                # Click the input field to focus it
                name_input.click()
                time.sleep(1)

                # Clear any existing text and type the client name
                name_input.clear()
                name_input.send_keys(client_name)
                logging.info(f"Entered client name: {client_name}")
                time.sleep(2)  # Wait for autocomplete

                # Press ENTER to select the name
                name_input.send_keys(Keys.ENTER)
                logging.info("Pressed ENTER to select the client name")

                # Wait for the conversation to load
                # Increased wait time to ensure conversation loads
                time.sleep(8)

                # Verify that we're in the conversation view
                try:
                    # Check for message composer or conversation container
                    self.driver.find_element(
                        By.CSS_SELECTOR, '.message-composer, .conversation-container, .messageComposer__wrapper, [role="combobox"][contenteditable="true"]')
                    logging.info("Conversation view has loaded successfully")
                    return True
                except:
                    logging.warning(
                        "Could not verify that conversation has loaded after selecting client")
                    return False

        except Exception as e:
            logging.exception(
                f"Error starting new conversation with {client_name}: {e}")
            return False

    def click_attachment_icon(self):
        """Clicks on the attachment (paper clip) icon in the conversation."""
        try:
            logging.info(
                "Attempting to click on any visible attachment/upload button...")

            # Wait a moment for any pop-up windows to fully render
            time.sleep(3)

            # Try several approaches to find any attachment/upload button
            possible_selectors = [
                # First try the specific SVG use element in the popup
                "//use[@href='#outline/attach']",
                "//svg[.//use[@href='#outline/attach']]",
                "//button[.//use[@href='#outline/attach']]",
                # Then try photos/photos selectors
                "//use[@href='#outline/photos/photos']",
                "//svg[.//use[@href='#outline/photos/photos']]",
                "//button[.//use[@href='#outline/photos/photos']]",
                # Then try finding attachment buttons by broader SVG names
                "//svg[@name='outline/attach']",
                "//svg[@name='outline/photos/photos']",
                # Then fall back to broader selectors
                "//button[contains(@class, 'upload')]",
                "//span[contains(text(), 'Upload')]",
                "//span[contains(text(), 'Attach')]",
                "//div[contains(@class, 'attachment')]",
                "//div[contains(@class, 'upload')]"
            ]

            for selector in possible_selectors:
                try:
                    logging.info(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logging.info(
                            f"Found {len(elements)} elements with selector {selector}")
                        for element in elements:
                            if element.is_displayed():
                                logging.info(
                                    f"Clicking on visible element with selector {selector}")
                                # Try JavaScript click which is more reliable
                                self.driver.execute_script(
                                    "arguments[0].click();", element)
                                time.sleep(2)
                                return True
                except Exception as e:
                    logging.info(f"Error with selector {selector}: {e}")
                    continue

            # If we still haven't found it, try using CSS selectors
            css_selectors = [
                # Direct CSS selectors for the attachment icons
                "[href='#outline/attach']",
                "[href='#outline/photos/photos']",
                "svg[name='outline/attach']",
                "svg[name='outline/photos/photos']",
                # Button containing paperclip or attachment icons
                "button.ant-btn svg",
                ".ant-upload-button",
                "[class*='attachment']",
                # Any visible button in the popup with icon
                ".ant-modal button",
                ".ant-modal-content button",
                # Direct parent of the icon
                "span[role='button'] svg"
            ]

            for selector in css_selectors:
                try:
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    if elements:
                        logging.info(
                            f"Found {len(elements)} elements with CSS selector {selector}")
                        for element in elements:
                            if element.is_displayed():
                                logging.info(
                                    f"Clicking on visible element with CSS selector {selector}")
                                self.driver.execute_script(
                                    "arguments[0].click();", element)
                                time.sleep(2)
                                return True
                except Exception as e:
                    logging.info(f"Error with CSS selector {selector}: {e}")
                    continue

            # Try to find ANY button in the dialog
            try:
                logging.info("Looking for any buttons in the dialog/popup...")
                popup_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, ".ant-modal-content button, .ant-modal button")
                for button in popup_buttons:
                    try:
                        if button.is_displayed():
                            logging.info(
                                "Found a button in the popup, inspecting...")
                            # Check if it has a child svg element
                            svg_elements = button.find_elements(
                                By.TAG_NAME, "svg")
                            if svg_elements:
                                logging.info(
                                    "Button has SVG, likely attachment. Clicking...")
                                self.driver.execute_script(
                                    "arguments[0].click();", button)
                                time.sleep(2)
                                return True
                    except Exception as e:
                        continue
            except Exception as e:
                logging.info(f"Error finding buttons in popup: {e}")

            # Last resort - check for any buttons with no text (icon buttons)
            try:
                logging.info("Looking for any icon buttons...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    try:
                        if button.is_displayed() and button.text.strip() == "":
                            # If it has children, it might be an icon button
                            if button.find_elements(By.XPATH, "./*"):
                                logging.info("Found a potential icon button")
                                self.driver.execute_script(
                                    "arguments[0].click();", button)
                                time.sleep(2)
                                return True
                    except:
                        continue
            except Exception as e:
                logging.info(f"Error with icon button fallback: {e}")

            # If we couldn't find any attachment icon, try directly injecting a file input
            logging.info(
                "No attachment icon found, but returning True to continue with file upload attempts")
            return True

        except Exception as e:
            logging.exception(f"Error clicking on attachment icon: {e}")
            return False

    def get_video_path(self, client_name):
        """Find the most recent video file for a given client matching the pattern Client Name_week_summary_*.mp4 (with spaces)."""
        import glob
        base_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output"
        pattern = os.path.join(base_path, f"{client_name}_week_summary_*.mp4")
        matching_files = glob.glob(pattern)
        if not matching_files:
            return None
        # Sort by modified time, newest first
        matching_files.sort(key=os.path.getmtime, reverse=True)
        return matching_files[0]

    def get_json_path(self, client_name):
        """Generate the correct JSON path for a given client.

        Args:
            client_name: Name of the client

        Returns:
            Full path to the client's JSON file
        """
        # Convert spaces to underscores in client name
        client_name_formatted = client_name.replace(" ", "_")

        # Construct the path to look for JSON files
        checkin_reviews_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"

        # Look for the most recent JSON file for this client (format: Client_Name_YYYY-MM-DD_fitness_wrapped_data.json)
        json_pattern = f"{client_name_formatted}_*_fitness_wrapped_data.json"
        matching_jsons = []

        # Check if directory exists
        if not os.path.exists(checkin_reviews_dir):
            logging.warning(
                f"Checkin reviews directory not found: {checkin_reviews_dir}")
            return None

        for file in os.listdir(checkin_reviews_dir):
            if file.startswith(client_name_formatted) and file.endswith("_fitness_wrapped_data.json"):
                matching_jsons.append(file)

        if not matching_jsons:
            logging.warning(f"No JSON data found for client: {client_name}")
            return None

        # Sort files by date (newest first) to get the most recent data
        matching_jsons.sort(reverse=True)
        json_filename = matching_jsons[0]

        full_path = os.path.join(checkin_reviews_dir, json_filename)
        logging.info(f"Found JSON data for {client_name}: {json_filename}")
        return full_path

    def get_first_name(self, full_name):
        """Extract the first name from a full name.

        Args:
            full_name: Full name of the client

        Returns:
            First name of the client
        """
        return full_name.split()[0]

    def type_message(self, client_name):
        """Types and sends a personalized message before attaching files.

        Args:
            client_name: Name of the client
        """
        try:
            # Get client's first name
            first_name = self.get_first_name(client_name)
            logging.info(f"Got first name: {first_name}")

            # Wait for the conversation to fully load
            time.sleep(3)

            logging.info("Trying to find textarea...")

            # Try multiple approaches to find the textarea
            textarea = None

            # Approach 1: Try multiple selectors
            textarea_selectors = [
                "textarea.ant-input[placeholder='Type your message']",
                "textarea[placeholder='Type your message']",
                "textarea.ant-input",
                "textarea"
            ]

            for selector in textarea_selectors:
                try:
                    logging.info(f"Trying textarea selector: {selector}")
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    logging.info(
                        f"Found {len(elements)} elements with selector {selector}")
                    for element in elements:
                        if element.is_displayed():
                            textarea = element
                            logging.info(
                                f"Found visible textarea with selector: {selector}")
                            break
                    if textarea:
                        break
                except Exception as e:
                    logging.info(
                        f"Error with textarea selector {selector}: {e}")
                    continue

            # Approach 2: If still not found, try to wait explicitly for the textarea
            if not textarea:
                try:
                    logging.info("Trying wait approach for textarea...")
                    textarea = self.wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "textarea")))
                    logging.info("Found textarea with wait approach")
                except Exception as e:
                    logging.info(f"Wait approach failed: {e}")

            # Approach 3: Last resort - look for any input element
            if not textarea:
                try:
                    logging.info("Looking for any input element...")
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for input_elem in inputs:
                        try:
                            if input_elem.is_displayed() and input_elem.get_attribute("type") != "file":
                                textarea = input_elem
                                logging.info("Found an input element to use")
                                break
                        except:
                            continue
                except Exception as e:
                    logging.info(f"Error finding input elements: {e}")

            if not textarea:
                logging.error("Could not find any message input field")
                return False

            # Type the initial greeting message
            message = f"Hey {first_name}, here's your weekly check-in!"

            # Clear the textarea
            try:
                textarea.clear()
                logging.info("Cleared textarea")
            except Exception as e:
                logging.info(f"Error clearing textarea: {e}")

            # Type the message using multiple methods
            try:
                # Method 1: Standard send_keys
                textarea.send_keys(message)
                logging.info(f"Typed message using send_keys: {message}")
            except Exception as e:
                logging.info(f"Error with send_keys: {e}")
                try:
                    # Method 2: JavaScript
                    self.driver.execute_script(
                        f"arguments[0].value = '{message}';", textarea)
                    logging.info("Typed message using JavaScript")
                except Exception as e:
                    logging.info(f"Error with JavaScript typing: {e}")
                    return False

            # Wait a brief moment to ensure the message is entered fully
            time.sleep(2)

            # Try to find Enter key and press it first (in some UIs this sends the message)
            try:
                textarea.send_keys(Keys.RETURN)
                logging.info("Pressed Enter key")
                time.sleep(2)

                # Check if message was sent by Enter key
                try:
                    message_elements = self.driver.find_elements(
                        By.XPATH, f"//div[contains(text(), '{message}')]")
                    if message_elements:
                        logging.info(
                            "Message appears to have been sent by Enter key")
                        return True
                except:
                    pass
            except Exception as e:
                logging.info(f"Error pressing Enter key: {e}")

            # If Enter key didn't work, try to find and click the Send button
            logging.info("Looking for Send button...")
            send_button = None
            send_selectors = [
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), 'Send')]",
                "//div[contains(@class, 'send')]",
                "//span[contains(text(), 'Send')]",
                "//button[contains(@class, 'ant-btn')][.//span[text()='Send']]",
                "//button[@type='submit']"
            ]

            for selector in send_selectors:
                try:
                    logging.info(f"Trying send button selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(
                        f"Found {len(elements)} send button candidates with selector {selector}")
                    for element in elements:
                        if element.is_displayed():
                            send_button = element
                            logging.info(
                                f"Found visible send button with selector: {selector}")
                            break
                    if send_button:
                        break
                except Exception as e:
                    logging.info(
                        f"Error with send button selector {selector}: {e}")
                    continue

            if not send_button:
                # Try to find any button that might be a send button
                try:
                    logging.info(
                        "Looking for any button that might be a send button...")
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        try:
                            if button.is_displayed():
                                button_text = button.text.lower()
                                if "send" in button_text or button_text == "":
                                    send_button = button
                                    logging.info(
                                        "Found a potential send button")
                                    break
                        except:
                            continue
                except Exception as e:
                    logging.info(f"Error finding general buttons: {e}")

            if not send_button:
                logging.error("Could not find send button")
                # Even if we can't find the send button, let's return True
                # since we at least typed the message
                return True

            # Try multiple ways to click the button
            try:
                # Method 1: Standard click
                send_button.click()
                logging.info("Clicked send button using standard click")
            except Exception as e:
                logging.info(f"Error with standard click: {e}")
                try:
                    # Method 2: JavaScript click
                    self.driver.execute_script(
                        "arguments[0].click();", send_button)
                    logging.info("Clicked send button using JavaScript")
                except Exception as e:
                    logging.info(f"Error with JavaScript click: {e}")
                    return False

            # Wait for the message to be sent
            time.sleep(3)

            return True
        except Exception as e:
            logging.exception(f"Error typing initial message: {e}")
            # Even if we failed, let's try to continue with file uploads
            return True

    def type_message_after_attachment(self, client_name):
        """Types a personalized message after attaching files.

        Args:
            client_name: Name of the client
        """
        try:
            # Get client's first name
            first_name = self.get_first_name(client_name)

            # Find the textarea to type a message
            # Try multiple selectors since the exact one might vary
            textarea_selectors = [
                "textarea.ant-input[placeholder='Type your message']",
                "textarea[placeholder='Type your message']",
                "textarea.ant-input",
                "textarea"
            ]

            textarea = None
            for selector in textarea_selectors:
                try:
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            textarea = element
                            break
                    if textarea:
                        break
                except:
                    continue

            if not textarea:
                logging.error("Could not find message textarea")
                return False

            # Type the follow-up message
            message = f"I've attached your personalized video and review document - enjoy!"
            textarea.clear()
            textarea.send_keys(message)
            logging.info(f"Typed follow-up message: {message}")

            # Wait a brief moment to ensure the message is entered fully
            time.sleep(1)

            # Find and click the Send button - try multiple approaches
            send_button = None
            send_selectors = [
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), 'Send')]",
                "//div[contains(@class, 'send')]",
                "//span[contains(text(), 'Send')]",
                "//button[contains(@class, 'ant-btn')][.//span[text()='Send']]"
            ]

            for selector in send_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            send_button = element
                            break
                    if send_button:
                        break
                except:
                    continue

            if not send_button:
                logging.error("Could not find send button")
                return False

            # Use JavaScript to click the button to avoid any potential issues
            self.driver.execute_script("arguments[0].click();", send_button)
            logging.info(
                "Clicked 'Send' button using JavaScript for follow-up message")

            # Wait for the message to be sent
            time.sleep(3)

            return True
        except Exception as e:
            logging.exception(f"Error typing follow-up message: {e}")
            return False

    def navigate_back_to_messages(self):
        """Returns to the main messages screen after sending a message to a client."""
        try:
            logging.info("Navigating back to main messages screen...")

            # First check if any modal dialogs are open and close them
            try:
                modal_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, ".ant-modal, .modal, [role='dialog']")
                if modal_elements:
                    for modal in modal_elements:
                        if modal.is_displayed():
                            logging.info(
                                "Found open dialog that might block navigation. Attempting to close it.")
                            self.close_dialog_after_posting()
                            time.sleep(1)
            except Exception as e:
                logging.info(f"Error checking for open dialogs: {e}")

            # Try clicking back button
            try:
                back_button_locator = (
                    By.XPATH, "//button[contains(@class, 'back') or contains(@aria-label, 'back')]")
                back_button = self.wait.until(
                    EC.element_to_be_clickable(back_button_locator))
                logging.info("Found back button, clicking...")

                # Use JavaScript to click which bypasses overlay issues
                self.driver.execute_script(
                    "arguments[0].click();", back_button)
                logging.info("Clicked back button using JavaScript")
                time.sleep(2)
                return True
            except Exception as e:
                logging.info(f"Back button not found or not clickable: {e}")

            # If back button failed, try messages link with JavaScript click
            try:
                logging.info("Trying to click messages link with JavaScript")
                messages_link = self.driver.find_element(By.ID, "nav_messages")
                self.driver.execute_script(
                    "arguments[0].click();", messages_link)
                logging.info("Clicked messages link using JavaScript")
                time.sleep(2)
                return True
            except Exception as e:
                logging.info(
                    f"Failed to click messages link with JavaScript: {e}")

            # Last resort: try to navigate directly to messages URL
            try:
                logging.info("Attempting direct navigation to messages URL")
                self.driver.get("https://www.trainerize.com/app/messages")
                time.sleep(3)
                return True
            except Exception as e:
                logging.exception(f"Failed direct navigation to messages: {e}")
                return False

        except Exception as e:
            logging.exception(f"Error navigating back to messages: {e}")
            return False

    def attach_video(self, video_path):
        """Attaches a video file to the message using various methods.

        Args:
            video_path: Full path to the video file to attach
        """
        try:
            logging.info(f"Attempting to attach video: {video_path}")

            # Try to use existing file inputs first
            found_input = False
            file_input = None

            # Method 1: Try to find any file input elements
            try:
                file_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='file']")
                logging.info(f"Found {len(file_inputs)} file input elements")

                if file_inputs:
                    for input_elem in file_inputs:
                        try:
                            # Make each input visible and accept videos
                            self.driver.execute_script("""
                                arguments[0].style.display = 'block';
                                arguments[0].style.visibility = 'visible';
                                arguments[0].style.opacity = '1';
                                arguments[0].setAttribute(
                                    'accept', '.mp4,video/mp4,video/*,*/*');
                            """, input_elem)

                            # Try to send keys to this input
                            input_elem.clear()
                            input_elem.send_keys(video_path)
                            logging.info(
                                f"Successfully sent file path to input element")
                            found_input = True
                            time.sleep(5)  # Wait for file to be processed
                            break
                        except Exception as e:
                            logging.info(f"Failed to use file input: {e}")
                            continue
            except Exception as e:
                logging.info(f"Error finding file inputs: {e}")

            # Method 2: If no existing inputs worked, try to create one
            if not found_input:
                logging.info("Creating a new file input element")
                try:
                    # Create a new file input element
                    self.driver.execute_script("""
                        var input = document.createElement('input');
                        input.type = 'file';
                        input.style.display = 'block';
                        input.style.position = 'fixed';
                        input.style.top = '0';
                        input.style.left = '0';
                        input.style.zIndex = '9999';
                        input.setAttribute(
                            'accept', '.mp4,video/mp4,video/*,*/*');
                        document.body.appendChild(input);
                    """)

                    # Find the newly created input
                    new_input = self.driver.find_element(
                        By.CSS_SELECTOR, "input[type='file'][style*='position: fixed']")
                    new_input.send_keys(video_path)
                    logging.info("Sent file path to new input element")
                    time.sleep(5)  # Wait for file to be processed
                    found_input = True
                except Exception as e:
                    logging.exception(f"Error creating new file input: {e}")

            # Wait for the file to appear in the dialog
            time.sleep(5)

            return found_input
        except Exception as e:
            logging.exception(f"Error attaching video: {e}")
            return False

    def attach_pdf(self, pdf_path):
        """Attaches a PDF file to the message using various methods.

        Args:
            pdf_path: Full path to the PDF file to attach
        """
        try:
            logging.info(f"Attempting to attach PDF: {pdf_path}")

            # Try to use existing file inputs first
            found_input = False
            file_input = None

            # Method 1: Try to find any file input elements
            try:
                file_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='file']")
                logging.info(f"Found {len(file_inputs)} file input elements")

                if file_inputs:
                    for input_elem in file_inputs:
                        try:
                            # Make each input visible and accept PDFs
                            self.driver.execute_script("""
                                arguments[0].style.display = 'block';
                                arguments[0].style.visibility = 'visible';
                                arguments[0].style.opacity = '1';
                                arguments[0].setAttribute(
                                    'accept', '.pdf,application/pdf,*/*');
                            """, input_elem)

                            # Try to send keys to this input
                            input_elem.clear()
                            input_elem.send_keys(pdf_path)
                            logging.info(
                                f"Successfully sent PDF path to input element")
                            found_input = True
                            time.sleep(5)  # Wait for file to be processed
                            break
                        except Exception as e:
                            logging.info(
                                f"Failed to use file input for PDF: {e}")
                            continue
            except Exception as e:
                logging.info(f"Error finding file inputs for PDF: {e}")

            # Wait for the file to appear in the dialog
            time.sleep(5)

            return found_input
        except Exception as e:
            logging.exception(f"Error attaching PDF: {e}")
            return False

    def click_post_button(self):
        """Clicks the POST button in the file attachment dialog."""
        try:
            logging.info("Attempting to click the POST button...")

            # Try several selectors for the POST button
            post_button_selectors = [
                "//button[@data-testid='dialog-defaultFooter-confirm-button']",
                "//button[contains(@class, 'btn--blue') and .//span[text()='POST']]",
                "//button[.//span[text()='POST']]",
                "//button[contains(@class, 'ant-btn')]//span[text()='POST']/parent::button",
                "//button[contains(text(), 'Post')]"
            ]

            for selector in post_button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                logging.info(
                                    f"Clicking POST button found with selector: {selector}")
                                # Use JavaScript to click the button
                                self.driver.execute_script(
                                    "arguments[0].click();", element)
                                time.sleep(3)  # Wait for post to complete
                                return True
                except Exception as e:
                    logging.info(
                        f"Error with POST button selector {selector}: {e}")
                    continue

            # If direct selectors didn't work, try a more general approach
            try:
                logging.info("Trying more general button approach...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    try:
                        if button.is_displayed() and ("POST" in button.text or "Post" in button.text):
                            logging.info("Found button with POST text")
                            self.driver.execute_script(
                                "arguments[0].click();", button)
                            time.sleep(3)
                            return True
                    except:
                        continue
            except Exception as e:
                logging.info(f"Error with general button approach: {e}")

            logging.error("Could not find the POST button")
            return False

        except Exception as e:
            logging.exception(f"Error clicking POST button: {e}")
            return False

    def close_dialog_after_posting(self):
        """Closes the dialog by clicking the X button after posting a file."""
        try:
            logging.info("Attempting to close the dialog after posting...")

            # Wait a moment for any animations to complete
            time.sleep(2)

            # Try several approaches to find and click the close (X) button
            close_button_selectors = [
                # First try the most specific locators
                "button.ant-modal-close",
                ".ant-modal-close",
                ".ant-modal-close-x",
                # Then try more general close buttons
                "button[class*='close']",
                "span[class*='close']",
                "div[class*='close']",
                "button[aria-label='Close']"
            ]

            for selector in close_button_selectors:
                try:
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                logging.info(
                                    f"Found close button with selector: {selector}")
                                # Try JavaScript click which is more reliable
                                self.driver.execute_script(
                                    "arguments[0].click();", element)
                                time.sleep(2)  # Wait for dialog to close

                                # Verify dialog is closed by checking if we can see message elements
                                try:
                                    self.driver.find_element(
                                        By.CSS_SELECTOR, ".messageContainer")
                                    logging.info(
                                        "Dialog appears to be closed as we can see message container")
                                    return True
                                except:
                                    logging.info(
                                        "Dialog might not be fully closed yet, continuing with other selectors")
                except Exception as e:
                    logging.info(
                        f"Error with close button selector {selector}: {e}")
                    continue

            # If CSS selectors didn't work, try XPath for buttons with X text
            try:
                close_xpath = "//button[contains(text(), 'X') or contains(text(), '×') or @aria-label='Close']"
                elements = self.driver.find_elements(By.XPATH, close_xpath)
                for element in elements:
                    if element.is_displayed():
                        logging.info("Found close button with X text")
                        self.driver.execute_script(
                            "arguments[0].click();", element)
                        time.sleep(2)
                        return True
            except Exception as e:
                logging.info(f"Error with X text button approach: {e}")

            # Attempt to press ESC key as a last resort
            try:
                logging.info("Trying ESC key to close dialog")
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(2)
                return True
            except Exception as e:
                logging.info(f"Error pressing ESC key: {e}")

            # If we reach here, we couldn't close the dialog, but let's not block the flow
            logging.warning(
                "Could not find or click the close button. Will try to continue anyway.")
            return True  # Return True anyway to allow the script to continue

        except Exception as e:
            logging.exception(f"Error closing dialog: {e}")
            # Return True to allow the script to continue even if there was an error
            return True

    def type_in_attachment_dialog(self, client_name, file_type):
        """Types a message in the attachment dialog before posting.

        Args:
            client_name: Name of the client
            file_type: Type of file being attached ("PDF" or "video")
        """
        try:
            # Get client's first name
            first_name = self.get_first_name(client_name)

            # Wait for the dialog to fully appear
            time.sleep(2)

            logging.info("Looking for textarea in the attachment dialog...")

            # Try to find the textarea in the dialog
            textarea = None

            # Very specific selector for the popup dialog textarea
            dialog_textarea_selectors = [
                ".ant-input.m16b[placeholder='Type your message']",
                "textarea.ant-input.m16b",
                "textarea[placeholder='Type your message']",
                "textarea.ant-input",
                "textarea"
            ]

            for selector in dialog_textarea_selectors:
                try:
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    logging.info(
                        f"Found {len(elements)} elements with selector {selector}")
                    for element in elements:
                        try:
                            if element.is_displayed():
                                textarea = element
                                logging.info(
                                    f"Found visible dialog textarea with selector: {selector}")
                                break
                        except:
                            continue
                    if textarea:
                        break
                except Exception as e:
                    logging.info(
                        f"Error with dialog textarea selector {selector}: {e}")
                    continue

            if not textarea:
                logging.error("Could not find dialog textarea")
                return False

            # Use a single standardized message regardless of file type
            message = f"Hey {first_name} heres your check in video and review for the week! Awesome work!"

            # Try both methods of typing
            try:
                textarea.clear()
                textarea.send_keys(message)
                logging.info(f"Typed in attachment dialog: {message}")
            except Exception as e:
                logging.info(f"Error typing in dialog with send_keys: {e}")
                try:
                    self.driver.execute_script(
                        f"arguments[0].value = '{message}';", textarea)
                    logging.info("Typed in dialog using JavaScript")
                except Exception as e:
                    logging.info(
                        f"Error typing in dialog with JavaScript: {e}")
                    return False

            time.sleep(1)  # Wait a moment after typing
            return True

        except Exception as e:
            logging.exception(f"Error typing in attachment dialog: {e}")
            return False

    def send_initial_message(self, client_name):
        """Sends a simple initial message to a client to establish the conversation.

        Args:
            client_name: Name of the client

        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            logging.info(f"Sending initial message to {client_name}...")

            # Wait for the conversation to fully load
            time.sleep(5)  # Increased wait time

            # Look for the message input area using multiple approaches
            # First try to find contenteditable divs which are common for modern chat interfaces
            contenteditable_selectors = [
                "[role='textbox']",
                "[contenteditable='true']",
                ".public-DraftEditor-content",
                "[aria-label*='message']",
                "[aria-label*='Type']",
                ".ql-editor"
            ]

            # Regular input selectors as fallback
            input_selectors = [
                ".messageComposer__wrapper",
                ".DraftEditor-root",
                ".public-DraftEditor-content[contenteditable='true']",
                "[aria-describedby='placeholder-fg30t']",
                "[role='combobox'][contenteditable='true']",
                "textarea",
                "input[type='text']"
            ]

            # Try contenteditable elements first
            message_input = None
            logging.info("Looking for contenteditable message input...")
            for selector in contenteditable_selectors:
                try:
                    elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            message_input = element
                            logging.info(
                                f"Found contenteditable message input with selector: {selector}")
                            break
                    if message_input:
                        break
                except Exception as e:
                    continue

            # If no contenteditable found, try regular inputs
            if not message_input:
                logging.info("Looking for regular message input elements...")
                for selector in input_selectors:
                    try:
                        elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                message_input = element
                                logging.info(
                                    f"Found message input with selector: {selector}")
                                break
                        if message_input:
                            break
                    except Exception as e:
                        continue

            if not message_input:
                logging.error("Could not find any message input field")
                # Take a screenshot to help diagnose the problem
                try:
                    screenshot_path = f"conversation_screen_{client_name.replace(' ', '_')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logging.info(f"Saved screenshot to {screenshot_path}")
                except:
                    pass
                return False

            # First click to focus the element
            try:
                # Use actions for more reliable clicking
                actions = ActionChains(self.driver)
                actions.move_to_element(message_input).click().perform()
                logging.info("Clicked on message input to focus it")
                time.sleep(1)
            except Exception as e:
                logging.info(f"Error focusing with ActionChains: {e}")
                try:
                    # Fallback to JavaScript click
                    self.driver.execute_script(
                        "arguments[0].click();", message_input)
                    logging.info("Clicked message input using JavaScript")
                    time.sleep(1)
                except Exception as e:
                    logging.info(f"Error focusing with JavaScript: {e}")

            # Now try multiple methods to type the simple smiley message
            smiley_sent = False
            message = ":)"

            # Method 1: ActionChains to simulate typing
            try:
                actions = ActionChains(self.driver)
                actions.send_keys(message).perform()
                logging.info("Typed smiley using ActionChains")
                time.sleep(1)
                smiley_sent = True
            except Exception as e:
                logging.info(f"ActionChains typing failed: {e}")

            # Method 2: JavaScript to set content (if method 1 failed)
            if not smiley_sent:
                try:
                    # For contenteditable divs
                    if message_input.get_attribute("contenteditable") == "true":
                        self.driver.execute_script(
                            "arguments[0].textContent = arguments[1];", message_input, message)
                    # For inputs/textareas
                    else:
                        self.driver.execute_script(
                            "arguments[0].value = arguments[1];", message_input, message)
                    logging.info("Set message content using JavaScript")
                    time.sleep(1)
                    smiley_sent = True
                except Exception as e:
                    logging.info(f"JavaScript content setting failed: {e}")

            # Method 3: send_keys directly (if other methods failed)
            if not smiley_sent:
                try:
                    message_input.clear()
                    message_input.send_keys(message)
                    logging.info("Typed message using direct send_keys")
                    time.sleep(1)
                    smiley_sent = True
                except Exception as e:
                    logging.info(f"Direct send_keys failed: {e}")

            if not smiley_sent:
                logging.error("Failed to type message using all methods")
                return False

            # Now try multiple send methods

            # Method 1: Press Enter key with ActionChains
            try:
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.RETURN).perform()
                logging.info("Pressed Enter using ActionChains")
                time.sleep(2)
            except Exception as e:
                logging.info(f"Enter key with ActionChains failed: {e}")

                # Method 2: Press Enter key directly on the element
                try:
                    message_input.send_keys(Keys.RETURN)
                    logging.info("Pressed Enter directly on element")
                    time.sleep(2)
                except Exception as e:
                    logging.info(f"Direct Enter key failed: {e}")

                    # Method 3: Look for send button
                    try:
                        send_buttons = self.find_send_button()
                        if send_buttons:
                            self.driver.execute_script(
                                "arguments[0].click();", send_buttons)
                            logging.info("Clicked send button")
                            time.sleep(2)
                        else:
                            logging.error("Could not find send button")
                            return False
                    except Exception as e:
                        logging.info(f"Send button click failed: {e}")
                        return False

            # Wait for the message to be sent
            time.sleep(3)

            # Check if message appears in the conversation
            try:
                message_elements = self.driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{message}')]")
                if message_elements:
                    for element in message_elements:
                        if element.is_displayed():
                            logging.info(
                                "Verified message appears in the conversation")
                            break
            except:
                logging.warning(
                    "Could not verify if message appears in conversation")

            # Return to the inbox by clicking the back button
            try:
                back_button_locator = (
                    By.XPATH, "//button[contains(@class, 'back') or contains(@aria-label, 'back')]")
                back_button = self.wait.until(
                    EC.element_to_be_clickable(back_button_locator))
                self.driver.execute_script(
                    "arguments[0].click();", back_button)
                logging.info("Clicked back button to return to inbox")
                time.sleep(2)
                return True
            except Exception as e:
                logging.error(f"Error clicking back button: {e}")
                # Try clicking the X button if back button fails
                try:
                    x_buttons = self.driver.find_elements(
                        By.XPATH, "//button[contains(@class, 'close') or @aria-label='Close' or contains(text(), 'X') or contains(text(), '×')]")
                    for button in x_buttons:
                        if button.is_displayed():
                            self.driver.execute_script(
                                "arguments[0].click();", button)
                            logging.info("Clicked X button to return to inbox")
                            time.sleep(2)
                            return True
                except Exception as e2:
                    logging.error(f"Error clicking X button: {e2}")

                # Try clicking messages in the navigation as a last resort
                try:
                    self.click_messages()
                    logging.info(
                        "Clicked messages in navigation to return to inbox")
                    time.sleep(2)
                    return True
                except:
                    logging.error("Failed all methods to return to inbox")
                    return False

        except Exception as e:
            logging.exception(
                f"Error sending initial message to {client_name}: {e}")
            return False

    def find_send_button(self):
        """Find and return the send button in the conversation."""
        try:
            # Try various selectors for send buttons
            send_selectors = [
                "button[type='submit']",
                "button.send-button",
                "button[aria-label*='Send']",
                "button.ant-btn-primary",
                "//button[contains(@class, 'send')]",
                "//button[contains(text(), 'Send')]",
                "//span[contains(text(), 'Send')]/parent::button",
                "//button[contains(@class, 'ant-btn')][.//span[text()='Send']]"
            ]

            for selector in send_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(
                            By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed():
                            logging.info(
                                f"Found send button with selector: {selector}")
                            return element
                except:
                    continue

            return None
        except Exception as e:
            logging.info(f"Error finding send button: {e}")
            return None

    def refresh_messages_page(self):
        """Refreshes the messages page by navigating to Overview and then back to Messages."""
        try:
            logging.info(
                "Refreshing messages by navigating to Overview and back...")

            # Step 1: Click on the Overview link to navigate away from messages
            try:
                logging.info("Clicking on Overview link in navigation...")
                overview_link_locator = (By.ID, "nav_overview")
                overview_link = self.wait.until(
                    EC.element_to_be_clickable(overview_link_locator))
                self.driver.execute_script(
                    "arguments[0].click();", overview_link)
                logging.info("Successfully clicked on Overview link")
                time.sleep(3)  # Wait for Overview page to load
            except Exception as e:
                logging.warning(
                    f"Error clicking Overview link: {e}. Trying alternate approach.")
                try:
                    # Try alternative selector
                    overview_xpath = "//a[@title='Overview' or contains(@class, 'leftNavItem')]"
                    overview_link = self.driver.find_element(
                        By.XPATH, overview_xpath)
                    self.driver.execute_script(
                        "arguments[0].click();", overview_link)
                    logging.info(
                        "Successfully clicked on Overview link using alternative selector")
                    time.sleep(3)
                except Exception as e:
                    logging.error(f"Failed to click on Overview link: {e}")
                    return False

            # Step 2: Click on Messages link to navigate back to messages
            logging.info("Clicking on Messages link to return to messages...")
            if self.click_messages():
                logging.info(
                    "Successfully refreshed messages by navigating out and back")
                time.sleep(3)  # Wait for messages to load
                return True
            else:
                logging.error(
                    "Failed to click Messages link when trying to return to messages")
                return False

        except Exception as e:
            logging.exception(f"Error refreshing messages page: {e}")
            return False

    def cleanup(self):
        """Cleans up resources (removes temp dir and closes driver)."""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'):
                logging.info("Closing webdriver...")
                try:
                    self.driver.close()
                except (WebDriverException, InvalidSessionIdException) as e:
                    logging.warning(
                        f"Error closing current window during cleanup: {e}")
                try:
                    self.driver.quit()
                except (WebDriverException, InvalidSessionIdException) as e:
                    logging.warning(
                        f"Error quitting webdriver during cleanup: {e}")
                logging.info("Webdriver closed.")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                logging.info(
                    f"Removing temp user data directory: {self.temp_user_data_dir}")
                shutil.rmtree(self.temp_user_data_dir)
                logging.info("Temp directory removed.")
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.exception(f"Error during cleanup: {e}")


# Entry point
if __name__ == "__main__":
    # Only the 3 clients missing Trainerize integration
    client_names = [
        "Alice Forster",
        "Anna Somogyi",
        "Claire Ruberu"
    ]

    # Login credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    # Create TrainerizeAutomation instance
    automation = TrainerizeAutomation()

    try:
        # Login
        if not automation.login(username, password):
            print("Login failed! Exiting.")
            automation.cleanup()
            exit(1)

        print("Login successful!")
        automation.handle_notification_popup()

        # The original script navigated to Messages. This behavior will change
        # as we now need to navigate to client schedules, not DMs.
        # The 'add_video_link_to_schedule' method will eventually handle
        # the necessary navigation to the client's schedule area.
        # print("Skipping direct navigation to Messages section for new workflow.")

        # Process each client
        for i, target_client in enumerate(client_names, 1):
            print(f"\n{'-' * 50}")
            print(
                f"Processing client {i}/{len(client_names)}: {target_client}")
            print(f"{'-' * 50}")

            try:
                video_path = automation.get_video_path(target_client)
                if not os.path.exists(video_path):
                    print(
                        f"No video file found for {target_client} at {video_path}. Skipping.")
                    logging.warning(
                        f"No video file found for {target_client} at {video_path}. Skipping.")
                    continue

                print(f"Found video: {video_path}")

                # Step 1: Upload video to YouTube
                print(
                    f"Uploading video for {target_client} to YouTube (placeholder)...")
                youtube_url = automation.upload_to_youtube(
                    video_path, target_client)

                if not youtube_url:
                    print(
                        f"Failed to upload video to YouTube for {target_client}. Skipping.")
                    logging.error(
                        f"Failed to upload video to YouTube for {target_client}. Skipping.")
                    continue

                print(
                    f"Video uploaded for {target_client} (placeholder URL): {youtube_url}")

                # Step 2: Add YouTube link to client's schedule in Trainerize
                first_name = automation.get_first_name(target_client)
                # The youtube_url is already part of the message in the updated logic below
                message_for_schedule = f"Hey {first_name}, here's your weekly check-in video! You can watch it here: {youtube_url}"
                print(
                    f"Adding video link to {target_client}'s schedule (placeholder)...")

                if automation.add_video_link_to_schedule(target_client, youtube_url, message_for_schedule):
                    print(
                        f"Successfully added video link to {target_client}'s schedule (placeholder).")
                else:
                    print(
                        f"Failed to add video link to {target_client}'s schedule (placeholder).")

                # The old logic for DMing files (video and PDF), including navigating within the
                # messages section, sending initial messages, attaching files, typing DM messages,
                # and navigating back to the messages list, has been removed from this loop.
                # The `add_video_link_to_schedule` method will be responsible for all
                # necessary navigation and actions to post the message to the client's schedule.

            except Exception as e:
                print(f"Error processing client {target_client}: {e}")
                logging.exception(
                    f"Error processing client {target_client}: {e}")
                print("Attempting to recover for next client...")
                # Future recovery logic might navigate to a main dashboard or client list
                # to ensure the script can continue with the next client.

        print("\nAll clients processed. Cleaning up...")

    except Exception as e:
        print(f"Error during execution: {e}")
        logging.exception(f"Global error during execution: {e}")

    finally:
        # Always clean up resources
        automation.cleanup()
        print("Script execution complete.")
