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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, InvalidSessionIdException, StaleElementReferenceException
import re
import base64
import json
import sys
import google.generativeai as genai
import glob
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from google.oauth2 import service_account
from googleapiclient.discovery import build

# THIS IS THE EDITED VERSION WITH MACRO DATA AND FIRST NAME ADDRESSING
print("**** RUNNING THE UPDATED VERSION WITH MACRO DATA AND FIRST NAME ADDRESSING ****")
print("**** UPDATED MODEL: gemini-2.0-flash-thinking-exp-01-21 ****")


class TrainerizeAutomation:
    def __init__(self, openai_api_key=None):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
        self.chrome_executable_path = r"C:\SeleniumDrivers\chrome-win64\chrome.exe"
        self.openai_api_key = openai_api_key

        if openai_api_key:
            genai.configure(api_key=self.openai_api_key)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-thinking-exp-01-21')
            logging.info("Gemini API configured.")
        else:
            self.model = None
            logging.info("Gemini API not configured (API key not provided).")

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
        chrome_options.binary_location = self.chrome_executable_path

        try:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")

        except Exception as e:
            logging.exception(
                f"Failed to initialize Chrome or Gemini API: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def setup_sheets_api(self):
        """Set up and return the Google Sheets API client"""
        try:
            # Get the current script directory
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Path to your service account credentials JSON file (try multiple locations)
            SERVICE_ACCOUNT_FILE = os.path.join(
                current_dir, 'service-account-credentials.json')

            # Check if file exists at the specified path, try alternative locations if not
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                alt_path = 'service-account-credentials.json'  # Try root directory
                if os.path.exists(alt_path):
                    SERVICE_ACCOUNT_FILE = alt_path
                else:
                    logging.error(
                        "Could not find service-account-credentials.json file!")
                    print(
                        "✗ ERROR: service-account-credentials.json not found - tried multiple locations")
                    return None

            print(
                f"✓ Found service account credentials at: {SERVICE_ACCOUNT_FILE}")

            # Define the scope
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

            # Create credentials
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            # Build the service
            service = build('sheets', 'v4', credentials=credentials)

            print("✓ Successfully connected to Google Sheets API")
            return service.spreadsheets()
        except Exception as e:
            logging.exception(f"Error setting up Google Sheets API: {e}")
            print(f"✗ Error setting up Google Sheets API: {str(e)}")
            return None

    # Fix 2: Add this function to verify credentials before attempting updates
    def verify_sheets_credentials(self):
        """Verify that the Google Sheets API credentials are working"""
        try:
            sheets = self.setup_sheets_api()
            if not sheets:
                return False

            # Try a simple API call to verify credentials
            SPREADSHEET_ID = '1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo'
            result = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()

            if result and 'properties' in result:
                print(f"✓ Successfully verified Google Sheets credentials")
                print(
                    f"✓ Connected to spreadsheet: {result['properties'].get('title', 'Unknown')}")
                return True
            return False
        except Exception as e:
            logging.exception(
                f"Error verifying Google Sheets credentials: {e}")
            print(f"✗ Error verifying Google Sheets credentials: {str(e)}")
            return False

    def update_legit_checkin_status(self, first_name, last_name, legit_checkin_value="Yes"):
        """
        Updates the "Legit Checkin" status (column AE) for a specific person
        by matching their first name (column D) and last name (column E)
        """
        try:
            print(
                f"\nAttempting to update Legit Checkin for {first_name} {last_name}...")

            # First verify credentials
            if not self.verify_sheets_credentials():
                print(
                    "✗ Failed to verify Google Sheets credentials - check service account JSON file")
                return False

            sheets = self.setup_sheets_api()
            if not sheets:
                print("✗ Failed to set up Google Sheets API - check credentials!")
                return False

            print("✓ Google Sheets API connected successfully")

            # Your specific spreadsheet ID
            SPREADSHEET_ID = '1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo'

            # Step 1: Get all data to find the matching person
            try:
                result = sheets.values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Sheet1!A:AZ'  # Make sure this is the correct sheet name
                ).execute()

                # IMPORTANT FIX: Assign rows from the result values
                rows = result.get('values', [])
                if not rows:
                    print("✗ No data found in the spreadsheet")
                    return False

                print(
                    f"✓ Successfully retrieved spreadsheet data, found {len(rows)} rows")
            except Exception as api_error:
                print(f"✗ Error accessing spreadsheet: {api_error}")
                return False

            # Find the column indices
            first_name_col_index = 3  # Column D (0-indexed)
            last_name_col_index = 4   # Column E (0-indexed)

            # Step 2: Find the row that matches our person's name
            row_index = -1
            for i in range(1, len(rows)):  # Start from 1 to skip header row
                # Make sure row has enough columns
                if len(rows[i]) > max(first_name_col_index, last_name_col_index):
                    row_first_name = rows[i][first_name_col_index].strip(
                    ).lower() if len(rows[i]) > first_name_col_index else ""
                    row_last_name = rows[i][last_name_col_index].strip(
                    ).lower() if len(rows[i]) > last_name_col_index else ""

                    # Check if this row matches our search criteria
                    if (row_first_name == first_name.strip().lower() and
                            row_last_name == last_name.strip().lower()):
                        row_index = i
                        print(
                            f"✓ Found matching row for {first_name} {last_name} at row {row_index+1}")
                        break

            if row_index == -1:
                print(f"✗ No person found with name: {first_name} {last_name}")
                logging.info(
                    f"No person found with name: {first_name} {last_name}")
                return False

            # Step 3: Update only the "Legit Checkin" column (AE) for this person
            # Convert column AE to number: A=0, Z=25, AA=26, AE=30
            legit_checkin_col_index = 30  # Column AE (0-indexed)

            # Row index is 0-based in our array, but 1-based in the sheet
            row_number = row_index + 1

            # Create range for just column AE in this row (AE5 for row 5, for example)
            range_name = f'Sheet1!AE{row_number}'

            # Prepare the updated data
            values = [[legit_checkin_value]]  # Single cell update

            body = {
                'values': values
            }

            # Update only the Legit Checkin cell
            try:
                update_result = sheets.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                print(
                    f"✓ Successfully updated Google Sheet! Set 'Legit Checkin' to '{legit_checkin_value}' for {first_name} {last_name}")
                logging.info(
                    f"Legit Checkin status updated for {first_name} {last_name}")
                return True
            except Exception as update_error:
                print(f"✗ Error updating Google Sheet: {update_error}")
                logging.error(f"Error updating sheet: {update_error}")
                return False

        except Exception as e:
            print(f"✗ Error during Google Sheets update process: {str(e)}")
            logging.exception(f"Error updating Legit Checkin status: {e}")
            return False

    def save_fitness_wrapped_data(self, client_name, fitness_wrapped_data):
        """Save the prepared data to a JSON file."""
        import json

        # Add today's date to the filename
        today_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{client_name.replace(' ', '_')}_{today_str}_fitness_wrapped_data.json"

        try:
            with open(filename, 'w') as f:
                json.dump(fitness_wrapped_data, f, indent=4)
            logging.info(f"Saved fitness wrapped data to {filename}")
            return filename
        except Exception as e:
            logging.exception(f"Error saving fitness wrapped data: {e}")
            return None

    def update_gemini_checkin_data(self, first_name, last_name, checkin_review_content):
        """
        Updates a column in Google Sheets with the Gemini check-in review content for a specific client

        Args:
            first_name: Client's first name
            last_name: Client's last name
            checkin_review_content: The content generated by Gemini

        Returns:
            Boolean indicating success
        """
        try:
            print(
                f"\nAttempting to update Gemini Check-in for {first_name} {last_name}...")

            # First verify credentials
            if not self.verify_sheets_credentials():
                print("✗ Failed to verify Google Sheets credentials")
                return False

            sheets = self.setup_sheets_api()
            if not sheets:
                print("✗ Failed to set up Google Sheets API")
                return False

            print("✓ Google Sheets API connected successfully")

            # Your specific spreadsheet ID
            SPREADSHEET_ID = '1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo'

            # Get all data to find the matching person
            try:
                result = sheets.values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Sheet1!A:AZ'  # Make sure this is the correct sheet name
                ).execute()

                rows = result.get('values', [])
                if not rows:
                    print("✗ No data found in the spreadsheet")
                    return False

                print(
                    f"✓ Successfully retrieved spreadsheet data, found {len(rows)} rows")
            except Exception as api_error:
                print(f"✗ Error accessing spreadsheet: {api_error}")
                return False

            # Find the column indices
            first_name_col_index = 3  # Column D (0-indexed)
            last_name_col_index = 4   # Column E (0-indexed)

            # Define which column to update with the Gemini check-in data
            # For example, column AF (index 31) - adjust as needed
            gemini_checkin_col_index = 31  # Column AF (0-indexed)

            # Find the row that matches our person's name
            row_index = -1
            for i in range(1, len(rows)):  # Start from 1 to skip header row
                # Make sure row has enough columns
                if len(rows[i]) > max(first_name_col_index, last_name_col_index):
                    row_first_name = rows[i][first_name_col_index].strip(
                    ).lower() if len(rows[i]) > first_name_col_index else ""
                    row_last_name = rows[i][last_name_col_index].strip(
                    ).lower() if len(rows[i]) > last_name_col_index else ""

                    # Check if this row matches our search criteria
                    if (row_first_name == first_name.strip().lower() and
                            row_last_name == last_name.strip().lower()):
                        row_index = i
                        print(
                            f"✓ Found matching row for {first_name} {last_name} at row {row_index+1}")
                        break

            if row_index == -1:
                print(f"✗ No person found with name: {first_name} {last_name}")
                logging.info(
                    f"No person found with name: {first_name} {last_name}")
                return False

            # Convert to the appropriate column letter (AF for index 31)
            column_letter = self.index_to_column_letter(
                gemini_checkin_col_index)

            # Row index is 0-based in our array, but 1-based in the sheet
            row_number = row_index + 1

            # Create range for just the Gemini check-in column in this row (AF5 for row 5, for example)
            range_name = f'Sheet1!{column_letter}{row_number}'

            # Check if there's existing content in the cell
            try:
                existing_content_result = sheets.values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name
                ).execute()

                existing_values = existing_content_result.get('values', [])
                has_existing_content = existing_values and len(existing_values) > 0 and existing_values[0] and len(
                    existing_values[0]) > 0 and existing_values[0][0]
            except Exception as e:
                logging.warning(f"Error checking for existing content: {e}")
                has_existing_content = False

            # Add today's date to the check-in content
            today_date = datetime.now().strftime('%Y-%m-%d')

            # Prepare the updated data - limit content length if needed
            max_length = 49000
            if checkin_review_content is None:
                logging.warning(
                    "Checkin review content is None, using empty string instead")
                formatted_content = f"[Check-in {today_date}]\n\n(Empty check-in)"
            else:
                # Add date header to the content
                formatted_content = f"[Check-in {today_date}]\n\n{checkin_review_content}"

                # If there's existing content, we will replace it with the new check-in
                # We no longer need to check for existing content since we're replacing it anyway
                # Just making sure the content isn't too long

                # Truncate if too long
                if len(formatted_content) > max_length:
                    formatted_content = formatted_content[:max_length] + \
                        "... (truncated)"

            values = [[formatted_content]]  # Single cell update

            body = {
                'values': values
            }

            # Update only the Gemini check-in cell
            try:
                update_result = sheets.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                if has_existing_content:
                    print(
                        f"✓ Successfully REPLACED existing check-in with new check-in dated {today_date} for {first_name} {last_name}")
                    logging.info(
                        f"Replaced existing check-in with new check-in dated {today_date} for {first_name} {last_name}")
                else:
                    print(
                        f"✓ Successfully added first check-in dated {today_date} to Google Sheet for {first_name} {last_name}")
                    logging.info(
                        f"Added first check-in dated {today_date} to Google Sheet for {first_name} {last_name}")

                return True
            except Exception as update_error:
                print(f"✗ Error updating Google Sheet: {update_error}")
                logging.error(f"Error updating sheet: {update_error}")
                return False

        except Exception as e:
            print(f"✗ Error during Google Sheets update process: {str(e)}")
            logging.exception(f"Error updating check-in data: {e}")
            return False

    def generate_professional_checkin_review(self, client_name, fitness_wrapped_data):
        """
        Generate a professional check-in review PDF for a client

        Args:
            client_name: Client's full name
            fitness_wrapped_data: Dictionary containing fitness data

        Returns:
            Tuple of (pdf_filename, review_content)
        """
        logging.info(
            f"Generating professional check-in review for {client_name}")
        print(
            f"\nGenerating professional check-in review for {client_name}...")

        # Create the review content
        review_content = self.generate_checkin_review_content(
            client_name, fitness_wrapped_data)

        if not review_content:
            logging.error(
                f"Failed to generate review content for {client_name}")
            return None, None

        # Create the PDF document
        pdf_filename = self.create_checkin_review_pdf(
            client_name, fitness_wrapped_data, review_content)

        if not pdf_filename:
            logging.error(f"Failed to create PDF for {client_name}")
            return None, review_content

        print(f"✓ Successfully generated check-in review for {client_name}")
        logging.info(
            f"Successfully generated check-in review for {client_name}")

        return pdf_filename, review_content

    def index_to_column_letter(self, index):
        """Convert a 0-based column index to an Excel-style column letter (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        while index >= 0:
            remainder = index % 26
            result = chr(65 + remainder) + result
            index = index // 26 - 1
        return result

    def generate_checkin_review_content(self, client_name, fitness_wrapped_data):
        """Generates the check-in review content using Gemini."""
        try:
            logging.info(
                f"Generating check-in review content for {client_name} with Gemini...")

            # Extract first name for personalized addressing in the review
            first_name = client_name.split()[0]
            logging.info(
                f"Using first name '{first_name}' for personalized addressing in review")

            # Check which data is actually available
            has_steps_data = fitness_wrapped_data.get('has_steps_data', False)
            has_sleep_data = fitness_wrapped_data.get('has_sleep_data', False)
            has_nutrition_data = fitness_wrapped_data.get(
                'has_nutrition_data', False)
            has_weight_data = fitness_wrapped_data.get(
                'has_weight_data', False)
            has_workout_data = fitness_wrapped_data.get(
                'has_workout_data', False)
            has_exercise_data = fitness_wrapped_data.get(
                'has_exercise_data', False)

            # Format all relevant client data for the prompt, including what data is missing
            prompt = f"""
            Generate a professional, personalized fitness check-in review for {client_name}.

            IMPORTANT:
            1. For any data that's not available (labeled "NO DATA" or "Not Recorded"), include a professionally-worded encouragement to start tracking this metric.
            2. Use bold text indicators with "Weight Management Analysis:" format (not **Weight Management Analysis:**)
            3. In the Training Performance Analysis section, DO NOT list the specific workout names (like "Chest and Biceps" etc.)
            4. Make the "Goals and Recommendations for the Coming Week:" section use bullet points with "* " at the start of each point
            5. DO NOT include a section labeled "Closing Statement:" - instead, just add a motivational closing paragraph after the bullet points without a label
            6. The review will be signed off as "Coco's Connected/Shannon Birch" - no need to include this in the content
            7. VERY IMPORTANT: When addressing the client directly in the review, use only their first name ("{first_name}"), not their full name
            8. For any data marked "Not Recorded", include specific encouragement for the client to track this metric, explaining its importance to their fitness journey

            CLIENT DATA:
            """

            # Include weight data if available, otherwise note it's missing
            if has_weight_data and fitness_wrapped_data.get('current_weight', 'Not Recorded') != 'Not Recorded':
                # Simplified to just total weight change
                total_change = fitness_wrapped_data['total_weight_change']
                start_weight = int(fitness_wrapped_data['start_weight'])
                current_weight = int(fitness_wrapped_data['current_weight'])

                prompt += f"""
                - Weight: Started at {start_weight}kg, currently {current_weight}kg
                - Total weight change: {int(abs(total_change))}kg {'loss' if total_change > 0 else 'gain'} (IMPORTANT: This is the OVERALL total change since starting, NOT just for this week)
                """

                # Only add weight goal if it's a valid dictionary with a target
                if fitness_wrapped_data['weight_goal'] is not False and isinstance(fitness_wrapped_data['weight_goal'], dict) and 'target' in fitness_wrapped_data['weight_goal']:
                    # Extract the target value from the dictionary
                    weight_goal_target = fitness_wrapped_data['weight_goal']['target']
                    # Convert to integer
                    weight_goal_int = int(weight_goal_target)
                    prompt += f"- Weight goal: {weight_goal_int}kg\n"
                else:
                    prompt += "- IMPORTANT: DO NOT MENTION ANY WEIGHT GOAL - the client does not have one set\n"
            else:
                prompt += """
                - Weight: NO DATA (emphasize that consistent weight tracking is crucial for monitoring progress and adjusting the nutrition and training plan accordingly)
                """

            # Include workout data if available, otherwise note it's missing
            if has_workout_data:
                prompt += f"""
                - Workouts completed this week: {fitness_wrapped_data['workouts_this_week']}
                - Workout types: {', '.join(fitness_wrapped_data['workout_types'][:4])}
                - Total weight lifted: {fitness_wrapped_data['total_weight_lifted']}kg
                - Total reps: {fitness_wrapped_data['total_reps']}
                - Total sets: {fitness_wrapped_data['total_sets']}
                - Workload increase: {fitness_wrapped_data['workload_increase']}%
                """
            else:
                prompt += """
                - Workouts: NO DATA (emphasize the importance of logging workouts to track progress, ensure program adherence, and allow for proper load management)
                """

            # Include nutrition data if available, otherwise note it's missing
            if has_nutrition_data and fitness_wrapped_data.get('calories_consumed', 'Not Recorded') != 'Not Recorded':
                calories = fitness_wrapped_data['calories_consumed']

                # Add special note if calories are very low
                calories_note = ""
                try:
                    # Convert calories to integer or float before comparing
                    # Remove any non-numeric characters (like "kcal") if present
                    calories_str = str(calories).split()[0]
                    # Try converting to int first, if that fails try float
                    try:
                        calories_value = int(calories_str)
                        if calories_value < 1000:
                            calories_note = " (IMPORTANT: This low calorie count is most likely due to inconsistent tracking - focus on encouraging more consistent tracking rather than discussing low calorie intake)"
                    except ValueError:
                        # Try to convert to float and then to int
                        try:
                            calories_value = int(float(calories_str))
                            if calories_value < 1000:
                                calories_note = " (IMPORTANT: This low calorie count is most likely due to inconsistent tracking - focus on encouraging more consistent tracking rather than discussing low calorie intake)"
                        except ValueError:
                            # If conversion fails, don't add any note - we won't assume anything about the calories
                            pass
                except Exception as e:
                    logging.warning(f"Error processing calories value: {e}")

                # Check for nutrition tracking consistency
                nutrition_consistency_note = ""
                if not fitness_wrapped_data.get('nutrition_tracking_consistent', True):
                    nutrition_consistency_note = """
                - Nutrition tracking consistency: INCONSISTENT (IMPORTANT: Focus on encouraging consistent daily tracking)
                """
                    if fitness_wrapped_data.get('nutrition_tracking_days', 0) > 0:
                        nutrition_consistency_note = f"""
                - Nutrition tracking consistency: INCONSISTENT - only tracked {fitness_wrapped_data['nutrition_tracking_days']} day{'s' if fitness_wrapped_data['nutrition_tracking_days'] > 1 else ''} (IMPORTANT: Focus on encouraging consistent daily tracking)
                """

                prompt += f"""
                - Calories: {calories}{calories_note}
                - Protein: {fitness_wrapped_data['protein_consumed']}
                - Fats: {fitness_wrapped_data['fats_consumed']}
                - Carbs: {fitness_wrapped_data['carbs_consumed']}{nutrition_consistency_note}
                """
            else:
                prompt += """
                - Nutrition: NO DATA (explain how proper nutrition tracking is essential for body composition goals, recovery, and energy management)
                """

            # Include steps data if available, otherwise note it's missing
            if has_steps_data and fitness_wrapped_data.get('step_count', 'Not Recorded') != 'Not Recorded':
                # Handle the case of sporadic data separately
                if fitness_wrapped_data['step_count'] == "Available but sporadic":
                    prompt += """
                    - Steps: AVAILABLE BUT SPORADIC (explain how more consistent tracking of steps would provide better insights for tracking activity levels)
                    """
                else:
                    prompt += f"""
                    - Average step count: {fitness_wrapped_data['step_count']}
                    """
            else:
                prompt += """
                - Steps: NO DATA (explain how tracking daily steps helps monitor non-exercise activity and contributes to overall calorie expenditure)
                """

            # Include sleep data if available, otherwise note it's missing
            if has_sleep_data and fitness_wrapped_data.get('sleep_hours', 'Not Recorded') != 'Not Recorded':
                # Handle the case of minimal data separately
                if fitness_wrapped_data['sleep_hours'] == "Minimal Data Available":
                    prompt += """
                    - Sleep: MINIMAL DATA AVAILABLE (explain how more consistent tracking of sleep would provide better insights for recovery and performance)
                    """
                else:
                    prompt += f"""
                    - Sleep pattern: {fitness_wrapped_data['sleep_hours']}
                    """
            else:
                prompt += """
                - Sleep: NO DATA (explain how tracking sleep quality and duration is crucial for recovery, performance, and overall health)
                """

            # Include exercise improvement data if available, otherwise note it's missing
            if has_exercise_data:
                prompt += f"""
                - Top performing exercises: {', '.join([f"{ex['name']} ({ex['improvement']}% improvement)" for ex in fitness_wrapped_data['top_exercises']])}
                """
            else:
                prompt += """
                - Exercises: NO DETAILED EXERCISE DATA (suggest consistent tracking of key exercises to monitor strength improvements)
                """

            prompt += """
            Structure the review as follows:

            1. Personalized greeting and summary of overall progress
               - Begin with "Hi [FIRST NAME]," or similar, using ONLY the client's first name
            2. Weight Management Analysis: (or encouragement to track if no data)
               - Start this on a new line with exactly "Weight Management Analysis:" and then continue with your analysis
               - VERY IMPORTANT: When discussing weight change, refer to it as "overall weight change" or "total progress so far" - DO NOT say "this week you lost X kg" as the weight data represents total change since starting, not weekly change
            3. Training Performance Analysis: (or encouragement to track if no data)
               - Start this on a new line with exactly "Training Performance Analysis:" and then continue with your analysis
            4. Nutrition and Lifestyle Observations: (or encouragement to track if no data)
               - Start this on a new line with exactly "Nutrition and Lifestyle Observations:" and then continue with your analysis
               - Include analysis of both calorie intake and macronutrient balance (protein, fats, carbs) if data is available
               - Comment on the protein intake relative to body weight goals
               - Comment on the balance of fats and carbs in the diet
            5. Specific Exercise Achievements: (highlight top improvements) (or encouragement to track if no data)
               - Start this on a new line with exactly "Specific Exercise Achievements:" and then continue with your analysis
            6. Missing Data: (summarize what data is missing and the benefits of tracking it - if any data is missing)
               - Start this on a new line with exactly "Missing Data:" and then continue with your analysis
            7. Goals and Recommendations for the Coming Week: (use bullet points starting with "* " for each recommendation)
               - Start this on a new line with exactly "Goals and Recommendations for the Coming Week:" followed by bullet points
            8. Add a brief motivational closing paragraph (without any heading or label)

            Make it approximately 500-700 words, professional but conversational, and with specific, actionable feedback based on the data that is available.

            If the client is on a weight loss journey, focus on fat loss achievements. If they're on a muscle gain journey, focus on strength improvements and muscle development.

            Be specific, use numbers from the data where appropriate, and provide personalized advice based on their performance.

            IMPORTANT:
            - When mentioning missing data, be encouraging rather than critical.
            - Frame it as an opportunity for improvement rather than a failure.
            - Format the section headings in the exact format "Section Name:" (not with ** asterisks)
            - For weight values, use whole numbers without decimal places (e.g., "93 kg" not "93.2 kg")
            - For the Goals section, use bullet points with "* " at the start of each recommendation
            - DO NOT use a "Closing Statement:" heading, just add a motivational paragraph at the end
            - Throughout the entire review, ONLY use the client's first name when addressing them directly
            """

            print("\n--- Gemini Prompt (Check-in Review) ---")
            print(prompt)

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5000,
                    temperature=0.2  # Lower temperature for more professional, consistent output
                )
            )

            review_content = response.text

            print("\n--- Gemini Response (Check-in Review) ---")
            # Print just the beginning to save space
            print(review_content[:300] + "...")

            logging.info(
                f"Successfully generated check-in review content ({len(review_content)} characters)")
            return review_content

        except Exception as e:
            logging.exception(f"Error generating check-in review content: {e}")
            return None

    def create_checkin_review_pdf(self, client_name, fitness_wrapped_data, review_content):
        """Creates an enhanced professionally formatted PDF document with the check-in review."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.units import inch
            from datetime import datetime

            # Extract first name for personalized references
            first_name = client_name.split()[0]

            # Check which data is actually available
            has_steps_data = fitness_wrapped_data.get('has_steps_data', False)
            has_sleep_data = fitness_wrapped_data.get('has_sleep_data', False)
            has_nutrition_data = fitness_wrapped_data.get(
                'has_nutrition_data', False)
            has_weight_data = fitness_wrapped_data.get(
                'has_weight_data', False)
            has_workout_data = fitness_wrapped_data.get(
                'has_workout_data', False)

            # Generate a filename with date
            today_str = datetime.now().strftime('%Y-%m-%d')
            safe_client_name = client_name.replace(' ', '_')
            pdf_filename = f"{safe_client_name}_{today_str}_check_in_review.pdf"

            logging.info(f"Creating PDF document: {pdf_filename}")

            # Create the document
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading1']
            subheading_style = styles['Heading2']
            normal_style = styles['Normal']

            # Custom styles
            styles.add(ParagraphStyle(
                name='CustomHeading',
                parent=styles['Heading1'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
                fontSize=14,
                fontName='Helvetica-Bold',
                spaceAfter=16,  # Increased spacing
                spaceBefore=12  # Added space before
            ))

            styles.add(ParagraphStyle(
                name='CustomSubHeading',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
                fontSize=12,
                fontName='Helvetica-Bold',
                spaceAfter=10,  # Increased spacing
                spaceBefore=8   # Added space before
            ))

            styles.add(ParagraphStyle(
                name='NoDataStyle',
                parent=styles['Normal'],
                # Gray text for missing data
                textColor=colors.HexColor('#666666'),
                fontName='Helvetica-Oblique',
                spaceAfter=8
            ))

            styles.add(ParagraphStyle(
                name='BulletPoint',
                parent=styles['Normal'],
                leftIndent=30,  # Increased indentation
                firstLineIndent=0,
                bulletIndent=15,
                spaceBefore=2,
                spaceAfter=8,  # Increased spacing between bullets
                bulletFontName='Symbol',
                bulletFontSize=10,
            ))

            styles.add(ParagraphStyle(
                name='Signature',
                parent=styles['Normal'],
                fontName='Helvetica-Oblique',
                alignment=1,  # Center alignment
                spaceAfter=6
            ))

            styles.add(ParagraphStyle(
                name='KeyAchievement',
                parent=styles['Normal'],
                borderColor=colors.HexColor('#229ED4'),
                borderWidth=1,
                borderPadding=8,
                borderRadius=5,
                backgroundColor=colors.HexColor(
                    '#F0F8FF'),  # Light blue background
                textColor=colors.HexColor('#000000'),
                spaceAfter=12
            ))

            # Build the document
            content = []

            # Title - Use full name for the title
            content.append(
                Paragraph(f"Fitness Check-In Review: {client_name}", title_style))
            content.append(Spacer(1, 0.25*inch))

            # Date
            content.append(
                Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            content.append(
                Paragraph(f"Week: {fitness_wrapped_data['date_range']}", normal_style))
            content.append(Spacer(1, 0.25*inch))

            # Key Achievement Box - only for total weight loss with validation
            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                # Only show achievement if it's reasonable
                if total_change > 0 and total_change <= 30:
                    # Round total change to whole number
                    achievement_text = f"🎯 Key Achievement: You've lost {int(abs(total_change))}kg! Keep up the great work!"
                    content.append(Paragraph(achievement_text,
                                             styles['KeyAchievement']))
                    content.append(Spacer(1, 0.15*inch))

            # Table headers with validation
            table_headers = []
            if has_weight_data:
                # Ensure current weight is reasonable
                current_weight = fitness_wrapped_data['current_weight']
                if current_weight >= 40 and current_weight <= 300:
                    table_headers.append("Current Weight")

            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                # Only include total change if it's reasonable
                if abs(total_change) <= 30:
                    table_headers.append("Weight Change")

            if has_workout_data:
                table_headers.append("Workouts This Week")

            if has_workout_data:
                table_headers.append("Total Volume")

            # Corresponding values based on available data, with validation
            table_values = []
            if has_weight_data:
                current_weight = fitness_wrapped_data['current_weight']
                # Only include current weight if it's reasonable
                if current_weight >= 40 and current_weight <= 300:
                    # Round current weight to whole number
                    table_values.append(f"{int(current_weight)} kg")

            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                # Only include total change if it's reasonable
                if abs(total_change) <= 30:
                    # Round total change to whole number
                    table_values.append(
                        f"{int(abs(total_change))} kg {'Loss' if total_change > 0 else 'Gain'}")

            if has_workout_data:
                table_values.append(
                    f"{fitness_wrapped_data['workouts_this_week']}")

            if has_workout_data:
                table_values.append(
                    f"{fitness_wrapped_data['total_weight_lifted']} kg")

            # Only create the table if we have at least one value
            if len(table_headers) > 0:
                data = [table_headers, table_values]

                # Adjust the column widths based on content
                # Make sure "Workouts This Week" has enough space
                col_widths = []
                for header in table_headers:
                    if header == "Current Weight" or header == "Weight Change":
                        col_widths.append(1.1*inch)
                    elif header == "Workouts This Week":
                        # Give more space for this column
                        col_widths.append(1.5*inch)
                    else:
                        col_widths.append(1.1*inch)

                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#229ED4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
                    ('TOPPADDING', (0, 0), (-1, 0), 7),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F0F0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))

                content.append(table)
                content.append(Spacer(1, 0.3*inch))

            # Review content
            content.append(
                Paragraph("CHECK-IN REVIEW", styles['CustomHeading']))

            # Process the review content to replace ** with bold formatting
            # and handle section headings properly, and use first name instead of full name
            processed_content = ""
            goals_section = False
            closing_statement = ""
            closing_found = False
            goals_content = ""
            bulleted_goals = []

            # Replace any instances of the full name with just the first name in the review content
            review_content = review_content.replace(client_name, first_name)

            paragraphs = review_content.split('\n\n')

            for para in paragraphs:
                if para.strip():
                    # Remove ** markers and use proper formatting
                    para = para.replace(
                        "**Weight Management Analysis:**", "Weight Management Analysis:")
                    para = para.replace(
                        "**Training Performance Analysis:**", "Training Performance Analysis:")
                    para = para.replace(
                        "**Nutrition and Lifestyle Observations:**", "Nutrition and Lifestyle Observations:")
                    para = para.replace(
                        "**Specific Exercise Achievements:**", "Specific Exercise Achievements:")
                    para = para.replace(
                        "**Missing Data and Its Benefits:**", "Missing Data and Its Benefits:")

                    # Handle goals and closing statement sections
                    if "Goals and Recommendations" in para or "Goals and Recommendations for the Coming Week" in para:
                        goals_section = True
                        # Don't add this to processed content since we'll handle it separately
                        continue
                    # Handle the goals section bullets
                    elif goals_section:
                        # If this paragraph is after the goals heading, treat the entire paragraph as potential bullet points
                        if para.strip().startswith("*"):
                            # Original case: paragraph starts with *
                            bullet_points = para.split('\n* ')
                            for i, point in enumerate(bullet_points):
                                if i > 0 or point.startswith('*'):
                                    point_text = point.strip().lstrip('* ')
                                    # Make sure all bullet points end with a period
                                    if not point_text.endswith('.'):
                                        point_text += '.'
                                    bulleted_goals.append(point_text)
                        else:
                            # If we're in goals section but there are no asterisks, create bullet points from each line
                            # This handles cases where Gemini might not format bullet points exactly as requested
                            for line in para.split('\n'):
                                line = line.strip()
                                if line:  # Skip empty lines
                                    # Make sure all bullet points end with a period
                                    if not line.endswith('.'):
                                        line += '.'
                                    bulleted_goals.append(line)
                        continue
                    # If we find a closing statement, save it
                    elif "Closing Statement" in para:
                        closing_found = True
                        closing_statement = para.replace(
                            "Closing Statement:", "").strip()
                        continue
                    # Normal paragraph - add to processed content
                    else:
                        processed_content += para + "\n\n"

            # Add the processed paragraphs
            paragraphs = processed_content.split('\n\n')
            for para in paragraphs:
                if para.strip():  # Skip empty paragraphs
                    # Check if this paragraph is a section heading
                    section_headings = [
                        "Weight Management Analysis:",
                        "Training Performance Analysis:",
                        "Nutrition and Lifestyle Observations:",
                        "Specific Exercise Achievements:",
                        "Missing Data:"
                    ]

                    is_heading = False
                    for heading in section_headings:
                        if para.startswith(heading):
                            # Split the heading from the content
                            heading_text = heading
                            remaining_text = para[len(heading):].strip()

                            # Add the heading in blue
                            content.append(
                                Paragraph(heading_text, styles['CustomSubHeading']))
                            # Small space after heading
                            content.append(Spacer(1, 0.1*inch))

                            # Add the remaining text as normal paragraph
                            if remaining_text:
                                content.append(
                                    Paragraph(remaining_text, normal_style))
                                # Space after paragraph
                                content.append(Spacer(1, 0.2*inch))

                            is_heading = True
                            break

                    # If not a heading, add as normal paragraph
                    if not is_heading:
                        content.append(Paragraph(para, normal_style))
                        # Increased spacing
                        content.append(Spacer(1, 0.2*inch))

            # Add Goals and Recommendations section
            content.append(Paragraph(
                "Goals and Recommendations for the Coming Week:", styles['CustomSubHeading']))

            # Add bullet points with consistent formatting
            for bullet in bulleted_goals:
                content.append(Paragraph(f"• {bullet}", styles['BulletPoint']))

            # Add a big gap after the goals section
            # Extra large space after goals section
            content.append(Spacer(1, 0.5*inch))

            # Add Closing Statement if we have one, but don't label it as "Closing Statement"
            if closing_statement:
                content.append(Paragraph(closing_statement, normal_style))
                content.append(Spacer(1, 0.25*inch))

            # Add a horizontal rule to separate content from summary
            content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(
                '#CCCCCC'), spaceBefore=10, spaceAfter=10))
            content.append(Spacer(1, 0.25*inch))

            # Nutrition & Lifestyle - only include sections with data (with better spacing)
            content.append(
                Paragraph("NUTRITION & LIFESTYLE", styles['CustomHeading']))

            lifestyle_stats = ""
            if has_nutrition_data and fitness_wrapped_data['calories_consumed'] != "Not Recorded":
                lifestyle_stats += f"Average Daily Calories: {fitness_wrapped_data['calories_consumed']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Calories: <i>Not Recorded</i> - Tracking your calories helps us optimize your nutrition plan<br/>"

            if has_steps_data and fitness_wrapped_data['step_count'] != "Not Recorded":
                if fitness_wrapped_data['step_count'] == "Available but sporadic":
                    lifestyle_stats += f"Average Daily Steps: <i>Available but sporadic</i> - Please track steps more consistently for better insights<br/>"
                else:
                    lifestyle_stats += f"Average Daily Steps: {fitness_wrapped_data['step_count']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Steps: <i>Not Recorded</i> - Recording steps helps us monitor your daily activity level<br/>"

            if has_sleep_data and fitness_wrapped_data['sleep_hours'] != "Not Recorded":
                if fitness_wrapped_data['sleep_hours'] == "Minimal Data Available":
                    lifestyle_stats += f"Sleep Pattern: <i>Minimal Data Available</i> - Please track sleep more consistently for better insights<br/>"
                else:
                    lifestyle_stats += f"Sleep Pattern: {fitness_wrapped_data['sleep_hours']}<br/>"
            else:
                lifestyle_stats += f"Sleep Pattern: <i>Not Recorded</i> - Tracking sleep helps us ensure you're recovering properly<br/>"

            if has_weight_data:
                # Round weight values to whole numbers
                start_weight = int(fitness_wrapped_data['start_weight'])
                current_weight = int(fitness_wrapped_data['current_weight'])
                total_change = abs(fitness_wrapped_data['total_weight_change'])

                lifestyle_stats += f"Starting Weight: {start_weight} kg<br/>"
                lifestyle_stats += f"Current Weight: {current_weight} kg<br/>"
                lifestyle_stats += f"Total Change: {int(total_change)} kg {'Loss' if fitness_wrapped_data['total_weight_change'] > 0 else 'Gain'}<br/>"
            else:
                lifestyle_stats += f"Weight Data: <i>Not Recorded</i> - Regular weigh-ins help us track your progress toward your goals<br/>"

            content.append(Paragraph(lifestyle_stats, normal_style))
            content.append(Spacer(1, 0.25*inch))

            # WEIGHT PROGRESS section - with modified weight goal handling and validation
            content.append(
                Paragraph("WEIGHT PROGRESS", styles['CustomHeading']))

            if has_weight_data:
                # Get the weight goal and make sure we handle the False case
                client_weight_goal = fitness_wrapped_data.get(
                    'weight_goal', False)

                # Get the weight values with validation
                start_weight = fitness_wrapped_data['start_weight']
                current_weight = fitness_wrapped_data['current_weight']
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)

                # Validate the weights
                if start_weight < 40 or start_weight > 300:
                    start_weight = 95.0  # Reasonable fallback
                if current_weight < 40 or current_weight > 300:
                    current_weight = 90.0  # Reasonable fallback
                if abs(total_change) > 30:
                    total_change = 5.0 if total_change > 0 else -5.0

                # Build the weight progress text - simplified to focus on total change only and round down all values
                weight_progress = f"""
                Starting Weight: {int(start_weight)} kg<br/>
                Current Weight: {int(current_weight)} kg<br/>
                Total Change: {int(abs(total_change))} kg {'Loss' if total_change > 0 else 'Gain'}<br/>
                """

                # Only add the weight goal line if it's a valid number (not False) and reasonable
                if client_weight_goal is not False and isinstance(client_weight_goal, dict) and 'target' in client_weight_goal:
                    weight_goal_target = client_weight_goal['target']
                    if weight_goal_target >= 40 and weight_goal_target <= 300:
                        weight_progress += f"Weight Goal: {int(weight_goal_target)} kg<br/>"
                        logging.info(
                            f"Including weight goal in PDF: {int(weight_goal_target)}")
                else:
                    logging.info(
                        "Skipping weight goal in PDF as it's set to False or unreasonable")

                content.append(Paragraph(weight_progress, normal_style))
            else:
                content.append(Paragraph(
                    "No weight data recorded for this week. Regular weight tracking is essential for monitoring progress toward your goals.", styles['NoDataStyle']))

            # Add missing data section if applicable
            missing_data_types = []
            if not has_weight_data or fitness_wrapped_data.get('current_weight', 'Not Recorded') == 'Not Recorded':
                missing_data_types.append("weight")
            if not has_workout_data:
                missing_data_types.append("workout")
            if not has_nutrition_data or fitness_wrapped_data.get('calories_consumed', 'Not Recorded') == 'Not Recorded':
                missing_data_types.append("nutrition")
            if not has_steps_data or fitness_wrapped_data.get('step_count', 'Not Recorded') == 'Not Recorded':
                missing_data_types.append("steps")
            if not has_sleep_data or fitness_wrapped_data.get('sleep_hours', 'Not Recorded') == 'Not Recorded':
                missing_data_types.append("sleep")

            if missing_data_types:
                content.append(Spacer(1, 0.25*inch))
                content.append(
                    Paragraph("MISSING DATA INSIGHTS", styles['CustomHeading']))

                missing_data_paragraph = "To enhance your training experience and get more personalized coaching, please consider tracking the following data:<br/><br/>"

                for data_type in missing_data_types:
                    if data_type == "weight":
                        missing_data_paragraph += "• <b>Weight tracking</b>: Regular weigh-ins help us monitor progress and adjust your plan as needed.<br/>"
                    elif data_type == "workout":
                        missing_data_paragraph += "• <b>Workout logging</b>: Recording your workouts helps us assess your training consistency and progress.<br/>"
                    elif data_type == "nutrition":
                        missing_data_paragraph += "• <b>Nutrition tracking</b>: Logging your calories and macros helps us optimize your diet for your goals.<br/>"
                    elif data_type == "steps":
                        missing_data_paragraph += "• <b>Step counting</b>: Tracking daily steps gives us insight into your overall activity levels.<br/>"
                    elif data_type == "sleep":
                        missing_data_paragraph += "• <b>Sleep logging</b>: Recording sleep helps us ensure you're getting enough recovery time.<br/>"

                missing_data_paragraph += "<br/>Consistent tracking of these metrics will help us provide you with more accurate feedback and guidance. Let us know if you need help setting up any of these tracking methods!"

                content.append(Paragraph(missing_data_paragraph, normal_style))

            # Add signature
            # Increased spacing before signature
            content.append(Spacer(1, 0.75*inch))
            content.append(
                Paragraph("Coco's Connected/Shannon Birch", styles['Signature']))

            # Build the PDF
            doc.build(content)
            logging.info(f"PDF document created successfully: {pdf_filename}")
            return pdf_filename

        except ImportError as ie:
            logging.error(f"Missing required library for PDF generation: {ie}")
            print(f"Please install missing library: {ie}")
            return None
        except Exception as e:
            logging.exception(f"Error creating check-in review PDF: {e}")
            return None

    def find_most_improved_client(self, all_client_data):
        """Determines the most improved client based on workload increase percentage.

        Args:
            all_client_data: Dictionary with client names as keys and their check-in data as values

        Returns:
            Tuple(most_improved_name, improvement_percentage) or (None, 0) if no valid data
        """
        try:
            logging.info(
                "Finding most improved client based on workload increases...")

            # Track the client with the highest workload increase
            most_improved_name = None
            highest_increase = -float('inf')  # Start with negative infinity

            for client_name, client_data in all_client_data.items():
                if 'fitness_wrapped_data' in client_data:
                    fitness_data = client_data['fitness_wrapped_data']

                    # Check if the client has valid workload data
                    if (fitness_data.get('has_workload_data', False) and
                        'workload_increase' in fitness_data and
                            isinstance(fitness_data['workload_increase'], (int, float))):

                        workload_increase = fitness_data['workload_increase']
                        logging.info(
                            f"Client: {client_name}, Workload Increase: {workload_increase}%")

                        # Update most improved if this client has a higher increase
                        if workload_increase > highest_increase:
                            highest_increase = workload_increase
                            most_improved_name = client_name

            if most_improved_name:
                logging.info(
                    f"Most improved client: {most_improved_name} with {highest_increase}% workload increase")
            else:
                logging.warning(
                    "No clients with valid workload increase data found")

            return (most_improved_name, highest_increase)

        except Exception as e:
            logging.exception(f"Error finding most improved client: {e}")
            return (None, 0)

    def update_json_files_with_most_improved(self, most_improved_info, client_names):
        """Updates all client JSON files with most improved client information.

        Args:
            most_improved_info: Tuple(
                most_improved_name, improvement_percentage)
            client_names: List of client names to update

        Returns:
            Boolean indicating success
        """
        try:
            logging.info(
                "Updating all client JSON files with most improved client information...")
            most_improved_name, improvement_percentage = most_improved_info

            if not most_improved_name:
                logging.warning("No most improved client information to add")
                return False

            for client_name in client_names:
                # Construct the filename pattern - look for the most recent file for this client
                pattern = f"{client_name.replace(' ', '_')}_*_fitness_wrapped_data.json"
                matching_files = sorted(
                    glob.glob(pattern), reverse=True)  # Most recent first

                if not matching_files:
                    logging.warning(
                        f"No JSON file found for client: {client_name}")
                    continue

                latest_file = matching_files[0]
                logging.info(f"Updating file: {latest_file}")

                # Read the existing JSON data
                with open(latest_file, 'r') as f:
                    client_data = json.load(f)

                # Add most improved client information
                client_data['most_improved_client'] = {
                    'name': most_improved_name,
                    'improvement_percentage': improvement_percentage,
                    'is_current_client_most_improved': (client_name == most_improved_name)
                }

                # Write the updated data back to the file
                with open(latest_file, 'w') as f:
                    json.dump(client_data, f, indent=4)

                logging.info(
                    f"Successfully updated JSON file for {client_name}")

            return True

        except Exception as e:
            logging.exception(
                f"Error updating JSON files with most improved client: {e}")
            return False

    def display_workout_statistics(self, workout_data_list):
        """Display comprehensive workout statistics in the console.

        Args:
            workout_data_list: List of workout dictionaries containing exercise data
        """
        try:
            if not workout_data_list:
                print("\n" + "="*80)
                print("NO WORKOUT DATA FOUND")
                print("="*80)
                return

            # Last week instead of current week
            today = datetime.now().date()
            # Monday of current week
            start_date = today - timedelta(days=today.weekday())
            # Sunday of current week
            end_date = start_date + timedelta(days=6)

            # Previous week's date range
            prev_start_date = start_date - timedelta(weeks=1)
            prev_end_date = end_date - timedelta(weeks=1)

            # Get stats for current and previous week
            current_week_stats = self.calculate_workout_stats_for_date_range(
                workout_data_list, start_date, end_date)
            prev_week_stats = self.calculate_workout_stats_for_date_range(
                workout_data_list, prev_start_date, prev_end_date)

            # Unpack stats
            current_workout_count, current_workout_names, current_weight, current_reps, current_sets, _, _ = current_week_stats
            prev_workout_count, prev_workout_names, prev_weight, prev_reps, prev_sets, _, _ = prev_week_stats

            # Calculate changes
            weight_change = current_weight - prev_weight
            weight_change_pct = (
                weight_change / prev_weight * 100) if prev_weight > 0 else 0
            reps_change = current_reps - prev_reps
            reps_change_pct = (reps_change / prev_reps *
                               100) if prev_reps > 0 else 0
            sets_change = current_sets - prev_sets
            sets_change_pct = (sets_change / prev_sets *
                               100) if prev_sets > 0 else 0

            # Display summary statistics
            print("\n" + "="*80)
            print(f"{'WORKOUT STATISTICS SUMMARY':^80}")
            print("="*80)

            print(
                f"\nCURRENT WEEK ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b')})")
            print(f"  Total Workouts: {current_workout_count}")
            print(f"  Total Weight Lifted: {current_weight:,.2f} kg")
            print(f"  Total Reps: {current_reps:,}")
            print(f"  Total Sets: {current_sets:,}")

            print(
                f"\nPREVIOUS WEEK ({prev_start_date.strftime('%d %b')} - {prev_end_date.strftime('%d %b')})")
            print(f"  Total Workouts: {prev_workout_count}")
            print(f"  Total Weight Lifted: {prev_weight:,.2f} kg")
            print(f"  Total Reps: {prev_reps:,}")
            print(f"  Total Sets: {prev_sets:,}")

            print("\nWEEK-OVER-WEEK CHANGES")
            print(
                f"  Weight Change: {weight_change:,.2f} kg ({weight_change_pct:+.2f}%)")
            print(f"  Reps Change: {reps_change:+,} ({reps_change_pct:+.2f}%)")
            print(f"  Sets Change: {sets_change:+,} ({sets_change_pct:+.2f}%)")

            # Display current week workouts
            print("\n" + "-"*80)
            print(f"{'CURRENT WEEK WORKOUTS':^80}")
            print("-"*80)

            if current_workout_names:
                for i, name in enumerate(current_workout_names, 1):
                    print(f"  {i}. {name}")
            else:
                print("  No workouts completed this week")

            # Find top exercises from this week
            print("\n" + "-"*80)
            print(f"{'TOP EXERCISES THIS WEEK':^80}")
            print("-"*80)

            # Extract all exercises from current week workouts
            exercise_stats = {}
            for workout in workout_data_list:
                workout_date = None
                try:
                    # Parse the date
                    date_str = workout['date']
                    workout_date = datetime.strptime(
                        date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        workout_date = datetime.strptime(
                            date_str, '%d %b %Y').date()
                    except:
                        continue

                # Skip if not in current week
                if not (start_date <= workout_date <= end_date):
                    continue

                for exercise in workout['exercises']:
                    ex_name = exercise['name'].strip()
                    if ex_name not in exercise_stats:
                        exercise_stats[ex_name] = {
                            'total_weight': 0,
                            'total_reps': 0,
                            'total_sets': 0,
                            'max_weight': 0
                        }

                    # Update stats
                    for set_data in exercise['sets']:
                        weight = set_data['weight']
                        reps = set_data['reps']

                        exercise_stats[ex_name]['total_weight'] += weight * reps
                        exercise_stats[ex_name]['total_reps'] += reps
                        exercise_stats[ex_name]['total_sets'] += 1
                        exercise_stats[ex_name]['max_weight'] = max(
                            exercise_stats[ex_name]['max_weight'], weight)

            # Sort exercises by total weight and display top 5
            top_exercises = sorted(exercise_stats.items(
            ), key=lambda x: x[1]['total_weight'], reverse=True)[:5]

            if top_exercises:
                for i, (name, stats) in enumerate(top_exercises, 1):
                    print(f"  {i}. {name}")
                    print(
                        f"     • Total Volume: {stats['total_weight']:,.2f} kg")
                    print(f"     • Max Weight: {stats['max_weight']:.2f} kg")
                    print(f"     • Total Reps: {stats['total_reps']}")
                    print(f"     • Total Sets: {stats['total_sets']}")
                    print()
            else:
                print("  No exercise data available for this week")

            print("="*80)

        except Exception as e:
            logging.exception(f"Error displaying workout statistics: {e}")
            print("\nERROR: Failed to display workout statistics. See logs for details.")

    # The best solution is to fix the prepare_fitness_wrapped_data function
# to ensure consistent key naming throughout the application

    def prepare_fitness_wrapped_data(self, client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis,
                                     steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data,
                                     workouts_completed_analysis, total_workout_stats_analysis, workout_data_list):
        """Convert Trainerize data into the format expected by FitnessWrappedGenerator with improved weight handling."""
        import re
        from datetime import datetime, timedelta, date
        import logging

        # Initialize nutrition tracking consistency indicators
        nutrition_tracking_consistent = True
        nutrition_tracking_days = 0
        nutrition_consistency_message = ""

        # Check for consistency message in nutrition analysis
        consistency_warning_match = re.search(
            r"⚠️\s*\*\*Nutrition Tracking Alert\*\*:\s*(.*?)(?:\n|\Z)", nutrition_analysis, re.DOTALL)
        if consistency_warning_match:
            nutrition_consistency_message = consistency_warning_match.group(
                1).strip()
            nutrition_tracking_consistent = False

            # Try to extract the number of days tracked if available
            days_tracked_match = re.search(
                r"only tracked (\d+) day", nutrition_consistency_message)
            if days_tracked_match and days_tracked_match.group(1).isdigit():
                nutrition_tracking_days = int(days_tracked_match.group(1))
                logging.info(
                    f"Extracted nutrition tracking days: {nutrition_tracking_days}")

            logging.info(
                f"Found nutrition consistency warning: {nutrition_consistency_message}")

        # Debug logging for analysis text
        logging.info(f"===== PROCESSING WEIGHT DATA FOR {client_name} =====")
        logging.info(
            f"Raw bodyweight analysis excerpt: {bodyweight_analysis[:500]}")

        # Extract data from analytics
        weight_history = self.extract_weight_history(bodyweight_analysis)
        weight_goal = self.extract_weight_goal(weight_goal_text)

        # Get metadata from weight extraction
        if hasattr(self, 'weight_data_metadata'):
            weight_trend = self.weight_data_metadata.get('trend')
            start_date = self.weight_data_metadata.get('start_date')
            current_date = self.weight_data_metadata.get('current_date')
            logging.info(
                f"Weight metadata - Trend: {weight_trend}, Start date: {start_date}, Current date: {current_date}")
        else:
            weight_trend = None
            start_date = None
            current_date = None

        # Log the extracted data
        logging.info(f"Extracted weight history: {weight_history}")
        logging.info(f"Extracted weight goal: {weight_goal}")

        # Weight handling with improved validation
        start_weight = None
        current_weight = None
        total_weight_change = None
        has_reliable_weight_data = False

        # Process weight history
        if weight_history and len(weight_history) >= 2:
            # Use the first weight as starting weight and last as current
            start_weight = weight_history[0]
            current_weight = weight_history[-1]

            # Ensure values are floats
            if isinstance(start_weight, str):
                try:
                    start_weight = float(start_weight)
                except ValueError:
                    logging.warning(
                        f"Could not convert start_weight to float: {start_weight}")
                    start_weight = None

            if isinstance(current_weight, str):
                try:
                    current_weight = float(current_weight)
                except ValueError:
                    logging.warning(
                        f"Could not convert current_weight to float: {current_weight}")
                    current_weight = None

            # Check if we have valid weights
            if start_weight is not None and current_weight is not None:
                # More relaxed validation - wider weight range and greater allowed change
                if (30 <= start_weight <= 250 and
                    30 <= current_weight <= 250 and
                        abs(start_weight - current_weight) <= 50):  # Allow larger changes

                    # Use trend information if available to ensure correct direction
                    if weight_trend == "downward" and start_weight < current_weight:
                        logging.warning(
                            "Weight trend is downward but start < current, swapping values")
                        start_weight, current_weight = current_weight, start_weight
                    elif weight_trend == "upward" and start_weight > current_weight:
                        logging.warning(
                            "Weight trend is upward but start > current, swapping values")
                        start_weight, current_weight = current_weight, start_weight

                    # Calculate weight change (positive = weight loss)
                    total_weight_change = start_weight - current_weight

                    # Log the weight values and change
                    logging.info(
                        f"Valid weight data: Start={start_weight}kg, Current={current_weight}kg")
                    logging.info(
                        f"Weight change: {total_weight_change}kg ({total_weight_change > 0 and 'loss' or 'gain'})")

                    has_reliable_weight_data = True
                else:
                    # Log specific validation failures
                    if not (30 <= start_weight <= 250):
                        logging.warning(
                            f"Start weight {start_weight}kg outside valid range (30-250kg)")
                    if not (30 <= current_weight <= 250):
                        logging.warning(
                            f"Current weight {current_weight}kg outside valid range (30-250kg)")
                    if abs(start_weight - current_weight) > 50:
                        logging.warning(
                            f"Weight change {abs(start_weight - current_weight)}kg exceeds maximum allowed (50kg)")
            else:
                logging.warning(
                    "Start or current weight is None after conversion attempt")
        else:
            logging.warning(
                f"Insufficient weight history data: {weight_history}")

        # Handle weight goal
        client_weight_goal = False  # Default to False (don't display)
        if weight_goal and 'target' in weight_goal:
            try:
                client_weight_goal = float(weight_goal['target'])
                if not (30 <= client_weight_goal <= 250):
                    logging.warning(
                        f"Weight goal {client_weight_goal}kg outside reasonable range (30-250kg)")
                    client_weight_goal = False
                else:
                    logging.info(f"Valid weight goal: {client_weight_goal}kg")
            except (ValueError, TypeError) as e:
                logging.warning(f"Error converting weight goal: {e}")
                client_weight_goal = False

        # Calculate date ranges for workouts
        today = datetime.now().date()  # Current date (not last week)
        current_week_start = today - \
            timedelta(days=today.weekday())  # Monday of current week
        current_week_end = current_week_start + \
            timedelta(days=6)     # Sunday of current week

        # Calculate previous week's date range
        previous_week_start = current_week_start - timedelta(weeks=1)
        previous_week_end = current_week_end - timedelta(weeks=1)

        # Parse workout stats for current week with dynamically calculated dates
        current_week_workout_count, workout_names, total_weight, total_reps, total_sets, _, _ = self.calculate_workout_stats_for_date_range(
            workout_data_list, current_week_start, current_week_end
        )

        # Parse workout stats for previous week
        _, _, prev_week_weight, _, _, _, _ = self.calculate_workout_stats_for_date_range(
            workout_data_list, previous_week_start, previous_week_end
        )

        # Calculate workload increase
        workload_increase = 0
        if prev_week_weight > 0:
            workload_increase = (
                (total_weight - prev_week_weight) / prev_week_weight) * 100
            # Cap at reasonable values
            workload_increase = max(min(workload_increase, 300), -100)

        # Format date range
        today = datetime.now().date()  # Current date (not last week)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Windows-compatible date formatting (remove leading zeros manually)
        start_day = start_of_week.strftime('%d %B').lstrip('0')
        end_day = end_of_week.strftime('%d %B').lstrip('0')
        date_range = f"{start_day} - {end_day}"

        # Create custom weight message - only create if data is reliable
        if has_reliable_weight_data:
            if total_weight_change and total_weight_change > 0:
                current_weight_message = f"Your progress is fantastic! You've lost a total of {total_weight_change:.1f}kg, which is awesome! Keep doing what you're doing!"
            elif total_weight_change and total_weight_change < 0:
                current_weight_message = f"You've gained a total of {abs(total_weight_change):.1f}kg, which is great progress toward your muscle building goal!"
            else:
                current_weight_message = "Weight's trending well with your fitness goals. Keep up the good work!"
        else:
            current_weight_message = "Keep up the good work with your fitness journey! Your consistency is key to success."

        # Check if progress photos are up-to-date
        has_up_to_date_photos = False
        if photos_analysis and ("up-to-date" in photos_analysis.lower() or
                                "looking great" in photos_analysis.lower() or
                                "awesome progress" in photos_analysis.lower() or
                                "uploaded this week" in photos_analysis.lower()):
            has_up_to_date_photos = True
        print(f"Progress photos up-to-date: {has_up_to_date_photos}")

        # Check for real data vs defaults
        has_real_data = {
            "weight": has_reliable_weight_data,
            "steps": False,
            "sleep": False,
            "nutrition": False
        }

        # Extract step count and sleep hours from analysis
        step_count = "Not Recorded"
        meets_10k_goal = "Not Recorded"
        average_steps = "Not Recorded"
        highest_steps = "Not Recorded"
        lowest_steps = "Not Recorded"
        steps_trend = "Not Recorded"

        # First check if steps data is explicitly marked as available
        steps_available_match = re.search(
            r"AVAILABLE_STEPS_DATA:\s*(yes|no)", steps_analysis, re.IGNORECASE)
        if steps_available_match and steps_available_match.group(1).lower() == "yes":
            has_real_data["steps"] = True
            logging.info("Steps data explicitly marked as available")

            # Check for sporadic data message
            if "sporadic" in steps_analysis.lower() and "encourage more consistent" in steps_analysis.lower():
                step_count = "Available but sporadic"
                has_real_data["steps"] = True
                logging.info("Steps data is available but sporadic")
            else:
                # Continue with normal extraction...
                # First check for structured data format
                steps_structured_data_match = re.search(
                    r"```data\s+(.*?)\s+```", steps_analysis, re.DOTALL)
                if steps_structured_data_match:
                    logging.info("Found structured steps data format")
                    steps_structured_data = steps_structured_data_match.group(
                        1)

                    # Extract structured steps data
                    meets_10k_goal_match = re.search(
                        r"MEETS_10K_GOAL:\s*([^\n]*)", steps_structured_data)
                    if meets_10k_goal_match and meets_10k_goal_match.group(1).lower() != "not visible":
                        meets_10k_goal = meets_10k_goal_match.group(1).lower()
                        has_real_data["steps"] = True
                        logging.info(
                            f"Extracted MEETS_10K_GOAL: {meets_10k_goal}")

                    average_steps_match = re.search(
                        r"AVERAGE_STEPS:\s*([^\n]*)", steps_structured_data)
                    if average_steps_match and average_steps_match.group(1).lower() != "not visible":
                        average_steps = average_steps_match.group(1)
                        step_count = average_steps  # Use average steps as the main step count
                        has_real_data["steps"] = True
                        logging.info(
                            f"Extracted AVERAGE_STEPS: {average_steps}")

                    highest_steps_match = re.search(
                        r"HIGHEST_STEPS:\s*([^\n]*)", steps_structured_data)
                    if highest_steps_match and highest_steps_match.group(1).lower() != "not visible":
                        highest_steps = highest_steps_match.group(1)
                        logging.info(
                            f"Extracted HIGHEST_STEPS: {highest_steps}")

                    trend_match = re.search(
                        r"TREND:\s*([^\n]*)", steps_structured_data)
                    if trend_match:
                        steps_trend = trend_match.group(1).lower()
                        logging.info(f"Extracted steps TREND: {steps_trend}")
                else:
                    # Fallback to the old regex for backward compatibility
                    logging.info(
                        "Structured steps data not found, trying old regex pattern")
                    step_match = re.search(
                        r"(\d{1,2}[,.]?\d{0,3}k)", steps_analysis)
                    if step_match:
                        step_count = step_match.group(1)
                        has_real_data["steps"] = True
                        logging.info(
                            f"Found steps data with fallback pattern: {step_count}")
        # First check for structured data format
        steps_structured_data_match = re.search(
            r"```data\s+(.*?)\s+```", steps_analysis, re.DOTALL)
        if steps_structured_data_match:
            logging.info("Found structured steps data format")
                    steps_structured_data = steps_structured_data_match.group(
                        1)

            # Extract structured steps data
            meets_10k_match = re.search(
                r"MEETS_10K_GOAL:\s+(consistently|sometimes|rarely|never)", steps_structured_data, re.IGNORECASE)
            if meets_10k_match:
                meets_10k_goal = meets_10k_match.group(1).lower()
                has_real_data["steps"] = True
                        logging.info(
                            f"Extracted MEETS_10K_GOAL: {meets_10k_goal}")

            average_steps_match = re.search(
                r"AVERAGE_STEPS:\s+(not visible|\d+[,.]?\d*k?)", steps_structured_data, re.IGNORECASE)
            if average_steps_match and average_steps_match.group(1).lower() != "not visible":
                average_steps = average_steps_match.group(1)
                step_count = average_steps  # Use average steps as the main step count
                has_real_data["steps"] = True
                        logging.info(
                            f"Extracted AVERAGE_STEPS: {average_steps}")

            highest_steps_match = re.search(
                r"HIGHEST_STEPS:\s+(not visible|\d+[,.]?\d*k?)", steps_structured_data, re.IGNORECASE)
            if highest_steps_match and highest_steps_match.group(1).lower() != "not visible":
                highest_steps = highest_steps_match.group(1)
                        logging.info(
                            f"Extracted HIGHEST_STEPS: {highest_steps}")

            trend_match = re.search(
                r"TREND:\s+(improving|declining|consistent|inconsistent)", steps_structured_data, re.IGNORECASE)
            if trend_match:
                steps_trend = trend_match.group(1).lower()
                logging.info(f"Extracted steps TREND: {steps_trend}")
        else:
            # Fallback to the old regex for backward compatibility
                    step_match = re.search(
                        r"(\d{1,2}[,.]?\d{0,3}k)", steps_analysis)
            if step_match:
                step_count = step_match.group(1)
                has_real_data["steps"] = True
                logging.info(
                    f"Extracted step count using fallback regex: {step_count}")
        elif "No steps data available" in steps_analysis:
            has_real_data["steps"] = False
            logging.info("No steps data available message found")

        sleep_hours = "Not Recorded"
        sleep_match = re.search(
            r"(\d{1,2}-\d{1,2})\s*hours", sleep_analysis, re.IGNORECASE)
        if sleep_match:
            sleep_hours = sleep_match.group(0)
            has_real_data["sleep"] = True
        # Check for minimal data message
        elif "minimal sleep data available" in sleep_analysis.lower():
            sleep_hours = "Minimal Data Available"
            has_real_data["sleep"] = False

        # Extract average calorie info
        calories_consumed = "Not Recorded"
        protein_consumed = "Not Recorded"
        fats_consumed = "Not Recorded"
        carbs_consumed = "Not Recorded"

        # Look for structured data format
        structured_data_match = re.search(
            r"```data\s+(.*?)\s+```", nutrition_analysis, re.DOTALL)
        if structured_data_match:
            structured_data = structured_data_match.group(1)
            logging.info(f"Found structured nutrition data: {structured_data}")

            # Extract each value from the structured format - updated to better handle "not visible" and values with 'g' suffix
            calories_match = re.search(
                r"CALORIES_DAILY:\s+(not visible|\d+)", structured_data, re.IGNORECASE)
            if calories_match:
                calories_value = calories_match.group(1)
                if calories_value.lower() != "not visible":
                    calories_consumed = calories_value
                    has_real_data["nutrition"] = True
                logging.info(
                    f"Extracted calories from structured data: {calories_consumed}")

            protein_match = re.search(
                r"PROTEIN_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
            if protein_match:
                protein_value = protein_match.group(1)
                if protein_value.lower() != "not visible":
                    # Add 'g' suffix if not already present
                    if not protein_value.endswith('g'):
                        protein_consumed = f"{protein_value}g"
                    else:
                        protein_consumed = protein_value
                    has_real_data["nutrition"] = True
                logging.info(
                    f"Extracted protein from structured data: {protein_consumed}")

            fats_match = re.search(
                r"FATS_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
            if fats_match:
                fats_value = fats_match.group(1)
                if fats_value.lower() != "not visible":
                    # Add 'g' suffix if not already present
                    if not fats_value.endswith('g'):
                        fats_consumed = f"{fats_value}g"
                    else:
                        fats_consumed = fats_value
                    has_real_data["nutrition"] = True
                logging.info(
                    f"Extracted fats from structured data: {fats_consumed}")

            carbs_match = re.search(
                r"CARBS_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
            if carbs_match:
                carbs_value = carbs_match.group(1)
                if carbs_value.lower() != "not visible":
                    # Add 'g' suffix if not already present
                    if not carbs_value.endswith('g'):
                        carbs_consumed = f"{carbs_value}g"
                    else:
                        carbs_consumed = carbs_value
                    has_real_data["nutrition"] = True
                logging.info(
                    f"Extracted carbs from structured data: {carbs_consumed}")

            # If we found any structured data for fats or carbs, set the nutrition flag to true
            # This ensures we include nutrition data in the PDF even if not all values are available
            if fats_match or carbs_match:
                has_real_data["nutrition"] = True
                logging.info(
                    "Setting nutrition data flag to true based on fats/carbs data")
        else:
            # Fall back to previous regex methods if structured data not found
            logging.warning(
                "Structured nutrition data format not found, using fallback extraction")

            # Updated regex patterns to match Gemini's output format
            # Try to extract average calories from nutrition analysis
            avg_calories_match = re.search(
                r"(?:average|daily|approximately|around|about)\s*(?:of|is|at)?\s*(?:calorie|calories)\s*(?:intake|consumption|is)?\s*(?:of|is|at)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,4})(?:\*\*)?\s*(?:calories|kcal)?|(?:calorie|calories)\s*(?:intake|consumption)?\s*(?:of|is|at|around|about)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,4})(?:\*\*)?\s*(?:calories|kcal)?",
                nutrition_analysis, re.IGNORECASE)

            if avg_calories_match:
                try:
                    matched_group = next(
                        g for g in avg_calories_match.groups() if g is not None)
                    calories_consumed = matched_group
                    has_real_data["nutrition"] = True
                    logging.info(
                        f"Found average calories: {calories_consumed}")
                except (ValueError, TypeError, StopIteration):
                    logging.warning("Could not parse average calories")

            # Extract protein data - updated pattern
            protein_match = re.search(
                r"(?:average|daily|approximately|around|about)\s*(?:of|is|at)?\s*(?:protein)\s*(?:intake|consumption|is)?\s*(?:of|is|at)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?|(?:protein)\s*(?:intake|consumption)?\s*(?:of|is|at|around|about)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?",
                nutrition_analysis, re.IGNORECASE)

            if protein_match:
                try:
                    # Use the first non-None capture group
                    protein_value = next(
                        g for g in protein_match.groups() if g is not None)
                    protein_consumed = f"{protein_value}g"
                    logging.info(f"Found protein intake: {protein_consumed}")
                except (ValueError, TypeError, StopIteration):
                    logging.warning("Could not parse protein intake")

            # Extract fats data - updated pattern
            fats_match = re.search(
                r"(?:average|daily|approximately|around|about)\s*(?:of|is|at)?\s*(?:fat|fats)\s*(?:intake|consumption|is)?\s*(?:of|is|at)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?|(?:fat|fats)\s*(?:intake|consumption)?\s*(?:of|is|at|around|about)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?",
                nutrition_analysis, re.IGNORECASE)

            if fats_match:
                try:
                    # Use the first non-None capture group
                    fats_value = next(
                        g for g in fats_match.groups() if g is not None)
                    fats_consumed = f"{fats_value}g"
                    logging.info(f"Found fat intake: {fats_consumed}")
                except (ValueError, TypeError, StopIteration):
                    logging.warning("Could not parse fat intake")

            # Extract carbs data - updated pattern
            carbs_match = re.search(
                r"(?:average|daily|approximately|around|about)\s*(?:of|is|at)?\s*(?:carb|carbs|carbohydrates)\s*(?:intake|consumption|is)?\s*(?:of|is|at)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?|(?:carb|carbs|carbohydrates)\s*(?:intake|consumption)?\s*(?:of|is|at|around|about)?\s*(?:approximately|around|about)?\s*(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)?",
                nutrition_analysis, re.IGNORECASE)

            if carbs_match:
                try:
                    # Use the first non-None capture group
                    carbs_value = next(
                        g for g in carbs_match.groups() if g is not None)
                    carbs_consumed = f"{carbs_value}g"
                    logging.info(f"Found carbs intake: {carbs_consumed}")
                except (ValueError, TypeError, StopIteration):
                    logging.warning("Could not parse carbs intake")

            # Backup pattern for finding numbers near macro words
            if not fats_match:
                backup_fats_match = re.search(
                    r"fats?.*?(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)", nutrition_analysis, re.IGNORECASE | re.DOTALL)
                if backup_fats_match:
                    fats_consumed = f"{backup_fats_match.group(1)}g"
                    has_real_data["nutrition"] = True
                    logging.info(
                        f"Found fat intake using backup pattern: {fats_consumed}")

            if not carbs_match:
                backup_carbs_match = re.search(
                    r"carbs?.*?(?:\*\*)?(\d{1,3})(?:\*\*)?\s*(?:g|grams)", nutrition_analysis, re.IGNORECASE | re.DOTALL)
                if backup_carbs_match:
                    carbs_consumed = f"{backup_carbs_match.group(1)}g"
                    has_real_data["nutrition"] = True
                    logging.info(
                        f"Found carbs intake using backup pattern: {carbs_consumed}")

            # Extract daily values (not weekly totals)
            daily_values_pattern = re.search(
                r"(\d+)(?:-(\d+))?\s*g(?:rams)?\s*per\s*day", nutrition_analysis, re.IGNORECASE)
            if daily_values_pattern:
                # Range format like "240-260g per day"
                if daily_values_pattern.group(2):
                    # Take the average of the range
                    min_val = int(daily_values_pattern.group(1))
                    max_val = int(daily_values_pattern.group(2))
                    avg_val = (min_val + max_val) // 2
                    if "carbs" in nutrition_analysis[max(0, daily_values_pattern.start() - 50):daily_values_pattern.start()].lower():
                        carbs_consumed = f"{avg_val}g"
                        has_real_data["nutrition"] = True
                        logging.info(
                            f"Found carbs from range: {carbs_consumed}")
                    elif "fat" in nutrition_analysis[max(0, daily_values_pattern.start() - 50):daily_values_pattern.start()].lower():
                        fats_consumed = f"{avg_val}g"
                        has_real_data["nutrition"] = True
                        logging.info(f"Found fats from range: {fats_consumed}")
                else:  # Single value like "80g per day"
                    val = int(daily_values_pattern.group(1))
                    if "carbs" in nutrition_analysis[max(0, daily_values_pattern.start() - 50):daily_values_pattern.start()].lower():
                        carbs_consumed = f"{val}g"
                        has_real_data["nutrition"] = True
                        logging.info(
                            f"Found carbs from single value: {carbs_consumed}")
                    elif "fat" in nutrition_analysis[max(0, daily_values_pattern.start() - 50):daily_values_pattern.start()].lower():
                        fats_consumed = f"{val}g"
                        has_real_data["nutrition"] = True
                        logging.info(
                            f"Found fats from single value: {fats_consumed}")

        # Make sure nutrition data flag is set properly
        has_real_data["nutrition"] = (has_real_data["nutrition"] or
                                      "carbs" in nutrition_analysis.lower() or
                                      "macronutrient" in nutrition_analysis.lower() or
                                      "calorie" in nutrition_analysis.lower())

        # Get top performing exercises with improvement percentages
        top_exercises = []
        try:
            # Calculate current week's date range
            today = datetime.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            current_week_end = current_week_start + timedelta(days=6)
            previous_week_start = current_week_start - timedelta(weeks=1)
            previous_week_end = current_week_end - timedelta(weeks=1)

            # Get top 3 performing exercises
            top_exercise_names = self.find_top_performing_exercises(
                workout_data_list,
                current_week_start,
                current_week_end,
                previous_week_start,
                previous_week_end,
                3  # Top 3 exercises
            )

            # Get improvement percentages for these exercises
            _, _, _, _, _, _, current_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list,
                current_week_start,
                current_week_end,
                target_exercises=top_exercise_names
            )

            _, _, _, _, _, _, previous_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list,
                previous_week_start,
                previous_week_end,
                target_exercises=top_exercise_names
            )

            # Calculate improvement for each exercise
            for exercise_name in top_exercise_names:
                current = current_exercise_workload.get(exercise_name, 0)
                previous = previous_exercise_workload.get(exercise_name, 0)

                improvement = 0
                if previous > 0:
                    improvement = ((current - previous) / previous) * 100
                elif current > 0:
                    improvement = 100  # New exercise this week

                # Cap improvement at reasonable values
                improvement = max(min(improvement, 500), -
                                  100)  # Between -100% and 500%

                # Store exercise name and improvement percentage
                top_exercises.append({
                    "name": exercise_name,
                    "improvement": round(improvement, 1)
                })

            logging.info(
                f"Top performing exercises with improvements: {top_exercises}")
        except Exception as e:
            logging.exception(
                f"Error calculating top exercise improvements: {e}")
            # Fallback data
            top_exercises = [
                {"name": "Barbell Bench Chest Press", "improvement": 10.0},
                {"name": "Lateral Raises", "improvement": 15.0},
                {"name": "B.B Back Squat", "improvement": 5.0}
            ]

        # Calculate unique workouts for the current week
        # Current week
        today = datetime.now().date()
        # Monday of current week
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)  # Sunday of current week

        logging.info(
            f"Calculating workouts for date range {start_date} to {end_date}")

        # Count unique workouts in the current week using a set to track unique workout+date combinations
        unique_workout_keys = set()
        workout_count = 0

        for workout in workout_data_list:
            date_str = workout.get('date', '')
            workout_name = workout.get('workout_type', workout.get(
                'workout_name', workout.get('type', '')))

            try:
                # Try parsing with '%d %b %Y' format (e.g., "6 Mar 2025")
                workout_date = datetime.strptime(date_str, '%d %b %Y').date()
                if start_date <= workout_date <= end_date:
                    # Create a unique key based on date AND workout name
                    unique_key = f"{workout_date.strftime('%Y-%m-%d')}_{workout_name}"

                    # Only count each unique workout (by date and name) once
                    if unique_key not in unique_workout_keys:
                        unique_workout_keys.add(unique_key)
                        workout_count += 1
                        logging.info(
                            f"  Found unique workout on {date_str}: {workout_name}")
            except (ValueError, TypeError):
                try:
                    # Fallback to %Y-%m-%d format (e.g., "2025-03-06")
                    workout_date = datetime.strptime(
                        date_str, '%Y-%m-%d').date()
                    if start_date <= workout_date <= end_date:
                        # Create a unique key based on date AND workout name
                        unique_key = f"{workout_date.strftime('%Y-%m-%d')}_{workout_name}"

                        # Only count each unique workout (by date and name) once
                        if unique_key not in unique_workout_keys:
                            unique_workout_keys.add(unique_key)
                            workout_count += 1
                            logging.info(
                                f"  Found unique workout on {date_str}: {workout_name}")
                except (ValueError, TypeError):
                    logging.warning(
                        f"Could not parse workout date: {date_str}")

        logging.info(f"Total unique workouts in date range: {workout_count}")

        # Create the fitness wrapped data dictionary
        fitness_wrapped_data = {
            "name": client_name,
            "business_name": "Coco's",
            "date_range": date_range,
            "start_weight": start_weight,
            "current_weight": current_weight,
            "weight_loss": total_weight_change,
            # Set equal to total_weight_change instead of using undefined variable
            "weight_change": total_weight_change,
            "total_weight_change": total_weight_change,
            "weight_trend": weight_trend,
            "weight_start_date": getattr(self, 'weight_data_metadata', {}).get('start_date'),
            "weight_current_date": getattr(self, 'weight_data_metadata', {}).get('current_date'),
            "weight_goal": weight_goal,
            "current_weight_message": current_weight_message,
            "workouts_this_week": workout_count,  # Use total workout count, not unique count
            "workout_types": list(set(workout['type'] for workout in workout_data_list if 'type' in workout)),
            "total_reps": total_reps,
            "total_sets": total_sets,
            "total_weight_lifted": total_weight,
            "workload_increase": round(workload_increase, 2),
            "calories_consumed": calories_consumed,
            "protein_consumed": protein_consumed,
            "fats_consumed": fats_consumed,
            "carbs_consumed": carbs_consumed,
            "nutrition_tracking_consistent": nutrition_tracking_consistent,
            "nutrition_tracking_days": nutrition_tracking_days,
            "nutrition_consistency_message": nutrition_consistency_message,
            "step_count": step_count,
            "highest_steps": highest_steps,  # Add the highest_steps to the JSON
            "sleep_hours": sleep_hours,
            "personalized_message": self.generate_personalized_message(client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis),
            "top_exercises": top_exercises if top_exercises else [],
            "has_weight_data": has_reliable_weight_data,
            "has_steps_data": has_real_data["steps"],
            "has_sleep_data": has_real_data["sleep"],
            "has_nutrition_data": has_real_data["nutrition"],
            "has_up_to_date_photos": has_up_to_date_photos,
            "has_workout_data": len(workout_data_list) > 0,
            "has_workload_data": workload_increase != 0,
            "has_exercise_data": len(top_exercises) > 0,
            "has_reliable_weight_data": has_reliable_weight_data
        }

        # Final logging of critical values
        logging.info(
            f"Final weight_goal value for {client_name}: {client_weight_goal}")
        logging.info(f"Has reliable weight data: {has_reliable_weight_data}")
        if has_reliable_weight_data:
            logging.info(
                f"Final weight values: start={start_weight}, current={current_weight}, change={total_weight_change}")
            if weight_trend:
                logging.info(f"Weight trend direction: {weight_trend}")
            if start_date and current_date:
                logging.info(
                    f"Weight measurement dates: {start_date} to {current_date}")

        return fitness_wrapped_data

    def extract_weight_history(self, bodyweight_analysis):
        """Extracts historical weight values, dates, and trend from bodyweight analysis text."""
        try:
            if not bodyweight_analysis or "No bodyweight data available" in bodyweight_analysis:
                logging.info("No bodyweight data available in analysis")
                return []

            # Log the first part of the bodyweight analysis for debugging
            logging.info(
                f"Extracting weight from analysis: {bodyweight_analysis[:300]}...")

            # Track additional information
            weight_trend = None
            start_date = None
            current_date = None

            # Extract trend
            trend_match = re.search(
                r"TREND:\s*(upward|downward|stable)", bodyweight_analysis, re.IGNORECASE)
            if trend_match:
                weight_trend = trend_match.group(1).lower()
                logging.info(f"Extracted weight trend: {weight_trend}")

            # Extract dates
            start_date_match = re.search(
                r"STARTING_DATE:\s*(\d{2}-\d{2}-\d{4})", bodyweight_analysis, re.IGNORECASE)
            if start_date_match:
                start_date = start_date_match.group(1)
                logging.info(f"Extracted starting date: {start_date}")

            current_date_match = re.search(
                r"CURRENT_DATE:\s*(\d{2}-\d{2}-\d{4})", bodyweight_analysis, re.IGNORECASE)
            if current_date_match:
                current_date = current_date_match.group(1)
                logging.info(f"Extracted current date: {current_date}")

            # First look for the structured format we requested
            start_weight_match = re.search(
                r"STARTING_WEIGHT:\s*(\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)
            current_weight_match = re.search(
                r"CURRENT_WEIGHT:\s*(\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)

            # If we found both in structured format, use them
            if start_weight_match and current_weight_match:
                try:
                    start_weight = float(start_weight_match.group(1))
                    current_weight = float(current_weight_match.group(1))

                    # Use trend information to verify the weights are in correct order
                    if weight_trend == "downward" and start_weight < current_weight:
                        logging.warning(
                            "Weight trend is downward but start < current, swapping values")
                        start_weight, current_weight = current_weight, start_weight
                        # Also swap dates if available
                        if start_date and current_date:
                            start_date, current_date = current_date, start_date
                    elif weight_trend == "upward" and start_weight > current_weight:
                        logging.warning(
                            "Weight trend is upward but start > current, swapping values")
                        start_weight, current_weight = current_weight, start_weight
                        # Also swap dates if available
                        if start_date and current_date:
                            start_date, current_date = current_date, start_date

                    logging.info(
                        f"Extracted structured weight data: Start={start_weight}kg ({start_date}), Current={current_weight}kg ({current_date})")
                    # Store the dates and trend in the returned data for use later
                    self.weight_data_metadata = {
                        "trend": weight_trend,
                        "start_date": start_date,
                        "current_date": current_date
                    }
                    return [start_weight, current_weight]
                except ValueError as e:
                    logging.warning(
                        f"Error converting structured weight values: {e}")
                    # Continue to fallback methods

            # If structured format failed, try specific patterns for starting/current weight
            # (Rest of the fallback extraction logic remains the same)

            # Fallback logic for extracting weights from text
            start_patterns = [
                r"start(?:ing)?\s*weight.*?(\d+\.?\d*)",
                r"initial\s*weight.*?(\d+\.?\d*)",
                r"first\s*weight.*?(\d+\.?\d*)",
                r"began\s*at.*?(\d+\.?\d*)"
            ]

            current_patterns = [
                r"current\s*weight.*?(\d+\.?\d*)",
                r"latest\s*weight.*?(\d+\.?\d*)",
                r"final\s*weight.*?(\d+\.?\d*)",
                r"now\s*weighs.*?(\d+\.?\d*)",
                r"currently\s*at.*?(\d+\.?\d*)"
            ]

            start_weight = None
            current_weight = None

            # Try to find starting weight
            for pattern in start_patterns:
                match = re.search(pattern, bodyweight_analysis, re.IGNORECASE)
                if match:
                    try:
                        start_weight = float(match.group(1))
                        logging.info(
                            f"Found starting weight with pattern: {start_weight}kg")
                        break
                    except ValueError:
                        continue

            # Try to find current weight
            for pattern in current_patterns:
                match = re.search(pattern, bodyweight_analysis, re.IGNORECASE)
                if match:
                    try:
                        current_weight = float(match.group(1))
                        logging.info(
                            f"Found current weight with pattern: {current_weight}kg")
                        break
                    except ValueError:
                        continue

            # If we found both, return them
            if start_weight is not None and current_weight is not None:
                # Use trend information to verify weights if available
                if weight_trend == "downward" and start_weight < current_weight:
                    logging.warning(
                        "Weight trend is downward but start < current, swapping values")
                    start_weight, current_weight = current_weight, start_weight
                elif weight_trend == "upward" and start_weight > current_weight:
                    logging.warning(
                        "Weight trend is upward but start > current, swapping values")
                    start_weight, current_weight = current_weight, start_weight

                logging.info(
                    f"Using matched weight values: Start={start_weight}kg, Current={current_weight}kg")

                # Store metadata even when fallback method is used
                self.weight_data_metadata = {
                    "trend": weight_trend,
                    "start_date": start_date,
                    "current_date": current_date
                }
                return [start_weight, current_weight]

            # Look for weight mentions with units
            weight_matches = re.findall(
                r"(\d+\.?\d*)\s*(?:kg|kilograms)", bodyweight_analysis, re.IGNORECASE)
            weights = []

            for weight_str in weight_matches:
                try:
                    weight = float(weight_str)
                    if 30 <= weight <= 250:  # Reasonable weight range
                        weights.append(weight)
                        logging.info(f"Found weight with unit: {weight}kg")
                except ValueError:
                    continue

            # If we found at least 2 weights, use first and last
            if len(weights) >= 2:
                # Determine order based on trend
                if weight_trend == "downward" and weights[0] < weights[-1]:
                    weights.reverse()
                elif weight_trend == "upward" and weights[0] > weights[-1]:
                    weights.reverse()

                logging.info(
                    f"Using extracted weights: Start={weights[0]}kg, Current={weights[-1]}kg")

                # Store metadata
                self.weight_data_metadata = {
                    "trend": weight_trend,
                    "start_date": start_date,
                    "current_date": current_date
                }
                return [weights[0], weights[-1]]

            # Log if extraction failed
            if len(weights) < 2:
                logging.warning(
                    f"Could not extract enough weight values. Found: {weights}")
                self.weight_data_metadata = {
                    "trend": weight_trend,
                    "start_date": start_date,
                    "current_date": current_date
                }

            return weights

        except Exception as e:
            logging.exception(f"Error extracting weight history: {e}")
            self.weight_data_metadata = {
                "trend": None, "start_date": None, "current_date": None}
            return []

    def extract_weight_goal(self, weight_goal_text):
        """Extracts weight goal from the weight goal text with improved pattern matching.

        Args:
            weight_goal_text: String containing the weight goal from the app

        Returns:
            Dictionary with 'target' key containing the goal weight, or None if extraction fails
        """
        try:
            # If there's obviously no weight goal, return None immediately
            if not weight_goal_text or "No weight goal found" in weight_goal_text:
                logging.info("No weight goal text provided")
                return None

            # Log the raw text for debugging
            logging.info(f"Raw weight goal text: '{weight_goal_text}'")

            # Enhanced patterns for weight goals
            goal_patterns = [
                r"(?:weight goal|target weight|goal weight)[:\s]*(\d+\.?\d*)",
                r"(?:aiming for|targeting|aim to reach)[:\s]*(\d+\.?\d*)\s*(?:kg|kilos)",
                r"(?:weight|body weight).*?(\d+\.?\d*)\s*kg",
                r"(?:goal|target).*?(\d+\.?\d*)\s*(?:kg|kilos)"
            ]

            # Try each pattern
            for pattern in goal_patterns:
                goal_match = re.search(
                    pattern, weight_goal_text, re.IGNORECASE)
                if goal_match:
                    try:
                        goal = float(goal_match.group(1))
                        # More relaxed range - 30kg to 250kg
                        if 30 <= goal <= 250:
                            logging.info(f"Found weight goal: {goal}kg")
                            return {'target': goal}
                        else:
                            logging.warning(
                                f"Weight goal outside reasonable range: {goal}kg")
                    except ValueError:
                        logging.warning(
                            f"Could not convert to float: {goal_match.group(1)}")
                        continue

            # If specific patterns don't match, extract all numbers associated with weight terms
            weight_numbers = []
            # Find all numbers near words like weight, goal, target
            weight_contexts = re.findall(
                r'[^.!?]*(?:weight|goal|target|kg)[^.!?]*[.!?]',
                weight_goal_text,
                re.IGNORECASE
            )

            for context in weight_contexts:
                for num_match in re.finditer(r'(\d+\.?\d*)', context):
                    try:
                        value = float(num_match.group(1))
                        if 30 <= value <= 250:  # Reasonable weight range
                            weight_numbers.append(value)
                            logging.info(
                                f"Found potential weight goal: {value}kg")
                    except (ValueError, TypeError):
                        continue

            if weight_numbers:
                # If multiple potential values, use a reasonable heuristic
                # For example, take the average or the most common value
                weight_goal = weight_numbers[0]  # Default to first value
                logging.info(
                    f"Selected weight goal from context: {weight_goal}kg")
                return {'target': weight_goal}

            # If we've reached this point, we couldn't extract a weight goal
            logging.warning(
                f"Could not extract valid weight goal from: '{weight_goal_text}'")
            return None

        except Exception as e:
            logging.exception(f"Error extracting weight goal: {e}")
            return None

    def predict_future_progress(self, historical_data, goal_data):
        """Predicts future progress based on current trajectory.

        Args:
            historical_data: List of numerical data points(e.g., weights)
            goal_data: Dictionary with at least a 'target' key

        Returns:
            String with prediction message
        """
        try:
            # Calculate the rate of progress
            weeks_of_data = len(historical_data)
            if weeks_of_data < 3:
                return "Insufficient data for prediction. Need at least 3 weeks of data to make a reliable prediction."

            total_change = historical_data[-1] - historical_data[0]
            weekly_rate = total_change / weeks_of_data

            # Calculate time to goal
            current = historical_data[-1]
            goal = goal_data['target']
            remaining_change = goal - current

            if weekly_rate == 0:
                return "At current rate, goal will not be reached (no change detected in measured values)."

            # If progress is in wrong direction or has stalled
            if (remaining_change > 0 and weekly_rate < 0) or (remaining_change < 0 and weekly_rate > 0):
                return "Based on current trend, you're moving away from your goal. Let's adjust your approach!"

            weeks_to_goal = abs(remaining_change / weekly_rate)

            # Format prediction
            predicted_date = (
                datetime.now() + timedelta(weeks=weeks_to_goal)).strftime('%d %b %Y')

            # Customize message based on goal type (weight loss or gain)
            if remaining_change < 0:  # Weight loss goal
                return f"Great progress! At your current rate of weight loss, you're on track to reach your goal of {goal}kg around {predicted_date} (approximately {round(weeks_to_goal)} weeks from now)."
            else:  # Weight gain goal
                return f"Keep pushing! At your current rate of progress, you're on track to reach your goal of {goal}kg around {predicted_date} (approximately {round(weeks_to_goal)} weeks from now)."
        except Exception as e:
            logging.exception(f"Error predicting future progress: {e}")
            return "Error generating progress prediction."

    def find_top_performing_exercises(self, workout_data_list, start_date, end_date, previous_start_date, previous_end_date, top_n=3):
        """
        Finds the top N exercises with the best performance improvement between two weeks.

        Args:
            workout_data_list: List of workout dictionaries
            start_date: Start date of current week
            end_date: End date of current week
            previous_start_date: Start date of previous week
            previous_end_date: End date of previous week
            top_n: Number of top exercises to return (default 3)

        Returns:
            List of the top N exercise names that showed the best improvement
        """
        try:
            logging.info(f"Finding top {top_n} performing exercises...")

            # Get all exercises performed in both weeks
            _, _, _, _, _, current_week_workout_data, _ = self.calculate_workout_stats_for_date_range(
                workout_data_list, start_date, end_date)
            _, _, _, _, _, previous_week_workout_data, _ = self.calculate_workout_stats_for_date_range(
                workout_data_list, previous_start_date, previous_end_date)

            # Find all unique exercise names in both weeks
            all_exercises = set()
            for workout in current_week_workout_data + previous_week_workout_data:
                for exercise in workout['exercises']:
                    all_exercises.add(exercise['name'].strip())

            # Calculate workload for each exercise in both weeks
            exercise_improvements = []

            for exercise_name in all_exercises:
                # Get current week workload for this exercise
                current_workload = 0
                for workout in current_week_workout_data:
                    for exercise in workout['exercises']:
                        if exercise['name'].strip() == exercise_name:
                            for set_data in exercise['sets']:
                                current_workload += set_data['weight'] * \
                                    set_data['reps']

                # Get previous week workload for this exercise
                previous_workload = 0
                for workout in previous_week_workout_data:
                    for exercise in workout['exercises']:
                        if exercise['name'].strip() == exercise_name:
                            for set_data in exercise['sets']:
                                previous_workload += set_data['weight'] * \
                                    set_data['reps']

                # Calculate improvement percentage
                improvement = 0
                if previous_workload > 0:
                    improvement = (
                        (current_workload - previous_workload) / previous_workload) * 100
                # New exercise (wasn't done last week)
                elif current_workload > 0:
                    improvement = 100  # Assign a high value but not infinity

                exercise_improvements.append({
                    'name': exercise_name,
                    'current_workload': current_workload,
                    'previous_workload': previous_workload,
                    'improvement': improvement,
                    'is_new': previous_workload == 0 and current_workload > 0
                })

            # Sort by improvement percentage (descending)
            exercise_improvements.sort(
                key=lambda x: x['improvement'], reverse=True)

            # Get top N exercises (prioritizing ones with data in both weeks)
            # First, include exercises with data in both weeks
            top_exercises = []
            for ex in exercise_improvements:
                if not ex['is_new'] and ex['current_workload'] > 0 and ex['previous_workload'] > 0:
                    top_exercises.append(ex['name'])
                    if len(top_exercises) >= top_n:
                        break

            # If we still need more exercises, include the new ones
            if len(top_exercises) < top_n:
                for ex in exercise_improvements:
                    if ex['is_new'] and ex['name'] not in top_exercises:
                        top_exercises.append(ex['name'])
                        if len(top_exercises) >= top_n:
                            break

            # If we still need more exercises, include any remaining ones
            if len(top_exercises) < top_n:
                for ex in exercise_improvements:
                    if ex['name'] not in top_exercises and ex['current_workload'] > 0:
                        top_exercises.append(ex['name'])
                        if len(top_exercises) >= top_n:
                            break

            logging.info(
                f"Top {len(top_exercises)} performing exercises: {top_exercises}")

            # If we still don't have enough exercises, use default exercises as fallback
            if len(top_exercises) < top_n:
                default_exercises = ["Barbell Bench Chest Press",
                                     "B.B Back Squat", "Lat Pull Down Wide Grip"]
                for ex in default_exercises:
                    if ex not in top_exercises:
                        top_exercises.append(ex)
                        if len(top_exercises) >= top_n:
                            break

            return top_exercises[:top_n]  # Return only top_n exercises

        except Exception as e:
            logging.exception(f"Error finding top performing exercises: {e}")
            # Return default exercises if something goes wrong
            return ["Barbell Bench Chest Press", "B.B Back Squat", "Lat Pull Down Wide Grip"][:top_n]

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

    def navigate_to_client(self, client_name):
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")
            logging.info("Clicking the 'Clients' link in the sidebar...")
            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            except TimeoutException as te:
                logging.error(
                    f"TimeoutException while waiting for Clients link: {te.msg}")
                return False

            time.sleep(2)
            logging.info(
                "Entering client name into the search bar on the Clients page...")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(
                EC.presence_of_element_located(search_input_locator))
            # Clear the search bar before typing the new client name
            search_input.clear()
            search_input.send_keys(client_name)
            time.sleep(2)
            logging.info(
                "Clicking on the client's name in the search results...")
            client_link_locator = (
                By.XPATH, f"//a[contains(text(), '{client_name}')]")
            try:
                client_link = self.wait.until(
                    EC.element_to_be_clickable(client_link_locator))
                client_link.click()
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(
                    f"Could not find or click client link for {client_name}: {e}")
                return False

            time.sleep(2)
            logging.info(
                "Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            try:
                open_button = self.wait.until(
                    EC.element_to_be_clickable(open_button_locator))
                open_button.click()
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(
                    f"Could not find or click 'Open' button for {client_name}: {e}")
                return False

            time.sleep(2)
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            logging.info(
                f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True
        except Exception as e:
            logging.exception(
                f"Error navigating to client {client_name} or switching tabs: {e}")
            return False

    def click_progress_photos_tab(self):
        """Clicks the 'Progress Photos' tab using a more robust XPath."""
        try:
            logging.info("Attempting to click the 'Progress Photos' tab...")
            # Use XPath to find the link containing "Progress Photos" and the correct href
            progress_photos_tab_locator = (
                By.XPATH, "//a[contains(@class, 'section-link') and contains(@href, '/progress/photo') and contains(., 'Progress Photos')]")
            progress_photos_tab = self.wait.until(
                EC.element_to_be_clickable(progress_photos_tab_locator))
            progress_photos_tab.click()
            logging.info("Successfully clicked the 'Progress Photos' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"'Progress Photos' tab not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred while clicking 'Progress Photos': {e}")
            return False

    def click_progress_tab(self):
        try:
            logging.info("Attempting to click the 'Progress' tab...")
            progress_tab_locator = (
                By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab = self.wait.until(
                EC.element_to_be_clickable(progress_tab_locator))
            progress_tab.click()
            logging.info("Successfully clicked the 'Progress' tab.")
            return "Successfully clicked Progress tab"
        except TimeoutException:
            logging.error(
                "TimeoutException: 'Progress' tab not found or not clickable within the timeout.")
            return "Failed to click Progress tab (Timeout)"
        except NoSuchElementException:
            logging.error(
                "NoSuchElementException: 'Progress' tab element not found on the page.")
            return "Failed to click Progress tab (Not Found)"
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return "Failed to click Progress tab (Unknown Error)"

    def click_biometrics(self):
        try:
            logging.info("Attempting to click the 'Biometrics' link...")
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "nav_progress")))
            time.sleep(1)
            biometrics_locator = (
                By.XPATH, "//a[@class='tz-sp section-link' and contains(@href, '/progress/bodyweight')]")
            biometrics_link = self.wait.until(
                EC.element_to_be_clickable(biometrics_locator))
            self.driver.execute_script(
                "arguments[0].click();", biometrics_link)
            logging.info("Successfully clicked the 'Biometrics' link.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"'Biometrics' link not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return False

    def navigate_to_goals_and_habits_tab(self):
        """Clicks the 'Goals and Habits' tab using multiple strategies for robustness."""
        try:
            logging.info("Attempting to click the 'Goals and Habits' tab...")

            # Strategy 1: Try by ID (original method)
            try:
                logging.info("Strategy 1: Try by ID")
                goals_tab_locator = (By.ID, "nav_goals_and habits")
                goals_tab = self.wait.until(
                    EC.element_to_be_clickable(goals_tab_locator))
                goals_tab.click()
                time.sleep(2)  # Wait for page to load
                logging.info(
                    "Successfully clicked 'Goals and Habits' tab by ID")
                return True
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning(f"Strategy 1 failed: {e}")

            # Strategy 2: Try by XPath with partial text
            try:
                logging.info("Strategy 2: Try by XPath with partial text")
                goals_xpath = "//a[contains(text(), 'Goals') and contains(@class, 'menu-item')]"
                goals_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, goals_xpath)))
                goals_element.click()
                time.sleep(2)  # Wait for page to load
                logging.info(
                    "Successfully clicked 'Goals and Habits' tab by XPath text match")
                return True
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning(f"Strategy 2 failed: {e}")

            # Strategy 3: Try to find it in the navigation menu by class and position
            try:
                logging.info("Strategy 3: Try by navigation menu position")
                nav_items = self.driver.find_elements(
                    By.CSS_SELECTOR, "a.leftNavMenu-item")
                # The Goals and Habits tab is often the 5th or 6th item in the menu
                potential_goals_tabs = [item for item in nav_items if "Goals" in item.get_attribute(
                    "title") or "goals" in item.get_attribute("id").lower()]

                if potential_goals_tabs:
                    potential_goals_tabs[0].click()
                    time.sleep(2)  # Wait for page to load
                    logging.info(
                        "Successfully clicked 'Goals and Habits' tab by navigation position")
                    return True
                else:
                    logging.warning(
                        "No potential Goals tabs found in navigation menu")
            except Exception as e:
                logging.warning(f"Strategy 3 failed: {e}")

            # Strategy 4: Try to navigate via URL directly
            try:
                logging.info("Strategy 4: Try direct URL navigation")
                current_url = self.driver.current_url
                # Extract the base URL and append the goals path
                if "/clients/" in current_url and "/profile/" in current_url:
                    base_url_parts = current_url.split("/profile/")
                    goals_url = f"{base_url_parts[0]}/profile/goals_and habits"
                    self.driver.get(goals_url)
                    time.sleep(3)  # Give it more time to load
                    logging.info(
                        f"Attempted direct navigation to Goals URL: {goals_url}")
                    return True
                else:
                    logging.warning(
                        f"Could not construct Goals URL from current URL: {current_url}")
            except Exception as e:
                logging.warning(f"Strategy 4 failed: {e}")

            # If we get here, all strategies failed
            logging.error(
                "All strategies to navigate to 'Goals and Habits' tab failed")
            return False

        except Exception as e:
            logging.exception(
                f"Unexpected error navigating to 'Goals and Habits' tab: {e}")
            return False

    def get_current_weight_goal(self):
        """Retrieves the text of the current weight goal from the Goals and Habits tab with enhanced robustness."""
        try:
            logging.info("Attempting to get current weight goal...")

            # Take a screenshot for debugging
            screenshot_path = "weight_goal_page.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(
                f"Saved screenshot of goals page to {screenshot_path}")

            # Strategy 1: Look for the weight goal tile using different selectors
            selectors = [
                "//div[contains(@class, 'goalTile')]//label[contains(@class, 'goalTile__title')]",
                "//div[contains(@class, 'goalTile')]//label[contains(text(), 'kg')]",
                "//label[contains(text(), 'Weight Goal')]",
                "//label[contains(text(), 'Target Weight')]",
                "//div[contains(@class, 'tz-card')]//label[contains(text(), 'kg')]"
            ]

            for selector in selectors:
                try:
                    logging.info(f"Trying selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(
                        f"Found {len(elements)} elements with selector: {selector}")

                    for element in elements:
                        text = element.text.strip()
                        logging.info(f"Element text: '{text}'")

                        # If the text contains weight-related keywords
                        if any(keyword in text.lower() for keyword in ['weight', 'kg', 'lbs', 'goal']):
                            logging.info(
                                f"Found weight goal element: '{text}'")
                            return text
                except Exception as e:
                    logging.warning(f"Error with selector {selector}: {e}")
                    continue

            # Strategy 2: Scan all card elements for weight-related text
            try:
                logging.info(
                    "Scanning all card elements for weight-related text")
                card_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, ".tz-card, .goalTile")

                for card in card_elements:
                    try:
                        card_text = card.text
                        logging.info(f"Card text: '{card_text}'")

                        # Look for weight goal patterns in the card text
                        weight_patterns = [
                            r"(?:weight goal|target weight)[:\s]*(\d+\.?\d*)",
                            r"(\d+\.?\d*)\s*kg"
                        ]

                        for pattern in weight_patterns:
                            match = re.search(
                                pattern, card_text, re.IGNORECASE)
                            if match:
                                full_match = match.group(0)
                                logging.info(
                                    f"Found weight goal in card: '{full_match}'")
                                # Return the full card text to get more context
                                return card_text
                    except Exception as card_e:
                        logging.warning(
                            f"Error processing card element: {card_e}")
                        continue
            except Exception as e:
                logging.warning(f"Error scanning card elements: {e}")

            # Strategy 3: Look for any weight-related text on the page
            try:
                logging.info("Scanning entire page for weight-related text")
                page_text = self.driver.find_element(By.TAG_NAME, "body").text

                # Look for any text that might contain a weight goal
                weight_patterns = [
                    r"(?:weight goal|target weight|goal weight)[:\s]*(\d+\.?\d*)",
                    r"(?:weight|goal)[:\s]*(\d+\.?\d*)\s*kg",
                    r"(\d+\.?\d*)\s*kg"
                ]

                for pattern in weight_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        goal_text = match.group(0)
                        logging.info(
                            f"Found weight goal in page text: '{goal_text}'")
                        return goal_text

                # Log a portion of the page text for debugging
                logging.info(f"Page text excerpt: '{page_text[:500]}...'")
            except Exception as e:
                logging.warning(f"Error scanning page text: {e}")

            # If we get here, we couldn't find the weight goal
            logging.warning("No weight goal found on the page")
            return "No weight goal found"

        except Exception as e:
            logging.exception(f"Error retrieving weight goal: {e}")
            return f"Error retrieving weight goal: {e}"

    def _navigate_to_graph(self, target_href_contains):
        """Generic function for navigating to graphs using keyboard."""
        try:
            logging.info(
                f"Navigating to graph containing '{target_href_contains}' using keyboard...")
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "nav_progress")))
            progress_tab = self.driver.find_element(
                By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab.send_keys(Keys.TAB)
            time.sleep(0.5)
            active_element = self.driver.switch_to.active_element

            for _ in range(100):  # Up to 100 tabs
                try:
                    href = active_element.get_attribute("href")
                    if href and target_href_contains in href:
                        active_element.send_keys(Keys.ENTER)
                        logging.info(
                            f"Successfully navigated to graph: {target_href_contains}")
                        return True
                except StaleElementReferenceException:
                    logging.warning(
                        "StaleElementReferenceException. Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(
                        By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

                active_element.send_keys(Keys.TAB)
                time.sleep(0.5)
                try:
                    # Re-acquire in case of DOM changes
                    active_element = self.driver.switch_to.active_element
                except StaleElementReferenceException:
                    logging.warning(
                        "StaleElementReferenceException. Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(
                        By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

            logging.error(
                f"Graph link containing '{target_href_contains}' not found via keyboard navigation.")
            return False

        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Error navigating to graph with keyboard: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return False

    def navigate_to_nutrition_graphs(self):
        return self._navigate_to_graph("caloriesintake")

    def navigate_to_sleep_graphs(self):
        return self._navigate_to_graph("sleep")

    def navigate_to_steps_graphs(self):
        return self._navigate_to_graph("steps")

    def _click_3m_button_if_exists(self):
        """Clicks the '3M' button on the graph if it exists."""
        try:
            logging.info(
                "Attempting to click '3M' button for graph timeframe...")
            button_locator = (
                By.XPATH, "//label[contains(@class, 'ant-radio-button-wrapper')]//span[text()='3M']")
            button_3m = self.wait.until(
                EC.element_to_be_clickable(button_locator))
            button_3m.click()
            logging.info("Successfully clicked '3M' button.")
            time.sleep(1)  # Wait for graph to update
            return True
        except (TimeoutException, NoSuchElementException):
            logging.warning(
                "'3M' button not found or not clickable (might not be present).")
            return False
        except Exception as e:
            logging.exception(f"Error clicking '3M' button: {e}")
            return False

    def analyze_bodyweight_graph(self):
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping bodyweight graph analysis.")
            return "Gemini API key not provided, skipping analysis."
        try:
            logging.info("Analyzing bodyweight graph with gemini-2.0-flash...")
            # Wait for the graph element to be present or for a timeout to occur.
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))

            self._click_3m_button_if_exists()  # Click 3M button if present

            time.sleep(2)  # Wait for the graph to potentially load fully
            screenshot_path = "bodyweight_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = self.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
                        Analyze this bodyweight graph from a fitness app. I need specific structured data from this graph:

                        1. EXACT DATA EXTRACTION(MOST IMPORTANT):
                        - Starting weight(first weight on the left side of the graph): Give the exact number in kg
                        - Current/latest weight(rightmost point on the graph): Give the exact number in kg
                        - Starting date(date of first weight point): If visible on the graph
                        - Current date(date of most recent weight point): If visible on the graph

                        2. Provide your answer in this EXACT STRUCTURED FORMAT:
                        STARTING_WEIGHT: [number] kg
                        STARTING_DATE: [date in DD-MM-YYYY format or "not visible"]
                        CURRENT_WEIGHT: [number] kg
                        CURRENT_DATE: [date in DD-MM-YYYY format or "not visible"]
                        TREND: [upward/downward/stable]

                        3. After the structured data above, provide a brief analysis of:
                        - Overall trend direction(weight loss, gain, or stable)
                        - Rate of change(rapid, moderate, slow)
                        - Pattern(consistent, fluctuating, plateaued)
                        - Recent changes(last few data points)

                        Focus on extracting the most accurate numerical data possible from the graph. This data will be programmatically processed.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Bodyweight Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])

            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5000)
            )
            try:
                analysis = response.text
                print("\n--- Gemini Response (Bodyweight Analysis) ---")
                print(analysis)
            except Exception as e:
                logging.warning(
                    f"Error accessing response.text for bodyweight analysis: {e}")
                # Try alternative approach to get the text
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        analysis = response.candidates[0].content.parts[0].text
                    else:
                        # Fallback message
                        analysis = "Unable to analyze bodyweight data with current model. Your weight progress looks on track though!"
                        logging.warning(
                            "No candidates in response, using fallback message")
                except Exception as fallback_error:
                    logging.exception(
                        f"Error in fallback handling: {fallback_error}")
                    analysis = "Unable to analyze bodyweight data. Your weight tracking is important for your progress."

            return analysis

        except TimeoutException:
            return "No bodyweight data available."

        except Exception as e:
            logging.exception(
                f"Error analyzing graph with gemini-2.0-flash: {e}")
            return f"Error: {e}"

    def analyze_nutrition_graph(self):
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping nutrition graph analysis.")
            return "Gemini API key not provided, skipping analysis."
        try:
            logging.info("Analyzing nutrition graph with gemini-2.0-flash...")
            self.navigate_to_nutrition_graphs()
            self._click_3m_button_if_exists()
            # Wait for the graph element to be present or for a timeout.
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)

            # Take first screenshot for protein and calories BEFORE scrolling
            calories_protein_screenshot_path = "nutrition_graph_calories_protein.png"
            self.driver.save_screenshot(calories_protein_screenshot_path)
            logging.info(
                f"Calories/Protein screenshot saved to {calories_protein_screenshot_path}")

            # Now find and scroll to the Carbs (g) heading for the second screenshot
            try:
                # Try to find the Carbs (g) heading
                carbs_heading = self.driver.find_element(
                    By.XPATH, "//h5[contains(text(), 'Carbs (g)')]")
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'start'});", carbs_heading)
                logging.info("Successfully scrolled to Carbs (g) section")
                time.sleep(1)  # Wait for scroll to complete
            except NoSuchElementException:
                # Fallback to try different ways to find the element
                try:
                    carbs_heading = self.driver.find_element(
                        By.XPATH, "//h5[@style='color: rgb(36, 31, 32);' and contains(text(), 'Carbs')]")
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'start'});", carbs_heading)
                    logging.info(
                        "Successfully scrolled to Carbs section using style attribute")
                    time.sleep(1)  # Wait for scroll to complete
                except NoSuchElementException:
                    # Try to find Fat (g) as a fallback
                    try:
                        fat_heading = self.driver.find_element(
                            By.XPATH, "//h5[contains(text(), 'Fat (g)')]")
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'start'});", fat_heading)
                        logging.info(
                            "Fallback: Successfully scrolled to Fat (g) section")
                        time.sleep(1)  # Wait for scroll to complete
                        # Scroll a bit more to try and get to carbs
                        self.driver.execute_script("window.scrollBy(0, 200);")
                    except NoSuchElementException:
                        logging.warning(
                            "Neither Carbs (g) nor Fat (g) headings found, will try to proceed anyway")
                        # Use a safer scrolling approach if we can't find any headings
                        self.driver.execute_script("window.scrollBy(0, 400);")
                        logging.info("Used backup scrolling method")

            # Scroll down to make fats and carbs graphs fully visible
            logging.info(
                "Scrolling down to make fats and carbs graphs fully visible")
            # Adjust scroll amount as needed
            self.driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(2)  # Wait for scrolling animation to complete

            # Take second screenshot for fats and carbs
            carbs_fats_screenshot_path = "nutrition_graph_carbs_fats.png"
            self.driver.save_screenshot(carbs_fats_screenshot_path)
            logging.info(
                f"Carbs/Fats screenshot saved to {carbs_fats_screenshot_path}")

            # Encode both images
            base64_image1 = self.encode_image(calories_protein_screenshot_path)
            base64_image2 = self.encode_image(carbs_fats_screenshot_path)

            if not base64_image1 or not base64_image2:
                return "Error: Could not encode one or both images."

            # FIRST GEMINI CALL - Calories and Protein
            calories_protein_prompt = [{
                "parts": [
                    {"text": f"""
                        Analyze these nutrition graphs from a personal training app, focusing on calories and protein:

                        1. Average daily intake of calories and protein
                        2. Recommended intake of calories and protein(shown on right side of graph)
                        3. Any visible trends - low days or high days
                        4. Week-by-week comparison for calories and protein
                        5. IMPORTANT: Check for consistency in tracking. Look for any gaps in the data or days where no data was logged. Report if tracking appears incomplete or inconsistent.
                        6. If you can tell how many days were actually tracked, mention the exact number in your analysis.

                        IMPORTANT: Begin your response with a structured data section using this exact format:
                        ```data
                        CALORIES_DAILY: [number]
                        PROTEIN_DAILY: [number]g
                        CALORIES_GOAL: [number]
                        PROTEIN_GOAL: [number]g
                        ```

                        If any value is not visible or cannot be determined, use "not visible" instead of a number.
                        Then, continue with your detailed analysis after the structured data section.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image1
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Calories/Protein Analysis) ---")
            print(calories_protein_prompt[0]['parts'][0]['text'])

            calories_protein_response = self.model.generate_content(
                contents=calories_protein_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2500)
            )

            # SECOND GEMINI CALL - Fats and Carbs
            fats_carbs_prompt = [{
                "parts": [
                    {"text": f"""
                        Analyze these nutrition graphs from a personal training app, focusing on fats and carbs:

                        1. Average daily intake of fats and carbs
                        2. Recommended intake of fats and carbs(shown on right side of graph)
                        3. Any visible trends - low days or high days
                        4. Week-by-week comparison for fats and carbs
                        5. IMPORTANT: Check for consistency in tracking. Look for any gaps in the data or days where no data was logged. Report if tracking appears incomplete or inconsistent.
                        6. If you can tell how many days were actually tracked, mention the exact number in your analysis.

                        IMPORTANT: Begin your response with a structured data section using this exact format:
                        ```data
                        FATS_DAILY: [number]g
                        CARBS_DAILY: [number]g
                        FATS_GOAL: [number]g
                        CARBS_GOAL: [number]g
                        ```

                        If any value is not visible or cannot be determined, use "not visible" instead of a number.
                        Then, continue with your detailed analysis after the structured data section.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image2
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Fats/Carbs Analysis) ---")
            print(fats_carbs_prompt[0]['parts'][0]['text'])

            fats_carbs_response = self.model.generate_content(
                contents=fats_carbs_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2500)
            )

            try:
                # Process both responses
                calories_protein_analysis = calories_protein_response.text if hasattr(
                    calories_protein_response, 'text') else ""
                fats_carbs_analysis = fats_carbs_response.text if hasattr(
                    fats_carbs_response, 'text') else ""

                print("\n--- Gemini Response (Calories/Protein Analysis) ---")
                print(calories_protein_analysis)

                print("\n--- Gemini Response (Fats/Carbs Analysis) ---")
                print(fats_carbs_analysis)

                # Combine the analyses
                combined_analysis = self._combine_nutrition_analyses(
                    calories_protein_analysis, fats_carbs_analysis)

                # Add diagnostic logging for regex patterns
                logging.info("NUTRITION ANALYSIS REGEX CHECK:")

                # Check for structured data format first
                structured_data_match = re.search(
                    r"```data\s+(.*?)\s+```", combined_analysis, re.DOTALL)

                if structured_data_match:
                    logging.info("✓ Found structured nutrition data format")
                    structured_data = structured_data_match.group(1)

                    # Check for each macro in the structured format
                    calories_match = re.search(
                        r"CALORIES_DAILY:\s+(not visible|\d+)", structured_data, re.IGNORECASE)
                    logging.info(
                        f"Calories regex match: {bool(calories_match)}")
                    if calories_match and calories_match.group(1).lower() != 'not visible':
                        logging.info(
                            f"Matched calories: {calories_match.group(1)}")

                    protein_match = re.search(
                        r"PROTEIN_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
                    logging.info(f"Protein regex match: {bool(protein_match)}")
                    if protein_match and protein_match.group(1).lower() != 'not visible':
                        logging.info(
                            f"Matched protein: {protein_match.group(1)}")

                    fats_match = re.search(
                        r"FATS_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
                    logging.info(f"Fats regex match: {bool(fats_match)}")
                    if fats_match and fats_match.group(1).lower() != 'not visible':
                        logging.info(f"Matched fats: {fats_match.group(1)}")

                    carbs_match = re.search(
                        r"CARBS_DAILY:\s+(not visible|\d+g?)", structured_data, re.IGNORECASE)
                    logging.info(f"Carbs regex match: {bool(carbs_match)}")
                    if carbs_match and carbs_match.group(1).lower() != 'not visible':
                        logging.info(f"Matched carbs: {carbs_match.group(1)}")
                else:
                    # Fall back to checking natural language patterns if structured data not found
                    logging.info(
                        "⚠ Structured data format not found, checking natural language patterns")
                    calories_match = re.search(
                        r"average\s*(?:of)?\s*(\d{1,4})\s*calories", combined_analysis, re.IGNORECASE)
                    logging.info(
                        f"Calories regex match: {bool(calories_match)}")
                    if calories_match:
                        logging.info(
                            f"Matched calories: {calories_match.group(1)}")

                    protein_match = re.search(
                        r"average\s*(?:of)?\s*(\d{1,3})\s*g(?:rams)?\s*(?:of)?\s*protein|protein\s*(?:intake|consumption)?\s*(?:of|is|was)?\s*(?:about|around|approximately)?\s*(\d{1,3})\s*g(?:rams)?", combined_analysis, re.IGNORECASE)
                    logging.info(f"Protein regex match: {bool(protein_match)}")
                    if protein_match:
                        logging.info(
                            f"Matched protein groups: {protein_match.groups()}")

                    fats_match = re.search(
                        r"average\s*(?:of)?\s*(\d{1,3})\s*g(?:rams)?\s*(?:of)?\s*fat|fat\s*(?:intake|consumption)?\s*(?:of|is|was)?\s*(?:about|around|approximately)?\s*(\d{1,3})\s*g(?:rams)?", combined_analysis, re.IGNORECASE)
                    logging.info(f"Fats regex match: {bool(fats_match)}")
                    if fats_match:
                        logging.info(
                            f"Matched fats groups: {fats_match.groups()}")

                    carbs_match = re.search(
                        r"average\s*(?:of)?\s*(\d{1,3})\s*g(?:rams)?\s*(?:of)?\s*carb(?:s|ohydrates)?|carb(?:s|ohydrates)?\s*(?:intake|consumption)?\s*(?:of|is|was)?\s*(?:about|around|approximately)?\s*(\d{1,3})\s*g(?:rams)?", combined_analysis, re.IGNORECASE)
                    logging.info(f"Carbs regex match: {bool(carbs_match)}")
                    if carbs_match:
                        logging.info(
                            f"Matched carbs groups: {carbs_match.groups()}")

                return combined_analysis
            except Exception as e:
                logging.warning(
                    f"Error processing nutrition analysis responses: {e}")
                # Try alternative approach to get the text
                try:
                    combined_analysis = ""

                    # Try to get calories/protein analysis
                    if hasattr(calories_protein_response, 'candidates') and calories_protein_response.candidates:
                        combined_analysis += calories_protein_response.candidates[0].content.parts[0].text + "\n\n"

                    # Try to get fats/carbs analysis
                    if hasattr(fats_carbs_response, 'candidates') and fats_carbs_response.candidates:
                        combined_analysis += fats_carbs_response.candidates[0].content.parts[0].text

                    if not combined_analysis:
                        # Fallback message
                        combined_analysis = "Unable to analyze nutrition data with current model. The nutrition tracking looks good though, keep it up!"
                        logging.warning(
                            "No candidates in response for nutrition analysis, using fallback message")

                    return combined_analysis
                except Exception as fallback_error:
                    logging.exception(
                        f"Error in fallback handling for nutrition analysis: {fallback_error}")
                    return "Unable to analyze nutrition data. Please make sure to log your meals to get insights next time!"

        except TimeoutException:
            logging.exception("Timeout while analyzing nutrition graph")
            return "Timeout while analyzing nutrition graph. Please ensure you have nutrition data logged."
        except Exception as e:
            logging.exception(f"Error analyzing nutrition graph: {e}")
            return "Error analyzing nutrition graph."

    def _combine_nutrition_analyses(self, calories_protein_analysis, fats_carbs_analysis):
        """Combine the analyses from the two Gemini calls into a single structured analysis."""
        try:
            logging.info("Combining nutrition analyses from two Gemini calls")

            # Initialize combined structured data
            combined_structured_data = {}
            tracking_indicators = {
                "days_tracked": 0,
                "is_consistent": True,
                "consistency_message": ""
            }

            # Process calories/protein analysis
            if calories_protein_analysis:
                # Extract structured data from calories/protein analysis
                calories_protein_data_match = re.search(
                    r"```data\s+(.*?)\s+```", calories_protein_analysis, re.DOTALL)

                if calories_protein_data_match:
                    calories_protein_data = calories_protein_data_match.group(
                        1)
                    logging.info(
                        f"Extracted calories/protein structured data: {calories_protein_data}")

                    # Extract calories data
                    calories_daily_match = re.search(
                        r"CALORIES_DAILY:\s+(not visible|\d+)", calories_protein_data, re.IGNORECASE)
                    if calories_daily_match:
                        combined_structured_data["CALORIES_DAILY"] = calories_daily_match.group(
                            1)
                        logging.info(
                            f"Extracted CALORIES_DAILY: {combined_structured_data['CALORIES_DAILY']}")

                    calories_goal_match = re.search(
                        r"CALORIES_GOAL:\s+(not visible|\d+)", calories_protein_data, re.IGNORECASE)
                    if calories_goal_match:
                        combined_structured_data["CALORIES_GOAL"] = calories_goal_match.group(
                            1)
                        logging.info(
                            f"Extracted CALORIES_GOAL: {combined_structured_data['CALORIES_GOAL']}")

                    # Extract protein data
                    protein_daily_match = re.search(
                        r"PROTEIN_DAILY:\s+(not visible|\d+g?)", calories_protein_data, re.IGNORECASE)
                    if protein_daily_match:
                        combined_structured_data["PROTEIN_DAILY"] = protein_daily_match.group(
                            1)
                        logging.info(
                            f"Extracted PROTEIN_DAILY: {combined_structured_data['PROTEIN_DAILY']}")

                    protein_goal_match = re.search(
                        r"PROTEIN_GOAL:\s+(not visible|\d+g?)", calories_protein_data, re.IGNORECASE)
                    if protein_goal_match:
                        combined_structured_data["PROTEIN_GOAL"] = protein_goal_match.group(
                            1)
                        logging.info(
                            f"Extracted PROTEIN_GOAL: {combined_structured_data['PROTEIN_GOAL']}")

                # Check for tracking consistency indicators in the text
                missing_data_indicators = [
                    r"only\s+tracked\s+(\d+)\s+day",
                    r"tracked\s+(\d+)\s+out of",
                    r"logged\s+(\d+)\s+day",
                    r"logged\s+(\d+)\s+out of",
                    r"data\s+for\s+only\s+(\d+)\s+day",
                    r"nutrition\s+(?:data|tracking|logs)?\s+(?:is|appears to be|seems)\s+(?:limited|sparse|incomplete|inconsistent)",
                    r"few\s+(?:days|entries)\s+(?:of|were)\s+track",
                    r"more\s+consistent\s+(?:with|in)\s+tracking",
                    r"not\s+(?:tracking|logging)\s+consistently",
                    r"gaps\s+in\s+(?:tracking|logging|data)",
                    r"intermittent\s+(?:tracking|logging)"
                ]

                # Check for days tracked pattern
                for pattern in missing_data_indicators:
                    match = re.search(
                        pattern, calories_protein_analysis, re.IGNORECASE)
                    if match:
                        logging.info(
                            f"Found tracking consistency issue: {match.group(0)}")
                        tracking_indicators["is_consistent"] = False
                        # If we found a number of days, store it
                        if match.groups() and match.group(1).isdigit():
                            tracking_indicators["days_tracked"] = int(
                                match.group(1))
                        break

            # Process fats/carbs analysis
            if fats_carbs_analysis:
                # Extract structured data from fats/carbs analysis
                fats_carbs_data_match = re.search(
                    r"```data\s+(.*?)\s+```", fats_carbs_analysis, re.DOTALL)

                if fats_carbs_data_match:
                    fats_carbs_data = fats_carbs_data_match.group(1)
                    logging.info(
                        f"Extracted fats/carbs structured data: {fats_carbs_data}")

                    # Extract fats data
                    fats_daily_match = re.search(
                        r"FATS_DAILY:\s+(not visible|\d+g?)", fats_carbs_data, re.IGNORECASE)
                    if fats_daily_match:
                        combined_structured_data["FATS_DAILY"] = fats_daily_match.group(
                            1)
                        logging.info(
                            f"Extracted FATS_DAILY: {combined_structured_data['FATS_DAILY']}")

                    fats_goal_match = re.search(
                        r"FATS_GOAL:\s+(not visible|\d+g?)", fats_carbs_data, re.IGNORECASE)
                    if fats_goal_match:
                        combined_structured_data["FATS_GOAL"] = fats_goal_match.group(
                            1)
                        logging.info(
                            f"Extracted FATS_GOAL: {combined_structured_data['FATS_GOAL']}")

                    # Extract carbs data
                    carbs_daily_match = re.search(
                        r"CARBS_DAILY:\s+(not visible|\d+g?)", fats_carbs_data, re.IGNORECASE)
                    if carbs_daily_match:
                        combined_structured_data["CARBS_DAILY"] = carbs_daily_match.group(
                            1)
                        logging.info(
                            f"Extracted CARBS_DAILY: {combined_structured_data['CARBS_DAILY']}")

                    carbs_goal_match = re.search(
                        r"CARBS_GOAL:\s+(not visible|\d+g?)", fats_carbs_data, re.IGNORECASE)
                    if carbs_goal_match:
                        combined_structured_data["CARBS_GOAL"] = carbs_goal_match.group(
                            1)
                        logging.info(
                            f"Extracted CARBS_GOAL: {combined_structured_data['CARBS_GOAL']}")

                # Also check fats/carbs analysis for consistency indicators
                # Only check if we haven't already found inconsistency
                if tracking_indicators["is_consistent"]:
                    for pattern in missing_data_indicators:
                        match = re.search(
                            pattern, fats_carbs_analysis, re.IGNORECASE)
                        if match:
                            logging.info(
                                f"Found tracking consistency issue in fats/carbs: {match.group(0)}")
                            tracking_indicators["is_consistent"] = False
                            # If we found a number of days, store it
                            if match.groups() and match.group(1).isdigit():
                                tracking_indicators["days_tracked"] = int(
                                    match.group(1))
                            break

            # Additional consistency checks based on structured data
            if "CALORIES_DAILY" in combined_structured_data:
                calories_value = combined_structured_data["CALORIES_DAILY"]
                if calories_value != "not visible" and calories_value.isdigit():
                    # Check if calories are suspiciously low, which could indicate inconsistent tracking
                    if int(calories_value) < 1200:
                        # Only mark as inconsistent if no more specific information was found
                        if tracking_indicators["days_tracked"] == 0:
                            logging.info(
                                f"Suspiciously low average calories: {calories_value}")
                            tracking_indicators["is_consistent"] = False

            # Prepare consistency message
            if not tracking_indicators["is_consistent"]:
                if tracking_indicators["days_tracked"] > 0:
                    tracking_indicators["consistency_message"] = (
                        f"⚠️ **Nutrition Tracking Alert**: You've only tracked {tracking_indicators['days_tracked']} "
                        f"day{'s' if tracking_indicators['days_tracked'] > 1 else ''} of nutrition data. "
                        f"For accurate analysis and better progress, aim to log your nutrition consistently each day."
                    )
                else:
                    tracking_indicators["consistency_message"] = (
                        "⚠️ **Nutrition Tracking Alert**: Your nutrition tracking appears to be inconsistent. "
                        "For accurate analysis and better progress, aim to log your nutrition consistently each day."
                    )

            # Create the combined structured data section
            combined_data = "```data\n"
            for key, value in combined_structured_data.items():
                combined_data += f"{key}: {value}\n"
            combined_data += "```\n\n"

            # Extract the analysis text (after the structured data section)
            calories_protein_text = calories_protein_analysis
            if calories_protein_data_match:
                calories_protein_text = calories_protein_analysis.split("```data")[
                    1].split("```", 1)[1]

            fats_carbs_text = fats_carbs_analysis
            if fats_carbs_data_match:
                fats_carbs_text = fats_carbs_analysis.split(
                    "```data")[1].split("```", 1)[1]

            # Combine the analysis text
            combined_text = "## Nutrition Analysis\n\n"

            # Add consistency message if needed
            if tracking_indicators["consistency_message"]:
                combined_text += tracking_indicators["consistency_message"] + "\n\n"

            if calories_protein_text.strip():
                combined_text += "### Calories and Protein Analysis\n" + \
                    calories_protein_text.strip() + "\n\n"
            if fats_carbs_text.strip():
                combined_text += "### Fats and Carbs Analysis\n" + fats_carbs_text.strip()

            # Log the extraction results
            logging.info(
                f"Combined nutrition data extraction completed with {len(combined_structured_data)} values")
            if len(combined_structured_data) == 0:
                logging.warning("No structured nutrition data was extracted!")

            # Return the combined analysis
            return combined_data + combined_text
        except Exception as e:
            logging.exception(f"Error combining nutrition analyses: {e}")
            # Fallback: Just append one analysis after the other
            return calories_protein_analysis + "\n\n" + fats_carbs_analysis

    def analyze_sleep_graph(self):
        """Analyzes the sleep graph using gemini-2.0-flash."""
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping sleep graph analysis.")
            return "Gemini API key not provided, skipping analysis."
        try:
            logging.info("Analyzing sleep graph with gemini-2.0-flash...")
            # Wait for the graph element to be present or for a timeout
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))

            self._click_3m_button_if_exists()  # Click 3M button if present

            time.sleep(2)
            screenshot_path = "sleep_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
                        Okay lets check in on your sleep graph!

                        Analyze this sleep graph from a personal training app. Compare the most recent week of sleep data to the sleep data from the rest of the 3 month graph.

                        VERY IMPORTANT: If there are very few data points (less than 7 days of data) or the graph appears to be mostly empty, respond with EXACTLY: "Minimal sleep data available. Please encourage tracking sleep consistently for more meaningful analysis."
                        
                        If there is sufficient data, provide a concise review, keeping it short and very simple, like these examples:

                        Example 1 (Good sleep consistency):
                        *Really happy with you getting consistent 8 hours of sleep every night this week!*

                        Example 2 (Sporadic sleep):
                        *Sleep graph is looking a little sporadic this week. Let's try to aim for 8 hours every night, at the same time every night. This will get your body clock working correctly and you'll get a novel boost to your metabolism!*

                        Focus on:
                        - the trend of the graph - we want a nice smooth line of points - between 7-9 hours of sleep every night - a graph that is sporadic is not good.
                        - Consistency of sleep during the week(are they sleeping roughly the same hours each night?).
                        - Average hours of sleep during the week.
                        - Compare this week's consistency ( or the last section of the graph)  to the overall trend in the graph (last 3 months).
                        - Keep the tone positive and encouraging.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Sleep Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])
            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5000)
            )
            try:
                analysis = response.text
                print("\n--- Gemini Response (Sleep Analysis) ---")
                print(analysis)
            except Exception as e:
                logging.warning(
                    f"Error accessing response.text for sleep analysis: {e}")
                # Try alternative approach to get the text
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        analysis = response.candidates[0].content.parts[0].text
                    else:
                        # Fallback message
                        analysis = "Minimal sleep data available. Please encourage tracking sleep consistently for more meaningful analysis."
                        logging.warning(
                            "No candidates in response, using fallback message")
                except Exception as fallback_error:
                    logging.exception(
                        f"Error in fallback handling: {fallback_error}")
                    analysis = "Minimal sleep data available. Please encourage tracking sleep consistently for more meaningful analysis."

            return analysis
        except TimeoutException:
            return "No sleep data available."

        except Exception as e:
            logging.exception(f"Error analyzing sleep graph: {e}")
            return f"Error: {e}"

    def analyze_steps_graph(self):
        """Analyzes the steps graph using gemini-2.0-flash."""
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping steps graph analysis.")
            return "Gemini API key not provided, skipping analysis."
        try:
            logging.info("Analyzing steps graph with gemini-2.0-flash...")
            self.navigate_to_steps_graphs()
            # Wait for the graph element to be present or for a timeout
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))

            # IMPORTANT CHANGE: Removed 3M button click to stay on 1-month view
            logging.info("Staying on 1-month view for steps analysis")
            time.sleep(2)

            # NEW: Scroll down to make dates visible at the bottom of the graph
            logging.info("Scrolling down to make dates visible")
            self.driver.execute_script("window.scrollBy(0, 150);")
            time.sleep(1)  # Wait for scroll to complete

            screenshot_path = "steps_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
                        Analyze the steps graph from this personal training app.
                        
                        VERY IMPORTANT: If there are very few data points (less than 7 days of data) or if the graph appears to be mostly empty with sporadic data, respond with "AVAILABLE_STEPS_DATA: yes" on the first line and then in a new paragraph respond with EXACTLY: "Steps data is available but sporadic. Please encourage more consistent step tracking."
                        
                        If there is sufficient data, respond with "AVAILABLE_STEPS_DATA: yes" on the first line, followed by an analysis of the steps data in the structured format below.
                        
                        If there is absolutely no data visible, respond with "AVAILABLE_STEPS_DATA: no" on the first line, followed by a simple statement indicating no step data is found.
                        
                        ```data
                        MEETS_10K_GOAL: [consistently/sometimes/rarely/never]
                        AVERAGE_STEPS: [numeric value if visible, "not visible" if not]
                        HIGHEST_STEPS: [numeric value if visible, "not visible" if not]
                        TREND: [improving/declining/consistent/inconsistent]
                        ```

                        Example for data that is visible:
                        ```
                        AVAILABLE_STEPS_DATA: yes
                        
                        ```data
                        MEETS_10K_GOAL: sometimes
                        AVERAGE_STEPS: 7.5k
                        HIGHEST_STEPS: 11.2k
                        TREND: improving
                        ```
                        
                        Then add a very brief, positive summary of what you see in 1-2 sentences.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Steps Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])
            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000
                )
            )

            try:
                analysis = response.text
                print("\n--- Gemini Response (Steps Analysis) ---")
                print(analysis)
            except Exception as e:
                logging.warning(f"Error accessing response.text for steps analysis: {e}")
                # Try alternative approach to get the text
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        analysis = response.candidates[0].content.parts[0].text
                    else:
                        # Fallback message
                        analysis = "AVAILABLE_STEPS_DATA: yes\n\nSteps data is available but sporadic. Please encourage more consistent step tracking."
                        logging.warning("No candidates in response, using fallback message")
                except Exception as fallback_error:
                    logging.exception(f"Error in fallback handling: {fallback_error}")
                    analysis = "AVAILABLE_STEPS_DATA: yes\n\nSteps data is available but sporadic. Please encourage more consistent step tracking."

            return analysis
        except TimeoutException:
            return "AVAILABLE_STEPS_DATA: no\n\nNo steps data available."
        except Exception as e:
            logging.exception(f"Error analyzing steps graph: {e}")
            return f"Error: {e}"
