import time
from datetime import date, timedelta, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options  # Import Options

# --- HARDCODED CREDENTIALS (FOR TESTING ONLY - NOT SECURE) ---
USERNAME = "shannonbirch@cocospersonaltraining.com"  # Replace with your actual username
PASSWORD = "cyywp7nyk"  # Replace with your actual password

# --- Configuration ---
DRIVER_PATH = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"  # Corrected path (using raw string)
TRAINERIZE_URL = "https://www.trainerize.com"  # Or the specific login page if different
CLIENT_NAME = "Nicole Lynch"
START_DATE_STR = "10/Feb/2025"  # Start date of the week to check
END_DATE_STR = "16/Feb/2025"    # End date of the week to check

# --- Date Conversion ---
try:
    START_DATE = datetime.strptime(START_DATE_STR, "%d/%b/%Y").date()
    END_DATE = datetime.strptime(END_DATE_STR, "%d/%b/%Y").date()
except ValueError:
    raise ValueError("Invalid date format.  Please use DD/Mon/YYYY (e.g., 10/Feb/2025).")

def login(driver):
    """Logs into Trainerize."""
    driver.get(TRAINERIZE_URL)

    # --- Find and interact with login elements ---
    #   (You'll need to inspect the Trainerize login page to get the correct element IDs/names/xpaths)
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username")) # Replace "username" with the actual ID
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))  # Replace "password" with the actual ID
        )
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login-button"))  # Replace "login-button"
        )

        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        login_button.click()

        # Wait for successful login (adjust the wait condition as needed)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ember19")) #changed to ember 19 as this seems consistent.
        )  # Replace with an element that appears *after* login
        print("Login successful!")

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Login failed: {e}")
        driver.quit()
        raise

def navigate_to_client(driver, client_name):
    """Navigates to the client's dashboard."""
    try:
        # 1. Search for the member's name
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ember32"))  # Find the correct ID of search box
        )
        search_box.send_keys(client_name)
        time.sleep(2)  # Allow time for search results to load

        # 2. Click "Open" (first pop-up)
        open_button1 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Open')]"))  # Use XPath or other locator
        )
        open_button1.click()
        time.sleep(2)

        # 3. Click "Open" (second pop-up, opens new tab)
        open_button2 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class,'btn btn-success btn-sm js-client-context-menu-open-in-tab')]"))  # Very specific selector, adjust if needed
        )
        open_button2.click()

        # 4. Switch to the new tab
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))  # Wait for 2 windows
        driver.switch_to.window(driver.window_handles[1])  # Switch to the second tab
        print (f"Successfully on the clients page")
        # Wait for client dashboard to load (adjust the wait condition as needed)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ember1448")) #changed to ember1448 as that seems stable
        )  # Replace with an element that appears on the client dashboard

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error navigating to client: {e}")
        driver.quit()
        raise


def get_progress_photos(driver, start_date, end_date):
    """Checks for progress photos within the date range."""
    try:
        # Navigate to Progress Photos
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        
        photos_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress-photos']")) # Replace with correct XPATH
        )
        photos_tab.click()

        # Find photo elements (you'll need to inspect the page to find the correct selectors)
        photo_elements = driver.find_elements(By.XPATH, "//div[@class='progress-photo-item']")  # Example selector

        photos_updated = False
        for photo_element in photo_elements:
            # Extract the date from the photo element (you'll need to figure out how the date is displayed)
            date_text = photo_element.find_element(By.XPATH, ".//span[@class='date']").text  # Example - adjust the selector!
            photo_date = datetime.strptime(date_text, "%d/%b/%Y").date()  # Adjust date format if needed

            if start_date <= photo_date <= end_date:
                photos_updated = True
                break  # Found at least one photo in the range

        return "Updated this week" if photos_updated else "No new photos"

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error checking progress photos: {e}")
        return "Error checking photos"

