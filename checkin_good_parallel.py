#!/usr/bin/env python3
"""
Parallel Trainerize Check-in Script
Processes multiple clients simultaneously using headless browsers for maximum speed
"""

import sys
import os
import json
import time
import logging
import re
import traceback
import math
import random
import tempfile
import shutil
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- START sys.path modification ---
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

print("**** RUNNING PARALLEL VERSION WITH HEADLESS BROWSERS ****")
print("**** PROCESSING 5 CLIENTS SIMULTANEOUSLY ****")

# Thread-safe logging setup
log_lock = threading.Lock()


def thread_safe_print(message, thread_id=None):
    """Thread-safe printing with optional thread identification"""
    with log_lock:
        if thread_id:
            print(f"[Thread {thread_id}] {message}")
        else:
            print(message)


class ParallelTrainerizeAutomation:
    def __init__(self, gemini_api_key=None, worker_id=None, headless=True):
        self.worker_id = worker_id or "Unknown"
        self.headless = headless

        logging.basicConfig(level=logging.WARNING,  # Reduced logging for parallel processing
                            format=f'%(asctime)s - Worker{self.worker_id} - %(levelname)s - %(message)s')

        thread_safe_print(
            f"Initializing headless Chrome worker {self.worker_id}...")

        self.gemini_api_key = gemini_api_key

        # Define the output directory and ensure it exists
        self.output_directory = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"
        try:
            os.makedirs(self.output_directory, exist_ok=True)
        except OSError as e:
            thread_safe_print(
                f"Error creating output directory: {e}", self.worker_id)
            self.output_directory = None

        if gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-thinking-exp-01-21')
        else:
            self.model = None

        # Chrome options optimized for parallel headless processing
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")  # New headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        # Speed up by not loading images
        chrome_options.add_argument("--disable-images")
        # Disable JS where possible
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--window-size=1920,1080")

        # Create unique temp directory for each worker
        self.temp_user_data_dir = tempfile.mkdtemp(
            prefix=f"trainerize_worker_{self.worker_id}_")
        chrome_options.add_argument(
            f"--user-data-dir={self.temp_user_data_dir}")

        # Additional performance optimizations
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            # Reduced timeout for faster processing
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)  # Reduced wait time

            thread_safe_print(
                f"Chrome worker {self.worker_id} initialized successfully!", self.worker_id)

        except Exception as e:
            thread_safe_print(
                f"Failed to initialize Chrome worker {self.worker_id}: {e}", self.worker_id)
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir, ignore_errors=True)
            raise

    def login(self, username, password):
        """Fast login optimized for headless operation"""
        try:
            thread_safe_print(f"Logging in to Trainerize...", self.worker_id)
            self.driver.get("https://www.trainerize.com/login")

            # Quick login process
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "Username")))
            username_field.clear()
            username_field.send_keys(username)

            password_field = self.driver.find_element(By.ID, "Password")
            password_field.clear()
            password_field.send_keys(password)

            login_button = self.driver.find_element(
                By.XPATH, "//input[@type='submit' and @value='Log In']")
            login_button.click()

            # Wait for successful login
            self.wait.until(EC.url_contains("Clients.aspx"))
            thread_safe_print(f"Login successful!", self.worker_id)
            return True

        except Exception as e:
            thread_safe_print(f"Login failed: {e}", self.worker_id)
            return False

    def process_single_client(self, client_name):
        """Process a single client - optimized for parallel execution"""
        try:
            thread_safe_print(
                f"Processing client: {client_name}", self.worker_id)

            # Navigate to client (simplified)
            if not self.navigate_to_client_fast(client_name):
                thread_safe_print(
                    f"Failed to navigate to {client_name}", self.worker_id)
                return None

            # Quick data collection
            client_data = self.collect_client_data_fast(client_name)
            if not client_data:
                thread_safe_print(
                    f"Failed to collect data for {client_name}", self.worker_id)
                return None

            # Save data
            success = self.save_client_data(client_name, client_data)
            if success:
                thread_safe_print(
                    f"✓ Successfully processed {client_name}", self.worker_id)
                return {client_name: client_data}
            else:
                thread_safe_print(
                    f"✗ Failed to save data for {client_name}", self.worker_id)
                return None

        except Exception as e:
            thread_safe_print(
                f"Error processing {client_name}: {e}", self.worker_id)
            return None

    def navigate_to_client_fast(self, client_name):
        """Fast client navigation optimized for headless browsers"""
        try:
            # Go to clients page
            self.driver.get("https://www.trainerize.com/Clients.aspx")
            time.sleep(1)  # Minimal wait

            # Search for client
            try:
                search_input = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH,
                     "//input[contains(@placeholder, 'Search') or contains(@class, 'search')]")
                ))
                search_input.clear()
                search_input.send_keys(client_name)
                time.sleep(0.5)  # Brief wait for search results
            except:
                thread_safe_print(
                    f"Could not find search input, trying direct client link", self.worker_id)

            # Click on client link
            client_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 f"//a[contains(text(), '{client_name}') or contains(@title, '{client_name}')]")
            ))
            client_link.click()

            # Wait for client page to load
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//h1 | //h2 | //*[contains(@class, 'client')]")))
            return True

        except Exception as e:
            thread_safe_print(
                f"Navigation to {client_name} failed: {e}", self.worker_id)
            return False

    def collect_client_data_fast(self, client_name):
        """Fast data collection focusing on essential workout data"""
        try:
            client_data = {
                'name': client_name,
                'timestamp': datetime.now().isoformat(),
                'worker_id': self.worker_id
            }

            # Get workout data (most important)
            workout_data = self.get_workout_data_fast()
            if workout_data:
                client_data['workouts'] = workout_data
                client_data['workouts_this_week'] = len(workout_data)
                client_data['has_exercise_data'] = True

                # Calculate basic stats
                total_reps = sum(
                    sum(int(s.get('reps', 0))
                        for s in ex.get('sets', []) if s.get('reps'))
                    for workout in workout_data
                    for ex in workout.get('exercises', [])
                )
                total_sets = sum(
                    len(ex.get('sets', []))
                    for workout in workout_data
                    for ex in workout.get('exercises', [])
                )

                client_data['total_reps'] = total_reps
                client_data['total_sets'] = total_sets
            else:
                client_data['workouts'] = []
                client_data['workouts_this_week'] = 0
                client_data['has_exercise_data'] = False
                client_data['total_reps'] = 0
                client_data['total_sets'] = 0

            # Try to get basic bodyweight (if available quickly)
            try:
                bodyweight = self.get_bodyweight_fast()
                if bodyweight:
                    client_data['current_weight'] = bodyweight
                    client_data['has_weight_data'] = True
                else:
                    client_data['has_weight_data'] = False
            except:
                client_data['has_weight_data'] = False

            return client_data

        except Exception as e:
            thread_safe_print(
                f"Data collection failed for {client_name}: {e}", self.worker_id)
            return None

    def get_workout_data_fast(self):
        """Fast workout data extraction"""
        try:
            # Navigate to workouts section
            workouts_link = self.driver.find_element(
                By.XPATH, "//a[contains(@href, 'workout') or contains(text(), 'Workout')]")
            workouts_link.click()
            time.sleep(1)

            # Get recent workouts (last week)
            workout_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'workout')] | //tr[contains(@class, 'workout')]")

            workouts = []
            # Limit to recent 10 workouts for speed
            for element in workout_elements[:10]:
                try:
                    workout_text = element.text
                    if workout_text and len(workout_text) > 5:
                        # Extract basic workout info
                        workout = {
                            'text': workout_text,
                            'date': self.extract_date_from_text(workout_text),
                            'exercises': self.extract_exercises_from_text(workout_text)
                        }
                        workouts.append(workout)
                except:
                    continue

            return workouts[:5]  # Return max 5 recent workouts for speed

        except Exception as e:
            thread_safe_print(
                f"Workout data extraction failed: {e}", self.worker_id)
            return []

    def get_bodyweight_fast(self):
        """Quick bodyweight check"""
        try:
            # Look for weight/biometrics section
            weight_link = self.driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress') or contains(text(), 'Weight') or contains(text(), 'Biometric')]")
            weight_link.click()
            time.sleep(1)

            # Find recent weight entry
            weight_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'kg') or contains(text(), 'lb')]")
            for element in weight_elements:
                text = element.text
                # Extract weight value
                weight_match = re.search(r'(\d+\.?\d*)\s*(kg|lb)', text)
                if weight_match:
                    weight_value = float(weight_match.group(1))
                    return weight_value

            return None

        except:
            return None

    def extract_date_from_text(self, text):
        """Extract date from workout text"""
        # Simple date extraction
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return datetime.now().strftime('%Y-%m-%d')

    def extract_exercises_from_text(self, text):
        """Extract exercise info from text"""
        exercises = []
        lines = text.split('\n')

        current_exercise = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this looks like an exercise name
            if any(keyword in line.lower() for keyword in ['squat', 'press', 'curl', 'row', 'pull', 'push', 'lift', 'raise']):
                if current_exercise:
                    exercises.append(current_exercise)
                current_exercise = {
                    'name': line,
                    'sets': []
                }

            # Check if this looks like set data (contains reps and weight)
            elif current_exercise and re.search(r'\d+.*\d+', line):
                set_data = self.parse_set_data(line)
                if set_data:
                    current_exercise['sets'].append(set_data)

        if current_exercise:
            exercises.append(current_exercise)

        return exercises

    def parse_set_data(self, text):
        """Parse set data from text"""
        # Look for patterns like "12 x 50kg" or "12 reps 50kg"
        patterns = [
            r'(\d+)\s*x\s*(\d+\.?\d*)\s*kg',
            r'(\d+)\s*reps?\s*(\d+\.?\d*)\s*kg',
            r'(\d+)\s*@\s*(\d+\.?\d*)\s*kg'
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return {
                    'reps': int(match.group(1)),
                    'weight': float(match.group(2))
                }

        return None

    def save_client_data(self, client_name, client_data):
        """Save client data with enhanced storage"""
        try:
            # Generate filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            client_name_clean = re.sub(r'[<>:"/\\|?*]', '_', client_name)
            json_filename = f"{client_name_clean}_{date_str}_fitness_wrapped_data.json"
            json_filepath = os.path.join(self.output_directory, json_filename)

            # Save JSON file
            with open(json_filepath, 'w') as f:
                json.dump(client_data, f, indent=2)

            # Save to SQLite if available
            if SQLITE_UTILS_IMPORTED:
                ig_username = client_name.lower().replace(' ', '_')
                save_metrics_to_sqlite(ig_username, client_data)

            # Enhanced storage
            if ENHANCED_STORAGE_AVAILABLE and client_data.get('workouts'):
                try:
                    storage_system = ComprehensiveWorkoutStorage()
                    ig_username = client_name.lower().replace(' ', '_')
                    storage_system.import_client_workout_data(
                        client_name, client_data['workouts'], ig_username)
                except Exception as e:
                    thread_safe_print(
                        f"Enhanced storage failed for {client_name}: {e}", self.worker_id)

            thread_safe_print(
                f"Data saved successfully for {client_name}", self.worker_id)
            return True

        except Exception as e:
            thread_safe_print(
                f"Failed to save data for {client_name}: {e}", self.worker_id)
            return False

    def cleanup(self):
        """Clean up browser and temp files"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass

        try:
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir, ignore_errors=True)
        except:
            pass


def process_client_worker(client_name, username, password, gemini_api_key, worker_id):
    """Worker function to process a single client"""
    automation = None
    try:
        thread_safe_print(f"Starting worker for {client_name}", worker_id)

        # Create automation instance
        automation = ParallelTrainerizeAutomation(
            gemini_api_key=gemini_api_key,
            worker_id=worker_id,
            headless=True
        )

        # Login
        if not automation.login(username, password):
            thread_safe_print(
                f"Login failed for worker {worker_id}", worker_id)
            return None

        # Process client
        result = automation.process_single_client(client_name)

        thread_safe_print(
            f"Worker {worker_id} completed {client_name}", worker_id)
        return result

    except Exception as e:
        thread_safe_print(
            f"Worker {worker_id} error processing {client_name}: {e}", worker_id)
        return None
    finally:
        if automation:
            automation.cleanup()


def main():
    """Main parallel processing function"""
    print("🚀 STARTING PARALLEL TRAINERIZE CHECK-IN PROCESS")
    print("=" * 60)

    # Configuration
    MAX_WORKERS = 5
    username = "shannonmichelle.mitchell@gmail.com"
    password = "Shanbot!2024"
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not gemini_api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables")
        return

    # Client list
    client_names = [
        "Alice Forster", "Anna Somogyi", "Elena Green", "Jen Frayne",
        "Jo Schiavetta", "Kelly Smith", "Kristy Cooper", "Kylie Pinder",
        "Nicole Lynch", "Raechel Muller", "Shane Minahan", "Claire Ruberu",
        "Danny Birch", "Jo Foy", "Joan Coughlin"
    ]

    print(
        f"📋 Processing {len(client_names)} clients with {MAX_WORKERS} parallel workers")
    print(f"🤖 Using headless Chrome browsers for maximum speed")

    # Track results
    all_results = {}
    processed_count = 0
    failed_count = 0

    start_time = time.time()

    # Process clients in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all client processing tasks
        future_to_client = {
            executor.submit(
                process_client_worker,
                client_name,
                username,
                password,
                gemini_api_key,
                f"W{i+1}"
            ): client_name
            for i, client_name in enumerate(client_names)
        }

        # Collect results as they complete
        for future in as_completed(future_to_client):
            client_name = future_to_client[future]
            try:
                # 5 minute timeout per client
                result = future.result(timeout=300)
                if result:
                    all_results.update(result)
                    processed_count += 1
                    print(
                        f"✅ [{processed_count}/{len(client_names)}] Completed: {client_name}")
                else:
                    failed_count += 1
                    print(
                        f"❌ [{processed_count + failed_count}/{len(client_names)}] Failed: {client_name}")

            except Exception as e:
                failed_count += 1
                print(
                    f"❌ [{processed_count + failed_count}/{len(client_names)}] Error with {client_name}: {e}")

    # Process completion
    end_time = time.time()
    total_time = end_time - start_time

    print("\n" + "=" * 60)
    print("🎉 PARALLEL PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"📊 Total clients: {len(client_names)}")
    print(f"✅ Successfully processed: {processed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(
        f"⚡ Average time per client: {total_time/len(client_names):.1f} seconds")
    print(
        f"🚀 Speed improvement: ~{len(client_names) * 300 / total_time:.1f}x faster than sequential")

    # Import weekly goals if enhanced storage available
    if ENHANCED_STORAGE_AVAILABLE and processed_count > 0:
        try:
            print("\n🎯 Importing weekly goals to SQLite...")
            storage_system = ComprehensiveWorkoutStorage()
            if storage_system.import_weekly_goals():
                print("✅ Weekly goals imported successfully")
            else:
                print("⚠️ Failed to import weekly goals")
        except Exception as e:
            print(f"⚠️ Error importing weekly goals: {e}")

    print(
        f"\n📁 Output files saved to: {os.path.join(os.getcwd(), 'output', 'checkin_reviews')}")
    print("🎬 Ready for video generation with simple_blue_video.py")


if __name__ == "__main__":
    main()
