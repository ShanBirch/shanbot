#!/usr/bin/env python3
"""
Apply Set-by-Set Progressions to Trainerize - Alice Only (for debugging)
Uses the set_by_set_progressions.json file with individualized set goals
"""

import json
import time
import logging
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('set_by_set_progressions.log'),
        logging.StreamHandler()
    ]
)


def load_set_by_set_progressions():
    """Load the set-by-set progression data"""
    try:
        with open('set_by_set_progressions.json', 'r') as f:
            data = json.load(f)
        logging.info(
            f"Loaded set-by-set progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error(
            "set_by_set_progressions.json not found. Run generate_set_by_set_progressions.py first.")
        return None
    except Exception as e:
        logging.error(f"Error loading set-by-set progressions: {e}")
        return None


def main():
    print("=" * 60)
    print("APPLYING SET-BY-SET REP PROGRESSION ALGORITHM - ALICE ONLY")
    print("=" * 60)

    # Load set-by-set progression data
    progressions_data = load_set_by_set_progressions()
    if not progressions_data:
        return

    # Filter to only Alice Forster
    alice_data = {}
    for client_name, workouts_data in progressions_data.items():
        if "alice" in client_name.lower():
            alice_data[client_name] = workouts_data
            break

    if not alice_data:
        print("Could not find Alice Forster in progression data")
        return

    # Show summary for Alice only
    alice_name = list(alice_data.keys())[0]
    alice_workouts = alice_data[alice_name]
    total_exercises = sum(len(exercises)
                          for exercises in alice_workouts.values())

    print(f"\nALICE FORSTER PROGRESSION SUMMARY:")
    print(f"  • Client: {alice_name}")
    print(f"  • {len(alice_workouts)} weight training workouts")
    print(f"  • {total_exercises} exercises with individualized set goals")

    print(f"\nWorkouts to update:")
    for workout_name, exercises in alice_workouts.items():
        print(f"  • {workout_name}: {len(exercises)} exercises")

    # Show sample individualized progression
    sample_workout = list(alice_workouts.keys())[0]
    sample_exercise = alice_workouts[sample_workout][0]
    print(f"\nSample individualized progression for {alice_name}:")
    print(f"  {sample_exercise['exercise_name']}: {sample_exercise['reps']}")

    # Show individual set reasoning
    if 'set_progressions' in sample_exercise:
        for prog in sample_exercise['set_progressions']:
            print(f"    {prog['reason']}")

    # Confirm before proceeding
    response = input(
        f"\nApply set-by-set progressions to {alice_name}? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    # Initialize the automation system
    try:
        automation = TrainerizeAutomation()

        # Login to Trainerize
        print("Logging into Trainerize...")
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("Failed to login to Trainerize")
            return

        print("Successfully logged into Trainerize!")

        # Process only Alice with set-by-set progressions
        results = automation.process_multiple_clients(alice_data)

        # Show final results
        print("\n" + "=" * 60)
        print("SET-BY-SET PROGRESSION DEPLOYMENT COMPLETE - ALICE ONLY")
        print("=" * 60)

        alice_result = results.get(alice_name, {})
        if alice_result.get('status') == 'success':
            print(f"\nSUCCESS: Alice Forster updated successfully!")
            print(f"  • Individualized set-by-set progression goals applied")
            print(f"  • Rep progression goals (6->8->10->12->15) applied to each set")
            print(f"  • Weight increases at 15 reps with reset to 6")
        else:
            print(f"\nFAILED: Alice Forster update failed")
            print(f"  Error: {alice_result.get('error', 'Unknown error')}")

    except Exception as e:
        logging.error(f"Error during set-by-set progression deployment: {e}")
        print(f"Error: {e}")

    finally:
        # Cleanup
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
