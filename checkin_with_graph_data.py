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
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import requests  # Add requests import for GraphQL API calls

# THIS IS THE EDITED VERSION WITH MACRO DATA AND FIRST NAME ADDRESSING
print("**** RUNNING THE UPDATED VERSION WITH MACRO DATA AND FIRST NAME ADDRESSING ****")
print("**** UPDATED MODEL: gemini-2.0-flash-thinking-exp-01-21 ****")

# --- Function to find available ChromeDriver ---


def find_chromedriver():
    """Find a valid ChromeDriver executable from multiple common locations"""

    # List of potential ChromeDriver locations
    potential_paths = [
        # Original path from script
        r"C:\SeleniumDrivers\chromedriver.exe",
        # Common Windows locations
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
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
    def __init__(self, openai_api_key=None):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.openai_api_key = openai_api_key

        # Define the output directory and ensure it exists
        self.output_directory = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"
        try:
            os.makedirs(self.output_directory, exist_ok=True)
            logging.info(
                f"Ensured output directory exists: {self.output_directory}")

        except OSError as e:
            logging.error(
                f"Error creating output directory {self.output_directory}: {e}")
            # Decide if you want to raise the error or continue without saving files
            # For now, let's log and continue
            self.output_directory = None  # Set to None to prevent saving errors later

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
        chrome_options.binary_location = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"

        try:
            # Find ChromeDriver
            chromedriver_path = find_chromedriver()

            if chromedriver_path:
                print(f"Using ChromeDriver: {chromedriver_path}")
                service = ChromeService(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(
                    service=service, options=chrome_options)
            else:
                # Fall back to webdriver-manager if no ChromeDriver found
                print("No ChromeDriver found. Falling back to webdriver-manager...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(
                    service=service, options=chrome_options)

            self.wait = WebDriverWait(self.driver, 20)
            # New: retrieve API token from cookies for GraphQL
            try:
                auth_cookie = self.driver.get_cookie('auth_token')
                self.api_token = auth_cookie['value'] if auth_cookie else None
            except Exception:
                self.api_token = None
            logging.info("Chrome initialized successfully!")

        except Exception as e:
            logging.exception(
                f"Failed to initialize Chrome or Gemini API: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    # Add GraphQL fetch helper to the class
    def fetch_graphql(self, query, variables=None):
        """Send a GraphQL request and return JSON, with debug prints."""
        import requests
        url = "https://www.trainerize.com/.apps/api/graphql"
        headers = {"Content-Type": "application/json"}
        if hasattr(self, 'api_token') and self.api_token:
            headers['Authorization'] = f"Bearer {self.api_token}"
        payload = {'query': query, 'variables': variables or {}}
        print(f"DEBUG GRAPHQL REQUEST: {payload}")
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(
                f"DEBUG GRAPHQL RESPONSE: status={response.status_code}, body={response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ERROR in GraphQL request: {e}")
            return None

    def cleanup_previous_files(self):
        """Cleans up files from previous runs in the output directories."""
        try:
            logging.info("Cleaning up files from previous runs...")

            # Clean videos directory
            videos_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output"
            # Clean checkin reviews directory
            reviews_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"

            # Ensure directories exist
            os.makedirs(videos_dir, exist_ok=True)
            os.makedirs(reviews_dir, exist_ok=True)

            # Clean videos directory
            for file in os.listdir(videos_dir):
                if file.endswith('.mp4'):  # Only delete video files
                    try:
                        file_path = os.path.join(videos_dir, file)
                        os.remove(file_path)
                        logging.info(f"Deleted video file: {file}")
                    except Exception as e:
                        logging.warning(
                            f"Could not delete video file {file}: {e}")

            # Clean checkin reviews directory
            for file in os.listdir(reviews_dir):
                if file.endswith(('.pdf', '.json')):  # Delete PDFs and JSON files
                    try:
                        file_path = os.path.join(reviews_dir, file)
                        os.remove(file_path)
                        logging.info(f"Deleted review file: {file}")
                    except Exception as e:
                        logging.warning(
                            f"Could not delete review file {file}: {e}")

            logging.info("Cleanup of previous files completed.")

        except Exception as e:
            logging.exception(
                "Error during cleanup of previous files:", exc_info=e)

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
        """Save the prepared data to a JSON file in the specified output directory."""
        import json
        import os  # Ensure os is imported within the function if not globally

        # Check if the output directory is valid
        if not self.output_directory:
            logging.error(
                "Output directory not set or could not be created. Cannot save JSON file.")
            return None

        # Add today's date to the filename
        today_str = datetime.now().strftime('%Y-%m-%d')
        base_filename = f"{client_name.replace(' ', '_')}_{today_str}_fitness_wrapped_data.json"
        # Construct the full path
        full_filename = os.path.join(self.output_directory, base_filename)

        try:
            with open(full_filename, 'w') as f:  # Use full_filename here
                json.dump(fitness_wrapped_data, f, indent=4)
            logging.info(f"Saved fitness wrapped data to {full_filename}")
            return full_filename  # Return the full path
        except Exception as e:
            logging.exception(
                f"Error saving fitness wrapped data to {full_filename}: {e}")
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
                prompt += f"""
                - Average step count: {fitness_wrapped_data['step_count']}
                """
            else:
                prompt += """
                - Steps: NO DATA (explain how tracking daily steps helps monitor non-exercise activity and contributes to overall calorie expenditure)
                """

            # Include sleep data if available, otherwise note it's missing
            if has_sleep_data and fitness_wrapped_data.get('sleep_hours', 'Not Recorded') != 'Not Recorded':
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
            import os  # Ensure os is imported within the function if not globally

            # *** ADDED LOGGING FOR DEBUGGING STEP DATA ***
            logging.info(
                f"DEBUG: create_checkin_review_pdf for {client_name} - Received step_count: {fitness_wrapped_data.get('step_count', 'KEY_MISSING')}")
            logging.info(
                f"DEBUG: create_checkin_review_pdf for {client_name} - Received has_steps_data: {fitness_wrapped_data.get('has_steps_data', 'KEY_MISSING')}")
            # *********************************************

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
            base_pdf_filename = f"{safe_client_name}_{today_str}_check_in_review.pdf"
            # Construct the full path
            full_pdf_filename = os.path.join(
                self.output_directory, base_pdf_filename)

            logging.info(f"Creating PDF document: {full_pdf_filename}")

            # Create the document using the full path
            doc = SimpleDocTemplate(
                full_pdf_filename,  # Use the full path here
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

            # --- Revised Step Display Logic ---
            if has_steps_data:
                # Check the specific value of step_count
                current_step_count_value = fitness_wrapped_data.get(
                    'step_count', 'Not Recorded')

                if current_step_count_value == "Inconsistent Tracking":
                    # Specific message for inconsistency
                    lifestyle_stats += f"Steps: Inconsistent Tracking<br/>"
                elif current_step_count_value != "Not Recorded":
                    # We have data AND a specific numerical/estimated count
                    lifestyle_stats += f"Average Daily Steps: {current_step_count_value}<br/>"
                else:
                    # We have has_steps_data=True, but step_count ended up as "Not Recorded"
                    # This implies other data (like trend) might exist, but not a usable count or inconsistency status
                    steps_trend_info = fitness_wrapped_data.get(
                        'steps_trend', 'Not Recorded')  # Safely get trend
                    if steps_trend_info != 'Not Recorded':
                        # Show trend instead
                        lifestyle_stats += f"Steps Trend: {steps_trend_info.capitalize()} (Avg N/A)<br/>"
                    else:
                        # Generic message if no trend either
                        lifestyle_stats += f"Steps Tracked (Average N/A)<br/>"
            else:
                # No step data at all (has_steps_data is False)
                lifestyle_stats += f"Average Daily Steps: <i>Not Recorded</i> - Recording steps helps us monitor your daily activity level<br/>"
            # --- End Revised Step Display Logic ---

            if has_sleep_data and fitness_wrapped_data['sleep_hours'] != "Not Recorded":
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
            logging.info(
                f"PDF document created successfully: {full_pdf_filename}")
            return full_pdf_filename  # Return the full path

        except ImportError as ie:
            logging.error(f"Missing required library for PDF generation: {ie}")
            print(f"Please install missing library: {ie}")
            return None
        except Exception as e:
            logging.exception(
                f"Error creating check-in review PDF at {full_pdf_filename}: {e}")
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
                # Construct the filename pattern using the output directory
                safe_client_name = client_name.replace(' ', '_')
                pattern = os.path.join(
                    self.output_directory, f"{safe_client_name}_*_fitness_wrapped_data.json")
                matching_files = sorted(
                    glob.glob(pattern), reverse=True)  # Most recent first

                if not matching_files:
                    logging.warning(
                        f"No JSON file found for client: {client_name} in {self.output_directory}")
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

    def prepare_fitness_wrapped_data(self, client_name, bodyweight_availability, bodyweight_structured_data, bodyweight_analysis_text, nutrition_analysis_results,
                                     sleep_availability, sleep_analysis_text, average_sleep_hours,
                                     steps_availability, steps_structured_data, steps_analysis_text,
                                     photos_analysis, weight_goal_text, weekly_summary_data,
                                     workouts_completed_analysis, total_workout_stats_analysis, workout_data_list):
        """Convert Trainerize data into the format expected by FitnessWrappedGenerator with updated sleep and steps data handling."""
        import re
        from datetime import datetime, timedelta, date
        import logging

        logging.info(
            f"DEBUG: prepare_fitness_wrapped_data for {client_name} - Received steps_availability: {steps_availability}, steps_structured_data: {steps_structured_data}")

        # Initialize nutrition tracking consistency indicators
        nutrition_tracking_consistent = True
        nutrition_tracking_days = 0
        nutrition_consistency_message = ""

        combined_nutrition_text = (nutrition_analysis_results.get('calories_protein', {}).get('analysis_text', '') +
                                   "\\n" +
                                   nutrition_analysis_results.get('fats_carbs', {}).get('analysis_text', ''))
        logging.info(
            f"Combined nutrition analysis text (for consistency check): {combined_nutrition_text[:300]}...")
        consistency_warning_match = re.search(
            r"⚠️\\s*\\*\\*Nutrition Tracking Alert\\*\\*:\\s*(.*?)(?:\\n|\\Z)", combined_nutrition_text, re.DOTALL)
        if consistency_warning_match:
            nutrition_consistency_message = consistency_warning_match.group(
                1).strip()
            nutrition_tracking_consistent = False
            days_tracked_match = re.search(
                r"only tracked (\\d+) day", nutrition_consistency_message)
            if days_tracked_match and days_tracked_match.group(1).isdigit():
                nutrition_tracking_days = int(days_tracked_match.group(1))
                logging.info(
                    f"Extracted nutrition tracking days: {nutrition_tracking_days}")
        else:
            logging.info(
                "No nutrition consistency warning found in combined text.")

        logging.info(f"===== PROCESSING WEIGHT DATA FOR {client_name} =====")
        logging.info(f"Bodyweight Availability: {bodyweight_availability}")
        logging.info(
            f"Bodyweight Structured Data: {bodyweight_structured_data}")

        start_weight_num = None
        current_weight_num = None
        total_weight_change_val = 0
        has_reliable_weight_data_flag = False
        weight_trend_str = bodyweight_structured_data.get(
            'TREND', "Not Recorded")
        current_date_from_graph_str = bodyweight_structured_data.get(
            'CURRENT_DATE', "Not Recorded")
        start_date_from_graph_str = bodyweight_structured_data.get(
            'STARTING_DATE', "Not Recorded")

        if bodyweight_availability == "substantial":
            logging.info("Substantial bodyweight data for the current week.")
            raw_curr = bodyweight_structured_data.get(
                'CURRENT_WEIGHT', "Not Recorded")
            raw_start = bodyweight_structured_data.get(
                'STARTING_WEIGHT', "Not Recorded")
            if raw_curr != "Not Recorded" and raw_curr.replace('.', '', 1).isdigit():
                current_weight_num = float(raw_curr)
                has_reliable_weight_data_flag = True
            if raw_start != "Not Recorded" and raw_start.replace('.', '', 1).isdigit():
                start_weight_num = float(raw_start)

            if isinstance(start_weight_num, float) and isinstance(current_weight_num, float):
                # Use trend to ensure calculation direction if needed, though Gemini prompt asks for start/current correctly.
                calc_start, calc_curr = start_weight_num, current_weight_num
                if weight_trend_str == "downward" and start_weight_num < current_weight_num:
                    calc_start, calc_curr = current_weight_num, start_weight_num
                elif weight_trend_str == "upward" and start_weight_num > current_weight_num:
                    calc_start, calc_curr = current_weight_num, start_weight_num
                total_weight_change_val = calc_start - calc_curr  # Positive for loss
        elif bodyweight_availability == "minimal":
            logging.info(
                "Minimal bodyweight data for current week. Current weight set to 'Not Recorded'.")
            # Still get historical start if available
            raw_start = bodyweight_structured_data.get(
                'STARTING_WEIGHT', "Not Recorded")
            if raw_start != "Not Recorded" and raw_start.replace('.', '', 1).isdigit():
                start_weight_num = float(raw_start)
            has_reliable_weight_data_flag = False
        else:  # 'none' or error states
            logging.info(
                f"Bodyweight availability '{bodyweight_availability}'. Current week data considered 'Not Recorded'.")
            has_reliable_weight_data_flag = False

        weight_goal_data = self.extract_weight_goal(
            weight_goal_text)  # Existing logic for goal is fine
        client_weight_goal_dict = {'target': float(weight_goal_data['target'])} if weight_goal_data and 'target' in weight_goal_data and str(
            weight_goal_data['target']).replace('.', '', 1).isdigit() and 30 <= float(weight_goal_data['target']) <= 250 else False

        current_weight_message_str = "Keep up the good work with your fitness journey! Consistency is key."
        if has_reliable_weight_data_flag and isinstance(current_weight_num, float) and isinstance(start_weight_num, float):
            if total_weight_change_val > 0:
                current_weight_message_str = f"Fantastic! Total loss of {abs(total_weight_change_val):.1f}kg. Keep it up!"
            elif total_weight_change_val < 0:
                current_weight_message_str = f"Great! Total gain of {abs(total_weight_change_val):.1f}kg. Solid progress!"
            else:
                current_weight_message_str = "Weight is stable. Let's keep monitoring!"
        elif bodyweight_availability in ["none", "minimal"]:
            current_weight_message_str = "Let's focus on consistent weight tracking this week to see your progress!"

        # Date ranges and workout stats (existing logic seems mostly fine here)
        today_dt = datetime.now().date()
        current_week_start_dt = today_dt - timedelta(days=today_dt.weekday())
        current_week_end_dt = current_week_start_dt + timedelta(days=6)
        previous_week_start_dt = current_week_start_dt - timedelta(weeks=1)
        previous_week_end_dt = current_week_end_dt - timedelta(weeks=1)

        current_week_workout_count, workout_names, total_weight_lifted_val, total_reps_val, total_sets_val, _, _ = self.calculate_workout_stats_for_date_range(
            workout_data_list, current_week_start_dt, current_week_end_dt
        )
        _, _, prev_week_weight, _, _, _, _ = self.calculate_workout_stats_for_date_range(
            workout_data_list, previous_week_start_dt, previous_week_end_dt
        )
        workload_increase = 0
        if prev_week_weight > 0:
            workload_increase = (
                (total_weight_lifted_val - prev_week_weight) / prev_week_weight) * 100
            workload_increase = max(min(workload_increase, 300), -100)

        start_day_str = current_week_start_dt.strftime('%d %B').lstrip('0')
        end_day_str = current_week_end_dt.strftime('%d %B').lstrip('0')
        date_range_str = f"{start_day_str} - {end_day_str}"

        has_up_to_date_photos_flag = "up-to-date" in photos_analysis.lower(
        ) or "looking great" in photos_analysis.lower()  # Simplified

        # --- Steps Data ---
        step_count_str = "Not Recorded"
        highest_steps_str = "Not Recorded"
        has_steps_data_flag = False
        steps_trend_str = "Not Recorded"
        if steps_availability == "substantial":
            avg_steps_raw = steps_structured_data.get(
                'AVERAGE_STEPS', "Not Recorded")
            if avg_steps_raw.lower() == "inconsistent tracking":
                step_count_str = "Inconsistent Tracking"
                has_steps_data_flag = True
            elif avg_steps_raw != "Not Recorded" and avg_steps_raw.lower() != "not visible":
                step_count_str = avg_steps_raw
                has_steps_data_flag = True
            highest_raw = steps_structured_data.get(
                'HIGHEST_STEPS', "Not Recorded")
            if highest_raw != "Not Recorded" and highest_raw.lower() != "not visible":
                highest_steps_str = highest_raw
            steps_trend_str = steps_structured_data.get(
                'TREND', "Not Recorded")
        elif steps_availability == "minimal":
            has_steps_data_flag = False  # Minimal is not enough for main display
            steps_trend_str = steps_structured_data.get(
                'TREND', "Not Recorded")  # Trend might still be useful
            if steps_trend_str != "Not Recorded":
                has_steps_data_flag = True  # If only trend, still some data
        # else: step values remain "Not Recorded", has_steps_data_flag remains False

        # --- Sleep Data ---
        sleep_hours_str = "Not Recorded"
        has_sleep_data_flag = False
        if sleep_availability == "substantial":
            if average_sleep_hours and average_sleep_hours.lower() != "not visible":
                sleep_hours_str = average_sleep_hours
                has_sleep_data_flag = True
            else:
                sleep_hours_str = "Tracking Consistent (Avg N/A)"
                has_sleep_data_flag = True
        # elif sleep_availability == "minimal": has_sleep_data_flag remains False
        # else: has_sleep_data_flag remains False

        # --- Nutrition Data ---
        calories_consumed_str = "Not Recorded"
        protein_consumed_str = "Not Recorded"
        fats_consumed_str = "Not Recorded"
        carbs_consumed_str = "Not Recorded"
        has_nutrition_data_flag = False
        cp_avail = nutrition_analysis_results.get(
            'calories_protein', {}).get('availability', 'error')
        fc_avail = nutrition_analysis_results.get(
            'fats_carbs', {}).get('availability', 'error')
        if cp_avail == "substantial":
            cp_sd = nutrition_analysis_results.get(
                'calories_protein', {}).get('structured_data', {})
            cals_raw = cp_sd.get("CALORIES_DAILY", "not visible")
            if cals_raw.lower() != "not visible" and cals_raw.isdigit():
                calories_consumed_str = cals_raw
                has_nutrition_data_flag = True
            prot_raw = cp_sd.get(
                "PROTEIN_DAILY", "not visible").replace('g', '').strip()
            if prot_raw.lower() != "not visible" and prot_raw.isdigit():
                protein_consumed_str = f"{prot_raw}g"
                has_nutrition_data_flag = True
        if fc_avail == "substantial":
            fc_sd = nutrition_analysis_results.get(
                'fats_carbs', {}).get('structured_data', {})
            fats_raw = fc_sd.get(
                "FATS_DAILY", "not visible").replace('g', '').strip()
            if fats_raw.lower() != "not visible" and fats_raw.isdigit():
                fats_consumed_str = f"{fats_raw}g"
                has_nutrition_data_flag = True
            carbs_raw = fc_sd.get(
                "CARBS_DAILY", "not visible").replace('g', '').strip()
            if carbs_raw.lower() != "not visible" and carbs_raw.isdigit():
                carbs_consumed_str = f"{carbs_raw}g"
                has_nutrition_data_flag = True
        # If all are still "Not Recorded", ensure flag is false.
        if all(val == "Not Recorded" for val in [calories_consumed_str, protein_consumed_str, fats_consumed_str, carbs_consumed_str]):
            has_nutrition_data_flag = False

        # Top exercises and most improved lift (existing logic seems okay)
        # ... (top_exercises and client_most_improved_lift_data calculation) ...
        top_exercises = []
        try:
            top_exercise_names = self.find_top_performing_exercises(
                workout_data_list, current_week_start_dt, current_week_end_dt,
                previous_week_start_dt, previous_week_end_dt, 3
            )
            _, _, _, _, _, _, current_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list, current_week_start_dt, current_week_end_dt, target_exercises=top_exercise_names
            )
            _, _, _, _, _, _, previous_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list, previous_week_start_dt, previous_week_end_dt, target_exercises=top_exercise_names
            )
            for exercise_name in top_exercise_names:
                current = current_exercise_workload.get(exercise_name, 0)
                previous = previous_exercise_workload.get(exercise_name, 0)
                improvement = ((current - previous) / previous) * \
                    100 if previous > 0 else (100 if current > 0 else 0)
                improvement = max(min(improvement, 500), -100)
                top_exercises.append(
                    {"name": exercise_name, "improvement": round(improvement, 1)})
        except Exception as e:
            logging.exception(f"Err top_exercises: {e}")
            top_exercises = []

        client_most_improved_lift_data = self.determine_client_most_improved_lift(
            workout_data_list, current_week_start_dt, current_week_end_dt, previous_week_start_dt, previous_week_end_dt
        )
        actual_workouts_this_week_count = current_week_workout_count
        personalized_msg_val = self.generate_personalized_message(
            client_name, actual_workouts_this_week_count, client_most_improved_lift_data
        )

        fitness_wrapped_data = {
            "name": client_name,
            "business_name": "Coco's",
            "date_range": date_range_str,
            "start_weight": start_weight_num if isinstance(start_weight_num, float) else "Not Recorded",
            "current_weight": current_weight_num if isinstance(current_weight_num, float) else "Not Recorded",
            # This is the calculated numeric change
            "weight_loss": total_weight_change_val,
            "weight_change": total_weight_change_val,
            "total_weight_change": total_weight_change_val,
            "weight_trend": weight_trend_str,
            "weight_start_date": start_date_from_graph_str,
            "weight_current_date": current_date_from_graph_str,
            "weight_goal": client_weight_goal_dict,
            "current_weight_message": current_weight_message_str,
            "workouts_this_week": actual_workouts_this_week_count,
            "workout_types": list(set(w['type'] for w in workout_data_list if 'type' in w and current_week_start_dt <= datetime.strptime(w['date'], '%Y-%m-%d' if '-' in w['date'] else '%d %b %Y').date() <= current_week_end_dt)) if workout_data_list else [],
            "total_reps": total_reps_val,
            "total_sets": total_sets_val,
            "total_weight_lifted": total_weight_lifted_val,
            "workload_increase": round(workload_increase, 2),
            "calories_consumed": calories_consumed_str,
            "protein_consumed": protein_consumed_str,
            "fats_consumed": fats_consumed_str,
            "carbs_consumed": carbs_consumed_str,
            "nutrition_tracking_consistent": nutrition_tracking_consistent,
            "nutrition_tracking_days": nutrition_tracking_days,
            "nutrition_consistency_message": nutrition_consistency_message,
            "step_count": step_count_str,
            "highest_steps": highest_steps_str,
            "steps_trend": steps_trend_str,
            "sleep_hours": sleep_hours_str,
            "most_improved_exercise": client_most_improved_lift_data,
            "personalized_message": personalized_msg_val,
            "top_exercises": top_exercises if top_exercises else [],
            "has_weight_data": has_reliable_weight_data_flag,
            "has_steps_data": has_steps_data_flag,
            "has_sleep_data": has_sleep_data_flag,
            "has_nutrition_data": has_nutrition_data_flag,
            "has_up_to_date_photos": has_up_to_date_photos_flag,
            "has_workout_data": actual_workouts_this_week_count > 0,
            "has_workload_data": prev_week_weight > 0 and total_weight_lifted_val > 0,
            "has_exercise_data": len(top_exercises) > 0 and any(ex['improvement'] != 0 for ex in top_exercises),
            "has_reliable_weight_data": has_reliable_weight_data_flag
        }
        logging.info(
            f"Final fitness_wrapped_data keys for {client_name}: has_weight_data={fitness_wrapped_data['has_weight_data']}, current_weight={fitness_wrapped_data['current_weight']}, etc.")
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

    def determine_client_most_improved_lift(self, workout_data_list, current_week_start, current_week_end, previous_week_start, previous_week_end):
        """
        Determines the client's single most improved lift/exercise for the week based on workload.

        Args:
            workout_data_list: List of all workout dictionaries.
            current_week_start: datetime.date object for the start of the current week.
            current_week_end: datetime.date object for the end of the current week.
            previous_week_start: datetime.date object for the start of the previous week.
            previous_week_end: datetime.date object for the end of the previous week.

        Returns:
            A dictionary with details of the most improved lift.
            Example: {
                "name": "Barbell Bench Press",
                "improvement_type": "workload",
                "current_performance_desc": "100kg for 5 reps",
                "improvement_highlight": "+20% workload"
            }
            Returns N/A values if no improvement or data.
        """
        logging.info(
            f"Determining most improved lift for current week {current_week_start}-{current_week_end} vs previous week {previous_week_start}-{previous_week_end}")
        try:
            # Get workout data for the current and previous weeks
            _, _, _, _, _, current_week_workouts_data, _ = \
                self.calculate_workout_stats_for_date_range(
                    workout_data_list, current_week_start, current_week_end)
            _, _, _, _, _, prev_week_workouts_data, _ = \
                self.calculate_workout_stats_for_date_range(
                    workout_data_list, previous_week_start, previous_week_end)

            all_exercise_names = set()
            for wd in current_week_workouts_data + prev_week_workouts_data:
                for ex in wd.get('exercises', []):
                    all_exercise_names.add(ex['name'].strip())

            if not all_exercise_names:
                logging.warning(
                    "No exercises found in the specified date ranges.")
                return {
                    "name": "N/A", "improvement_type": "none",
                    "current_performance_desc": "No workout data", "improvement_highlight": ""
                }

            exercise_improvements = []

            for ex_name in all_exercise_names:
                current_workload = 0
                current_best_set_weight = 0
                current_best_set_reps = 0

                for workout in current_week_workouts_data:
                    for exercise in workout.get('exercises', []):
                        if exercise['name'].strip() == ex_name:
                            for s_set in exercise.get('sets', []):
                                weight = s_set.get('weight', 0)
                                reps = s_set.get('reps', 0)
                                current_workload += weight * reps
                                if weight > current_best_set_weight:
                                    current_best_set_weight = weight
                                    current_best_set_reps = reps
                                elif weight == current_best_set_weight and reps > current_best_set_reps:
                                    current_best_set_reps = reps

                prev_workload = 0
                for workout in prev_week_workouts_data:
                    for exercise in workout.get('exercises', []):
                        if exercise['name'].strip() == ex_name:
                            for s_set in exercise.get('sets', []):
                                prev_workload += s_set.get('weight', 0) * \
                                    s_set.get('reps', 0)

                improvement_percentage = 0
                if prev_workload > 0:
                    improvement_percentage = (
                        (current_workload - prev_workload) / prev_workload) * 100
                elif current_workload > 0:  # New exercise or no prev workload
                    improvement_percentage = 100  # Assign a high value for new exercises with workload

                if current_workload > 0:  # Only consider exercises performed this week
                    exercise_improvements.append({
                        'name': ex_name,
                        'current_workload': current_workload,
                        'prev_workload': prev_workload,
                        'improvement': improvement_percentage,
                        'current_best_set_weight': current_best_set_weight,
                        'current_best_set_reps': current_best_set_reps
                    })

            if not exercise_improvements:
                logging.warning(
                    "No exercises with workload found this week to determine improvement.")
                return {
                    "name": "N/A", "improvement_type": "none",
                    "current_performance_desc": "No workouts logged this week", "improvement_highlight": ""
                }

            # Sort by improvement percentage (descending)
            exercise_improvements.sort(
                key=lambda x: x['improvement'], reverse=True)

            most_improved = exercise_improvements[0]

            # Cap improvement at reasonable values for display
            display_improvement = max(
                min(most_improved['improvement'], 500), -100)

            current_performance_desc = f"{most_improved['current_best_set_weight']}kg for {most_improved['current_best_set_reps']} reps"
            if most_improved['current_best_set_weight'] == 0 and most_improved['current_best_set_reps'] == 0:
                current_performance_desc = "bodyweight or reps"

            improvement_highlight_str = ""
            if most_improved['prev_workload'] == 0 and most_improved['current_workload'] > 0:
                improvement_highlight_str = "great job hitting it this week!"
            elif display_improvement > 0:
                improvement_highlight_str = f"a {display_improvement:.0f}% increase in workload!"
            elif display_improvement < 0:
                improvement_highlight_str = f"a {abs(display_improvement):.0f}% decrease in workload."
            else:  # display_improvement == 0
                improvement_highlight_str = "consistent workload!"

            result = {
                "name": most_improved['name'],
                "improvement_type": "workload",  # Could be 'weight' or 'reps' if logic changes
                "current_performance_desc": current_performance_desc,
                "improvement_highlight": improvement_highlight_str
            }
            logging.info(f"Most improved lift: {result}")
            return result

        except Exception as e:
            logging.exception(f"Error determining most improved lift: {e}")
            return {
                "name": "N/A", "improvement_type": "error",
                "current_performance_desc": "Error in analysis", "improvement_highlight": ""
            }

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

            # Wait longer for the page to load after login
            time.sleep(5)

            clients_link_locator = (
                By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(
                    EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
                time.sleep(3)  # Wait longer after clicking
            except TimeoutException as te:
                logging.error(
                    f"TimeoutException while waiting for Clients link: {te.msg}")
                return False

            logging.info(
                "Entering client name into the search bar on the Clients page...")
            search_input_locator = (
                By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            try:
                search_input = self.wait.until(
                    EC.presence_of_element_located(search_input_locator))
                search_input.clear()
                time.sleep(1)  # Wait after clearing
                search_input.send_keys(client_name)
                logging.info(
                    "Waiting extra time for search results grid to load...")
                time.sleep(5)  # Increase wait after typing search term
            except TimeoutException:
                logging.error("Could not find search input")
                return False

            logging.info(
                "Clicking on the client's name in the search results...")
            # Use title attribute and lowercase comparison for robustness
            client_link_locator = (
                By.XPATH, f"//a[translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{client_name.lower()}']")
            try:
                # Wait specifically for the link element to be PRESENT in the DOM first
                self.wait.until(
                    EC.presence_of_element_located(client_link_locator))
                logging.info(
                    "Client link element found in DOM, now waiting for clickable...")
                client_link = self.wait.until(
                    EC.element_to_be_clickable(client_link_locator))
                client_link.click()
                time.sleep(4)  # Increase wait after clicking link
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
                time.sleep(3)  # Wait longer after clicking
            except (TimeoutException, NoSuchElementException) as e:
                logging.error(
                    f"Could not find or click 'Open' button for {client_name}: {e}")
                return False

            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            time.sleep(2)  # Wait after switching tabs
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
                        Analyze this bodyweight graph from a fitness app.

                        IMPORTANT: Start your entire response *immediately* with the data availability assessment using this EXACT format:
                        AVAILABILITY: [none/minimal/substantial] (Assess this based on the data points visible for the *most recent week*.)

                        Then, if AVAILABILITY is 'substantial' or 'minimal' (meaning some data exists), provide the following structured data:
                        ```data
                        STARTING_WEIGHT: [number or "not visible"] kg
                        STARTING_DATE: [date in DD-MM-YYYY format or "not visible"]
                        CURRENT_WEIGHT: [number or "not visible"] kg
                        CURRENT_DATE: [date in DD-MM-YYYY format or "not visible"]
                        TREND: [upward/downward/stable or "not visible"]
                        ```

                        After the AVAILABILITY line (and the ```data block if applicable), provide a brief textual analysis.
                        If AVAILABILITY is 'none' or 'minimal' for the recent week, the textual analysis should be a brief, encouraging message about tracking weight consistently.
                        If AVAILABILITY is 'substantial' for the recent week:
                        CRITICALLY, for the "Recent Changes" point, focus specifically on the **most recent week's (last 7 days')** trend and data points visible on the graph:
                        - Overall trend direction(weight loss, gain, or stable over the entire graph period)
                        - Rate of change(rapid, moderate, slow over the entire graph period)
                        - Pattern(consistent, fluctuating, plateaued over the entire graph period)
                        - Recent changes (Specifically analyze the **most recent week's performance** based on the last ~7 days of data points visible on the graph. How does this very recent period compare to the overall trend?)

                        Focus on extracting the most accurate numerical data possible from the graph.
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\\n--- Gemini Prompt (Bodyweight Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])

            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5000)
            )

            raw_analysis = ""
            try:
                raw_analysis = response.text
                print("\\n--- Gemini Response (Bodyweight Analysis) ---")
                print(raw_analysis)
            except Exception as e:
                logging.warning(
                    f"Error accessing response.text for bodyweight analysis: {e}")
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        raw_analysis = response.candidates[0].content.parts[0].text
                        print(
                            "\\n--- Gemini Response (Bodyweight Analysis - Fallback) ---")
                        print(raw_analysis)
                    else:
                        analysis = "Unable to analyze bodyweight data with current model. Your weight progress looks on track though!"
                        logging.warning(
                            "No candidates in response, using fallback message")
                        return "error", {}, analysis  # Modified return
                except Exception as fallback_error:
                    logging.exception(
                        f"Error in fallback handling: {fallback_error}")
                    analysis = "Unable to analyze bodyweight data. Your weight tracking is important for your progress."
                    return "error", {}, analysis  # Modified return

            # Parse availability, structured data, and analysis text
            availability_status = "unknown"
            structured_data = {}
            analysis_text = "Analysis could not be parsed."

            lines = raw_analysis.strip().split('\\n')
            line_index = 0

            # Parse AVAILABILITY
            if line_index < len(lines) and lines[line_index].startswith("AVAILABILITY:"):
                status_part = lines[line_index].split(
                    ":", 1)[1].strip().lower()
                if status_part in ["none", "minimal", "substantial"]:
                    availability_status = status_part
                else:
                    logging.warning(
                        f"Unrecognized bodyweight availability: {status_part}")
                    availability_status = "unknown_format"
                line_index += 1
            else:
                logging.warning(
                    "Could not parse bodyweight AVAILABILITY from Gemini response.")
                analysis_text = raw_analysis.strip()
                return availability_status, structured_data, analysis_text

            # Parse structured data if availability is not 'none'
            if availability_status in ["minimal", "substantial"]:
                if line_index < len(lines) and lines[line_index].strip() == "```data":
                    line_index += 1
                    data_lines = []
                    while line_index < len(lines) and lines[line_index].strip() != "```":
                        data_lines.append(lines[line_index])
                        line_index += 1
                    if line_index < len(lines) and lines[line_index].strip() == "```":
                        line_index += 1  # Consume closing ```

                    for data_line in data_lines:
                        if ":" in data_line:
                            key, value = data_line.split(":", 1)
                            structured_data[key.strip()] = value.strip().replace(
                                " kg", "")  # Remove units for consistency
                    logging.info(
                        f"Extracted structured bodyweight data: {structured_data}")
                else:
                    logging.warning(
                        "Expected ```data block not found for bodyweight.")

            # Get the rest as analysis text
            if line_index < len(lines):
                analysis_text = "\\n".join(lines[line_index:]).strip()
            elif availability_status in ["none", "minimal"] and not analysis_text:
                analysis_text = f"Bodyweight data for the recent week appears {availability_status}. Consistent tracking is key for monitoring progress."
            elif availability_status == "substantial" and not analysis_text:
                analysis_text = "Substantial bodyweight data detected for the recent week, but analysis text is missing."
                logging.warning(analysis_text)
            elif not analysis_text:  # Default if still empty
                analysis_text = "Could not parse bodyweight analysis text."
                logging.warning(analysis_text)

            return availability_status, structured_data, analysis_text

        except TimeoutException:
            # Added logging
            logging.warning(
                "TimeoutException: Bodyweight graph element not found.")
            # Modified return
            return "no_data_found", {}, "No bodyweight data available for the current week."

        except Exception as e:
            logging.exception(
                f"Error analyzing graph with gemini-2.0-flash: {e}")
            return "error", {}, f"Error analyzing bodyweight graph: {e}"  # Modified return

    def analyze_nutrition_graph(self):
        """Analyzes nutrition graphs using Gemini, assessing availability and comparing recent week to overall trend for each nutrient group."""
        # GraphQL fallback debug snippet
        from datetime import datetime, timedelta
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now().date() - timedelta(days=7)).isoformat()
        graphql_query = '''
        query NutritionRecords($start: String!, $end: String!) {
            nutritionRecords(start: $start, end: $end) {
                date
                calories
                protein
                fats
                carbs
            }
        }
        '''
        data = self.fetch_graphql(
            graphql_query, {"start": start_date, "end": end_date})
        print(f"DEBUG: Nutrition GraphQL data: {data}")
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping nutrition graph analysis.")
            # Return default structure indicating analysis skipped
            return {
                "calories_protein": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Analysis skipped (no API key)."},
                "fats_carbs": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Analysis skipped (no API key)."}
            }

        results = {  # Initialize results dictionary
            "calories_protein": {"availability": "error", "structured_data": {}, "analysis_text": "Analysis failed."},
            "fats_carbs": {"availability": "error", "structured_data": {}, "analysis_text": "Analysis failed."}
        }

        try:
            logging.info("Navigating to nutrition graphs...")
            if not self.navigate_to_nutrition_graphs():
                logging.error("Failed to navigate to nutrition graphs.")
                results["calories_protein"]["availability"] = "navigation_failed"
                results["calories_protein"]["analysis_text"] = "Navigation failed."
                results["fats_carbs"]["availability"] = "navigation_failed"
                results["fats_carbs"]["analysis_text"] = "Navigation failed."
                return results

            # Use default graph view (likely 1 month)
            # self._click_3m_button_if_exists() # Removed 3M click
            logging.info("Analyzing nutrition graphs (default view)...")
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)

            # --- Screenshot 1: Calories & Protein ---
            screenshot1_path = "nutrition_graph_cal_prot.png"
            self.driver.save_screenshot(screenshot1_path)
            logging.info(
                f"Calories/Protein screenshot saved to {screenshot1_path}")
            base64_image1 = TrainerizeAutomation.encode_image(screenshot1_path)

            # --- Scroll and Screenshot 2: Fats & Carbs ---
            try:
                # Try scrolling to make carbs/fats visible
                self.driver.execute_script("window.scrollBy(0, 400);")
                time.sleep(1)
            except Exception as scroll_e:
                logging.warning(
                    f"Could not scroll for fats/carbs screenshot: {scroll_e}")

            screenshot2_path = "nutrition_graph_fat_carb.png"
            self.driver.save_screenshot(screenshot2_path)
            logging.info(f"Fats/Carbs screenshot saved to {screenshot2_path}")
            base64_image2 = TrainerizeAutomation.encode_image(screenshot2_path)

            # --- Process Calories/Protein (Image 1) ---
            if base64_image1:
                prompt1_parts = [{"parts": [{"text": """
Analyze this nutrition graph screenshot focusing ONLY on CALORIES and PROTEIN.

1. Assess Data Availability for Calories/Protein: Determine if the data is none, minimal, or substantial.
2. Generate Analysis Based on Availability:
    - If 'none' or 'minimal': Respond ONLY with a brief, encouraging message about tracking calories/protein consistently.
    - If 'substantial':
        a. Extract Structured Data for Calories/Protein (use "not visible" if undetectable).
        b. Provide Detailed Analysis: Focus *only* on the recent week (last ~7 days visible on the graph) for Calories and Protein. Discuss consistency and average intake for this recent week.

OUTPUT FORMAT: Start IMMEDIATELY with availability:
AVAILABILITY: [none/minimal/substantial]

If 'substantial', add the structured data block IMMEDIATELY after:
                        ```data
CALORIES_DAILY: [number or "not visible"]
PROTEIN_DAILY: [number or "not visible"]g
CALORIES_GOAL: [number or "not visible"]
PROTEIN_GOAL: [number or "not visible"]g
```
Then, on a NEW LINE, provide ONLY the generated analysis text.
"""}, {"inline_data": {"mime_type": "image/png", "data": base64_image1}}]}]

                print("\n--- Gemini Prompt (Calories/Protein Analysis) ---")
                # print(prompt1_parts[0]['parts'][0]['text']) # Keep prompt log concise
                response1 = self.model.generate_content(
                    contents=prompt1_parts, generation_config=genai.GenerationConfig(max_output_tokens=2500))
                results["calories_protein"] = self._parse_nutrient_analysis(
                    response1, "Calories/Protein")
            else:
                results["calories_protein"]["availability"] = "image_error"
                results["calories_protein"]["analysis_text"] = "Could not encode calories/protein image."

            # --- Process Fats/Carbs (Image 2) ---
            if base64_image2:
                prompt2_parts = [{"parts": [{"text": """
Analyze this nutrition graph screenshot focusing ONLY on FATS and CARBS.

1. Assess Data Availability for Fats/Carbs: Determine if the data is none, minimal, or substantial.
2. Generate Analysis Based on Availability:
    - If 'none' or 'minimal': Respond ONLY with a brief, encouraging message about tracking fats/carbs consistently.
    - If 'substantial':
        a. Extract Structured Data for Fats/Carbs (use "not visible" if undetectable).
        b. Provide Detailed Analysis: Focus *only* on the recent week (last ~7 days visible on the graph) for Fats and Carbs. Discuss consistency and average intake for this recent week.

OUTPUT FORMAT: Start IMMEDIATELY with availability:
AVAILABILITY: [none/minimal/substantial]

If 'substantial', add the structured data block IMMEDIATELY after:
                        ```data
FATS_DAILY: [number or "not visible"]g
CARBS_DAILY: [number or "not visible"]g
FATS_GOAL: [number or "not visible"]g
CARBS_GOAL: [number or "not visible"]g
```
Then, on a NEW LINE, provide ONLY the generated analysis text.
"""}, {"inline_data": {"mime_type": "image/png", "data": base64_image2}}]}]

                print("\n--- Gemini Prompt (Fats/Carbs Analysis) ---")
                # print(prompt2_parts[0]['parts'][0]['text']) # Keep prompt log concise
                response2 = self.model.generate_content(
                    contents=prompt2_parts, generation_config=genai.GenerationConfig(max_output_tokens=2500))
                results["fats_carbs"] = self._parse_nutrient_analysis(
                    response2, "Fats/Carbs")
            else:
                results["fats_carbs"]["availability"] = "image_error"
                results["fats_carbs"]["analysis_text"] = "Could not encode fats/carbs image."

            return results

        except TimeoutException:
            logging.warning(
                "TimeoutException: Nutrition graph element not found.")
            results["calories_protein"]["availability"] = "no_data_found"
            results["calories_protein"]["analysis_text"] = "Nutrition graph not found."
            results["fats_carbs"]["availability"] = "no_data_found"
            results["fats_carbs"]["analysis_text"] = "Nutrition graph not found."
            return results
        except Exception as e:
            logging.exception(f"Error analyzing nutrition graphs: {e}")
            # Keep default error status in results dictionary
            return results

    def _parse_nutrient_analysis(self, response, nutrient_group_name):
        """Helper function to parse Gemini response for a nutrient group."""
        parsed_result = {"availability": "error",
                         "structured_data": {}, "analysis_text": "Parsing failed."}
        raw_text = ""

        try:
            # Extract text from response
            try:
                raw_text = response.text
                print(
                    f"\n--- Gemini Response ({nutrient_group_name} Analysis) ---")
                print(raw_text)
            except Exception as e_text:
                logging.warning(
                    f"Error accessing response.text for {nutrient_group_name}: {e_text}")
                if hasattr(response, 'candidates') and response.candidates:
                    raw_text = response.candidates[0].content.parts[0].text
                    print(
                        f"\n--- Gemini Response ({nutrient_group_name} Analysis - Fallback) ---")
                    print(raw_text)
                else:
                    parsed_result["availability"] = "processing_error"
                    parsed_result["analysis_text"] = f"Unable to process {nutrient_group_name} response."
                    return parsed_result

            # Parse the raw text
            lines = raw_text.strip().split('\n')
            line_index = 0
            availability_status = "unknown"
            structured_data = {}
            analysis_text = ""

            # Parse AVAILABILITY
            if line_index < len(lines) and lines[line_index].startswith("AVAILABILITY:"):
                status_part = lines[line_index].split(
                    ":", 1)[1].strip().lower()
                if status_part in ["none", "minimal", "substantial"]:
                    availability_status = status_part
                else:
                    logging.warning(
                        f"Unrecognized {nutrient_group_name} availability: {status_part}")
                    availability_status = "unknown_format"
                line_index += 1
            else:
                logging.warning(
                    f"Could not parse {nutrient_group_name} AVAILABILITY.")
                analysis_text = raw_text.strip()  # Use whole text if parsing fails here
                parsed_result["availability"] = availability_status
                parsed_result["analysis_text"] = analysis_text
                return parsed_result

            # Parse structured data if substantial
            if availability_status == "substantial":
                if line_index < len(lines) and lines[line_index].strip() == "```data":
                    line_index += 1
                    data_lines = []
                    while line_index < len(lines) and lines[line_index].strip() != "```":
                        data_lines.append(lines[line_index])
                        line_index += 1
                    if line_index < len(lines) and lines[line_index].strip() == "```":
                        line_index += 1  # Consume closing ```

                    for data_line in data_lines:
                        if ":" in data_line:
                            key, value = data_line.split(":", 1)
                            structured_data[key.strip()] = value.strip()
                    logging.info(
                        f"Extracted structured {nutrient_group_name} data: {structured_data}")
                else:
                    logging.warning(
                        f"Expected ```data block not found for substantial {nutrient_group_name} data.")

            # Get the rest as analysis text
            if line_index < len(lines):
                analysis_text = "\n".join(lines[line_index:]).strip()
            elif availability_status in ["none", "minimal"] and not structured_data:
                # Handle single-line message case for none/minimal
                if len(lines) == 1 and len(lines[0].split(":", 1)) > 1:
                    potential_message = lines[0].split(":", 1)[1].strip()
                    if len(potential_message) > 10:
                        analysis_text = potential_message
                else:
                    analysis_text = f"{nutrient_group_name} data tracking appears {availability_status}. Consistent logging is key."
            elif availability_status == "substantial" and not analysis_text:
                analysis_text = f"Substantial {nutrient_group_name} data detected, but analysis text is missing."
                logging.warning(analysis_text)
            elif not analysis_text:
                analysis_text = f"Could not parse {nutrient_group_name} analysis text."
                logging.warning(analysis_text)

            parsed_result["availability"] = availability_status
            parsed_result["structured_data"] = structured_data
            parsed_result["analysis_text"] = analysis_text
            return parsed_result

        except Exception as e:
            logging.exception(
                f"Error parsing {nutrient_group_name} analysis: {e}")
            # Keep default error status
            return parsed_result

    def analyze_sleep_graph(self):
        """Analyzes the sleep graph using the configured Gemini model, assessing data availability and extracting average hours for recent week if substantial."""
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping sleep graph analysis.")
            return "not_analyzed", "Gemini API key not provided, skipping analysis.", None

        try:
            logging.info("Navigating to sleep graph...")
            if not self.navigate_to_sleep_graphs():
                logging.error("Failed to navigate to sleep graphs.")
                return "navigation_failed", "Failed to navigate to sleep graphs.", None

            logging.info("Analyzing sleep graph with Gemini...")
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))

            # self._click_3m_button_if_exists()
            time.sleep(2)
            screenshot_path = "sleep_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "image_error", "Error: Could not encode sleep graph image.", None

            # Updated prompt requesting average sleep for substantial data
            prompt_parts = [{
                "parts": [
                    {"text": f"""
                    Analyze this sleep graph screenshot.

                    1. Assess Data Availability: First, determine if the graph shows:
                        - none: No data points visible.
                        - minimal: Only a few scattered data points, large gaps, clearly inconsistent tracking.
                        - substantial: Reasonably consistent tracking, especially in the most recent week (enough data for meaningful analysis).

                    2. Generate Analysis Based on Availability:
                        - If 'none' or 'minimal': Respond ONLY with a brief, encouraging message focused on tracking consistency. Example: "There isn't much sleep data here yet. Let's try to track sleep consistently each night - aiming for 7-9 hours helps recovery and metabolism!"
                        - If 'substantial':
                            a. Extract Average Sleep: Determine the approximate average sleep hours for the most recent week (last ~7 days shown). Examples: "8 hours", "7-8 hours", "7.5 hours". If not clearly discernible, use "not visible".
                            b. Provide Detailed Analysis: Focus *only* on the most recent week (last ~7 days visible on the graph). Discuss consistency and duration trends observed *within this recent week only*.
                            c. Style Guide: Mimic this style - "Alright, looking at your most recent week of sleep, it seems [more/less consistent] ... The key takeaway is [recommendation]..."

                    IMPORTANT OUTPUT FORMAT: Start your entire response *immediately* with the availability assessment and average sleep (if applicable) using this EXACT format:

                    If availability is 'none' or 'minimal':
                    AVAILABILITY: [none/minimal]

                    If availability is 'substantial':
                    AVAILABILITY: substantial
                    AVERAGE_RECENT_WEEK_SLEEP: [value like X hours / X-Y hours / X.Y hours / not visible]

                    Then, on a new line AFTER the availability/average lines, provide ONLY the generated analysis text based on the data availability. Do not add any other introductory phrases.
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

            raw_analysis = ""
            try:
                raw_analysis = response.text
                print("\n--- Gemini Response (Sleep Analysis) ---")
                print(raw_analysis)
            except Exception as e:
                logging.warning(
                    f"Error accessing response.text for sleep analysis: {e}")
                try:
                    if hasattr(response, 'candidates') and response.candidates:
                        raw_analysis = response.candidates[0].content.parts[0].text
                        print("\n--- Gemini Response (Sleep Analysis - Fallback) ---")
                        print(raw_analysis)
                    else:
                        return "processing_error", "Unable to process sleep analysis response from Gemini.", None
                except Exception as fallback_error:
                    logging.exception(
                        f"Error in fallback text extraction for sleep analysis: {fallback_error}")
                    return "processing_error", "Unable to process sleep analysis response from Gemini.", None

            # Parse availability, average sleep, and analysis text
            availability_status = "unknown"
            analysis_text = "Analysis could not be parsed."
            average_sleep_hours = None  # Initialize as None

            lines = raw_analysis.strip().split('\n')
            line_index = 0

            # Parse AVAILABILITY
            if line_index < len(lines) and lines[line_index].startswith("AVAILABILITY:"):
                status_part = lines[line_index].split(
                    ":", 1)[1].strip().lower()
                if status_part in ["none", "minimal", "substantial"]:
                    availability_status = status_part
                else:
                    logging.warning(
                        f"Unrecognized availability status: {status_part}")
                    availability_status = "unknown_format"
                line_index += 1
            else:
                logging.warning(
                    "Could not parse AVAILABILITY status from Gemini response.")
                analysis_text = raw_analysis.strip()  # Use the whole response if parsing fails
                return availability_status, analysis_text, average_sleep_hours  # Return early

            # Parse AVERAGE_RECENT_WEEK_SLEEP if substantial
            if availability_status == "substantial":
                if line_index < len(lines) and lines[line_index].startswith("AVERAGE_RECENT_WEEK_SLEEP:"):
                    avg_sleep_part = lines[line_index].split(":", 1)[1].strip()
                    if avg_sleep_part.lower() != "not visible":
                        # Store the extracted string (e.g., "7-8 hours")
                        average_sleep_hours = avg_sleep_part
                        logging.info(
                            f"Extracted average recent week sleep: {average_sleep_hours}")
                    else:
                        logging.info(
                            "Average recent week sleep marked as 'not visible'.")
                    line_index += 1
                else:
                    logging.warning(
                        "Expected AVERAGE_RECENT_WEEK_SLEEP line not found for substantial data.")

            # Get the rest as analysis text
            if line_index < len(lines):
                analysis_text = "\n".join(lines[line_index:]).strip()
            elif availability_status in ["none", "minimal"]:
                # Handle case where message might be on the AVAILABILITY line itself if only one line returned
                # Check if there was content after ':'
                if len(lines) == 1 and len(lines[0].split(":", 1)) > 1:
                    potential_message = lines[0].split(":", 1)[1].strip()
                    # Heuristic: assume it's the message if longer than status
                    if len(potential_message) > 10:
                        analysis_text = potential_message
                        logging.warning(
                            "Assuming single-line response for none/minimal sleep data is the message.")
                    else:
                        analysis_text = f"Sleep data appears {availability_status}. Consistent tracking is key."
                else:  # Default message if truly nothing else
                    analysis_text = f"Sleep data appears {availability_status}. Consistent tracking is key."
            else:
                # Substantial data but no analysis text found after structured lines
                analysis_text = "Substantial sleep data detected, but analysis text is missing."
                logging.warning(analysis_text)

            logging.info(
                f"Sleep analysis complete. Availability: {availability_status}, Avg Recent Sleep: {average_sleep_hours}")
            return availability_status, analysis_text, average_sleep_hours

        except TimeoutException:
            logging.warning("TimeoutException: Sleep graph element not found.")
            return "no_data_found", "No sleep data found on the page.", None
        except Exception as e:
            logging.exception(f"Error analyzing sleep graph: {e}")
            return "error", f"An unexpected error occurred during sleep analysis: {e}", None

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
                        Analyze this steps graph from a personal training app, focusing specifically on the 10,000 steps per day goal *for the most recent week (last ~7 days visible on the graph)*.

                        Your analysis should include *for this recent week only*:
                        1. Overall assessment of whether the person is consistently meeting the 10k steps goal
                        2. Identify patterns: Are they consistently above 10k, consistently below, or inconsistent?
                        3. Identify highest step days(significantly above 10k) and lowest step days(significantly below 10k)
                        4. Assess the trend *within the most recent week (last ~7 days visible on the graph)*: Is their step count improving, declining, or staying consistent *during this recent period*?

                        IMPORTANT: Begin your response with a structured data section using this exact format:
                        ```data
                        MEETS_10K_GOAL: [consistently/sometimes/rarely/never]
                        AVERAGE_STEPS: [number like Xk or X,XXX OR the literal string "Inconsistent Tracking" OR "not visible"]
                        HIGHEST_STEPS: [number like Xk or X,XXX or "not visible"]
                        LOWEST_STEPS: [number like Xk or X,XXX or "not visible"]
                        TREND: [improving/declining/consistent/inconsistent]
                        ```
                        **Crucially, for AVERAGE_STEPS:** 
                        1. Assess consistency for the most recent week (last ~7 days). 
                        2. If tracking looks very inconsistent (e.g., many missing days, huge gaps), set AVERAGE_STEPS to the exact string "Inconsistent Tracking".
                        3. If tracking looks reasonably consistent, try to read an average label. If no label is visible, **estimate** the average daily steps by visually assessing the data points/bars height relative to the Y-axis. Provide your best estimate (e.g., "~8.5k", "around 9,000").
                        4. Use "not visible" ONLY if there is absolutely no data in the recent week.

                        Then, provide actionable feedback in an encouraging, motivational tone. Examples:

                        - If they're consistently hitting 10k+: "Really impressive consistency with your steps! Maintaining 10k+ steps daily is powering your results and keeping your metabolism fired up!"

                        - If they're inconsistent: "You're hitting some amazing step days up to[X]k! If we can bring those lower days up to 10k consistently, your metabolism will stay elevated every day, accelerating your results."

                        - If they're consistently below 10k: "Let's focus on gradually increasing your daily steps to reach that 10k goal. Even adding 1, 000 steps per day can make a big difference in your metabolism and progress!"

                        Keep it concise, action-oriented, and motivating!
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
                    max_output_tokens=5000)
            )
            analysis = response.text

            print("\n--- Gemini Response (Steps Analysis) ---")
            print(analysis)

            return analysis
        except TimeoutException:
            return "No steps data available."
        except Exception as e:
            logging.exception(f"Error analyzing steps graph: {e}")
            return f"Error: {e}"

    def analyze_progress_photos(self):
        """Analyzes progress photos using gemini-2.0-flash if they exist."""
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping progress photos analysis.")
            return "Gemini API key not provided, skipping analysis."
        try:
            logging.info("Analyzing progress photos with gemini-2.0-flash...")
            # Wait for some element on the progress photos page to be present.

            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "img.photo-comparison-image")))

            time.sleep(2)  # Give images time to load
            screenshot_path = "progress_photos.png"
            # take screenshot of whole screen
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
                        Okay lets check in on your progress photos!

                        Analyze these progress photos from a personal training app.

                        Check if they are up-to-date for this week.

                        If they ARE up-to-date:  Give a compliment! (e.g., "Love to see you get your progress photos up! Looking strong!", "Awesome to see the progress pics this week, you're getting fitter day by day!")

                        If they are NOT up-to-date: Gently encourage them to upload some if they are comfortable. (e.g., "No progress piccies this week! Try get them up if you feel comfortable with it",  "Haven't seen progress photos this week, no pressure but they can be a great way to track progress visually!")

                        Keep it brief and friendly!
                        """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Progress Photos Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])

            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5000)
            )

            analysis = response.text

            print("\n--- Gemini Response (Progress Photos Analysis) ---")
            print(analysis)

            print(analysis)
            return analysis

        except TimeoutException:
            return "No progress photos available."
        except Exception as e:
            logging.exception(f"Error analyzing progress photos: {e}")
            return f"Error: {e}"

    def click_review_by_workout(self):
        """Clicks the 'Review By Workout' link on the Progress page."""
        try:
            logging.info("Attempting to click the 'Review By Workout' link...")

            # Locate the "Review By Workout" link using XPath.  Target _self is also added.
            review_link_locator = (
                By.XPATH, "//a[@class='tz-sp section-link text-overflow-none' and contains(@href, '/progress/workout') and @target='_self']")
            review_link = self.wait.until(
                EC.element_to_be_clickable(review_link_locator))
            review_link.click()
            logging.info("Successfully clicked the 'Review By Workout' link.")
            return "Successfully clicked 'Review By Workout' link"

        except TimeoutException:
            logging.error(
                "TimeoutException: 'Review By Workout' link not found or not clickable within timeout.")
            return "Failed to click 'Review By Workout' link (Timeout)"
        except NoSuchElementException:
            logging.error(
                "NoSuchElementException: 'Review By Workout' link element not found on the page.")
            return "Failed to click 'Review By Workout' link (Not Found)"
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return "Failed to click 'Review By Workout' link (Unknown Error)"

    def process_workouts(self):
        """Gets workout data, processes workout details with name-only uniqueness."""
        try:
            workout_data_list = []
            processed_workout_keys = set()  # For tracking unique workout NAME+DATE combinations

            # Initial load and count of workouts
            self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.baseGridRow")))
            time.sleep(1)

            # Process one workout at a time using a safer method
            i = 0
            while True:
                # Check if we have any rows left
                rows = self.driver.find_elements(
                    By.CSS_SELECTOR, "div.baseGridRow")
                if i >= len(rows):
                    logging.info(
                        f"Processed all {len(processed_workout_keys)} unique workouts from {i} rows")
                    break

                try:
                    current_row = rows[i]

                    # Get workout name and date
                    date_element = current_row.find_element(
                        By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                    date_str = date_element.text.strip()

                    workout_element = current_row.find_element(
                        By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                    workout_name = workout_element.text.strip()

                    # Create a unique key combining workout name and date
                    workout_key = f"{workout_name}_{date_str}"

                    logging.info(
                        f"Found workout {i+1}/{len(rows)}: '{workout_name}' on date: '{date_str}'")

                    # Skip if this exact workout (name+date) has already been processed
                    if workout_key in processed_workout_keys:
                        logging.info(
                            f"Skipping duplicate workout: {workout_name} on {date_str}")
                        i += 1
                        continue

                    # Process this workout
                    processed_workout_keys.add(workout_key)
                    logging.info(
                        f"Processing unique workout: {workout_name} on {date_str}")

                    # Click the workout name - we need to use JavaScript because the element might not be visible
                    self.driver.execute_script(
                        "arguments[0].click();", workout_element)
                    time.sleep(2)

                    # Analyze workout details
                    formatted_workout_data_list = self.analyze_workout_details_stripped(
                        workout_name, date_str)

                    if formatted_workout_data_list:
                        for workout_dict in formatted_workout_data_list:
                            workout_data_list.append(workout_dict)
                            logging.info(
                                f"Added workout data for: {workout_dict['workout_type']} on {workout_dict['date']}")

                    # Use the BACK button to return to workout list
                    back_button_locator = (
                        By.CSS_SELECTOR, "button[data-testid='clientProgress-workouts-detailTable-backButton']")
                    try:
                        back_button = self.wait.until(
                            EC.element_to_be_clickable(back_button_locator))
                        back_button.click()
                        time.sleep(2)  # Wait for page to load
                    except Exception as back_error:
                        logging.warning(
                            f"Could not find BACK button: {back_error}")
                        self.driver.back()
                        time.sleep(2)

                    # Wait for the list page to load again
                    self.wait.until(EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.baseGridRow")))
                    logging.info("Back on workout list page")

                    # Re-fetch the rows since the DOM has been refreshed
                    i += 1

                except Exception as e:
                    logging.warning(
                        f"Error processing workout at index {i}: {e}")
                    i += 1  # Move to next workout on error

            logging.info(
                f"Final workout_data_list contains data for {len(processed_workout_keys)} unique workouts")
            return workout_data_list

        except Exception as e:
            logging.exception(f"Error during workout processing: {e}")
            return []

    def analyze_workout_details_stripped(self, workout_name, date_str):
        # This method now directly calls the base implementation.
        return analyze_workout_details_stripped_base(self, workout_name, date_str)

    def generate_personalized_message(self, client_name, workouts_this_week, most_improved_exercise_data):
        logging.info(
            f"Generating personalized message for {client_name} based on workouts: {workouts_this_week} and improvement: {most_improved_exercise_data}")

        first_name = client_name.split()[0]  # Extract first name
        message = f"Hey {first_name}! "  # Use first name

        try:
            improvement_type = most_improved_exercise_data.get(
                "improvement_type", "none")
            exercise_name = most_improved_exercise_data.get(
                "name", "your lifts")
            current_performance = most_improved_exercise_data.get(
                "current_performance_desc", "")
            improvement_highlight = most_improved_exercise_data.get(
                "improvement_highlight", "")

            if improvement_type in ["weight", "reps"] and exercise_name != "N/A":
                # Focus on specific lift improvement
                # Checks if highlight is specific enough
                if "kg" in improvement_highlight.lower() or "rep" in improvement_highlight.lower():
                    message += f"Awesome to see you pushing hard on {exercise_name}, {improvement_highlight.lower()} Keep it up!"
                elif current_performance:
                    message += f"Great job with {exercise_name}, hitting {current_performance}! Solid progress."
                else:
                    message += f"Excellent work on {exercise_name} this week! Keep building that strength."
            elif workouts_this_week > 0:
                if workouts_this_week >= 3:
                    message += f"Fantastic consistency hitting {workouts_this_week} gym sessions this week! Very proud of your effort!"
                elif workouts_this_week > 0:
                    message += f"Great to see you in the gym {workouts_this_week} time(s) this week! Keep that momentum."
                else:  # Fallback if workouts_this_week is 0 for some reason but this branch is hit.
                    message += "Keep up the great effort with your training! Every session counts."
            else:
                message += "Keep pushing towards your fitness goals this week! You've got this."

            # Ensure message is within word limits (approx. 10-25 words)
            words = message.split()
            if len(words) > 25:
                # Attempt a simple trim if too long, focusing on core message types
                if improvement_type in ["weight", "reps"] and exercise_name != "N/A":
                    message = f"Hey {first_name}! Awesome job on {exercise_name}, {improvement_highlight.lower()} Keep it up!"
                    if len(message.split()) > 25 and current_performance:
                        message = f"Hey {first_name}! Great work hitting {current_performance} on {exercise_name}! Solid progress."
                elif workouts_this_week > 0:
                    message = f"Hey {first_name}, great work getting to the gym {workouts_this_week} time(s) this week! Proud of you!"
                else:
                    # Generic trim if specific trims are still too long or don't apply
                    message = ' '.join(words[:22]) + "... Keep it up!"

            if len(words) < 10:  # Pad if too short
                if workouts_this_week > 0:
                    message += " Really proud of your commitment!"
                else:
                    message += " Looking forward to seeing your progress!"

            # Final length check and adjustment if necessary
            final_words = message.split()
            if len(final_words) > 25:
                message = ' '.join(final_words[:25])
            if len(final_words) < 10:
                message = f"Hey {first_name}, keep up the great work and consistency this week!"

        except Exception as e:
            logging.exception(
                f"Error generating personalized message for {client_name}: {e}")
            message = f"Hey {first_name}, keep up the fantastic effort this week! You're doing great."

        logging.info(f"Generated message for {client_name}: {message}")
        return message

    def navigate_back_to_clients_list(self):
        """Navigates back to the main Clients list tab and closes the dialog."""
        try:
            logging.info(
                "Navigating back to the Clients list tab and closing dialog...")
            try:
                self.driver.close()  # Close the current client's profile tab
                logging.info("Closed client profile tab.")
            except (WebDriverException, InvalidSessionIdException) as e:
                logging.warning(f"Error closing client tab: {e}")

            original_window_handle = self.driver.window_handles[0]
            self.driver.switch_to.window(original_window_handle)
            logging.info("Switched back to the main Clients list tab.")
            time.sleep(2)  # small wait for page to settle

            logging.info(
                "Attempting to close client profile dialog if present...")
            close_button_locator = (
                By.CSS_SELECTOR, "span[data-testid='close-button'].closeButton.clickable")
            try:
                close_button = self.wait.until(
                    EC.element_to_be_clickable(close_button_locator))
                close_button.click()
                logging.info("Client profile dialog closed successfully.")
            except TimeoutException:
                logging.warning(
                    "Client profile dialog close button not found or not clickable (may not be present). Continuing anyway.")
            except Exception as close_exception:
                logging.error(
                    f"Error while trying to close client profile dialog: {close_exception}")
            return True
        except Exception as e:
            logging.exception(f"Error navigating back to Clients list: {e}")
            return False

    def cleanup(self):
        """Cleans up resources (removes temp dir, and now closes driver correctly)."""
        try:
            logging.info("Cleaning up...")
            if hasattr(self, 'driver'):  # Check if driver exists before trying to close
                logging.info("Closing webdriver...")
                try:
                    self.driver.close()  # Close the current window (if any)
                except (WebDriverException, InvalidSessionIdException) as e:
                    logging.warning(
                        f"Error closing current window during cleanup: {e}")
                try:
                    self.driver.quit()   # Quit the browser entirely
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

    @staticmethod
    def encode_image(image_path):
        """Encodes an image file to Base64 format."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            logging.error(f"Error: Image file not found at path: {image_path}")
            return None
        except Exception as e:
            logging.exception(f"Error encoding image: {e}")
            return None

    def is_element_stale(self, element):
        """Helper function to check if an element is stale."""
        try:
            element.is_enabled()  # Try to interact with the element
            return False         # If no exception, element is not stale
        except StaleElementReferenceException:
            return True          # Exception means element is stale

    def calculate_workout_stats_for_date_range(self, workout_data_list, start_date, end_date, target_exercises=None):
        """Calculates workout stats within a specific date range with proper unique workout counting."""
        if not workout_data_list:
            return 0, [], 0, 0, 0, [], {}

        total_weight_lifted = 0
        total_reps = 0
        total_sets = 0
        workout_data_in_range = []
        exercise_workload = {}

        # Track unique workouts by date+name
        unique_workout_keys = set()
        unique_workouts = []

        for workout in workout_data_list:
            date_str = workout['date']
            workout_date_obj = None

            try:
                # First attempt to parse as YYYY-MM-DD
                workout_date_obj = datetime.strptime(
                    date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    # Then try DD MMM YYYY format
                    workout_date_obj = datetime.strptime(
                        date_str, '%d %b %Y').date()
                except ValueError:
                    # Skip any unparseable dates
                    logging.warning(f"Could not parse date: {date_str}")
                    continue

            # Check if this workout falls within our target date range
            if start_date <= workout_date_obj <= end_date:
                workout_name = workout['workout_type']

                # Create a unique key based on date AND workout name
                unique_key = f"{workout_date_obj.strftime('%Y-%m-%d')}_{workout_name}"

                # Only process each unique workout (by date and name) once
                if unique_key not in unique_workout_keys:
                    unique_workout_keys.add(unique_key)
                    unique_workouts.append(workout)
                    workout_data_in_range.append(workout)

                    # Process exercises and sets
                    for exercise in workout['exercises']:
                        exercise_name = exercise['name'].strip()
                        exercise_total_weight = 0
                        for set_data in exercise['sets']:
                            weight = set_data['weight']
                            reps = set_data['reps']
                            total_weight_lifted += weight * reps
                            total_reps += reps
                            total_sets += 1
                            exercise_total_weight += weight * reps

                        if target_exercises and exercise_name in target_exercises:
                            exercise_workload.setdefault(exercise_name, 0)
                            exercise_workload[exercise_name] += exercise_total_weight

        # Count unique workouts and get their names
        workout_count = len(unique_workout_keys)
        workout_names_in_range = [workout['workout_type']
                                  for workout in unique_workouts]

        # Print a detailed summary of unique workouts by date (helps with debugging)
        workouts_by_date = {}
        for unique_key in unique_workout_keys:
            # Extract date part from unique key
            date_part = unique_key.split('_')[0]
            workout_name = unique_key.split('_', 1)[1]  # Extract workout name
            if date_part not in workouts_by_date:
                workouts_by_date[date_part] = []
            workouts_by_date[date_part].append(workout_name)

        logging.info(
            f"UNIQUE Workouts in date range {start_date} to {end_date}:")
        for date, workouts in sorted(workouts_by_date.items()):
            logging.info(f"  {date}: {', '.join(workouts)}")
        logging.info(f"Total UNIQUE workout count in range: {workout_count}")

        return workout_count, workout_names_in_range, total_weight_lifted, total_reps, total_sets, workout_data_in_range, exercise_workload


def analyze_workout_details_stripped_base(self, workout_name, date_str):
    """Base analyze_workout_details_stripped for both TrainerizeAutomation and TrainerizeCSVParsing."""
    try:
        logging.info(
            "Starting analyze_workout_details_stripped (revised date-set mapping)...")
        workout_list_for_page = []  # Initialize list to store workout data for each date
        dates = []

        # --- 1. Extract Dates from Header Row ---
        date_header_cells = self.driver.find_elements(By.XPATH,
                                                      "//thead[@class='ant-table-thead']/tr[1]/th[contains(@class, 'bgGray10') and contains(@class, 'colorPrimaryBlue') and contains(@class, 'clickable')]")
        dates = [cell.text.strip() for cell in date_header_cells]
        logging.info(f"Extracted Dates: {dates}")

        # --- 2. Iterate through Dates and then Table Body Rows ---
        # Iterate through dates
        for current_date_index, current_date_str in enumerate(dates):
            # Create workout data for EACH date
            workout_data = {'date': current_date_str,
                            'workout_type': workout_name, 'exercises': []}
            current_exercise_data = None

            rows = self.driver.find_elements(By.XPATH,
                                             "//tbody[@class='ant-table-tbody']/tr[@class='ant-table-row ant-table-row-level-0']")
            logging.info(
                # DEBUG - keep for general info
                f"Processing date: {current_date_str}. Number of table rows found: {len(rows)}")

            for row_index, row in enumerate(rows):
                cells = row.find_elements(By.XPATH, "./td")
                if not cells or len(cells) < 2:
                    continue

                # --- Check for Exercise Name Cell ---
                exercise_name_cells = row.find_elements(By.XPATH,
                                                        "./td[@class='ant-table-fixed-columns-in-body clickable ant-table-row-cell-break-word' and @rowspan and contains(@style, 'color: rgb(34, 158, 212)')]")
                if exercise_name_cells:
                    exercise_name_cell = exercise_name_cells[0]
                    exercise_name = exercise_name_cell.text.strip()
                    current_exercise_name = exercise_name
                    # Initialize exercise data
                    current_exercise_data = {'name': exercise_name, 'sets': []}
                    # Add exercise to workout data
                    workout_data['exercises'].append(current_exercise_data)
                    logging.info(
                        # DEBUG - keep for general info
                        f"  Date: {current_date_str}, Row {row_index}: Exercise Detected - {exercise_name}")

                # --- Check for Set Data Row (within an exercise) ---
                set_number_cells = row.find_elements(By.XPATH,
                                                     "./td[@class='ant-table-fixed-columns-in-body ant-table-row-cell-break-word' and contains(@style, 'text-align: center; font-size: 12px;') and contains(text(), 'SET')]")
                # Check if current_exercise_data is initialized
                if set_number_cells and current_exercise_data is not None:
                    set_number_cell = set_number_cells[0]
                    set_number_text = set_number_cell.text.strip()
                    logging.info(
                        # DEBUG - keep for general info
                        f"  Date: {current_date_str}, Row {row_index}: Set Detected - {set_number_text} for Exercise - {current_exercise_name}")

                    # --- Extract Set Data for the CURRENT Date Column ---
                    # Data cells start from 3rd cell onwards (index 2)
                    data_cells = cells[2:]
                    if current_date_index < len(data_cells):
                        # Get data cell corresponding to the current date
                        data_cell = data_cells[current_date_index]
                        set_text = data_cell.text.strip()
                        # DEBUG - keep for general info
                        logging.info(
                            f"    Date: {current_date_str}, Cell Text for Date Column: '{set_text}'")
                        if set_text and set_text != "-":  # Ignore empty/placeholder
                            match = re.match(
                                r"(\d+)\s*X\s*([\d.-]*)\s*(?:kg)?", set_text, re.IGNORECASE)
                            if match:
                                reps_str, weight_str = match.groups()
                                try:
                                    reps = int(reps_str)
                                    weight = float(
                                        weight_str) if weight_str and weight_str != '-' else 0.0
                                    set_data = {'set': int(set_number_text.split(' ')[1]), 'reps': reps, 'weight': weight,
                                                'date': current_date_str}  # Date is current date
                                    current_exercise_data['sets'].append(
                                        set_data)  # Append set data to current exercise
                                    logging.info(
                                        # DEBUG - keep for general info
                                        f"      Date: {current_date_str}, Extracted Set Data: Set {set_number_text.split(' ')[1]}, Reps: {reps}, Weight: {weight}")
                                except ValueError:
                                    logging.warning(
                                        f"    Date: {current_date_str}, ValueError parsing set data: {set_text}")
                            else:
                                logging.warning(
                                    f"    Date: {current_date_str}, Unparsable set data format: {set_text}")
            # Only add to list if there are exercises for this date
            if workout_data['exercises']:
                # Add populated workout data to the list
                workout_list_for_page.append(workout_data)

        logging.info(
            "Exiting analyze_workout_details_stripped (revised date-set mapping) - Data extraction complete.")
        # Return the list of workout dictionaries for all dates on the page
        return workout_list_for_page

    except Exception as e:
        logging.exception(
            f"Error analyzing workout details (revised date-set mapping): {e}")
        return []


if __name__ == "__main__":
    # Full list of clients to process
    client_names = [
        "Rebecca DAngelo",

        "Kelly Smith",
        "Alice Forster",
        "Sarika Ramani",

        "Nicole Lynch",
        "Conor Beveridge",
        "Kristy Cooper",
        "Rick Preston",
        "Claire Ruberu",
        "Kylie Pinder",
        "Jo Foy",
        "Tony Strupl",

        "Anna Somogyi",
        "Danny Birch",


        "Shane Minahan"
    ]

    # Login credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    # Ensure this is securely managed
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # Create TrainerizeAutomation instance
    automation = TrainerizeAutomation(gemini_api_key)

    # GraphQL health check for debugging
    print("DEBUG: Running GraphQL health check")
    test_query = "query { __typename }"
    health_data = automation.fetch_graphql(test_query)
    print(f"DEBUG: GraphQL health check result: {health_data}")
    # Clean up previous files before starting
    automation.cleanup_previous_files()

    # Dictionary to store data for all clients
    all_client_data = {}
    # Track retries per client
    client_retries = {name: 0 for name in client_names}
    max_retries = 1  # Allow 1 retry per client

    # Verify the credentials file
    import os
    if os.path.exists('service-account-credentials.json'):
        print("✓ Service account credentials file found")
    else:
        print("✗ ERROR: service-account-credentials.json not found!")
        # Exit or continue as needed

        # Verify Google Sheets API before processing clients
        print("Verifying Google Sheets API access...")
        if automation.verify_sheets_credentials():
            print("✓ Google Sheets API verification successful")
        else:
            print("⚠️ Warning: Google Sheets integration may not work correctly")

    initial_login_successful = False
    try:
        # Initial Login
        if automation.login(username, password):
            print("Initial login successful!")
            automation.handle_notification_popup()
            initial_login_successful = True
        else:
            print("Initial login failed! Exiting.")
            automation.cleanup()
            sys.exit(1)

        # Process each client using a while loop for retry logic
        client_index = 0
        while client_index < len(client_names):
            client_name = client_names[client_index]
            print(f"\\n{'-'*50}")
            print(
                f"Processing client {client_index + 1}/{len(client_names)}: {client_name} (Attempt {client_retries[client_name] + 1}/{max_retries + 1})")
            print(f"{'-'*50}")

            try:
                # Navigate to client
                if not automation.navigate_to_client(client_name):
                    print(
                        f"Skipping {client_name}: Could not navigate to client initially.")
                    # Attempt to recover for the next client
                    if not automation.navigate_back_to_clients_list():
                        print(
                            "Warning: Could not recover session to navigate back to client list. Trying general URL.")
                        try:
                            automation.driver.get(
                                "https://www.trainerize.com/Clients.aspx")
                            time.sleep(3)
                        except Exception as nav_e:
                            print(
                                f"FATAL: Could not navigate back to clients page after failing to navigate to {client_name}. Error: {nav_e}. Exiting.")
                            break  # Exit loop if recovery fails
                    client_index += 1  # Move to next client after skipping
                    continue  # Skip rest of the loop for this client

                # Variables to store analysis results
                bodyweight_availability = "not_analyzed"
                bodyweight_structured_data = {}
                bodyweight_analysis_text = "No data available"
                # --- Updated Nutrition Analysis Result Structure ---
                nutrition_analysis_results = {
                    "calories_protein": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Analysis not performed."},
                    "fats_carbs": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Analysis not performed."}
                }
                sleep_availability, sleep_analysis_text, average_sleep_hours = "not_analyzed", "Analysis not performed", None
                steps_availability, steps_structured_data, steps_analysis_text = "not_analyzed", {
                }, "Analysis not performed"
                photos_analysis = "No data available"
                weight_goal_text = "No weight goal found"
                workout_data_list = []

                # Analyze bodyweight
                if automation.click_progress_tab():
                    if automation.click_biometrics():
                        bodyweight_availability, bodyweight_structured_data, bodyweight_analysis_text = automation.analyze_bodyweight_graph()

                # Analyze nutrition - Store the results dictionary
                if automation.navigate_to_nutrition_graphs():
                    nutrition_analysis_results = automation.analyze_nutrition_graph()
                else:
                    logging.warning(
                        f"Failed to navigate to nutrition graphs for {client_name}.")
                    # Keep default 'not_analyzed' status

                # Analyze sleep
                if automation.navigate_to_sleep_graphs():
                    sleep_availability, sleep_analysis_text, average_sleep_hours = automation.analyze_sleep_graph()
                else:
                    logging.warning(
                        f"Failed to navigate to sleep graphs for {client_name}.")
                    sleep_availability, sleep_analysis_text = "navigation_failed", "Failed to navigate to sleep graph page."

                # Analyze steps
                if automation.navigate_to_steps_graphs():
                    # Assuming analyze_steps_graph returns a tuple (availability, structured_data, analysis_text)
                    # If it still returns just text, adjust this call and prepare_fitness_wrapped_data
                    steps_result = automation.analyze_steps_graph()
                    if isinstance(steps_result, tuple) and len(steps_result) == 3:
                        steps_availability, steps_structured_data, steps_analysis_text = steps_result
                    # Handle older return format if necessary
                    elif isinstance(steps_result, str):
                        steps_analysis_text = steps_result
                        # Attempt to parse availability/structured data from text if needed, or set defaults
                        # Indicate parsing needed or data structure assumed
                        steps_availability = "unknown_format"
                        logging.warning(
                            "analyze_steps_graph returned string, expected tuple. Adapt parsing if needed.")
                    else:
                        logging.warning(
                            f"Unexpected return type from analyze_steps_graph for {client_name}: {type(steps_result)}")
                        steps_availability, steps_analysis_text = "error", "Unexpected return format from step analysis."
                else:
                    logging.warning(
                        f"Failed to navigate to steps graphs for {client_name}.")
                    steps_availability, steps_analysis_text = "navigation_failed", "Failed to navigate to steps graph page."

                # Analyze progress photos
                if automation.click_progress_photos_tab():
                    photos_analysis = automation.analyze_progress_photos()

                # Get weight goal
                if automation.navigate_to_goals_and_habits_tab():
                    weight_goal_text = automation.get_current_weight_goal()

                # Get workout data
                if automation.click_progress_tab():
                    if automation.click_review_by_workout().startswith("Successfully"):
                        workout_data_list = automation.process_workouts()
                        print(
                            f"Retrieved {len(workout_data_list)} workout records")
                        automation.display_workout_statistics(
                            workout_data_list)

                # Prepare and save the fitness data - Pass the nutrition results dictionary
                # IMPORTANT: Ensure prepare_fitness_wrapped_data expects nutrition_analysis_results dictionary
                fitness_wrapped_data = automation.prepare_fitness_wrapped_data(
                    client_name,
                    bodyweight_availability,  # New
                    bodyweight_structured_data,  # New
                    bodyweight_analysis_text,  # Old bodyweight_analysis, now text part
                    nutrition_analysis_results,  # Pass the dictionary here
                    sleep_availability,
                    sleep_analysis_text,
                    average_sleep_hours,
                    steps_availability,
                    steps_structured_data,
                    steps_analysis_text,
                    photos_analysis,
                    weight_goal_text,
                    {}, "", "",  # weekly_summary, workouts_completed, total_workout_stats placeholders
                    workout_data_list
                )

                # Save data to JSON file
                json_filename = automation.save_fitness_wrapped_data(
                    client_name, fitness_wrapped_data)
                if json_filename:
                    print(
                        f"Successfully saved data for {client_name} to {json_filename}")
                    all_client_data[client_name] = {
                        'fitness_wrapped_data': fitness_wrapped_data}
                else:
                    print(f"Failed to save data for {client_name}")

                # Generate professional check-in review PDF and get content
                pdf_filename, review_content = automation.generate_professional_checkin_review(
                    client_name, fitness_wrapped_data)

                if pdf_filename and review_content:
                    print(
                        f"✓ Professional check-in review created: {pdf_filename}")
                    # Extract first and last name
                    name_parts = client_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        # Update Google Sheets with the check-in review content
                        if automation.update_gemini_checkin_data(first_name, last_name, review_content):
                            print(
                                f"✓ Check-in review content uploaded to Google Sheets for {client_name}")
                        else:
                            print(
                                f"✗ Failed to upload check-in review to Google Sheets for {client_name}")
                    else:
                        print(
                            f"⚠️ Could not split client name '{client_name}' into first and last name for Sheets update.")
                elif review_content:
                    print(
                        f"⚠️ Failed to create PDF, but review content generated for {client_name}.")
                    # Optionally attempt Sheets update even without PDF - consider adding logic here if needed
                else:  # Corrected else block
                    print(
                        f"✗ Failed to generate check-in review PDF and content for {client_name}")

                # Navigate back to clients list before processing the next client
                # Corrected indentation for this block
                if not automation.navigate_back_to_clients_list():
                    print(
                        f"Warning: Issue returning to clients list after processing {client_name}.")
                    # Try to recover by going to clients page directly
                    try:
                        automation.driver.get(
                            "https://www.trainerize.com/Clients.aspx")
                        time.sleep(3)
                    except Exception as recovery_e:
                        print(
                            f"FATAL: Error recovering session after client {client_name}: {recovery_e}. Exiting.")
                        break  # Exit loop if recovery fails

                # Successful processing, move to next client
                client_index += 1

            except (WebDriverException, TimeoutException, NoSuchElementException, InvalidSessionIdException, Exception) as e:
                print(f"ERROR processing client {client_name}: {e}")
                logging.exception(
                    f"Exception caught for client {client_name}:")

                client_retries[client_name] += 1
                if client_retries[client_name] <= max_retries:
                    print(
                        f"Attempting retry {client_retries[client_name]}/{max_retries} for {client_name} after error...")
                    try:
                        print("Cleaning up current browser session...")
                        automation.cleanup()  # Close browser if possible
                    except Exception as cleanup_err:
                        print(
                            f"Error during cleanup before retry: {cleanup_err}")

                    print("Waiting 10 seconds before retry...")
                    time.sleep(10)

                    print("Re-initializing browser and logging in...")
                    try:
                        automation = TrainerizeAutomation(
                            gemini_api_key)  # Re-create instance
                        if automation.login(username, password):
                            print("Re-login successful. Retrying client...")
                            automation.handle_notification_popup()
                            # The loop will automatically retry the current client_index
                            continue  # Go to the start of the while loop for the same client
                        else:
                            print(
                                f"Re-login failed after error with {client_name}. Skipping client.")
                            client_index += 1  # Skip to next client
                            # Still need to ensure next client starts fresh
                            print("Cleaning up again after failed re-login...")
                            automation.cleanup()
                            print("Re-initializing for next client...")
                            automation = TrainerizeAutomation(gemini_api_key)
                            if not automation.login(username, password):
                                print(
                                    "FATAL: Could not log in after failed retry. Exiting.")
                                break  # Exit the loop if we can't even log in for the next client
                            automation.handle_notification_popup()

                    except Exception as init_err:
                        print(
                            f"FATAL: Error re-initializing automation after error: {init_err}. Exiting loop.")
                        break  # Exit loop if re-initialization fails

                else:
                    print(
                        f"Max retries exceeded for {client_name}. Skipping client.")
                    client_index += 1  # Move to next client
                    # Ensure we start fresh for the next client after skipping
                    print(
                        f"Cleaning up session after skipping {client_name}...")
                    try:
                        automation.cleanup()
                    except Exception as cleanup_err:
                        print(
                            f"Error during cleanup after skipping client: {cleanup_err}")

                    # Only try to re-initialize if there are more clients
                    if client_index < len(client_names):
                        print("Re-initializing for next client...")
                        try:
                            automation = TrainerizeAutomation(gemini_api_key)
                            if not automation.login(username, password):
                                print(
                                    "FATAL: Could not log in for the next client after skipping. Exiting.")
                                break  # Corrected break statement placement
                            automation.handle_notification_popup()
                        except Exception as init_err:
                            print(
                                f"FATAL: Error re-initializing automation for next client: {init_err}. Exiting loop.")
                            break
                    else:
                        print(
                            "Reached end of client list after skipping last client.")

        # After processing all clients (or exiting loop)
        if initial_login_successful:  # Only proceed if initial login worked
            print("\nFinding most improved client...")
            most_improved_info = automation.find_most_improved_client(
                all_client_data)
            if most_improved_info[0]:
                print(
                    f"\nMost improved client: {most_improved_info[0]} with {most_improved_info[1]:.2f}% workload increase")
                # Update all JSON files with most improved information
                # Use keys from processed data
                if automation.update_json_files_with_most_improved(most_improved_info, list(all_client_data.keys())):
                    print(
                        "Successfully updated all client JSON files with most improved information")
                else:
                    print("Failed to update JSON files with most improved information")
            else:
                print(
                    "\nCould not determine most improved client (no valid workload data or no clients processed successfully)")

            print("\nAll clients processed (or attempted). Cleaning up...")
        else:
            print("Script exited before processing clients due to initial login failure.")

    except Exception as e:
        print(f"Fatal error during script execution: {e}")
        logging.exception("Fatal error in main execution block:")

    finally:
        # Always clean up resources
        print("Final cleanup.")
        try:
            automation.cleanup()
        except Exception as final_cleanup_e:
            print(f"Error during final cleanup: {final_cleanup_e}")
        print("Script execution complete.")