def get_body_weight(driver, start_date, end_date):
    """Gets body weight data and compares it to the previous weigh-in."""
    try:
        # Navigate to Biometrics > Body Weight
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        
        biometrics_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='biometrics']")) # Replace with correct XPATH
        )
        biometrics_tab.click()
        
        bodyweight_tab = WebDriverWait(driver, 10).until(
           EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='bodyweight']")) # Replace with correct XPATH
        )
        bodyweight_tab.click()
        time.sleep(2)
        # Find the weight data elements (this is highly dependent on the Trainerize website structure)
        weight_elements = driver.find_elements(By.XPATH, "//div[@class='data-point']")  #  VERY LIKELY TO NEED ADJUSTMENT

        weights = []
        for element in weight_elements:
            try:
                date_text = element.find_element(By.XPATH, ".//span[@class='date']").text #Adjust
                weight_text = element.find_element(By.XPATH, ".//span[@class='value']").text #Adjust
                weight_date = datetime.strptime(date_text, "%d %b").date() #Adjust date
                weight_value = float(weight_text.replace("kg", "").strip())  # Clean up the value
                weights.append((weight_date, weight_value))
            except NoSuchElementException:
                continue # Skip if date or weight can be located


        # Sort weights by date
        weights.sort(key=lambda x: x[0])

        if not weights:
            return "No weight data available"

        # Find the most recent weigh-in within the target week
        latest_weight = None
        for weight_date, weight_value in reversed(weights):  # Iterate in reverse (most recent first)
             if start_date <= weight_date <= end_date:
                latest_weight = (weight_date, weight_value)
                break

        if latest_weight is None:
             return "No weigh-in this week"

        # Find the previous weigh-in
        previous_weight = None
        for i in range(len(weights) - 2, -1, -1): #Iterate backwords from second last value
            if weights[i][0] < latest_weight[0]:
                previous_weight = weights[i]
                break

        if previous_weight is None:
            return f"Latest weight: {latest_weight[1]}kg (no previous weigh-in)"

        # Calculate the difference
        weight_diff = latest_weight[1] - previous_weight[1]
        if weight_diff > 0:
            return f"Up {weight_diff:.2f}kg this week compared to last"
        elif weight_diff < 0:
            return f"Down {abs(weight_diff):.2f}kg this week compared to last"  # Use abs to show positive loss
        else:
            return "No change in weight this week"

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error getting body weight: {e}")
        return "Error getting weight data"
    
def get_calorie_intake(driver, start_date, end_date):
    """Analyzes calorie intake for the week."""
    try:
        # Navigate to Nutrition > Calorie Intake
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        nutrition_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='nutrition']")) # Replace with correct XPATH
        )
        nutrition_tab.click()
        calorie_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='calorie-intake']")) # Replace with correct XPATH
        )
        calorie_tab.click()

        # Extract calorie data (this will be very specific to the website structure)
        calorie_data = []
        calorie_elements = driver.find_elements(By.XPATH, "//div[@class='calorie-entry']")  #  NEEDS ADJUSTMENT - find the right selector

        for element in calorie_elements:
            try:
                date_text = element.find_element(By.XPATH, ".//span[@class='date']").text  #  NEEDS ADJUSTMENT
                calorie_text = element.find_element(By.XPATH, ".//span[@class='calories']").text  #  NEEDS ADJUSTMENT
                calorie_date = datetime.strptime(date_text, "%d %b").date() #Adjust date
                calorie_value = int(calorie_text.replace("kcal", "").strip())  # Clean and convert to integer

                if start_date <= calorie_date <= end_date:
                    calorie_data.append((calorie_date, calorie_value))
            except (NoSuchElementException, ValueError):
                continue  # Skip if date or calorie value is invalid

        if not calorie_data:
            return "No calorie data for this week"

        # Calculate average weekly intake
        total_calories = sum(calorie for _, calorie in calorie_data)
        average_calories = total_calories / len(calorie_data)

        # Check for days over the recommended intake (you'll need to get the recommended intake from somewhere -  client goals?)
        # For this example, I'll assume a recommended intake of 1500 calories
        recommended_intake = 1500
        days_over = []
        for calorie_date, calorie_value in calorie_data:
            if calorie_value > recommended_intake:
                days_over.append((calorie_date, calorie_value))
        days_over_string = ""
        for x in days_over:
            days_over_string = days_over_string + f"{x[0].strftime('%A')} {x[1]}, "
        return f"Average Weekly Calories: {average_calories:.0f} cals, {days_over_string}"

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error getting calorie intake: {e}")
        return "Error getting calorie data"
    
