#!/usr/bin/env python3
"""
Fresh Weekly Updater - Using only working pb.py methods
"""

import json
import time
import logging
import sys
from pb import TrainerizeAutomation
from selenium.webdriver.common.by import By


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


def update_single_client(automation, client_name, client_data):
    """Update workouts for a single client using pb.py methods"""
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

        logging.info(f"Found {len(progressions)} exercises to update")

        # Find workouts using pb.py method - just try the Back workout for now
        try:
            workout_types = ["Back"]

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
                            # Use a simple method to find exercise containers
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
                                f"Found exercises: {exercises_in_workout}")

                            # Update each exercise that has progression data
                            for exercise_name in exercises_in_workout:
                                if exercise_name in progressions:
                                    progression_data = progressions[exercise_name]

                                    # Use the recommended_reps which contains the full goal string
                                    if 'recommended_reps' in progression_data:
                                        goal_string = progression_data['recommended_reps']
                                        logging.info(
                                            f"Updating {exercise_name}: {goal_string}")

                                        # Extract weight and reps for the pb.py method
                                        # The goal string is like "S1: 50.0kg*8 | S2: 50.0kg*8 | S3: 50.0kg*8"
                                        # We'll extract the first set's weight and reps
                                        try:
                                            # Parse "S1: 50.0kg*8" to get weight=50.0, reps=8
                                            first_set = goal_string.split(
                                                '|')[0].strip()  # "S1: 50.0kg*8"
                                            weight_reps = first_set.split(
                                                ':')[1].strip()  # "50.0kg*8"
                                            weight_str, reps_str = weight_reps.split(
                                                '*')  # ["50.0kg", "8"]
                                            weight = float(
                                                weight_str.replace('kg', ''))  # 50.0
                                            reps = int(reps_str)  # 8

                                            logging.info(
                                                f"Parsed: {exercise_name} -> {weight}kg x {reps} reps")

                                            # Use pb.py method to update exercise goals
                                            automation.modify_exercise_goals(
                                                exercise_name, weight, reps)
                                        except Exception as parse_error:
                                            logging.error(
                                                f"Error parsing goal string '{goal_string}': {parse_error}")
                                            # Fallback to using the raw recommended values
                                            weight = progression_data.get(
                                                'recommended_weight', 0)
                                            reps = 6  # Default reps
                                            automation.modify_exercise_goals(
                                                exercise_name, weight, reps)
                                    else:
                                        # Fallback to basic progression data
                                        weight = progression_data.get(
                                            'recommended_weight', 0)
                                        reps = 6  # Default reps
                                        logging.info(
                                            f"Using fallback: {exercise_name} -> {weight}kg x {reps} reps")
                                        automation.modify_exercise_goals(
                                            exercise_name, weight, reps)
                                else:
                                    logging.info(
                                        f"No progression data for {exercise_name}")

                            # Save workout using pb.py method
                            logging.info(f"Saving {workout_type} workout...")
                            automation.save_workout()

                        except Exception as e:
                            logging.error(
                                f"Error processing exercises in {workout_type} workout: {e}")

                    # Return to training program
                    automation.navigate_to_training_program()
                    time.sleep(2)
                    break  # Only do one workout for now

                else:
                    logging.info(
                        f"No {workout_type} workout found, trying next...")
                    continue

        except Exception as e:
            logging.error(f"Error finding workouts: {e}")
            return False

        logging.info(f"Completed updating {client_name}")
        return True

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
            logging.FileHandler('fresh_updater.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print("=" * 60)
    print("FRESH WEEKLY UPDATER")
    print("Using only working pb.py methods")
    print("=" * 60)

    # Load progression data
    progression_data = load_progression_data()
    if not progression_data:
        print("Failed to load progression history")
        return

    print(f"Loaded progression data for {len(progression_data)} clients")
    for client_name in progression_data.keys():
        print(f"  - {client_name}")

    # Just update Alice Forster for now to test
    client_name = "Alice Forster"
    if client_name not in progression_data:
        print(f"No data for {client_name}")
        return

    # Show what data we have for Alice
    latest_entry = max(progression_data[client_name], key=lambda x: x['date'])
    progressions = latest_entry.get('progressions', {})

    print(f"\nProgression data for {client_name}:")
    for exercise, data in list(progressions.items())[:5]:  # Show first 5
        if 'recommended_reps' in data:
            print(f"  - {exercise}: {data['recommended_reps']}")

    # Confirm
    response = input(
        f"\nUpdate Back workout for {client_name} with correct progression data? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Initialize automation using pb.py
    try:
        automation = TrainerizeAutomation()

        # Login
        print("\nLogging into Trainerize...")
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("Login failed")
            return

        print("Login successful!")
        automation.handle_notification_popup()

        # Process just Alice for testing
        if update_single_client(automation, client_name, progression_data[client_name]):
            print(f"✓ Successfully updated {client_name}")
        else:
            print(f"✗ Failed to update {client_name}")

        print("\nTest update complete!")

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        print(f"Error: {e}")

    finally:
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
