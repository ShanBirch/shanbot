#!/usr/bin/env python3
"""
Fix the progression data format to match what the automation script expects
Keep individual workout names but ensure proper structure
"""

import json
import logging

logging.basicConfig(level=logging.INFO)


def fix_progression_format_v2():
    """Convert the progression data to the expected format with individual workout names"""
    try:
        # Load the current progression data
        with open('set_by_set_progressions.json', 'r') as f:
            original_data = json.load(f)

        logging.info(f"Loaded original data with {len(original_data)} clients")

        # Convert format - keep individual workout names
        fixed_data = {}

        for client_name, workouts in original_data.items():
            logging.info(f"Processing client: {client_name}")

            # Initialize client with empty dict
            fixed_data[client_name] = {}

            # Keep each workout separate with its original name
            for workout_name, exercises in workouts.items():
                logging.info(
                    f"  Processing workout: {workout_name} with {len(exercises)} exercises")

                # Keep the workout name as-is
                fixed_data[client_name][workout_name] = []

                # Add all exercises from this workout
                for exercise in exercises:
                    # Ensure the exercise has the expected structure
                    fixed_exercise = {
                        "exercise_name": exercise["exercise_name"],
                        # This contains the formatted GOALS string
                        "reps": exercise["reps"]
                    }

                    # Add optional fields if they exist
                    if "set_progressions" in exercise:
                        fixed_exercise["set_progressions"] = exercise["set_progressions"]
                    if "action" in exercise:
                        fixed_exercise["action"] = exercise["action"]
                    if "weight" in exercise:
                        fixed_exercise["weight"] = exercise["weight"]

                    fixed_data[client_name][workout_name].append(
                        fixed_exercise)

        # Save the fixed data
        with open('set_by_set_progressions_v2.json', 'w') as f:
            json.dump(fixed_data, f, indent=2)

        logging.info(f"Fixed data saved to set_by_set_progressions_v2.json")

        # Show summary
        print("\nFIXED PROGRESSION DATA SUMMARY (V2):")
        for client_name, workouts in fixed_data.items():
            total_exercises = sum(len(exercises)
                                  for exercises in workouts.values())
            print(
                f"  • {client_name}: {len(workouts)} workouts, {total_exercises} total exercises")
            for workout_name, exercises in workouts.items():
                print(f"    - {workout_name}: {len(exercises)} exercises")

        # Show sample
        if fixed_data:
            sample_client = list(fixed_data.keys())[0]
            sample_workout = list(fixed_data[sample_client].keys())[0]
            sample_exercise = fixed_data[sample_client][sample_workout][0]
            print(f"\nSample exercise for {sample_client} - {sample_workout}:")
            print(
                f"  {sample_exercise['exercise_name']}: {sample_exercise['reps']}")

        return True

    except Exception as e:
        logging.error(f"Error fixing progression format: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("FIXING PROGRESSION DATA FORMAT V2 - PRESERVING WORKOUT NAMES")
    print("=" * 60)

    if fix_progression_format_v2():
        print("\n✅ Format fix V2 completed successfully!")
        print("You can now use set_by_set_progressions_v2.json with the automation script.")
    else:
        print("\n❌ Format fix V2 failed.")
