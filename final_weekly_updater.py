#!/usr/bin/env python3
"""
Final Weekly Updater - Complete system using working pb.py methods
Updates all workouts for all clients with proper progression data
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

                                    # Use the recommended_reps which contains the full goal string
                                    if 'recommended_reps' in progression_data:
                                        goal_string = progression_data['recommended_reps']

                                        # Extract weight and reps for the pb.py method
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
                                                f"  ✓ {exercise_name}: {weight}kg x {reps} reps")

                                            # Use pb.py method to update exercise goals
                                            automation.modify_exercise_goals(
                                                exercise_name, weight, reps)
                                            exercises_updated += 1
                                        except Exception as parse_error:
                                            logging.error(
                                                f"Error parsing goal string '{goal_string}': {parse_error}")
                                            # Fallback to using the raw recommended values
                                            weight = progression_data.get(
                                                'recommended_weight', 0)
                                            reps = 6  # Default reps
                                            automation.modify_exercise_goals(
                                                exercise_name, weight, reps)
                                            exercises_updated += 1
                                    else:
                                        # Fallback to basic progression data
                                        weight = progression_data.get(
                                            'recommended_weight', 0)
                                        reps = 6  # Default reps
                                        logging.info(
                                            f"  ✓ {exercise_name}: {weight}kg x {reps} reps (fallback)")
                                        automation.modify_exercise_goals(
                                            exercise_name, weight, reps)
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
            logging.FileHandler('final_weekly_updater.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print("=" * 70)
    print("🏋️ FINAL WEEKLY PROGRAM UPDATER")
    print("Complete workout progression system using working pb.py methods")
    print("=" * 70)

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
    print("\nProgression Algorithm:")
    print("  • 6→8→10→12→15 reps progression")
    print("  • At 15 reps: increase weight, reset to 6 reps")
    print("  • Dumbbell increments: 1,2,3,4,5,6,7.5,8,9,10,12.5,15,17.5,20,22.5,25...")
    print("  • Barbell/Machine: +2.5kg increments")

    # Confirm
    response = input(
        f"\nUpdate ALL workouts for ALL {len(progression_data)} clients? (y/n): ")
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
        print("\n" + "=" * 70)
        print("🎉 WEEKLY PROGRAM UPDATE COMPLETE")
        print("=" * 70)
        print(f"✅ Successfully updated: {successful} clients")
        print(f"❌ Failed: {failed} clients")

        if successful > 0:
            print(f"\n🏋️ All successful clients now have:")
            print(f"  • Updated workout goals based on latest performance")
            print(f"  • Progressive overload applied (6→8→10→12→15 reps)")
            print(f"  • Proper weight increases when hitting 15 reps")
            print(f"  • Equipment-specific increment patterns")

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
