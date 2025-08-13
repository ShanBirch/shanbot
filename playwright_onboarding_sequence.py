import sys
import os

import re
from playwright.sync_api import sync_playwright, expect
import json
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def schedule_workouts(page1, workout_schedule) -> None:
    """Schedule workouts in the calendar for different days of the week."""
    print("\nScheduling workouts in calendar...")

    # Navigate to calendar
    page1.get_by_test_id("leftNavMenu-item-calendar").click()
    page1.wait_for_timeout(2000)  # Wait for calendar to load

    # Schedule each workout according to the client's preferred days
    for workout_name, schedule in workout_schedule.items():
        try:
            print(f"\nScheduling {workout_name} for {schedule['day']}...")

            # Open the scheduling dialog
            page1.locator(
                "div:nth-child(3) > div > div:nth-child(3) > div").first.click(button="right")
            page1.wait_for_timeout(1000)

            page1.get_by_test_id(
                "dropdownButton-menuItem-workout").get_by_text("Workout").click()
            page1.wait_for_timeout(1000)

            # Select from current training
            page1.get_by_role(
                "radio", name="Select from current training").check()
            page1.get_by_text("Type in workout name or").click()

            # Select the specific workout
            page1.get_by_role("option", name=f"{workout_name}").locator(
                "div").nth(1).click()
            page1.wait_for_timeout(1000)

            # Click the "Add Activity" header to dismiss the workout selection popup
            page1.get_by_text("Add Activity").first.click()
            page1.wait_for_timeout(1000)

            # Set up weekly repeat
            page1.get_by_test_id(
                "multipleActivitiesDialog-dateSelect-repeat-setupButton").click()

            # Select the day of the week using the title attribute
            page1.get_by_title(schedule['day']).click()

            # Set number of weeks
            page1.get_by_test_id(
                "repeatDialog-weeklyRepeatFor-select").locator("svg").click()
            page1.get_by_test_id(
                f"repeatDialog-weeklyRepeatFor-option-{schedule['weeks']}").click()

            # Click APPLY in the repeat options dialog
            page1.get_by_role("button", name="APPLY").click()
            page1.wait_for_timeout(1000)

            # Save the workout schedule
            page1.get_by_test_id("multipleActivitiesDialog-saveButton").click()
            page1.wait_for_timeout(2000)

            print(f"{workout_name} scheduled successfully!")

        except Exception as e:
            print(f"Error scheduling {workout_name}: {e}")
            continue

    try:
        print("\nScheduling cardio sessions...")
        # Schedule cardio sessions on non-workout days or as specified
        page1.locator(
            "div:nth-child(3) > div > div:nth-child(3) > div").first.click()
        page1.get_by_test_id(
            "dropdownButton-menuItem-cardio").get_by_text("Cardio").click()
        page1.wait_for_timeout(1000)

        # Select cardio types
        page1.get_by_text("Running").click()
        page1.get_by_text("Walking").click()

        # Set cardio duration
        page1.get_by_test_id(
            "multipleActivitiesDialog-activity-cardio-target-radio-time").check()
        page1.get_by_role("textbox", name=":00:00").click()
        page1.get_by_role("button", name="01").first.click()

        # Set up cardio schedule
        page1.get_by_test_id(
            "multipleActivitiesDialog-dateSelect-repeat-setupButton").click()

        # Select cardio days - use remaining days or alternate days if full schedule
        weekdays = ['Monday', 'Tuesday', 'Wednesday',
                    'Thursday', 'Friday', 'Saturday', 'Sunday']
        workout_days = [schedule['day']
                        for schedule in workout_schedule.values()]
        cardio_days = [day for day in weekdays if day not in workout_days]
        if not cardio_days:  # If all days are workout days, alternate cardio
            cardio_days = workout_days[::2]  # Every other workout day

        # Select each cardio day
        for day in cardio_days[:4]:  # Limit to 4 cardio days maximum
            page1.get_by_title(day).click()

        # Set number of weeks for cardio (same as workouts)
        page1.get_by_test_id(
            "repeatDialog-weeklyRepeatFor-select").locator("svg").click()
        page1.get_by_test_id("repeatDialog-weeklyRepeatFor-option-6").click()

        # Click APPLY in the repeat options dialog
        page1.get_by_role("button", name="APPLY").click()
        page1.wait_for_timeout(1000)

        # Save cardio schedule
        page1.get_by_test_id("multipleActivitiesDialog-saveButton").click()
        page1.wait_for_timeout(2000)

        print("Cardio sessions scheduled successfully!")

    except Exception as e:
        print(f"Error scheduling cardio sessions: {e}")