def get_cardio_activities(driver, start_date, end_date):
    """Analyzes completed cardio activities for the week."""
    try:
        # Navigate to Cardio Activities
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        cardio_tab = WebDriverWait(driver, 10).until(
             EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='cardio-activities']")) # Replace with correct XPATH
        )
        cardio_tab.click()
        activities_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='activities']")) # Replace with correct XPATH
        )
        activities_tab.click()
      

        # Find cardio activity elements
        activity_elements = driver.find_elements(By.XPATH, "//div[@class='cardio-activity']")  #  NEEDS ADJUSTMENT - find the right selector!

        activities_completed = []
        longest_activity = None
        longest_duration = timedelta()  # Initialize to zero duration

        for element in activity_elements:
            try:
                date_text = element.find_element(By.XPATH, ".//span[@class='date']").text  #  NEEDS ADJUSTMENT
                duration_text = element.find_element(By.XPATH, ".//span[@class='duration']").text  #  NEEDS ADJUSTMENT
                activity_type = element.find_element(By.XPATH, ".//span[@class='type']").text  #  NEEDS ADJUSTMENT
                activity_date = datetime.strptime(date_text, "%d %b").date()#adjust date

                # Parse duration (this might be in different formats, e.g., "1h 30m", "45min")
                # You'll need to write a robust parsing function.  Here's a basic example:
                duration_parts = duration_text.split()
                hours = 0
                minutes = 0
                for i in range(0, len(duration_parts), 2):
                    if duration_parts[i+1].startswith("h"):
                        hours = int(duration_parts[i])
                    elif duration_parts[i+1].startswith("m"):
                        minutes = int(duration_parts[i])
                duration = timedelta(hours=hours, minutes=minutes)

                if start_date <= activity_date <= end_date:
                    activities_completed.append((activity_type, duration))
                    if duration > longest_duration:
                        longest_duration = duration
                        longest_activity = (activity_type, duration)
            except (NoSuchElementException, ValueError):
                continue  # Skip if data is invalid

        if not activities_completed:
            return "No cardio activities completed this week."

        activity_summary = f"Total Cardio Activities Tracked: {len(activities_completed)} "

        if longest_activity:
            activity_summary += f" Longest Activity = {longest_activity[0]} {longest_activity[1]}"

        return activity_summary

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error getting cardio activities: {e}")
        return "Error getting cardio data"

def get_workouts_completed(driver, start_date, end_date):
    """Counts the number of workouts completed within the week."""
    try:
        # Navigate to Review by Workout
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        workout_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='review-by-workout']")) # Replace with correct XPATH
        )
        workout_tab.click()

        # Find workout elements
        workout_elements = driver.find_elements(By.XPATH, "//div[@class='workout-entry']")  # NEEDS ADJUSTMENT

        workouts_count = 0
        for element in workout_elements:
            try:
                date_text = element.find_element(By.XPATH, ".//span[@class='date']").text  # NEEDS ADJUSTMENT
                workout_date = datetime.strptime(date_text, "%d %b").date()#Adjust date
                if start_date <= workout_date <= end_date:
                    workouts_count += 1
            except (NoSuchElementException, ValueError):
                continue

        return f"Total Workouts Completed: {workouts_count}"

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error getting workout count: {e}")
        return "Error getting workout data"


