#!/usr/bin/env python3
"""
Fixed Parallel Trainerize Check-in Script
Processes multiple clients using a pool of authenticated browser sessions
"""

import sys
import os
import json
import time
import logging
import re
import traceback
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
import google.generativeai as genai

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

# --- START ENHANCED STORAGE IMPORT ---
try:
    from comprehensive_workout_storage_system import ComprehensiveWorkoutStorage
    ENHANCED_STORAGE_AVAILABLE = True
    print("✓ Enhanced workout storage system loaded successfully")
except ImportError as e:
    ENHANCED_STORAGE_AVAILABLE = False
    print(f"⚠️  Enhanced storage system not available: {e}")
# --- END ENHANCED STORAGE IMPORT ---

print("**** RUNNING IMPROVED PARALLEL VERSION ****")
print("**** 3 AUTHENTICATED BROWSERS + 2 PROCESSING WORKERS ****")

# Thread-safe logging
log_lock = threading.Lock()


def thread_safe_print(message, worker_id=None):
    """Thread-safe printing"""
    with log_lock:
        if worker_id:
            print(f"[Worker {worker_id}] {message}")
        else:
            print(message)


class FastTrainerizeSession:
    def __init__(self, worker_id, headless=True):
        self.worker_id = worker_id
        self.headless = headless
        self.output_directory = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"

        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)

        # Initialize Gemini
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash-thinking-exp-01-21')
        else:
            self.model = None

        # Optimized Chrome options for headless operation
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Performance optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up page loads
        # DON'T disable JavaScript - needed for login!
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Unique temp directory
        self.temp_user_data_dir = tempfile.mkdtemp(
            prefix=f"trainerize_fast_{worker_id}_")
        chrome_options.add_argument(
            f"--user-data-dir={self.temp_user_data_dir}")

        # Initialize Chrome
        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 20)

        thread_safe_print(f"Chrome session initialized", self.worker_id)

    def login(self, username, password):
        """Login to Trainerize"""
        try:
            thread_safe_print("Logging in to Trainerize...", self.worker_id)
            self.driver.get("https://www.trainerize.com/login")

            # Wait for and fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "Username")))
            username_field.clear()
            username_field.send_keys(username)

            # Fill password
            password_field = self.driver.find_element(By.ID, "Password")
            password_field.clear()
            password_field.send_keys(password)

            # Click login
            login_button = self.driver.find_element(
                By.XPATH, "//input[@type='submit' and @value='Log In']")
            login_button.click()

            # Wait for redirect to client page
            self.wait.until(EC.url_contains("Clients.aspx"))
            thread_safe_print("Login successful!", self.worker_id)
            return True

        except Exception as e:
            thread_safe_print(f"Login failed: {e}", self.worker_id)
            return False

    def get_client_list(self):
        """Get list of clients from the main page"""
        try:
            self.driver.get("https://www.trainerize.com/Clients.aspx")
            time.sleep(2)

            # Find all client links
            client_links = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'Client.aspx')]")
            client_names = []

            for link in client_links:
                try:
                    client_name = link.text.strip()
                    if client_name and len(client_name) > 1:
                        client_names.append(client_name)
                except:
                    continue

            thread_safe_print(
                f"Found {len(client_names)} clients", self.worker_id)
            return client_names[:15]  # Limit to first 15 for speed

        except Exception as e:
            thread_safe_print(
                f"Error getting client list: {e}", self.worker_id)
            return []

    def process_client_fast(self, client_name):
        """Fast client processing optimized for speed"""
        try:
            thread_safe_print(f"Processing {client_name}...", self.worker_id)

            # Navigate to client
            if not self.navigate_to_client(client_name):
                return None

            # Collect essential data only
            client_data = self.collect_minimal_data(client_name)
            if not client_data:
                return None

            # Save data
            if self.save_client_data(client_name, client_data):
                thread_safe_print(f"✓ Completed {client_name}", self.worker_id)
                return client_data
            else:
                thread_safe_print(
                    f"✗ Save failed for {client_name}", self.worker_id)
                return None

        except Exception as e:
            thread_safe_print(
                f"Error processing {client_name}: {e}", self.worker_id)
            return None

    def navigate_to_client(self, client_name):
        """Navigate to specific client page"""
        try:
            # Go to clients page
            self.driver.get("https://www.trainerize.com/Clients.aspx")
            time.sleep(1)

            # Find and click client link
            client_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH,
                 f"//a[contains(text(), '{client_name}') and contains(@href, 'Client.aspx')]")
            ))
            client_link.click()

            # Wait for client page to load
            time.sleep(2)
            return True

        except Exception as e:
            thread_safe_print(
                f"Navigation to {client_name} failed: {e}", self.worker_id)
            return False

    def collect_minimal_data(self, client_name):
        """Collect minimal essential data for speed"""
        try:
            client_data = {
                'name': client_name,
                'timestamp': datetime.now().isoformat(),
                'worker_id': self.worker_id,
                'business_name': 'Cocos Personal Training',
                'date_range': self.get_week_range()
            }

            # Get workouts (most important data)
            workouts = self.get_recent_workouts()
            client_data['workouts'] = workouts
            client_data['workouts_this_week'] = len(workouts)
            client_data['has_exercise_data'] = len(workouts) > 0

            if workouts:
                # Calculate basic stats
                total_reps, total_sets, total_weight = self.calculate_workout_stats(
                    workouts)
                client_data['total_reps'] = total_reps
                client_data['total_sets'] = total_sets
                client_data['total_weight_lifted'] = total_weight

                # Find most improved exercise
                client_data['most_improved_exercise'] = self.find_most_improved(
                    workouts)
            else:
                client_data['total_reps'] = 0
                client_data['total_sets'] = 0
                client_data['total_weight_lifted'] = 0
                client_data['most_improved_exercise'] = {'name': 'N/A'}

            # Try to get weight quickly
            try:
                weight = self.get_current_weight()
                if weight:
                    client_data['current_weight'] = weight
                    client_data['has_weight_data'] = True
                    client_data['current_weight_message'] = f"Current weight: {weight}kg"
                else:
                    client_data['has_weight_data'] = False
            except:
                client_data['has_weight_data'] = False

            # Set default values for other metrics
            client_data.update({
                'has_nutrition_data': False,
                'has_steps_data': False,
                'has_sleep_data': False,
                'current_nutrition_message': 'Keep focusing on balanced nutrition!',
                'current_steps_message': 'Stay active with daily walks!',
                'current_sleep_message': 'Aim for 7-9 hours of quality sleep!'
            })

            return client_data

        except Exception as e:
            thread_safe_print(f"Data collection failed: {e}", self.worker_id)
            return None

    def get_week_range(self):
        """Get current week date range"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return f"{monday.strftime('%d %b')} - {sunday.strftime('%d %b')}"

    def get_recent_workouts(self):
        """Get recent workout data quickly"""
        try:
            # Navigate to workouts
            workout_link = self.driver.find_element(
                By.XPATH, "//a[contains(@href, 'Workout') or contains(text(), 'Workout')]")
            workout_link.click()
            time.sleep(2)

            # Get workout elements
            workout_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'workout')] | //tr[contains(@class, 'row')]")

            workouts = []
            for element in workout_elements[:5]:  # Limit to 5 recent workouts
                try:
                    workout_text = element.text
                    if workout_text and len(workout_text) > 10:
                        workout = {
                            'name': self.extract_workout_name(workout_text),
                            'date': self.extract_workout_date(workout_text),
                            'exercises': self.parse_workout_exercises(workout_text),
                            'raw_text': workout_text
                        }
                        workouts.append(workout)
                except:
                    continue

            return workouts

        except Exception as e:
            thread_safe_print(
                f"Workout extraction failed: {e}", self.worker_id)
            return []

    def extract_workout_name(self, text):
        """Extract workout name from text"""
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['day', 'workout', 'training', 'session']):
                return line.strip()
        return "Workout Session"

    def extract_workout_date(self, text):
        """Extract date from workout text"""
        import re
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

    def parse_workout_exercises(self, text):
        """Parse exercises from workout text"""
        exercises = []
        lines = text.split('\n')

        current_exercise = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for exercise names
            exercise_keywords = ['squat', 'press', 'curl', 'row',
                                 'pull', 'push', 'lift', 'raise', 'deadlift', 'bench']
            if any(keyword in line.lower() for keyword in exercise_keywords):
                if current_exercise:
                    exercises.append(current_exercise)
                current_exercise = {
                    'name': line,
                    'sets': []
                }

            # Check for set data
            elif current_exercise and re.search(r'\d+.*\d+', line):
                set_data = self.parse_set_info(line)
                if set_data:
                    current_exercise['sets'].append(set_data)

        if current_exercise:
            exercises.append(current_exercise)

        return exercises

    def parse_set_info(self, text):
        """Parse individual set information"""
        import re
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

        # Try just reps
        reps_match = re.search(r'(\d+)\s*reps?', text.lower())
        if reps_match:
            return {
                'reps': int(reps_match.group(1)),
                'weight': 0
            }

        return None

    def calculate_workout_stats(self, workouts):
        """Calculate total workout statistics"""
        total_reps = 0
        total_sets = 0
        total_weight = 0

        for workout in workouts:
            for exercise in workout.get('exercises', []):
                for set_data in exercise.get('sets', []):
                    total_reps += set_data.get('reps', 0)
                    total_sets += 1
                    total_weight += set_data.get('reps', 0) * \
                        set_data.get('weight', 0)

        return total_reps, total_sets, total_weight

    def find_most_improved(self, workouts):
        """Find the exercise with most improvement"""
        try:
            if not workouts:
                return {'name': 'N/A'}

            # Simple logic: find exercise with highest recent performance
            best_exercise = {'name': 'N/A',
                             'current_performance_desc': 'No data'}
            best_total = 0

            for workout in workouts:
                for exercise in workout.get('exercises', []):
                    exercise_total = 0
                    for set_data in exercise.get('sets', []):
                        reps = set_data.get('reps', 0)
                        weight = set_data.get('weight', 0)
                        exercise_total += reps * weight

                    if exercise_total > best_total:
                        best_total = exercise_total
                        best_exercise = {
                            'name': exercise.get('name', 'Unknown Exercise'),
                            'current_performance_desc': f"Total workload: {exercise_total:.1f}kg"
                        }

            return best_exercise

        except:
            return {'name': 'N/A', 'current_performance_desc': 'No data'}

    def get_current_weight(self):
        """Get current weight quickly"""
        try:
            # Look for progress/weight section
            progress_link = self.driver.find_element(
                By.XPATH, "//a[contains(text(), 'Progress') or contains(text(), 'Weight')]")
            progress_link.click()
            time.sleep(1)

            # Find weight elements
            weight_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'kg') or contains(text(), 'lb')]")
            for element in weight_elements:
                text = element.text
                weight_match = re.search(r'(\d+\.?\d*)\s*kg', text)
                if weight_match:
                    return float(weight_match.group(1))

            return None

        except:
            return None

    def save_client_data(self, client_name, client_data):
        """Save client data to JSON and database"""
        try:
            # Save JSON file
            date_str = datetime.now().strftime('%Y-%m-%d')
            client_name_clean = re.sub(r'[<>:"/\\|?*]', '_', client_name)
            json_filename = f"{client_name_clean}_{date_str}_fitness_wrapped_data.json"
            json_filepath = os.path.join(self.output_directory, json_filename)

            with open(json_filepath, 'w') as f:
                json.dump(client_data, f, indent=2)

            # Save to SQLite
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
                        f"Enhanced storage failed: {e}", self.worker_id)

            return True

        except Exception as e:
            thread_safe_print(f"Save failed: {e}", self.worker_id)
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


def process_client_batch(client_names, username, password, worker_id):
    """Process a batch of clients with a single browser session"""
    session = None
    results = []

    try:
        thread_safe_print(
            f"Starting batch processor with {len(client_names)} clients", worker_id)

        # Create session
        session = FastTrainerizeSession(worker_id, headless=True)

        # Login once
        if not session.login(username, password):
            thread_safe_print("Login failed - aborting batch", worker_id)
            return results

        # Process each client
        for client_name in client_names:
            try:
                result = session.process_client_fast(client_name)
                if result:
                    results.append((client_name, result))
                    thread_safe_print(f"✓ {client_name} completed", worker_id)
                else:
                    thread_safe_print(f"✗ {client_name} failed", worker_id)
            except Exception as e:
                thread_safe_print(f"✗ {client_name} error: {e}", worker_id)

        thread_safe_print(
            f"Batch completed: {len(results)}/{len(client_names)} successful", worker_id)
        return results

    except Exception as e:
        thread_safe_print(f"Batch processor error: {e}", worker_id)
        return results
    finally:
        if session:
            session.cleanup()


def main():
    """Main improved parallel processing function"""
    print("🚀 STARTING IMPROVED PARALLEL TRAINERIZE CHECK-IN")
    print("=" * 60)

    # Configuration
    NUM_WORKERS = 3  # Reduced to 3 for stability
    username = "shannonmichelle.mitchell@gmail.com"
    password = "Shanbot!2024"

    # Client list
    all_clients = [
        "Alice Forster", "Anna Somogyi", "Elena Green", "Jen Frayne",
        "Jo Schiavetta", "Kelly Smith", "Kristy Cooper", "Kylie Pinder",
        "Nicole Lynch", "Raechel Muller", "Shane Minahan", "Claire Ruberu",
        "Danny Birch", "Jo Foy", "Joan Coughlin"
    ]

    print(
        f"📋 Processing {len(all_clients)} clients with {NUM_WORKERS} parallel sessions")
    print(f"🤖 Using optimized headless Chrome browsers")

    # Split clients into batches
    batch_size = len(all_clients) // NUM_WORKERS + 1
    client_batches = [all_clients[i:i + batch_size]
                      for i in range(0, len(all_clients), batch_size)]

    print(
        f"📦 Split into {len(client_batches)} batches: {[len(batch) for batch in client_batches]}")

    # Track results
    all_results = []
    processed_count = 0

    start_time = time.time()

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Submit batch processing tasks
        future_to_batch = {
            executor.submit(
                process_client_batch,
                batch,
                username,
                password,
                f"B{i+1}"
            ): i
            for i, batch in enumerate(client_batches)
        }

        # Collect results
        for future in as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            try:
                # 10 minute timeout per batch
                batch_results = future.result(timeout=600)
                all_results.extend(batch_results)
                processed_count += len(batch_results)
                print(
                    f"✅ Batch {batch_idx + 1} completed: {len(batch_results)} clients processed")

            except Exception as e:
                print(f"❌ Batch {batch_idx + 1} failed: {e}")

    # Final summary
    end_time = time.time()
    total_time = end_time - start_time
    failed_count = len(all_clients) - processed_count

    print("\n" + "=" * 60)
    print("🎉 IMPROVED PARALLEL PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"📊 Total clients: {len(all_clients)}")
    print(f"✅ Successfully processed: {processed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(
        f"⚡ Average time per client: {total_time/len(all_clients):.1f} seconds")

    if processed_count > 0:
        print(
            f"🚀 Efficiency: {processed_count} clients in {total_time:.1f}s = {processed_count/total_time*60:.1f} clients/minute")

    # Import weekly goals
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