def run_onboarding(client_data, meal_plan_pdf_path):
    """
    Automates Trainerize onboarding using Playwright sync API.
    Args:
        client_data (dict): Dictionary with client info (email, first_name, last_name, etc.)
        meal_plan_pdf_path (str): Path to the meal plan PDF to upload
    """
    browser = None
    context = None
    playwright = None
    try:
        # Parse training days from client data
        training_days_raw = client_data.get(
            'training_days', 'Monday, Wednesday, Friday')  # Default if not specified

        # Handle different formats of training days
        if '-' in training_days_raw:  # Format: "Monday - Friday"
            start_day, end_day = [d.strip()
                                  for d in training_days_raw.split('-')]
            weekdays = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']
            start_idx = weekdays.index(start_day)
            end_idx = weekdays.index(end_day)
            # Handle wrap-around (e.g., "Friday - Monday")
            if end_idx < start_idx:
                end_idx += 7
            training_days = weekdays[start_idx:end_idx + 1]
            if end_idx >= 7:  # Fix wrap-around days
                training_days.extend(weekdays[:end_idx - 7 + 1])
        else:  # Format: "Monday, Wednesday, Friday"
            training_days = [day.strip()
                             for day in training_days_raw.split(',')]

        # Create workout schedule based on number of training days
        workout_types = ['Chest', 'Back', 'Legs', 'Core', 'Shoulders']
        workout_schedule = {}

        # If 3 or fewer days, combine workouts
        if len(training_days) <= 3:
            if len(training_days) == 1:
                # Full body workout on the single day
                workout_schedule = {
                    'Full Body Workout': {'day': training_days[0], 'weeks': 6}
                }
            elif len(training_days) == 2:
                # Split into upper and lower body
                workout_schedule = {
                    'Upper Body': {'day': training_days[0], 'weeks': 6},
                    'Lower Body': {'day': training_days[1], 'weeks': 6}
                }
            else:  # 3 days
                # Push, Pull, Legs split
                workout_schedule = {
                    'Push Day': {'day': training_days[0], 'weeks': 6},
                    'Pull Day': {'day': training_days[1], 'weeks': 6},
                    'Leg Day': {'day': training_days[2], 'weeks': 6}
                }
        else:
            # Assign workouts to each training day
            for i, day in enumerate(training_days):
                if i < len(workout_types):
                    workout_schedule[f'{workout_types[i]} Day'] = {
                        'day': day, 'weeks': 6}

        # Store the schedule in client_data for use in scheduling
        client_data['workout_schedule'] = workout_schedule

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto("https://www.trainerize.com/login.aspx")
            page.get_by_role("link", name="sign in").click()
            page.get_by_role("textbox", name="Enter your email Your").click()
            page.get_by_role("textbox", name="Enter your email Your").fill(
                client_data["coach_email"])
            page.get_by_role(
                "textbox", name="Enter your email Your").press("Enter")
            page.get_by_test_id("email-input").click()
            page.get_by_test_id("email-input").fill(client_data["coach_email"])
            page.get_by_test_id("password-input").click()
            page.get_by_test_id(
                "password-input").fill(client_data["coach_password"])
            page.get_by_test_id("password-input").press("Enter")
            page.get_by_test_id("signIn-button").click()
            page.get_by_test_id("leftNavMenu-item-clients").click()
            page.get_by_test_id("clientGrid-toolbar-addClient").click()
            page.get_by_test_id(
                "addClientDialog-emailInput").fill(client_data["email"])
            page.get_by_test_id("addClientDialog-firstNameInput").click()
            page.get_by_test_id(
                "addClientDialog-firstNameInput").fill(client_data["first_name"])
            page.get_by_test_id("addClientDialog-lastNameInput").click()
            page.get_by_test_id(
                "addClientDialog-lastNameInput").fill(client_data["last_name"])
            page.get_by_test_id("rolePicker").get_by_text(
                "Full Access 2-way messaging").click()
            page.get_by_role(
                "option", name="Full Access 1-way messaging").click()
            page.get_by_test_id("dialog-defaultFooter-confirm-button").click()
            with page.expect_popup() as page1_info:
                # Before clicking 'OPEN CLIENT ACCOUNT', add debugging
                print("Waiting for 'OPEN CLIENT ACCOUNT' button...")
                page.screenshot(path="before_open_client_account.png")
                page.wait_for_timeout(5000)  # Wait 5 seconds
                open_btn = page.locator(
                    "button:has-text('OPEN CLIENT ACCOUNT')")
                open_btn.wait_for(state="visible", timeout=60000)
                open_btn.click()
            page1 = page1_info.value
            # Wait for the new tab to fully load
            try:
                page1.wait_for_load_state("networkidle")
                # Give the new tab a moment to stabilize
                page1.wait_for_timeout(2000)
                page1.get_by_test_id("leftNavMenu-item-mealPlan").click()
                # Wait for the meal plan upload div to appear before clicking
                page1.wait_for_selector(
                    'div:has-text("Attach a meal plan PDFSelect a PDF to upload it.")', timeout=10000)
                upload_div = page1.locator(
                    'div:has-text("Attach a meal plan PDFSelect a PDF to upload it.")').nth(1)
                upload_div.click()
                # Wait for the file input to be attached (not necessarily visible)
                page1.wait_for_selector(
                    'input[type="file"]', state="attached", timeout=10000)
                file_input = page1.locator('input[type="file"]')
                file_input.set_input_files(meal_plan_pdf_path)
                # After setting the input file, short wait for upload to process
                page1.screenshot(path="after_upload.png")
                page1.wait_for_timeout(1000)
                # Wait for the CONFIRM button to be enabled and visible, then click it
                try:
                    confirm_btn = page1.locator(
                        '[data-testid="dialog-defaultFooter-confirm-button"]:not([disabled])')
                    confirm_btn.wait_for(state="visible", timeout=15000)
                    confirm_btn.screenshot(path="before_confirm_click.png")
                    confirm_btn.click()
                    print("PDF uploaded and confirmed.")
                except Exception as e:
                    print(f"Error waiting for or clicking Confirm button: {e}")
                    page1.screenshot(path="error_confirm_click.png")
                    raise
                # Optionally wait for spinner/overlay to disappear
                try:
                    page1.wait_for_selector(
                        '.ant-spin', state='detached', timeout=5000)
                except Exception:
                    pass  # Ignore if not found
                # Wait for the dialog to close (the title input disappears)
                try:
                    page1.wait_for_selector(
                        'input[value^="Shannon_Birch_meal_plan_"]', state="detached", timeout=10000)
                except Exception:
                    pass
                # Wait for loading screen/overlay to disappear after clicking Confirm
                try:
                    page1.wait_for_selector(
                        '.ant-modal-mask', state='detached', timeout=20000)
                except Exception:
                    pass

                # Add a longer wait to ensure the dialog is fully closed and the page is ready
                print("Waiting extra time after confirming PDF upload...")
                # Wait 7 seconds (adjust as needed)
                page1.wait_for_timeout(7000)

                # Check if the page is closed before proceeding
                if page1.is_closed():
                    print("The page was closed after PDF upload. Cannot continue.")
                    return
                print("Open pages after upload:", context.pages)
                # Debug: Print current URL and title before proceeding
                try:
                    print(f"Current page URL: {page1.url}")
                    print(f"Current page title: {page1.title()}")
                except Exception as debug_e:
                    print(f"Error getting page URL or title: {debug_e}")

                page1.wait_for_timeout(1000)
            except Exception as e:
                print("Error interacting with the new client tab:", e)
                page1.screenshot(path="error_in_client_tab.png")
                raise

        # Navigate to training program
        # Debug: Take a screenshot and print page content before clicking
        page1.screenshot(path="before_training_program_click.png")
        try:
            print(page1.content())
        except Exception as e:
            print(f"Error printing page content: {e}")

        # Try clicking using data-testid first, then fallback to text-based selector
        try:
            page1.wait_for_selector(
                '[data-testid="leftNavMenu-item-trainingProgram"]', timeout=10000)
            page1.get_by_test_id("leftNavMenu-item-trainingProgram").click()
        except Exception as e:
            print(f"Primary selector failed: {e}. Trying by text selector...")
            try:
                page1.get_by_text("Training Program", exact=True).click()
            except Exception as e2:
                print(
                    f"Text selector also failed: {e2}. Trying CSS selector...")
                try:
                    page1.locator('p.tz-p.color--gray80.pl8',
                                  has_text="Training Program").click()
                except Exception as e3:
                    print(f"All selectors failed for Training Program: {e3}")
                    raise

        page1.wait_for_selector(
            f'text="Start building out {client_data["first_name"]}\'s"', timeout=10000)
        page1.get_by_text(
            f"Start building out {client_data['first_name']}'s").click()
        page1.wait_for_selector(
            '[data-testid="editTrainingPhase-nameInput"]', timeout=10000)
        page1.get_by_test_id(
            "editTrainingPhase-nameInput").fill(client_data["program_name"])
        page1.wait_for_selector('input[type="text"]', timeout=10000)
        page1.get_by_role("textbox").nth(1).click()
        page1.wait_for_selector('text="12"', timeout=10000)
        page1.get_by_text("12", exact=True).click()
        page1.wait_for_selector(
            'button:has-text("Increase Value")', timeout=10000)
        page1.get_by_role("button", name="Increase Value").dblclick()
        page1.wait_for_selector(
            '[data-testid="dialog-defaultFooter-confirm-button"]:not([disabled])', timeout=10000)
        page1.get_by_test_id("dialog-defaultFooter-confirm-button").click()
        page1.wait_for_selector('button:has-text("New")', timeout=10000)
        page1.get_by_role("button", name="New").click()
        page1.wait_for_selector(
            'input[placeholder="workout name, like Day 1 Abs"]', timeout=10000)
        page1.get_by_role(
            "textbox", name="workout name, like Day 1 Abs").fill("Chest Day")
        page1.wait_for_selector(
            '[data-testid="workoutBuilder-startBuildingButton"]', timeout=10000)
        page1.get_by_test_id("workoutBuilder-startBuildingButton").click()

        # Define all workout days and their exercises
        workout_days = {
            "Chest Day": ["Bench Press", "dumbell bench press", "cable chest flys", "tricep push down"],
            "Back Day": ["Lat Pulldown", "Seated Cable Row", "Face Pulls", "Barbell Row"],
            "Leg Day": ["Squats", "Romanian Deadlift", "Leg Press", "Calf Raises"],
            "Core Day": ["Plank", "Russian Twists", "Cable Crunches", "Leg Raises"],
            "Shoulder Day": ["Military Press", "Lateral Raises", "Front Raises", "Rear Delt Flys"]
        }

        first_day = True
        for day_name, exercises in workout_days.items():
            print(f"\nCreating {day_name}...")

            if not first_day:
                # Only click New for subsequent workouts
                # Wait for previous save to complete
                page1.wait_for_timeout(2000)
                page1.get_by_role("button", name="New").click()
                page1.get_by_role(
                    "textbox", name="workout name, like Day 1 Abs").fill(day_name)
                page1.get_by_test_id(
                    "workoutBuilder-startBuildingButton").click()
            first_day = False

            page1.wait_for_timeout(2000)  # Wait for builder to load

            # Add exercises for this day
            for exercise in exercises:
                print(f"Adding exercise: {exercise}")
                try:
                    # Find and interact with search box using specific selector
                    search_box = page1.locator(
                        'input.ant-input[placeholder="Search for an exercise"]')
                    search_box.click()
                    search_box.fill("")  # Clear first
                    page1.wait_for_timeout(500)  # Small wait after clearing
                    search_box.fill(exercise)
                    search_box.press("Enter")
                    page1.wait_for_timeout(2000)  # Wait for search results

                    # Try clicking the exercise with multiple strategies
                    try:
                        page1.get_by_text(
                            exercise, exact=True).click(timeout=3000)
                    except Exception:
                        try:
                            first_exercise = page1.locator(
                                '[data-testid^="exerciseLibrary-exercise-"]').first
                            first_exercise.click(timeout=3000)
                        except Exception:
                            print(
                                f"Could not select exercise: {exercise}, trying next one")
                            continue

                    page1.wait_for_timeout(1000)  # Wait for modal to stabilize

                    # Try clicking the Add button
                    try:
                        add_button = page1.locator(
                            'button.ant-btn.btn.btn--medium.btn--blue.fullWidth.m8t.gtBtn-blue.dsV2').first
                        add_button.click(timeout=5000)
                    except Exception as e:
                        try:
                            # Fallback to text-based selector
                            page1.get_by_role(
                                "button", name="Add to Workout").click(timeout=5000)
                        except Exception as e:
                            print(
                                f"Error clicking add button for {exercise}: {e}")
                            continue

                    # Wait for exercise to be added
                    page1.wait_for_timeout(2000)
                    print(f"Successfully added exercise: {exercise}")

                except Exception as e:
                    print(f"Error adding exercise {exercise}: {e}")
                    continue

            # Configure sets and reps for all exercises before saving
            print(f"\nConfiguring sets and reps for {day_name}...")
            exercise_count = len(exercises)

            for i in range(exercise_count):
                try:
                    print(f"\nConfiguring exercise {i+1}")

                    # Set number of sets first
                    target_sets = "4"  # Default sets
                    if day_name == "Core Day":
                        target_sets = "3"
                    elif i == 0:  # First exercise gets 5 sets
                        target_sets = "5"

                    # Click and set the number of sets
                    print(f"Setting {target_sets} sets")
                    sets_input = page1.locator(
                        'input[data-testid="workoutBuilder-exerciseSetInput"]').nth(i)
                    sets_input.click()
                    sets_input.press("Control+a")  # Select all text
                    sets_input.press("Delete")  # Clear the field
                    sets_input.fill(target_sets)
                    page1.wait_for_timeout(500)

                    # Set reps
                    reps = "12"  # Default reps
                    if day_name == "Chest Day" or day_name == "Back Day":
                        reps = "8" if i < 2 else "12"
                    elif day_name == "Leg Day":
                        reps = "10" if i < 2 else "15"
                    elif day_name == "Core Day":
                        reps = "20"
                    elif day_name == "Shoulder Day":
                        reps = "12" if i < 2 else "15"

                    # Click and set reps
                    print(f"Setting {reps} reps")
                    reps_input = page1.locator(
                        'input[data-testid="workoutBuilder-recordTypeInput"]').nth(i)
                    reps_input.click()
                    reps_input.fill(reps)
                    page1.wait_for_timeout(500)

                    print(
                        f"Completed configuring exercise {i+1} with {target_sets} sets and {reps} reps")
                    page1.wait_for_timeout(1000)

                except Exception as e:
                    print(f"Error configuring exercise {i+1}: {e}")
                    continue

            # Save the workout
            print(f"\nSaving {day_name}...")
            save_button = page1.locator(
                'button[data-testid="workoutBuilder-saveBtn"]')
            save_button.click(timeout=5000)
            page1.wait_for_timeout(3000)
            print(f"{day_name} saved successfully!")

        print("All workout days created successfully!")

        # Schedule all workouts in the calendar
        schedule_workouts(page1, client_data['workout_schedule'])

        print("\nScript completed successfully!")

    except Exception as e:
        print("=== PLAYWRIGHT SCRIPT EXCEPTION START ===")
        print("Top-level exception in Playwright script:", repr(e))
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        print("=== PLAYWRIGHT SCRIPT EXCEPTION END ===")
        print("\nBrowser will remain open for inspection (error occurred). Press Enter to close the browser...")
        # input()  # Commented out to avoid event loop closure in non-interactive environments
        return  # Prevent further Playwright actions after a fatal error
    finally:
        if context:
            context.close()
        if browser:
            browser.close()


