#!/usr/bin/env python3
"""
Simple Weekly Updater - Clean script based on pb.py
Updates all client workout goals using progression_history.json
"""

import json
import time
import logging
import sys
from pb import TrainerizeAutomation


def load_progression_history():
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


def update_client_workouts(automation, client_name, client_data):
    """Update all workouts for a single client"""
    try:
        logging.info(f"\n=== Processing {client_name} ===")

        # Navigate to client
        if not automation.navigate_to_client(client_name):
            logging.error(f"Failed to navigate to {client_name}")
            return False

        # Navigate to training program
        if not automation.navigate_to_training_program():
            logging.error(
                f"Failed to navigate to training program for {client_name}")
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

        # Discover workouts
        workout_names = automation.discover_workout_names()
        if not workout_names:
            logging.error(f"No workouts found for {client_name}")
            return False

        logging.info(f"Found workouts: {workout_names}")

        # Process each workout
        for workout_name in workout_names:
            logging.info(f"\n--- Processing workout: {workout_name} ---")

            # Click workout
            if not automation.click_workout(workout_name):
                logging.error(f"Failed to click workout: {workout_name}")
                continue

            # Click edit workout
            if not automation.click_edit_workout():
                logging.error(f"Failed to edit workout: {workout_name}")
                automation.navigate_to_training_program()
                continue

            # Get exercises in workout
            exercises_in_workout = automation.discover_exercise_names()
            logging.info(f"Found exercises: {exercises_in_workout}")

            # Update each exercise
            for exercise_name in exercises_in_workout:
                if exercise_name in progressions:
                    progression_data = progressions[exercise_name]

                    # Get weight and reps for the modify_exercise_goals method
                    weight = progression_data.get('next_weight', 0)
                    reps = progression_data.get('next_reps', 6)

                    logging.info(
                        f"Updating {exercise_name}: {weight}kg x {reps} reps")
                    automation.modify_exercise_goals(
                        exercise_name, weight, reps)
                else:
                    logging.info(f"No progression data for {exercise_name}")

            # Save workout
            logging.info(f"Saving workout: {workout_name}")
            automation.save_workout()

            # Return to training program
            automation.navigate_to_training_program()

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
            logging.FileHandler('simple_weekly_updater.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print("=" * 60)
    print("SIMPLE WEEKLY UPDATER")
    print("=" * 60)

    # Load progression data
    progression_data = load_progression_history()
    if not progression_data:
        print("Failed to load progression history")
        return

    print(f"Loaded progression data for {len(progression_data)} clients")
    for client_name in progression_data.keys():
        print(f"  - {client_name}")

    # Confirm
    response = input(
        f"\nUpdate workouts for all {len(progression_data)} clients? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Initialize automation
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

        # Process each client
        successful = 0
        failed = 0

        for client_name, client_data in progression_data.items():
            try:
                if update_client_workouts(automation, client_name, client_data):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Unexpected error with {client_name}: {e}")
                failed += 1

            # Return to clients list
            try:
                automation.driver.get(
                    "https://www.trainerize.com/manage/clients.aspx")
                time.sleep(3)
            except:
                pass

        # Final results
        print("\n" + "=" * 60)
        print("UPDATE COMPLETE")
        print("=" * 60)
        print(f"Successfully updated: {successful} clients")
        print(f"Failed: {failed} clients")

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
