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
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import requests  # Add requests import for GraphQL API calls
from collections import defaultdict

# Import calendar analyzer for comprehensive data analysis
from calendar_analyzer import CalendarAnalyzer

# --- START sys.path modification ---
# Assuming checkin_good_110525.py is in 'shanbot' directory
# and dashboard_sqlite_utils.py is in 'shanbot/app/dashboard_modules'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_MODULES_PATH = os.path.join(SCRIPT_DIR, "app", "dashboard_modules")
if APP_MODULES_PATH not in sys.path:
    sys.path.insert(0, APP_MODULES_PATH)
# --- END sys.path modification ---

# --- START DB UTILS IMPORT ---
try:
    from dashboard_sqlite_utils import get_db_connection, create_workout_tables_if_not_exist, save_workout_session, get_ig_username_by_name, create_user_table_if_not_exists, save_metrics_to_sqlite
    SQLITE_UTILS_IMPORTED = True
    print("Successfully imported SQLite utility functions.")
except ImportError as e:
    SQLITE_UTILS_IMPORTED = False
    print(f"WARNING: Could not import SQLite utility functions: {e}")
    print("Workout data will not be saved to SQLite.")

# --- START ENHANCED STORAGE IMPORT ---
try:
    from comprehensive_workout_storage_system import ComprehensiveWorkoutStorage
    ENHANCED_STORAGE_AVAILABLE = True
    print("✓ Enhanced workout storage system loaded successfully")
except ImportError as e:
    ENHANCED_STORAGE_AVAILABLE = False
    print(f"⚠️  Enhanced storage system not available: {e}")
    print("Using basic SQLite storage only.")