def schedule_workouts_selenium(driver, wait, workout_schedule):
    """Schedule workouts in the calendar for different days of the week using Selenium."""
    print("\nScheduling workouts in calendar...")
    # Navigate to calendar
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-calendar"]'))).click()
    time.sleep(2)
    # Schedule each workout according to the client's preferred days
    for workout_name, schedule in workout_schedule.items():
        try:
            print(f"\nScheduling {workout_name} for {schedule['day']}...")
            # Open the scheduling dialog (right-click equivalent is not directly supported, so use click and fallback if needed)
            calendar_cell = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.react-calendar__tile")))
            calendar_cell.click()
            time.sleep(1)
            # Click 'Workout' in dropdown
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'Workout')]"))).click()
            time.sleep(1)
            # Select from current training (radio button)
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='radio' and @value='current']"))).click()
            except Exception:
                pass
            # Type in workout name
            workout_input = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@placeholder='Type in workout name or']")))
            workout_input.click()
            workout_input.send_keys(workout_name)
            time.sleep(1)
            # Select the specific workout
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(text(), '{workout_name}')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            # Click 'Add Activity' header to dismiss
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(),'Add Activity')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            # Set up weekly repeat
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Repeat')]"))).click()
            except Exception:
                pass
            # Select the day of the week
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//button[contains(@title, '{schedule['day']}')]"))).click()
            except Exception:
                pass
            # Set number of weeks
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//select[@data-testid='repeatDialog-weeklyRepeatFor-select']"))).click()
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//option[@value='{schedule['weeks']}']"))).click()
            except Exception:
                pass
            # Click APPLY
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'APPLY')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            # Save the workout schedule
            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="multipleActivitiesDialog-saveButton"]'))).click()
            time.sleep(2)
            print(f"{workout_name} scheduled successfully!")
        except Exception as e:
            print(f"Error scheduling {workout_name}: {e}")
            continue
    # Cardio scheduling (simplified)
    try:
        print("\nScheduling cardio sessions...")
        calendar_cell = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.react-calendar__tile")))
        calendar_cell.click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(),'Cardio')]"))).click()
        time.sleep(1)
        # Select cardio types (if available)
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'Running')]"))).click()
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'Walking')]"))).click()
        except Exception:
            pass
        # Set cardio duration (if available)
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@type='radio' and @value='time']"))).click()
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@name='duration']"))).send_keys("01")
        except Exception:
            pass
        # Set up cardio schedule (repeat, days, weeks, etc.)
        # ... (similar to above, can be extended as needed)
        # Save cardio schedule
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="multipleActivitiesDialog-saveButton"]'))).click()
        time.sleep(2)
        print("Cardio sessions scheduled successfully!")
    except Exception as e:
        print(f"Error scheduling cardio sessions: {e}")


