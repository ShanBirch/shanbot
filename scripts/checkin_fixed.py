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
import csv
import sys
import json
import google.generativeai as genai


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
            self.model = genai.GenerativeModel('gemini-2.0-flash')
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

    # Add these functions to the TrainerizeAutomation class

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

            # Calculate current week's date range
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=6)             # Sunday

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

    def prepare_fitness_wrapped_data(self, client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis,
                                     steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data,
                                     workouts_completed_analysis, total_workout_stats_analysis, workout_data_list):
        """Convert Trainerize data into the format expected by FitnessWrappedGenerator with improved weight handling."""
        import re
        from datetime import datetime, timedelta, date
        import logging

        # Extract data from analytics with better logging
        weight_history = self.extract_weight_history(bodyweight_analysis)
        weight_goal = self.extract_weight_goal(weight_goal_text)

        # Log weight data for debugging
        logging.info(f"Extracted weight history: {weight_history}")
        logging.info(f"Extracted weight goal: {weight_goal}")

        # Better weight handling
        start_weight = None
        current_weight = None
        weight_loss = None

        if weight_history and len(weight_history) >= 2:
            # Use the first weight as starting weight and last as current
            start_weight = weight_history[0]
            current_weight = weight_history[-1]
            weight_loss = start_weight - current_weight

            logging.info(
                f"Calculated weights - Start: {start_weight}, Current: {current_weight}, Loss: {weight_loss}")
        else:
            # Fallback values
            start_weight = 96.0  # Default starting weight
            current_weight = 94.5  # Default current weight
            weight_loss = 1.5  # Default weight loss
            logging.warning(
                f"Insufficient weight history. Using defaults - Start: {start_weight}, Current: {current_weight}")

        # Ensure weight loss is positive for progress (use abs if weight loss is the goal)
        weight_change = abs(weight_loss) if weight_loss else 0

        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())  # Monday
        current_week_end = current_week_start + timedelta(days=6)     # Sunday

        # Calculate current week's date range dynamically
        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())  # Monday
        current_week_end = current_week_start + \
            timedelta(days=6)     # Sunday (7 days total, inclusive)

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

        # Log what we found for debugging
        logging.info(
            f"Current week range: {current_week_start} to {current_week_end}")
        logging.info(
            f"Found {current_week_workout_count} workouts in current week")
        for idx, name in enumerate(workout_names, 1):
            logging.info(f"  {idx}. {name}")
        logging.info(
            f"Previous week range: {previous_week_start} to {previous_week_end}")
        logging.info(f"Previous week total weight: {prev_week_weight}")

        # Calculate workload increase
        workload_increase = 0
        if prev_week_weight > 0:
            workload_increase = (
                (total_weight - prev_week_weight) / prev_week_weight) * 100
        logging.info(f"Calculated workload increase: {workload_increase:.2f}%")

        # Get top performing exercises with improvement percentages
        top_exercises = []
        try:
            # Calculate current week's date range
            today = datetime.now().date()
            current_week_start = today - \
                timedelta(days=today.weekday())  # Monday
            current_week_end = current_week_start + \
                timedelta(days=6)     # Sunday
            previous_week_start = current_week_start - timedelta(weeks=1)
            previous_week_end = current_week_end - timedelta(weeks=1)

            # Get top 3 performing exercises
            top_exercise_names = self.find_top_performing_exercises(
                workout_data_list,
                current_week_start,  # Dynamic current week start
                current_week_end,    # Dynamic current week end
                previous_week_start,
                previous_week_end,
                3  # Top 3 exercises
            )

            # Get improvement percentages for these exercises
            _, _, _, _, _, _, current_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list,
                current_week_start,  # Use the dynamic date variable we just created
                current_week_end,    # Use the dynamic date variable we just created
                target_exercises=top_exercise_names
            )

            _, _, _, _, _, _, previous_exercise_workload = self.calculate_workout_stats_for_date_range(
                workout_data_list,
                previous_week_start,  # Use the dynamic date variable we just created
                previous_week_end,    # Use the dynamic date variable we just created
                target_exercises=top_exercise_names
            )

            # Calculate improvement for each exercise
            for i, exercise_name in enumerate(top_exercise_names):
                current = current_exercise_workload.get(exercise_name, 0)
                previous = previous_exercise_workload.get(exercise_name, 0)

                improvement = 0
                if previous > 0:
                    improvement = ((current - previous) / previous) * 100
                elif current > 0:
                    improvement = 100  # New exercise this week

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

        # Check for real data vs defaults
        has_real_data = {
            "weight": weight_history and len(weight_history) >= 2,
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

        # Format date range
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Windows-compatible date formatting (remove leading zeros manually)
        start_day = start_of_week.strftime('%d %B').lstrip('0')
        end_day = end_of_week.strftime('%d %B').lstrip('0')
        date_range = f"{start_day} - {end_day}"

        # Create custom weight message based on data
        if weight_loss and weight_loss > 0:
            current_weight_message = f"Weight's trending down nicely! You've lost {weight_loss:.1f}kg, which is awesome! Keep doing what you're doing!"
        elif weight_loss and weight_loss < 0:
            current_weight_message = f"You've gained {abs(weight_loss):.1f}kg, which is great progress toward your muscle building goal!"
        else:
            current_weight_message = "Weight's trending well with your fitness goals. Keep up the good work!"

        # Check if progress photos are up-to-date
        has_up_to_date_photos = False
        if photos_analysis and ("up-to-date" in photos_analysis.lower() or
                                "looking great" in photos_analysis.lower() or
                                "awesome progress" in photos_analysis.lower() or
                                "uploaded this week" in photos_analysis.lower()):
            has_up_to_date_photos = True
        print(f"Progress photos up-to-date: {has_up_to_date_photos}")

        # Create data structure with data availability flags
        fitness_wrapped_data = {
            "name": client_name,
            "business_name": "Coco's",
            "date_range": date_range,
            "start_weight": start_weight,
            "current_weight": current_weight,
            "weight_loss": weight_change,
            "weight_goal": weight_goal["target"] if weight_goal else 90.0,
            "current_weight_message": current_weight_message,
            "workouts_this_week": current_week_workout_count,
            "workout_types": workout_names[:4] if workout_names else ["Upper Body", "Lower Body", "HIIT", "Cardio"],
            "total_reps": total_reps,
            "total_sets": total_sets,
            "total_weight_lifted": round(total_weight),
            "workload_increase": round(workload_increase, 2),
            "calories_consumed": calories_consumed,  # Now represents average calories
            "step_count": step_count,
            "sleep_hours": sleep_hours,
            "personalized_message": self.generate_personalized_message(bodyweight_analysis, nutrition_analysis, sleep_analysis),
            "top_exercises": top_exercises,

            # Data availability flags - make sure these match what's actually used in build_video
            "has_weight_data": has_real_data["weight"],
            "has_steps_data": has_real_data["steps"],
            "has_sleep_data": has_real_data["sleep"],
            "has_nutrition_data": has_real_data["nutrition"],
            "has_up_to_date_photos": has_up_to_date_photos,

            # Remove this if it's causing problems
            # "has_photos_data": True,

            # Additional flags that might be used later
            "has_workout_data": current_week_workout_count > 0,
            "has_workload_data": workload_increase > 0,
            "has_exercise_data": len(top_exercises) >= 3
        }

        return fitness_wrapped_data

    def generate_fitness_wrapped_video(self, fitness_wrapped_data):
        """Generate a fitness wrapped video using the provided data."""
        try:
            try:
                import sys
                fwv_path = "."  # Current directory
                if fwv_path not in sys.path:
                    sys.path.append(fwv_path)
                import importlib.util
                fwv_path_file = "./fwv.py"  # Use current directory
                spec = importlib.util.spec_from_file_location(
                    "fwv", fwv_path_file)
                if spec is None or spec.loader is None:
                    raise ImportError(
                        f"Module 'fwv' not found at {fwv_path_file}. Please ensure it is present.")
                fwv = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(fwv)
                FitnessWrappedGenerator = fwv.FitnessWrappedGenerator
            except ImportError:
                raise ImportError(
                    "Module 'fwv' not found at ./fwv.py. Please ensure it is present.")
            generator = FitnessWrappedGenerator(fitness_wrapped_data)
            video_result = generator.build_video()

            if video_result:
                logging.info(
                    f"Successfully created fitness wrapped video for {fitness_wrapped_data['name']}")
                logging.info(f"Video saved to: {generator.output_path}")

                # Upload to Google Drive and get shareable link
                drive_link = generator.upload_to_google_drive()

                if drive_link:
                    logging.info(
                        f"Video uploaded to Google Drive: {drive_link}")

                    # Generate Instagram message
                    instagram_message = generator.generate_instagram_message()
                    logging.info(
                        f"Instagram message generated: {instagram_message}")

                    return True, generator.output_path, drive_link, instagram_message
                else:
                    logging.warning(
                        "Video created but not uploaded to Google Drive")
                    return True, generator.output_path, None, None
            else:
                logging.error(
                    f"Failed to create fitness wrapped video for {fitness_wrapped_data['name']}")
                return False, None, None, None
        except Exception as e:
            logging.exception(f"Error generating fitness wrapped video: {e}")
            return False, None, None, None

    def save_fitness_wrapped_data(self, client_name, fitness_wrapped_data):
        """Save the prepared data to a JSON file."""
        import json

        filename = f"{client_name.replace(' ', '_')}_fitness_wrapped_data.json"
        try:
            with open(filename, 'w') as f:
                json.dump(fitness_wrapped_data, f, indent=4)
            logging.info(f"Saved fitness wrapped data to {filename}")
            return filename
        except Exception as e:
            logging.exception(f"Error saving fitness wrapped data: {e}")
            return None

    def extract_weight_history(self, bodyweight_analysis):
        """Extracts historical weight values from bodyweight analysis text.

        Args:
            bodyweight_analysis: String containing the bodyweight analysis from Gemini

        Returns:
            List of weight values or empty list if extraction fails
        """
        try:
            if not bodyweight_analysis or "No bodyweight data available" in bodyweight_analysis:
                logging.info("No bodyweight data available in analysis")
                return []

            # Look for common patterns in Gemini's output that indicate weight values
            weights = []

            # Try to find the starting weight
            start_weight_match = re.search(
                r"starting weight.*?(\d+\.?\d*)", bodyweight_analysis, re.IGNORECASE)
            if start_weight_match:
                try:
                    weights.append(float(start_weight_match.group(1)))
                    logging.info(
                        f"Found starting weight: {start_weight_match.group(1)}")
                except ValueError:
                    pass

            # Try to find the latest weight
            latest_weight_match = re.search(
                r"latest weight.*?(\d+\.?\d*)", bodyweight_analysis, re.IGNORECASE)
            if latest_weight_match:
                try:
                    latest_weight = float(latest_weight_match.group(1))
                    if latest_weight not in weights:
                        weights.append(latest_weight)
                        logging.info(f"Found latest weight: {latest_weight}")
                except ValueError:
                    pass

            # Try to find second latest weight
            second_latest_match = re.search(
                r"second latest weight.*?(\d+\.?\d*)|previous weight.*?(\d+\.?\d*)", bodyweight_analysis, re.IGNORECASE)
            if second_latest_match:
                try:
                    second_latest = float(second_latest_match.group(
                        1) or second_latest_match.group(2))
                    if second_latest not in weights:
                        weights.append(second_latest)
                        logging.info(
                            f"Found second latest weight: {second_latest}")
                except ValueError:
                    pass

            # Try to find any weight mentions with kg or lbs
            all_weights = re.findall(
                r"(\d+\.?\d*)\s*(?:kg|pounds|lbs)", bodyweight_analysis, re.IGNORECASE)
            for weight_str in all_weights:
                try:
                    weight = float(weight_str)
                    if weight not in weights:
                        weights.append(weight)
                        logging.info(
                            f"Found weight from units pattern: {weight}")
                except ValueError:
                    continue

            # If we couldn't extract at least 3 weights, try a more aggressive approach
            if len(weights) < 3:
                logging.info(
                    f"Only found {len(weights)} weights, trying more aggressive extraction")
                # Look for any numbers that might be weights (between 40-200 kg for adults)
                potential_weights = re.findall(
                    r"(\d+\.?\d*)", bodyweight_analysis)
                for weight_str in potential_weights:
                    try:
                        weight = float(weight_str)
                        if 40 <= weight <= 200 and weight not in weights:
                            weights.append(weight)
                            logging.info(
                                f"Found potential weight from aggressive extraction: {weight}")
                    except ValueError:
                        continue

            # If we have at least 3 weights, assume they're in chronological order
            logging.info(f"Total weights extracted: {len(weights)}")
            logging.info(f"Extracted weights: {weights}")
            return weights

        except Exception as e:
            logging.exception(f"Error extracting weight history: {e}")
            return []

    def extract_weight_goal(self, weight_goal_text):
        """Extracts weight goal from the weight goal text.

        Args:
            weight_goal_text: String containing the weight goal from the app

        Returns:
            Dictionary with 'target' key containing the goal weight, or None if extraction fails
        """
        try:
            if not weight_goal_text or "No weight goal found" in weight_goal_text:
                logging.info("No weight goal found in text")
                return None

            # Look for patterns like "Weight Goal: 70kg" or "Target Weight: 70 kg"
            goal_match = re.search(
                r"(?:weight goal|target weight|goal weight).*?(\d+\.?\d*)", weight_goal_text, re.IGNORECASE)
            if goal_match:
                try:
                    goal = float(goal_match.group(1))
                    logging.info(
                        f"Found weight goal from standard pattern: {goal}")
                    return {'target': goal}
                except ValueError:
                    pass

            # Look for any number followed by kg
            kg_match = re.search(r"(\d+\.?\d*)\s*kg",
                                 weight_goal_text, re.IGNORECASE)
            if kg_match:
                try:
                    goal = float(kg_match.group(1))
                    logging.info(f"Found weight goal from kg pattern: {goal}")
                    return {'target': goal}
                except ValueError:
                    pass

            # Look for any number that might be a reasonable weight goal
            potential_goals = re.findall(r"(\d+\.?\d*)", weight_goal_text)
            for goal_str in potential_goals:
                try:
                    goal = float(goal_str)
                    if 40 <= goal <= 120:  # Reasonable weight range in kg
                        logging.info(
                            f"Found weight goal from number extraction: {goal}")
                        return {'target': goal}
                except ValueError:
                    continue

            logging.warning(
                f"Could not extract weight goal from: {weight_goal_text}")
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

    def click_cardio_activities(self):
        """Clicks the 'Cardio activities' link using keyboard navigation."""
        try:
            logging.info("Navigating to 'Cardio activities' using keyboard...")
            self.wait.until(EC.presence_of_element_located(
                (By.ID, "nav_progress")))

            # Find a focusable element (e.g., the Progress tab)
            progress_tab = self.driver.find_element(
                By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
            progress_tab.send_keys(Keys.TAB)
            time.sleep(0.5)
            active_element = self.driver.switch_to.active_element

            for _ in range(100):  # try tab up to 100 times
                try:
                    href = active_element.get_attribute("href")
                    # Check if href is not None and contains the target
                    if href and "activities" in href:
                        active_element.send_keys(Keys.ENTER)
                        logging.info(
                            "Successfully navigated to 'Cardio activities' using keyboard.")
                        return True
                except StaleElementReferenceException:  # Handle potential stale element
                    logging.warning(
                        "StaleElementReferenceException. Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(
                        By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

                active_element.send_keys(Keys.TAB)
                time.sleep(0.5)  # small delay between TABS

                try:  # Handle potetntial StaleElement when reaquiring active_element
                    active_element = self.driver.switch_to.active_element
                except StaleElementReferenceException:
                    logging.warning(
                        "StaleElementReferenceException.  Re-finding Progress tab.")
                    progress_tab = self.driver.find_element(
                        By.XPATH, "//a[@id='nav_progress' and @data-testid='leftNavMenu-item-progress' and @title='Progress']")
                    progress_tab.send_keys(Keys.TAB)  # Start tabbing again.
                    time.sleep(0.5)
                    active_element = self.driver.switch_to.active_element

            logging.error(
                "'Cardio activities' link not found via keyboard navigation.")
            return False
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"Error navigating to 'Cardio activities' with keyboard: {e}")
            return False
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return False

    def click_walking_graph(self):
        """Clicks the 'Walking' link within Cardio Activities using XPath."""
        pass  # Add pass to avoid syntax error if function is empty

    def navigate_to_goals_and_habits_tab(self):
        """Clicks the 'Goals and Habits' tab directly using its ID."""
        try:
            logging.info("Attempting to click the 'Goals and Habits' tab...")
            # Corrected ID with space
            goals_tab_locator = (By.ID, "nav_goals_and habits")
            goals_tab = self.wait.until(
                EC.element_to_be_clickable(goals_tab_locator))
            goals_tab.click()
            logging.info("Successfully clicked the 'Goals and Habits' tab.")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(
                f"'Goals and Habits' tab not found or not clickable: {e}")
            return False
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred while clicking 'Goals and Habits' tab: {e}")
            return False

    def get_current_weight_goal(self):
        """Retrieves the text of the current weight goal from the Goals and Habits tab."""
        try:
            logging.info("Attempting to get current weight goal...")
            weight_goal_locator = (
                By.XPATH, "//div[@class='goalTile__header flex-left']//label[@class='tz-label--large  goalTile__title']")
            weight_goal_label = self.wait.until(
                EC.presence_of_element_located(weight_goal_locator))
            # using lambda to refetch if stale
            weight_goal_text = self.wait.until(
                lambda driver: weight_goal_label.text)
            logging.info(
                f"Successfully retrieved weight goal: {weight_goal_text}")
            return weight_goal_text
        except NoSuchElementException:
            return "No weight goal found."
        except TimeoutException:
            return "No weight goal found (Timeout)."
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
                        Okay lets check in on your bodyweight graph!

                        Analyze this bodyweight graph from a personal training app, focusing on these key points:

                        1.  **Trend of the graph:** Is it trending downwards (good!), upwards (needs attention), or staying consistent?
                        2.  **Up-to-date weigh-ins:** Check if the latest weigh-in is within the current week. If not, gently encourage them to update it weekly.
                        3.  **Key weight values:** Get the:
                            *   Beginning weight (from the start of the graph).
                            *   Latest weight.
                            *   Second latest weight (to see the most recent weekly change).
                        4.  **Weight Loss Congratulation:** If there's any weight loss compared to the beginning weight, give them a congrats!

                        Example Feedback Styles (ensure your response sounds like these):

                        *Really good to see you keeping your weigh ins up to date. The downward trend is looking really promising, keep it up*

                        *No weigh ins recorded just yet, i know its hard but lets try to track our weight weekly its really beneficial*

                        *Looks like the weight has gone up a little this week, dont let that stress you out, body weight is always fluctuating due to salt and water passing though the body.*

                        *Stoked with this last weigh in 1kg down! amazing!*

                        Make it concise and encouraging, like a personal trainer would!
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
                        Okay lets check on this nutrition graph, and write a short review for your client!

                        Analyze this nutrition graph from a personal training app, focusing on:

                        1.  **Recommended Nutrition & Protein Goals:** Check if the graph displays these goals and how the client is tracking against them.
                        2.  **High and Low Days:** Identify any days where nutrition (calories) or protein intake is significantly higher or lower than usual.
                        3.  **Protein Intake Advice:**
                            *   If protein is consistently low, offer simple, actionable ways to increase it (protein bar, smoothie, etc.).
                        4.  **Calorie Intake Advice:**
                            *   If calories are too low, suggest healthy ways to get more meals in (eating earlier, whole foods).
                            *   If calories are too high, suggest simple ways to reduce them (morning fasting).
                        5.  **IMPORTANT - Calculate Average Calories:** Calculate and explicitly mention the average daily calorie intake using a phrase like "average of X calories per day" or "averaging X calories daily".

                        **IMPORTANT**: If the client's nutrition looks like its close to the target give or take 25% (above or below) of their goal, consider this a WIN! Give them a positive congratulatory message about staying on track.

                        please note, always stay extremely positive with your review.
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
                        Okay lets check in on your sleep graph!

                        Analyze this sleep graph from a personal training app. Compare the most recent week of sleep data to the sleep data from the rest of the 3 month graph.

                        Provide a concise review, keeping it short and very simple, like these examples:

                        Example 1 (Good sleep consistency):
                        *Really happy with you getting consistent 8 hours of sleep every night this week!*

                        Example 2 (Sporadic sleep):
                        *Sleep graph is looking a little sporadic this week. Let's try to aim for 8 hours every night, at the same time every night. This will get your body clock working correctly and you'll get a novel boost to your metabolism!*

                        Focus on:
                        - Consistency of sleep during the week (are they sleeping roughly the same hours each night?).
                        - Average hours of sleep during the week.
                        - Compare this week's consistency and average to the overall trend in the graph (last 3 months).
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
                        Okay lets check in on your steps graph!

                        Analyze this steps graph from a personal training app.

                        Focus on:
                        - Overall trend of steps throughout the week.
                        - Identify high step days and low step days.
                        - Assess consistency: Are steps consistently around the same level, or are there big fluctuations?
                        - Based on the graph, provide a short, encouraging review of their step activity.

                        Example Feedback Styles (ensure your response sounds like these):

                        *Really good to see you getting 10k steps a day!*

                        *Your steps are looking really good somedays, upto 15k but lacking others! Solid effort on the big days, lets gets the low days up. This will get the metabolism cranking and the fat dropping off!*

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

    def find_workout_on_date(self, target_date_str, workout_name_contains=None):
        """Explicitly searches for workouts on a specific date."""
        try:
            # Find all workout rows
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "div.baseGridRow")
            logging.info(
                f"Searching for workout on date containing '{target_date_str}', name filter: '{workout_name_contains}'")
            logging.info(f"Found {len(rows)} rows to search through")

            for row in rows:
                try:
                    # Get date text
                    date_element = row.find_element(
                        By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                    date_text = date_element.text.strip()

                    # Check if date contains the target string
                    if target_date_str in date_text:
                        # If workout name is specified, check for it
                        if workout_name_contains:
                            workout_element = row.find_element(
                                By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                            workout_name = workout_element.text.strip()
                            logging.info(
                                f"Found workout on matching date {date_text}: {workout_name}")

                            if workout_name_contains.lower() in workout_name.lower():
                                logging.info(
                                    f"Found specific workout: {workout_name} on {date_text}")
                                return workout_element
                        else:
                            # Return the first workout on this date
                            workout_element = row.find_element(
                                By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                            logging.info(
                                f"Found workout on {date_text}: {workout_element.text.strip()}")
                            return workout_element
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logging.warning(f"Error checking row: {e}")
                    continue

            logging.warning(
                f"No workout found for date: {target_date_str}, name filter: {workout_name_contains}")
            return None
        except Exception as e:
            logging.error(
                f"Error searching for workout on {target_date_str}: {e}")
            return None

    def generate_personalized_message(self, bodyweight_analysis, nutrition_analysis, sleep_analysis):
        """Generate a personalized message based on client data."""
        if not self.model:
            # Default message if Gemini is not available
            message = "Another fantastic week! Your workload has increased nicely.\n"
            message += "Your nutrition is on point, and your weight is trending in the right direction.\n"
            message += "Keep pushing, and you'll reach that goal weight in no time!"
            return message

        try:
            prompt = f"""Generate a personalized, encouraging message (5-7 sentences) for a fitness client's weekly wrap-up video.
            Base it on this data:
            
            Bodyweight Analysis: {bodyweight_analysis}
            
            Nutrition Analysis: {nutrition_analysis}
            
            Sleep Analysis: {sleep_analysis}
            
            The message should be motivational, highlight their progress, and encourage them to keep going. 
            Mention specific achievements if possible. Format with line breaks for better readability on video slides. 
            Generate only report (do not let us know you have generated the report)
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

    def _process_single_workout(self, workout_link, workout_name, date_str):
        """Helper function to process a single workout link, now returns structured data and uses the BACK button."""
        try:
            logging.info(f"Processing workout: {workout_name} on {date_str}")

            # --- Click the workout name ---
            workout_link.click()
            time.sleep(2)

            # --- Analyze workout details (on the new page, same tab) ---
            formatted_workout_data_list = self.analyze_workout_details_stripped(
                workout_name, date_str)

            # --- Use the specific BACK button instead of browser back ---
            logging.info(
                "Looking for BACK button to return to workout list page")
            back_button_locator = (
                By.CSS_SELECTOR, "button[data-testid='clientProgress-workouts-detailTable-backButton']")

            try:
                back_button = self.wait.until(
                    EC.element_to_be_clickable(back_button_locator))
                logging.info("Found BACK button, clicking it")
                back_button.click()
                time.sleep(1)  # Short wait for page navigation
            except Exception as back_error:
                logging.warning(
                    f"Could not find or click BACK button: {back_error}")
                logging.info("Falling back to browser back button")
                self.driver.back()

            # Wait for the list page to load again
            self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.baseGridRow a[data-testid='clientProgress-workouts-summaryGrid-workoutName']")))
            logging.info("Back on workout list page")

            return formatted_workout_data_list

        except Exception as e:
            logging.exception(f"Error processing workout link: {e}")
            try:
                # Emergency recovery - try to get back to the list page if something fails
                self.driver.back()
                time.sleep(2)
            except:
                pass
            return None

    def analyze_workout_details_stripped(self, workout_name, date_str):
        """Calls the base function with workout_name and date_str parameters."""
        return analyze_workout_details_stripped_base(self, workout_name, date_str)

    def _group_workout_data_by_week(self, weekly_workout_data):
        """Groups workout data by week for analysis."""
        # This is just a passthrough function for now - could implement actual grouping if needed
        return weekly_workout_data

    def analyze_workouts_completed_this_week(self, weekly_summary_data):
        """Analyzes workouts completed this week - now directly uses weekly_summary_data."""
        try:
            logging.info("Analyzing workouts completed this week...")
            if not weekly_summary_data:
                return "No workout data available for this week."

            current_week_workout_count = 0
            workout_names_str = ""

            # --- Calculate Current Week's Date Range ---
            today = datetime.now().date()
            start_date_range = today - \
                timedelta(days=today.weekday())  # Monday
            end_date_range = start_date_range + \
                timedelta(days=6)       # Sunday
            date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}"

            # --- Calculate stats for current week and get workout data + exercise workload ---
            current_week_workout_count_val, current_week_workout_names, _, _, _, _, _ = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, start_date_range, end_date_range)
            current_week_workout_count = current_week_workout_count_val
            if current_week_workout_names:
                workout_names_str = "\n- " + \
                    "\n- ".join(current_week_workout_names)

            analysis_text = f"""
            Total workouts for week of {date_range_str_prompt}: {current_week_workout_count}
            Workouts completed week of {date_range_str_prompt}:{workout_names_str}
            """

            logging.info("Workout Completed Analysis generated.")
            return analysis_text

        except Exception as e:
            logging.exception(
                f"Error analyzing workouts completed this week: {e}")
            return "Error analyzing workouts completed this week."

    def analyze_total_workout_stats(self, weekly_summary_data):
        """Analyzes total workout stats - now directly uses weekly_summary_data."""
        try:
            logging.info("Analyzing total workout stats...")
            if not weekly_summary_data:
                return "No workout data available to analyze total stats."

             # --- Calculate Current Week's Date Range ---
            today = datetime.now().date()
            start_date_range = today - \
                timedelta(days=today.weekday())  # Monday
            end_date_range = start_date_range + \
                timedelta(days=6)       # Sunday
            date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}"

            # --- Calculate stats for current week and get workout data + exercise workload ---
            _, _, current_week_weight, current_week_reps, current_week_sets, _, _ = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, start_date_range, end_date_range)

            analysis_text = f"""
            --- Totals for week of {date_range_str_prompt}: ---
            Total Weight Lifted: {current_week_weight:.2f} kg
            Total Reps Done: {current_week_reps}
            Total Sets Done: {current_week_sets}
            """
            logging.info("Total Workout Stats Analysis generated.")
            return analysis_text

        except Exception as e:
            logging.exception(f"Error analyzing total workout stats: {e}")
            return "Error analyzing total workout stats."

    def analyze_workload_increase(self, weekly_summary_data):
        """Analyzes workload increase - now directly uses weekly_summary_data."""
        try:
            logging.info("Analyzing workload increase...")
            if not weekly_summary_data:
                return "No workout data available to analyze workload increase."

            # --- Date Range for Prompt ---
            # --- Calculate Current Week's Date Range ---
            today = datetime.now().date()
            start_date_range = today - \
                timedelta(days=today.weekday())  # Monday
            end_date_range = start_date_range + \
                timedelta(days=6)       # Sunday
            date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}"

            # --- Previous Week Date Range ---
            previous_start_date_range = start_date_range - timedelta(weeks=1)
            previous_end_date_range = end_date_range - timedelta(weeks=1)

            # --- Calculate stats for current week and previous week ---
            _, _, current_week_weight, _, _, _, _ = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, start_date_range, end_date_range)
            _, _, previous_week_weight, _, _, _, _ = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, previous_start_date_range, previous_end_date_range)

            workload_change_percentage_text = "No workload data for either week to compare."
            if previous_week_weight > 0:
                workload_change_percentage = (
                    (current_week_weight - previous_week_weight) / previous_week_weight) * 100
                workload_change_percentage_text = f"Workload change vs previous week: {workload_change_percentage:.2f}%"
            elif current_week_weight > 0:
                workload_change_percentage_text = "Workload change vs previous week: Increase from 0 kg to {:.2f} kg (Percentage change: N/A - Previous week workload was 0)".format(
                    current_week_weight)

            analysis_text = f"""
            --- Total Workload Change comparing previous week to current week:
            {workload_change_percentage_text}
            """

            if previous_week_weight > 0:
                if workload_change_percentage > 0:
                    analysis_text += "\nLove this see this increase in overall workload! Keep it coming!"
                else:
                    analysis_text += "\nSlight decrease in total worload, this will happen a lot! Amaazing work for turnning up!"

            logging.info("Workload Increase Analysis generated.")
            return analysis_text

        except Exception as e:
            logging.exception(f"Error analyzing workload increase: {e}")
            return "Error analyzing workload increase."

    def analyze_specific_exercises(self, weekly_summary_data, target_exercises=None):
        """Analyzes specific exercises - now accepts target_exercises as a parameter."""
        try:
            logging.info("Analyzing specific exercises...")
            if not weekly_summary_data:
                return "No workout data available to analyze specific exercises."

            # If no target exercises provided, use defaults
            if not target_exercises:
                target_exercises = ["Barbell Bench Chest Press",
                                    "B.B Back Squat", "Lat Pull Down Wide Grip"]
                logging.info("No target exercises provided, using defaults")
            else:
                logging.info(
                    f"Using dynamically selected exercises: {target_exercises}")

            # --- Date Range for Prompt ---
            # --- Calculate Current Week's Date Range ---
            today = datetime.now().date()
            start_date_range = today - \
                timedelta(days=today.weekday())  # Monday
            end_date_range = start_date_range + \
                timedelta(days=6)       # Sunday
            date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}"

            # --- Previous Week Date Range ---
            previous_start_date_range = start_date_range - timedelta(weeks=1)
            previous_end_date_range = end_date_range - timedelta(weeks=1)
            previous_date_range_str_prompt = f"{previous_start_date_range.strftime('%d/%m/%Y')}-{previous_end_date_range.strftime('%d/%m/%Y')}"

            # --- Calculate stats for current week and previous week + get workout data + exercise workload ---
            current_week_workout_count, _, _, _, _, current_week_workout_data, current_week_exercise_workload = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, start_date_range, end_date_range, target_exercises)
            previous_week_workout_count, _, _, _, _, previous_week_workout_data, previous_week_exercise_workload = self.calculate_workout_stats_for_date_range(
                weekly_summary_data, previous_start_date_range, previous_end_date_range, target_exercises)

            exercise_details_output = ""
            # --- Capture Exercise Details Output ---
            import io
            output_buffer = io.StringIO()
            import sys
            original_stdout = sys.stdout
            sys.stdout = output_buffer  # Redirect stdout to buffer

            # Print the exercise details - use the passed target_exercises
            print_exercise_details(current_week_workout_data, previous_week_workout_data,
                                   target_exercises, date_range_str_prompt, previous_date_range_str_prompt)

            sys.stdout = original_stdout  # Restore stdout
            exercise_details_output = output_buffer.getvalue().strip()  # Capture and strip output

            exercise_workload_change_output = ""
            output_buffer_workload = io.StringIO()
            sys.stdout = output_buffer_workload  # Redirect stdout to buffer

            calculate_exercise_workload_change(
                current_week_exercise_workload, previous_week_exercise_workload, target_exercises)  # Call workload change function

            sys.stdout = original_stdout  # Restore stdout
            # Capture and strip output
            exercise_workload_change_output = output_buffer_workload.getvalue().strip()

            # Add a header mentioning these are top-performing exercises
            analysis_text = f"""
            --- YOUR TOP PERFORMING EXERCISES ---
            These exercises showed the most improvement or consistency in your recent workouts:
            
            {exercise_details_output}

            {exercise_workload_change_output}
            """

            logging.info("Specific Exercises Analysis generated.")
            return analysis_text

        except Exception as e:
            logging.exception(f"Error analyzing specific exercises: {e}")
            return "Error analyzing specific exercises."

    def generate_check_in_review(self, client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis, steps_analysis, photos_analysis,
                                 weight_goal, weekly_summary_data, exercise_recommendation, workouts_completed_analysis,
                                 total_workout_stats_analysis, workload_increase_analysis, specific_exercises_analysis,
                                 progress_prediction=None):  # Add this new parameter with default value
        """Generates a check-in review using Gemini, with workout analysis done by Gemini - REVISED PROMPT (FORCEFUL)."""
        if not self.model:
            logging.warning(
                "Gemini API key not provided, skipping check-in review generation.")
            return "Gemini API key not provided, skipping check-in review."

        review_text = "Default Review Text"
        try:
            logging.info(
                "Generating check-in review with Gemini (data-driven analysis) - REVISED PROMPT (FORCEFUL)...")

            recommendations = []

            if exercise_recommendation:
                recommendations.append(exercise_recommendation)

            if "No sleep data available" in sleep_analysis:
                recommendations.append(
                    "I noticed there's no sleep data available this week. Tracking your sleep can be really helpful...")
            elif "Data Quality: Missing data" in sleep_analysis:
                recommendations.append(
                    "It looks like there might be some missing sleep data this week...")
            if "Data Completeness: Missing data" in nutrition_analysis or "Data Completeness: Days are missed" in nutrition_analysis:
                recommendations.append(
                    "I see a few days are missing from your calorie tracking this week...")
            elif "No nutrition data available" in nutrition_analysis:
                recommendations.append(
                    "It seems there's no nutrition data for this week. Tracking your nutrition is essential...")

            prompt_recommendation_section = ""
            if recommendations:
                prompt_recommendation_section = "\n**Focus Areas:**\n\n" + \
                    "\n".join([f"* {rec}" for rec in recommendations])

            # Add progress prediction to the prompt if available
            progress_prediction_section = ""
            if progress_prediction and "Insufficient data" not in progress_prediction and "Error" not in progress_prediction:
                progress_prediction_section = f"\n\n**Progress Prediction:**\n{progress_prediction}"

            prompt = f"""
            You are a an enthusiatstic fitness coach writing client check-in reviews.
            Analyze the following data for {client_name}'s weekly progress and provide a comprehensive and encouraging review.If some data is missing from the analysis, dont add it in to the report, maybe just mention it in the summary at the end saying something like "if your looking to up your game this week you could try track your sleep, generally the more you track the better the results become! But mainly Just focus postively, on what data we do have.

            **Workout Analysis:**

            **1. Workouts Completed This Week:**
            {workouts_completed_analysis}

            **2. Total Workout Stats (All Weeks):**
            {total_workout_stats_analysis}

            **3. Workload Increase (Current vs Previous Week):**
            {workload_increase_analysis}

            **4. Specific Exercise Analysis:**
            {specific_exercises_analysis}

            **Progression Photos Analysis:**
            {photos_analysis}

            **Bodyweight Analysis:**
            {bodyweight_analysis}
            {progress_prediction_section}

            **Nutrition Analysis:**
            {nutrition_analysis}

            **Steps Analysis:**
            {steps_analysis}

            **Sleep Analysis:**
            {sleep_analysis}

            {weight_goal}

            Use the EXAMPLE reviews below for structural guidance. Keep it to exact format plz.

    Example 1
    Hey (first name) Here's your review for the week! :)

    Workout Summary

    Total workouts for week of 24/02/2025-02/03/2025: 5
    Workouts completed week of 24/02/2025-02/03/2025:
    - Saturday
    - Back and Triceps
    - Core and Arms 2
    - Chest and Biceps
    - Lower

    --- Totals for week of 24/02/2025-02/03/2025: ---
    Total Weight Lifted: 21827.00 kg
    Total Reps Done: 461
    Total Sets Done: 49

    --- Exercise: Barbell Bench Chest Press ---

    **Week of 24/02/2025-02/03/2025:**
    Workout - 28 Feb 2025
    Exercise - Barbell Bench Chest Press
        Set 1: 6 reps, 60.00 kg
        Set 2: 4 reps, 100.00 kg
        Set 3: 5 reps, 100.00 kg

    **Week of 17/02/2025-23/02/2025:**
    Workout - 17 Feb 2025
    Exercise - Barbell Bench Chest Press
        Set 1: 10 reps, 60.00 kg
        Set 2: 6 reps, 100.00 kg
        Set 3: 6 reps, 110.00 kg
        Set 4: 5 reps, 120.00 kg
        Set 5: 6 reps, 100.00 kg

        
    --- Exercise: B.B Back Squat ---

    **Week of 24/02/2025-02/03/2025:**
    Workout - 25 Feb 2025
    Exercise - B.B Back Squat
        Set 1: 5 reps, 60.00 kg
        Set 2: 4 reps, 80.00 kg
        Set 3: 3 reps, 100.00 kg
        Set 4: 3 reps, 120.00 kg
        Set 5: 100 reps, 60.00 kg

    **Week of 17/02/2025-23/02/2025:**
    Not performed in week of 17/02/2025-23/02/2025



    --- Exercise: Lat Pull Down Wide Grip ---

    **Week of 24/02/2025-02/03/2025:**
    Workout - 24 Feb 2025
    Exercise - Lat Pull Down Wide Grip
        Set 1: 10 reps, 75.00 kg
        Set 2: 10 reps, 75.00 kg
        Set 3: 8 reps, 75.00 kg
        Set 4: 7 reps, 75.00 kg
        Set 5: 6 reps, 75.00 kg

    **Week of 17/02/2025-23/02/2025:**
    Workout - 19 Feb 2025
    Exercise - Lat Pull Down Wide Grip
        Set 1: 10 reps, 75.00 kg
        Set 2: 10 reps, 75.00 kg
        Set 3: 8 reps, 75.00 kg
        Set 4: 6 reps, 75.00 kg
        Set 5: 6 reps, 75.00 kg



    B.B Back Squat: Workload change vs previous week: 0%
    Lat Pull Down Wide Grip: Workload change vs previous week: 2.50%
    Barbell Bench Chest Press: Workload change vs previous week: -58.82%

    Photos: Didn't see any new progress pics this week. No worries, but if you can, snapping some regularly is super helpful to see how far you've come visually!

    Weight: Weight's still trending down nicely, which is awesome! 2 kilos down already, v nice progress! Keep doing what you're doing! If you keep going at this rate, you should hit your goal weight around August!

    Food: Looks like calories crept up a bit on the weekend there. Totally normal, but maybe think about trying to even things out a bit more across the week. Love that you're tracking your food – that's the biggest step!

    Steps: Steps are up and down a bit, but some days you're crushing it! How about trying to aim for 10k every day? Really impressed with those high step days, keep that energy going!

    Sleep: Loving the consistent sleep tracking! That's amazing. Let's shoot for around 8 hours of sleep each night if you can and try to make it a routine, bed at the same time and up at the same time everyday, this will help keep your internal body clock happy!
        
    Summary - Another great week! really happy with the progress!


    Keep Moving - Coach Shan

    Check in review notes for gpt
        Always stay positive with the client
        For information that is missing enocurage the client to provide it next week, as kindly as possible
        Offer scientific advice to help motivate the client achieve their goals.
            """

            print("\n--- Gemini Check-in Review Prompt ---")
            print(prompt)

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000)
            )
            review_text = response.text

            print("\n--- Gemini Check-in Review Response ---")
            print(review_text)

        except Exception as e:
            logging.exception(f"Error generating check-in review: {e}")
            review_text = "Error generating check-in review. Please check the logs for details."
        finally:
            logging.info("Exiting generate_check_in_review function.")
            return review_text

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


def print_exercise_details(workout_data_current_week, workout_data_previous_week, target_exercises, date_range_str_prompt, previous_date_range_str_prompt):
    """Prints details for specified exercises for current and previous weeks."""
    for exercise_name in target_exercises:
        print(f"\n--- Exercise: {exercise_name} ---")

        print(f"\n**Week of {date_range_str_prompt}:**")
        found_in_current_week = False
        for workout in workout_data_current_week:
            # Date is already in string format from parsing
            workout_date_str = workout['date']
            for exercise in workout['exercises']:
                if exercise['name'].strip() == exercise_name:
                    found_in_current_week = True
                    print(f"  Workout - {workout_date_str}")
                    print(f"  Exercise - {exercise['name']}")
                    for set_data in exercise['sets']:
                        print(
                            f"    Set {set_data['set']}: {set_data['reps']} reps, {set_data['weight']:.2f} kg")
        if not found_in_current_week:
            print(f"  Not performed in week of {date_range_str_prompt}")

        print(f"\n**Week of {previous_date_range_str_prompt}:**")
        found_in_previous_week = False
        for workout in workout_data_previous_week:
            # Date is already in string format from parsing
            workout_date_str = workout['date']
            for exercise in workout['exercises']:
                if exercise['name'].strip() == exercise_name:
                    found_in_previous_week = True
                    print(f"  Workout - {workout_date_str}")
                    print(f"  Exercise - {exercise['name']}")
                    for set_data in exercise['sets']:
                        print(
                            f"    Set {set_data['set']}: {set_data['reps']} reps, {set_data['weight']:.2f} kg")
        if not found_in_previous_week:
            print(
                f"  Not performed in week of {previous_date_range_str_prompt}")


def calculate_exercise_workload_change(current_week_exercise_workload, previous_week_exercise_workload, target_exercises):
    """Calculates and prints workload change for specified exercises with enhanced visibility."""
    print("\n" + "="*80)
    print(f"{'EXERCISE WORKLOAD CHANGES':^80}")
    print("="*80)

    # Table header
    print(f"{'EXERCISE':<40} {'CURRENT WEEK':<15} {'PREVIOUS WEEK':<15} {'CHANGE %':<10} {'STATUS'}")
    print("-"*80)

    for exercise_name in target_exercises:
        current_workload = current_week_exercise_workload.get(exercise_name, 0)
        previous_workload = previous_week_exercise_workload.get(
            exercise_name, 0)

        if previous_workload > 0:
            workload_change_percentage = (
                (current_workload - previous_workload) / previous_workload) * 100

            # Determine status and format
            if workload_change_percentage > 5:
                status = "↑ IMPROVED"
                change_str = f"+{workload_change_percentage:.2f}%"
            elif workload_change_percentage < -5:
                status = "↓ DECREASED"
                change_str = f"{workload_change_percentage:.2f}%"
            else:
                status = "→ MAINTAINED"
                change_str = f"{workload_change_percentage:.2f}%"

            print(
                f"{exercise_name[:38]:<40} {current_workload:,.2f} kg      {previous_workload:,.2f} kg      {change_str:<10} {status}")

        else:
            if current_workload > 0:
                print(
                    f"{exercise_name[:38]:<40} {current_workload:,.2f} kg      {'N/A':<15} {'NEW':<10} ★ NEW EXERCISE")
            else:
                print(
                    f"{exercise_name[:38]:<40} {'0.00 kg':<15} {'0.00 kg':<15} {'N/A':<10} NO DATA")

    print("="*80)


def find_workouts_in_date_range(self, start_date, end_date, workout_name_contains=None):
    """Finds all workouts within a specified date range.

    Args:
        start_date: Date object for the start of the range
        end_date: Date object for the end of the range
        workout_name_contains: Optional filter for workout names

    Returns:
        List of tuples, each containing (workout_element, workout_name, date_text)
    """
    try:
        # Find all workout rows
        rows = self.driver.find_elements(By.CSS_SELECTOR, "div.baseGridRow")
        logging.info(
            f"Searching for workouts between {start_date.strftime('%d %b %Y')} and {end_date.strftime('%d %b %Y')}")
        logging.info(f"Found {len(rows)} rows to search through")

        found_workouts = []

        for row in rows:
            try:
                # Get date text
                date_element = row.find_element(
                    By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-date']")
                date_text = date_element.text.strip()

                # Parse the date
                try:
                    if date_text.lower() == 'saturday':
                        # For "Saturday", use the Saturday of the current week
                        saturday_date = start_date + \
                            timedelta(days=(5 - start_date.weekday() + 7) % 7)
                        row_date = saturday_date
                    else:
                        row_date = datetime.strptime(
                            date_text, '%d %b %Y').date()

                    # Check if date is in range
                    if start_date <= row_date <= end_date:
                        workout_element = row.find_element(
                            By.CSS_SELECTOR, "[data-testid='clientProgress-workouts-summaryGrid-workoutName']")
                        workout_name = workout_element.text.strip()

                        # Filter by workout name if specified
                        if workout_name_contains and workout_name_contains.lower() not in workout_name.lower():
                            continue

                        logging.info(
                            f"Found workout in date range: {workout_name} on {date_text}")
                        found_workouts.append(
                            (workout_element, workout_name, date_text))
                except ValueError:
                    # Skip rows with unparseable dates
                    continue

            except NoSuchElementException:
                continue
            except Exception as e:
                logging.warning(f"Error checking row: {e}")
                continue

        if not found_workouts:
            logging.warning(f"No workouts found in date range")
        else:
            logging.info(f"Found {len(found_workouts)} workouts in date range")

        return found_workouts

    except Exception as e:
        logging.error(f"Error searching for workouts in date range: {e}")
        return []


if __name__ == '__main__':
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Trainerize Automation with Fitness Wrapped Video Generation')
    parser.add_argument('--generate-video', action='store_true',
                        help='Generate fitness wrapped video after check-in review')
    parser.add_argument('--video-only', action='store_true',
                        help='Skip check-in review and only generate video from existing JSON')
    parser.add_argument('--json-file', type=str,
                        help='JSON file to use for video generation (required with --video-only)')
    parser.add_argument('--clients', nargs='+', default=["Shannon Birch"],
                        help='List of client names to process')
    args = parser.parse_args()

    # If video-only mode, just generate the video from JSON
    if args.video_only:
        if not args.json_file:
            print("Error: --json-file is required with --video-only")
            sys.exit(1)

        try:
            with open(args.json_file, 'r') as f:
                fitness_wrapped_data = json.load(f)

            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "fwv", r"C:\Users\Shannon\OneDrive\Desktop\shanbot\shanbot\shanbot\shanbot\fwv.py")
            if spec is None or spec.loader is None:
                raise ImportError(
                    "Module 'fwv' not found at C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\shanbot\\shanbot\\shanbot\\fwv.py. Please ensure it is present.")
            fwv = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fwv)
            FitnessWrappedGenerator = fwv.FitnessWrappedGenerator
            generator = FitnessWrappedGenerator(fitness_wrapped_data)
            print(
                f"Generating video for {fitness_wrapped_data.get('name', 'unknown client')}")

            if generator.build_video():
                print(
                    f"Success! Video created and saved to: {generator.output_path}")
            else:
                print("Error: Failed to create video.")
            sys.exit(0)
        except Exception as e:
            print(f"Error generating video from JSON: {e}")
            sys.exit(1)

    # Normal check-in review mode
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    client_names = args.clients

    trainerize_bot = TrainerizeAutomation(gemini_api_key)
    all_workout_data = []

    # Calculate current week's date range (Monday to Sunday)
    today = datetime.now().date()
    # Get Monday of current week (0 = Monday, 6 = Sunday)
    start_date_range = today - timedelta(days=today.weekday())
    # Get Sunday of current week
    end_date_range = start_date_range + timedelta(days=6)
    date_range_str_prompt = f"{start_date_range.strftime('%d/%m/%Y')}-{end_date_range.strftime('%d/%m/%Y')}"

    # Previous week's date range
    previous_start_date_range = start_date_range - timedelta(weeks=1)
    previous_end_date_range = end_date_range - timedelta(weeks=1)
    previous_date_range_str_prompt = f"{previous_start_date_range.strftime('%d/%m/%Y')}-{previous_end_date_range.strftime('%d/%m/%Y')}"

    print(f"Current week date range: {start_date_range} to {end_date_range}")
    print(
        f"Previous week date range: {previous_start_date_range} to {previous_end_date_range}")

    default_target_exercises = [
        "Barbell Bench Chest Press",
        "B.B Back Squat",
        "Lat Pull Down Wide Grip"
    ]

    # --- Set logging level to INFO ---
    logging.getLogger().setLevel(logging.INFO)

    all_reviews = []  # List to store reviews for all clients

    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()

            for client_name in client_names:
                print(
                    f"\n--- Starting check-in and data scrape for {client_name} ---")
                bodyweight_analysis = "No analysis yet."
                nutrition_analysis = "No analysis yet."
                sleep_analysis = "No analysis yet."
                steps_analysis = "No analysis yet."
                photos_analysis = "No analysis yet."
                weight_goal_text = "No weight goal found."
                workout_review_text_output = "No workout review generated yet."
                gpt_workout_analysis_output = "No GPT workout analysis yet."
                exercise_recommendation = None
                weekly_workout_data_all_weeks = []
                current_week_workout_data = []
                weekly_summary_data_for_review = {}

                workouts_completed_analysis_output = "No analysis yet."
                total_workout_stats_analysis_output = "No analysis yet."
                workload_increase_analysis_output = "No analysis yet."
                specific_exercises_analysis_output = "No analysis yet."

                if trainerize_bot.navigate_to_client(client_name):
                    print("Navigated to client")
                    if trainerize_bot.click_progress_tab():
                        print("Clicked progress tab")
                        # Analyze Bodyweight Graph
                        if trainerize_bot.click_biometrics():
                            print("Clicked biometrics")
                            bodyweight_analysis = trainerize_bot.analyze_bodyweight_graph()
                            print(
                                f"\n--- {client_name} - Bodyweight Graph Analysis ---")
                            print(bodyweight_analysis)

                        # Navigate to and analyze Nutrition Graph
                        if trainerize_bot.navigate_to_nutrition_graphs():
                            print("Navigated to nutrition graphs")
                            nutrition_analysis = trainerize_bot.analyze_nutrition_graph()
                            print(
                                f"\n--- {client_name} - Nutrition Graph Analysis ---")
                            print(nutrition_analysis)

                        # Navigate to and analyze Sleep Graph
                        if trainerize_bot.navigate_to_sleep_graphs():
                            print("Navigated to sleep graphs")
                            sleep_analysis = trainerize_bot.analyze_sleep_graph()
                            print(
                                f"\n--- {client_name} - Sleep Graph Analysis ---")
                            print(sleep_analysis)

                        # Navigate to and analyze Steps Graph
                        if trainerize_bot.navigate_to_steps_graphs():
                            print("Navigated to steps graphs")
                            steps_analysis = trainerize_bot.analyze_steps_graph()
                            print(
                                f"\n--- {client_name} - Steps Graph Analysis ---")
                            print(steps_analysis)

                        # Add this after processing workouts in the main script:

                        # When you've processed the workouts:
                        if trainerize_bot.click_review_by_workout().startswith("Successfully"):
                            print("Clicked review by workout")
                            weekly_workout_data_all_weeks = trainerize_bot.process_workouts()  # Get all workout data

                            # Display comprehensive workout statistics in the console
                            print("\n\n")
                            print("="*80)
                            print(
                                f"{' WORKOUT STATISTICS FOR ' + client_name.upper() + ' ':=^80}")
                            print("="*80)
                            trainerize_bot.display_workout_statistics(
                                weekly_workout_data_all_weeks)

                            weekly_summary_data_for_review = trainerize_bot._group_workout_data_by_week(
                                weekly_workout_data_all_weeks)  # Group data for review

                            # Get the top 3 performing exercises dynamically for this client
                            dynamic_target_exercises = trainerize_bot.find_top_performing_exercises(
                                weekly_workout_data_all_weeks,
                                start_date_range,
                                end_date_range,
                                previous_start_date_range,
                                previous_end_date_range,
                                3  # Top 3 exercises
                            )

                            print("\n\n" + "="*80)
                            print(f"{'TOP PERFORMING EXERCISES':^80}")
                            print("="*80)
                            for i, ex in enumerate(dynamic_target_exercises, 1):
                                print(f"  {i}. {ex}")
                            print("="*80)

                            # Gemini Workout Analysis Calls
                            workouts_completed_analysis_output = trainerize_bot.analyze_workouts_completed_this_week(
                                weekly_summary_data_for_review)
                            total_workout_stats_analysis_output = trainerize_bot.analyze_total_workout_stats(
                                weekly_summary_data_for_review)
                            workload_increase_analysis_output = trainerize_bot.analyze_workload_increase(
                                weekly_summary_data_for_review)
                            # Pass the dynamic exercises to the analysis function
                            specific_exercises_analysis_output = trainerize_bot.analyze_specific_exercises(
                                weekly_summary_data_for_review, dynamic_target_exercises)

                            print(
                                "Processed workouts and performed Gemini workout analysis")

                    # Click Progress Photos tab and analyze photos
                    if trainerize_bot.click_progress_photos_tab():
                        print("Clicked progress photos tab")
                        photos_analysis = trainerize_bot.analyze_progress_photos()
                        print(
                            f"\n--- {client_name} - Progress Photos Analysis ---")
                        print(photos_analysis)

                    # Navigate to Goals and Habits tab and get weight goal
                    if trainerize_bot.navigate_to_goals_and_habits_tab():
                        print("Navigated to goals and habits tab")
                        weight_goal_text = trainerize_bot.get_current_weight_goal()
                        print(f"\n--- {client_name} - Current Weight Goal ---")
                        print(weight_goal_text)

                        # Generate progress prediction if we have weight data and a goal
                        weight_history = trainerize_bot.extract_weight_history(
                            bodyweight_analysis)
                        weight_goal = trainerize_bot.extract_weight_goal(
                            weight_goal_text)
                        progress_prediction = ""

                        if weight_history and len(weight_history) >= 3 and weight_goal:
                            print("\n--- Generating Weight Progress Prediction ---")
                            progress_prediction = trainerize_bot.predict_future_progress(
                                weight_history, weight_goal)
                            print(
                                f"Extracted Weight History: {weight_history}")
                            print(f"Extracted Weight Goal: {weight_goal}")
                            print(
                                f"Progress Prediction: {progress_prediction}")

                            if progress_prediction:
                                logging.info(
                                    f"Generated progress prediction: {progress_prediction}")
                            else:
                                logging.warning(
                                    "Failed to generate progress prediction")

                        else:
                            if not weight_history or len(weight_history) < 3:
                                print(
                                    "Insufficient weight history data for prediction")
                            if not weight_goal:
                                print("No weight goal found for prediction")
                            progress_prediction = "Insufficient data for prediction. Need at least 3 weeks of weight data and a goal weight."

                        # Generate and Print Check-in Review
                        print("Generating check-in review")
                        check_in_review = trainerize_bot.generate_check_in_review(
                            client_name,
                            bodyweight_analysis,
                            nutrition_analysis,
                            sleep_analysis,
                            steps_analysis,
                            photos_analysis,
                            weight_goal_text,
                            weekly_summary_data_for_review,
                            exercise_recommendation,
                            workouts_completed_analysis_output,
                            total_workout_stats_analysis_output,
                            workload_increase_analysis_output,
                            specific_exercises_analysis_output,
                            progress_prediction  # Add this new parameter to the function call
                        )

                        # NEW PART: Prepare and save data for fitness wrapped video
                        print("\n--- Preparing data for fitness wrapped video ---")
                        fitness_wrapped_data = trainerize_bot.prepare_fitness_wrapped_data(
                            client_name,
                            bodyweight_analysis,
                            nutrition_analysis,
                            sleep_analysis,
                            steps_analysis,
                            photos_analysis,
                            weight_goal_text,
                            weekly_summary_data_for_review,
                            workouts_completed_analysis_output,
                            total_workout_stats_analysis_output,
                            weekly_workout_data_all_weeks
                        )

                        json_filename = trainerize_bot.save_fitness_wrapped_data(
                            client_name, fitness_wrapped_data)
                        print(
                            f"Saved fitness wrapped data to {json_filename} for video generation")

                        # Generate video if requested
                        if args.generate_video:
                            print("\n--- Generating fitness wrapped video ---")
                            success, video_path, drive_link, instagram_message = trainerize_bot.generate_fitness_wrapped_video(
                                fitness_wrapped_data)
                            if success:
                                print(
                                    f"Successfully created fitness wrapped video for {client_name}")
                                print(f"Video saved to: {video_path}")
                                if drive_link:
                                    print(
                                        f"Video uploaded to Google Drive: {drive_link}")
                                    print(
                                        f"Instagram message generated: {instagram_message}")
                                else:
                                    print(
                                        "Video created but not uploaded to Google Drive")
                            else:
                                print(
                                    f"Failed to create fitness wrapped video for {client_name}")

                else:
                    logging.warning(
                        f"Could not navigate to client: {client_name}. Moving to the next client.")
                    all_reviews.append(
                        f"\n--- Review for {client_name} ---\nError: Could not navigate to client profile.")
                    print("Could not navigate to client profile")
                    continue

                if not trainerize_bot.navigate_back_to_clients_list():
                    logging.error(
                        f"Could not navigate back to clients list after processing {client_name}. Stopping client processing.")
                    all_reviews.append(
                        f"\n--- Review for {client_name} ---\nError: Could not navigate back to clients list for next client.")
                    print("Could not navigate back to clients list")
                    break
                else:
                    print("Navigated back to clients list")

        else:
            print("Login failed. Script aborted.")

    except Exception as e:
        logging.exception(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()

    if all_reviews:
        print("\n\n--- ALL CLIENT REVIEWS ---")
        for review in all_reviews:
            print(review)
            print("-" * 50)

            print("\n\n")

# This code only runs when the script is executed directly
if __name__ == "__main__":
    # Example client list for direct execution
    client_names = ["Shannon Birch", "Ben Pryke"]
    print("\n" + "="*100)
    print("                          FINAL WORKOUT STATISTICS SUMMARY FOR ALL CLIENTS")
    print("="*100)

    print("="*100)
    print(f"{'FINAL WORKOUT STATISTICS SUMMARY FOR ALL CLIENTS':^100}")
    print("="*100)
    
    # Print workout statistics for all clients
    for client_idx, client_name in enumerate(client_names, 1):
        # Find the workout data
        client_workouts = []
        try:
            # Try to load the JSON file for this client
            json_filename = f"{client_name.replace(' ', '_')}_fitness_wrapped_data.json"
            try:
                with open(json_filename, 'r') as f:
                    fitness_data = json.load(f)
    
                    print(f"\n{client_idx}. {client_name}")
                    print(
                        f"   - Workouts Completed: {fitness_data.get('workouts_this_week', 'N/A')}")
                    print(
                        f"   - Total Weight Lifted: {fitness_data.get('total_weight_lifted', 'N/A'):,} kg")
                    print(
                        f"   - Total Reps: {fitness_data.get('total_reps', 'N/A'):,}")
                    print(
                        f"   - Total Sets: {fitness_data.get('total_sets', 'N/A'):,}")
                    print(
                        f"   - Workload Change: {fitness_data.get('workload_increase', 'N/A'):+.2f}%")
    
                    print("   - Top Exercises:")
                    top_exercises = fitness_data.get('top_exercises', [])
                    if top_exercises:
                        for i, ex in enumerate(top_exercises, 1):
                            improvement = ex.get('improvement', 0)
                            improvement_str = f"{improvement:+.1f}%" if improvement else "N/A"
                            print(
                                f"     {i}. {ex.get('name', 'Unknown')} ({improvement_str})")
                    else:
                        print("     No top exercises found")
    
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"\n{client_idx}. {client_name}")
                print("   - No workout data available")
        except Exception as e:
            print(f"\n{client_idx}. {client_name}")
            print(f"   - Error retrieving workout data: {str(e)}")
    
    print("\n" + "="*100)
    print(f"{'SCRIPT EXECUTION COMPLETE':^100}")
    print("="*100)
    
    print("\n" + "="*100)
    print("                          FINAL WORKOUT STATISTICS SUMMARY FOR ALL CLIENTS")
    print("="*100)
    
    
    def print_all_client_stats(client_names):
        # Print workout statistics for all clients
        for client_idx, client_name in enumerate(client_names, 1):
            # Find the workout data
            client_workouts = []
            try:
                # Try to load the JSON file for this client
                json_filename = f"{client_name.replace(' ', '_')}_fitness_wrapped_data.json"
                try:
                    with open(json_filename, 'r') as f:
                        fitness_data = json.load(f)
    
                        print(f"\n{client_idx}. {client_name}")
                        print(
                            f"   - Workouts Completed: {fitness_data.get('workouts_this_week', 'N/A')}")
                        print(
                            f"   - Total Weight Lifted: {fitness_data.get('total_weight_lifted', 'N/A'):,} kg")
    
                        print(
                            f"   - Total Reps: {fitness_data.get('total_reps', 'N/A'):,}")
                        print(
                            f"   - Total Sets: {fitness_data.get('total_sets', 'N/A'):,}")
                        print(
                            f"   - Workload Change: {fitness_data.get('workload_increase', 'N/A'):+.2f}%")
    
                        print("   - Top Exercises:")
                        top_exercises = fitness_data.get('top_exercises', [])
                        if top_exercises:
                            for i, ex in enumerate(top_exercises, 1):
                                improvement = ex.get('improvement', 0)
                                improvement_str = f"{improvement:+.1f}%" if improvement else "N/A"
                                print(
                                    f"     {i}. {ex.get('name', 'Unknown')} ({improvement_str})")
                        else:
                            print("     No top exercises found")
    
                except (FileNotFoundError, json.JSONDecodeError):
                    print(f"\n{client_idx}. {client_name}")
                    print("   - No workout data available")
            except Exception as e:
                print(f"\n{client_idx}. {client_name}")
                print(f"   - Error retrieving workout data: {str(e)}")
    
        print("\n" + "="*100)
    
    
    # This will only run when the script is executed directly, not when imported by run_checkin.py
    if __name__ == "__main__":
        # Define default clients to process if running script directly
        default_clients = ["Shannon Birch", "Ben Pryke",
                           "Alice Forster", "Sarika Ramani"]
        print_all_client_stats(default_clients)
