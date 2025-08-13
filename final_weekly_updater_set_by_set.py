#!/usr/bin/env python3
"""
Final Weekly Updater - Set-by-Set Progression System
Updates all workouts for all clients with individual set progression data
Each set progresses independently using the 6→8→10→12→15 algorithm
"""

import json
import time
import logging
import sys
from pb import TrainerizeAutomation
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_progression_data():
    """Load progression history from JSON file"""
    try:
        with open('progression_history.json', 'r') as f:
            data = json.load(f)
        logging.info(f"Loaded progression data for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error("progression_history.json not found")
        return None
    except Exception as e:
        logging.error(f"Error loading progression history: {e}")
        return None


def modify_exercise_goals_set_by_set(automation, exercise_name, goal_string):
    """
    Modified version that sets the full goal string with individual set targets
    Example: "GOALS: S1: 50.0kg*8 | S2: 45.0kg*12 | S3: 40.0kg*6"
    """
    try:
        logging.info(
            f"Setting set-by-set goals for {exercise_name}: {goal_string}")

        # Find the exercise container in the workout list
        exercise_in_list_locator = (
            By.XPATH, f"//div[@class='exerciseList fullContent flex-left flex-column']//div[@class='exerciseList-exercise__name ' and @title='{exercise_name}']/ancestor::div[contains(@class, 'workoutExercise')]")

        try:
            workout_list_exercise_div = automation.wait.until(
                EC.presence_of_element_located(exercise_in_list_locator))
            logging.info(f"Found container for '{exercise_name}'.")
        except:
            logging.error(
                f"Could not find container for '{exercise_name}' in the workout list.")
            return False

        # Find and modify the reps input field (this is where goals go)
        try:
            reps_input_locator = (
                By.XPATH, ".//input[@data-testid='workoutBuilder-recordTypeInput']")
            reps_input = workout_list_exercise_div.find_element(
                *reps_input_locator)
            reps_input.click()
            time.sleep(0.2)

            # Clear the field completely
            reps_input.send_keys(Keys.CONTROL + "a")
            reps_input.send_keys(Keys.DELETE)
            time.sleep(0.2)

            # Set the full goal string with individual set targets
            reps_input.send_keys(goal_string)
            logging.info(f"✓ Set individual set goals: {goal_string}")
            time.sleep(0.5)
            return True

        except Exception as e:
            logging.error(f"Error setting goals for '{exercise_name}': {e}")
            return False

    except Exception as e:
        logging.error(
            f"Error modifying exercise goals for '{exercise_name}': {e}")
        return False


def update_single_client(automation, client_name, client_data):
    """Update workouts for a single client using set-by-set progression"""
    try:
        logging.info(f"\n=== Processing {client_name} ===")

        # Navigate to client using pb.py method
        if not automation.navigate_to_client(client_name):
            logging.error(f"Failed to navigate to {client_name}")
            return False

        # Navigate to training program using pb.py method
        if not automation.navigate_to_training_program():
            logging.error(f"Failed to navigate to training program")
            return False

        # Get latest progression data
        if not client_data:
            logging.warning(f"No progression data for {client_name}")
            return False

        latest_entry = max(client_data, key=lambda x: x['date'])
        progressions = latest_entry.get('progressions', {})

        if not progressions:
            logging.warning(f"No progressions found for {client_name}")
            return False

        logging.info(
            f"Found {len(progressions)} exercises with set-by-set progression data")

        # Find and update ALL workouts
        try:
            workout_types = ["Back", "Chest", "Leg", "Core",
                             "Shoulder", "Push", "Pull", "Upper", "Lower", "Full"]
            updated_workouts = 0

            for workout_type in workout_types:
                logging.info(f"Trying to find {workout_type} workout...")

                if automation.click_workout_fuzzy(workout_type):
                    logging.info(
                        f"Successfully found and clicked {workout_type} workout")

                    # Edit workout using pb.py method
                    if automation.click_edit_workout():
                        logging.info("Entered edit mode")

                        # Get exercises in this workout
                        try:
                            exercise_elements = automation.driver.find_elements(
                                By.XPATH,
                                "//div[@class='exerciseList-exercise__name ']"
                            )

                            exercises_in_workout = []
                            for elem in exercise_elements:
                                if elem.is_displayed():
                                    exercise_name = elem.get_attribute('title')
                                    if exercise_name:
                                        exercises_in_workout.append(
                                            exercise_name)

                            logging.info(
                                f"Found {len(exercises_in_workout)} exercises in {workout_type} workout")

                            # Update each exercise that has progression data
                            exercises_updated = 0
                            for exercise_name in exercises_in_workout:
                                if exercise_name in progressions:
                                    progression_data = progressions[exercise_name]

                                    # Use the recommended_reps which contains the FULL goal string with individual sets
                                    if 'recommended_reps' in progression_data:
                                        # This should be like "S1: 50.0kg*8 | S2: 45.0kg*12 | S3: 40.0kg*6"
                                        goal_string = progression_data['recommended_reps']

                                        # Add "GOALS: " prefix if not already there
                                        if not goal_string.startswith("GOALS:"):
                                            goal_string = f"GOALS: {goal_string}"

                                        logging.info(f"  → {exercise_name}")
                                        logging.info(f"    {goal_string}")

                                        # Use our new set-by-set method
                                        if modify_exercise_goals_set_by_set(automation, exercise_name, goal_string):
                                            exercises_updated += 1

                                    else:
                                        # Fallback to basic progression data
                                        weight = progression_data.get(
                                            'recommended_weight', 0)
                                        reps = 6  # Default reps
                                        fallback_goal = f"GOALS: S1: {weight}kg*{reps} | S2: {weight}kg*{reps} | S3: {weight}kg*{reps}"
                                        logging.info(
                                            f"  → {exercise_name}: {fallback_goal} (fallback)")
                                        if modify_exercise_goals_set_by_set(automation, exercise_name, fallback_goal):
                                            exercises_updated += 1
                                else:
                                    logging.info(
                                        f"  - {exercise_name}: No progression data")

                            if exercises_updated > 0:
                                # Save workout using pb.py method
                                logging.info(
                                    f"Saving {workout_type} workout ({exercises_updated} exercises updated)...")
                                automation.save_workout()
                                updated_workouts += 1
                            else:
                                logging.info(
                                    f"No exercises to update in {workout_type} workout")

                        except Exception as e:
                            logging.error(
                                f"Error processing exercises in {workout_type} workout: {e}")

                    # Return to training program for next workout
                    automation.navigate_to_training_program()
                    time.sleep(2)

                else:
                    logging.info(f"No {workout_type} workout found")
                    continue

        except Exception as e:
            logging.error(f"Error finding workouts: {e}")
            return False

        logging.info(
            f"Completed updating {client_name} - {updated_workouts} workouts updated")
        return updated_workouts > 0

    except Exception as e:
        logging.error(f"Error updating {client_name}: {e}")
        return False


def main():
    """Main function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('set_by_set_updater.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print("=" * 80)
    print("🏋️ SET-BY-SET WEEKLY PROGRAM UPDATER")
    print("Individual set progression system - each set progresses independently!")
    print("=" * 80)

    # Load progression data
    progression_data = load_progression_data()
    if not progression_data:
        print("Failed to load progression history")
        return

    print(f"\nLoaded progression data for {len(progression_data)} clients:")
    total_exercises = 0
    for client_name in progression_data.keys():
        latest_entry = max(
            progression_data[client_name], key=lambda x: x['date'])
        exercise_count = len(latest_entry.get('progressions', {}))
        total_exercises += exercise_count
        print(f"  - {client_name}: {exercise_count} exercises")

    print(f"\nTotal: {total_exercises} exercises across all clients")
    print("\n🎯 SET-BY-SET PROGRESSION ALGORITHM:")
    print("  • Each set progresses independently: 6→8→10→12→15 reps")
    print("  • At 15 reps: increase weight, reset to 6 reps")
    print("  • Example: S1: 50kg*8 | S2: 45kg*12 | S3: 40kg*6")
    print("  • Dumbbell increments: 1,2,3,4,5,6,7.5,8,9,10,12.5,15,17.5,20,22.5,25...")
    print("  • Barbell/Machine: +2.5kg increments")

    # Show sample data
    if progression_data:
        sample_client = list(progression_data.keys())[0]
        latest_entry = max(
            progression_data[sample_client], key=lambda x: x['date'])
        sample_progressions = latest_entry.get('progressions', {})

        print(f"\n📋 Sample set-by-set progressions for {sample_client}:")
        count = 0
        for exercise, data in sample_progressions.items():
            if count >= 3:  # Show first 3 examples
                break
            if 'recommended_reps' in data:
                print(f"  • {exercise}:")
                print(f"    {data['recommended_reps']}")
                count += 1

    # Confirm
    response = input(
        f"\n🚀 Update ALL workouts with SET-BY-SET progression for ALL {len(progression_data)} clients? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Initialize automation using pb.py
    try:
        automation = TrainerizeAutomation()

        # Login
        print("\n🔐 Logging into Trainerize...")
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("❌ Login failed")
            return

        print("✅ Login successful!")
        automation.handle_notification_popup()

        # Process all clients
        successful = 0
        failed = 0

        for client_name, client_data in progression_data.items():
            try:
                if update_single_client(automation, client_name, client_data):
                    successful += 1
                    print(f"✅ Successfully updated {client_name}")
                else:
                    failed += 1
                    print(f"❌ Failed to update {client_name}")
            except Exception as e:
                logging.error(f"Unexpected error with {client_name}: {e}")
                failed += 1
                print(f"❌ Error updating {client_name}: {e}")

            # Return to clients list for next client
            try:
                automation.driver.get(
                    "https://www.trainerize.com/manage/clients.aspx")
                time.sleep(3)
            except:
                pass

        # Final results
        print("\n" + "=" * 80)
        print("🎉 SET-BY-SET WEEKLY PROGRAM UPDATE COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully updated: {successful} clients")
        print(f"❌ Failed: {failed} clients")

        if successful > 0:
            print(f"\n🏋️ All successful clients now have:")
            print(f"  • Individual set-by-set progression goals")
            print(f"  • Each set progresses independently (6→8→10→12→15)")
            print(f"  • Weight increases when individual sets hit 15 reps")
            print(f"  • Equipment-specific increment patterns")
            print(f"  • Format: GOALS: S1: 50kg*8 | S2: 45kg*12 | S3: 40kg*6")

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        print(f"❌ Error: {e}")

    finally:
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
