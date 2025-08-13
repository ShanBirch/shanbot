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
# Add HttpError for specific error catching
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
import io
import tempfile
import shutil
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

# Gemini Model Names
GEMINI_MODEL_PRIMARY = "gemini-2.5-pro-exp-03-25"
GEMINI_MODEL_FALLBACK_1 = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_MODEL_FALLBACK_2 = "gemini-2.0-flash"

# Retry Parameters
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds


class PostOnboardingHandler:
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.webhook_url = "https://hooks.zapier.com/hooks/catch/17459466/2ni82qv/"
        self.google_drive_folder_id = "YOUR_GOOGLE_DRIVE_FOLDER_ID"  # Add your folder ID here
        genai.configure(api_key=self.gemini_api_key)
        # Model is now set per call with fallback
        # self.model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')

        # Initialize Google Drive service
        try:
            # Use service account credentials
            # credentials = service_account.Credentials.from_service_account_file(
            #     'path/to/your/service-account-key.json',  # Add your service account key path
            #     scopes=['https://www.googleapis.com/auth/drive.file']
            # )
            # self.drive_service = build('drive', 'v3', credentials=credentials)
            # logger.info("Successfully initialized Google Drive service")
            logger.info(
                "Google Drive service initialization is currently commented out.")
            self.drive_service = None  # Explicitly set to None
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.drive_service = None

    async def process_onboarding_completion(self, ig_username: str, subscriber_id: str, conversation_history: List[Dict]) -> bool:
        logger.info(
            f"[Onboarding BG Task] Starting for ig_username: '{ig_username}', subscriber_id: '{subscriber_id}'")
        try:
            # 1. Extract onboarding data
            logger.info(
                f"[Onboarding BG Task] Starting data extraction for {ig_username}/{subscriber_id} from {len(conversation_history)} messages")
            client_data = await self._analyze_conversation(conversation_history)
            if not client_data:
                logger.error(
                    f"[Onboarding BG Task] Failed to extract client data for {ig_username}/{subscriber_id}")
                return False

            # Ensure client_data has subscriber_id for later use
            client_data['personal_info']['subscriber_id'] = {
                "value": subscriber_id, "confidence": 100}

            logger.info(
                f"[Onboarding BG Task] Successfully extracted data for {ig_username}: {json.dumps(client_data, indent=2)}")

            # 2. Calculate nutrition needs
            nutrition_data = self._calculate_nutrition(client_data)
            if not nutrition_data:
                logger.error(
                    f"[Onboarding BG Task] Failed to calculate nutrition data for {ig_username}/{subscriber_id}")
                return False

            logger.info(
                f"[Onboarding BG Task] Calculated nutrition data: {json.dumps(nutrition_data, indent=2)}")

            # 3. Generate meal plan
            meal_plan = await self._generate_meal_plan(nutrition_data, client_data)
            if not meal_plan:
                logger.error(
                    f"[Onboarding BG Task] Failed to generate meal plan for {ig_username}/{subscriber_id}")
                return False

            logger.info(
                f"[Onboarding BG Task] Generated meal plan with {len(meal_plan.get('meal_plan_text', '').split())} words")

            # 3b. Generate workout program structure
            program_request = self._design_workout_program(client_data)
            if not program_request:
                logger.error(
                    f"[Onboarding BG Task] Failed to design workout program for {ig_username}/{subscriber_id}")
                return False

            # 4. Create PDF
            pdf_path = self._create_meal_plan_pdf(
                meal_plan['meal_plan_text'], client_data, nutrition_data)
            if not pdf_path:
                logger.error(
                    f"[Onboarding BG Task] Failed to create PDF for {ig_username}/{subscriber_id}")
                return False

            logger.info(f"[Onboarding BG Task] Created PDF at: {pdf_path}")

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
                    f"[Onboarding BG Task] Workout program to be sent to pe.py: {json.dumps(client_data.get('workout_program', {}), indent=2)}")
                meal_plan_pdf_full_path = os.path.join(
                    PDF_OUTPUT_DIR, pdf_path)
                logger.info(
                    f"[Onboarding BG Task] Starting Playwright onboarding for {pw_client_data['email']}...")
                # Before launching pe.py subprocess, save the workout program
                self.save_workout_program_to_analytics(
                    ig_username, program_request, subscriber_id)
                # Save meal plan to analytics for record-keeping before launching subprocess
                self.save_meal_plan_to_analytics(
                    ig_username, meal_plan, subscriber_id)

                # --- Add AI message to history BEFORE launching subprocess ---
                logger.info(
                    "[Onboarding BG Task] Skipping addition of 'starting setup' message to analytics history.")
                # --- End Add AI message ---

                # Launch onboarding in a subprocess and wait for completion
                # Ensure workout_program is included
                client_data_json = json.dumps(client_data)
                success_flags = await self._launch_onboarding_subprocess_and_wait(
                    client_data, meal_plan_pdf_full_path)

                onboarding_ok = False
                if isinstance(success_flags, dict):
                    onboarding_ok = success_flags.get("client_added_success", False) and \
                        success_flags.get("meal_plan_upload_success", False) and \
                        success_flags.get(
                            "workout_program_build_success", False)
                elif isinstance(success_flags, bool):
                    onboarding_ok = success_flags

                if onboarding_ok:
                    logger.info(
                        "Successfully completed Playwright onboarding subprocess")

                    # Add a delay to ensure everything is fully completed
                    time.sleep(5)  # Wait 5 seconds

                    # Set ManyChat tag and update analytics
                    try:
                        # Try to import the new function for setting a custom field
                        from webhook_handlers import get_user_data, set_manychat_custom_field
                        # Ensure get_user_data can also use subscriber_id if needed
                        _, metrics_dict, * \
                            _ = get_user_data(ig_username, subscriber_id)

                        logger.info(
                            f"[POST-ONBOARDING] Fetched subscriber_id for ManyChat update: '{subscriber_id}'")

                        if subscriber_id:
                            field_name_onboarding = "onboarding"  # Keep for logging clarity
                            field_id_onboarding = 12993480       # The ID you provided
                            field_value_onboarding = True
                            logger.info(
                                f"[POST-ONBOARDING] Attempting to set custom field by ID '{field_id_onboarding}' (Name: '{field_name_onboarding}') to {field_value_onboarding} for subscriber_id: {subscriber_id}")

                            custom_field_set_successfully = await set_manychat_custom_field(
                                subscriber_id,
                                field_name=field_name_onboarding,  # Pass name for logging/fallback
                                field_value=field_value_onboarding,
                                field_id=field_id_onboarding      # Pass the ID here
                            )

                            if custom_field_set_successfully:
                                logger.info(
                                    f"[POST-ONBOARDING] Successfully set custom field '{field_name_onboarding}' to '{field_value_onboarding}' for subscriber_id: {subscriber_id}")

                                # --- Set trial_week_1 to True in analytics ---
                                try:
                                    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                                    logger.info(
                                        f"[AnalyticsUpdate] Attempting to set trial_week_1=True for SID: {subscriber_id} in {analytics_file_path}")

                                    with open(analytics_file_path, "r") as f:
                                        analytics_data = json.load(f)

                                    user_id_to_update = None
                                    user_metrics_to_update = None

                                    # Prioritize search by subscriber_id
                                    for uid, u_data in analytics_data.get("conversations", {}).items():
                                        metrics = u_data.get("metrics", {})
                                        if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                                            user_id_to_update = uid
                                            user_metrics_to_update = metrics
                                            logger.info(
                                                f"[AnalyticsUpdate] Found user by subscriber_id '{subscriber_id}' (JSON key: '{uid}') for trial_week_1 update.")
                                            break

                                    if not user_id_to_update:
                                        logger.warning(
                                            f"[AnalyticsUpdate] User not found by subscriber_id '{subscriber_id}'. Falling back to ig_username '{ig_username}' for trial_week_1 update.")
                                        for uid, u_data in analytics_data.get("conversations", {}).items():
                                            metrics = u_data.get("metrics", {})
                                            if isinstance(metrics, dict) and metrics.get("ig_username", "").lower() == ig_username.lower():
                                                user_id_to_update = uid
                                                user_metrics_to_update = metrics
                                                logger.info(
                                                    f"[AnalyticsUpdate] Found user by ig_username '{ig_username}' (JSON key: '{uid}') for trial_week_1 update.")
                                                break

                                    if user_metrics_to_update:
                                        user_metrics_to_update['trial_week_1'] = True
                                        logger.info(
                                            f"[AnalyticsUpdate] Set 'trial_week_1': True for user (JSON key: '{user_id_to_update}', SID: '{subscriber_id}').")

                                        # Also set is_onboarding to False
                                        user_metrics_to_update['is_onboarding'] = False
                                        logger.info(
                                            f"[AnalyticsUpdate] Set 'is_onboarding': False for user (JSON key: '{user_id_to_update}', SID: '{subscriber_id}').")

                                        with open(analytics_file_path, "w") as f:
                                            json.dump(
                                                analytics_data, f, indent=2)
                                        logger.info(
                                            f"[AnalyticsUpdate] Successfully saved analytics_data_good.json after setting trial_week_1 and is_onboarding.")

                                        # --- Add final confirmation message to analytics history ---
                                        final_confirmation_message = "Awesome, your set up check your emails!!  Hey also, I can count your calories for you as well! Just take a photo of your food and give me a brief description and ill sought it out for you! I've got your recommended intake so yea, easy as! Try it if you want!"
                                        self.add_ai_message_to_analytics(
                                            ig_username, subscriber_id, final_confirmation_message)
                                        logger.info(
                                            f"[AnalyticsUpdate] Added final confirmation message to analytics history for SID: {subscriber_id}.")
                                        # --- End adding final message ---

                                    else:
                                        logger.error(
                                            f"[AnalyticsUpdate] Could not find user with SID '{subscriber_id}' or IGUser '{ig_username}' to set trial_week_1.")

                                except FileNotFoundError:
                                    logger.error(
                                        f"[AnalyticsUpdate] {analytics_file_path} not found. Cannot set trial_week_1.")
                                except json.JSONDecodeError:
                                    logger.error(
                                        f"[AnalyticsUpdate] Error decoding {analytics_file_path}. Cannot set trial_week_1.")
                                except Exception as e_analytics:
                                    logger.error(
                                        f"[AnalyticsUpdate] Error setting trial_week_1 for SID {subscriber_id}: {e_analytics}", exc_info=True)
                                # --- End set trial_week_1 ---
                            else:
                                logger.warning(
                                    f"[POST-ONBOARDING] Failed to set custom field '{field_name_onboarding}' to '{field_value_onboarding}' for subscriber_id: {subscriber_id}.")

                        else:
                            logger.warning(
                                f"[POST-ONBOARDING] No subscriber_id available for '{ig_username}', could not set custom field.")
                    except ImportError:
                        logger.error(
                            f"[POST-ONBOARDING] Could not import 'set_manychat_custom_field' from 'webhook_handlers'. Please ensure it is defined. Custom field not set.")
                    except Exception as e:
                        logger.error(
                            f"[POST-ONBOARDING] Failed to set ManyChat custom field after subprocess: {e}", exc_info=True)

                    return True  # Return True because pe.py succeeded
                else:
                    logger.error(
                        f"[Onboarding BG Task] pe.py subprocess failed (flags: {success_flags}), not sending onboarding complete message.")
                    return False
            except Exception as e:
                logger.error(
                    f"[Onboarding BG Task] Playwright onboarding failed: {repr(e)}")
                return False

            # 7. Build Trainerize Program (optional, if still needed)
            # This section seems redundant now as pe.py handles it.
            # Consider removing or commenting out if pe.py is the definitive onboarding script.
            # program_success = await self._build_trainerize_program(client_data)
            # if not program_success:
            #     logger.error(
            #         f"[Onboarding BG Task] Failed to build Trainerize program for {ig_username}/{subscriber_id}")
            #     try:
            #         add_todo_item(
            #             ig_username=ig_username,
            #             client_name=client_data['personal_info']['full_name']['value'],
            #             description="Failed to automatically build Trainerize program - needs manual setup"
            #         )
            #     except Exception as todo_error:
            #         logger.error(
            #             f"[Onboarding BG Task] Failed to add todo item for failed program build: {todo_error}")
            # else:
            #     logger.info(
            #         f"[Onboarding BG Task] Successfully built Trainerize program for {ig_username}/{subscriber_id}")
            #     try:
            #         add_todo_item(
            #             ig_username=ig_username,
            #             client_name=client_data['personal_info']['full_name']['value'],
            #             description="Trainerize program built successfully",
            #             status="completed"
            #         )
            #     except Exception as todo_error:
            #         logger.error(
            #             f"[Onboarding BG Task] Failed to add todo item for successful program build: {todo_error}")

            logger.info(
                f"[Onboarding BG Task] Successfully completed post-onboarding process for {ig_username}/{subscriber_id}")
            return True

        except Exception as e:
            logger.error(
                f"[Onboarding BG Task] Error in post-onboarding process for {ig_username}/{subscriber_id}: {e}", exc_info=True)
        return False

    async def process_onboarding_with_fixed_data(self, ig_username: str, subscriber_id: str, direct_client_data: Dict, nutrition_targets_override: Dict) -> bool:
        logger.info(
            f"[Onboarding Fixed Data] Starting for ig_username: '{ig_username}', subscriber_id: '{subscriber_id}'")
        try:
            client_data = direct_client_data
            # Ensure subscriber_id is in the personal_info for consistency if not already
            if 'personal_info' in client_data and 'subscriber_id' not in client_data['personal_info']:
                client_data['personal_info']['subscriber_id'] = {
                    "value": subscriber_id, "confidence": 100}
            elif 'personal_info' not in client_data:  # Should not happen with molly.py
                client_data['personal_info'] = {'subscriber_id': {
                    "value": subscriber_id, "confidence": 100}}

            logger.info(
                f"[Onboarding Fixed Data] Using direct client data for {ig_username}: {json.dumps(client_data, indent=2)}")

            # 2. Use overridden nutrition needs
            nutrition_data = nutrition_targets_override
            if not nutrition_data:
                logger.error(
                    f"[Onboarding Fixed Data] Nutrition override data is missing for {ig_username}/{subscriber_id}")
                return False
            logger.info(
                f"[Onboarding Fixed Data] Using overridden nutrition data: {json.dumps(nutrition_data, indent=2)}")

            # 3. Generate meal plan
            meal_plan = await self._generate_meal_plan(nutrition_data, client_data)
            if not meal_plan:
                logger.error(
                    f"[Onboarding Fixed Data] Failed to generate meal plan for {ig_username}/{subscriber_id}")
                return False
            logger.info(
                f"[Onboarding Fixed Data] Generated meal plan with {len(meal_plan.get('meal_plan_text', '').split())} words")

            # 3b. Generate workout program structure
            program_request = self._design_workout_program(client_data)
            if not program_request:
                logger.error(
                    f"[Onboarding Fixed Data] Failed to design workout program for {ig_username}/{subscriber_id}")
                return False

            # 4. Create PDF
            pdf_path = self._create_meal_plan_pdf(
                meal_plan['meal_plan_text'], client_data, nutrition_data)
            if not pdf_path:
                logger.error(
                    f"[Onboarding Fixed Data] Failed to create PDF for {ig_username}/{subscriber_id}")
                return False
            logger.info(f"[Onboarding Fixed Data] Created PDF at: {pdf_path}")

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
                    "workout_program": program_request
                }
                client_data['workout_program'] = program_request
                logger.info(
                    f"[Onboarding Fixed Data] Workout program to be sent to pe.py: {json.dumps(client_data.get('workout_program', {}), indent=2)}")
                meal_plan_pdf_full_path = os.path.join(
                    PDF_OUTPUT_DIR, pdf_path)
                logger.info(
                    f"[Onboarding Fixed Data] Starting Playwright onboarding for {pw_client_data['email']}...")

                self.save_workout_program_to_analytics(
                    ig_username, program_request, subscriber_id)
                self.save_meal_plan_to_analytics(
                    ig_username, meal_plan, subscriber_id)

                logger.info(
                    "[Onboarding Fixed Data] Skipping addition of 'starting setup' message to analytics history.")

                # Ensure this is the complete and correct client_data
                client_data_json = json.dumps(client_data)
                success_flags = await self._launch_onboarding_subprocess_and_wait(
                    client_data, meal_plan_pdf_full_path)

                if success_flags['client_added_success'] and success_flags['meal_plan_upload_success'] and success_flags['workout_program_build_success']:
                    logger.info(
                        "Successfully completed Playwright onboarding subprocess (Fixed Data)")
                    time.sleep(5)

                    try:
                        from webhook_handlers import get_user_data, set_manychat_custom_field
                        # Use subscriber_id directly as it's a primary identifier
                        _, metrics_dict_mc, * \
                            _ = get_user_data(
                                ig_username=ig_username, subscriber_id=subscriber_id)

                        logger.info(
                            f"[POST-ONBOARDING Fixed Data] Fetched subscriber_id for ManyChat update: '{subscriber_id}'")

                        if subscriber_id:
                            field_name_onboarding = "onboarding"
                            field_id_onboarding = 12993480
                            field_value_onboarding = True
                            logger.info(
                                f"[POST-ONBOARDING Fixed Data] Attempting to set custom field by ID '{field_id_onboarding}' (Name: '{field_name_onboarding}') to {field_value_onboarding} for subscriber_id: {subscriber_id}")

                            custom_field_set_successfully = await set_manychat_custom_field(
                                subscriber_id,
                                field_name=field_name_onboarding,
                                field_value=field_value_onboarding,
                                field_id=field_id_onboarding
                            )

                            if custom_field_set_successfully:
                                logger.info(
                                    f"[POST-ONBOARDING Fixed Data] Successfully set custom field '{field_name_onboarding}' to '{field_value_onboarding}' for subscriber_id: {subscriber_id}")
                                try:
                                    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                                    logger.info(
                                        f"[AnalyticsUpdate Fixed Data] Attempting to set trial_week_1=True for SID: {subscriber_id} in {analytics_file_path}")
                                    with open(analytics_file_path, "r") as f:
                                        analytics_data = json.load(f)
                                    user_id_to_update = None
                                    user_metrics_to_update = None

                                    for uid, u_data in analytics_data.get("conversations", {}).items():
                                        metrics = u_data.get("metrics", {})
                                        if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                                            user_id_to_update = uid
                                            user_metrics_to_update = metrics
                                            logger.info(
                                                f"[AnalyticsUpdate Fixed Data] Found user by subscriber_id '{subscriber_id}' (JSON key: '{uid}') for trial_week_1 update.")
                                            break
                                    if not user_id_to_update and ig_username:  # Fallback to ig_username if subscriber_id not found
                                        logger.warning(
                                            f"[AnalyticsUpdate Fixed Data] User not found by subscriber_id '{subscriber_id}'. Falling back to ig_username '{ig_username}' for trial_week_1 update.")
                                        for uid, u_data in analytics_data.get("conversations", {}).items():
                                            metrics = u_data.get("metrics", {})
                                            if isinstance(metrics, dict) and metrics.get("ig_username", "").lower() == ig_username.lower():
                                                user_id_to_update = uid
                                                user_metrics_to_update = metrics
                                                logger.info(
                                                    f"[AnalyticsUpdate Fixed Data] Found user by ig_username '{ig_username}' (JSON key: '{uid}') for trial_week_1 update.")
                                                break

                                    if user_metrics_to_update:  # If user found by either id
                                        user_metrics_to_update['trial_week_1'] = True
                                        logger.info(
                                            f"[AnalyticsUpdate Fixed Data] Set 'trial_week_1': True for user (JSON key: '{user_id_to_update}', SID: '{subscriber_id}').")
                                        user_metrics_to_update['is_onboarding'] = False
                                        logger.info(
                                            f"[AnalyticsUpdate Fixed Data] Set 'is_onboarding': False for user (JSON key: '{user_id_to_update}', SID: '{subscriber_id}').")
                                        with open(analytics_file_path, "w") as f:
                                            json.dump(
                                                analytics_data, f, indent=2)
                                        logger.info(
                                            f"[AnalyticsUpdate Fixed Data] Successfully saved analytics_data_good.json after setting trial_week_1 and is_onboarding.")
                                        final_confirmation_message = "Awesome, your set up check your emails!!  Hey also, I can count your calories for you as well! Just take a photo of your food and give me a brief description and ill sought it out for you! I've got your recommended intake so yea, easy as! Try it if you want!"
                                        self.add_ai_message_to_analytics(
                                            ig_username, subscriber_id, final_confirmation_message)  # ig_username needed here
                                        logger.info(
                                            f"[AnalyticsUpdate Fixed Data] Added final confirmation message to analytics history for SID: {subscriber_id}.")
                                    else:
                                        logger.error(
                                            f"[AnalyticsUpdate Fixed Data] Could not find user with SID '{subscriber_id}' or IGUser '{ig_username}' to set trial_week_1.")
                                except FileNotFoundError:
                                    logger.error(
                                        f"[AnalyticsUpdate Fixed Data] {analytics_file_path} not found. Cannot set trial_week_1.")
                                except json.JSONDecodeError:
                                    logger.error(
                                        f"[AnalyticsUpdate Fixed Data] Error decoding {analytics_file_path}. Cannot set trial_week_1.")
                                except Exception as e_analytics:
                                    logger.error(
                                        f"[AnalyticsUpdate Fixed Data] Error setting trial_week_1 for SID {subscriber_id}: {e_analytics}", exc_info=True)
                            else:
                                logger.warning(
                                    f"[POST-ONBOARDING Fixed Data] Failed to set custom field '{field_name_onboarding}' for subscriber_id: {subscriber_id}.")
                        else:  # subscriber_id was missing for ManyChat
                            logger.warning(
                                f"[POST-ONBOARDING Fixed Data] No subscriber_id available, could not set ManyChat custom field.")
                    except ImportError:
                        logger.error(
                            f"[POST-ONBOARDING Fixed Data] Could not import from 'webhook_handlers'. Custom field not set.")
                    except Exception as e:
                        logger.error(
                            f"[POST-ONBOARDING Fixed Data] Failed to set ManyChat custom field after subprocess: {e}", exc_info=True)
                    return True
                else:  # pe.py subprocess failed
                    logger.error(
                        f"[Onboarding Fixed Data] pe.py subprocess failed (flags: {success_flags}), not sending onboarding complete message.")
                    # Add a todo if pe.py fails
                    try:
                        add_todo_item(
                            ig_username=ig_username,
                            client_name=client_data.get('personal_info', {}).get(
                                'full_name', {}).get('value', 'Unknown Client from Fixed Data'),
                            task_description=f"Onboarding subprocess (pe.py) FAILED for FIXED DATA ({ig_username}, SID: {subscriber_id}) with flags {success_flags}. Needs manual check.",
                            status="pending"
                        )
                    except Exception as todo_error:
                        logger.error(
                            f"Failed to add todo item for failed fixed data subprocess: {todo_error}")
                    return False
            except Exception as e:
                logger.error(
                    f"[Onboarding Fixed Data] Playwright onboarding failed: {repr(e)}", exc_info=True)
                return False

            logger.info(
                f"[Onboarding Fixed Data] Successfully completed post-onboarding process for {ig_username}/{subscriber_id}")
            return True

        except Exception as e:
            logger.error(
                f"[Onboarding Fixed Data] Error in post-onboarding process for {ig_username}/{subscriber_id}: {e}", exc_info=True)
            return False

    async def _call_gemini_with_fallback_and_retry(self, prompt: str, purpose: str) -> Optional[str]:
        """Calls Gemini API with defined models, fallback, and retries."""
        models_to_try = [
            GEMINI_MODEL_PRIMARY,
            GEMINI_MODEL_FALLBACK_1,
            GEMINI_MODEL_FALLBACK_2
        ]

        for model_name in models_to_try:
            logger.info(
                f"[GeminiCall - {purpose}] Attempting model: {model_name}")
            model = genai.GenerativeModel(model_name)
            for attempt in range(MAX_RETRIES):
                try:
                    response = await asyncio.to_thread(model.generate_content, prompt)
                    # Ensure response.text is accessed safely
                    if response and hasattr(response, 'text') and response.text:
                        logger.info(
                            f"[GeminiCall - {purpose}] Successfully got response from {model_name} on attempt {attempt + 1}")
                        return response.text.strip()
                    elif response and response.prompt_feedback and response.prompt_feedback.block_reason:
                        logger.error(
                            f"[GeminiCall - {purpose}] Content blocked by {model_name} on attempt {attempt + 1}. Reason: {response.prompt_feedback.block_reason}")
                        # If blocked, don't retry this model, try next model in the list
                        break
                    else:
                        logger.warning(
                            f"[GeminiCall - {purpose}] Received empty or unexpected response from {model_name} on attempt {attempt + 1}. Response: {response}")
                        # Treat as a failure for this attempt, retry or move to next model

                except ResourceExhausted as e:
                    logger.warning(
                        f"[GeminiCall - {purpose}] Quota exhausted for {model_name} on attempt {attempt + 1}. Error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        logger.info(
                            f"[GeminiCall - {purpose}] Retrying in {RETRY_DELAY} seconds...")
                        await asyncio.sleep(RETRY_DELAY)
                    else:
                        logger.error(
                            f"[GeminiCall - {purpose}] Max retries reached for {model_name} due to ResourceExhausted.")
                        break  # Stop retrying this model, try next model
                except (InternalServerError, ServiceUnavailable) as e:
                    logger.warning(
                        f"[GeminiCall - {purpose}] Server error with {model_name} on attempt {attempt + 1}. Error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        logger.info(
                            f"[GeminiCall - {purpose}] Retrying in {RETRY_DELAY} seconds...")
                        await asyncio.sleep(RETRY_DELAY)
                    else:
                        logger.error(
                            f"[GeminiCall - {purpose}] Max retries reached for {model_name} due to server error.")
                        break  # Stop retrying this model, try next model
                except Exception as e:
                    logger.error(
                        f"[GeminiCall - {purpose}] Unexpected error with {model_name} on attempt {attempt + 1}: {e}", exc_info=True)
                    # For unexpected errors, stop retrying this model and move to the next
                    break
            logger.warning(
                f"[GeminiCall - {purpose}] All retries failed for model {model_name}. Trying next model if available.")

        logger.error(
            f"[GeminiCall - {purpose}] All models and retries failed for prompt.")
        return None

    async def _analyze_conversation(self, conversation_history: List[Dict]) -> Optional[Dict]:
        """Extract client information from conversation history using Gemini with fallback/retry."""
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

            # Get Gemini response using the new helper
            logger.info(
                "[DataExtraction] Calling Gemini for data extraction...")
            response_text = await self._call_gemini_with_fallback_and_retry(prompt, "data_extraction")

            if not response_text:
                logger.error(
                    "[DataExtraction] Failed to get response from Gemini for data extraction after all retries/fallbacks.")
                return None

            logger.info(
                f"[DataExtraction] Received response from Gemini ({len(response_text)} chars)")

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
                goal = client_data['physical_info']['primary_fitness_goal']['value']

                # --- Add Check for None values ---
                if weight is None or height is None or activity_level is None or goal is None:
                    logger.error(
                        f"Missing essential data for nutrition calculation: weight={weight}, height={height}, activity={activity_level}, goal={goal}")
                    return None

                goal = goal.lower()  # Convert goal to lowercase after checking it's not None
                # --- End Check ---

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

    async def _generate_meal_plan(self, nutrition_data: Dict, client_data: Dict) -> Optional[Dict]:
        """Generate meal plan using Gemini with fallback/retry."""
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

            prompt = f"""Create a simple three-day meal plan for a client with these requirements:

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

Provide ONLY three day meal plans in this exact format:

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

DAY 3 MEAL PLAN
[Repeat exact same format as Day 1]

IMPORTANT:
1. Do not include any section headers with asterisks or hashes
2. Each meal must be a specific recipe with exact quantities
3. Include only the meal plans - no other sections
4. Keep formatting clean and simple
5. MUST include all six meals for each day, including dinner
6. Try to incorporate client's preferred meals where appropriate, adjusting portions to meet macro targets
7. All meals must comply with the client's dietary type ({client_data['dietary_info']['diet_type']['value']})"""

            logger.info(
                "[MealPlanGen] Calling Gemini for 3-day meal plan generation...")
            meal_plan_text = await self._call_gemini_with_fallback_and_retry(prompt, "meal_plan_generation")

            if not meal_plan_text:
                logger.error(
                    "[MealPlanGen] Failed to get response from Gemini for 3-day meal plan generation after all retries/fallbacks.")
                return None

            logger.info(
                f"[MealPlanGen] Received 3-day meal plan text ({len(meal_plan_text)} chars)")

            # Verify dinner is included in all three days
            day1_meals = self._extract_day_meals(meal_plan_text, "DAY 1")
            day2_meals = self._extract_day_meals(meal_plan_text, "DAY 2")
            day3_meals = self._extract_day_meals(meal_plan_text, "DAY 3")

            if "Dinner" not in day1_meals or "Dinner" not in day2_meals or "Dinner" not in day3_meals:
                logger.warning(
                    "Dinner missing from one or more days in the 3-day meal plan, regenerating...")
                # Recursive call to regenerate
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

            # Day 3 Meal Plan
            story.append(PageBreak())
            story.append(Paragraph("DAY 3 MEAL PLAN", day_title_style))

            day3_meals = self._extract_day_meals(meal_plan_text, "DAY 3")
            for meal_type in meal_order:
                if meal_type in day3_meals:
                    meal_content = []
                    meal_content.append(Paragraph(meal_type, meal_title_style))
                    meal_content.append(
                        Paragraph(self._format_meal_content(day3_meals[meal_type]), body_style))
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
                "pull": [
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
                "push": [
                    {"name": "Barbell Bench Chest Press",
                        "sets": "4", "reps": "8-10"},
                    {"name": "Incline Dumbbell Bench press",
                        "sets": "3", "reps": "10-12"},
                    {"name": "Cable Chest fly", "sets": "3", "reps": "12-15"},
                    {"name": "Standing Shoulder Press", "sets": "3",
                        "reps": "8-10"},  # Moved from separate shoulders
                    # Moved from separate shoulders
                    {"name": "Lateral Raise", "sets": "3", "reps": "12-15"},
                    {"name": "Cable Bench Triceps Push Down",
                        "sets": "3", "reps": "12-15"},
                    {"name": "Rope Tricep Pushdown", "sets": "3", "reps": "15-20"}
                ],
                "legs_heavy": [
                    {"name": "Barbell Back Squat", "sets": "4", "reps": "6-8"},
                    {"name": "Barbell Hip Thrusts",
                        "sets": "4", "reps": "8-10"},  # Added
                    # Added
                    {"name": "Romanian Deadlifts (RDLs)",
                     "sets": "3", "reps": "8-10"},
                    {"name": "Leg Press", "sets": "3", "reps": "8-10"},
                    {"name": "Hamstring Curl Machine",
                        "sets": "3", "reps": "10-12"}
                ],
                "legs_light": [
                    {"name": "Goblet Squat", "sets": "3", "reps": "12-15"},
                    {"name": "Dumbbell Lunges", "sets": "3",
                        "reps": "10-12 per leg"},
                    {"name": "Glute Hyperextensions", "sets": "3",
                        "reps": "15-20"},  # Added for preference
                    {"name": "Leg Extensions Machine",
                        "sets": "3", "reps": "15-20"},
                    {"name": "Cable Pull Throughs", "sets": "3", "reps": "15-20"}
                ],
                # Removed old "legs", "shoulders", "arms" as they are incorporated or replaced
                "core": [
                    {"name": "Plank", "sets": "3", "reps": "30-60 seconds"},
                    {"name": "Leg Raises", "sets": "3", "reps": "15-20"},
                    {"name": "Russian Twists", "sets": "3",
                        "reps": "15-20 per side"},
                    {"name": "Cable Crunches", "sets": "3", "reps": "15-20"}
                ]
            },
            "home": {  # Home workouts can remain simpler or be expanded later if needed
                "full_body": [
                    {"name": "Push Up", "sets": "3", "reps": "10-15"},
                    {"name": "Body Weight Squats", "sets": "3", "reps": "15-20"},
                    {"name": "Plank", "sets": "3", "reps": "30-45 seconds"},
                    {"name": "Walking Lunges", "sets": "3", "reps": "12 each leg"},
                    {"name": "Close Grip Push Ups", "sets": "3", "reps": "10-15"}
                ],
                "core": [
                    {"name": "Crunches", "sets": "3", "reps": "20-25"},
                    {"name": "Bird Dog", "sets": "3", "reps": "10-12 per side"},
                    {"name": "Glute Bridges", "sets": "3", "reps": "15-20"}
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

            templates = self._get_exercise_templates()
            program_name = f"{full_name}'s Custom Program - {goal.title()} Focus"
            workout_definitions = []

            if "gym" in training_location and num_training_days == 6:
                # Molly's specific 6-day split
                # Legs (Heavy), Pull, Push, Legs (Light), Pull, Legs (Heavy or Medium)
                # For simplicity, let's alternate Heavy/Light for the 3 leg days.
                # We'll use one Push and two Pulls.
                day_sequence = [
                    "legs_heavy",
                    "pull",
                    "push",
                    "legs_light",
                    "pull",
                    "legs_heavy"  # Could be a third variation, e.g., legs_medium if defined
                ]
                program_name = f"{full_name}'s 6-Day Split - {goal.title()} Focus"
                logger.info(
                    f"Applying Molly's 6-day gym split: {day_sequence}")

                for day_type_main in day_sequence:
                    if day_type_main not in templates["gym"]:
                        logger.error(
                            f"Day type '{day_type_main}' not found in gym templates. Skipping.")
                        continue

                    current_day_exercises = list(
                        templates["gym"][day_type_main])  # Make a copy

                    # Add core exercises to this day
                    if "core" in templates["gym"]:
                        current_day_exercises.extend(
                            list(templates["gym"]["core"]))  # Extend with a copy
                    else:
                        logger.warning(
                            "Core template not found for gym. Core exercises will not be added.")

                    workout_def = {
                        "day_type": f"{day_type_main.replace('_', ' ').title()} + Core",
                        "exercises_list": current_day_exercises
                    }
                    workout_definitions.append(workout_def)

            elif "gym" in training_location:  # General gym splits for other day counts
                if num_training_days >= 5:
                    split_type = "5_day_split"  # PPL + Upper/Lower or similar
                    # Example: Pull, Push, Legs, Upper, Lower
                    # Needs specific 5-day sequence defined if we want to be precise
                    # Simplified example
                    workout_types_main = ["pull", "push",
                                          "legs_heavy", "pull", "legs_light"]
                    program_name = f"{full_name}'s 5 Day Gym Split - {goal.title()} Focus"
                elif num_training_days == 4:
                    split_type = "4_day_split"  # Upper/Lower
                    # Example: Upper, Lower, Upper, Lower
                    workout_types_main = [
                        "push", "pull", "legs_heavy", "legs_light"]
                    program_name = f"{full_name}'s 4 Day Gym Split - {goal.title()} Focus"
                elif num_training_days <= 3:
                    split_type = "3_day_split"  # Full body or Push/Pull/Legs
                    workout_types_main = ["push", "pull", "legs_heavy"]
                    program_name = f"{full_name}'s 3 Day Gym Split - {goal.title()} Focus"
                else:  # Default to 3 day if something is off
                    workout_types_main = ["push", "pull", "legs_heavy"]
                    program_name = f"{full_name}'s 3 Day Gym Split (Default) - {goal.title()} Focus"

                logger.info(
                    f"Applying general gym split: {split_type} with main types: {workout_types_main}")
                for day_type_main in workout_types_main:
                    if day_type_main not in templates["gym"]:
                        logger.error(
                            f"Day type '{day_type_main}' not found in gym templates. Skipping.")
                        continue
                    current_day_exercises = list(
                        templates["gym"][day_type_main])
                    if "core" in templates["gym"]:
                        current_day_exercises.extend(
                            list(templates["gym"]["core"]))
                    workout_def = {
                        "day_type": f"{day_type_main.replace('_', ' ').title()} + Core",
                        "exercises_list": current_day_exercises
                    }
                    workout_definitions.append(workout_def)

            else:  # home workouts (assuming full_body approach for now)
                program_name = f"{full_name}'s Home Workout - {goal.title()} Focus"
                # Max 3 distinct full body days for home workouts, add core to each
                num_home_workouts = min(num_training_days, 3)
                logger.info(
                    f"Applying home workout plan for {num_home_workouts} days.")
                for i in range(num_home_workouts):
                    current_day_exercises = list(
                        templates["home"]["full_body"])
                    if "core" in templates["home"]:
                        current_day_exercises.extend(
                            list(templates["home"]["core"]))
                    workout_def = {
                        "day_type": f"Full Body Day {i+1} + Core",
                        "exercises_list": current_day_exercises
                    }
                    workout_definitions.append(workout_def)

            # The modification of sets/reps based on goal and liked exercises can be complex
            # and might be better handled by Gemini directly if we pass it the base template
            # For now, this example doesn't include the dynamic set/rep adjustment per exercise
            # based on goal, as it was in the original _design_workout_program.
            # This part needs to be re-integrated carefully if desired.
            # The liked_exercises check for adding sets also needs re-integration.
            # This example focuses on the new 6-day structure for Molly.

            final_program_request = {
                "client_name": full_name,
                "program_name": program_name,
                "workout_definitions": workout_definitions
            }

            logger.info(
                f"Designed workout program for {full_name}: Program Name: {program_name}")
            logger.info(
                f"Number of workouts defined: {len(workout_definitions)}")
            for i, wd in enumerate(workout_definitions):
                logger.info(
                    f"  Day {i+1}: {wd['day_type']}, Exercises: {len(wd['exercises_list'])}")

            return final_program_request

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

    async def _launch_onboarding_subprocess_and_wait(self, client_data, meal_plan_pdf_full_path) -> Dict[str, bool]:
        """Launch the pe.py script as a subprocess and wait for it to complete, capturing its output."""
        script_path = os.path.join(os.path.dirname(__file__), 'pe.py')

        # Prepare client_data as a JSON string argument
        # Ensure it's safe for command line by stripping newlines if any
        client_data_json_str = json.dumps(client_data).replace('\n', ' ')

        # Initialize success flags to False
        client_added_successfully = False
        meal_plan_uploaded_successfully = False
        workout_program_built_successfully = False

        command = [
            sys.executable,  # Use the current Python interpreter
            script_path,
            client_data_json_str,
            meal_plan_pdf_full_path
        ]

        logger.info(
            f"[PE.PY SUBPROCESS] Executing command: {' '.join(command[:2])} ... (args omitted for brevity)")

        try:
            # Preferred: run asynchronously via asyncio on supported event loops
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
        except NotImplementedError:
            # Windows ProactorEventLoop cannot spawn subprocesses – fallback to sync run in thread
            logger.warning(
                "[PE.PY SUBPROCESS] Event loop does not support subprocess exec. Falling back to blocking subprocess.run() in a thread")

            def _run_blocking():
                return subprocess.run(command, capture_output=True, text=True, check=False)

            completed = await asyncio.to_thread(_run_blocking)
            stdout = completed.stdout.encode()
            stderr = completed.stderr.encode()
            # For consistency with the async path
            process = completed  # type: ignore

        # Decode output
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        logger.info(f"[PE.PY SUBPROCESS] stdout: {stdout_str}")
        if stderr_str:
            logger.error(f"[PE.PY SUBPROCESS] stderr: {stderr_str}")

        # Parse output for success flags
        if "CLIENT_ADDED_SUCCESS: True" in stdout_str:
            client_added_successfully = True
        if "MEAL_PLAN_UPLOAD_SUCCESS: True" in stdout_str:
            meal_plan_uploaded_successfully = True
        if "WORKOUT_PROGRAM_BUILD_SUCCESS: True" in stdout_str:
            workout_program_built_successfully = True

        logger.info(
            f"[PE.PY SUBPROCESS] Client Added: {client_added_successfully}, Meal Plan: {meal_plan_uploaded_successfully}, Workout Program: {workout_program_built_successfully}")

        return {
            "client_added_success": client_added_successfully,
            "meal_plan_upload_success": meal_plan_uploaded_successfully,
            "workout_program_build_success": workout_program_built_successfully
        }

    def save_workout_program_to_analytics(self, ig_username, workout_program, subscriber_id):
        logger.info(
            f"[AnalyticsSave - WorkoutProgram] Attempting for subscriber_id: '{subscriber_id}', ig_username: '{ig_username}'")
        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
        import json  # Ensure json is imported
        try:
            with open(analytics_file_path, "r", encoding="utf-8") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(
                f"[AnalyticsSave - WorkoutProgram] File not found or JSON error ({e}). Initializing new data.")
            analytics_data = {"conversations": {}}

        user_id_key_to_use = None
        conversations = analytics_data.get("conversations", {})

        # Priority 1: Find user by subscriber_id in metrics
        if subscriber_id:
            for uid, user_data_loop in conversations.items():
                # Add check for user_data_loop being a dictionary
                if isinstance(user_data_loop, dict):
                    metrics = user_data_loop.get("metrics", {})
                    if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                        user_id_key_to_use = uid
                        logger.info(
                            f"[AnalyticsSave - WorkoutProgram] Found user by subscriber_id '{subscriber_id}' in metrics. JSON key: '{uid}'.")
                        break
                else:
                    logger.warning(
                        f"[AnalyticsSave - WorkoutProgram] Skipping non-dict entry for user ID '{uid}' during subscriber_id search.")

        # Priority 2: Find user by ig_username in metrics (if not found by subscriber_id)
        if not user_id_key_to_use and ig_username:
            for uid, user_data_loop in conversations.items():
                # Add check for user_data_loop being a dictionary
                if isinstance(user_data_loop, dict):
                    metrics = user_data_loop.get("metrics", {})
                    if isinstance(metrics, dict) and metrics.get("ig_username", "").lower() == ig_username.lower():
                        user_id_key_to_use = uid
                        logger.info(
                            f"[AnalyticsSave - WorkoutProgram] Found user by ig_username '{ig_username}' in metrics. JSON key: '{uid}'.")
                        break
                else:
                    logger.warning(
                        f"[AnalyticsSave - WorkoutProgram] Skipping non-dict entry for user ID '{uid}' during ig_username search.")

        # Priority 3: Find user by top-level key matching subscriber_id (if still not found)
        if not user_id_key_to_use and subscriber_id and str(subscriber_id) in conversations:
            user_id_key_to_use = str(subscriber_id)
            logger.info(
                f"[AnalyticsSave - WorkoutProgram] Found user by top-level key matching subscriber_id '{subscriber_id}'.")

        # Priority 4: Find user by top-level key matching ig_username (if still not found)
        if not user_id_key_to_use and ig_username and ig_username in conversations:
            user_id_key_to_use = ig_username
            logger.info(
                f"[AnalyticsSave - WorkoutProgram] Found user by top-level key matching ig_username '{ig_username}'.")

        # If user still not found, create a new entry using subscriber_id as key if available, else ig_username
        if not user_id_key_to_use:
            if subscriber_id:
                user_id_key_to_use = str(subscriber_id)
                logger.info(
                    f"[AnalyticsSave - WorkoutProgram] User not found. Creating new entry with subscriber_id '{user_id_key_to_use}' as key.")
            elif ig_username:
                user_id_key_to_use = ig_username
                logger.info(
                    f"[AnalyticsSave - WorkoutProgram] User not found by SID. Creating new entry with ig_username '{user_id_key_to_use}' as key.")
            else:
                logger.error(
                    "[AnalyticsSave - WorkoutProgram] Cannot save workout program: No ig_username or subscriber_id provided to create a new user entry.")
                return

        # Ensure the user entry and metrics dictionary exist
        user_entry = conversations.setdefault(user_id_key_to_use, {})
        metrics_dict = user_entry.setdefault("metrics", {})

        # Update/set the workout program and identifiers
        metrics_dict["workout_program"] = workout_program
        if subscriber_id:  # Always store/update subscriber_id if available
            metrics_dict["subscriber_id"] = str(subscriber_id)
        if ig_username:  # Always store/update ig_username if available
            metrics_dict["ig_username"] = ig_username

        logger.info(
            f"[AnalyticsSave - WorkoutProgram] User '{user_id_key_to_use}' metrics updated with workout program. SID: '{metrics_dict.get('subscriber_id')}', IG: '{metrics_dict.get('ig_username')}'")

        try:
            with open(analytics_file_path, "w", encoding="utf-8") as f:
                json.dump(analytics_data, f, indent=2)
            logger.info(
                f"[AnalyticsSave - WorkoutProgram] Successfully saved workout program for user: '{user_id_key_to_use}' (SID: {subscriber_id}, IG: {ig_username})")
        except Exception as e:
            logger.error(
                f"[AnalyticsSave - WorkoutProgram] Error writing analytics file for user '{user_id_key_to_use}': {e}")

    def save_meal_plan_to_analytics(self, ig_username, meal_plan_data, subscriber_id):
        logger.info(
            f"[AnalyticsSave - MealPlan] Attempting for subscriber_id: '{subscriber_id}', ig_username: '{ig_username}'")
        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
        import json  # Ensure json is imported
        try:
            with open(analytics_file_path, "r", encoding="utf-8") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(
                f"[AnalyticsSave - MealPlan] File not found or JSON error ({e}). Initializing new data.")
            analytics_data = {"conversations": {}}

        user_id_key_to_use = None
        conversations = analytics_data.get("conversations", {})

        # Priority 1: Find user by subscriber_id in metrics
        if subscriber_id:
            for uid, user_data_loop in conversations.items():
                # Add check for user_data_loop being a dictionary
                if isinstance(user_data_loop, dict):
                    metrics = user_data_loop.get("metrics", {})
                    if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                        user_id_key_to_use = uid
                        logger.info(
                            f"[AnalyticsSave - MealPlan] Found user by subscriber_id '{subscriber_id}' in metrics. JSON key: '{uid}'.")
                        break
                else:
                    logger.warning(
                        f"[AnalyticsSave - MealPlan] Skipping non-dict entry for user ID '{uid}' during subscriber_id search.")

        # Priority 2: Find user by ig_username in metrics (if not found by subscriber_id)
        if not user_id_key_to_use and ig_username:
            for uid, user_data_loop in conversations.items():
                # Add check for user_data_loop being a dictionary
                if isinstance(user_data_loop, dict):
                    metrics = user_data_loop.get("metrics", {})
                    if isinstance(metrics, dict) and metrics.get("ig_username", "").lower() == ig_username.lower():
                        user_id_key_to_use = uid
                        logger.info(
                            f"[AnalyticsSave - MealPlan] Found user by ig_username '{ig_username}' in metrics. JSON key: '{uid}'.")
                        break
                else:
                    logger.warning(
                        f"[AnalyticsSave - MealPlan] Skipping non-dict entry for user ID '{uid}' during ig_username search.")

        # Priority 3: Find user by top-level key matching subscriber_id (if still not found)
        if not user_id_key_to_use and subscriber_id and str(subscriber_id) in conversations:
            user_id_key_to_use = str(subscriber_id)
            logger.info(
                f"[AnalyticsSave - MealPlan] Found user by top-level key matching subscriber_id '{subscriber_id}'.")

        # Priority 4: Find user by top-level key matching ig_username (if still not found)
        if not user_id_key_to_use and ig_username and ig_username in conversations:
            user_id_key_to_use = ig_username
            logger.info(
                f"[AnalyticsSave - MealPlan] Found user by top-level key matching ig_username '{ig_username}'.")

        # If user still not found, create a new entry using subscriber_id as key if available, else ig_username
        if not user_id_key_to_use:
            if subscriber_id:
                user_id_key_to_use = str(subscriber_id)
                logger.info(
                    f"[AnalyticsSave - MealPlan] User not found. Creating new entry with subscriber_id '{user_id_key_to_use}' as key.")
            elif ig_username:
                user_id_key_to_use = ig_username
                logger.info(
                    f"[AnalyticsSave - MealPlan] User not found by SID. Creating new entry with ig_username '{user_id_key_to_use}' as key.")
            else:
                logger.error(
                    "[AnalyticsSave - MealPlan] Cannot save meal plan: No ig_username or subscriber_id provided to create a new user entry.")
                return

        # Ensure the user entry and metrics dictionary exist
        user_entry = conversations.setdefault(user_id_key_to_use, {})
        metrics_dict = user_entry.setdefault("metrics", {})

        # Update/set the meal plan and identifiers
        metrics_dict["meal_plan"] = meal_plan_data
        if subscriber_id:  # Always store/update subscriber_id if available
            metrics_dict["subscriber_id"] = str(subscriber_id)
        if ig_username:  # Always store/update ig_username if available
            metrics_dict["ig_username"] = ig_username

        logger.info(
            f"[AnalyticsSave - MealPlan] User '{user_id_key_to_use}' metrics updated with meal plan. SID: '{metrics_dict.get('subscriber_id')}', IG: '{metrics_dict.get('ig_username')}'")

        try:
            with open(analytics_file_path, "w", encoding="utf-8") as f:
                json.dump(analytics_data, f, indent=2)
            logger.info(
                f"[AnalyticsSave - MealPlan] Successfully saved meal plan for user: '{user_id_key_to_use}' (SID: {subscriber_id}, IG: {ig_username})")
        except Exception as e:
            logger.error(
                f"[AnalyticsSave - MealPlan] Error writing analytics file for user '{user_id_key_to_use}': {e}")

    def add_ai_message_to_analytics(self, ig_username, subscriber_id, message_text):
        logger.info(
            f"[AnalyticsSaveAttempt] Called for subscriber_id: '{subscriber_id}' (ig_username: '{ig_username}') with message: '{message_text[:50]}...'")
        analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
        import json
        import datetime

        try:
            logger.info(
                f"[AnalyticsSaveAttempt] Reading analytics file: {analytics_file_path}")
            with open(analytics_file_path, "r", encoding="utf-8") as f:
                analytics_data = json.load(f)
            logger.info(
                f"[AnalyticsSaveAttempt] Successfully read analytics file.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(
                f"[AnalyticsSaveAttempt] Analytics file not found or corrupt at {analytics_file_path}. Error: {e}. Cannot add message.")
            return

        user_id_found = None
        user_data_entry = None

        logger.info(
            f"[AnalyticsSaveAttempt] Searching for user by subscriber_id '{subscriber_id}' in analytics data...")
        current_conversations = analytics_data.get("conversations", {})

        # --- Primary Search: By subscriber_id within metrics ---
        for uid, user_entry in current_conversations.items():
            metrics = user_entry.get("metrics", {})
            # Ensure comparison is string vs string
            if isinstance(metrics, dict) and metrics.get("subscriber_id") == str(subscriber_id):
                user_id_found = uid
                user_data_entry = user_entry
                logger.info(
                    f"[AnalyticsSaveAttempt] Found user by subscriber_id. User ID in JSON: '{uid}'")
                break

        # --- Fallback Search: By ig_username (if subscriber_id search failed) ---
        if not user_id_found:
            logger.warning(
                f"[AnalyticsSaveAttempt] User not found by subscriber_id '{subscriber_id}'. Falling back to ig_username '{ig_username}'...")
            for uid, user_entry in current_conversations.items():
                metrics = user_entry.get("metrics", {})
                if isinstance(metrics, dict) and metrics.get("ig_username", "").lower() == ig_username.lower():
                    user_id_found = uid
                    user_data_entry = user_entry
                    logger.info(
                        f"[AnalyticsSaveAttempt] Found user by ig_username after subscriber_id fallback. User ID in JSON: '{uid}'")
                    break
                # Also check if the top-level key matches ig_username (legacy?)
                elif uid.lower() == ig_username.lower():
                    user_id_found = uid
                    user_data_entry = user_entry
                    logger.info(
                        f"[AnalyticsSaveAttempt] Found user by top-level key matching ig_username '{ig_username}' after subscriber_id fallback.")
                    break

        # --- Handle Not Found ---
        if not user_id_found or user_data_entry is None:
            logger.error(
                f"[AnalyticsSaveAttempt] Could not find user by subscriber_id '{subscriber_id}' or ig_username '{ig_username}'. Message not added.")
            return

        if "metrics" not in user_data_entry:
            logger.warning(
                f"[AnalyticsSaveAttempt] Metrics dictionary missing for user '{user_id_found}'. Creating it.")
            user_data_entry["metrics"] = {}

        metrics_dict = user_data_entry["metrics"]

        if "conversation_history" not in metrics_dict:
            logger.info(
                f"[AnalyticsSaveAttempt] 'conversation_history' list missing in metrics for user '{user_id_found}'. Creating it.")
            metrics_dict["conversation_history"] = []

        logger.info(
            f"[AnalyticsSaveAttempt] Current conversation_history length for '{user_id_found}': {len(metrics_dict['conversation_history'])}")

        new_message = {
            "type": "ai",
            "text": message_text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        metrics_dict["conversation_history"].append(new_message)
        logger.info(
            f"[AnalyticsSaveAttempt] Appended AI message to conversation_history in metrics for '{user_id_found}'. New length: {len(metrics_dict['conversation_history'])}")

        try:
            logger.info(
                f"[AnalyticsSaveAttempt] Attempting to write updated analytics data to {analytics_file_path} for user '{user_id_found}'...")
            with open(analytics_file_path, "w", encoding="utf-8") as f:
                json.dump(analytics_data, f, indent=2)
            logger.info(
                f"[AnalyticsSaveAttempt] Successfully wrote updated analytics to {analytics_file_path} after adding AI message for '{user_id_found}'.")
        except Exception as e:
            logger.error(
                f"[AnalyticsSaveAttempt] Failed to save updated analytics data for '{user_id_found}'. Error: {e}")

# Example usage:
# handler = PostOnboardingHandler(gemini_api_key="YOUR_API_KEY")
# asyncio.run(handler.process_onboarding_completion("test_user", "test_subscriber", []))


if __name__ == "__main__":
    print("[DEBUG] post_onboarding_handler.py executed directly as __main__.")

    # --- Jo Schiavetta's details ---
    JO_IG_USERNAME_DIRECT = "jo_schiavetta_test"  # Placeholder
    JO_SUBSCRIBER_ID_DIRECT = "jo_subscriber_id_test"  # Placeholder
    JO_EMAIL_DIRECT = "jo.schiavetta@example.com"  # Placeholder
    JO_FULL_NAME_DIRECT = "Jo Schiavetta"
    JO_PHONE_DIRECT = "0472866895"
    JO_BIRTH_DATE_DIRECT = "1970-12-08"
    JO_GENDER_DIRECT = "female"
    # Placeholder, assuming an average weight for height for BMR calc, actual weight loss is target driven.
    JO_WEIGHT_DIRECT = 70
    JO_HEIGHT_DIRECT = 165
    JO_GOAL_DIRECT = "weight loss"
    JO_SPECIFIC_WEIGHT_GOAL_DIRECT = None
    JO_ACTIVITY_LEVEL_DIRECT = 1  # Sedentary
    JO_LOCATION_DIRECT = None
    JO_DIET_TYPE_DIRECT = "none"  # Omnivore
    JO_REGULAR_MEALS_NOTES = """
Prefers 2-3 meals per day.
Protein shake around 10 AM.
Lunch: Half chicken breast, lentils, veggies, sauerkraut, olive oil & vinegar.
Dinner: Meat, vegetables, salad, OR sandwiches (egg salad/tuna).
Likes: Yogurt with berries, all meats (pork, white meat, tuna, chicken), cauliflower soup.
Treats: Dark chocolate (2 rows) OR scotch finger biscuits.
Wine: 1-2 glasses/night, 2 nights/wk (not for meal plan).
    """
    JO_MEAL_NOTES_DIRECT = JO_REGULAR_MEALS_NOTES  # Consolidating for clarity
    JO_OTHER_DIETARY_RESTRICTIONS_DIRECT = "none"
    JO_DISLIKED_FOODS_DIRECT = "none specified"  # Assuming none for now
    JO_CURRENT_ROUTINE_DIRECT = "Sedentary, planning to start"
    JO_TRAINING_LOCATION_DIRECT = "home"  # Assuming home for now
    JO_DISLIKED_EXERCISES_DIRECT = "none specified"
    JO_LIKED_EXERCISES_DIRECT = "none specified"
    JO_TRAINING_DAYS_DIRECT = "Flexible, starting out"  # Placeholder
    # Re-use existing key
    JO_GEMINI_API_KEY_DIRECT = "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"

    JO_CUSTOM_NUTRITION_TARGETS_DIRECT = {
        'daily_calories': 1000,
        # Approx for 1000 cals
        'macros': {'protein': 100, 'carbs': 75, 'fats': 33}
    }

    # Using all caps for client_data fields to match Elena's example for clarity
    jo_client_data_direct = {
        'personal_info': {
            'email': {'value': JO_EMAIL_DIRECT, 'confidence': 100},
            'full_name': {'value': JO_FULL_NAME_DIRECT, 'confidence': 100},
            'phone': {'value': JO_PHONE_DIRECT, 'confidence': 100},
            'birth_date': {'value': JO_BIRTH_DATE_DIRECT, 'confidence': 100},
            'gender': {'value': JO_GENDER_DIRECT, 'confidence': 100},
            'subscriber_id': {'value': JO_SUBSCRIBER_ID_DIRECT, 'confidence': 100}
        },
        'physical_info': {
            # Placeholder weight
            'current_weight_kg': {'value': JO_WEIGHT_DIRECT, 'confidence': 100},
            'height_cm': {'value': JO_HEIGHT_DIRECT, 'confidence': 100},
            'primary_fitness_goal': {'value': JO_GOAL_DIRECT, 'confidence': 100},
            'specific_weight_goal_kg': {'value': JO_SPECIFIC_WEIGHT_GOAL_DIRECT, 'confidence': 0},
            'activity_level': {'value': JO_ACTIVITY_LEVEL_DIRECT, 'confidence': 100}
        },
        'dietary_info': {
            'diet_type': {'value': JO_DIET_TYPE_DIRECT, 'confidence': 100},
            'regular_meals': {  # Store some structured preferences here
                'breakfast': {'value': "Protein shake around 10 AM. Yogurt + berries also liked.", 'confidence': 95},
                'lunch': {'value': "Half a chicken breast - lentils, veggies, sauerkraut - olive oil vinegar.", 'confidence': 95},
                'dinner': {'value': "Meat - vegetables - salad - or sandwiches - egg salad or tuna sandwich. Cauliflower soup liked.", 'confidence': 95}
            },
            'meal_notes': {'value': JO_MEAL_NOTES_DIRECT, 'confidence': 95},
            'other_dietary_restrictions': {'value': JO_OTHER_DIETARY_RESTRICTIONS_DIRECT, 'confidence': 95},
            'disliked_foods': {'value': JO_DISLIKED_FOODS_DIRECT, 'confidence': 95}
        },
        'training_info': {
            'current_routine': {'value': JO_CURRENT_ROUTINE_DIRECT, 'confidence': 95},
            'training_location': {'value': JO_TRAINING_LOCATION_DIRECT, 'confidence': 100},
            'disliked_exercises': {'value': JO_DISLIKED_EXERCISES_DIRECT, 'confidence': 95},
            'liked_exercises': {'value': JO_LIKED_EXERCISES_DIRECT, 'confidence': 100},
            'training_days': {'value': JO_TRAINING_DAYS_DIRECT, 'confidence': 100}
        },
        'general_info': {
            'location': {'value': JO_LOCATION_DIRECT, 'confidence': 0}
        }
        # No 'workout_program' or 'custom_meal_plan_text_for_analytics' here as we are generating it
    }

    async def run_jo_schiavetta_meal_plan_generation():
        print(f"=== Generating Meal Plan PDF for {JO_FULL_NAME_DIRECT} ===")
        if sys.platform.startswith("win") and not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())

        handler = PostOnboardingHandler(
            gemini_api_key=JO_GEMINI_API_KEY_DIRECT)

        jo_client_data_direct['dietary_info'][
            'meal_notes'] = "CRITICAL: Client requires a meal plan with ONLY 2-3 meals per day (e.g., shake, lunch, dinner). " + JO_MEAL_NOTES_DIRECT

        print(
            f"[DEBUG] Generating meal plan for {JO_FULL_NAME_DIRECT} with nutrition: {JO_CUSTOM_NUTRITION_TARGETS_DIRECT}")
        print(
            f"[DEBUG] Client data dietary notes: {jo_client_data_direct['dietary_info']['meal_notes']}")

        meal_plan_data = await handler._generate_meal_plan(
            nutrition_data=JO_CUSTOM_NUTRITION_TARGETS_DIRECT,
            client_data=jo_client_data_direct
        )

        if not meal_plan_data or not meal_plan_data.get("meal_plan_text"):
            print(
                f"Failed to generate meal plan text for {JO_FULL_NAME_DIRECT}.")
            return

        print(
            f"Successfully generated meal plan text for {JO_FULL_NAME_DIRECT}.")
        # Corrected commented line:
        # print(f"Meal Plan Text:\n{meal_plan_data['meal_plan_text'][:500]}...") # Optionally print snippet

        # 2. Create PDF
        # Corrected indentation for this block:
        pdf_filename = handler._create_meal_plan_pdf(
            meal_plan_text=meal_plan_data['meal_plan_text'],
            client_data=jo_client_data_direct,
            nutrition_data=JO_CUSTOM_NUTRITION_TARGETS_DIRECT
        )

        if pdf_filename:
            full_pdf_path = os.path.join(PDF_OUTPUT_DIR, pdf_filename)
            print(
                f"Successfully created meal plan PDF for {JO_FULL_NAME_DIRECT} at: {full_pdf_path}")
        else:
            print(f"Failed to create meal plan PDF for {JO_FULL_NAME_DIRECT}.")

        print(f"--- {JO_FULL_NAME_DIRECT}'s Meal Plan Generation Complete ---")
        # Script will continue and not exit here unless you manually stop it.

    # Comment out Elena's run if you only want to run Jo's
    # print("[DEBUG] Attempting to run Elena Green onboarding logic...")
    # asyncio.run(run_elena_onboarding_directly())

    # Run Jo Schiavetta's meal plan generation
    # Corrected indentation for this block:
    print(f"[DEBUG] Attempting to generate meal plan for Jo Schiavetta...")
    asyncio.run(run_jo_schiavetta_meal_plan_generation())