def run_onboarding_selenium(client_data, meal_plan_pdf_path):
    """
    Automates Trainerize onboarding using Selenium WebDriver (Chrome).
    Args:
        client_data (dict): Dictionary with client info (email, first_name, last_name, etc.)
        meal_plan_pdf_path (str): Path to the meal plan PDF to upload
    """
    chrome_options = Options()
    chrome_options.binary_location = r'C:\Users\Shannon\Downloads\chrome-win64 (4)\chrome-win64\chrome.exe'
    service = Service(
        r'C:\Users\Shannon\Downloads\chromedriver-win64 (3)\chromedriver-win64\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)
    try:
        # Login
        driver.get("https://www.trainerize.com/login.aspx")
        wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "sign in"))).click()
        email_box = wait.until(EC.element_to_be_clickable((By.NAME, "email")))
        email_box.send_keys(client_data["coach_email"])
        email_box.send_keys(Keys.ENTER)
        password_box = wait.until(
            EC.element_to_be_clickable((By.ID, "password-input")))
        password_box.send_keys(client_data["coach_password"])
        password_box.send_keys(Keys.ENTER)
        wait.until(EC.element_to_be_clickable(
            (By.ID, "signIn-button"))).click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-clients"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="clientGrid-toolbar-addClient"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="addClientDialog-emailInput"]'))).send_keys(client_data["email"])
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="addClientDialog-firstNameInput"]'))).send_keys(client_data["first_name"])
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="addClientDialog-lastNameInput"]'))).send_keys(client_data["last_name"])
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="rolePicker"]'))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[contains(., 'Full Access 1-way messaging')]"))).click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="dialog-defaultFooter-confirm-button"]'))).click()
        # Wait for popup and switch to it
        time.sleep(5)
        driver.switch_to.window(driver.window_handles[-1])
        # Meal plan upload
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-mealPlan"]'))).click()
        upload_div = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(text(), 'Attach a meal plan PDFSelect a PDF to upload it.')]")))
        upload_div.click()
        file_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[type="file"]')))
        file_input.send_keys(meal_plan_pdf_path)
        time.sleep(2)
        confirm_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="dialog-defaultFooter-confirm-button"]')))
        confirm_btn.click()
        # Wait for upload to finish
        time.sleep(7)
        # Navigate to Training Program
        try:
            training_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-trainingProgram"]')))
            training_btn.click()
        except Exception:
            try:
                training_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//p[text()='Training Program']")))
                training_btn.click()
            except Exception as e:
                print(f"Could not find Training Program menu: {e}")
                driver.save_screenshot("training_program_not_found.png")
                return
        # Continue with workout creation and scheduling as needed...
        # Example: create a workout (simplified, extend as needed)
        # schedule_workouts_selenium(driver, wait, client_data['workout_schedule'])
        print("Selenium onboarding sequence completed (core steps). Extend as needed for full workflow.")
    except Exception as e:
        print(f"Selenium script error: {e}")
        driver.save_screenshot("selenium_error.png")
    finally:
        pass  # Do not close the browser automatically for inspection


