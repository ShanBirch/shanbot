import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import shutil
import tempfile
import os
import argparse

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class TrainerizeScheduler:
    def __init__(self, chrome_binary_path=None):
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
        if chrome_binary_path:
            chrome_options.binary_location = chrome_binary_path
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def cleanup(self):
        try:
            if hasattr(self, 'driver'):
                self.driver.close()
                self.driver.quit()
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def handle_cookie_dialog(self):
        try:
            # Try to find and click the Accept/Close button for OneTrust cookie dialog
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "onetrust-group-container")))
            # Try several possible button texts
            button_selectors = [
                (By.ID, "onetrust-accept-btn-handler"),
                (By.CSS_SELECTOR, "button[aria-label='Accept All Cookies']"),
                (By.XPATH, "//button[contains(text(), 'Accept')]"),
                (By.XPATH, "//button[contains(text(), 'Got it')]"),
                (By.XPATH, "//button[contains(text(), 'Close')]"),
            ]
            for by, selector in button_selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        time.sleep(1)
                        return True
                except Exception:
                    continue
            # If not found, try to hide the dialog with JS
            self.driver.execute_script(
                "document.getElementById('onetrust-group-container').style.display='none';")
            time.sleep(0.5)
            return True
        except Exception:
            # If not present, just continue
            return False

    def login(self, username, password):
        try:
            self.driver.get("https://www.trainerize.com/login.aspx")
            time.sleep(2)
            self.handle_cookie_dialog()
            self.wait.until(EC.presence_of_element_located((By.ID, "t_email")))
            email_field = self.driver.find_element(By.ID, "t_email")
            email_field.send_keys(username)
            find_me_button = self.driver.find_element(
                By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(2)
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "emailInput")))
            email_field_second = self.driver.find_element(By.ID, "emailInput")
            email_field_second.send_keys(username)
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.send_keys(password)
            sign_in_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def navigate_to_client(self, client_name):
        try:
            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            clients_link = self.wait.until(
                EC.element_to_be_clickable(clients_link_locator))
            clients_link.click()
            time.sleep(2)
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            search_input.clear()
            search_input.send_keys(client_name)
            time.sleep(2)
            client_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//a[contains(., '{client_name.split()[0]}')]")))
            client_link.click()
            time.sleep(2)
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(
                EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            self.driver.refresh()
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f"Error navigating to client: {e}")
            return False

    def schedule_workouts_and_cardio(self):
        import traceback
        try:
            logging.info("Starting to schedule workouts and cardio...")
            workout_schedule = [
                ("Chest Day", "Monday"),
                ("Back Day", "Tuesday"),
                ("Shoulder Day", "Wednesday"),
                ("Leg Day", "Thursday"),
                ("Core Day", "Friday"),
            ]
            cardio_days = ["Monday", "Wednesday", "Friday", "Sunday"]
            cardio_activity = "Walking"
            repeat_weeks = "6"

            def click_sidebar_tab_calendar():
                try:
                    calendar_tab = None
                    try:
                        calendar_tab = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#nav_calendar[data-testid='leftNavMenu-item-calendar']")))
                    except Exception:
                        calendar_tab = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[.//svg[@name='outline/calendar/calendar-regular']]")))
                    if calendar_tab:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", calendar_tab)
                        time.sleep(0.5)
                        try:
                            calendar_tab.click()
                        except Exception:
                            self.driver.execute_script(
                                "arguments[0].click();", calendar_tab)
                        time.sleep(1)
                        logging.info("Clicked Calendar tab in sidebar.")
                        return True
                    else:
                        logging.error("Calendar tab not found in sidebar.")
                        return False
                except Exception as e:
                    logging.error(f"Could not click sidebar tab Calendar: {e}")
                    return False
            click_sidebar_tab_calendar()
            for workout_name, day_title in workout_schedule:
                try:
                    logging.info(
                        f"Scheduling workout: {workout_name} on {day_title}")
                    schedule_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
                    )))
                    schedule_btn.click()
                    time.sleep(1)
                    workout_menu = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//li[@data-testid='dropdownButton-menuItem-workout']"
                    )))
                    workout_menu.click()
                    time.sleep(1)
                    select_current_program = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//p[contains(@class, 'color--black') and text()='Select from current training program']"
                    )))
                    select_current_program.click()
                    time.sleep(0.5)
                    try:
                        logging.info(
                            "[STEP] Waiting for workout input to be clickable...")
                        try:
                            workout_input = self.wait.until(EC.element_to_be_clickable((
                                By.XPATH, "//div[contains(@class, 'ant-select-selection__placeholder') and contains(text(), 'Type in workout name')]"
                            )))
                            logging.info(
                                "[SUCCESS] Workout input is clickable.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Workout input not clickable: {e}")
                            self.driver.save_screenshot(
                                'fail_workout_input_clickable.png')
                            with open('fail_workout_input_clickable.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        logging.info("[STEP] Clicking workout input...")
                        try:
                            workout_input.click()
                            logging.info("[SUCCESS] Clicked workout input.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Could not click workout input: {e}")
                            self.driver.save_screenshot(
                                'fail_workout_input_click.png')
                            with open('fail_workout_input_click.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        logging.info(
                            "[STEP] Waiting for input box to be present (ant-select-search__field)...")
                        try:
                            input_box = self.wait.until(EC.presence_of_element_located((
                                By.XPATH, "//input[contains(@class, 'ant-select-search__field')]"
                            )))
                            logging.info(
                                "[SUCCESS] Input box (ant-select-search__field) is present.")
                        except Exception as e:
                            logging.error(
                                f"[FAIL] Input box (ant-select-search__field) not present: {e}")
                            self.driver.save_screenshot(
                                'fail_input_box_present.png')
                            with open('fail_input_box_present.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise
                        # Try normal send_keys
                        logging.info(
                            f"[STEP] Trying input_box.send_keys({workout_name})...")
                        try:
                            input_box.clear()
                            input_box.send_keys(workout_name)
                            time.sleep(0.5)
                            value_after_typing = input_box.get_attribute(
                                'value')
                            logging.info(
                                f"[RESULT] Input box value after send_keys: '{value_after_typing}'")
                        except Exception as e:
                            logging.error(f"[FAIL] send_keys failed: {e}")
                        if value_after_typing.strip().lower() != workout_name.strip().lower():
                            # Try JavaScript set value
                            logging.info(
                                "[STEP] Trying JavaScript value set...")
                            try:
                                self.driver.execute_script(
                                    "arguments[0].value = arguments[1];", input_box, workout_name)
                                time.sleep(0.5)
                                value_after_js = input_box.get_attribute(
                                    'value')
                                logging.info(
                                    f"[RESULT] Input box value after JS set: '{value_after_js}'")
                            except Exception as e:
                                logging.error(
                                    f"[FAIL] JS set value failed: {e}")
                            if value_after_js.strip().lower() != workout_name.strip().lower():
                                # Try click+send_keys again
                                logging.info(
                                    "[STEP] Trying click+send_keys again...")
                                try:
                                    input_box.click()
                                    input_box.send_keys(workout_name)
                                    time.sleep(0.5)
                                    value_after_click = input_box.get_attribute(
                                        'value')
                                    logging.info(
                                        f"[RESULT] Input box value after click+send_keys: '{value_after_click}'")
                                except Exception as e:
                                    logging.error(
                                        f"[FAIL] click+send_keys failed: {e}")
                                if value_after_click.strip().lower() != workout_name.strip().lower():
                                    # Try character by character
                                    logging.info(
                                        "[STEP] Trying character-by-character typing...")
                                    try:
                                        input_box.clear()
                                        for char in workout_name:
                                            input_box.send_keys(char)
                                            time.sleep(0.1)
                                        value_after_chars = input_box.get_attribute(
                                            'value')
                                        logging.info(
                                            f"[RESULT] Input box value after char-by-char: '{value_after_chars}'")
                                    except Exception as e:
                                        logging.error(
                                            f"[FAIL] char-by-char typing failed: {e}")
                                    if value_after_chars.strip().lower() != workout_name.strip().lower():
                                        logging.info(
                                            "[STEP] All typing methods failed, trying to click workout name in dropdown...")
                                        try:
                                            workout_options = self.driver.find_elements(
                                                By.XPATH, "//p[contains(@class, 'tz-lp') and contains(@data-testid, 'workoutGrid-workoutName')]")
                                            logging.info(
                                                f"[RESULT] Found {len(workout_options)} workout options in dropdown.")
                                            for idx, opt in enumerate(workout_options):
                                                logging.info(
                                                    f"[RESULT] Option {idx}: '{opt.text}' (data-testid: {opt.get_attribute('data-testid')})")
                                            workout_option = self.wait.until(EC.element_to_be_clickable((
                                                By.XPATH, f"//p[contains(@class, 'tz-lp') and contains(text(), '{workout_name}')]")
                                            ))
                                            workout_option.click()
                                            logging.info(
                                                f"[SUCCESS] Clicked workout option '{workout_name}' in dropdown.")
                                        except Exception as click_e:
                                            logging.error(
                                                f"[FAIL] Failed to click workout option '{workout_name}': {click_e}")
                                            try:
                                                dropdown_html = self.driver.find_element(
                                                    By.XPATH, "//div[contains(@class, 'ant-select-dropdown')]//div").get_attribute('outerHTML')
                                                logging.error(
                                                    f"[FAIL] Dropdown HTML: {dropdown_html}")
                                            except Exception as html_e:
                                                logging.error(
                                                    f"[FAIL] Could not get dropdown HTML: {html_e}")
                                            self.driver.save_screenshot(
                                                'fail_dropdown_click.png')
                                            with open('fail_dropdown_click.html', 'w', encoding='utf-8') as f:
                                                f.write(
                                                    self.driver.page_source)
                                            raise Exception(
                                                "All typing and clicking methods failed!")
                        try:
                            input_box.send_keys(Keys.ENTER)
                            logging.info(
                                "[STEP] Pressed Enter after typing workout name.")
                            time.sleep(1)
                        except Exception as e:
                            logging.error(f"[FAIL] Pressing Enter failed: {e}")
                    except Exception as e:
                        logging.error(
                            f"[FAIL] Failed to type in workout name: {e}")
                        self.driver.save_screenshot('workout_input_error.png')
                        with open('workout_input_error.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        raise
                    add_activity = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//h2[contains(text(), 'Add Activity')]"
                    )))
                    add_activity.click()
                    time.sleep(1)
                    repeat_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
                    )))
                    repeat_btn.click()
                    time.sleep(1)
                    day_btn = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{day_title}']"
                    )))
                    day_btn.click()
                    time.sleep(0.5)
                    repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
                    )))
                    repeat_dropdown.click()
                    week_option = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//li[@data-testid='repeatDialog-weeklyRepeatFor-option-{repeat_weeks}']"
                    )))
                    week_option.click()
                    time.sleep(0.5)
                    apply_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
                    )))
                    apply_btn.click()
                    time.sleep(1)
                    add_btn = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
                    )))
                    add_btn.click()
                    time.sleep(2)
                except Exception as e:
                    logging.error(
                        f"Error scheduling workout {workout_name}: {e}\n{traceback.format_exc()}")
            # Only schedule cardio once, with all repeat days selected
            repeat_days = ["Monday", "Tuesday", "Wednesday",
                           "Thursday", "Friday", "Saturday", "Sunday"]
            logging.info(
                f"Scheduling cardio: {cardio_activity} on {', '.join(repeat_days)}")
            logging.info(
                "[CARDIO] Checking for modal overlays before clicking schedule button...")
            # Try to close modal overlays if present
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[CARDIO] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[CARDIO] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[CARDIO] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[CARDIO] No modal overlay detected.")
            logging.info("[CARDIO] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for cardio menu...")
            cardio_menu = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[.//p[text()='Cardio']]"
            )))
            cardio_menu.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for activity dropdown...")
            activity_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div.ant-select-selection__rendered"
            )))
            activity_dropdown.click()
            logging.info("[CARDIO] Waiting for walking option...")
            walking_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[contains(@data-testid, 'activity-cardio-activitySelectOption-walking')]"
            )))
            walking_option.click()
            time.sleep(0.5)
            # Skip time selection, go straight to custom target
            logging.info("[CARDIO] Clicking <span>Add my own target</span>...")
            add_own_target_span = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//span[text()='Add my own target']"
            )))
            add_own_target_span.click()
            logging.info("[CARDIO] Clicked <span>Add my own target</span>.")
            target_input = self.wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "input[data-testid='multipleActivitiesDialog-activity-cardio-target-textInput']"
            )))
            target_input.clear()
            target_input.send_keys("10,000 Steps")
            logging.info(
                "[CARDIO] Typed '10,000 Steps' into custom target input.")
            time.sleep(0.5)
            logging.info("[CARDIO] Waiting for add activity header...")
            add_activity = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//h2[contains(text(), 'Add Activity')]"
            )))
            add_activity.click()
            time.sleep(1)
            logging.info("[CARDIO] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            for repeat_day in repeat_days:
                try:
                    logging.info(
                        f"[CARDIO] Selecting repeat day: {repeat_day}")
                    day_btn = self.wait.until(EC.element_to_be_clickable((
                        By.XPATH, f"//button[@data-testid and @title='{repeat_day}']"
                    )))
                    day_btn.click()
                except Exception as e:
                    logging.error(
                        f"[CARDIO][FAIL] Could not select repeat day {repeat_day}: {e}")
            time.sleep(0.5)
            # Set repeat weeks to 6
            logging.info("[CARDIO] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[CARDIO] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[CARDIO] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            # Ensure Apply and Add are clicked
            logging.info("[CARDIO] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[CARDIO] Clicked apply button.")
            time.sleep(1)
            logging.info("[CARDIO] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[CARDIO] Clicked add button.")
            time.sleep(2)
            logging.info("Finished scheduling workouts and cardio.")
            time.sleep(30)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_workouts_and_cardio: {e}\n{traceback.format_exc()}")
            return False

    def schedule_body_stats(self):
        import traceback
        try:
            logging.info(
                "Scheduling Body stats on Monday, repeat for 6 weeks.")
            logging.info(
                "[BODY STATS] Checking for modal overlays before clicking schedule button...")
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[BODY STATS] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[BODY STATS] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[BODY STATS] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[BODY STATS] No modal overlay detected.")
            logging.info("[BODY STATS] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            # Click <p class="tz-p">Body stats</p>
            logging.info("[BODY STATS] Clicking Body stats <p> element...")
            body_stats_p = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//p[contains(@class, 'tz-p') and text()='Body stats']"
            )))
            body_stats_p.click()
            logging.info("[BODY STATS] Clicked Body stats <p> element.")
            time.sleep(0.5)
            # Set up repeat
            logging.info("[BODY STATS] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            logging.info("[BODY STATS] Selecting repeat day: Monday")
            day_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@data-testid and @title='Monday']"
            )))
            day_btn.click()
            time.sleep(0.5)
            logging.info("[BODY STATS] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[BODY STATS] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[BODY STATS] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            logging.info("[BODY STATS] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[BODY STATS] Clicked apply button.")
            time.sleep(1)
            logging.info("[BODY STATS] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[BODY STATS] Clicked add button.")
            time.sleep(15)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_body_stats: {e}\n{traceback.format_exc()}")
            return False

    def schedule_progress_photos(self):
        import traceback
        try:
            logging.info(
                "Scheduling Progress Photos on Monday, repeat for 6 weeks.")
            logging.info(
                "[PHOTOS] Checking for modal overlays before clicking schedule button...")
            try:
                modal = self.driver.find_element(
                    By.CSS_SELECTOR, ".modal-wrap, .ant-modal")
                if modal.is_displayed():
                    logging.info(
                        "[PHOTOS] Modal overlay detected. Attempting to close it...")
                    close_btn = None
                    try:
                        close_btn = modal.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Close'], button.ant-modal-close, span.ant-modal-close-x, svg")
                    except Exception:
                        pass
                    if close_btn and close_btn.is_displayed():
                        close_btn.click()
                        logging.info("[PHOTOS] Modal overlay closed.")
                    else:
                        modal.click()
                        logging.info(
                            "[PHOTOS] Clicked modal overlay to close.")
                    time.sleep(1)
            except Exception:
                logging.info("[PHOTOS] No modal overlay detected.")
            logging.info("[PHOTOS] Waiting for schedule button...")
            schedule_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='masterProgram-scheduleButton']"
            )))
            schedule_btn.click()
            time.sleep(1)
            # Click <p class="tz-p">Photos</p>
            logging.info("[PHOTOS] Clicking Photos <p> element...")
            photos_p = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//p[contains(@class, 'tz-p') and text()='Photos']"
            )))
            photos_p.click()
            logging.info("[PHOTOS] Clicked Photos <p> element.")
            time.sleep(0.5)
            # Set up repeat
            logging.info("[PHOTOS] Waiting for repeat button...")
            repeat_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "p[data-testid='multipleActivitiesDialog-dateSelect-repeat-setupButton']"
            )))
            repeat_btn.click()
            time.sleep(1)
            logging.info("[PHOTOS] Selecting repeat day: Monday")
            day_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[@data-testid and @title='Monday']"
            )))
            day_btn.click()
            time.sleep(0.5)
            logging.info("[PHOTOS] Waiting for repeat weeks dropdown...")
            repeat_dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "div[data-testid='repeatDialog-weeklyRepeatFor-select']"
            )))
            repeat_dropdown.click()
            logging.info("[PHOTOS] Clicked repeat weeks dropdown.")
            week_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, "//li[@data-testid='repeatDialog-weeklyRepeatFor-option-6']"
            )))
            week_option.click()
            logging.info("[PHOTOS] Selected 6 weeks repeat option.")
            time.sleep(0.5)
            logging.info("[PHOTOS] Waiting for apply button...")
            apply_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='dialog-defaultFooter-confirm-button']"
            )))
            apply_btn.click()
            logging.info("[PHOTOS] Clicked apply button.")
            time.sleep(1)
            logging.info("[PHOTOS] Waiting for add button...")
            add_btn = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, "button[data-testid='multipleActivitiesDialog-saveButton']"
            )))
            add_btn.click()
            logging.info("[PHOTOS] Clicked add button.")
            time.sleep(15)
            return True
        except Exception as e:
            logging.error(
                f"Error in schedule_progress_photos: {e}\n{traceback.format_exc()}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Trainerize Scheduling Test Script")
    parser.add_argument('--username', type=str,
                        default="Shannonbirch@cocospersonaltraining.com", help='Coach email/username')
    parser.add_argument('--password', type=str,
                        default="cyywp7nyk2", help='Coach password')
    parser.add_argument('--client_name', type=str,
                        default="Shannon Birch", help='Client name to schedule for')
    parser.add_argument('--chrome_binary_path', type=str,
                        default=r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\chrome-win64\\chrome.exe", help='Path to Chrome binary')
    parser.add_argument('--close-on-finish', action='store_true',
                        help='Close browser when finished (default: False)')
    args = parser.parse_args()

    scheduler = TrainerizeScheduler(chrome_binary_path=args.chrome_binary_path)
    try:
        if scheduler.login(args.username, args.password):
            if scheduler.navigate_to_client(args.client_name):
                scheduler.schedule_workouts_and_cardio()
                scheduler.schedule_body_stats()
                scheduler.schedule_progress_photos()
    finally:
        # Commented out to keep browser open on failure for debugging
        # if args.close_on_finish:
        #     scheduler.cleanup()
        pass


if __name__ == "__main__":
    main()