# --- END ENHANCED STORAGE IMPORT ---

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
        # Use system Chrome instead of portable version
        # chrome_options.binary_location = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"

        try:
            # Use the manually downloaded ChromeDriver 137 that matches our Chrome version
            chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
            print(
                f"Using manually downloaded ChromeDriver: {chromedriver_path}")
            service = ChromeService(executable_path=chromedriver_path)
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
            1. For any data that's not available (labeled "NO DATA" or "Not Recorded"), include a professionally-worded encouragement to start tracking this metric UNLESS the specific text for that metric is "No data recorded for the current week." If that specific text is provided for a metric, use that exact text as the analysis for that section.
            2. Use bold text indicators with "Weight Management Analysis:" format (not **Weight Management Analysis:**)
            3. In the Training Performance Analysis section, DO NOT list the specific workout names (like "Chest and Biceps" etc.)
            4. Make the "Goals and Recommendations for the Coming Week:" section use bullet points with "* " at the start of each point
            5. DO NOT include a section labeled "Closing Statement:" - instead, just add a motivational closing paragraph after the bullet points without a label
            6. The review will be signed off as "Coco's Connected/Shannon Birch" - no need to include this in the content
            7. VERY IMPORTANT: When addressing the client directly in the review, use only their first name ("{first_name}"), not their full name
            8. For any data marked "Not Recorded" (and not covered by point 1's exception), include specific encouragement for the client to track this metric, explaining its importance to their fitness journey

            CLIENT DATA:
            """

            # Bodyweight section for prompt
            if fitness_wrapped_data.get('bodyweight_analysis_for_prompt') == "No data recorded for the current week.":
                prompt += """
                - Weight: No data recorded for the current week.
                """
            elif has_weight_data and fitness_wrapped_data.get('current_weight', 'Not Recorded') != 'Not Recorded':
                total_change = fitness_wrapped_data['total_weight_change']
                start_weight = int(fitness_wrapped_data['start_weight'])
                current_weight = int(fitness_wrapped_data['current_weight'])
                prompt += f"""
                - Weight: Started at {start_weight}kg, currently {current_weight}kg
                - Total weight change: {int(abs(total_change))}kg {'loss' if total_change > 0 else 'gain'} (IMPORTANT: This is the OVERALL total change since starting, NOT just for this week)
                """
                if fitness_wrapped_data['weight_goal'] is not False and isinstance(fitness_wrapped_data['weight_goal'], dict) and 'target' in fitness_wrapped_data['weight_goal']:
                    weight_goal_target = fitness_wrapped_data['weight_goal']['target']
                    weight_goal_int = int(weight_goal_target)
                    prompt += f"- Weight goal: {weight_goal_int}kg\n"
                else:
                    prompt += "- IMPORTANT: DO NOT MENTION ANY WEIGHT GOAL - the client does not have one set\n"
            else:
                prompt += """
                - Weight: NO DATA (emphasize that consistent weight tracking is crucial for monitoring progress and adjusting the nutrition and training plan accordingly)
                """

            # Workout data (existing logic is fine)
            if has_workout_data:
                prompt += f"""
                - Workouts completed this week: {fitness_wrapped_data['workouts_this_week']}
                - Workout types: { ', '.join(fitness_wrapped_data['workout_types'][:4])}
                - Total weight lifted: {fitness_wrapped_data['total_weight_lifted']}kg
                - Total reps: {fitness_wrapped_data['total_reps']}
                - Total sets: {fitness_wrapped_data['total_sets']}
                - Workload increase: {fitness_wrapped_data['workload_increase']}%
                """
            else:
                prompt += """
                - Workouts: NO DATA (emphasize the importance of logging workouts to track progress, ensure program adherence, and allow for proper load management)
                """

            # Nutrition section for prompt using the consolidated text
            nutrition_prompt_text = fitness_wrapped_data.get(
                'nutrition_analysis_for_prompt', "NO DATA (explain how proper nutrition tracking is essential for body composition goals, recovery, and energy management)")
            if nutrition_prompt_text == "No data recorded for the current week.":
                prompt += """
                - Nutrition: No data recorded for the current week.
                """
            elif has_nutrition_data and fitness_wrapped_data.get('calories_consumed', 'Not Recorded') != 'Not Recorded':
                calories = fitness_wrapped_data['calories_consumed']
                calories_note = ""
                try:
                    calories_str = str(calories).split()[0]
                    try:
                        calories_value = int(calories_str)
                        if calories_value < 1000:
                            calories_note = " (IMPORTANT: This low calorie count is most likely due to inconsistent tracking - focus on encouraging more consistent tracking rather than discussing low calorie intake)"
                    except ValueError:
                        try:
                            calories_value = int(float(calories_str))
                            if calories_value < 1000:
                                calories_note = " (IMPORTANT: This low calorie count is most likely due to inconsistent tracking - focus on encouraging more consistent tracking rather than discussing low calorie intake)"
                        except ValueError:
                            pass
                except Exception as e:
                    logging.warning(f"Error processing calories value: {e}")
                nutrition_consistency_note = ""
                if not fitness_wrapped_data.get('nutrition_tracking_consistent', True):
                    days_tracked = fitness_wrapped_data.get(
                        'nutrition_tracking_days', 0)
                    if days_tracked > 0:
                        nutrition_consistency_note = f"""
                - Nutrition tracking consistency: INCONSISTENT - only tracked {days_tracked} day{'s' if days_tracked > 1 else ''} (IMPORTANT: Focus on encouraging consistent daily tracking)
"""
                    else:
                        nutrition_consistency_note = """
                - Nutrition tracking consistency: INCONSISTENT (IMPORTANT: Focus on encouraging consistent daily tracking)
                """
                prompt += f"""
                - Calories: {calories}{calories_note}
                - Protein: {fitness_wrapped_data['protein_consumed']}
                - Fats: {fitness_wrapped_data['fats_consumed']}
                - Carbs: {fitness_wrapped_data['carbs_consumed']}{nutrition_consistency_note}
                """
            else:  # General NO DATA for nutrition if not covered by specific "No data recorded..."
                prompt += """
                - Nutrition: NO DATA (explain how proper nutrition tracking is essential for body composition goals, recovery, and energy management)
                """

            # Steps section for prompt
            steps_prompt_text = fitness_wrapped_data.get(
                'steps_analysis_for_prompt', "NO DATA (explain how tracking daily steps helps monitor non-exercise activity and contributes to overall calorie expenditure)")
            if steps_prompt_text == "No data recorded for the current week.":
                prompt += """
                - Steps: No data recorded for the current week.
                """
            elif has_steps_data and fitness_wrapped_data.get('step_count', 'Not Recorded') != 'Not Recorded':
                prompt += f"""
                - Average step count: {fitness_wrapped_data['step_count']}
                """
                if fitness_wrapped_data.get('step_count') == "Inconsistent Tracking":
                    prompt += "                (explain how tracking daily steps helps monitor non-exercise activity and contributes to overall calorie expenditure, and encourage more consistent tracking)\
"
            else:
                prompt += """
                - Steps: NO DATA (explain how tracking daily steps helps monitor non-exercise activity and contributes to overall calorie expenditure)
                """

            # Sleep section for prompt
            sleep_prompt_text = fitness_wrapped_data.get(
                'sleep_analysis_for_prompt', "NO DATA (explain how tracking sleep quality and duration is crucial for recovery, performance, and overall health)")
            if sleep_prompt_text == "No data recorded for the current week.":
                prompt += """
                - Sleep: No data recorded for the current week.
                """
            elif has_sleep_data and fitness_wrapped_data.get('sleep_hours', 'Not Recorded') != 'Not Recorded':
                prompt += f"""
                - Sleep pattern: {fitness_wrapped_data['sleep_hours']}
                """
            else:
                prompt += """
                - Sleep: NO DATA (explain how tracking sleep quality and duration is crucial for recovery, performance, and overall health)
                """

            # Exercise improvement data (existing logic fine)
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
            2. Weight Management Analysis: (If the input for this section is "No data recorded for the current week.", then use that exact text. Otherwise, provide your analysis or encouragement to track if no data)
               - Start this on a new line with exactly "Weight Management Analysis:" and then continue with your analysis
               - VERY IMPORTANT: When discussing weight change, refer to it as "overall weight change" or "total progress so far" - DO NOT say "this week you lost X kg" as the weight data represents total change since starting, not weekly change
            3. Training Performance Analysis: (or encouragement to track if no data)
               - Start this on a new line with exactly "Training Performance Analysis:" and then continue with your analysis
            4. Nutrition and Lifestyle Observations: (If the input for this section is "No data recorded for the current week.", then use that exact text. Otherwise, provide your analysis, or encouragement to track if no data. This section covers Nutrition, Steps, and Sleep from the CLIENT DATA section above. Synthesize these into your observations.)
               - Start this on a new line with exactly "Nutrition and Lifestyle Observations:" and then continue with your analysis
               - Include analysis of both calorie intake and macronutrient balance (protein, fats, carbs) if data is available
               - Comment on the protein intake relative to body weight goals
               - Comment on the balance of fats and carbs in the diet
               - Incorporate steps and sleep analysis here as well.
            5. Specific Exercise Achievements: (highlight top improvements) (or encouragement to track if no data)
               - Start this on a new line with exactly "Specific Exercise Achievements:" and then continue with your analysis
            6. Missing Data: (summarize what data is missing and the benefits of tracking it - if any data is missing AND the specific text for that metric was NOT "No data recorded for the current week." If it was, it has already been stated, so do not repeat it here. Focus on other types of missing data or general encouragement for metrics not specifically called out as "No data recorded for the current week.")
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
                name='NoDataBlueStyle',  # New style for blue "no data" message
                parent=styles['Normal'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
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
                                # Check for the specific "No data" message for styling
                                if remaining_text == "No data recorded for the current week.":
                                    content.append(
                                        Paragraph(remaining_text, styles['NoDataBlueStyle']))
                                else:
                                    content.append(
                                        Paragraph(remaining_text, normal_style))
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

    def analyze_detailed_workout_progress(self, workout_data_list, current_week_start_dt, current_week_end_dt, previous_week_start_dt, previous_week_end_dt, top_n_lifts=3):
        """
        Analyzes workout progress in detail, comparing current week to previous week
        for each workout type and identifying most improved lifts by volume.

        Args:
            workout_data_list: List of all workout dictionaries.
            current_week_start_dt: datetime.date object for the start of the current week.
            current_week_end_dt: datetime.date object for the end of the current week.
            previous_week_start_dt: datetime.date object for the start of the previous week.
            previous_week_end_dt: datetime.date object for the end of the previous week.
            top_n_lifts: Number of top improved lifts to return.

        Returns:
            dict: Containing 'workout_breakdown' and 'most_improved_lifts_by_volume'.
        """
        from collections import defaultdict
        import logging

        detailed_analysis = {
            "workout_breakdown": [],
            "most_improved_lifts_by_volume": []
        }

        # Helper to parse date string from workout_data_list
        def parse_workout_date(date_str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d %b %Y').date()
                except ValueError:
                    logging.warning(
                        f"Could not parse date: {date_str} in analyze_detailed_workout_progress")
                    return None

        # 1. Filter workouts into current and previous week buckets
        current_week_sessions = []
        previous_week_sessions = []
        for session in workout_data_list:
            session_date = parse_workout_date(session['date'])
            if not session_date:
                continue

            # Ensure session['exercises'] is a list
            if not isinstance(session.get('exercises'), list):
                logging.warning(
                    f"Skipping session on {session_date} for workout {session.get('workout_type')} due to malformed exercises data.")
                continue

            if current_week_start_dt <= session_date <= current_week_end_dt:
                current_week_sessions.append(session)
            elif previous_week_start_dt <= session_date <= previous_week_end_dt:
                previous_week_sessions.append(session)

        # 2. Process Workout Breakdown (session by session for current week)
        # Group current week sessions by workout_type
        current_workouts_by_type = defaultdict(list)
        for session in current_week_sessions:
            current_workouts_by_type[session['workout_type']].append(session)

        for workout_type, sessions_this_week in current_workouts_by_type.items():
            workout_type_breakdown = {
                "workout_name": workout_type,
                "sessions_current_week": [],
                "overall_status_for_video": "No improvements this week"  # Default
            }
            any_exercise_improved_in_type = False
            performed_last_week_for_comparison = False

            for current_session in sorted(sessions_this_week, key=lambda s: parse_workout_date(s['date'])):
                current_session_date = parse_workout_date(
                    current_session['date'])
                session_detail = {
                    "date": current_session_date.strftime('%Y-%m-%d'),
                    "exercises": []
                }

                # Find the most recent comparable session in the previous week for this workout_type
                comparable_prev_sessions = sorted([
                    s for s in previous_week_sessions
                    if s['workout_type'] == workout_type and parse_workout_date(s['date']) < current_session_date
                ], key=lambda s: parse_workout_date(s['date']), reverse=True)

                previous_comparable_session = comparable_prev_sessions[
                    0] if comparable_prev_sessions else None
                if previous_comparable_session:
                    performed_last_week_for_comparison = True

                for current_ex in current_session.get('exercises', []):
                    # Ensure current_ex and its sets are well-formed
                    if not isinstance(current_ex, dict) or not isinstance(current_ex.get('sets'), list):
                        logging.warning(
                            f"Skipping exercise in {workout_type} on {current_session_date} due to malformed data: {current_ex}")
                        continue

                    ex_name = current_ex['name']
                    current_workload = sum(s['weight'] * s['reps'] for s in current_ex['sets']
                                           if isinstance(s, dict) and 'weight' in s and 'reps' in s)

                    previous_workload_for_ex = 0
                    if previous_comparable_session:
                        for prev_ex in previous_comparable_session.get('exercises', []):
                            if isinstance(prev_ex, dict) and prev_ex['name'] == ex_name and isinstance(prev_ex.get('sets'), list):
                                previous_workload_for_ex = sum(
                                    s['weight'] * s['reps'] for s in prev_ex['sets'] if isinstance(s, dict) and 'weight' in s and 'reps' in s)
                                break

                    improvement = 0
                    improved_this_ex = False
                    if previous_workload_for_ex > 0:
                        improvement = (
                            (current_workload - previous_workload_for_ex) / previous_workload_for_ex) * 100
                        if improvement > 0:
                            improved_this_ex = True
                            any_exercise_improved_in_type = True
                    elif current_workload > 0:  # New exercise or no previous data but done this week
                        improved_this_ex = True  # Considered an "improvement" if done this week and not last
                        any_exercise_improved_in_type = True

                    session_detail["exercises"].append({
                        "name": ex_name,
                        "sets_current": [{'reps': s.get('reps', 0), 'weight': s.get('weight', 0)} for s in current_ex['sets']],
                        "workload_current": current_workload,
                        "workload_previous_comparable": previous_workload_for_ex,
                        "workload_improvement_vs_previous": round(improvement, 1) if previous_workload_for_ex > 0 else (100 if current_workload > 0 else 0),
                        "improved_this_session": improved_this_ex
                    })
                workout_type_breakdown["sessions_current_week"].append(
                    session_detail)

            if any_exercise_improved_in_type:
                workout_type_breakdown["overall_status_for_video"] = "Some exercises improved"
            elif not performed_last_week_for_comparison and any(s['exercises'] for s in workout_type_breakdown["sessions_current_week"]):
                # Or "Not performed last week for comparison"
                workout_type_breakdown["overall_status_for_video"] = "Good job getting it done this week!"
            elif not any(s['exercises'] for s in workout_type_breakdown["sessions_current_week"]):
                workout_type_breakdown["overall_status_for_video"] = "No data for this workout this week"

            detailed_analysis["workout_breakdown"].append(
                workout_type_breakdown)

        # 3. Process Most Improved Lifts by Absolute Volume Increase
        exercise_volume_changes = defaultdict(lambda: {"current_total_workload": 0, "previous_total_workload": 0, "current_week_sets_all_sessions": [
        ], "previous_week_sets_all_sessions": []})

        # Aggregate current week workloads and sets for each exercise
        for session in current_week_sessions:
            for ex in session.get('exercises', []):
                if not isinstance(ex, dict) or not isinstance(ex.get('sets'), list):
                    continue
                ex_name = ex['name']
                ex_workload = sum(s['weight'] * s['reps'] for s in ex['sets']
                                  if isinstance(s, dict) and 'weight' in s and 'reps' in s)
                exercise_volume_changes[ex_name]["current_total_workload"] += ex_workload
                exercise_volume_changes[ex_name]["current_week_sets_all_sessions"].extend([{'reps': s.get(
                    'reps', 0), 'weight': s.get('weight', 0), 'date': session['date']} for s in ex['sets']])

        # Aggregate previous week workloads and sets for each exercise
        for session in previous_week_sessions:
            for ex in session.get('exercises', []):
                if not isinstance(ex, dict) or not isinstance(ex.get('sets'), list):
                    continue
                ex_name = ex['name']
                # Only consider exercises that were also done in the current week for direct comparison of improvement
                if ex_name in exercise_volume_changes:
                    ex_workload = sum(s['weight'] * s['reps'] for s in ex['sets']
                                      if isinstance(s, dict) and 'weight' in s and 'reps' in s)
                    exercise_volume_changes[ex_name]["previous_total_workload"] += ex_workload
                    exercise_volume_changes[ex_name]["previous_week_sets_all_sessions"].extend([{'reps': s.get(
                        'reps', 0), 'weight': s.get('weight', 0), 'date': session['date']} for s in ex['sets']])

        lifts_with_improvement = []
        for ex_name, data in exercise_volume_changes.items():
            volume_increase = data["current_total_workload"] - \
                data["previous_total_workload"]
            # Positive increase or new exercise performed
            if volume_increase > 0 or (data["current_total_workload"] > 0 and data["previous_total_workload"] == 0):
                lifts_with_improvement.append({
                    "name": ex_name,
                    "volume_increase_kg": volume_increase,
                    "current_total_workload_kg": data["current_total_workload"],
                    "previous_total_workload_kg": data["previous_total_workload"],
                    # Sort sets by date
                    "current_week_sets": sorted(data["current_week_sets_all_sessions"], key=lambda x: parse_workout_date(x['date'])),
                    "previous_week_sets_comparable": sorted(data["previous_week_sets_all_sessions"], key=lambda x: parse_workout_date(x['date'])) if data["previous_week_sets_all_sessions"] else []
                })

        # Sort by volume_increase_kg descending
        detailed_analysis["most_improved_lifts_by_volume"] = sorted(
            lifts_with_improvement, key=lambda x: x["volume_increase_kg"], reverse=True)[:top_n_lifts]

        logging.info(
            f"Detailed workout analysis generated. Breakdown items: {len(detailed_analysis['workout_breakdown'])}, Top lifts by volume: {len(detailed_analysis['most_improved_lifts_by_volume'])}")
        return detailed_analysis

    def prepare_fitness_wrapped_data(self, client_name, bodyweight_availability, bodyweight_structured_data, bodyweight_analysis_text, nutrition_analysis_results,
                                     sleep_availability, sleep_analysis_text, average_sleep_hours,
                                     steps_availability, steps_structured_data, steps_analysis_text,
                                     photos_analysis, weight_goal_text, weekly_summary_data,
                                     workouts_completed_analysis, total_workout_stats_analysis, workout_data_list):
        """Prepare comprehensive fitness wrapped data for the client."""
        # Initialize consistency_check_text to prevent UnboundLocalError
        consistency_check_text = ""
        logging.info(f"DEBUG prepare_fitness_wrapped_data for {client_name}:")
        logging.info(
            f"  Raw bodyweight_availability: {bodyweight_availability}, bodyweight_analysis_text: {bodyweight_analysis_text}")
        logging.info(
            f"  Raw nutrition_analysis_results: {nutrition_analysis_results}")
        logging.info(
            f"  Raw sleep_availability: {sleep_availability}, sleep_analysis_text: {sleep_analysis_text}, average_sleep_hours: {average_sleep_hours}")
        logging.info(f"  Raw steps_availability: {steps_availability}")
        logging.info(f"  Raw steps_structured_data: {steps_structured_data}")
        logging.info(f"  Raw steps_analysis_text: {steps_analysis_text}")

        # Initialize nutrition tracking consistency indicators
        nutrition_tracking_consistent = True
        nutrition_tracking_days = 0
        nutrition_consistency_message = ""

        # Consolidate nutrition analysis text for consistency check and later use
        # For the prompt to Gemini later
        cp_analysis_text_for_prompt = nutrition_analysis_results.get(
            'calories_protein', {}).get('analysis_text', 'Analysis not available.')
        fc_analysis_text_for_prompt = nutrition_analysis_results.get(
            'fats_carbs', {}).get('analysis_text', 'Analysis not available.')

        cp_no_data = cp_analysis_text_for_prompt == "No data recorded for the current week."
        fc_no_data = fc_analysis_text_for_prompt == "No data recorded for the current week."

        if cp_no_data and fc_no_data:
            combined_nutrition_text_for_prompt = "No data recorded for the current week."
        elif cp_no_data:
            combined_nutrition_text_for_prompt = f"Calories & Protein: No data recorded for the current week.\nFats & Carbs: {fc_analysis_text_for_prompt}"
        elif fc_no_data:
            combined_nutrition_text_for_prompt = f"Calories & Protein: {cp_analysis_text_for_prompt}\nFats & Carbs: No data recorded for the current week."
        else:
            combined_nutrition_text_for_prompt = f"Calories & Protein: {cp_analysis_text_for_prompt}\nFats & Carbs: {fc_analysis_text_for_prompt}"

        original_cp_text = nutrition_analysis_results.get(
            'calories_protein', {}).get('analysis_text', '')
        original_fc_text = nutrition_analysis_results.get(
            'fats_carbs', {}).get('analysis_text', '')

        if not (original_cp_text == "No data recorded for the current week." and original_fc_text == "No data recorded for the current week."):
            consistency_check_text = original_cp_text + "\n" + original_fc_text
        logging.info(
            f"Combined nutrition analysis text (for consistency check): {consistency_check_text[:300]}...")
        consistency_warning_match = re.search(
            r"⚠️\s*\*\*Nutrition Tracking Alert\*\*:\s*(.*?)(?:\n|\Z)", consistency_check_text, re.DOTALL
        )
        if consistency_warning_match:
            nutrition_consistency_message = consistency_warning_match.group(
                1).strip()
            nutrition_tracking_consistent = False
            days_tracked_match = re.search(
                r"only tracked (\d+) day", nutrition_consistency_message
            )
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
        # Keep for PDF, might be useful even if overall availability is 'none' for recent week
        steps_trend_str = "Not Recorded"

        # Use the new direct inputs for steps
        if steps_availability == "substantial":
            avg_steps_raw = steps_structured_data.get(
                'AVERAGE_STEPS', "Not Recorded")
            if avg_steps_raw and avg_steps_raw.lower() == "inconsistent tracking":
                step_count_str = "Inconsistent Tracking"  # This specific string is used in PDF
                has_steps_data_flag = True
            elif avg_steps_raw and avg_steps_raw != "Not Recorded" and avg_steps_raw.lower() != "not visible":
                step_count_str = avg_steps_raw
                has_steps_data_flag = True
            else:  # Should not happen if availability is substantial and avg_steps_raw is 'not visible'
                # Fallback for substantial if avg_steps is somehow 'not visible'
                step_count_str = "Tracked (Avg N/A)"
                has_steps_data_flag = True

            highest_raw = steps_structured_data.get(
                'HIGHEST_STEPS', "Not Recorded")
            if highest_raw and highest_raw != "Not Recorded" and highest_raw.lower() != "not visible":
                highest_steps_str = highest_raw

            current_steps_trend = steps_structured_data.get(
                'TREND', "Not Recorded")
            if current_steps_trend and current_steps_trend.lower() != "not visible":
                steps_trend_str = current_steps_trend

        elif steps_availability == "minimal":
            step_count_str = "Inconsistent Tracking"  # For PDF and Gemini prompt later
            has_steps_data_flag = True  # Minimal means some data, so flag true
            current_steps_trend = steps_structured_data.get(
                'TREND', "Not Recorded")
            if current_steps_trend and current_steps_trend.lower() != "not visible":
                steps_trend_str = current_steps_trend

        elif steps_availability == "none":  # Explicitly "none"
            # This will be used by PDF. The analysis_text has "No data..."
            step_count_str = "Not Recorded"
            has_steps_data_flag = False
            # steps_trend_str remains "Not Recorded"

        # For cases like "navigation_failed", "image_error", "error", "not_analyzed"
        # steps_analysis_text will contain the specific error or "No data..." if it was set
        # has_steps_data_flag will remain False if it wasn't set to True above.
        # step_count_str will remain "Not Recorded"

        logging.info(
            f"Processed steps data for {client_name}: Availability='{steps_availability}', Avg='{step_count_str}', Trend='{steps_trend_str}', HasDataFlag='{has_steps_data_flag}'")

        # --- Sleep Data ---
        sleep_hours_str = "Not Recorded"
        has_sleep_data_flag = False
        if sleep_availability == "substantial":
            if average_sleep_hours and average_sleep_hours.lower() != "not visible":
                sleep_hours_str = average_sleep_hours
                has_sleep_data_flag = True
            else:  # Substantial but average_sleep_hours somehow not visible or None
                sleep_hours_str = "Tracking Consistent (Avg N/A)"
                has_sleep_data_flag = True
        elif sleep_availability == "minimal":
            sleep_hours_str = "Inconsistent Tracking"  # Or use Gemini's text for minimal
            has_sleep_data_flag = True  # Minimal implies some data
        # For "none" or other error/not_analyzed states, sleep_hours_str remains "Not Recorded"
        # and has_sleep_data_flag remains False, sleep_analysis_text has the specific message.

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

        # --- START New Detailed Workout Analysis ---
        detailed_workout_analysis_data = self.analyze_detailed_workout_progress(
            workout_data_list,
            current_week_start_dt,
            current_week_end_dt,
            previous_week_start_dt,
            previous_week_end_dt,
            top_n_lifts=3  # You can adjust how many top lifts by volume you want
        )
        # --- END New Detailed Workout Analysis ---

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
            "has_reliable_weight_data": has_reliable_weight_data_flag,

            # Pass the specific analysis texts for each metric to be used in the main Gemini prompt
            "bodyweight_analysis_for_prompt": bodyweight_analysis_text,
            "nutrition_analysis_for_prompt": combined_nutrition_text_for_prompt,
            "sleep_analysis_for_prompt": sleep_analysis_text,
            "steps_analysis_for_prompt": steps_analysis_text,

            # --- START Add new detailed workout data to JSON ---
            "workout_breakdown": detailed_workout_analysis_data.get("workout_breakdown", []),
            "most_improved_lifts_details": detailed_workout_analysis_data.get("most_improved_lifts_by_volume", [])
            # --- END Add new detailed workout data to JSON ---
        }
        logging.info(
            f"Final fitness_wrapped_data keys for {client_name}: has_weight_data={fitness_wrapped_data['has_weight_data']}, current_weight={fitness_wrapped_data['current_weight']}, workout_breakdown_items={len(fitness_wrapped_data.get('workout_breakdown', []))}, etc.")
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
            _, _, _, _, _, current_week_workouts_data, _ = self.calculate_workout_stats_for_date_range(
                    workout_data_list, current_week_start, current_week_end)
            _, _, _, _, _, prev_week_workouts_data, _ = self.calculate_workout_stats_for_date_range(
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
            # Use title attribute with contains for partial matching (more flexible)
            client_link_locator = (
                By.XPATH, f"//a[contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{client_name.lower()}')]")
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

            lines = raw_analysis.strip().split('\n')  # Use literal newline for splitting
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
                # If availability truly cannot be parsed, and text suggests no data, set accordingly
                if "no bodyweight data" in analysis_text.lower() or "not visible" in analysis_text.lower():
                    availability_status = "none"
                    analysis_text = "No bodyweight data recorded for the current week."
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
                # Use literal newline for joining
                analysis_text = '\n'.join(lines[line_index:]).strip()
            elif availability_status == "none":  # Ensures if no text follows AVAILABILITY: none
                analysis_text = "No bodyweight data recorded for the current week."
            # Corrected for minimal
            elif availability_status in ["minimal"] and not analysis_text:
                analysis_text = f"Bodyweight data for the recent week appears {availability_status}. Consistent tracking is key for monitoring progress."
            elif availability_status == "substantial" and not analysis_text:
                analysis_text = "Substantial bodyweight data detected for the recent week, but analysis text is missing."
                logging.warning(analysis_text)
            elif not analysis_text:  # Default if still empty and not 'none' or 'minimal'
                analysis_text = "Could not parse bodyweight analysis text."
                logging.warning(analysis_text)

            # Explicitly set for "none" availability
            if availability_status == "none":
                analysis_text = "No bodyweight data recorded for the current week."

            return availability_status, structured_data, analysis_text

        except TimeoutException:
            # Added logging
            logging.warning(
                "TimeoutException: Bodyweight graph element not found.")
            # Modified return
            return "no_data_found", {}, "No bodyweight data recorded for the current week."

        except Exception as e:
            logging.exception(
                f"Error analyzing graph with gemini-2.0-flash: {e}")
            return "error", {}, f"Error analyzing bodyweight graph: {e}"  # Modified return

    def analyze_comprehensive_calendar_data(self, client_name, username, password, gemini_api_key):
        """
        Comprehensive calendar analysis using the EXISTING browser session.
        Returns structured data compatible with existing checkin format.
        """
        print("🔍 Starting comprehensive calendar analysis using existing session...")

        try:
            # Use the existing browser session - we're already logged in and on the client's profile
            print("✅ Using existing browser session (already logged in)")

            # Navigate to calendar tab using existing session
            print("📅 Navigating to calendar tab...")
            if not self.click_calendar_tab():
                print("❌ Could not open calendar tab")
                return self._get_default_calendar_results()

            # Wait for calendar to load
            print("⏳ Waiting for calendar to load...")
            time.sleep(5)

            # Take a screenshot for analysis
            print("📸 Taking calendar screenshot...")
            screenshot_path = f"{client_name.replace(' ', '_')}_calendar_analysis.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"✅ Screenshot saved: {screenshot_path}")

            # Analyze calendar with Gemini if API key is available
            calendar_analysis = ""
            if gemini_api_key:
                print("🤖 Analyzing calendar with Gemini AI...")
                calendar_analysis = self.analyze_calendar_with_gemini(
                    screenshot_path, gemini_api_key)

            # Extract visible calendar data
            print("📋 Extracting visible calendar data...")
            calendar_data = self.extract_calendar_data_from_current_page()

            # Convert calendar data to checkin format
            return self._convert_calendar_data_to_checkin_format(calendar_data, calendar_analysis)

        except Exception as e:
            print(f"❌ Error in comprehensive calendar analysis: {e}")
            logging.exception(
                f"Calendar analysis error for {client_name}: {e}")
            return self._get_default_calendar_results()

    def click_calendar_tab(self):
        """Navigate to the calendar tab using existing session"""
        try:
            print("🔍 Looking for calendar tab...")

            # Try multiple selectors for calendar tab
            calendar_selectors = [
                "//a[contains(@href, 'calendar')]",
                "//a[contains(text(), 'Calendar')]",
                "//p[text()='Calendar']/parent::a",
                "//*[contains(@class, 'nav') and contains(text(), 'Calendar')]",
                "//nav//a[contains(text(), 'Calendar')]"
            ]

            for i, selector in enumerate(calendar_selectors, 1):
                try:
                    print(
                        f"🔍 Trying calendar selector {i}: {selector[:50]}...")
                    calendar_element = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector)))

                    if calendar_element and calendar_element.is_displayed():
                        print(f"✅ Found calendar tab with selector {i}")

                        # Scroll into view and click
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", calendar_element)
                        time.sleep(1)
                        calendar_element.click()

                        print("✅ Successfully clicked calendar tab")
                        time.sleep(3)  # Wait for calendar to load
                        return True

                except TimeoutException:
                    print(f"❌ Selector {i} timed out")
                    continue
                except Exception as e:
                    print(f"❌ Selector {i} failed: {e}")
                    continue

            print("❌ Could not find calendar tab with any selector")
            return False

        except Exception as e:
            print(f"❌ Error clicking calendar tab: {e}")
            return False

    def extract_calendar_data_from_current_page(self):
        """Extract all visible calendar data from the current page."""
        try:
            print("📋 Extracting visible calendar data...")

            # Get current week dates
            today = datetime.now().date()
            current_week_start = today - timedelta(days=today.weekday())
            current_week_end = current_week_start + timedelta(days=6)
            print(
                f"📅 Current week: {current_week_start} to {current_week_end}")

            calendar_data = {
                "nutrition_entries": [],
                "walking_entries": [],
                "weight_entries": [],
                "workout_entries": [],
                "daily_summary": {}
            }

            # First expand all "+More" buttons to reveal hidden entries
            clicked_buttons = set()
            total_buttons_clicked = 0
            max_attempts = 3

            for attempt in range(max_attempts):
                print(f"🔍 Pass {attempt + 1}: Looking for '+More' buttons...")

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
                            print(
                                f"⏭️ Skipping already clicked button: {button_text}")
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
                        print(f"⚠️ Error clicking '+More' button: {e}")
                        continue

                if clicked_in_this_pass == 0:
                    print(
                        f"✅ No new buttons clicked in pass {attempt}, stopping")
                    break

                time.sleep(2)  # Wait for new content to load

            print(f"✅ Expanded {total_buttons_clicked} '+More' buttons")

            # Now look for nutrition entries
            print("🔍 Scanning for nutrition entries...")
            nutrition_patterns = [
                "//*[contains(text(), 'Cals') and contains(text(), '/') and contains(text(), 'Meal')]",
                "//*[contains(text(), 'cal') and contains(text(), '/') and contains(text(), 'Meal')]"
            ]

            found_entries = False
            for pattern in nutrition_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if 'Cals' in text and 'Meal' in text and len(text) < 100:
                                # Try to find the day this belongs to
                                day_info = self.find_day_for_element(element)
                                if day_info != "Unknown":
                                    found_entries = True
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

            if not found_entries:
                print("ℹ️ No nutrition entries found for the current week")

            # Look for walking entries
            print("🔍 Scanning for walking entries...")
            walking_patterns = [
                "//*[contains(text(), 'Walking') and not(contains(text(), 'Program'))]",
                "//div[contains(@data-rbd-droppable-id, '')]//div[contains(text(), 'Walking')]"
            ]

            found_walking = False
            for pattern in walking_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if 'Walking' in text and len(text) < 100:
                                day_info = self.find_day_for_element(element)
                                if day_info != "Unknown":
                                    found_walking = True
                                    status = self.check_activity_status(
                                        element)
                                entry = {
                                    "type": "walking",
                                    "text": text,
                                    "day": day_info,
                                    "status": status,
                                    "element_location": element.location
                                }
                                calendar_data["walking_entries"].append(
                                    entry)
                                print(
                                    f"🚶 Found walking: {text} ({status}) (Day: {day_info})")
                except Exception as e:
                    print(f"⚠️ Error finding walking with pattern: {e}")
                    continue

            if not found_walking:
                print("ℹ️ No walking entries found for the current week")

            return calendar_data

        except Exception as e:
            print(f"❌ Error extracting calendar data: {e}")
            return {
                "nutrition_entries": [],
                "walking_entries": [],
                "weight_entries": [],
                "workout_entries": [],
                "daily_summary": {}
            }

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
                    By.XPATH, "//*[contains(text(), '+ ') and contains(text(), 'More')]")

                if not more_buttons:
                    print("ℹ️ No more '+More' buttons found")
                    break

                for button in more_buttons:
                    try:
                        # Get button text and location for tracking
                        button_text = button.text
                        button_location = button.location

                        # Create a unique identifier for this button
                        button_id = f"{button_text}_{button_location['x']}_{button_location['y']}"

                        if button_id in clicked_buttons:
                            print(
                                f"⏭️ Skipping already clicked button: {button_text}")
                            continue

                        # Scroll button into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)

                        # Try to click the button
                        button.click()
                        clicked_buttons.add(button_id)
                        total_buttons_clicked += 1
                        print(f"✅ Clicked '+More' button: {button_text}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Error processing button: {e}")
                        continue

            print(
                f"✅ Completed expanding buttons. Total clicked: {total_buttons_clicked}")
            return total_buttons_clicked

        except Exception as e:
            print(f"❌ Error expanding buttons: {e}")
            return 0

    def analyze_detailed_nutrition_entries_integrated(self, nutrition_entries):
        """Analyze detailed nutrition entries by clicking into them and extracting meal information."""
        try:
            print(
                f"🍎 Starting detailed analysis of {len(nutrition_entries)} nutrition entries...")
            detailed_meals = []

            for i, entry in enumerate(nutrition_entries, 1):
                try:
                    print(
                        f"\n🍎 === Analyzing nutrition entry {i}/{len(nutrition_entries)} ===")
                    entry_text = entry.get("text", f"Entry {i}")
                    print(f"📊 Entry: {entry_text}")

                    # Get the clickable element
                    element = entry.get("element")
                    if not element:
                        print("⚠️ No element found for this entry")
                        continue

                    # Try to click on the nutrition entry
                    print(f"🖱️ Attempting to click nutrition entry...")

                    # Scroll element into view
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)

                    # Try different click methods
                    click_successful = False

                    # Method 1: Regular click
                    try:
                        element.click()
                        click_successful = True
                        print(f"✅ Regular click successful")
                    except Exception as e1:
                        print(f"⚠️ Regular click failed: {e1}")

                        # Method 2: JavaScript click
                        try:
                            self.driver.execute_script(
                                "arguments[0].click();", element)
                            click_successful = True
                            print(f"✅ JavaScript click successful")
                        except Exception as e2:
                            print(f"⚠️ JavaScript click failed: {e2}")

                    if click_successful:
                        print(f"✅ Successfully clicked nutrition entry")
                        time.sleep(4)  # Wait for details to load

                        # Extract detailed meal information
                        meal_info = self.extract_detailed_meal_info()
                        if meal_info and meal_info.get("foods_by_meal"):
                            detailed_meals.append({
                                "entry_text": entry_text,
                                "day": entry.get("day", "Unknown"),
                                "meal_details": meal_info
                            })
                            print(
                                f"✅ Extracted detailed meal info for {entry_text}")
                        else:
                            print(
                                f"⚠️ Could not extract detailed meal info for {entry_text}")

                        # Close the popup
                        self.close_nutrition_popup()

                    else:
                        print(f"❌ Could not click nutrition entry {i}")

                except Exception as e:
                    print(f"❌ Error analyzing nutrition entry {i}: {e}")
                    # Try to close any open popups
                    self.close_nutrition_popup()
                    continue

            print(
                f"✅ Detailed nutrition analysis complete. Extracted {len(detailed_meals)} detailed meal entries")
            return detailed_meals

        except Exception as e:
            print(f"❌ Error in detailed nutrition analysis: {e}")
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
            time.sleep(2)

            # STEP 1: Enhanced scrolling within the popup to see all content
            print("📜 Scrolling within popup to see all meal details...")
            try:
                # Try multiple strategies to find the scrollable container
                popup_containers = [
                    "//div[contains(@class, 'modal')]",
                    "//div[contains(@class, 'popup')]",
                    "//div[contains(@class, 'dialog')]",
                    "//div[contains(@role, 'dialog')]",
                    "//div[contains(@class, 'overlay')]",
                    "//div[contains(@class, 'meal-details')]",
                    "//div[contains(@class, 'nutrition-popup')]",
                    "//div[contains(@class, 'scroll')]",
                ]

                popup_container = None
                scrollable_area = None

                # First, try to find the main popup container
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
                    except Exception as e:  # Added except clause
                        print(f"Error finding popup container: {e}")
                        continue

                # Try to find the specific scrollable area within the popup (left side with meals)
                if popup_container:
                    scrollable_selectors = [
                        ".//div[contains(@class, 'scroll')]",
                        ".//div[contains(@class, 'meal')]",
                        ".//div[contains(@class, 'content')]",
                        ".//div[contains(@class, 'left')]",
                        ".//div[contains(@class, 'details')]",
                    ]

                    for scroll_selector in scrollable_selectors:
                        try:
                            scroll_areas = popup_container.find_elements(
                                By.XPATH, scroll_selector)
                            for area in scroll_areas:
                                if area.is_displayed() and area.size['height'] > 200:
                                    scrollable_area = area
                                    print(
                                        f"✅ Found scrollable area: {scroll_selector}")
                                    break
                            if scrollable_area:
                                break
                        except Exception as e:  # Added except clause
                            print(f"Error finding scrollable area: {e}")
                            continue

                if scrollable_area:
                    # Scroll by a fixed amount repeatedly until no more scroll
                    last_scroll_height = self.driver.execute_script(
                        "return arguments[0].scrollHeight", scrollable_area)
                    while True:
                            self.driver.execute_script(
                            "arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_area)
                    time.sleep(1)  # Give time for content to load
                    new_scroll_height = self.driver.execute_script(
                            "return arguments[0].scrollHeight", scrollable_area)
                        if new_scroll_height == last_scroll_height:
                            break
                        last_scroll_height = new_scroll_height
                    print("✅ Finished scrolling within popup.")
                else:
                    print("⚠️ Could not find a scrollable area in the popup.")

            except Exception as e:
                print(f"❌ Error during initial popup scrolling setup: {e}")

            # ... (rest of extract_detailed_meal_info logic)
            # The remaining part of this function is not shown in the error context
            # but would typically extract date, total calories, meals, macros, foods by meal
            # from the now fully loaded popup content.
            # For example, using WebDriverWait and By.XPATH to find elements like:

            try:
                # Date
                date_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class, 'modal-header')]//span[contains(@class, 'date')]"))
                )
                meal_info["date"] = date_element.text.strip()
                print(f"📅 Extracted date: {meal_info['date']}")
            except Exception as e:
                print(f"⚠️ Could not extract date from nutrition popup: {e}")

            try:
                # Total Calories
                total_calories_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class, 'total-calories')]//span[contains(@class, 'value')]"))
                )
                meal_info["total_calories"] = total_calories_element.text.strip()
                                        print(
                    f"🔥 Extracted total calories: {meal_info['total_calories']}")
            except Exception as e:
                                            print(
                    f"⚠️ Could not extract total calories from nutrition popup: {e}")

            try:
                # Macros (e.g., protein, carbs, fat)
                macro_elements = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'macros')]//div[contains(@class, 'macro-item')]"))
                )
                for macro_elem in macro_elements:
                    name = macro_elem.find_element(
                        By.XPATH, ".//span[contains(@class, 'name')]").text.strip()
                    value = macro_elem.find_element(
                        By.XPATH, ".//span[contains(@class, 'value')]").text.strip()
                    meal_info["macros"][name] = value
                print(f"📊 Extracted macros: {meal_info['macros']}")
            except Exception as e:
                print(f"⚠️ Could not extract macros from nutrition popup: {e}")

            try:
                # Meals and Foods by Meal
                meal_sections = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class, 'meal-section')]"))
                )
                for meal_section in meal_sections:
                    meal_name = meal_section.find_element(
                        By.XPATH, ".//h4[contains(@class, 'meal-name')]").text.strip()
                    meal_info["meals"][meal_name] = []
                    meal_info["foods_by_meal"][meal_name] = []

                    food_items = meal_section.find_elements(
                        By.XPATH, ".//div[contains(@class, 'food-item')]")
                    for food_item in food_items:
                        food_name = food_item.find_element(
                            By.XPATH, ".//span[contains(@class, 'food-name')]").text.strip()
                        food_calories = food_item.find_element(
                            By.XPATH, ".//span[contains(@class, 'food-calories')]").text.strip()
                        meal_info["meals"][meal_name].append(
                            f"{food_name} ({food_calories})")
                        meal_info["foods_by_meal"][meal_name].append(
                            {"name": food_name, "calories": food_calories})
                                                                    print(
                    f"🍽️ Extracted meals and foods: {meal_info['foods_by_meal']}")
                                        except Exception as e:
                                            print(
                    f"⚠️ Could not extract meals/foods from nutrition popup: {e}")

            return meal_info

        except Exception as e:
            print(f"❌ Error extracting detailed meal info: {e}")
            return {}

    def close_nutrition_popup(self):
        """Closes the nutrition detail popup."""
        try:
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'close-button')] | //div[contains(@class, 'modal-header')]//button"))
            )
            close_button.click()
            print("✅ Closed nutrition popup.")
            time.sleep(2)  # Give time for the popup to disappear
        except TimeoutException:
            print("⚠️ Timeout waiting for nutrition popup close button.")
        except NoSuchElementException:
            print("⚠️ Nutrition popup close button not found (might already be closed).")
        except Exception as e:
            print(f"❌ Error closing nutrition popup: {e}")

    def organize_data_by_day(self, calendar_data):
        """Organizes calendar data entries into a dictionary by day for easier access."""
        organized_data = {
            "Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [],
            "Friday": [], "Saturday": [], "Sunday": []
        }

        all_entries = (
            calendar_data.get("nutrition_entries", []) +
            calendar_data.get("walking_entries", []) +
            calendar_data.get("weight_entries", []) +
            calendar_data.get("workout_entries", [])
        )

        for entry in all_entries:
            day = entry.get("day")
            if day and day in organized_data:
                organized_data[day].append(entry)

        return organized_data

    def take_current_week_screenshot(self):
        """Takes a screenshot of the current week's calendar view."""
        screenshot_path = os.path.join(tempfile.gettempdir(
        ), f"calendar_week_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        try:
            calendar_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'calendar-week')] | //div[contains(@class, 'fc-view-container')]"))
            )
            calendar_element.screenshot(screenshot_path)
            print(f"✅ Screenshot saved to {screenshot_path}")
            return screenshot_path
        except TimeoutException:
            print("⚠️ Could not locate calendar element for screenshot.")
            return None
        except Exception as e:
            print(f"❌ Error taking calendar screenshot: {e}")
            return None

    def find_day_for_element(self, element):
        """Improved: Finds the day (e.g., 'Monday 10') for a given element within the calendar view.
           It now correctly uses import re and handles potential errors better."""
        try:
            # Traverse up the DOM to find a parent element that indicates the day
            parent = element
            for _ in range(10):  # Limit traversal depth
                try:
                    parent_text = parent.text.strip()
                    if parent_text:
                        # Extract the day and date
                        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                        if day in parent_text:
                                # Try to find the date number
                                import re
                                date_match = re.search(r'\d+', parent_text)
                                if date_match:
                                    date_num = date_match.group()
                                    return f"{day} {date_num}"
                            return day
                    parent = parent.find_element(By.XPATH, "..")
                except Exception as e:  # Catch specific exceptions during traversal
                    print(f"Error traversing parents for day: {e}")
                    break

            # If we couldn't find it in parents, try looking at nearby elements
            try:
                # Look for day elements near the current element
                nearby_elements = self.driver.find_elements(
                    By.XPATH, "//*[contains(@class, 'day') or contains(@class, 'date')]")
                for nearby_elem in nearby_elements:
                    if nearby_elem.is_displayed():
                        text = nearby_elem.text.strip()
                            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                                if day in text:
                                    # Try to find the date number
                    import re
                                    date_match = re.search(r'\d+', text)
                                    if date_match:
                                        date_num = date_match.group()
                                        return f"{day} {date_num}"
                                    return day
            except Exception as e:  # Catch specific exceptions here
                print(f"Error finding day from nearby elements: {e}")

            return "Unknown"
        except Exception as e:
            print(f"An unexpected error occurred in find_day_for_element: {e}")
            return "Unknown"

    def check_activity_status(self, element):
        """Check if an activity is completed or planned based on visual indicators."""
        try:
            # Look for checkmarks or completion indicators
            parent = element.find_element(By.XPATH, "./..")
            parent_html = parent.get_attribute('outerHTML')

            # Look for completion indicators
            if any(indicator in parent_html.lower() for indicator in ['check', 'complete', 'done', '✓']):
                return "completed"
            elif any(indicator in parent_html.lower() for indicator in ['circle', 'empty', 'planned']):
                return "planned"
            else:
                return "unknown"

        except:
            return "unknown"

    def analyze_calendar_with_gemini(self, screenshot_path, gemini_api_key):
        """Analyze calendar screenshot with Gemini AI."""
        try:
            if not gemini_api_key:
                return "Gemini API key not provided"

            print("🤖 Analyzing calendar with Gemini AI...")

            # Configure Gemini
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel(
                'gemini-2.0-flash-thinking-exp-01-21')

            # Encode image
            base64_image = self.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt = """
            Analyze this fitness calendar screenshot and provide insights about:
            1. Nutrition tracking patterns and consistency
            2. Walking/exercise activities completed vs planned
            3. Weight tracking entries
            4. Overall weekly activity summary
            5. Any patterns or trends you notice

            Focus on providing actionable insights for fitness coaching.
            """

            prompt_parts = [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            response = model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000)
            )

            return response.text

        except Exception as e:
            print(f"❌ Error analyzing calendar with Gemini: {e}")
            return f"Error analyzing calendar: {e}"

    def _convert_calendar_data_to_checkin_format(self, calendar_data, ai_analysis=""):
        """Convert calendar data to checkin format."""
        try:
            if not calendar_data:
                return self._get_default_calendar_results()

            # Ensure calendar_data is a dictionary
            if isinstance(calendar_data, list):
                calendar_data = {
                    "nutrition_entries": calendar_data,
                    "walking_entries": [],
                    "weight_entries": [],
                    "workout_entries": [],
                    "daily_summary": {}
                }

            # Process nutrition data
            nutrition_results = self._process_nutrition_data(
                calendar_data.get("nutrition_entries", []), ai_analysis)

            # Process weight data
            weight_results = self._process_weight_data(
                calendar_data.get("weight_entries", []), ai_analysis)

            # Process walking data
            walking_results = self._process_walking_data(
                calendar_data.get("walking_entries", []), ai_analysis)

            # If no entries found for current week, return appropriate message
            if (not calendar_data.get("nutrition_entries") and
                not calendar_data.get("weight_entries") and
                    not calendar_data.get("walking_entries")):
                return {
                    "nutrition_analysis_results": {
                        "calories_protein": {
                            "availability": "none",
                            "structured_data": {},
                            "analysis_text": "No data recorded for the current week."
                        },
                        "fats_carbs": {
                            "availability": "none",
                            "structured_data": {},
                            "analysis_text": "No data recorded for the current week."
                        }
                    },
                    "bodyweight_availability": "none",
                    "bodyweight_structured_data": {},
                    "bodyweight_analysis_text": "No data recorded for the current week.",
                    "sleep_availability": "none",
                    "sleep_analysis_text": "No data recorded for the current week.",
                    "average_sleep_hours": "Not Recorded",
                    "steps_availability": "none",
                    "steps_structured_data": {},
                    "steps_analysis_text": "No data recorded for the current week."
                }

            return {
                "nutrition_analysis_results": nutrition_results,
                "bodyweight_availability": weight_results["availability"],
                "bodyweight_structured_data": weight_results["structured_data"],
                "bodyweight_analysis_text": weight_results["analysis_text"],
                "sleep_availability": "none",  # These are handled separately
                "sleep_analysis_text": "No data recorded for the current week.",
                "average_sleep_hours": "Not Recorded",
                "steps_availability": walking_results["availability"],
                "steps_structured_data": walking_results["structured_data"],
                "steps_analysis_text": walking_results["analysis_text"]
            }

        except Exception as e:
            print(f"❌ Error converting calendar data: {e}")
            return self._get_default_calendar_results()

    def _get_default_calendar_results(self):
        """Return default results when calendar analysis fails."""
        return {
            "nutrition_analysis_results": {
                "calories_protein": {
                    "availability": "none",
                    "structured_data": {},
                    "analysis_text": "No nutrition data recorded for the current week."
                },
                "fats_carbs": {
                    "availability": "none",
                    "structured_data": {},
                    "analysis_text": "No nutrition data recorded for the current week."
                }
            },
            "bodyweight_availability": "none",
            "bodyweight_structured_data": {},
            "bodyweight_analysis_text": "No bodyweight data recorded for the current week.",
            "steps_availability": "none",
            "steps_structured_data": {},
            "steps_analysis_text": "No steps data recorded for the current week.",
            "sleep_availability": "none",
            "sleep_analysis_text": "No sleep data recorded for the current week.",
            "average_sleep_hours": "Not Recorded"
        }

    def _process_nutrition_data(self, nutrition_entries, ai_analysis):
        """Process nutrition entries and convert to expected format."""
        try:
            if not nutrition_entries:
                return {
                    "calories_protein": {
                        "availability": "none",
                        "structured_data": {},
                        "analysis_text": "No nutrition data recorded for the current week."
                    },
                    "fats_carbs": {
                        "availability": "none",
                        "structured_data": {},
                        "analysis_text": "No nutrition data recorded for the current week."
                    }
                }

            # Extract calorie information from entries
            total_calories = 0
            total_meals = 0
            daily_entries = {}

            for entry in nutrition_entries:
                text = entry.get("text", "")
                day = entry.get("day", "Unknown")

                # Extract calories from text like "1442.78 Cals / 3 Meals"
                import re
                cal_match = re.search(r'(\d+\.?\d*)\s*Cals?', text)
                meal_match = re.search(r'(\d+)\s*Meals?', text)

                if cal_match:
                    calories = float(cal_match.group(1))
                    total_calories += calories

                if meal_match:
                    meals = int(meal_match.group(1))
                    total_meals += meals

                if day not in daily_entries:
                    daily_entries[day] = []
                daily_entries[day].append(text)

            # Determine availability based on data quality
            if len(nutrition_entries) >= 5:  # Good data for most days
                availability = "substantial"
            elif len(nutrition_entries) >= 2:  # Some data
                availability = "minimal"
            else:
                availability = "none"

            avg_calories = int(
                total_calories / len(nutrition_entries)) if nutrition_entries else 0

            analysis_text = f"Calendar shows {len(nutrition_entries)} nutrition entries. "
            if avg_calories > 0:
                analysis_text += f"Average daily calories: {avg_calories}. "
            analysis_text += f"Total meals tracked: {total_meals}."

            return {
                "calories_protein": {
                    "availability": availability,
                    "structured_data": {
                        "CALORIES_DAILY": str(avg_calories),
                        "PROTEIN_DAILY": "not visible"  # Calendar view doesn't show protein breakdown
                    },
                    "analysis_text": analysis_text
                },
                "fats_carbs": {
                    "availability": availability,
                    "structured_data": {
                        "FATS_DAILY": "not visible",
                        "CARBS_DAILY": "not visible"
                    },
                    "analysis_text": analysis_text
                }
            }

        except Exception as e:
            print(f"❌ Error processing nutrition data: {e}")
            return {
                "calories_protein": {
                    "availability": "error",
                    "structured_data": {},
                    "analysis_text": f"Error processing nutrition data: {e}"
                },
                "fats_carbs": {
                    "availability": "error",
                    "structured_data": {},
                    "analysis_text": f"Error processing nutrition data: {e}"
                }
            }

    def _process_weight_data(self, weight_entries, ai_analysis):
        """Process weight entries and convert to expected format."""
        try:
            if not weight_entries:
                return "none", {}, "No bodyweight data recorded for the current week."

            # Extract weight values from entries
            weights = []
            dates = []

            for entry in weight_entries:
                text = entry.get("text", "")
                day = entry.get("day", "Unknown")

                # Extract weight from text like "Weight 85.2 kg"
                import re
                weight_match = re.search(r'(\d+\.?\d*)\s*kg', text)
                if weight_match:
                    weight = float(weight_match.group(1))
                    weights.append(weight)
                    dates.append(day)

            if not weights:
                return "minimal", {}, "Weight entries found but values not extractable."

            # Determine trend
            if len(weights) >= 2:
                if weights[-1] < weights[0]:
                    trend = "downward"
                elif weights[-1] > weights[0]:
                    trend = "upward"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            availability = "substantial" if len(weights) >= 3 else "minimal"

            structured_data = {
                "STARTING_WEIGHT": str(weights[0]) if weights else "not visible",
                "CURRENT_WEIGHT": str(weights[-1]) if weights else "not visible",
                "TREND": trend,
                "STARTING_DATE": dates[0] if dates else "not visible",
                "CURRENT_DATE": dates[-1] if dates else "not visible"
            }

            analysis_text = f"Found {len(weight_entries)} weight entries. "
            if weights:
                analysis_text += f"Weight range: {min(weights):.1f}kg - {max(weights):.1f}kg. "
                analysis_text += f"Trend: {trend}."

            return availability, structured_data, analysis_text

        except Exception as e:
            print(f"❌ Error processing weight data: {e}")
            return "error", {}, f"Error processing weight data: {e}"

    def _process_walking_data(self, walking_entries, ai_analysis):
        """Process walking entries and convert to expected format."""
        try:
            if not walking_entries:
                return "none", {}, "No steps data recorded for the current week."

            completed_walks = [
                e for e in walking_entries if e.get("status") == "completed"]
            planned_walks = [
                e for e in walking_entries if e.get("status") == "planned"]

            # Determine availability based on data
            if len(walking_entries) >= 5:
                availability = "substantial"
            elif len(walking_entries) >= 2:
                availability = "minimal"
            else:
                availability = "none"

            # Estimate steps (rough approximation)
            if completed_walks:
                estimated_steps = len(completed_walks) * 3000  # Rough estimate
                avg_steps = f"~{estimated_steps:,} (estimated from {len(completed_walks)} walks)"
            else:
                avg_steps = "Inconsistent Tracking"

            structured_data = {
                "AVERAGE_STEPS": avg_steps,
                "HIGHEST_STEPS": "not visible",
                "TREND": "upward" if len(completed_walks) > len(planned_walks) else "stable"
            }

            analysis_text = f"Found {len(walking_entries)} walking activities. "
            analysis_text += f"Completed: {len(completed_walks)}, Planned: {len(planned_walks)}."

            return availability, structured_data, analysis_text

        except Exception as e:
            print(f"❌ Error processing walking data: {e}")
            return "error", {}, f"Error processing walking data: {e}"

    def analyze_nutrition_graph(self):
        """Analyze nutrition graphs - placeholder for compatibility."""
        return {
            'calories_protein': {
                'availability': 'none',
                'structured_data': {},
                'analysis_text': 'Nutrition analysis handled by calendar data.'
            },
            'fats_carbs': {
                'availability': 'none',
                'structured_data': {},
                'analysis_text': 'Nutrition analysis handled by calendar data.'
            }
        }

    def analyze_sleep_graph(self):
        """Analyze sleep graphs - placeholder for compatibility."""
        return "none", "No sleep data recorded for the current week.", "Not Recorded"

    def analyze_steps_graph(self):
        """Analyze steps graphs - placeholder for compatibility."""
        return "none", {}, "Steps analysis handled by calendar data."

    def analyze_progress_photos(self):
        """Analyze progress photos."""
        try:
            logging.info("Analyzing progress photos...")
            if not self.click_progress_photos_tab():
                return "No progress photos data available for analysis."

            time.sleep(3)
            screenshot_path = "progress_photos.png"
            self.driver.save_screenshot(screenshot_path)

            if self.model:
                base64_image = self.encode_image(screenshot_path)
                if base64_image:
                    prompt = """
                    Analyze this progress photos page and determine if the client has up-to-date photos.
                    Look for recent photos and provide a brief assessment of photo consistency.
                    """

                    prompt_parts = [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {
                                "mime_type": "image/png", "data": base64_image}}
                        ]
                    }]

                    response = self.model.generate_content(
                        contents=prompt_parts,
                        generation_config=genai.GenerationConfig(
                            max_output_tokens=1000)
                    )
                    return response.text

            return "Progress photos section accessed but analysis not available."

        except Exception as e:
            logging.exception(f"Error analyzing progress photos: {e}")
            return f"Error analyzing progress photos: {e}"

    def click_review_by_workout(self):
        """Click the 'Review by Workout' button."""
        try:
            logging.info("Attempting to click 'Review by Workout' button...")
            review_button_locator = (
                By.XPATH, "//a[contains(text(), 'Review by Workout')]")
            review_button = self.wait.until(
                EC.element_to_be_clickable(review_button_locator))
            # Scroll to the button to make sure it's in view
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", review_button)
            time.sleep(1)
            review_button.click()
            logging.info("Successfully clicked 'Review by Workout' button.")
            # Add a longer wait here for the workout page to load
            time.sleep(5)
            return True
        except (TimeoutException, NoSuchElementException):
            logging.error("'Review by Workout' button not found.")
            return False
        except Exception as e:
            logging.exception(
                f"Error clicking 'Review by Workout' button: {e}")
            return False

    def process_workouts(self):
        """
        Process workout data from the Progress tab by iterating through pages
        and analyzing each workout's details from its modal.
        """
        try:
            logging.info("💪 Starting comprehensive workout processing...")

            if not self.click_review_by_workout():
                logging.error(
                    "Could not navigate to the 'Review by Workout' page. Aborting workout processing.")
                return []

            workout_data_list = []
            page_number = 1

            while True:
                logging.info(f"--- Processing workout page {page_number} ---")

                try:
                    workout_cards_xpath = "//div[contains(@class, 'p-4') and .//div[contains(@class, 'text-sm font-medium')]]"
                    workout_elements = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, workout_cards_xpath))
                    )
                    logging.info(
                        f"Found {len(workout_elements)} workout cards on page {page_number}.")
                except TimeoutException:
                    logging.info(
                        "No more workout cards found on this page. Concluding workout processing.")
                    break

                if not workout_elements:
                    logging.info("No workouts found on the page.")
                    break

                workout_details_to_process = []
                for element in workout_elements:
                    try:
                        workout_name = element.find_element(
                            By.XPATH, ".//div[contains(@class, 'text-sm font-medium')]").text
                        date_str = element.find_element(
                            By.XPATH, ".//div[contains(@class, 'text-xs')]").text
                        workout_details_to_process.append(
                            (workout_name, date_str))
                    except StaleElementReferenceException:
                        logging.warning(
                            "StaleElementReferenceException while gathering workout details. Will re-fetch elements.")
                        break  # Break inner loop to re-fetch elements
                    except Exception as e:
                        logging.error(
                            f"Error gathering details for a workout card: {e}")
                
                if len(workout_details_to_process) != len(workout_elements):
                    logging.info(
                        "Stale elements detected, re-processing page.")
                    continue

                for name, date in workout_details_to_process:
                    try:
                        workout_data = self.analyze_workout_details_stripped(
                            name, date)
                        if workout_data:
                            workout_data_list.append(workout_data)
                            logging.info(
                                f"✅ Successfully processed and stored: {name} on {date}")
                    except Exception as e:
                        logging.error(
                            f"Error processing workout '{name}' on '{date}': {e}", exc_info=True)

                try:
                    next_button = self.driver.find_element(
                        By.XPATH, "//button[contains(., 'Next')]")
                    if 'disabled' in next_button.get_attribute('class'):
                        logging.info(
                            "Next button is disabled. Reached the last page.")
                        break
                    
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView();", next_button)
                    time.sleep(1)
                    next_button.click()
                    logging.info("Navigated to the next page.")
                    page_number += 1
                    time.sleep(2)
                except NoSuchElementException:
                    logging.info(
                        "No 'Next' button found. Reached the last page.")
                    break
                except Exception as e:
                    logging.error(f"Error clicking 'Next' button: {e}")
                    break

            logging.info(
                f"[PASS] Processed a total of {len(workout_data_list)} workouts across all pages.")
            return workout_data_list

        except Exception as e:
            logging.exception(
                f"❌ An unexpected error occurred during the main workout processing loop: {e}")
            return []  # Return empty list on major failure

    def analyze_workout_details_stripped(self, workout_name, date_str):
        """
        Analyzes the details of a specific workout by clicking on it and parsing the exercises.
        This version is stripped down for the check-in script to only use the base implementation.
        """
        # This method now directly calls the base implementation.
        return self.analyze_workout_details_stripped_base(workout_name, date_str)

    def generate_personalized_message(self, client_name, workouts_this_week, most_improved_exercise_data):
        """Generate a personalized message for the client."""
        try:
            first_name = client_name.split()[0]

            if workouts_this_week >= 3:
                base_message = f"Great work this week, {first_name}! You completed {workouts_this_week} workouts."
            elif workouts_this_week >= 1:
                base_message = f"Good effort this week, {first_name}! You completed {workouts_this_week} workout(s)."
            else:
                base_message = f"Let's get back on track next week, {first_name}!"

            if most_improved_exercise_data and most_improved_exercise_data.get('name') != 'N/A':
                exercise_name = most_improved_exercise_data['name']
                improvement = most_improved_exercise_data.get(
                    'improvement_highlight', '')
                base_message += f" Your {exercise_name} showed {improvement}"

            return base_message

        except Exception as e:
            logging.exception(f"Error generating personalized message: {e}")
            return f"Keep up the great work, {client_name.split()[0]}!"

    def navigate_back_to_clients_list(self):
        """Navigates back to the clients list from a client's profile."""
        try:
            logging.info("Navigating back to clients list...")
            # This XPath assumes there's a link/button with text "Clients"
            # It might need adjustment based on the actual UI
            back_to_clients_link = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(), 'Clients')]"))
            )
            back_to_clients_link.click()
            logging.info("Successfully navigated back to clients list.")
            return True
        except Exception as e:
            logging.exception("Could not navigate back to clients list.")
            return False

    def cleanup(self):
        """Clean up resources."""
        try:
            logging.info("Cleaning up resources...")
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                logging.info("Browser closed successfully")

            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
                logging.info("Temporary user data directory cleaned up")

        except Exception as e:
            logging.exception(f"Error during cleanup: {e}")

    @staticmethod
    def encode_image(image_path):
        """Encode image to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logging.exception(f"Error encoding image {image_path}: {e}")
            return None

    def is_element_stale(self, element):
        """Check if an element is stale."""
        try:
            element.is_enabled()
            return False
        except StaleElementReferenceException:
            return True

    def calculate_workout_stats_for_date_range(self, workout_data_list, start_date, end_date, target_exercises=None):
        """Calculates workout statistics for a given date range."""
        try:
            total_workouts = 0
            workout_names = []
            total_weight = 0
            total_reps = 0
            total_sets = 0
            workout_data = []
            exercise_workload = {}

            for workout in workout_data_list:
                try:
                    # Parse workout date
                    workout_date = None
                    date_str = workout.get('date', '')

                    try:
                        if '-' in date_str:
                            workout_date = datetime.strptime(
                                date_str, '%Y-%m-%d').date()
                        else:
                            workout_date = datetime.strptime(
                                date_str, '%d %b %Y').date()
                    except:
                        continue

                    # Check if workout is in date range
                    if start_date <= workout_date <= end_date:
                        total_workouts += 1
                        workout_names.append(
                            workout.get('workout_type', 'Unknown'))
                        workout_data.append(workout)

                        # Process exercises
                        for exercise in workout.get('exercises', []):
                            exercise_name = exercise.get('name', '')

                            for set_data in exercise.get('sets', []):
                                weight = set_data.get('weight', 0)
                                reps = set_data.get('reps', 0)

                                total_weight += weight * reps
                                total_reps += reps
                                total_sets += 1

                                # Track exercise workload
                                if target_exercises is None or exercise_name in target_exercises:
                                    if exercise_name not in exercise_workload:
                                        exercise_workload[exercise_name] = 0
                                    exercise_workload[exercise_name] += weight * reps

                except Exception as e:
                    logging.warning(
                        f"Error processing workout in date range calculation: {e}")
                    continue

            return total_workouts, workout_names, total_weight, total_reps, total_sets, workout_data, exercise_workload

        except Exception as e:
            logging.exception(f"Error calculating workout stats: {e}")
            return 0, [], 0, 0, 0, [], {}


def analyze_workout_details_stripped_base(self, workout_name, date_str):
    """
    Base implementation for analyzing workout details.
    This function is now part of the TrainerizeAutomation class.
    """
    from datetime import datetime
    import re
    import time
    logging.info(
        f"Analyzing workout details for '{workout_name}' on {date_str}")
    workout_data = {
        "workout_type": workout_name,
        "date": None,
        "exercises": []
    }

    try:
        # Re-format date from "01 Jan 2024" to "2024-01-01"
        try:
            dt_object = datetime.strptime(date_str, '%d %b %Y')
            workout_data['date'] = dt_object.strftime('%Y-%m-%d')
        except ValueError:
            logging.warning(
                f"Could not parse date '{date_str}'. Using original.")
            workout_data['date'] = date_str

        # Find and click the workout card to open the details modal
        # This is a complex XPath to find the right card based on workout name and date
        try:
            workout_card_xpath = f"//div[contains(@class, 'p-4') and .//div[contains(., '{workout_name}')] and .//div[contains(., '{date_str}')]]"
            workout_card = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, workout_card_xpath))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", workout_card)
            time.sleep(1)  # Brief pause after scrolling
            workout_card.click()
            logging.info(f"Clicked workout card for '{workout_name}'")
        except TimeoutException:
            logging.error(
                f"Could not find or click workout card for '{workout_name}' on {date_str}.")
            return None

        # Wait for the modal to appear
        modal_xpath = "//div[contains(@class, 'ReactModal__Content')]"
        try:
            modal = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, modal_xpath))
            )
            logging.info("Workout details modal is visible.")
        except TimeoutException:
            logging.error("Workout details modal did not appear.")
            return None

        # Inside the modal, find all exercise tables
        exercise_tables_xpath = ".//div[contains(@class, 'mb-4') and .//table]"
        try:
            exercise_tables = modal.find_elements(
                By.XPATH, exercise_tables_xpath)
            logging.info(f"Found {len(exercise_tables)} exercise tables.")
        except NoSuchElementException:
            logging.warning("No exercise tables found in the modal.")
            exercise_tables = []

        for table in exercise_tables:
            try:
                # Get exercise name from the h3 tag above the table
                exercise_name = table.find_element(
                    By.XPATH, ".//h3").text.strip()
                exercise_data = {
                    "name": exercise_name,
                    "sets": []
                }

                # Get all rows from the table body
                rows = table.find_elements(By.XPATH, ".//tbody/tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 3:  # Expecting Set, Reps, Weight
                        try:
                            reps = int(cols[1].text.strip())
                            weight_text = cols[2].text.strip().lower()
                            # Handle "bodyweight" or other non-numeric weights
                            if "body" in weight_text:
                                weight = 0  # Assuming 0 for bodyweight exercises
                            else:
                                # Clean up weight string (remove 'kg', etc.)
                                weight_val = re.findall(
                                    r"[-+]?\d*\.\d+|\d+", weight_text)
                                weight = float(
                                    weight_val[0]) if weight_val else 0

                            exercise_data["sets"].append(
                                {"reps": reps, "weight": weight})
                        except (ValueError, IndexError) as e:
                            logging.warning(
                                f"Could not parse row in '{exercise_name}': {e}. Row text: {[c.text for c in cols]}")

                if exercise_data["sets"]:
                    workout_data["exercises"].append(exercise_data)
            except Exception as e:
                logging.error(
                    f"Error processing an exercise table: {e}", exc_info=True)

        # Close the modal
        try:
            close_button_xpath = "//button[contains(@class, 'ReactModal__CloseButton')]"
            close_button = self.driver.find_element(
                By.XPATH, close_button_xpath)
            close_button.click()
            logging.info("Closed workout details modal.")
            # Wait for modal to disappear
            self.wait.until(
                EC.invisibility_of_element_located((By.XPATH, modal_xpath)))
        except Exception as e:
            logging.warning(
                f"Could not close modal: {e}. It might have auto-closed.")

        return workout_data if workout_data["exercises"] else None
    except Exception as e:
        logging.exception(
            f"An unexpected error occurred in analyze_workout_details_stripped_base for '{workout_name}': {e}")
        # Try to close modal on error to prevent being stuck
        try:
            self.driver.find_element(
                By.XPATH, "//button[contains(@class, 'ReactModal__CloseButton')]").click()
        except:
            pass
        return None


# Main execution function
def main():
    """Main execution function for client check-in analysis."""
    import os

    # Get API key from environment
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY environment variable not set!")
        return

    # Get credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    if not username or not password:
        print("❌ TRAINERIZE_USERNAME and TRAINERIZE_PASSWORD environment variables must be set!")
        return

    # Client to analyze
    client_name = "nicole lynch"
    if not client_name:
        print("❌ Client name is required!")
        return

    automation = None
    try:
        print(
            f"🚀 Starting comprehensive check-in analysis for {client_name}...")

        # Initialize automation
        automation = TrainerizeAutomation(openai_api_key=gemini_api_key)

        # Clean up previous files
        automation.cleanup_previous_files()

        # Login
        print("🔐 Logging in to Trainerize...")
        if not automation.login(username, password):
            print("❌ Login failed!")
            return

        # Navigate to client
        print(f"👤 Navigating to client: {client_name}")
        if not automation.navigate_to_client(client_name):
            print(f"❌ Could not navigate to client: {client_name}")
            return

        # === STEP 1: COMPREHENSIVE CALENDAR ANALYSIS ===
        print("\n📅 === STEP 1: COMPREHENSIVE CALENDAR ANALYSIS ===")
        calendar_results = automation.analyze_comprehensive_calendar_data(
            client_name, username, password, gemini_api_key)

        print("✅ Calendar analysis complete!")

        # === STEP 2: NAVIGATE TO PROGRESS TAB FOR WORKOUT ANALYSIS ===
        print("\n💪 === STEP 2: WORKOUT ANALYSIS ===")
        print("📊 Navigating to Progress tab for workout analysis...")

        # Click on Progress tab
        if not automation.click_progress_tab():
            print("❌ Could not navigate to Progress tab")
            workout_data_list = []
        else:
            print("✅ Successfully navigated to Progress tab")
            # Process workouts
            workout_data_list = automation.process_workouts()
            print(f"✅ Processed {len(workout_data_list)} workouts")

        # === STEP 3: ADDITIONAL ANALYSES ===
        print("\n📸 === STEP 3: ADDITIONAL ANALYSES ===")

        # Progress photos
        photos_analysis = automation.analyze_progress_photos()

        # Goals and weight goal
        print("🎯 Analyzing goals and weight targets...")
        if automation.navigate_to_goals_and_habits_tab():
            weight_goal_text = automation.get_current_weight_goal()
        else:
            weight_goal_text = "Could not access goals page"

        # === STEP 4: PREPARE FITNESS WRAPPED DATA ===
        print("\n📊 === STEP 4: PREPARING COMPREHENSIVE REPORT ===")

        fitness_wrapped_data = automation.prepare_fitness_wrapped_data(
            client_name=client_name,
            bodyweight_availability=calendar_results.get(
                "bodyweight_availability", "none"),
            bodyweight_structured_data=calendar_results.get(
                "bodyweight_structured_data", {}),
            bodyweight_analysis_text=calendar_results.get(
                "bodyweight_analysis_text", "No data"),
            nutrition_analysis_results=calendar_results.get(
                "nutrition_analysis_results", {}),
            sleep_availability=calendar_results.get(
                "sleep_availability", "none"),
            sleep_analysis_text=calendar_results.get(
                "sleep_analysis_text", "No data"),
            average_sleep_hours=calendar_results.get(
                "average_sleep_hours", "Not Recorded"),
            steps_availability=calendar_results.get(
                "steps_availability", "none"),
            steps_structured_data=calendar_results.get(
                "steps_structured_data", {}),
            steps_analysis_text=calendar_results.get(
                "steps_analysis_text", "No data"),
            photos_analysis=photos_analysis,
            weight_goal_text=weight_goal_text,
            weekly_summary_data={},
            workouts_completed_analysis="",
            total_workout_stats_analysis="",
            workout_data_list=workout_data_list
        )

        # === STEP 5: GENERATE REPORTS ===
        print("\n📄 === STEP 5: GENERATING REPORTS ===")

        # Save JSON data
        json_filename = automation.save_fitness_wrapped_data(
            client_name, fitness_wrapped_data)
        if json_filename:
            print(f"✅ JSON data saved: {json_filename}")

        # Generate PDF report
        pdf_filename, review_content = automation.generate_professional_checkin_review(
            client_name, fitness_wrapped_data)
        if pdf_filename:
            print(f"✅ PDF report generated: {pdf_filename}")

        print(f"\n🎉 === ANALYSIS COMPLETE FOR {client_name.upper()} ===")
        print(
            f"📊 Calendar data: {len(calendar_results.get('nutrition_analysis_results', {}).get('calories_protein', {}).get('structured_data', {}))} nutrition entries")
        print(f"💪 Workout data: {len(workout_data_list)} workouts processed")
        print(f"📄 Reports generated: JSON + PDF")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        logging.exception(f"Error in main execution: {e}")

    finally:
        if automation:
            automation.cleanup()


if __name__ == "__main__":
    main()