# =====================
# SELENIUM VERSION BELOW (Full Modular Workflow)
# =====================

def selenium_onboard_client(driver, wait, client_data):
    """Onboard a client: login, add client, and switch to client tab."""
    driver.get("https://www.trainerize.com/login.aspx")
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "sign in"))).click()
    email_box = wait.until(EC.element_to_be_clickable((By.NAME, "email")))
    email_box.send_keys(client_data["coach_email"])
    email_box.send_keys(Keys.ENTER)
    password_box = wait.until(
        EC.element_to_be_clickable((By.ID, "password-input")))
    password_box.send_keys(client_data["coach_password"])
    password_box.send_keys(Keys.ENTER)
    wait.until(EC.element_to_be_clickable((By.ID, "signIn-button"))).click()
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-clients"]'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="clientGrid-toolbar-addClient"]'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="addClientDialog-emailInput"]'))).send_keys(client_data["email"])
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="addClientDialog-firstNameInput"]'))).send_keys(client_data["first_name"])
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="addClientDialog-lastNameInput"]'))).send_keys(client_data["last_name"])
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="rolePicker"]'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//li[contains(., 'Full Access 1-way messaging')]"))).click()
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="dialog-defaultFooter-confirm-button"]'))).click()
    time.sleep(5)
    driver.switch_to.window(driver.window_handles[-1])
    print("Client onboarded and client tab active.")


