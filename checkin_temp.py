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
        weight_change = None  # Renamed from weight_loss to be more accurate

        if weight_history and len(weight_history) >= 2:
            # Use the first weight as starting weight and last as current
            start_weight = weight_history[0]
            current_weight = weight_history[-1]
            # Positive if losing weight, negative if gaining
            weight_change = start_weight - current_weight

            logging.info(
                f"Calculated weights - Start: {start_weight}, Current: {current_weight}, Change: {weight_change}")
        else:
            # Fallback values
            start_weight = 96.0  # Default starting weight
            current_weight = 94.5  # Default current weight
            # Default weight change (assuming weight loss scenario)
            weight_change = 1.5
            logging.warning(
                f"Insufficient weight history. Using defaults - Start: {start_weight}, Current: {current_weight}")

        # Determine if the client is on a weight loss or weight gain program
        is_weight_loss_goal = True  # Default assumption that client wants to lose weight

        # We can try to determine goal direction from weight_goal and current_weight
        if weight_goal and 'target' in weight_goal and current_weight is not None:
            is_weight_loss_goal = current_weight > weight_goal['target']
            logging.info(
                f"Goal direction: {'Weight loss' if is_weight_loss_goal else 'Weight gain'}")

        # The absolute value of weight change (always positive)
        absolute_weight_change = abs(
            weight_change) if weight_change is not None else 0

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

        # Create custom weight message based on data - improved with clearer logic
        if weight_change is not None:
            if weight_change > 0:
                current_weight_message = f"Weight's trending down nicely! You've lost {weight_change:.1f}kg, which is awesome! Keep doing what you're doing!"
            elif weight_change < 0:
                current_weight_message = f"You've gained {abs(weight_change):.1f}kg, which is great progress toward your muscle building goal!"
            else:
                current_weight_message = "Weight's trending well with your fitness goals. Keep up the good work!"
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

        # Generate personalized message with all available data
        personalized_message = self.generate_personalized_message(
            bodyweight_analysis,
            nutrition_analysis,
            sleep_analysis,
            steps_analysis,
            photos_analysis,
            workout_data_list
        )

        # Create data structure with data availability flags
        fitness_wrapped_data = {
            "name": client_name,
            "business_name": "Coco's",
            "date_range": date_range,
            "start_weight": start_weight,
            "current_weight": current_weight,
            # Raw weight change (positive for loss, negative for gain)
            "weight_change": weight_change,
            "absolute_weight_change": absolute_weight_change,  # Always positive
            "is_weight_loss_goal": is_weight_loss_goal,  # Flag indicating goal direction
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
            "personalized_message": personalized_message,
            "top_exercises": top_exercises,

            # Data availability flags - make sure these match what's actually used in build_video
            "has_weight_data": has_real_data["weight"],
            "has_steps_data": has_real_data["steps"],
            "has_sleep_data": has_real_data["sleep"],
            "has_nutrition_data": has_real_data["nutrition"],
            "has_up_to_date_photos": has_up_to_date_photos,

            # Additional flags
            "has_workout_data": current_week_workout_count > 0,
            "has_workload_data": workload_increase > 0,
            "has_exercise_data": len(top_exercises) >= 3
        }

        return fitness_wrapped_data

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

    def save_all_checkins(self, client_data_dict):
        """Save all client check-ins to a single file with timestamp.

        Args:
            client_data_dict: Dictionary with client names as keys and their check-in data as values

        Returns:
            String: Path to the saved file
        """
        try:
            import json
            from datetime import datetime

            # Generate timestamp for the filename
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"all_client_checkins_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(client_data_dict, f, indent=4)

            logging.info(
                f"Successfully saved all client check-ins to {filename}")
            return filename
        except Exception as e:
            logging.exception(f"Error saving all client check-ins: {e}")
            return None

    def analyze_workout_details_stripped(self, workout_name, date_str):
        """Calls the base function with workout_name and date_str parameters."""
        return analyze_workout_details_stripped_base(self, workout_name, date_str)

    def generate_personalized_message(self, bodyweight_analysis, nutrition_analysis, sleep_analysis, steps_analysis=None, photos_analysis=None, workout_data_list=None):
        """Generate a comprehensive personalized message based on all available client data.

        Args:
            bodyweight_analysis: String with bodyweight analysis
            nutrition_analysis: String with nutrition analysis
            sleep_analysis: String with sleep analysis
            steps_analysis: String with steps analysis (optional)
            photos_analysis: String with progress photos analysis (optional)
            workout_data_list: List of workout dictionaries (optional)

        Returns:
            String: Personalized message incorporating all available data
        """
        if not self.model:
            # Default message if Gemini is not available
            message = "Another fantastic week! Your workload has increased nicely.\n"
            message += "Your nutrition is on point, and your weight is trending in the right direction.\n"
            message += "Keep pushing, and you'll reach that goal weight in no time!"
            return message

        try:
            # Create a summary of workout data if available
            workout_summary = "No workout data available."
            if workout_data_list and len(workout_data_list) > 0:
                # Calculate current week's date range
                today = datetime.now().date()
                start_date = today - timedelta(days=today.weekday())  # Monday
                end_date = start_date + timedelta(days=6)             # Sunday

                # Get current week's workout stats
                workout_count, workout_types, total_weight, total_reps, total_sets, _, _ = self.calculate_workout_stats_for_date_range(
                    workout_data_list, start_date, end_date
                )

                # Format the workout summary
                workout_summary = f"Completed {workout_count} workouts this week, lifting a total of {total_weight:.2f} kg across {total_sets} sets and {total_reps} reps."
                if workout_types:
                    workout_types_str = ", ".join(workout_types[:3])
                    if len(workout_types) > 3:
                        workout_types_str += f", and {len(workout_types) - 3} more"
                    workout_summary += f" Workout types included {workout_types_str}."

            # Build comprehensive prompt with all available data
            prompt = f"""Generate a personalized, encouraging message (3-5 sentences) for a fitness client's weekly wrap-up video.
            Base it on ALL the following data (include data from each section that has content):
            
            Bodyweight Analysis: {bodyweight_analysis}
            
            Nutrition Analysis: {nutrition_analysis}
            
            Sleep Analysis: {sleep_analysis}
            
            Steps Analysis: {steps_analysis if steps_analysis else "No step data available."}
            
            Progress Photos: {photos_analysis if photos_analysis else "No progress photo data available."}
            
            Workout Summary: {workout_summary}
            
            The message should:
            1. Be motivational and highlight specific achievements
            2. Mention trends in weight, nutrition, sleep, and activity when available
            3. Give specific, actionable advice based on the data
            4. Encourage continued progress
            5. Format with line breaks for better readability on video slides
            6. be no longer than 5 sentences
            Generate only the final message (do not acknowledge you generated it) and do not mention the client's name.
            """

            response = self.model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(max_output_tokens=300)
            )

            return response.text
        except Exception as e:
            logging.exception(f"Error generating personalized message: {e}")
            # Fallback message
            return "Another fantastic week of progress!\nYour workload is increasing and your consistency is showing results.\nYour nutrition choices are supporting your goals.\nSleep patterns are helping with recovery.\nKeep pushing, and you'll reach that goal weight in no time!"

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

    # Dictionary to store all client check-ins
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

                # Prepare the fitness data
                fitness_wrapped_data = automation.prepare_fitness_wrapped_data(
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

                # Store this client's data in the all_client_data dictionary
                all_client_data[client_name] = {
                    "fitness_wrapped_data": fitness_wrapped_data,
                    "raw_data": {
                        "bodyweight_analysis": bodyweight_analysis,
                        "nutrition_analysis": nutrition_analysis,
                        "sleep_analysis": sleep_analysis,
                        "steps_analysis": steps_analysis,
                        "photos_analysis": photos_analysis,
                        "weight_goal_text": weight_goal_text,
                        "workout_count": len(workout_data_list) if workout_data_list else 0
                    }
                }

                # Save individual client data to JSON file with timestamp
                json_filename = automation.save_fitness_wrapped_data(
                    client_name, fitness_wrapped_data)
                if json_filename:
                    print(
                        f"Successfully saved data for {client_name} to {json_filename}")
                else:
                    print(f"Failed to save data for {client_name}")

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

        # After processing all clients, save all client data to a single file
        if all_client_data:
            all_clients_filename = automation.save_all_checkins(
                all_client_data)
            if all_clients_filename:
                print(
                    f"\nSuccessfully saved all client check-ins to {all_clients_filename}")
            else:
                print("\nFailed to save all client check-ins")

        print("\nAll clients processed. Cleaning up...")

    except Exception as e:
        print(f"Fatal error during execution: {e}")

    finally:
        # Always clean up resources
        automation.cleanup()
        print("Script execution complete.")
