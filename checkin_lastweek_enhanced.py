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
            self.model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
            logging.info(
                "Gemini API configured with model: gemini-2.0-pro-exp-02-05")
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
            # Path to your service account credentials JSON file
            SERVICE_ACCOUNT_FILE = 'service-account-credentials.json'

            # Define the scope
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            service = build('sheets', 'v4', credentials=credentials)

            return service.spreadsheets()
        except Exception as e:
            logging.exception(f"Error setting up Google Sheets API: {e}")
            return None

    def update_legit_checkin_status(self, first_name, last_name, legit_checkin_value="Yes"):
        """
        Updates the "Legit Checkin" status (column AE) for a specific person
        by matching their first name (column D) and last name (column E)
        """
        try:
            sheets = self.setup_sheets_api()
            if not sheets:
                logging.error("Failed to set up Google Sheets API")
                return False

            # Your specific spreadsheet ID
            SPREADSHEET_ID = '1038Ep0lYGEtpipNAIzH7RB67-KOAfXA-TcUTKBKqIfo'

            # Step 1: Get all data to find the matching person
            result = sheets.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:AZ'  # Make sure this is the correct sheet name
            ).execute()

            rows = result.get('values', [])

            if not rows:
                logging.info("No data found in sheet.")
                return False

            # Find the column indices
            first_name_col_index = 3  # Column D (0-indexed)
            last_name_col_index = 4   # Column E (0-indexed)

            # Step 2: Find the row that matches our person's name
            row_index = -1
            for i in range(1, len(rows)):  # Start from 1 to skip header row
                if len(rows[i]) > last_name_col_index:  # Make sure row has enough columns
                    row_first_name = rows[i][first_name_col_index].strip(
                    ).lower() if len(rows[i]) > first_name_col_index else ""
                    row_last_name = rows[i][last_name_col_index].strip(
                    ).lower() if len(rows[i]) > last_name_col_index else ""

                    # Check if this row matches our search criteria
                    if (row_first_name == first_name.strip().lower() and
                            row_last_name == last_name.strip().lower()):
                        row_index = i
                        break

            if row_index == -1:
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
            update_result = sheets.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            logging.info(
                f"Legit Checkin status updated for {first_name} {last_name}")
            return True

        except Exception as e:
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

    def create_checkin_review_pdf(self, client_name, fitness_wrapped_data, review_content):
        """Creates an enhanced professionally formatted PDF document with the check-in review."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.units import inch
            from datetime import datetime

            # Check which data is actually available
            has_steps_data = fitness_wrapped_data.get('has_steps_data', False)
            has_sleep_data = fitness_wrapped_data.get('has_sleep_data', False)
            has_nutrition_data = fitness_wrapped_data.get(
                'has_nutrition_data', False)
            has_weight_data = fitness_wrapped_data.get(
                'has_weight_data', False)
            has_reliable_weight_data = fitness_wrapped_data.get(
                'has_reliable_weight_data', False)
            has_workout_data = fitness_wrapped_data.get(
                'has_workout_data', False)

            # If weight data exists but is unreliable, ignore it completely
            if has_weight_data and not has_reliable_weight_data:
                has_weight_data = False
                logging.info(
                    "Ignoring unreliable weight data in PDF generation")

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
                spaceAfter=16,  # Increased spacing
                spaceBefore=12  # Added space before
            ))

            styles.add(ParagraphStyle(
                name='CustomSubHeading',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
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

            # Title
            content.append(
                Paragraph(f"Fitness Check-In Review: {client_name}", title_style))
            content.append(Spacer(1, 0.25*inch))

            # Date
            content.append(
                Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            content.append(
                Paragraph(f"Week: {fitness_wrapped_data['date_range']}", normal_style))
            content.append(Spacer(1, 0.25*inch))

            # Key Achievement Box - only shown if weight data is reliable
            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                if total_change > 0:
                    achievement_text = f"🎯 Key Achievement: You've lost {abs(total_change):.2f}kg! Keep up the great work!"
                    content.append(Paragraph(achievement_text,
                                   styles['KeyAchievement']))
                    content.append(Spacer(1, 0.15*inch))

            # Table headers - only include weight if data is reliable
            table_headers = []
            if has_weight_data:
                table_headers.append("Current Weight")
                table_headers.append("Weight Change")

            if has_workout_data:
                table_headers.append("Workouts This Week")
                table_headers.append("Total Volume")

            # Corresponding values
            table_values = []
            if has_weight_data:
                table_values.append(
                    f"{fitness_wrapped_data['current_weight']} kg")

                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                table_values.append(
                    f"{abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}")

            if has_workout_data:
                table_values.append(
                    f"{fitness_wrapped_data['workouts_this_week']}")
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
            # and handle section headings properly
            processed_content = ""
            goals_section = False
            closing_statement = ""
            closing_found = False
            goals_content = ""
            bulleted_goals = []

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
                    elif goals_section and para.strip().startswith("*"):
                        # Extract bullet points
                        bullet_points = para.split('\n* ')
                        for i, point in enumerate(bullet_points):
                            if i > 0 or point.startswith('*'):
                                point_text = point.strip().lstrip('* ')
                                # Make sure all bullet points end with a period
                                if not point_text.endswith('.'):
                                    point_text += '.'
                                bulleted_goals.append(point_text)
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
                    content.append(Paragraph(para, normal_style))
                    content.append(Spacer(1, 0.2*inch))  # Increased spacing

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
            if has_nutrition_data:
                lifestyle_stats += f"Average Daily Calories: {fitness_wrapped_data['calories_consumed']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Calories: <i>No data available</i><br/>"

            if has_steps_data:
                lifestyle_stats += f"Average Daily Steps: {fitness_wrapped_data['step_count']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Steps: <i>No data available</i><br/>"

            if has_sleep_data:
                lifestyle_stats += f"Sleep Pattern: {fitness_wrapped_data['sleep_hours']}"
            else:
                lifestyle_stats += f"Sleep Pattern: <i>No data available</i>"

            content.append(Paragraph(lifestyle_stats, normal_style))
            content.append(Spacer(1, 0.35*inch))  # Increased spacing

            # WEIGHT PROGRESS section - only include if data is reliable
            if has_weight_data:
                content.append(
                    Paragraph("WEIGHT PROGRESS", styles['CustomHeading']))

                # Get the weight goal and make sure we handle the False case
                client_weight_goal = fitness_wrapped_data.get(
                    'weight_goal', False)

                # Use the values directly - no validation or fallback here
                start_weight = fitness_wrapped_data['start_weight']
                current_weight = fitness_wrapped_data['current_weight']
                total_change = fitness_wrapped_data['total_weight_change']

                # Build the weight progress text - simplified to focus on total change only
                weight_progress = f"""
                Starting Weight: {start_weight} kg<br/>
                Current Weight: {current_weight} kg<br/>
                Total Change: {abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}<br/>
                """

                # Only add the weight goal line if it's a valid number (not False)
                if client_weight_goal is not False:
                    weight_progress += f"Weight Goal: {client_weight_goal} kg<br/>"
                    logging.info(
                        f"Including weight goal in PDF: {client_weight_goal}")
                else:
                    logging.info(
                        "Skipping weight goal in PDF as it's set to False")

                content.append(Paragraph(weight_progress, normal_style))
            else:
                content.append(
                    Paragraph("WEIGHT PROGRESS", styles['CustomHeading']))
                content.append(Paragraph(
                    "No weight data recorded yet. Regular weight tracking is essential for monitoring progress toward your goals.", styles['NoDataStyle']))

            # Add missing data section if applicable
            missing_data_types = []
            if not has_weight_data:
                missing_data_types.append("weight")
            if not has_workout_data:
                missing_data_types.append("workout")
            if not has_nutrition_data:
                missing_data_types.append("nutrition")
            if not has_steps_data:
                missing_data_types.append("step")
            if not has_sleep_data:
                missing_data_types.append("sleep")

            if missing_data_types:
                content.append(Spacer(1, 0.35*inch))  # Increased spacing
                content.append(
                    Paragraph("DATA TRACKING OPPORTUNITIES", styles['CustomHeading']))
                missing_data_text = "To improve the accuracy and personalization of your check-ins, consider tracking the following: "
                missing_data_text += ", ".join(missing_data_types) + "."
                missing_data_text += " Consistent tracking helps us make better recommendations tailored to your progress."
                content.append(Paragraph(missing_data_text, normal_style))

            # Add signature
            # Increased spacing before signature
            content.append(Spacer(1, 0.75*inch))
            content.append(
                Paragraph("Coco's Connected/Shannon Birch", styles['Signature']))

            # Build the PDF
            doc.build(content)
            logging.info(f"PDF document created successfully: {pdf_filename}")

            # Extract first and last name from the client name
            name_parts = client_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                # Handle multi-word last names
                last_name = ' '.join(name_parts[1:])

                # Update the "Legit Checkin" status in Google Sheets
                if self.update_legit_checkin_status(first_name, last_name, "Yes"):
                    logging.info(
                        f"Updated Legit Checkin status for {client_name} in Google Sheets")
                else:
                    logging.warning(
                        f"Failed to update Legit Checkin status for {client_name} in Google Sheets")
            else:
                logging.warning(
                    f"Could not parse first and last name from: {client_name}")

            return pdf_filename

        except ImportError as ie:
            logging.error(f"Missing required library for PDF generation: {ie}")
            print(f"Please install missing library: {ie}")
            return None
        except Exception as e:
            logging.exception(f"Error creating check-in review PDF: {e}")
            return None

    def generate_professional_checkin_review(self, client_name, fitness_wrapped_data):
        """Generates a professional PDF check-in review using the enhanced Gemini model.

        Args:
            client_name: Name of the client
            fitness_wrapped_data: Dictionary containing client fitness data with enhanced metrics

        Returns:
            String: Path to the generated PDF file or None if generation failed
        """
        try:
            if not self.model:
                logging.warning(
                    "Gemini API key not provided, cannot generate check-in review.")
                return None

            # Check if ReportLab is installed
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.units import inch
            except ImportError:
                logging.error(
                    "ReportLab library is not installed. Cannot generate PDF.")
                print("Please install ReportLab with: pip install reportlab")
                return None

            logging.info(
                f"Generating enhanced professional check-in review for {client_name}...")

            # 1. Generate the enhanced check-in review content using Gemini
            review_content = self.generate_enhanced_checkin_review_content(
                client_name, fitness_wrapped_data)
            if not review_content:
                logging.error("Failed to generate enhanced review content")
                # Fall back to the original content generator
                logging.info(
                    "Falling back to original review content generator")
                review_content = self.generate_checkin_review_content(
                    client_name, fitness_wrapped_data)
                if not review_content:
                    logging.error(
                        "Failed to generate review content with fallback method")
                    return None

            # 2. Create the enhanced PDF document
            pdf_filename = self.create_enhanced_checkin_review_pdf(
                client_name, fitness_wrapped_data, review_content)
            if not pdf_filename:
                logging.error("Failed to create enhanced PDF document")
                # Fall back to the original PDF generator
                logging.info("Falling back to original PDF generator")
                pdf_filename = self.create_checkin_review_pdf(
                    client_name, fitness_wrapped_data, review_content)
                if not pdf_filename:
                    logging.error(
                        "Failed to create PDF document with fallback method")
                    return None

            logging.info(
                f"Successfully generated enhanced check-in review PDF: {pdf_filename}")
            return pdf_filename

        except Exception as e:
            logging.exception(
                f"Error generating professional check-in review: {e}")
            return None

    def extract_enhanced_step_data_for_video(steps_analysis):
        """Extract more precise step data from the enhanced analysis for video generation."""
        import re

        try:
            # Look for precise average daily steps with improved pattern matching
            step_patterns = [
                # Look for "average daily steps" with number formats like 10000, 10,000, or 10k
                r"average\s+daily\s+steps\s*(?:of|is|:)?\s*(?:about|approximately)?\s*(\d{1,2}[,.]?\d{0,3}k|\d{1,6})",
                # Look for "averaging X steps" pattern
                r"averaging\s+(?:about|approximately)?\s*(\d{1,2}[,.]?\d{0,3}k|\d{1,6})\s+steps",
                # Look for "X steps per day" pattern
                r"(\d{1,2}[,.]?\d{0,3}k|\d{1,6})\s+steps\s+(?:per|a|each)\s+day",
                # More generic pattern as fallback
                r"(\d{1,2}[,.]?\d{0,3}k|\d{1,6})\s+(?:daily)?\s*steps"
            ]

            # Try each pattern in order of preference
            for pattern in step_patterns:
                matches = re.findall(pattern, steps_analysis, re.IGNORECASE)
                if matches:
                    # Get the first match (likely the most relevant mention)
                    step_count = matches[0]
                    # Handle 'k' format (like 10k)
                    if 'k' in step_count.lower():
                        # Convert 10k to 10,000
                        step_count = step_count.lower().replace('k', ',000')

                    # Clean up number formatting
                    step_count = re.sub(r'[^\d,]', '', step_count)
                    logging.info(f"Extracted precise step count: {step_count}")
                    return step_count

            # If we couldn't find a specific average, look for ranges and take the average
            range_pattern = r"(\d{1,2}[,.]?\d{0,3}k|\d{1,6})\s*(?:-|to)\s*(\d{1,2}[,.]?\d{0,3}k|\d{1,6})\s+steps"
            range_matches = re.findall(
                range_pattern, steps_analysis, re.IGNORECASE)

            if range_matches:
                # Get the first range match
                low, high = range_matches[0]

                # Convert 'k' format if present
                if 'k' in low.lower():
                    low = low.lower().replace('k', '000')
                if 'k' in high.lower():
                    high = high.lower().replace('k', '000')

                # Clean up and convert to integers
                low = int(re.sub(r'[^\d]', '', low))
                high = int(re.sub(r'[^\d]', '', high))

                # Calculate the average
                avg_steps = int((low + high) / 2)
                step_count = f"{avg_steps:,}".replace(',', ',')
                logging.info(f"Calculated average from range: {step_count}")
                return step_count

            # If still no match, look for any number followed by "steps"
            general_step_pattern = r"(\d{1,2}[,.]?\d{0,3}k|\d{1,6})(?:\+)?\s*steps"
            general_matches = re.findall(
                general_step_pattern, steps_analysis, re.IGNORECASE)

            if general_matches:
                # Use the largest number mentioned (more likely to be a daily total than a specific instance)
                step_values = []
                for match in general_matches:
                    if 'k' in match.lower():
                        # Convert 10k to 10000
                        value = float(match.lower().replace('k', '')) * 1000
                    else:
                        # Remove commas and convert to integer
                        value = int(re.sub(r'[^\d]', '', match))
                    step_values.append(value)

                # Get the median value (more robust than max or average)
                step_values.sort()
                median_index = len(step_values) // 2
                step_count = f"{int(step_values[median_index]):,}".replace(
                    ',', ',')
                logging.info(
                    f"Using median step value from mentions: {step_count}")
                return step_count

            # Fallback to default
            logging.warning(
                "Could not extract specific step count, using default")
            return "10,000"

        except Exception as e:
            logging.exception(
                f"Error extracting enhanced step data for video: {e}")
            return "10,000"  # Default fallback

    def extract_enhanced_sleep_data_for_video(sleep_analysis):
        """Extract more precise sleep data from the enhanced analysis for video generation."""
        import re

        try:
            # Try to find the most specific weekly average first
            weekly_avg_patterns = [
                r"average(?:s|d|ing)?\s+(?:of)?\s*(\d{1,2}(?:\.\d+)?)\s*hours\s+(?:of)?\s*sleep",
                r"average\s+(?:nightly|daily)?\s*sleep\s+(?:duration|time)?\s*(?:of|is|:)?\s*(\d{1,2}(?:\.\d+)?)\s*hours",
                r"sleeping\s+(?:an average of)?\s*(\d{1,2}(?:\.\d+)?)\s*hours\s+(?:per|a|each)\s+night"
            ]

            for pattern in weekly_avg_patterns:
                matches = re.findall(pattern, sleep_analysis, re.IGNORECASE)
                if matches:
                    avg_hours = float(matches[0])
                    # Round to 1 decimal place
                    sleep_hours = f"{avg_hours:.1f} Hours per Night"
                    logging.info(
                        f"Extracted precise average sleep hours: {sleep_hours}")
                    return sleep_hours

            # Look for sleep range (e.g., 7-8 hours)
            range_pattern = r"(\d{1,2}(?:\.\d+)?)\s*(?:-|to)\s*(\d{1,2}(?:\.\d+)?)\s*hours"
            range_matches = re.findall(
                range_pattern, sleep_analysis, re.IGNORECASE)

            if range_matches:
                low, high = range_matches[0]
                low_val = float(low)
                high_val = float(high)

                # Use specific formatting: "7-8 Hours per Night"
                sleep_hours = f"{low_val:.1f}-{high_val:.1f} Hours per Night"
                logging.info(f"Extracted sleep range: {sleep_hours}")
                return sleep_hours

            # Last resort: look for any hours mentioned with sleep
            hours_pattern = r"(\d{1,2}(?:\.\d+)?)\s*hours\s+(?:of)?\s*sleep"
            hours_matches = re.findall(
                hours_pattern, sleep_analysis, re.IGNORECASE)

            if hours_matches:
                # Use the average of all mentioned hour values for more accuracy
                total = 0
                count = 0
                for match in hours_matches:
                    total += float(match)
                    count += 1

                if count > 0:
                    avg = total / count
                    sleep_hours = f"{avg:.1f} Hours per Night"
                    logging.info(
                        f"Calculated average from mentions: {sleep_hours}")
                    return sleep_hours

            # Fallback to default but with improved formatting for the video
            logging.warning(
                "Could not extract specific sleep data, using default")
            return "7-9 Hours per Night"

        except Exception as e:
            logging.exception(
                f"Error extracting enhanced sleep data for video: {e}")
            return "7-9 Hours per Night"  # Default fallback

    def extract_enhanced_step_data_for_video(steps_analysis):
        """Extract more precise step data from the enhanced analysis for video generation."""
        import re

        try:
            logging.info(
                "Extracting enhanced step data for video from analysis")

            # Explicitly extract from exact pattern that matches our most common format
            exact_pattern = r"most recent week.*averaging approximately (\d{1,2}[,.]?\d{0,3})\s*steps"
            exact_match = re.search(
                exact_pattern, steps_analysis, re.IGNORECASE)
            if exact_match:
                step_count = exact_match.group(1)
                logging.info(
                    f"Found exact match in most recent week: {step_count}")
                return step_count

            # Look for numbers with commas already in them - high priority
            comma_pattern = r"averaging.*?(\d{1,2},\d{3})\s+steps"
            comma_match = re.search(
                comma_pattern, steps_analysis, re.IGNORECASE)
            if comma_match:
                step_count = comma_match.group(1)
                logging.info(f"Found number with comma: {step_count}")
                return step_count

            # Try a larger context pattern
            context_pattern = r"most recent week.*?(\d{1,2}[,.]?\d{3})\s*steps"
            context_match = re.search(
                context_pattern, steps_analysis, re.IGNORECASE)
            if context_match:
                step_count = context_match.group(1)
                logging.info(f"Found from context pattern: {step_count}")
                return step_count

            # Direct extraction of the specific line from common format
            direct_line = re.search(
                r"client is averaging approximately ([\d,]+) steps", steps_analysis)
            if direct_line:
                step_count = direct_line.group(1)
                logging.info(f"Direct line extraction: {step_count}")
                return step_count

            # Look for specific patterns with steps
            step_number_patterns = [
                r"averaging (?:about |approximately )?([0-9]{1,2},[0-9]{3})",
                r"average (?:of |about |approximately )?([0-9]{1,2},[0-9]{3})",
                r"([0-9]{1,2},[0-9]{3}) steps per day"
            ]

            for pattern in step_number_patterns:
                match = re.search(pattern, steps_analysis, re.IGNORECASE)
                if match:
                    step_count = match.group(1)
                    logging.info(f"Found from numeric pattern: {step_count}")
                    return step_count

            # Look for weekly breakdown patterns
            week_pattern = r"Week of.*?Average daily steps:? ([0-9]{1,2},[0-9]{3})"
            week_matches = re.findall(
                week_pattern, steps_analysis, re.IGNORECASE)

            if week_matches:
                # Get the last one, which is likely the most recent
                step_count = week_matches[-1]
                logging.info(f"Found from last week match: {step_count}")
                return step_count

            # Extract all numbers followed by "steps"
            number_pattern = r"([0-9]{1,2}(?:,[0-9]{3}))\s*steps"
            number_matches = re.findall(number_pattern, steps_analysis)

            if number_matches:
                # Take the first one as it's likely to be the most relevant mention
                step_count = number_matches[0]
                logging.info(f"Found from 'steps' suffix: {step_count}")
                return step_count

            # If we've tried everything and still don't have a match, use a more general approach
            general_pattern = r"(\d{1,2},\d{3})"
            general_matches = re.findall(general_pattern, steps_analysis)

            if general_matches:
                # Take the first comma-formatted number
                step_count = general_matches[0]
                logging.info(
                    f"Using first comma-formatted number: {step_count}")
                return step_count

            # Fallback to default with comma formatting for consistency
            logging.warning(
                "Could not extract specific step count, using default")
            return "10,000"

        except Exception as e:
            logging.exception(
                f"Error extracting enhanced step data for video: {e}")
            return "10,000"  # Default fallback

    def process_client_data_with_enhanced_averages(self, client_name, bodyweight_analysis, nutrition_analysis,
                                                   sleep_analysis, steps_analysis, photos_analysis,
                                                   weight_goal_text, workout_data_list):
        """Process client data with enhanced extraction for better video representation."""
        try:
            # First, extract basic data
            fitness_wrapped_data = self.prepare_fitness_wrapped_data(
                client_name,
                bodyweight_analysis,
                nutrition_analysis,
                sleep_analysis,
                steps_analysis,
                photos_analysis,
                weight_goal_text,
                {},  # weekly_summary_data (empty dict, not needed)
                "",  # workouts_completed_analysis (not needed)
                "",  # total_workout_stats_analysis (not needed)
                workout_data_list
            )

            # Now extract enhanced data for analysis purposes
            enhanced_weight_data = extract_enhanced_weight_data(
                bodyweight_analysis)
            enhanced_nutrition_data = extract_enhanced_nutrition_data(
                nutrition_analysis)
            enhanced_sleep_data = extract_enhanced_sleep_data(sleep_analysis)
            enhanced_steps_data = extract_enhanced_step_data(steps_analysis)

            # Add enhanced data for analysis to the fitness wrapped data
            fitness_wrapped_data.update({
                # Enhanced weight data
                "weight_weekly_changes": enhanced_weight_data["weekly_changes"],
                "weight_avg_weekly_change": enhanced_weight_data["avg_weekly_change"],
                "weight_pattern": enhanced_weight_data["pattern"],

                # Enhanced nutrition data
                "protein_grams": enhanced_nutrition_data["protein_grams"],
                "calorie_assessment": enhanced_nutrition_data["calorie_assessment"],

                # Enhanced sleep data
                "sleep_consistency": enhanced_sleep_data["consistency"],
                "sleep_quality": enhanced_sleep_data["quality"],

                # Enhanced steps data
                "weekly_steps_total": enhanced_steps_data["weekly_total"],
                "steps_consistency": enhanced_steps_data["consistency"],
                "activity_level": enhanced_steps_data["activity_level"]
            })

            # IMPORTANT - Now extract video-optimized data
            # This data will override the basic data for better video presentation

            # Extract better formatted step count for video
            video_step_count = extract_enhanced_step_data_for_video(
                steps_analysis)
            if video_step_count and video_step_count != "10,000":  # If we got a meaningful value
                fitness_wrapped_data["step_count"] = video_step_count
                logging.info(
                    f"Updated step_count with better formatted value: {video_step_count}")

            # Extract better formatted sleep hours for video
            video_sleep_hours = extract_enhanced_sleep_data_for_video(
                sleep_analysis)
            if video_sleep_hours and video_sleep_hours != "7-9 Hours per Night":  # If we got a meaningful value
                fitness_wrapped_data["sleep_hours"] = video_sleep_hours
                logging.info(
                    f"Updated sleep_hours with better formatted value: {video_sleep_hours}")

            return fitness_wrapped_data

        except Exception as e:
            logging.exception(
                f"Error processing client data with enhanced averages: {e}")
            # Fall back to original method if there's any error
            return self.prepare_fitness_wrapped_data(
                client_name,
                bodyweight_analysis,
                nutrition_analysis,
                sleep_analysis,
                steps_analysis,
                photos_analysis,
                weight_goal_text,
                {},
                "",
                "",
                workout_data_list
            )

    def extract_enhanced_sleep_data_for_video(sleep_analysis):
        """Extract more precise sleep data from the enhanced analysis for video generation."""
        import re

        try:
            logging.info(
                "Extracting enhanced sleep data for video from analysis")

            # First try to find the most recent week's average with more precise patterns
            recent_week_patterns = [
                r"most recent week.*averaging (?:about|approximately)?\s*(\d{1,2}(?:\.\d+)?)\s*hours",
                r"current week.*average.*?(\d{1,2}(?:\.\d+)?)\s*hours",
                r"this week.*average.*?(\d{1,2}(?:\.\d+)?)\s*hours"
            ]

            for pattern in recent_week_patterns:
                matches = re.search(pattern, sleep_analysis, re.IGNORECASE)
                if matches:
                    avg_hours = float(matches.group(1))
                    sleep_hours = f"{avg_hours:.1f} Hours per Night"
                    logging.info(
                        f"Extracted most recent week average: {sleep_hours}")
                    return sleep_hours

            # Look for general average patterns
            avg_patterns = [
                r"averaging\s+(?:about|approximately)?\s*(\d{1,2}(?:\.\d+)?)\s*hours",
                r"average(?:s|d|ing)?\s+(?:of)?\s*(\d{1,2}(?:\.\d+)?)\s*hours\s+(?:of)?\s*sleep",
                r"average\s+(?:nightly|daily)?\s*sleep\s+(?:duration|time)?\s*(?:of|is|:)?\s*(\d{1,2}(?:\.\d+)?)\s*hours"
            ]

            for pattern in avg_patterns:
                matches = re.search(pattern, sleep_analysis, re.IGNORECASE)
                if matches:
                    avg_hours = float(matches.group(1))
                    sleep_hours = f"{avg_hours:.1f} Hours per Night"
                    logging.info(
                        f"Extracted average sleep hours: {sleep_hours}")
                    return sleep_hours

            # Look for explicit weekly averages from weekly breakdowns
            weekly_pattern = r"Week of.*?averaging\s+(?:only)?\s*(\d{1,2}(?:\.\d+)?)\s*hours"
            weekly_matches = re.findall(
                weekly_pattern, sleep_analysis, re.IGNORECASE)

            if weekly_matches:
                # Prioritize the last weekly average as it's likely the most recent
                most_recent_avg = float(weekly_matches[-1])
                sleep_hours = f"{most_recent_avg:.1f} Hours per Night"
                logging.info(
                    f"Using most recent weekly average: {sleep_hours}")
                return sleep_hours

            # Look for ranges in the most recent week
            recent_range_patterns = [
                r"most recent week.*?(\d{1,2}(?:\.\d+)?)\s*(?:-|to)\s*(\d{1,2}(?:\.\d+)?)\s*hours",
                r"this week.*?(\d{1,2}(?:\.\d+)?)\s*(?:-|to)\s*(\d{1,2}(?:\.\d+)?)\s*hours",
                r"current week.*?(\d{1,2}(?:\.\d+)?)\s*(?:-|to)\s*(\d{1,2}(?:\.\d+)?)\s*hours"
            ]

            for pattern in recent_range_patterns:
                matches = re.search(pattern, sleep_analysis, re.IGNORECASE)
                if matches:
                    low_val = float(matches.group(1))
                    high_val = float(matches.group(2))
                    sleep_hours = f"{low_val:.1f}-{high_val:.1f} Hours per Night"
                    logging.info(
                        f"Extracted recent week sleep range: {sleep_hours}")
                    return sleep_hours

            # Look for any sleep range
            range_pattern = r"(\d{1,2}(?:\.\d+)?)\s*(?:-|to)\s*(\d{1,2}(?:\.\d+)?)\s*hours"
            range_matches = re.search(
                range_pattern, sleep_analysis, re.IGNORECASE)

            if range_matches:
                low_val = float(range_matches.group(1))
                high_val = float(range_matches.group(2))
                sleep_hours = f"{low_val:.1f}-{high_val:.1f} Hours per Night"
                logging.info(f"Extracted general sleep range: {sleep_hours}")
                return sleep_hours

            # Look for any hours mentioned with sleep as last resort
            hours_pattern = r"(\d{1,2}(?:\.\d+)?)\s*hours\s+(?:of)?\s*sleep"
            hours_matches = re.findall(
                hours_pattern, sleep_analysis, re.IGNORECASE)

            if hours_matches:
                # Use the average of all mentioned hour values for more accuracy
                total = sum(float(match) for match in hours_matches)
                avg = total / len(hours_matches)
                sleep_hours = f"{avg:.1f} Hours per Night"
                logging.info(
                    f"Calculated average from mentions: {sleep_hours}")
                return sleep_hours

            # Fallback to default with improved formatting for the video
            logging.warning(
                "Could not extract specific sleep data, using default")
            return "7-9 Hours per Night"

        except Exception as e:
            logging.exception(
                f"Error extracting enhanced sleep data for video: {e}")
            return "7-9 Hours per Night"  # Default fallback

    def generate_checkin_review_content(self, client_name, fitness_wrapped_data):
        """Generates the check-in review content using Gemini."""
        try:
            logging.info(
                f"Generating check-in review content for {client_name} with Gemini...")

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
            Generate a professional, personalized fitness check-in review for {client_name}. The review should be formal yet encouraging, highlighting achievements and areas for improvement.
            
            IMPORTANT: 
            1. For any data that's not available (labeled "NO DATA"), include a professionally-worded encouragement to start tracking this metric.
            2. Use bold text indicators with "Weight Management Analysis:" format (not **Weight Management Analysis:**)
            3. In the Training Performance Analysis section, DO NOT list the specific workout names (like "Chest and Biceps" etc.)
            4. Make the "Goals and Recommendations for the Coming Week:" section use bullet points with "* " at the start of each point
            5. DO NOT include a section labeled "Closing Statement:" - instead, just add a motivational closing paragraph after the bullet points without a label
            6. The review will be signed off as "Coco's Connected/Shannon Birch" - no need to include this in the content
            
            CLIENT DATA:
            """

            # Include weight data if available, otherwise note it's missing
            if has_weight_data:
                # Simplified to just total weight change
                total_change = fitness_wrapped_data['total_weight_change']

                prompt += f"""
                - Weight: Started at {fitness_wrapped_data['start_weight']}kg, currently {fitness_wrapped_data['current_weight']}kg
                - Total weight change: {abs(total_change):.2f}kg {'loss' if total_change > 0 else 'gain'}
                """

                # Only add weight goal if it's a valid number (not False)
                if fitness_wrapped_data['weight_goal'] is not False:
                    prompt += f"- Weight goal: {fitness_wrapped_data['weight_goal']}kg\n"
                else:
                    prompt += "- IMPORTANT: DO NOT MENTION ANY WEIGHT GOAL - the client does not have one set\n"
            else:
                prompt += """
                - Weight: NO DATA (mention that tracking weight is important for monitoring progress)
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
                - Workouts: NO DATA (suggest logging workouts to track progress and ensure program adherence)
                """

            # Include nutrition data if available, otherwise note it's missing
            if has_nutrition_data:
                prompt += f"""
                - Average daily calories: {fitness_wrapped_data['calories_consumed']}
                """
            else:
                prompt += """
                - Calories: NO DATA (mention that nutrition tracking is essential for reaching fitness goals)
                """

            # Include steps data if available, otherwise note it's missing
            if has_steps_data:
                prompt += f"""
                - Average step count: {fitness_wrapped_data['step_count']}
                """
            else:
                prompt += """
                - Steps: NO DATA (suggest tracking steps for better overall activity monitoring)
                """

            # Include sleep data if available, otherwise note it's missing
            if has_sleep_data:
                prompt += f"""
                - Sleep pattern: {fitness_wrapped_data['sleep_hours']}
                """
            else:
                prompt += """
                - Sleep: NO DATA (mention that sleep quality affects recovery and performance)
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
            2. Weight Management Analysis: (or encouragement to track if no data)
            3. Training Performance Analysis: (or encouragement to track if no data)
            4. Nutrition and Lifestyle Observations: (or encouragement to track if no data)
            5. Specific Exercise Achievements: (highlight top improvements) (or encouragement to track if no data)
            6. Missing Data: (summarize what data is missing and the benefits of tracking it - if any data is missing)
            7. Goals and Recommendations for the Coming Week: (use bullet points starting with "* " for each recommendation)
            8. Add a brief motivational closing paragraph (without any heading or label)
            
            Make it approximately 500-700 words, professional but conversational, and with specific, actionable feedback based on the data that is available.
            
            If the client is on a weight loss journey, focus on fat loss achievements. If they're on a muscle gain journey, focus on strength improvements and muscle development.
            
            Be specific, use numbers from the data where appropriate, and provide personalized advice based on their performance.
            
            IMPORTANT: 
            - When mentioning missing data, be encouraging rather than critical. 
            - Frame it as an opportunity for improvement rather than a failure.
            - Format the section headings in the exact format "Section Name:" (not with ** asterisks)
            - For the Goals section, use bullet points with "* " at the start of each recommendation
            - DO NOT use a "Closing Statement:" heading, just add a motivational paragraph at the end
            """

            print("\n--- Gemini Prompt (Check-in Review) ---")
            print(prompt)

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2048,
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
                spaceAfter=16,  # Increased spacing
                spaceBefore=12  # Added space before
            ))

            styles.add(ParagraphStyle(
                name='CustomSubHeading',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
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

            # Title
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
                    achievement_text = f"🎯 Key Achievement: You've lost {abs(total_change):.2f}kg! Keep up the great work!"
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
                    table_values.append(f"{current_weight} kg")

            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                # Only include total change if it's reasonable
                if abs(total_change) <= 30:
                    table_values.append(
                        f"{abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}")

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
            # and handle section headings properly
            processed_content = ""
            goals_section = False
            closing_statement = ""
            closing_found = False
            goals_content = ""
            bulleted_goals = []

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
                    elif goals_section and para.strip().startswith("*"):
                        # Extract bullet points
                        bullet_points = para.split('\n* ')
                        for i, point in enumerate(bullet_points):
                            if i > 0 or point.startswith('*'):
                                point_text = point.strip().lstrip('* ')
                                # Make sure all bullet points end with a period
                                if not point_text.endswith('.'):
                                    point_text += '.'
                                bulleted_goals.append(point_text)
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
                    content.append(Paragraph(para, normal_style))
                    content.append(Spacer(1, 0.2*inch))  # Increased spacing

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
            if has_nutrition_data:
                lifestyle_stats += f"Average Daily Calories: {fitness_wrapped_data['calories_consumed']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Calories: <i>No data available</i><br/>"

            if has_steps_data:
                lifestyle_stats += f"Average Daily Steps: {fitness_wrapped_data['step_count']}<br/>"
            else:
                lifestyle_stats += f"Average Daily Steps: <i>No data available</i><br/>"

            if has_sleep_data:
                lifestyle_stats += f"Sleep Pattern: {fitness_wrapped_data['sleep_hours']}"
            else:
                lifestyle_stats += f"Sleep Pattern: <i>No data available</i>"

            content.append(Paragraph(lifestyle_stats, normal_style))
            content.append(Spacer(1, 0.35*inch))  # Increased spacing

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

                # Build the weight progress text - simplified to focus on total change only
                weight_progress = f"""
                Starting Weight: {start_weight} kg<br/>
                Current Weight: {current_weight} kg<br/>
                Total Change: {abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}<br/>
                """

                # Only add the weight goal line if it's a valid number (not False) and reasonable
                if client_weight_goal is not False and client_weight_goal >= 40 and client_weight_goal <= 300:
                    weight_progress += f"Weight Goal: {client_weight_goal} kg<br/>"
                    logging.info(
                        f"Including weight goal in PDF: {client_weight_goal}")
                else:
                    logging.info(
                        "Skipping weight goal in PDF as it's set to False or unreasonable")

                content.append(Paragraph(weight_progress, normal_style))
            else:
                content.append(Paragraph(
                    "No weight data recorded for this week. Regular weight tracking is essential for monitoring progress toward your goals.", styles['NoDataStyle']))

            # Add missing data section if applicable
            missing_data_types = []
            if not has_weight_data:
                missing_data_types.append("weight")
            if not has_workout_data:
                missing_data_types.append("workout")
            if not has_nutrition_data:
                missing_data_types.append("nutrition")
            if not has_steps_data:
                missing_data_types.append("step")
            if not has_sleep_data:
                missing_data_types.append("sleep")

            if missing_data_types:
                content.append(Spacer(1, 0.35*inch))  # Increased spacing
                content.append(
                    Paragraph("DATA TRACKING OPPORTUNITIES", styles['CustomHeading']))
                missing_data_text = "To improve the accuracy and personalization of your check-ins, consider tracking the following: "
                missing_data_text += ", ".join(missing_data_types) + "."
                missing_data_text += " Consistent tracking helps us make better recommendations tailored to your progress."
                content.append(Paragraph(missing_data_text, normal_style))

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
            Tuple (most_improved_name, improvement_percentage) or (None, 0) if no valid data
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
            most_improved_info: Tuple (most_improved_name, improvement_percentage)
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
            today = datetime.now().date() - timedelta(weeks=1)
            # Monday of last week
            start_date = today - timedelta(days=today.weekday())
            # Sunday of last week
            end_date = start_date + timedelta(days=6)

            # Week before last week's date range
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
        today = datetime.now().date() - timedelta(weeks=1)  # Last week
        current_week_start = today - \
            timedelta(days=today.weekday())  # Monday of last week
        current_week_end = current_week_start + \
            timedelta(days=6)     # Sunday of last week

        # Calculate week before last week's date range
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
        today = datetime.now().date() - timedelta(weeks=1)  # Last week
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
        step_count = "10000"  # Default
        step_match = re.search(r"(\d{1,2}[,.]?\d{0,3}k)", steps_analysis)
        if step_match:
            step_count = step_match.group(1)
            has_real_data["steps"] = True

        sleep_hours = "8-9 Hours Most Nights"  # Default
        sleep_match = re.search(
            r"(\d{1,2}-\d{1,2})\s*hours", sleep_analysis, re.IGNORECASE)
        if sleep_match:
            sleep_hours = sleep_match.group(0)
            has_real_data["sleep"] = True

        # Extract average calorie info
        calories_consumed = "2700"  # Default

        # Try to extract average calories from nutrition analysis
        avg_calories_match = re.search(
            r"average\s*(?:of)?\s*(\d{1,4})\s*calories", nutrition_analysis, re.IGNORECASE)
        if avg_calories_match:
            try:
                calories_consumed = avg_calories_match.group(1)
                has_real_data["nutrition"] = True
                logging.info(f"Found average calories: {calories_consumed}")
            except (ValueError, TypeError):
                logging.warning("Could not parse average calories")

        # If no average found, look for daily calorie targets or mentions
        if not avg_calories_match:
            # Try to find any calories mention with numbers
            calories_matches = re.findall(
                r"(\d{1,4})\s*calories", nutrition_analysis, re.IGNORECASE)
            if calories_matches:
                # If we have multiple calorie values mentioned, try to average them
                try:
                    calorie_values = [
                        int(cal) for cal in calories_matches if 1000 <= int(cal) <= 4000]
                    if calorie_values:
                        average = sum(calorie_values) // len(calorie_values)
                        calories_consumed = str(average)
                        has_real_data["nutrition"] = True
                        logging.info(
                            f"Calculated average calories from multiple values: {calories_consumed}")
                except (ValueError, TypeError):
                    # If we can't parse or average, just use the first one
                    calories_consumed = calories_matches[0]
                    has_real_data["nutrition"] = True
                    logging.info(
                        f"Using first calorie value found: {calories_consumed}")

        # Get top performing exercises with improvement percentages
        top_exercises = []
        try:
            # Calculate last week's date range
            today = datetime.now().date() - timedelta(weeks=1)
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

        # Create data structure with data availability flags and all the enhanced information
        fitness_wrapped_data = {
            "name": client_name,
            "business_name": "Coco's",
            "date_range": date_range,

            # Weight data with improved reliability
            "start_weight": start_weight if has_reliable_weight_data else None,
            "current_weight": current_weight if has_reliable_weight_data else None,
            "weight_loss": total_weight_change if has_reliable_weight_data else None,
            "weight_change": total_weight_change if has_reliable_weight_data else None,
            "total_weight_change": total_weight_change if has_reliable_weight_data else None,

            # New fields for weight metadata
            "weight_trend": weight_trend,
            "weight_start_date": start_date,
            "weight_current_date": current_date,

            # Other data fields
            "weight_goal": client_weight_goal,
            "current_weight_message": current_weight_message,
            "workouts_this_week": current_week_workout_count,
            "workout_types": workout_names[:4] if workout_names else ["Upper Body", "Lower Body", "HIIT", "Cardio"],
            "total_reps": total_reps,
            "total_sets": total_sets,
            "total_weight_lifted": round(total_weight),
            "workload_increase": round(workload_increase, 2),
            "calories_consumed": calories_consumed,
            "step_count": step_count,
            "sleep_hours": sleep_hours,
            "personalized_message": self.generate_personalized_message(bodyweight_analysis, nutrition_analysis, sleep_analysis),
            "top_exercises": top_exercises,

            # Data availability flags
            "has_weight_data": has_reliable_weight_data,
            "has_steps_data": has_real_data["steps"],
            "has_sleep_data": has_real_data["sleep"],
            "has_nutrition_data": has_real_data["nutrition"],
            "has_up_to_date_photos": has_up_to_date_photos,

            # Additional flags
            "has_workout_data": current_week_workout_count > 0,
            "has_workload_data": workload_increase > 0,
            "has_exercise_data": len(top_exercises) >= 3,

            # Reliability flag
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
            historical_data: List of numerical data points (e.g., weights)
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

    def create_enhanced_checkin_review_pdf(self, client_name, fitness_wrapped_data, review_content):
        """Creates an enhanced professionally formatted PDF document with the check-in review."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.units import inch
            from datetime import datetime

            # Check which data is actually available
            has_steps_data = fitness_wrapped_data.get('has_steps_data', False)
            has_sleep_data = fitness_wrapped_data.get('has_sleep_data', False)
            has_nutrition_data = fitness_wrapped_data.get(
                'has_nutrition_data', False)
            has_weight_data = fitness_wrapped_data.get(
                'has_weight_data', False)
            has_reliable_weight_data = fitness_wrapped_data.get(
                'has_reliable_weight_data', False)
            has_workout_data = fitness_wrapped_data.get(
                'has_workout_data', False)

            # If weight data exists but is unreliable, ignore it completely
            if has_weight_data and not has_reliable_weight_data:
                has_weight_data = False
                logging.info(
                    "Ignoring unreliable weight data in PDF generation")

            # Check for enhanced data
            has_enhanced_sleep = 'sleep_consistency' in fitness_wrapped_data and fitness_wrapped_data[
                'sleep_consistency'] != "Not specified"
            has_enhanced_steps = 'steps_consistency' in fitness_wrapped_data and fitness_wrapped_data[
                'steps_consistency'] != "Not specified"
            has_enhanced_nutrition = 'protein_grams' in fitness_wrapped_data and fitness_wrapped_data[
                'protein_grams'] != "Not specified"
            has_enhanced_weight = 'weight_pattern' in fitness_wrapped_data and fitness_wrapped_data[
                'weight_pattern'] != "Not specified"

            # Generate a filename with date
            today_str = datetime.now().strftime('%Y-%m-%d')
            safe_client_name = client_name.replace(' ', '_')
            pdf_filename = f"{safe_client_name}_{today_str}_check_in_review.pdf"

            logging.info(f"Creating enhanced PDF document: {pdf_filename}")

            # Create the document
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Styles - using the same styles from your original function
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
                spaceAfter=16,  # Increased spacing
                spaceBefore=12  # Added space before
            ))

            styles.add(ParagraphStyle(
                name='CustomSubHeading',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#229ED4'),  # Trainerize blue
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

            # New styles for enhanced data
            styles.add(ParagraphStyle(
                name='InsightBox',
                parent=styles['Normal'],
                borderColor=colors.HexColor('#5CB85C'),  # Green border
                borderWidth=1,
                borderPadding=6,
                borderRadius=3,
                backgroundColor=colors.HexColor(
                    '#DFF0D8'),  # Light green background
                textColor=colors.HexColor('#3C763D'),
                spaceAfter=10
            ))

            styles.add(ParagraphStyle(
                name='HighlightText',
                parent=styles['Normal'],
                textColor=colors.HexColor('#229ED4'),
                fontName='Helvetica-Bold',
                spaceAfter=4
            ))

            # Build the document
            content = []

            # Title
            content.append(
                Paragraph(f"Fitness Check-In Review: {client_name}", title_style))
            content.append(Spacer(1, 0.25*inch))

            # Date
            content.append(
                Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
            content.append(
                Paragraph(f"Week: {fitness_wrapped_data['date_range']}", normal_style))
            content.append(Spacer(1, 0.25*inch))

            # Key Achievement Box - only shown if weight data is reliable
            if has_weight_data:
                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                if total_change > 0:
                    achievement_text = f"🎯 Key Achievement: You've lost {abs(total_change):.2f}kg! Keep up the great work!"
                    content.append(Paragraph(achievement_text,
                                   styles['KeyAchievement']))
                    content.append(Spacer(1, 0.15*inch))

            # Table headers - only include weight if data is reliable
            table_headers = []
            if has_weight_data:
                table_headers.append("Current Weight")
                table_headers.append("Weight Change")

            if has_workout_data:
                table_headers.append("Workouts This Week")
                table_headers.append("Total Volume")

            # Corresponding values
            table_values = []
            if has_weight_data:
                table_values.append(
                    f"{fitness_wrapped_data['current_weight']} kg")

                total_change = fitness_wrapped_data.get(
                    'total_weight_change', 0)
                table_values.append(
                    f"{abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}")

            if has_workout_data:
                table_values.append(
                    f"{fitness_wrapped_data['workouts_this_week']}")
                table_values.append(
                    f"{fitness_wrapped_data['total_weight_lifted']} kg")

            # Only create the table if we have at least one value
            if len(table_headers) > 0:
                data = [table_headers, table_values]

                # Adjust the column widths based on content
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
            # and handle section headings properly
            processed_content = ""
            goals_section = False
            closing_statement = ""
            closing_found = False
            goals_content = ""
            bulleted_goals = []

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
                    elif goals_section and para.strip().startswith("*"):
                        # Extract bullet points
                        bullet_points = para.split('\n* ')
                        for i, point in enumerate(bullet_points):
                            if i > 0 or point.startswith('*'):
                                point_text = point.strip().lstrip('* ')
                                # Make sure all bullet points end with a period
                                if not point_text.endswith('.'):
                                    point_text += '.'
                                bulleted_goals.append(point_text)
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
                    content.append(Paragraph(para, normal_style))
                    content.append(Spacer(1, 0.2*inch))  # Increased spacing

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

            # ENHANCED SECTION: NUTRITION & LIFESTYLE with more detailed information
            content.append(
                Paragraph("NUTRITION & LIFESTYLE", styles['CustomHeading']))

            lifestyle_stats = ""
            if has_nutrition_data:
                lifestyle_stats += f"Average Daily Calories: {fitness_wrapped_data['calories_consumed']}<br/>"

                # Add enhanced nutrition data if available
                if has_enhanced_nutrition and 'calorie_assessment' in fitness_wrapped_data:
                    lifestyle_stats += f"Calorie Assessment: <i>{fitness_wrapped_data['calorie_assessment']}</i><br/>"

                if has_enhanced_nutrition and 'protein_grams' in fitness_wrapped_data:
                    lifestyle_stats += f"Protein Intake: <i>{fitness_wrapped_data['protein_grams']} grams</i><br/>"
            else:
                lifestyle_stats += f"Average Daily Calories: <i>No data available</i><br/>"

            if has_steps_data:
                lifestyle_stats += f"Average Daily Steps: {fitness_wrapped_data['step_count']}<br/>"

                # Add enhanced steps data if available
                if has_enhanced_steps and 'steps_consistency' in fitness_wrapped_data:
                    lifestyle_stats += f"Steps Consistency: <i>{fitness_wrapped_data['steps_consistency']}</i><br/>"

                if has_enhanced_steps and 'activity_level' in fitness_wrapped_data:
                    lifestyle_stats += f"Activity Level: <i>{fitness_wrapped_data['activity_level']}</i><br/>"

                if 'weekly_steps_total' in fitness_wrapped_data and fitness_wrapped_data['weekly_steps_total'] != "Not specified":
                    lifestyle_stats += f"Weekly Steps Total: <i>{fitness_wrapped_data['weekly_steps_total']}</i><br/>"
            else:
                lifestyle_stats += f"Average Daily Steps: <i>No data available</i><br/>"

            if has_sleep_data:
                lifestyle_stats += f"Sleep Pattern: {fitness_wrapped_data['sleep_hours']}<br/>"

                # Add enhanced sleep data if available
                if has_enhanced_sleep and 'sleep_consistency' in fitness_wrapped_data:
                    lifestyle_stats += f"Sleep Consistency: <i>{fitness_wrapped_data['sleep_consistency']}</i><br/>"

                if has_enhanced_sleep and 'sleep_quality' in fitness_wrapped_data:
                    lifestyle_stats += f"Sleep Quality: <i>{fitness_wrapped_data['sleep_quality']}</i>"
            else:
                lifestyle_stats += f"Sleep Pattern: <i>No data available</i>"

            content.append(Paragraph(lifestyle_stats, normal_style))
            content.append(Spacer(1, 0.35*inch))  # Increased spacing

            # ENHANCED SECTION: WEIGHT PROGRESS with more detailed trend information
            content.append(
                Paragraph("WEIGHT PROGRESS", styles['CustomHeading']))

            if has_weight_data:
                # Get the weight goal and make sure we handle the False case
                client_weight_goal = fitness_wrapped_data.get(
                    'weight_goal', False)

                # Use the values directly - no validation or fallback here
                start_weight = fitness_wrapped_data['start_weight']
                current_weight = fitness_wrapped_data['current_weight']
                total_change = fitness_wrapped_data['total_weight_change']

                # Build the weight progress text - now with enhanced data
                weight_progress = f"""
                Starting Weight: {start_weight} kg<br/>
                Current Weight: {current_weight} kg<br/>
                Total Change: {abs(total_change):.2f} kg {'Loss' if total_change > 0 else 'Gain'}<br/>
                """

                # Add enhanced weight data if available
                if has_enhanced_weight:
                    if 'weight_pattern' in fitness_wrapped_data and fitness_wrapped_data['weight_pattern'] != "Not specified":
                        weight_progress += f"Weight Pattern: <i>{fitness_wrapped_data['weight_pattern']}</i><br/>"

                    if 'weight_avg_weekly_change' in fitness_wrapped_data and fitness_wrapped_data['weight_avg_weekly_change'] is not None:
                        weight_progress += f"Average Weekly Change: <i>{fitness_wrapped_data['weight_avg_weekly_change']:.2f} kg</i><br/>"

                # Only add the weight goal line if it's a valid number (not False)
                if client_weight_goal is not False:
                    weight_progress += f"Weight Goal: {client_weight_goal} kg<br/>"
                    logging.info(
                        f"Including weight goal in PDF: {client_weight_goal}")
                else:
                    logging.info(
                        "Skipping weight goal in PDF as it's set to False")

                content.append(Paragraph(weight_progress, normal_style))

                # Add weekly changes insight box if available
                if 'weight_weekly_changes' in fitness_wrapped_data and fitness_wrapped_data['weight_weekly_changes']:
                    weekly_changes = fitness_wrapped_data['weight_weekly_changes']
                    if len(weekly_changes) > 0:
                        weekly_insight = "Weekly Weight Changes: "
                        # Show up to 3 weekly changes
                        for i, change in enumerate(weekly_changes[:3]):
                            weekly_insight += f"Week {i+1}: {change:.2f} kg"
                            if i < min(2, len(weekly_changes)-1):
                                weekly_insight += ", "
                        content.append(Spacer(1, 0.1*inch))
                        content.append(
                            Paragraph(weekly_insight, styles['InsightBox']))
            else:
                content.append(Paragraph(
                    "No weight data recorded yet. Regular weight tracking is essential for monitoring progress toward your goals.", styles['NoDataStyle']))

            # Add missing data section if applicable
            missing_data_types = []
            if not has_weight_data:
                missing_data_types.append("weight")
            if not has_workout_data:
                missing_data_types.append("workout")
            if not has_nutrition_data:
                missing_data_types.append("nutrition")
            if not has_steps_data:
                missing_data_types.append("step")
            if not has_sleep_data:
                missing_data_types.append("sleep")

            if missing_data_types:
                content.append(Spacer(1, 0.35*inch))  # Increased spacing
                content.append(
                    Paragraph("DATA TRACKING OPPORTUNITIES", styles['CustomHeading']))
                missing_data_text = "To improve the accuracy and personalization of your check-ins, consider tracking the following: "
                missing_data_text += ", ".join(missing_data_types) + "."
                missing_data_text += " Consistent tracking helps us make better recommendations tailored to your progress."
                content.append(Paragraph(missing_data_text, normal_style))

            # Add signature
            # Increased spacing before signature
            content.append(Spacer(1, 0.75*inch))
            content.append(
                Paragraph("Coco's Connected/Shannon Birch", styles['Signature']))

            # Build the PDF
            doc.build(content)
            logging.info(
                f"Enhanced PDF document created successfully: {pdf_filename}")

            # Extract first and last name from the client name
            name_parts = client_name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                # Handle multi-word last names
                last_name = ' '.join(name_parts[1:])

                # Update the "Legit Checkin" status in Google Sheets
                if self.update_legit_checkin_status(first_name, last_name, "Yes"):
                    logging.info(
                        f"Updated Legit Checkin status for {client_name} in Google Sheets")
                else:
                    logging.warning(
                        f"Failed to update Legit Checkin status for {client_name} in Google Sheets")
            else:
                logging.warning(
                    f"Could not parse first and last name from: {client_name}")

            return pdf_filename

        except ImportError as ie:
            logging.error(f"Missing required library for PDF generation: {ie}")
            print(f"Please install missing library: {ie}")
            return None
        except Exception as e:
            logging.exception(
                f"Error creating enhanced check-in review PDF: {e}")
            return None

    def generate_enhanced_checkin_review_content(self, client_name, fitness_wrapped_data):
        """Generates a more detailed check-in review content using the enhanced Gemini model."""
        try:
            logging.info(
                f"Generating enhanced check-in review content for {client_name} with Gemini...")

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

            # Check for enhanced data availability
            has_enhanced_weight = 'weight_pattern' in fitness_wrapped_data and fitness_wrapped_data[
                'weight_pattern'] != "Not specified"
            has_enhanced_nutrition = 'calorie_assessment' in fitness_wrapped_data and fitness_wrapped_data[
                'calorie_assessment'] != "Not specified"
            has_enhanced_sleep = 'sleep_consistency' in fitness_wrapped_data and fitness_wrapped_data[
                'sleep_consistency'] != "Not specified"
            has_enhanced_steps = 'steps_consistency' in fitness_wrapped_data and fitness_wrapped_data[
                'steps_consistency'] != "Not specified"

            # Format all relevant client data for the prompt, including enhanced data
            prompt = f"""
            Generate a comprehensive, personalized fitness check-in review for {client_name}. The review should be professional yet encouraging, with detailed insights based on patterns and trends in their data.
            
            IMPORTANT FORMATTING GUIDELINES: 
            1. For any data that's not available (labeled "NO DATA"), include a professionally-worded encouragement to start tracking this metric.
            2. Use format "Weight Management Analysis:" (not **Weight Management Analysis:**) for section headings
            3. In the Training Performance Analysis section, DO NOT list the specific workout names
            4. Make the "Goals and Recommendations for the Coming Week:" section use bullet points with "* " at the start
            5. DO NOT include a section labeled "Closing Statement:" - instead, add a motivational closing paragraph after the bullet points without a label
            6. The review will be signed off as "Coco's Connected/Shannon Birch" - no need to include this in the content
            
            CLIENT DATA:
            """

            # Include enhanced weight data if available
            if has_weight_data:
                total_change = fitness_wrapped_data['total_weight_change']

                prompt += f"""
                WEIGHT DATA:
                - Started at {fitness_wrapped_data['start_weight']}kg, currently {fitness_wrapped_data['current_weight']}kg
                - Total weight change: {abs(total_change):.2f}kg {'loss' if total_change > 0 else 'gain'}
                """

                # Add enhanced weight data if available
                if has_enhanced_weight:
                    prompt += f"- Weight pattern: {fitness_wrapped_data.get('weight_pattern', 'Not specified')}\n"

                    if 'weight_avg_weekly_change' in fitness_wrapped_data and fitness_wrapped_data['weight_avg_weekly_change'] is not None:
                        prompt += f"- Average weekly change: {fitness_wrapped_data['weight_avg_weekly_change']:.2f}kg\n"

                    if 'weight_weekly_changes' in fitness_wrapped_data and fitness_wrapped_data['weight_weekly_changes']:
                        weekly_changes = fitness_wrapped_data['weight_weekly_changes']
                        if len(weekly_changes) > 0:
                            prompt += "- Recent weekly changes: "
                            # Show up to 3 most recent changes
                            for i, change in enumerate(weekly_changes[:3]):
                                prompt += f"Week {i+1}: {change:.2f}kg"
                                if i < min(2, len(weekly_changes)-1):
                                    prompt += ", "
                            prompt += "\n"

                # Only add weight goal if it's a valid number (not False)
                if fitness_wrapped_data['weight_goal'] is not False:
                    prompt += f"- Weight goal: {fitness_wrapped_data['weight_goal']}kg\n"
                else:
                    prompt += "- IMPORTANT: DO NOT MENTION ANY WEIGHT GOAL - the client does not have one set\n"
            else:
                prompt += """
                WEIGHT DATA: NO DATA (mention that consistent weight tracking is important for monitoring progress)
                """

            # Include workout data if available
            if has_workout_data:
                prompt += f"""
                WORKOUT DATA:
                - Workouts completed this week: {fitness_wrapped_data['workouts_this_week']}
                - Workout types: {', '.join(fitness_wrapped_data['workout_types'][:4])}
                - Total weight lifted: {fitness_wrapped_data['total_weight_lifted']}kg
                - Total reps: {fitness_wrapped_data['total_reps']}
                - Total sets: {fitness_wrapped_data['total_sets']}
                - Workload increase: {fitness_wrapped_data['workload_increase']}%
                """
            else:
                prompt += """
                WORKOUT DATA: NO DATA (suggest logging workouts to track progress and ensure program adherence)
                """

            # Include enhanced nutrition data if available
            if has_nutrition_data:
                prompt += f"""
                NUTRITION DATA:
                - Average daily calories: {fitness_wrapped_data['calories_consumed']}
                """

                if has_enhanced_nutrition:
                    if 'calorie_assessment' in fitness_wrapped_data:
                        prompt += f"- Calorie assessment: {fitness_wrapped_data['calorie_assessment']}\n"
                    if 'protein_grams' in fitness_wrapped_data and fitness_wrapped_data['protein_grams'] != "Not specified":
                        prompt += f"- Protein intake: {fitness_wrapped_data['protein_grams']} grams\n"
            else:
                prompt += """
                NUTRITION DATA: NO DATA (mention that nutrition tracking is essential for reaching fitness goals)
                """

            # Include enhanced steps data if available
            if has_steps_data:
                prompt += f"""
                STEPS DATA:
                - Average daily steps: {fitness_wrapped_data['step_count']}
                """

                if has_enhanced_steps:
                    if 'steps_consistency' in fitness_wrapped_data:
                        prompt += f"- Steps consistency: {fitness_wrapped_data['steps_consistency']}\n"
                    if 'activity_level' in fitness_wrapped_data:
                        prompt += f"- Activity level: {fitness_wrapped_data['activity_level']}\n"
                    if 'weekly_steps_total' in fitness_wrapped_data and fitness_wrapped_data['weekly_steps_total'] != "Not specified":
                        prompt += f"- Weekly steps total: {fitness_wrapped_data['weekly_steps_total']}\n"
            else:
                prompt += """
                STEPS DATA: NO DATA (suggest tracking steps for better overall activity monitoring)
                """

            # Include enhanced sleep data if available
            if has_sleep_data:
                prompt += f"""
                SLEEP DATA:
                - Sleep pattern: {fitness_wrapped_data['sleep_hours']}
                """

                if has_enhanced_sleep:
                    if 'sleep_consistency' in fitness_wrapped_data:
                        prompt += f"- Sleep consistency: {fitness_wrapped_data['sleep_consistency']}\n"
                    if 'sleep_quality' in fitness_wrapped_data:
                        prompt += f"- Sleep quality: {fitness_wrapped_data['sleep_quality']}\n"
            else:
                prompt += """
                SLEEP DATA: NO DATA (mention that sleep quality affects recovery and performance)
                """

            # Include exercise improvement data if available
            if has_exercise_data:
                prompt += f"""
                EXERCISE DATA:
                - Top performing exercises: {', '.join([f"{ex['name']} ({ex['improvement']}% improvement)" for ex in fitness_wrapped_data['top_exercises']])}
                """
            else:
                prompt += """
                EXERCISE DATA: NO DETAILED DATA (suggest consistent tracking of key exercises to monitor strength improvements)
                """

            prompt += """
            REVIEW STRUCTURE:
            
            1. Personalized greeting and detailed summary of overall progress
            2. Weight Management Analysis: 
            - Include trend patterns and week-to-week changes if available
            - Comment on consistency of weight tracking and changes
            - Discuss rate of progress relative to goals when applicable
            
            3. Training Performance Analysis: 
            - Highlight workload improvements and consistency
            - Mention specific strength gains in key exercises if available
            - Note volume increases compared to previous periods
            
            4. Nutrition and Lifestyle Observations: 
            - Analyze caloric intake relative to goals
            - Discuss protein intake if data is available
            - Integrate sleep and activity patterns with nutrition habits
            - Note how steps and activity level contribute to overall health
            
            5. Pattern Recognition (NEW SECTION):
            - Identify correlations between different metrics (e.g., sleep quality and workout performance)
            - Note consistency patterns across all tracked metrics
            - Highlight areas where data tracking has improved
            
            6. Missing Data (if any): 
            - Summarize what data is missing and the benefits of tracking it
            - Frame as opportunity rather than criticism
            
            7. Goals and Recommendations for the Coming Week: 
            - Use bullet points starting with "* " for each recommendation
            - Make recommendations highly specific based on the identified patterns
            - Include 4-6 actionable bullet points
            
            8. Add a brief motivational closing paragraph (without any heading or label)
            
            Make it approximately 700-900 words, professional but conversational, with specific, actionable feedback based on patterns in the data.
            
            If the client is on a weight loss journey, focus on fat loss achievements and metabolic patterns. If they're on a muscle gain journey, focus on strength improvements, recovery patterns, and muscle development.
            
            Be specific, use numbers from the data where appropriate, and highlight trends and patterns rather than just single data points.
            """

            logging.info("Sending enhanced prompt to Gemini")
            print("\n--- Enhanced Gemini Prompt (Check-in Review) ---")
            # Print abbreviated prompt to save space
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=4096,  # Increased token limit for more detailed response
                    temperature=0.2  # Lower temperature for more professional, consistent output
                )
            )

            review_content = response.text

            print("\n--- Gemini Response (Enhanced Check-in Review) ---")
            # Print just the beginning to save space
            print(
                review_content[:500] + "..." if len(review_content) > 500 else review_content)

            logging.info(
                f"Successfully generated enhanced check-in review content ({len(review_content)} characters)")
            return review_content

        except Exception as e:
            logging.exception(
                f"Error generating enhanced check-in review content: {e}")
            return None

    def extract_enhanced_step_data(steps_analysis):
        """Extract more detailed step data from the enhanced analysis."""
        import re

        try:
            # Extract average daily steps
            step_averages = re.findall(r"average(?:\s+daily)?\s+(?:of\s+)?(?:about\s+)?(\d{1,2}[,.]?\d{0,3}k|\d{1,5})",
                                       steps_analysis, re.IGNORECASE)

            # Extract weekly totals if available
            weekly_totals = re.findall(r"(?:weekly|week's|total)(?:\s+steps)?\s+(?:of\s+)?(?:about\s+)?(\d{1,3}[,.]?\d{0,3}k|\d{5,7})",
                                       steps_analysis, re.IGNORECASE)

            # Extract consistency patterns
            consistent = "consistent" in steps_analysis.lower()
            inconsistent = any(term in steps_analysis.lower() for term in [
                               "inconsistent", "varies", "variable", "fluctuates"])

            # Extract activity level assessment
            activity_level = None
            for level in ["sedentary", "low active", "somewhat active", "active", "highly active"]:
                if level in steps_analysis.lower():
                    activity_level = level
                    break

            # Compile enhanced data
            enhanced_data = {
                "step_count": step_averages[0] if step_averages else "Not specified",
                "weekly_total": weekly_totals[0] if weekly_totals else "Not specified",
                "consistency": "Consistent" if consistent and not inconsistent else "Inconsistent" if inconsistent else "Not specified",
                "activity_level": activity_level or "Not specified"
            }

            return enhanced_data

        except Exception as e:
            logging.exception(f"Error extracting enhanced step data: {e}")
            return {
                "step_count": "10000",  # Default
                "weekly_total": "70000",  # Default
                "consistency": "Not specified",
                "activity_level": "Not specified"
            }

    def extract_enhanced_sleep_data(sleep_analysis):
        """Extract more detailed sleep data from the enhanced analysis."""
        import re

        try:
            # Extract average sleep hours
            sleep_range_match = re.search(
                r"(\d{1,2}(?:\.\d+)?)\s*-\s*(\d{1,2}(?:\.\d+)?)\s*hours", sleep_analysis, re.IGNORECASE)
            sleep_average_match = re.search(
                r"average(?:s|d)?\s+(?:of\s+)?(?:about\s+)?(\d{1,2}(?:\.\d+)?)\s*hours", sleep_analysis, re.IGNORECASE)

            if sleep_range_match:
                min_hours = float(sleep_range_match.group(1))
                max_hours = float(sleep_range_match.group(2))
                sleep_hours = f"{min_hours}-{max_hours} Hours"
            elif sleep_average_match:
                avg_hours = float(sleep_average_match.group(1))
                sleep_hours = f"{avg_hours} Hours Average"
            else:
                sleep_hours = "7-9 Hours"  # Default

            # Extract sleep consistency
            consistent = "consistent" in sleep_analysis.lower()
            inconsistent = any(term in sleep_analysis.lower() for term in [
                               "inconsistent", "varies", "variable", "irregular", "sporadic"])

            # Extract sleep quality assessment
            optimal = any(term in sleep_analysis.lower()
                          for term in ["optimal", "ideal", "excellent", "great"])
            suboptimal = any(term in sleep_analysis.lower() for term in [
                             "suboptimal", "insufficient", "inadequate", "poor"])

            # Compile enhanced data
            enhanced_data = {
                "sleep_hours": sleep_hours,
                "consistency": "Consistent" if consistent and not inconsistent else "Inconsistent" if inconsistent else "Not specified",
                "quality": "Optimal" if optimal and not suboptimal else "Suboptimal" if suboptimal else "Not specified",
            }

            return enhanced_data

        except Exception as e:
            logging.exception(f"Error extracting enhanced sleep data: {e}")
            return {
                "sleep_hours": "7-9 Hours",  # Default
                "consistency": "Not specified",
                "quality": "Not specified"
            }

    def extract_enhanced_nutrition_data(nutrition_analysis):
        """Extract more detailed nutrition data from the enhanced analysis."""
        import re

        try:
            # Extract average calories with improved pattern matching
            avg_calories_matches = re.findall(
                r"average(?:s|d|ing)?\s+(?:of\s+)?(?:about\s+)?(\d{1,4})\s*(?:to\s*\d{1,4})?\s*calories",
                nutrition_analysis,
                re.IGNORECASE
            )

            if avg_calories_matches:
                calories_consumed = avg_calories_matches[0]
            else:
                # Try to find any calorie numbers
                calorie_numbers = re.findall(
                    r"(\d{1,4})\s*calories", nutrition_analysis, re.IGNORECASE)
                if calorie_numbers:
                    # Filter to reasonable calorie numbers
                    reasonable_numbers = [
                        int(cal) for cal in calorie_numbers if 1000 <= int(cal) <= 4000]
                    if reasonable_numbers:
                        calories_consumed = str(
                            sum(reasonable_numbers) // len(reasonable_numbers))
                    else:
                        calories_consumed = "2700"  # Default
                else:
                    calories_consumed = "2700"  # Default

            # Extract protein information
            protein_matches = re.findall(
                r"(\d{1,3})\s*(?:g|grams)\s*(?:of)?\s*protein", nutrition_analysis, re.IGNORECASE)
            protein_grams = protein_matches[0] if protein_matches else "Not specified"

            # Extract calorie assessment
            too_high = any(term in nutrition_analysis.lower()
                           for term in ["too high", "excessive", "reduce calories"])
            too_low = any(term in nutrition_analysis.lower() for term in [
                          "too low", "insufficient", "increase calories"])
            appropriate = any(term in nutrition_analysis.lower() for term in [
                              "appropriate", "adequate", "on target", "on track"])

            # Compile enhanced data
            enhanced_data = {
                "calories_consumed": calories_consumed,
                "protein_grams": protein_grams,
                "calorie_assessment": "Too high" if too_high and not too_low else "Too low" if too_low and not too_high else "Appropriate" if appropriate else "Not specified"
            }

            return enhanced_data

        except Exception as e:
            logging.exception(f"Error extracting enhanced nutrition data: {e}")
            return {
                "calories_consumed": "2700",  # Default
                "protein_grams": "Not specified",
                "calorie_assessment": "Not specified"
            }

    def extract_enhanced_weight_data(bodyweight_analysis):
        """Extract more detailed weight data from the enhanced analysis."""
        import re
        from datetime import datetime, timedelta

        try:
            # Extract the structured format data first
            start_weight_match = re.search(
                r"STARTING_WEIGHT:\s*(\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)
            current_weight_match = re.search(
                r"CURRENT_WEIGHT:\s*(\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)
            start_date_match = re.search(
                r"STARTING_DATE:\s*(\d{2}-\d{2}-\d{4})", bodyweight_analysis, re.IGNORECASE)
            current_date_match = re.search(
                r"CURRENT_DATE:\s*(\d{2}-\d{2}-\d{4})", bodyweight_analysis, re.IGNORECASE)
            trend_match = re.search(
                r"TREND:\s*(upward|downward|stable)", bodyweight_analysis, re.IGNORECASE)

            # Extract weekly change rates
            weekly_changes = re.findall(
                r"week of [^:]+: ([-+]?\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)
            avg_weekly_change_match = re.search(
                r"average\s+weekly\s+change(?:\s+rate)?(?:\s+of)?\s+([-+]?\d+\.?\d*)\s*kg", bodyweight_analysis, re.IGNORECASE)

            # Extract pattern information
            plateau = "plateau" in bodyweight_analysis.lower()
            fluctuating = any(term in bodyweight_analysis.lower()
                              for term in ["fluctuat", "inconsistent", "variable"])
            consistent = "consistent" in bodyweight_analysis.lower() and not fluctuating

            # Compile enhanced data
            enhanced_data = {
                "start_weight": float(start_weight_match.group(1)) if start_weight_match else None,
                "current_weight": float(current_weight_match.group(1)) if current_weight_match else None,
                "start_date": start_date_match.group(1) if start_date_match else None,
                "current_date": current_date_match.group(1) if current_date_match else None,
                "trend": trend_match.group(1) if trend_match else None,
                "weekly_changes": [float(wc) for wc in weekly_changes] if weekly_changes else [],
                "avg_weekly_change": float(avg_weekly_change_match.group(1)) if avg_weekly_change_match else None,
                "pattern": "Plateau" if plateau else "Fluctuating" if fluctuating else "Consistent" if consistent else "Not specified"
            }

            return enhanced_data

        except Exception as e:
            logging.exception(f"Error extracting enhanced weight data: {e}")
            return {
                "start_weight": None,
                "current_weight": None,
                "start_date": None,
                "current_date": None,
                "trend": None,
                "weekly_changes": [],
                "avg_weekly_change": None,
                "pattern": "Not specified"
            }

    # Update the prepare_fitness_wrapped_data method to include the enhanced data
    def update_prepare_fitness_wrapped_data(self, client_name, bodyweight_analysis, nutrition_analysis,
                                            sleep_analysis, steps_analysis, photos_analysis, weight_goal_text,
                                            weekly_summary_data, workouts_completed_analysis,
                                            total_workout_stats_analysis, workout_data_list):

        # Extract enhanced data first
        enhanced_weight_data = extract_enhanced_weight_data(
            bodyweight_analysis)
        enhanced_nutrition_data = extract_enhanced_nutrition_data(
            nutrition_analysis)
        enhanced_sleep_data = extract_enhanced_sleep_data(sleep_analysis)
        enhanced_steps_data = extract_enhanced_step_data(steps_analysis)

        # Call the original method to get the baseline fitness wrapped data
        fitness_wrapped_data = self.prepare_fitness_wrapped_data(
            client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis,
            steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data,
            workouts_completed_analysis, total_workout_stats_analysis, workout_data_list
        )

        # Add the enhanced data to the fitness wrapped data
        fitness_wrapped_data.update({
            # Enhanced weight data
            "weight_weekly_changes": enhanced_weight_data["weekly_changes"],
            "weight_avg_weekly_change": enhanced_weight_data["avg_weekly_change"],
            "weight_pattern": enhanced_weight_data["pattern"],

            # Enhanced nutrition data
            "protein_grams": enhanced_nutrition_data["protein_grams"],
            "calorie_assessment": enhanced_nutrition_data["calorie_assessment"],

            # Enhanced sleep data
            "sleep_consistency": enhanced_sleep_data["consistency"],
            "sleep_quality": enhanced_sleep_data["quality"],

            # Enhanced steps data
            "weekly_steps_total": enhanced_steps_data["weekly_total"],
            "steps_consistency": enhanced_steps_data["consistency"],
            "activity_level": enhanced_steps_data["activity_level"]
        })

        return fitness_wrapped_data

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
            Analyze this bodyweight graph from a fitness app in comprehensive detail. I need both structured data and detailed analysis:
            
            1. EXACT DATA EXTRACTION (MOST IMPORTANT): 
            - Starting weight (first weight on the left side of the graph): Give the exact number in kg
            - Current/latest weight (rightmost point on the graph): Give the exact number in kg
            - Starting date (date of first weight point): If visible on the graph
            - Current date (date of most recent weight point): If visible on the graph
            
            2. Provide your answer in this EXACT STRUCTURED FORMAT at the beginning:
            STARTING_WEIGHT: [number] kg
            STARTING_DATE: [date in DD-MM-YYYY format or "not visible"]
            CURRENT_WEIGHT: [number] kg
            CURRENT_DATE: [date in DD-MM-YYYY format or "not visible"]
            TREND: [upward/downward/stable]
            
            3. Then provide a WEEK-BY-WEEK DETAILED ANALYSIS:
            - Analyze each visible data point with its approximate date
            - Calculate weekly changes whenever possible (e.g., "Week of [date]: [x.x] kg change")
            - Identify any plateau periods, rapid changes, or inconsistencies
            
            4. TREND COMPARISON:
            - Compare this week's weight data to last week's data in detail
            - Calculate the average weekly change rate over the entire period
            - Note if the recent trend (last 2 weeks) differs from the overall trend
            
            5. PATTERN IDENTIFICATION:
            - Identify any recurring patterns (weekly fluctuations, monthly cycles)
            - Note consistency/inconsistency of weigh-in frequency
            - Highlight any correlations between weight changes and time periods (if visible)
            
            Ensure all numerical data is as precise as possible from what you can see in the graph.
            This information will be used for both programmatic processing and providing detailed client feedback.
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
                    max_output_tokens=1000)
            )
            analysis = response.text

            print("\n--- Gemini Response (Bodyweight Analysis) ---")
            print(analysis)

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
            # Wait for the graph element to be present or for a timeout.
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))
            time.sleep(2)
            screenshot_path = "nutrition_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = self.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
            Provide an in-depth analysis of this nutrition graph from a personal training app. Tell me as much about this graph as you can:
            
            1. DETAILED DATA EXTRACTION:
            - Identify all visible data points on the graph with their dates
            - For each data point, specify the exact calorie value if visible
            - Note protein intake values if they are included
            - Identify any target/goal lines and their values
            
            2. WEEKLY BREAKDOWN:
            - Provide a detailed week-by-week analysis of calorie and protein intake (if shown)
            - Calculate the average for each week and note the trend between weeks
            - Identify the highest and lowest days in each week with their specific values
            - Note any patterns within weeks (e.g., higher weekends, lower weekdays)
            
            3. TREND COMPARISON:
            - Compare this week's nutrition data to last week's data in detail
            - Calculate the percent change in average daily calories between weeks
            - Note if there's a consistent pattern emerging across multiple weeks
            
            4. NUTRITIONAL INSIGHTS:
            - Assess if calorie intake is appropriate (likely too high, too low, or appropriate)
            - Evaluate protein intake levels relative to fitness goals (if visible)
            - Calculate and prominently mention the average daily calorie intake using phrases like "average of X calories per day" or "averaging X calories daily"
            
            5. ACTIONABLE RECOMMENDATIONS:
            - If calories are consistently low, suggest specific, healthy ways to increase intake
            - If calories are consistently high, offer practical strategies to reduce intake
            - For protein, suggest specific foods or timing strategies based on the data
            - Recommend specific meal timing adjustments if patterns suggest they would be helpful
            
            Keep your tone positive and encouraging, but provide substantial detailed analysis that can help identify specific patterns and areas for improvement.
            """},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]

            print("\n--- Gemini Prompt (Nutrition Analysis) ---")
            print(prompt_parts[0]['parts'][0]['text'])

            response = self.model.generate_content(
                contents=prompt_parts,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=1000)
            )
            analysis = response.text

            print("\n--- Gemini Response (Nutrition Analysis) ---")
            print(analysis)

            return analysis

        except TimeoutException:
            return "No nutrition data available."
        except Exception as e:
            logging.exception(
                f"Error analyzing nutrition graph with gemini-2.0-flash: {e}")
            return f"Error: {e}"

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
            Provide a comprehensive analysis of this sleep graph from a personal training app. Tell me as much about this graph as you can:
            
            1. DETAILED DATA EXTRACTION:
            - Identify all visible data points with their dates (or at least the week they represent)
            - Extract the exact sleep duration for each data point visible on the graph
            - Note any missing days where data wasn't recorded
            
            2. WEEKLY BREAKDOWN:
            - Provide a detailed week-by-week analysis of sleep patterns
            - For each week, calculate:
              * Average sleep duration
              * Consistency score (how similar sleep duration is each night)
              * Highest and lowest sleep durations with their days
              * Sleep quality indicators if available
            
            3. TREND COMPARISON:
            - Compare this week's sleep data to last week's data in detail
            - Calculate the change in average sleep duration between weeks
            - Note changes in sleep consistency between weeks
            - Compare the most recent week to the average of all visible weeks
            
            4. PATTERN IDENTIFICATION:
            - Identify any recurring patterns (weekend vs. weekday differences, etc.)
            - Spot any cycles or trends over multiple weeks
            - Note if sleep duration correlates with any visible day patterns
            
            5. SLEEP QUALITY ASSESSMENT:
            - Evaluate if sleep durations fall within the optimal 7-9 hour range
            - Assess the consistency of sleep timing (if visible)
            - Identify any concerning patterns (highly variable sleep, consistently short sleep)
            
            6. ACTIONABLE RECOMMENDATIONS:
            - Suggest specific strategies to improve sleep duration if needed
            - Recommend ways to increase sleep consistency if that's an issue
            - Provide practical tips for better sleep quality based on the observed patterns
            
            Keep your tone positive and encouraging, but provide substantial detailed analysis that can help identify specific patterns and areas for improvement.
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
                    max_output_tokens=1000)
            )
            analysis = response.text

            print("\n--- Gemini Response (Sleep Analysis) ---")
            print(analysis)

            print(analysis)
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
            # Wait for the graph element to be present or for a timeout
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "canvas.chartjs-render-monitor")))

            self._click_3m_button_if_exists()  # Click 3M button if present

            time.sleep(2)
            screenshot_path = "steps_graph.png"
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
            base64_image = TrainerizeAutomation.encode_image(screenshot_path)
            if not base64_image:
                return "Error: Could not encode image."

            prompt_parts = [{
                "parts": [
                    {"text": f"""
            Provide a comprehensive analysis of this steps graph from a personal training app. Tell me as much about this graph as you can:
            
            1. DETAILED DATA EXTRACTION:
            - Identify all visible data points with their dates
            - Extract the exact or approximate step count for each data point
            - Note any days where data appears to be missing
            - Identify any target/goal lines and their values
            
            2. WEEKLY BREAKDOWN:
            - Provide a detailed week-by-week analysis of step patterns
            - For each week calculate:
              * Total steps for the week
              * Average daily steps
              * Highest and lowest step days with their exact counts
              * Number of days meeting common step goals (e.g., 10,000 steps)
            
            3. TREND COMPARISON:
            - Compare this week's step data to last week's data in detail
            - Calculate the percent change in average daily steps between weeks
            - Compare the most recent week to the average of all visible weeks
            - Note if there's a consistent trend over multiple weeks (increasing, decreasing, stable)
            
            4. PATTERN IDENTIFICATION:
            - Identify any recurring patterns (weekend vs. weekday differences, etc.)
            - Note consistency/inconsistency of daily step activity
            - Spot any correlations between high/low step days and particular days of the week
            
            5. ACTIVITY LEVEL ASSESSMENT:
            - Evaluate overall activity level relative to common benchmarks:
              * Sedentary: under 5,000 steps
              * Low active: 5,000-7,499 steps
              * Somewhat active: 7,500-9,999 steps
              * Active: 10,000-12,499 steps
              * Highly active: 12,500+ steps
            
            6. ACTIONABLE RECOMMENDATIONS:
            - Suggest specific strategies to increase steps on low days
            - Recommend ways to maintain consistency across all days
            - Provide practical tips for building more movement into their daily routine
            
            Keep your tone positive and encouraging, but provide substantial detailed analysis that can help identify specific patterns and areas for improvement.
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
                    max_output_tokens=1000)
            )
            analysis = response.text

            print("\n--- Gemini Response (Steps Analysis) ---")
            print(analysis)

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
                    max_output_tokens=1000)
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
            processed_workout_names = set()  # For tracking unique workout NAMES

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
                        f"Processed all {len(processed_workout_names)} unique workout types from {i} rows")
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

                    logging.info(
                        f"Found workout {i+1}/{len(rows)}: '{workout_name}' on date: '{date_str}'")

                    # Skip if workout NAME has already been processed (regardless of date)
                    if workout_name in processed_workout_names:
                        logging.info(
                            f"Skipping duplicate workout type: {workout_name}")
                        i += 1
                        continue

                    # Process this workout
                    processed_workout_names.add(workout_name)
                    logging.info(
                        f"Processing unique workout type: {workout_name}")

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
                f"Final workout_data_list contains data for {len(processed_workout_names)} unique workout types")
            return workout_data_list

        except Exception as e:
            logging.exception(f"Error during workout processing: {e}")
            return []

    def analyze_workout_details_stripped(self, workout_name, date_str):
        """Calls the base function with workout_name and date_str parameters."""
        return analyze_workout_details_stripped_base(self, workout_name, date_str)

    def generate_personalized_message(self, bodyweight_analysis, nutrition_analysis, sleep_analysis):
        """Generate a personalized message based on client data."""
        if not self.model:
            # Default message if Gemini is not available
            message = "Another fantastic week! Your workload has increased nicely.\n"
            message += "Your nutrition is on point, and your weight is trending in the right direction.\n"
            message += "Keep pushing, and you'll reach that goal weight in no time!"
            return message

        try:
            prompt = f"""Generate a personalized, encouraging message (3-5 sentences) for a fitness client's weekly wrap-up video.
            Base it on this data:
            
            Bodyweight Analysis: {bodyweight_analysis}
            
            Nutrition Analysis: {nutrition_analysis}
            
            Sleep Analysis: {sleep_analysis}
            
            The message should be motivational, highlight their progress, and encourage them to keep going. 
            Mention specific achievements if possible. Format with line breaks for better readability on video slides. 
            Generate only report (do not let us know you have generated the report) (do not use the clients name in the message)
            """

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(max_output_tokens=250)
            )

            return response.text
        except Exception as e:
            logging.exception(f"Error generating personalized message: {e}")
            # Fallback message
            return "Another fantastic week! Your workload has increased by over 25%\nYour nutrition is on point,\nand your weight is dropping.\nWhat more could you ask for!\nKeep pushing, and you'll reach\nthat goal weight in no time!"

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
                f"Processing date: {current_date_str}. Number of table rows found: {len(rows)}")  # DEBUG - keep for general info

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
                        f"  Date: {current_date_str}, Row {row_index}: Exercise Detected - {exercise_name}")  # DEBUG - keep for general info

                # --- Check for Set Data Row (within an exercise) ---
                set_number_cells = row.find_elements(By.XPATH,
                                                     "./td[@class='ant-table-fixed-columns-in-body ant-table-row-cell-break-word' and contains(@style, 'text-align: center; font-size: 12px;') and contains(text(), 'SET')]")
                # Check if current_exercise_data is initialized
                if set_number_cells and current_exercise_data is not None:
                    set_number_cell = set_number_cells[0]
                    set_number_text = set_number_cell.text.strip()
                    logging.info(
                        f"  Date: {current_date_str}, Row {row_index}: Set Detected - {set_number_text} for Exercise - {current_exercise_name}")  # DEBUG - keep for general info

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
                                        f"      Date: {current_date_str}, Extracted Set Data: Set {set_number_text.split(' ')[1]}, Reps: {reps}, Weight: {weight}")  # DEBUG - keep for general info
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


# Entry point

if __name__ == "__main__":
    # Full list of clients to process
    client_names = [
        "Shannon Birch",
        "Ben Pryke",
        "Alice Forster",
        "Sarika Ramani",
        "Helen Forster",
        "Nicole Lynch",
        "Conor Beveridge",
        "Rebecca DAngelo",
        "Rick Preston",
        "Claire Ruberu",
        "Kylie Pinder",
        "Jo Foy",
        "Manny Le-ray",
        "Tony Strupl",
        "Heath Kilgour",
        "Anna Somogyi",
        "Danny Birch",
        "MJ Devine",
        "Ben Norman",
        "Adri Rivera",
        "Amanda Buckingham",
        "Naman Tiwari",
        "Kelly Smith",
        "Shane Minahan"
    ]

    # Login credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # Create TrainerizeAutomation instance
    automation = TrainerizeAutomation(gemini_api_key)

    # Dictionary to store data for all clients - ADDED THIS LINE
    all_client_data = {}

    try:
        # Login
        if not automation.login(username, password):
            print("Login failed! Exiting.")
            automation.cleanup()
            sys.exit(1)

        print("Login successful!")
        automation.handle_notification_popup()

        # Process each client
        for i, client_name in enumerate(client_names, 1):
            print(f"\n{'-'*50}")
            print(f"Processing client {i}/{len(client_names)}: {client_name}")
            print(f"{'-'*50}")

            try:
                # Navigate to client
                if not automation.navigate_to_client(client_name):
                    print(
                        f"Skipping {client_name}: Could not navigate to client")
                    continue

                # Variables to store analysis results
                bodyweight_analysis = "No data available"
                nutrition_analysis = "No data available"
                sleep_analysis = "No data available"
                steps_analysis = "No data available"
                photos_analysis = "No data available"
                weight_goal_text = "No weight goal found"
                workout_data_list = []

                # Analyze bodyweight
                if automation.click_progress_tab():
                    if automation.click_biometrics():
                        bodyweight_analysis = automation.analyze_bodyweight_graph()

                # Analyze nutrition
                if automation.navigate_to_nutrition_graphs():
                    nutrition_analysis = automation.analyze_nutrition_graph()

                # Analyze sleep
                if automation.navigate_to_sleep_graphs():
                    sleep_analysis = automation.analyze_sleep_graph()

                # Analyze steps
                if automation.navigate_to_steps_graphs():
                    steps_analysis = automation.analyze_steps_graph()

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

                        # Display workout statistics
                        automation.display_workout_statistics(
                            workout_data_list)

                # Extract enhanced data
                enhanced_weight_data = extract_enhanced_weight_data(
                    bodyweight_analysis)
                enhanced_nutrition_data = extract_enhanced_nutrition_data(
                    nutrition_analysis)
                enhanced_sleep_data = extract_enhanced_sleep_data(
                    sleep_analysis)
                enhanced_steps_data = extract_enhanced_step_data(
                    steps_analysis)

                # Prepare and save the fitness data
                fitness_wrapped_data = process_client_data_with_enhanced_averages(
                    automation,  # <-- IMPORTANT: Pass automation as first argument
                    client_name,
                    bodyweight_analysis,
                    nutrition_analysis,
                    sleep_analysis,
                    steps_analysis,
                    photos_analysis,
                    weight_goal_text,
                    workout_data_list
                )

                # Save data to JSON file with timestamp
                json_filename = automation.save_fitness_wrapped_data(
                    client_name, fitness_wrapped_data)
                if json_filename:
                    print(
                        f"Successfully saved data for {client_name} to {json_filename}")
                    # Store the data for most improved client calculation - ADDED THIS BLOCK
                    all_client_data[client_name] = {
                        'fitness_wrapped_data': fitness_wrapped_data}
                else:
                    print(f"Failed to save data for {client_name}")

                # Generate professional check-in review
                pdf_filename = automation.generate_professional_checkin_review(
                    client_name, fitness_wrapped_data)
                if pdf_filename:
                    print(
                        f"✓ Professional check-in review created: {pdf_filename}")
                else:
                    print(
                        f"✗ Failed to generate check-in review for {client_name}")

                # Navigate back to clients list before processing the next client
                if not automation.navigate_back_to_clients_list():
                    print(
                        f"Warning: Issue returning to clients list after processing {client_name}.")
                    # Try to recover by going to clients page directly
                    try:
                        automation.driver.get(
                            "https://www.trainerize.com/Clients.aspx")
                        time.sleep(3)
                    except Exception as e:
                        print(f"Error recovering session: {e}")
                        break  # Break out of the client loop if we can't recover

            except Exception as e:
                print(f"Error processing client {client_name}: {e}")
                # Try to recover for next client
                try:
                    # Try to go back to clients list
                    automation.driver.get(
                        "https://www.trainerize.com/Clients.aspx")
                    time.sleep(3)
                except:
                    print("Error recovering after client processing failure. Exiting.")
                    break

        # After processing all clients, determine the most improved client - MOVED THIS BLOCK HERE
        print("\nFinding most improved client...")
        most_improved_info = automation.find_most_improved_client(
            all_client_data)
        if most_improved_info[0]:
            print(
                f"\nMost improved client: {most_improved_info[0]} with {most_improved_info[1]:.2f}% workload increase")

            # Update all JSON files with most improved information
            if automation.update_json_files_with_most_improved(most_improved_info, client_names):
                print(
                    "Successfully updated all client JSON files with most improved information")
            else:
                print("Failed to update JSON files with most improved information")
        else:
            print("\nCould not determine most improved client (no valid workload data)")

        print("\nAll clients processed. Cleaning up...")

    except Exception as e:
        print(f"Fatal error during execution: {e}")

    finally:
        # Always clean up resources
        automation.cleanup()
        print("Script execution complete.")