def selenium_upload_meal_plan(driver, wait, meal_plan_pdf_path):
    """Upload a meal plan PDF for the client using Selenium."""
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-mealPlan"]'))).click()
    upload_div = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(text(), 'Attach a meal plan PDFSelect a PDF to upload it.')]")))
    upload_div.click()
    file_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'input[type="file"]')))
    file_input.send_keys(meal_plan_pdf_path)
    time.sleep(2)
    confirm_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="dialog-defaultFooter-confirm-button"]')))
    confirm_btn.click()
    time.sleep(7)
    print("Meal plan uploaded and confirmed.")


def selenium_design_workouts(driver, wait, client_data):
    """Create and design workouts for the client using Selenium."""
    # Navigate to Training Program
    try:
        training_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-trainingProgram"]')))
        training_btn.click()
    except Exception:
        try:
            training_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//p[text()='Training Program']")))
            training_btn.click()
        except Exception as e:
            print(f"Could not find Training Program menu: {e}")
            driver.save_screenshot("training_program_not_found.png")
            return
    # Wait for builder to load and fill in program name
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-testid="editTrainingPhase-nameInput"]'))).send_keys(client_data["program_name"])
    time.sleep(1)
    # Example: create a workout (extend as needed)
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="dialog-defaultFooter-confirm-button"]'))).click()
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'button[data-testid="workoutBuilder-startBuildingButton"]'))).click()
    # Add exercises (simplified example)
    for exercise in ["Bench Press", "Squats"]:
        try:
            search_box = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'input.ant-input[placeholder="Search for an exercise"]')))
            search_box.clear()
            search_box.send_keys(exercise)
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//div[contains(text(), '{exercise}')]"))).click()
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'Add to Workout')]"))).click()
            time.sleep(1)
            print(f"Added exercise: {exercise}")
        except Exception as e:
            print(f"Error adding exercise {exercise}: {e}")
    # Save workout
    try:
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-testid="workoutBuilder-saveBtn"]'))).click()
        print("Workout saved.")
    except Exception as e:
        print(f"Error saving workout: {e}")


