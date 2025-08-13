#!/usr/bin/env python3
"""
Fix progression data by removing non-existent workouts and exercises
"""

import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def fix_progression_data():
    """Fix the progression data by consolidating duplicate workouts and removing non-matching exercises"""

    # Load the original progression data
    with open('set_by_set_progressions.json', 'r') as f:
        data = json.load(f)

    # Define the mapping of incorrect workout names to correct ones
    workout_name_mapping = {
        'Back': 'Back Day',
        'Shoulders': 'Shoulder Day',
        'Chest + Arms': None,  # This workout doesn't exist in Trainerize
    }

    # Track changes
    changes_made = []

    for client_name, workouts in data.items():
        logging.info(f"Processing client: {client_name}")

        # Create a new workouts dict to avoid modifying during iteration
        new_workouts = {}

        for workout_name, exercises in workouts.items():

            # Check if this workout name needs to be mapped
            if workout_name in workout_name_mapping:
                correct_name = workout_name_mapping[workout_name]

                if correct_name is None:
                    # Skip this workout entirely (doesn't exist in Trainerize)
                    changes_made.append(
                        f"{client_name}: Removed non-existent workout '{workout_name}'")
                    logging.info(
                        f"  Removed non-existent workout: {workout_name}")
                    continue
                else:
                    # Rename the workout
                    if correct_name in new_workouts:
                        # Merge exercises if the correct workout already exists
                        new_workouts[correct_name].extend(exercises)
                        changes_made.append(
                            f"{client_name}: Merged '{workout_name}' into existing '{correct_name}'")
                        logging.info(
                            f"  Merged {workout_name} -> {correct_name}")
                    else:
                        new_workouts[correct_name] = exercises
                        changes_made.append(
                            f"{client_name}: Renamed '{workout_name}' to '{correct_name}'")
                        logging.info(
                            f"  Renamed {workout_name} -> {correct_name}")
            else:
                # Keep the workout as-is
                new_workouts[workout_name] = exercises

        # Update the client's workouts
        data[client_name] = new_workouts

    # Save the fixed data
    with open('set_by_set_progressions_fixed.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Report changes
    logging.info(f"\n--- PROGRESSION DATA FIXES COMPLETE ---")
    logging.info(f"Changes made: {len(changes_made)}")
    for change in changes_made:
        logging.info(f"  - {change}")

    logging.info(f"\nFixed data saved to: set_by_set_progressions_fixed.json")

    # Count exercises per client in fixed data
    logging.info(f"\n--- FIXED DATA SUMMARY ---")
    for client_name, workouts in data.items():
        total_exercises = sum(len(exercises)
                              for exercises in workouts.values())
        workout_count = len(workouts)
        logging.info(
            f"{client_name}: {workout_count} workouts, {total_exercises} exercises")
        for workout_name in workouts.keys():
            logging.info(f"  - {workout_name}")


if __name__ == "__main__":
    fix_progression_data()
