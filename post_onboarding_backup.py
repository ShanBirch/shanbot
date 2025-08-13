import subprocess
import sys
# Import only the new Playwright function
from playwright_onboarding_sequence import run_onboarding
from todo_utils import add_todo_item  # Import add_todo_item function
from pb import TrainerizeAutomation  # Import TrainerizeAutomation
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import asyncio
import requests
import base64
import logging
import json
import os
import time
print("=== POST_ONBOARDING_HANDLER.PY (EDITED) ===")
print("=== RUNNING HANDLER FROM ===", os.path.abspath(__file__))
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('post_onboarding')

# Constants
LOGO_PATH = r"C:\Users\Shannon\OneDrive\Documents\cocos logo.png"
PDF_OUTPUT_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\meal plans"
PYTHON_EXE = r"C:\\Program Files\\Python39\\python.exe"


class PostOnboardingHandler:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.webhook_url = "https://hooks.zapier.com/hooks/catch/17459466/2ni82qv/"
        self.google_drive_folder_id = "YOUR_GOOGLE_DRIVE_FOLDER_ID"  # Add your folder ID here
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')

        # Initialize Google Drive service
        try:
            # Use service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                'path/to/your/service-account-key.json',  # Add your service account key path
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Successfully initialized Google Drive service")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.drive_service = None

    async def process_onboarding_completion(self, ig_username: str, conversation_history: List[Dict]) -> bool:
        try:
            # 1. Extract onboarding data
            logger.info(
                f"Starting data extraction for {ig_username} from {len(conversation_history)} messages")
            client_data = await self._analyze_conversation(conversation_history)
            if not client_data:
                logger.error(
                    f"Failed to extract client data for {ig_username}")
                return False

            logger.info(
                f"Successfully extracted data for {ig_username}: {json.dumps(client_data, indent=2)}")

            # 2. Calculate nutrition needs
            nutrition_data = self._calculate_nutrition(client_data)
            if not nutrition_data:
                logger.error(
                    f"Failed to calculate nutrition data for {ig_username}")
                return False

            logger.info(
                f"Calculated nutrition data: {json.dumps(nutrition_data, indent=2)}")

            # 3. Generate meal plan
            meal_plan = await self._generate_meal_plan(nutrition_data, client_data)
            if not meal_plan:
                logger.error(f"Failed to generate meal plan for {ig_username}")
                return False

            logger.info(
                f"Generated meal plan with {len(meal_plan.get('meal_plan_text', '').split())} words")

            # 3b. Generate workout program structure
            program_request = self._design_workout_program(client_data)
            if not program_request:
                logger.error(
                    f"Failed to design workout program for {ig_username}")
                return False

            # 4. Create PDF
            pdf_path = self._create_meal_plan_pdf(
                meal_plan['meal_plan_text'], client_data, nutrition_data)
            if not pdf_path:
                logger.error(f"Failed to create PDF for {ig_username}")
                return False

            logger.info(f"Created PDF at: {pdf_path}")

            # 5. Playwright Onboarding (replaces Zapier)
            try:
                # Map client_data to Playwright onboarding fields
                pw_client_data = {
                    "coach_email": "shannonbirch@cocospersonaltraining.com",
                    "coach_password": "cyywp7nyk2",
                    "email": client_data['personal_info']['email']['value'],
                    "first_name": client_data['personal_info']['full_name']['value'].split(' ')[0],
                    "last_name": client_data['personal_info']['full_name']['value'].split(' ')[1] if len(client_data['personal_info']['full_name']['value'].split(' ')) > 1 else "",
                    "program_name": f"{client_data['personal_info']['full_name']['value']}'s Program",
                    "training_days": client_data['training_info']['training_days']['value'],
                    "workout_program": program_request  # Pass the designed program to Playwright
                }
                # Attach the designed workout program to client_data before passing to pe.py
                client_data['workout_program'] = program_request
                # Log the workout program being sent
                logger.info(
                    f"Workout program to be sent to pe.py: {json.dumps(client_data.get('workout_program', {}), indent=2)}")
                meal_plan_pdf_full_path = os.path.join(
                    PDF_OUTPUT_DIR, pdf_path)
                logger.info(
                    f"Starting Playwright onboarding for {pw_client_data['email']}...")
                # Before launching pe.py subprocess, save the workout program
                self.save_workout_program_to_analytics(
                    ig_username, program_request)
                # Save meal plan to analytics for record-keeping before launching subprocess
                self.save_meal_plan_to_analytics(ig_username, meal_plan)

                # Launch onboarding in a subprocess and wait for completion
                # Ensure workout_program is included
                client_data_json = json.dumps(client_data)
                exit_code = self._launch_onboarding_subprocess_and_wait(
                    client_data, meal_plan_pdf_full_path)

                if exit_code == 0:
                    logger.info(
                        "Successfully completed Playwright onboarding subprocess")

                    # Add a delay to ensure everything is fully completed
                    time.sleep(5)  # Wait 5 seconds

                    # Set ManyChat tag and update analytics
                    try:
                        # Assuming set_manychat_tag exists
                        from webhook_handlers import get_user_data, set_manychat_tag
                        _, metrics_dict, *_ = get_user_data(ig_username)
                        subscriber_id = metrics_dict.get(
                            'subscriber_id', '') if metrics_dict else ''
                        logger.info(
                            f"[POST-ONBOARDING] Fetched subscriber_id for {ig_username}: '{subscriber_id}'")

                        if subscriber_id:
                            tag_name = "onboarded"
                            logger.info(
                                f"[POST-ONBOARDING] Attempting to set tag '{tag_name}' for subscriber_id: {subscriber_id}")
                            # Replace with actual function call to set tag
                            # await set_manychat_tag(subscriber_id, tag_name)
                            # For now, we'll log as if it's done, user needs to implement/verify set_manychat_tag
                            # This is a placeholder for the actual ManyChat API call to set a tag.
                            # You will need to ensure `set_manychat_tag` is correctly implemented
                            # in `webhook_handlers.py` to use ManyChat's API for adding a tag.
                            # Example of what that function *might* do:
                            # manychat_api_url = f"https://api.manychat.com/fb/subscriber/addTag"
                            # headers = {'Authorization': f'Bearer {MANYCHAT_API_KEY}', 'Content-Type': 'application/json'}
                            # data = {'subscriber_id': subscriber_id, 'tag_name': tag_name}
                            # response = requests.post(manychat_api_url, headers=headers, json=data)
                            # if response.status_code == 200 and response.json().get('status') == 'success':
                            #     logger.info(f"Successfully set tag '{tag_name}' for subscriber_id: {subscriber_id}")
                            # else:
                            #     logger.error(f"Failed to set tag '{tag_name}'. Response: {response.text}")
                            #     raise Exception(f"Failed to set tag via ManyChat API")

                            # Simulate successful tag setting for now
                            logger.info(
                                f"[POST-ONBOARDING] Placeholder: Tag '{tag_name}' set for subscriber_id: {subscriber_id}")

                            message_for_analytics = "Awesome, your set up check your emails!! Hey also, I can count your calories for you as well! Just take a photo of your food and give me a brief description and ill sought it out for you! I've got your recommended intake so yea, easy as! Try it if you want!"
                            self.add_ai_message_to_analytics(
                                ig_username, message_for_analytics)
                        else:
                            logger.warning(
                                f"[POST-ONBOARDING] No subscriber_id found for {ig_username}, could not set tag or update analytics.")
                    except ImportError:
                        logger.error(
                            f"Could not import set_manychat_tag from webhook_handlers. Please ensure it is defined.")
                    except Exception as e:
                        logger.error(
                            f"Failed to set ManyChat tag or update analytics: {e}")

                    return True
                else:
                    logger.error(
                        f"pe.py subprocess failed with exit code {exit_code}, not sending onboarding complete message.")
                    return False
            except Exception as e:
                logger.error(f"Playwright onboarding failed: {repr(e)}")
                return False

            # 7. Build Trainerize Program (optional, if still needed)
            program_success = await self._build_trainerize_program(client_data)
            if not program_success:
                logger.error(
                    f"Failed to build Trainerize program for {ig_username}")
                try:
                    add_todo_item(
                        ig_username=ig_username,
                        client_name=client_data['personal_info']['full_name']['value'],
                        description="Failed to automatically build Trainerize program - needs manual setup"
                    )
                except Exception as todo_error:
                    logger.error(
                        f"Failed to add todo item for failed program build: {todo_error}")
            else:
                logger.info(
                    f"Successfully built Trainerize program for {ig_username}")
                try:
                    add_todo_item(
                        ig_username=ig_username,
                        client_name=client_data['personal_info']['full_name']['value'],
                        description="Trainerize program built successfully",
                        status="completed"
                    )
                except Exception as todo_error:
                    logger.error(
                        f"Failed to add todo item for successful program build: {todo_error}")

            logger.info(
                f"Successfully completed post-onboarding process for {ig_username}")
            return True

        except Exception as e:
            logger.error(
                f"Error in post-onboarding process for {ig_username}: {e}")
            return False

    async def _analyze_conversation(self, conversation_history: List[Dict]) -> Optional[Dict]:
        """Extract client information from conversation history using Gemini."""
        try:
            # Format conversation for Gemini
            formatted_convo = self._format_conversation(conversation_history)
            logger.info(
                f"Formatted conversation with {len(conversation_history)} messages")

            prompt = f"""You are a data extraction expert. Analyze this conversation and extract client information into a STRICTLY formatted JSON object.

Conversation:
{formatted_convo}

CRITICAL INSTRUCTIONS:
1. You MUST follow the EXACT structure provided below - do not deviate or add new fields
2. All fields shown in the structure are REQUIRED - do not omit any
3. Use the EXACT same field names and nesting structure
4. For missing information, use null for the value but keep the confidence at 0
5. For gender, use ONLY "male" or "female" (lowercase)
6. For activity_level, use number 1-5 where:
   1 = sedentary
   2 = lightly active
   3 = moderately active
   4 = very active
   5 = extremely active
7. For goals, use lowercase and one of: "weight loss", "muscle gain", "maintenance"
8. For diet_type, use lowercase and one of: "none", "vegetarian", "vegan", "pescatarian", "keto"
9. All numerical values (weight, height) should be numbers, not strings
10. Dates must be in YYYY-MM-DD format
11. Phone numbers should not include spaces or international codes

EXACT Structure to Follow:
{self._get_expected_json_structure()}

CRITICAL: Your response must contain ONLY the JSON object - no other text, no markdown formatting."""

            # Get Gemini response
            logger.info("Sending prompt to Gemini")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            logger.info(
                f"Received response from Gemini ({len(response_text)} chars)")

            # Clean up the response
            response_text = response_text.replace(
                '```json', '').replace('```', '')
            response_text = response_text.strip()
            logger.info(f"Cleaned response text ({len(response_text)} chars)")

            try:
                # Try to parse the JSON response
                data = json.loads(response_text)
                logger.info("Successfully parsed JSON response")

                # Validate required sections
                required_sections = ['personal_info', 'physical_info',
                                     'dietary_info', 'training_info', 'general_info']
                missing_sections = [
                    section for section in required_sections if section not in data]
                if missing_sections:
                    logger.error(
                        f"Missing required sections: {missing_sections}")
                    return None

                # Log the extracted data for key fields
                logger.info(f"Extracted data summary:")
                logger.info(
                    f"Name: {data['personal_info'].get('full_name', {}).get('value', 'Not found')}")
                logger.info(
                    f"Email: {data['personal_info'].get('email', {}).get('value', 'Not found')}")
                logger.info(
                    f"Gender: {data['personal_info'].get('gender', {}).get('value', 'Not found')}")
                logger.info(
                    f"Weight: {data['physical_info'].get('current_weight_kg', {}).get('value', 'Not found')} kg")
                logger.info(
                    f"Goal: {data['physical_info'].get('primary_fitness_goal', {}).get('value', 'Not found')}")

                return data
            except json.JSONDecodeError as e:
                logger.error(
                    f"Invalid JSON from Gemini (after cleaning): {response_text[:200]}")
                logger.error(f"JSON error: {e}")
                error_position = int(str(e).split('char ')[-1])
                logger.error(
                    f"Error at position {error_position}: {response_text[max(0, error_position-20):error_position]}[HERE]{response_text[error_position:error_position+20]}")
                return None

        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return None

    def _map_activity_level_from_description(self, description: str) -> str:
        """Map activity level description to activity level string."""
        description = description.lower()
        if "sedentary" in description:
            return "sedentary"
        elif "light" in description:
            return "lightly_active"
        elif "moderate" in description:
            return "moderately_active"
        elif "very" in description or "intense" in description:
            return "very_active"
        elif "extreme" in description or "athlete" in description:
            return "extra_active"
        return "moderately_active"  # default

    def _calculate_nutrition(self, client_data: Dict) -> Dict:
        """Calculate nutrition needs based on client data."""
        try:
            # Log the received data structure
            logger.info(
                f"Calculating nutrition with data structure: {json.dumps(client_data, indent=2)}")

            try:
                # Extract data from the standardized structure
                weight = client_data['physical_info']['current_weight_kg']['value']
                height = client_data['physical_info']['height_cm']['value']
                activity_level = client_data['physical_info']['activity_level']['value']
                goal = client_data['physical_info']['primary_fitness_goal']['value'].lower(
                )

                logger.info(f"Extracted weight: {weight}, height: {height}")
                logger.info(f"Activity level: {activity_level}, goal: {goal}")
            except KeyError as e:
                logger.error(f"Failed to extract required data: {e}")
                return None

            # Calculate activity multiplier based on level (1-5)
            activity_multiplier = {
                1: 1.2,    # Sedentary
                2: 1.375,  # Lightly active
                3: 1.55,   # Moderately active
                4: 1.725,  # Very active
                5: 1.9     # Extra active
            }.get(activity_level, 1.55)  # Default to moderately active
            logger.info(f"Using activity multiplier: {activity_multiplier}")

            # Calculate BMR using Mifflin-St Jeor
            bmr = (10 * weight) + (6.25 * height) - (5 * 30) + \
                5  # Age defaulted to 30 if not available
            logger.info(f"Calculated BMR: {bmr}")

            tdee = bmr * activity_multiplier
            logger.info(f"Calculated TDEE: {tdee}")

            # Adjust for goal
            goal_map = {
                'weight loss': -500,
                'muscle gain': 300,
                'maintenance': 0
            }

            target_calories = tdee + goal_map.get(goal, 0)
            logger.info(f"Calculated target calories: {target_calories}")

            result = {
                'daily_calories': round(target_calories),
                'macros': {
                    'protein': round(weight * 2.2),  # 2.2g per kg
                    'carbs': round((target_calories * 0.4) / 4),  # 40% carbs
                    'fats': round((target_calories * 0.3) / 9)  # 30% fats
                }
            }

            logger.info(
                f"Final nutrition calculation: {json.dumps(result, indent=2)}")
            return result

        except Exception as e:
            logger.error(f"Error calculating nutrition: {str(e)}")
            logger.error(
                f"Client data structure: {json.dumps(client_data, indent=2)}")
            return None

    async def _generate_meal_plan(self, nutrition_data: Dict, client_data: Dict) -> Dict:
        """Generate meal plan using Gemini."""
        try:
            # Calculate meal times based on workout schedule
            workout_time = self._get_workout_time(client_data['training_info'])
            meal_times = self._calculate_meal_times(workout_time)

            # Format regular meals they like
            regular_meals = client_data['dietary_info']['regular_meals']
            preferred_meals = []
            if regular_meals:
                if regular_meals.get('breakfast', {}).get('value'):
                    preferred_meals.extend(
                        [f"Breakfast: {regular_meals['breakfast']['value']}"])
                if regular_meals.get('lunch', {}).get('value'):
                    preferred_meals.extend(
                        [f"Lunch: {regular_meals['lunch']['value']}"])
                if regular_meals.get('dinner', {}).get('value'):
                    preferred_meals.extend(
                        [f"Dinner: {regular_meals['dinner']['value']}"])

            prompt = f"""Create a simple two-day meal plan for a client with these requirements:

Daily Nutrition Targets:
- Calories: {nutrition_data['daily_calories']}
- Protein: {nutrition_data['macros']['protein']}g
- Carbs: {nutrition_data['macros']['carbs']}g
- Fats: {nutrition_data['macros']['fats']}g

Goal: {client_data['physical_info']['primary_fitness_goal']['value']}
Training Days: {client_data['training_info']['training_days']['value']}

Client Preferences:
- Dietary Type: {client_data['dietary_info']['diet_type']['value']}
- Foods to Avoid: {client_data['dietary_info']['disliked_foods']['value']}
- Regular Meals They Enjoy:
{chr(10).join(f"  • {meal}" for meal in preferred_meals)}

Client's workout time: {workout_time}

Please incorporate the client's preferred meals where possible while meeting the nutritional targets.

Provide ONLY two day meal plans in this exact format:

DAY 1 MEAL PLAN

Pre-workout ({meal_times['pre_workout']})
Meal: [Specific meal name]
Ingredients:
- [Ingredient 1] [exact quantity]
- [Ingredient 2] [exact quantity]
Preparation: [Simple prep steps]
Macros: [XXX calories, XXg protein, XXg carbs, XXg fats]

[Continue same format for each meal time]

Post-workout Breakfast ({meal_times['post_workout']})
Morning Snack ({meal_times['morning_snack']})
Lunch ({meal_times['lunch']})
Afternoon Snack ({meal_times['afternoon_snack']})
Dinner ({meal_times['dinner']})

DAY 2 MEAL PLAN
[Repeat exact same format as Day 1]

IMPORTANT:
1. Do not include any section headers with asterisks or hashes
2. Each meal must be a specific recipe with exact quantities
3. Include only the meal plans - no other sections
4. Keep formatting clean and simple
5. MUST include all six meals for each day, including dinner
6. Try to incorporate client's preferred meals where appropriate, adjusting portions to meet macro targets
7. All meals must comply with the client's dietary type ({client_data['dietary_info']['diet_type']['value']})"""

            response = self.model.generate_content(prompt)
            meal_plan_text = response.text.strip()

            # Verify dinner is included in both days
            day1_meals = self._extract_day_meals(meal_plan_text, "DAY 1")
            day2_meals = self._extract_day_meals(meal_plan_text, "DAY 2")

            if "Dinner" not in day1_meals or "Dinner" not in day2_meals:
                logger.warning(
                    "Dinner missing from meal plan, regenerating...")
                return await self._generate_meal_plan(nutrition_data, client_data)

            return {
                "meal_plan_text": meal_plan_text,
                "meal_times": meal_times
            }

        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            return None

    def _get_workout_time(self, training_info: Dict) -> str:
        """Extract workout time from training schedule."""
        try:
            # Get training days from the new standardized structure
            training_days = training_info['training_days']['value']

            # Default to morning workout
            default_time = '6:00 AM'

            # If we have training days info, parse it
            if training_days:
                # Convert various formats to a list of days
                if isinstance(training_days, list):
                    days = training_days
                else:
                    # Handle string formats like "Monday - Friday" or "Monday, Wednesday, Friday"
                    days = [day.strip()
                            for day in training_days.replace('-', ',').split(',')]

                logger.info(f"Extracted training days: {days}")
                return default_time

            return default_time

        except Exception as e:
            logger.error(f"Error getting workout time: {e}")
            return '6:00 AM'  # Default time if error

    def _calculate_meal_times(self, workout_time: str) -> Dict[str, str]:
        """Calculate all meal times based on workout time."""
        try:
            # Convert workout time to datetime for easier calculations
            workout_dt = datetime.strptime(workout_time, '%I:%M %p')

            # Calculate relative times
            pre_workout = (workout_dt - timedelta(minutes=30)
                           ).strftime('%I:%M %p')
            post_workout = (workout_dt + timedelta(minutes=90)
                            ).strftime('%I:%M %p')

            # Adjust other meal times based on workout time
            if workout_dt.hour < 10:  # Morning workout
                morning_snack = '10:30 AM'
                lunch = '1:00 PM'
                afternoon_snack = '4:00 PM'
                dinner = '7:00 PM'
            elif workout_dt.hour < 16:  # Afternoon workout
                morning_snack = '9:30 AM'
                lunch = '12:00 PM'
                afternoon_snack = (
                    workout_dt + timedelta(minutes=90)).strftime('%I:%M %p')
                dinner = '7:30 PM'
            else:  # Evening workout
                morning_snack = '9:30 AM'
                lunch = '12:30 PM'
                afternoon_snack = '3:30 PM'
                dinner = (workout_dt + timedelta(minutes=90)
                          ).strftime('%I:%M %p')

            return {
                'pre_workout': pre_workout,
                'post_workout': post_workout,
                'morning_snack': morning_snack,
                'lunch': lunch,
                'afternoon_snack': afternoon_snack,
                'dinner': dinner
            }
        except Exception as e:
            logger.error(f"Error calculating meal times: {e}")
            # Return default times if calculation fails
            return {
                'pre_workout': '5:30 AM',
                'post_workout': '7:30 AM',
                'morning_snack': '10:30 AM',
                'lunch': '1:00 PM',
                'afternoon_snack': '4:00 PM',
                'dinner': '7:00 PM'
            }

    def _create_meal_plan_pdf(self, meal_plan_text: str, client_data: Dict, nutrition_data: Dict) -> str:
        """Create PDF with meal plan."""
        try:
            # Create filename as 'Full Name Meal Plan.pdf' (no timestamp, spaces allowed)
            full_name = client_data['personal_info']['full_name']['value'].strip(
            )
            filename = f"{full_name} Meal Plan.pdf"
            full_path = os.path.join(PDF_OUTPUT_DIR, filename)
            logger.info(f"[MEAL PLAN PDF] Using filename: {filename}")

            # Ensure output directory exists
            os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

            # Create a canvas directly first to set PDF metadata
            c = canvas.Canvas(full_path, pagesize=A4)
            c.setTitle(
                f"Meal Plan - {client_data['personal_info']['full_name']['value']}")
            c.setAuthor("COCOS PT")
            c.setCreator("COCOS PT Meal Plan Generator")
            c.setProducer("ReportLab PDF Library")
            c.setSubject("Custom Meal Plan")

            # Save the canvas settings
            c.save()

            # Now create the actual document
            doc = SimpleDocTemplate(
                full_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Rest of your existing PDF creation code...
            styles = getSampleStyleSheet()
            story = []

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                spaceAfter=30,
                textColor=colors.HexColor("#1A237E"),
                alignment=1,
                fontName='Helvetica-Bold'
            )

            day_title_style = ParagraphStyle(
                'DayTitle',
                parent=styles['Heading2'],
                fontSize=20,
                spaceBefore=20,
                spaceAfter=20,
                textColor=colors.HexColor("#1A237E"),
                fontName='Helvetica-Bold',
                keepWithNext=True
            )

            meal_title_style = ParagraphStyle(
                'MealTitle',
                parent=styles['Heading3'],
                fontSize=16,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor("#2E3B55"),
                fontName='Helvetica-Bold',
                keepWithNext=True
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=12,
                spaceBefore=6,
                spaceAfter=6,
                leading=16
            )

            # Cover page
            if os.path.exists(LOGO_PATH):
                story.append(Image(LOGO_PATH, width=2*inch, height=2*inch))
            story.append(Spacer(1, 30))
            story.append(Paragraph("MEAL PLAN", title_style))

            # Client info box
            info_style = ParagraphStyle(
                'Info',
                parent=body_style,
                alignment=1,
                fontSize=14
            )

            client_info = f"""
            <para alignment="center">
            <b>Client:</b> {client_data['personal_info']['full_name']['value']}<br/>
            <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
            <b>Goal:</b> {client_data['physical_info']['primary_fitness_goal']['value']}
            </para>
            """
            story.append(Paragraph(client_info, info_style))

            # Targets box
            targets = f"""
            <para alignment="center" bgcolor="#F5F5F5">
            <b>Daily Targets</b><br/>
            Calories: {nutrition_data['daily_calories']}<br/>
            Protein: {nutrition_data['macros']['protein']}g<br/>
            Carbs: {nutrition_data['macros']['carbs']}g<br/>
            Fats: {nutrition_data['macros']['fats']}g
            </para>
            """
            story.append(Paragraph(targets, info_style))

            # Day 1 Meal Plan
            story.append(PageBreak())
            story.append(Paragraph("DAY 1 MEAL PLAN", day_title_style))

            # Process meals in specific order
            meal_order = [
                "Pre-workout",
                "Post-workout Breakfast",
                "Morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ]

            day1_meals = self._extract_day_meals(meal_plan_text, "DAY 1")
            for meal_type in meal_order:
                if meal_type in day1_meals:
                    meal_content = []
                    meal_content.append(Paragraph(meal_type, meal_title_style))
                    meal_content.append(
                        Paragraph(self._format_meal_content(day1_meals[meal_type]), body_style))
                    story.append(KeepTogether(meal_content))

            # Day 2 Meal Plan
            story.append(PageBreak())
            story.append(Paragraph("DAY 2 MEAL PLAN", day_title_style))

            day2_meals = self._extract_day_meals(meal_plan_text, "DAY 2")
            for meal_type in meal_order:
                if meal_type in day2_meals:
                    meal_content = []
                    meal_content.append(Paragraph(meal_type, meal_title_style))
                    meal_content.append(
                        Paragraph(self._format_meal_content(day2_meals[meal_type]), body_style))
                    story.append(KeepTogether(meal_content))

            # Build the PDF with native PDF settings
            doc.build(story)

            # Verify the file exists and is a valid PDF
            if not os.path.exists(full_path):
                logger.error(f"PDF file was not created at {full_path}")
                return None

            # Log the file size and path
            file_size = os.path.getsize(full_path)
            logger.info(
                f"Created native PDF file: {full_path} (size: {file_size} bytes)")

            return filename

        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            return None

    def _format_meal_content(self, content: str) -> str:
        """Format meal content with ingredients and instructions."""
        try:
            sections = content.split('\n')
            formatted = []

            current_section = None
            for line in sections:
                line = line.strip()
                if not line:
                    continue

                # Handle section headers
                if line.lower().startswith(('meal:', 'ingredients:', 'preparation:', 'macros:')):
                    current_section = line.lower().split(':')[0]
                    formatted.append(f"<b>{line}</b>")
                else:
                    # Format ingredients as bullet points, keep other sections as is
                    if current_section == 'ingredients':
                        if not line.startswith('•'):
                            line = f"• {line}"
                    formatted.append(line)

            return '<br/>'.join(formatted)

        except Exception as e:
            logger.error(f"Error formatting meal content: {e}")
            return content

    def _extract_day_meals(self, text: str, day_type: str) -> Dict[str, str]:
        """Extract meals for a specific day."""
        meals = {}
        try:
            # Find the section for the specific day
            day_start = text.find(day_type)
            if day_start == -1:
                return meals

            # Find the end of this day's section
            next_day = text.find("DAY", day_start + len(day_type))
            if next_day == -1:
                day_section = text[day_start:]
            else:
                day_section = text[day_start:next_day]

            # Define meal markers with their exact text
            meal_markers = [
                ("Pre-workout", "Post-workout"),
                ("Post-workout Breakfast", "Morning Snack"),
                ("Morning Snack", "Lunch"),
                ("Lunch", "Afternoon Snack"),
                ("Afternoon Snack", "Dinner"),
                ("Dinner", "DAY")  # Will catch next day or end of text
            ]

            # Extract each meal section
            for current_meal, next_meal in meal_markers:
                meal_start = day_section.find(current_meal)
                if meal_start != -1:
                    # Find the start of the next meal or end of text
                    meal_end = day_section.find(
                        next_meal, meal_start + len(current_meal))
                    if meal_end == -1:
                        meal_end = len(day_section)

                    # Extract and clean the meal content
                    meal_content = day_section[meal_start:meal_end].strip()
                    if meal_content:
                        meals[current_meal] = meal_content

            logger.info(
                f"Extracted meals for {day_type}: {list(meals.keys())}")
            if "Dinner" not in meals:
                logger.warning(f"Dinner was not found in {day_type}")

            return meals

        except Exception as e:
            logger.error(f"Error extracting {day_type} meals: {e}")
            return meals

    async def _send_to_zapier(self, client_data: Dict, nutrition_data: Dict, pdf_path: str) -> bool:
        """Send data to Zapier webhook for Trainerize onboarding."""
        try:
            # Split full name into first and last name
            full_name = client_data['personal_info']['full_name']['value']
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Determine workout type based on training location and gender
            training_location = client_data['training_info']['training_location']['value'].lower(
            )
            gender = client_data['personal_info'].get(
                'gender', {}).get('value', 'male')
            gender_prefix = "Mens" if gender.lower() == "male" else "Womens"
            workout_type = f"{gender_prefix} {'Full Gym' if 'gym' in training_location else 'At Home'}"

            # Read and prepare the PDF file
            full_pdf_path = os.path.join(PDF_OUTPUT_DIR, pdf_path)
            if not os.path.exists(full_pdf_path):
                logger.error(f"PDF file not found at {full_pdf_path}")
                return False

            # Check file size before processing
            file_size = os.path.getsize(full_pdf_path)
            if file_size > 5 * 1024 * 1024:  # 5MB limit
                logger.error(
                    f"PDF file size ({file_size} bytes) exceeds 5MB limit")
                return False

            # Read and encode the file
            with open(full_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                # Ensure proper base64 encoding with correct padding
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

            # Prepare the file data in the format Zapier expects
            file_data = {
                "content": pdf_base64,
                "name": pdf_path,
                "type": "application/pdf"
            }

            # Prepare the complete payload
            payload = {
                "client": {
                    "email": client_data['personal_info']['email']['value'],
                    "first_name": first_name,
                    "last_name": last_name
                },
                "program": {
                    "type": workout_type,
                    "nutrition": {
                        "daily_calories": nutrition_data['daily_calories'],
                        "protein": nutrition_data['macros']['protein'],
                        "carbs": nutrition_data['macros']['carbs'],
                        "fats": nutrition_data['macros']['fats']
                    }
                },
                "files": {
                    "meal_plan": file_data
                }
            }

            # Add headers for proper content type and file handling
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Log the payload structure (without the actual file content)
            payload_log = payload.copy()
            if 'files' in payload_log and 'meal_plan' in payload_log['files']:
                payload_log['files']['meal_plan']['content'] = '[BASE64_CONTENT]'
            logger.info(
                f"Sending payload to Zapier: {json.dumps(payload_log, indent=2)}")

            # Send to Zapier with timeout and proper error handling
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30  # 30 second timeout
            )

            # Handle the response
            try:
                response_data = response.json()
                if response.status_code == 200:
                    if response_data.get('status') == 'success':
                        logger.info(
                            f"Successfully sent data to Zapier for {full_name}")
                        return True
                    else:
                        logger.error(
                            f"Zapier returned error in response: {response_data}")
                        return False
                else:
                    logger.error(
                        f"Zapier request failed with status {response.status_code}: {response_data}")
                    return False
            except json.JSONDecodeError:
                logger.error(
                    f"Invalid JSON response from Zapier: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Timeout while sending data to Zapier")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while sending to Zapier: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending to Zapier: {e}")
            logger.error(f"Full error details: {str(e)}")
            return False

    @staticmethod
    def _format_conversation(conversation_history: List[Dict]) -> str:
        """Format conversation history for Gemini analysis."""
        formatted = []
        for msg in conversation_history:
            speaker = "Shannon" if msg['type'] == 'ai' else "Client"
            formatted.append(f"{speaker}: {msg['text']}")
        return "\n".join(formatted)

    @staticmethod
    def _get_expected_json_structure() -> str:
        """Return expected JSON structure for Gemini analysis."""
        return """{
    "personal_info": {
        "email": {"value": "example@email.com", "confidence": 95},
        "full_name": {"value": "John Smith", "confidence": 95},
        "phone": {"value": "0412345678", "confidence": 95},
        "birth_date": {"value": "1990-01-01", "confidence": 95},
        "gender": {"value": "male", "confidence": 95}
    },
    "physical_info": {
        "current_weight_kg": {"value": 80, "confidence": 95},
        "height_cm": {"value": 180, "confidence": 95},
        "primary_fitness_goal": {"value": "weight loss", "confidence": 95},
        "specific_weight_goal_kg": {"value": 75, "confidence": 95},
        "activity_level": {"value": 3, "confidence": 95}
    },
    "dietary_info": {
        "diet_type": {"value": "none", "confidence": 95},
        "regular_meals": {
            "breakfast": {"value": "eggs and toast", "confidence": 95},
            "lunch": {"value": "chicken and rice", "confidence": 95},
            "dinner": {"value": "fish and vegetables", "confidence": 95}
        },
        "meal_notes": {"value": "prefers high protein meals", "confidence": 95},
        "other_dietary_restrictions": {"value": "none", "confidence": 95},
        "disliked_foods": {"value": "none", "confidence": 95}
    },
    "training_info": {
        "current_routine": {"value": "gym 3x per week", "confidence": 95},
        "training_location": {"value": "gym", "confidence": 95},
        "disliked_exercises": {"value": "none", "confidence": 95},
        "liked_exercises": {"value": "squats, deadlifts", "confidence": 95},
        "training_days": {"value": "Monday, Wednesday, Friday", "confidence": 95}
    },
    "general_info": {
        "location": {"value": "Melbourne", "confidence": 95}
    }
}"""

    @staticmethod
    def _get_meal_plan_json_structure() -> str:
        """Return expected JSON structure for meal plan."""
        return """
{
    "day_1": {
        "meal_1": {
            "name": "Breakfast",
            "time": "7:00 AM",
            "foods": [
                {
                    "item": "Eggs",
                    "amount": "4 whole",
                    "macros": {"protein": 24, "carbs": 0, "fats": 20}
                }
            ],
            "total_macros": {"protein": 30, "carbs": 32, "fats": 23},
            "calories": 455
        }
    }
    // ... rest of structure as defined in plan ...
}
"""

    def _get_exercise_templates(self) -> Dict:
        """Returns exercise templates for different workout types and locations."""
        return {
            "gym": {
                "back": [
                    {"name": "Wide Grip Chin Up/ Assisted Chin Up",
                        "sets": "3", "reps": "8-10"},
                    {"name": "Lat Pull Down Wide Grip",
                        "sets": "3", "reps": "10-12"},
                    {"name": "Barbell Bent Over Row", "sets": "3", "reps": "8-10"},
                    {"name": "Seated row", "sets": "3", "reps": "12-15"},
                    {"name": "Face Pulls", "sets": "3", "reps": "15-20"},
                    {"name": "Alternating Hammer Curls",
                        "sets": "3", "reps": "12-15"}
                ],
                "chest": [
                    {"name": "Barbell Bench Chest Press",
                        "sets": "4", "reps": "8-10"},
                    {"name": "Incline Dumbbell Bench press",
                        "sets": "3", "reps": "10-12"},
                    {"name": "Cable Chest fly", "sets": "3", "reps": "12-15"},
                    {"name": "Cable Bench Triceps Push Down",
                        "sets": "3", "reps": "12-15"},
                    {"name": "Rope Tricep Pushdown", "sets": "3", "reps": "15-20"}
                ],
                "legs": [
                    {"name": "Barbell Back Squat", "sets": "4", "reps": "8-10"},
                    {"name": "Bulgarian Lunge", "sets": "3", "reps": "10-12"},
                    {"name": "Dumbbell Romanian Deadlifts",
                        "sets": "3", "reps": "10-12"},
                    {"name": "Leg Extensions", "sets": "3", "reps": "15-20"},
                    {"name": "Lying Leg Curl", "sets": "3", "reps": "15-20"}
                ],
                "shoulders": [
                    {"name": "Standing Shoulder Press",
                        "sets": "4", "reps": "8-10"},
                    {"name": "Lateral Raise", "sets": "3", "reps": "12-15"},
                    {"name": "Face Pulls", "sets": "3", "reps": "15-20"},
                    {"name": "Deltoid Lateral Raise",
                        "sets": "3", "reps": "12-15"},
                    {"name": "Cable Y Rows", "sets": "3", "reps": "12-15"}
                ],
                "arms": [
                    {"name": "Easy Curl Bar Bicep Curls",
                        "sets": "3", "reps": "10-12"},
                    {"name": "Cable Skull Crusher", "sets": "3", "reps": "10-12"},
                    {"name": "Alternating Hammer Curls",
                        "sets": "3", "reps": "12-15"},
                    {"name": "Rope Tricep Pushdown", "sets": "3", "reps": "12-15"},
                    {"name": "Concentrated Bicep Curls",
                        "sets": "3", "reps": "15-20"}
                ]
            },
            "home": {
                "full_body": [
                    {"name": "Push Up", "sets": "3", "reps": "10-15"},
                    {"name": "Body Weight Squats", "sets": "3", "reps": "15-20"},
                    {"name": "Plank", "sets": "3", "reps": "30-45 seconds"},
                    {"name": "Walking Lunges", "sets": "3", "reps": "12 each leg"},
                    {"name": "Close Grip Push Ups", "sets": "3", "reps": "10-15"}
                ]
            }
        }

    def _design_workout_program(self, client_data: Dict) -> Dict:
        """
        Designs a workout program based on client data and preferences.
        Returns a structure matching BuildProgramRequest format.
        """
        try:
            # Extract relevant information
            training_location = client_data['training_info']['training_location']['value'].lower(
            )
            liked_exercises = client_data['training_info']['liked_exercises']['value'].lower(
            ).split(', ')
            training_days_raw = client_data['training_info']['training_days']['value']
            goal = client_data['physical_info']['primary_fitness_goal']['value'].lower(
            )
            full_name = client_data['personal_info']['full_name']['value']

            # Determine number of training days
            if '-' in training_days_raw:  # Format: "Monday - Friday"
                start_day, end_day = [d.strip().lower()
                                      for d in training_days_raw.split('-')]
                weekdays = ['monday', 'tuesday', 'wednesday',
                            'thursday', 'friday', 'saturday', 'sunday']
                start_idx = weekdays.index(start_day)
                end_idx = weekdays.index(end_day)
                # Handle wrap-around (e.g., "Friday - Monday")
                if end_idx < start_idx:
                    end_idx += 7
                num_training_days = end_idx - start_idx + 1
            else:  # Format: "Monday, Wednesday, Friday"
                num_training_days = len([d.strip()
                                        for d in training_days_raw.split(',')])

            logger.info(
                f"Calculated {num_training_days} training days from '{training_days_raw}'")

            # Get exercise templates
            templates = self._get_exercise_templates()

            # Default to 5-day split for gym workouts unless explicitly fewer days specified
            if training_location == "gym":
                if num_training_days < 3:
                    split_type = "3_day_split"
                    program_name = f"{full_name}'s 3 Day Split - {goal.title()} Focus"
                    workout_types = ["back", "chest", "legs"]
                else:
                    # Default to 5-day split
                    split_type = "5_day_split"
                    program_name = f"{full_name}'s 5 Day Split - {goal.title()} Focus"
                    workout_types = ["back", "chest",
                                     "legs", "shoulders", "arms"]
            else:  # home workouts
                split_type = "full_body"
                program_name = f"{full_name}'s Home Workout - {goal.title()} Focus"
                # Max 3 days for home workouts
                workout_types = ["full_body"] * min(num_training_days, 3)

            logger.info(
                f"Selected program type: {split_type} with {len(workout_types)} workouts")

            # Build workout definitions
            workout_definitions = []
            for day_type in workout_types:
                # Get template exercises for this day
                template_exercises = templates[training_location][day_type]

                # Modify sets/reps based on goal
                exercises_list = []
                for exercise in template_exercises:
                    modified_exercise = exercise.copy()

                    # Adjust sets/reps based on goal
                    if goal == "weight loss":
                        # Higher reps, moderate weight
                        reps = modified_exercise['reps'].split(
                            '-')[1]  # Use higher end of range
                        modified_exercise['reps'] = reps
                    elif goal == "muscle gain":
                        # More sets, moderate reps
                        modified_exercise['sets'] = str(
                            int(modified_exercise['sets']) + 1)
                        reps = modified_exercise['reps'].split(
                            '-')[0]  # Use lower end of range
                        modified_exercise['reps'] = reps

                    # Prioritize liked exercises if mentioned
                    if any(liked in exercise['name'].lower() for liked in liked_exercises):
                        # Add an extra set for exercises they enjoy
                        modified_exercise['sets'] = str(
                            int(modified_exercise['sets']) + 1)

                    exercises_list.append(modified_exercise)

                workout_def = {
                    "day_type": day_type,
                    "exercises_list": exercises_list
                }
                workout_definitions.append(workout_def)

            # Create the final program request structure
            program_request = {
                "client_name": full_name,
                "program_name": program_name,
                "workout_definitions": workout_definitions
            }

            logger.info(f"Designed workout program for {full_name}:")
            logger.info(f"Program type: {split_type}")
            logger.info(f"Number of workouts: {len(workout_definitions)}")
            logger.info(f"Goal focus: {goal}")
            logger.info(f"Training days: {training_days_raw}")
            logger.info(f"Location: {training_location}")

            return program_request

        except Exception as e:
            logger.error(f"Error designing workout program: {e}")
            return None

    async def _build_trainerize_program(self, client_data: Dict) -> bool:
        """
        Builds a Trainerize program for the client using Playwright automation.
        """
        try:
            # Design the program
            program_request = self._design_workout_program(client_data)
            if not program_request:
                logger.error("Failed to design workout program")
                return False

            # Map client_data to Playwright onboarding fields
            pw_client_data = {
                "coach_email": "shannonbirch@cocospersonaltraining.com",
                "coach_password": "cyywp7nyk2",
                "email": client_data['personal_info']['email']['value'],
                "first_name": client_data['personal_info']['full_name']['value'].split(' ')[0],
                "last_name": client_data['personal_info']['full_name']['value'].split(' ')[1] if len(client_data['personal_info']['full_name']['value'].split(' ')) > 1 else "",
                "program_name": f"{client_data['personal_info']['full_name']['value']}'s Program",
                "training_days": client_data['training_info']['training_days']['value'],
                "workout_program": program_request  # Pass the designed program to Playwright
            }

            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    logger.info(
                        f"Starting Playwright automation attempt {retry_count + 1}")
                    # Run the Playwright automation
                    process = await asyncio.create_subprocess_exec(
                        PYTHON_EXE,
                        "test_minimal.py",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await process.communicate()

                    logger.info(
                        f"Playwright stdout: {stdout.decode(errors='replace')}")
                    logger.info(
                        f"Playwright stderr: {stderr.decode(errors='replace')}")

                    if process.returncode == 0:
                        logger.info(
                            "Successfully completed Playwright automation")
                        return True
                    else:
                        logger.error(
                            f"Playwright automation failed with return code {process.returncode}")
                        retry_count += 1
                        await asyncio.sleep(5)  # Wait before retrying

                except Exception as e:
                    logger.error(
                        f"Error during Playwright automation (attempt {retry_count + 1}): {str(e)}")
                    retry_count += 1
                    await asyncio.sleep(5)

            logger.error(
                f"Failed to complete Playwright automation after {max_retries} attempts")
            return False

        except Exception as e:
            logger.error(f"Error in _build_trainerize_program: {str(e)}")
            return False

    def _launch_onboarding_subprocess_and_wait(self, client_data, meal_plan_pdf_path):
        """Launch pe.py as a subprocess, passing client_data and meal_plan_pdf_path as arguments, and wait for it to finish. Returns exit code."""
        import sys
        import json
        import os
        import subprocess
        try:
            client_data_json = json.dumps(client_data)
            script_path = os.path.join(os.path.dirname(__file__), "pe.py")
            command = [
                sys.executable,
                script_path,
                client_data_json,
                meal_plan_pdf_path
            ]
            process = subprocess.run(command)
            logger.info("pe.py subprocess finished for %s with exit code %s",
                        client_data.get('email', 'unknown'), process.returncode)
            return process.returncode
        except Exception as e:
            logger.error(f"Failed to launch pe.py subprocess: {e}")
            return -1

    def save_workout_program_to_analytics(self, ig_username, workout_program):
        analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        import json
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            analytics_data = {"conversations": {}}
        # Find or create user
        user_id = None
        for uid, user_data in analytics_data.get("conversations", {}).items():
            metrics = user_data.get("metrics", {})
            if metrics.get("ig_username", "").lower() == ig_username.lower():
                user_id = uid
                break
        if not user_id:
            # Create new user entry
            user_id = ig_username
            analytics_data["conversations"][user_id] = {
                "metrics": {"ig_username": ig_username}}
        analytics_data["conversations"][user_id]["metrics"]["workout_program"] = workout_program
        with open(analytics_file_path, "w") as f:
            json.dump(analytics_data, f, indent=2)

    def save_meal_plan_to_analytics(self, ig_username, meal_plan_data):
        analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        import json
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            analytics_data = {"conversations": {}}
        # Find or create user
        user_id = None
        for uid, user_data in analytics_data.get("conversations", {}).items():
            metrics = user_data.get("metrics", {})
            if metrics.get("ig_username", "").lower() == ig_username.lower():
                user_id = uid
                break
        if not user_id:
            # Create new user entry
            user_id = ig_username
            analytics_data["conversations"][user_id] = {
                "metrics": {"ig_username": ig_username}}
        analytics_data["conversations"][user_id]["metrics"]["meal_plan"] = meal_plan_data
        with open(analytics_file_path, "w") as f:
            json.dump(analytics_data, f, indent=2)

    def add_ai_message_to_analytics(self, ig_username, message_text):
        analytics_file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        import json
        import datetime
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(
                f"Analytics file not found or corrupt at {analytics_file_path}, cannot add message.")
            return

        user_id = None
        user_data_entry = None
        for uid, user_entry in analytics_data.get("conversations", {}).items():
            # Check both root uid and metrics for ig_username
            if uid == ig_username or user_entry.get("metrics", {}).get("ig_username", "").lower() == ig_username.lower():
                user_id = uid
                user_data_entry = user_entry
                break

        if not user_id or not user_data_entry:
            logger.warning(
                f"Could not find user {ig_username} in analytics to add message history.")
            return

        # Ensure metrics dictionary exists
        if "metrics" not in user_data_entry:
            logger.warning(
                f"Metrics dictionary missing for user {ig_username}. Creating it.")
            user_data_entry["metrics"] = {}

        metrics_dict = user_data_entry["metrics"]

        # Ensure conversation_history exists *within metrics*
        if "conversation_history" not in metrics_dict:
            metrics_dict["conversation_history"] = []

        # Append the new AI message to the history *within metrics*
        new_message = {
            "type": "ai",
            "text": message_text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        metrics_dict["conversation_history"].append(new_message)
        logger.info(
            f"Appended AI message to conversation history within metrics for {ig_username}")

        # Save the updated analytics data
        try:
            with open(analytics_file_path, "w") as f:
                json.dump(analytics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save updated analytics data: {e}")

# Example usage:
# handler = PostOnboardingHandler(gemini_api_key="YOUR_API_KEY")
# asyncio.run(handler.process_onboarding_completion("test_user", []))