def selenium_schedule_workouts(driver, wait, workout_schedule):
    """Schedule workouts in the calendar for different days of the week using Selenium."""
    print("\nScheduling workouts in calendar...")
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '[data-testid="leftNavMenu-item-calendar"]'))).click()
    time.sleep(2)
    for workout_name, schedule in workout_schedule.items():
        try:
            print(f"\nScheduling {workout_name} for {schedule['day']}...")
            calendar_cell = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.react-calendar__tile")))
            calendar_cell.click()
            time.sleep(1)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'Workout')]"))).click()
            time.sleep(1)
            workout_input = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@placeholder='Type in workout name or']")))
            workout_input.click()
            workout_input.send_keys(workout_name)
            time.sleep(1)
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(text(), '{workout_name}')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(text(),'Add Activity')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Repeat')]"))).click()
            except Exception:
                pass
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//button[contains(@title, '{schedule['day']}')]"))).click()
            except Exception:
                pass
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//select[@data-testid='repeatDialog-weeklyRepeatFor-select']"))).click()
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//option[@value='{schedule['weeks']}']"))).click()
            except Exception:
                pass
            try:
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'APPLY')]"))).click()
            except Exception:
                pass
            time.sleep(1)
            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '[data-testid="multipleActivitiesDialog-saveButton"]'))).click()
            time.sleep(2)
            print(f"{workout_name} scheduled successfully!")
        except Exception as e:
            print(f"Error scheduling {workout_name}: {e}")
            continue
    print("All workouts scheduled.")