def get_workout_progression(driver, start_date, end_date):
    """Analyzes workout progression for two lifts."""
    try:
        # Navigate to Review by Workout (same as previous function)
        progress_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='progress']")) # Replace with correct XPATH or other locator
        )
        progress_tab.click()
        workout_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-test-id='review-by-workout']")) # Replace with correct XPATH
        )
        workout_tab.click()

        # Find workout elements (same as previous function)
        workout_elements = driver.find_elements(By.XPATH, "//div[@class='workout-entry']")  # NEEDS ADJUSTMENT

        progressions = []
        for element in workout_elements:
           try:
                date_text = element.find_element(By.XPATH, ".//span[@class='date']").text  # NEEDS ADJUSTMENT
                workout_date = datetime.strptime(date_text, "%d %b").date()#Adjust date
                if start_date <= workout_date <= end_date:
                 #Within each workout, find lift details
                  lift_elements = element.find_elements(By.XPATH, ".//div[@class='lift-entry']") #NEEDS ADJUSTMENT
                  for lift in lift_elements:
                      try:
                          lift_name = lift.find_element(By.XPATH, ".//span[@class='lift-name']").text #NEEDS ADJUSTMENT
                          weight = lift.find_element(By.XPATH, ".//span[@class='weight']").text #NEEDS ADJUSTMENT
                          reps = lift.find_element(By.XPATH, ".//span[@class='reps']").text #NEEDS ADJUSTMENT

                          progressions.append((workout_date, lift_name, weight, reps))
                      except NoSuchElementException:
                        continue #Skip if not found
           except (NoSuchElementException, ValueError):
            continue  # Skip this workout if date parsing fails

        #Analyze progressions (This is a simplified example.  You could implement more complex logic)
        # Sort by lift name and then date:
        progressions.sort(key=lambda x: (x[1], x[0]))
        progression_summary = ""

        #Example:  Compare two lifts
        if len(progressions) >= 2:
            for i in range(len(progressions) -1):
                if progressions[i][1] == progressions[i+1][1]: #Same Lift Name
                   progression_summary += f"{progressions[i][1]} improved from {progressions[i][0].strftime('%d %b')} {progressions[i][2]} for {progressions[i][3]} reps, to {progressions[i + 1][0].strftime('%d %b')} {progressions[i+1][2]} for {progressions[i+1][3]},"

        return f"Noticeable Workout Progression: {progression_summary}"

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error getting workout progression: {e}")
        return "Error getting workout progression data"


def generate_checkin_review(driver, client_name, start_date, end_date):
    """Generates the check-in review text."""

    progress_photos = get_progress_photos(driver, start_date, end_date)
    body_weight = get_body_weight(driver, start_date, end_date)
    calorie_intake = get_calorie_intake(driver, start_date, end_date)
    cardio_activities = get_cardio_activities(driver, start_date, end_date)
    workouts_completed = get_workouts_completed(driver, start_date, end_date)
    workout_progression = get_workout_progression(driver, start_date, end_date)

    review = f"Hey {client_name},\n\nGreat to check in on your progress for the week of {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}!\n\nHere's a summary:\n"
    review += f"* Progress Photos - {progress_photos}\n"
    review += f"* Body Weight - {body_weight}\n"
    review += f"* {calorie_intake}\n"  # Already includes "Average Weekly Calories"
    review += f"* {cardio_activities}\n" # Already includes "Total Cardio Activities"
    review += f"* {workouts_completed}\n"
    review += f"* {workout_progression}\n"

    review += "\nOverall Really great week from you Nic! Very happy with your consistency. Keep it coming\n"
    review += "Keep Moving Coach Shan"

    return review


def main():
    """Main function to run the bot."""
    # --- Configure Chrome Options ---
    chrome_options = Options()
    chrome_options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"  # REPLACE WITH YOUR ACTUAL PATH
    # Optional: Add other options if you want (like in your Instagram script)
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--disable-notifications")

    # Use the Service object AND the options
    service = Service(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    try:
        login(driver)
        navigate_to_client(driver, CLIENT_NAME)
        review = generate_checkin_review(driver, CLIENT_NAME, START_DATE, END_DATE)
        print("\n--- Check-in Review ---\n")
        print(review)

    finally:
        driver.quit()  # Always close the browser, even if errors occur

if __name__ == "__main__":
    main()