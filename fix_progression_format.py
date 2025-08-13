#!/usr/bin/env python3
"""
Fix the progression data format to match what the automation script expects
Convert from workout-name keys to "Weight Training" key format
"""

import json
import logging

logging.basicConfig(level=logging.INFO)


def fix_progression_format():
    """Convert the progression data to the expected format"""
    try:
        # Load the current progression data
        with open('set_by_set_progressions.json', 'r') as f:
            original_data = json.load(f)

        logging.info(f"Loaded original data with {len(original_data)} clients")

        # Convert format
        fixed_data = {}

        for client_name, workouts in original_data.items():
            logging.info(f"Processing client: {client_name}")

            # Initialize client with Weight Training key
            fixed_data[client_name] = {
                "Weight Training": []
            }

            # Combine all workout exercises into Weight Training
            for workout_name, exercises in workouts.items():
                logging.info(
                    f"  Processing workout: {workout_name} with {len(exercises)} exercises")

                # Add all exercises from this workout to Weight Training
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

                    fixed_data[client_name]["Weight Training"].append(
                        fixed_exercise)

        # Save the fixed data
        with open('set_by_set_progressions_fixed.json', 'w') as f:
            json.dump(fixed_data, f, indent=2)

        logging.info(f"Fixed data saved to set_by_set_progressions_fixed.json")

        # Show summary
        print("\nFIXED PROGRESSION DATA SUMMARY:")
        for client_name, workouts in fixed_data.items():
            exercise_count = len(workouts["Weight Training"])
            print(f"  • {client_name}: {exercise_count} exercises")

        # Show sample
        if fixed_data:
            sample_client = list(fixed_data.keys())[0]
            sample_exercise = fixed_data[sample_client]["Weight Training"][0]
            print(f"\nSample exercise for {sample_client}:")
            print(
                f"  {sample_exercise['exercise_name']}: {sample_exercise['reps']}")

        return True

    except Exception as e:
        logging.error(f"Error fixing progression format: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("FIXING PROGRESSION DATA FORMAT")
    print("=" * 60)

    if fix_progression_format():
        print("\n✅ Format fix completed successfully!")
        print(
            "You can now use set_by_set_progressions_fixed.json with the automation script.")
    else:
        print("\n❌ Format fix failed.")