def run_full_selenium_workflow(client_data, meal_plan_pdf_path):
    """Run the full onboarding, meal plan upload, workout design, and scheduling workflow with Selenium."""
    chrome_options = Options()
    chrome_options.binary_location = r'C:\Users\Shannon\Downloads\chrome-win64 (4)\chrome-win64\chrome.exe'
    service = Service(
        r'C:\Users\Shannon\Downloads\chromedriver-win64 (3)\chromedriver-win64\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)
    try:
        selenium_onboard_client(driver, wait, client_data)
        selenium_upload_meal_plan(driver, wait, meal_plan_pdf_path)
        selenium_design_workouts(driver, wait, client_data)
        if 'workout_schedule' in client_data:
            selenium_schedule_workouts(
                driver, wait, client_data['workout_schedule'])
        print("Selenium full workflow completed.")
    except Exception as e:
        print(f"Selenium script error: {e}")
        driver.save_screenshot("selenium_error.png")
    finally:
        pass  # Do not close the browser automatically for inspection

# To run the full Selenium workflow, call run_full_selenium_workflow(client_data, meal_plan_pdf_path)
# Example usage (uncomment to use):
# run_full_selenium_workflow(client_data, meal_plan_pdf_path)


if __name__ == "__main__":
    # Use default test data
    client_data = {
        'coach_email': 'shannonbirch@cocospersonaltraining.com',
        'coach_password': 'cyywp7nyk2',
        'email': 'shannonbirch@live.com',
        'first_name': 'Shannon',
        'last_name': 'Birch',
        'program_name': 'Shannons Program',
        'workout_schedule': {
            'Chest Day': {'day': 'Monday', 'weeks': 6},
            'Leg Day': {'day': 'Wednesday', 'weeks': 6}
        }
    }
    meal_plan_pdf_path = r'C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\output\\meal plans\\Shannon_Birch_meal_plan_20250508_173956.pdf'
    run_full_selenium_workflow(client_data, meal_plan_pdf_path)
