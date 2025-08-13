#!/usr/bin/env python3
"""
Apply Set-by-Set Progressions to Trainerize - FIXED VERSION
Uses the set_by_set_progressions_v2.json file with individualized set goals
Based on working pb.py navigation foundation
"""

import json
import time
import logging
from weekly_program_updater_fixed import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('set_by_set_progressions_fixed.log'),
        logging.StreamHandler()
    ]
)


def load_set_by_set_progressions():
    """Load the set-by-set progression data"""
    try:
        with open('set_by_set_progressions_v2.json', 'r') as f:
            data = json.load(f)
        logging.info(f"Loaded set-by-set progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error(
            "set_by_set_progressions_v2.json not found. Run fix_progression_format_v2.py first.")
        return None
    except Exception as e:
        logging.error(f"Error loading set-by-set progressions: {e}")
        return None


def test_single_client_first(automation, progressions_data):
    """Test with a single client first to verify everything works"""
    if not progressions_data:
        return False

    # Get first client for testing
    test_client = list(progressions_data.keys())[0]
    test_data = {test_client: progressions_data[test_client]}

    print(f"\n🧪 TESTING WITH SINGLE CLIENT: {test_client}")
    print("This will help us verify the system works before processing all clients.")

    response = input(f"Test with {test_client} first? (y/n): ")
    if response.lower() != 'y':
        return False

    # Process single client
    results = automation.process_multiple_clients(test_data)

    if results.get(test_client, {}).get('status') == 'success':
        print(f"✅ Test successful for {test_client}!")
        return True
    else:
        print(
            f"❌ Test failed for {test_client}: {results.get(test_client, {}).get('error', 'Unknown error')}")
        return False


def main():
    print("=" * 60)
    print("APPLYING SET-BY-SET REP PROGRESSION ALGORITHM - FIXED VERSION")
    print("=" * 60)

    # Load set-by-set progression data
    progressions_data = load_set_by_set_progressions()
    if not progressions_data:
        return

    # Show summary
    total_workouts = sum(len(workouts)
                         for workouts in progressions_data.values())
    total_exercises = sum(
        len(exercises)
        for workouts in progressions_data.values()
        for exercises in workouts.values()
    )

    print(f"\nSET-BY-SET PROGRESSION SUMMARY:")
    print(f"  • {len(progressions_data)} clients")
    print(f"  • {total_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with individualized set goals")
    print(f"\nNew Set-by-Set Rep Progression Algorithm:")
    print(f"  • 6->8->10->12->15 reps progression applied to EACH SET individually")
    print(f"  • At 15 reps: increase weight, reset to 6 reps")
    print(f"  • Dumbbell increments: 1,2,3,4,5,6,7.5,8,9,10,12.5,15,17.5,20,22.5,25...")
    print(f"  • Barbell/Machine: +2.5kg increments")
    print(f"  • Goals format: GOALS: S1: 20kg*10 | S2: 22.5kg*6 | S3: 20kg*8 (individualized!)")

    # Show client breakdown
    print(f"\nClients to update:")
    for client_name, workouts in progressions_data.items():
        exercise_count = sum(len(exercises) for exercises in workouts.values())
        print(f"  • {client_name}: {exercise_count} exercises")

    # Show sample individualized progression
    if progressions_data:
        sample_client = list(progressions_data.keys())[0]
        sample_workout = list(progressions_data[sample_client].keys())[0]
        sample_exercise = progressions_data[sample_client][sample_workout][0]
        print(
            f"\nSample individualized progression for {sample_client} - {sample_workout}:")
        print(
            f"  {sample_exercise['exercise_name']}: {sample_exercise['reps']}")

    # Initialize the automation system
    try:
        automation = TrainerizeAutomation()

        # Login to Trainerize
        print("\nLogging into Trainerize...")
        username = "shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("❌ Failed to login to Trainerize")
            return

        print("✅ Successfully logged into Trainerize!")

        # Test with single client first
        if not test_single_client_first(automation, progressions_data):
            print("Single client test failed or skipped. Proceeding to full deployment.")

        # Confirm before proceeding with all clients
        response = input(
            f"\nApply set-by-set progressions to all {len(progressions_data)} clients? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return

        # Process all clients with set-by-set progressions
        print("\n🚀 Starting full client update process...")
        results = automation.process_multiple_clients(progressions_data)

        # Show final results
        print("\n" + "=" * 60)
        print("SET-BY-SET PROGRESSION DEPLOYMENT COMPLETE")
        print("=" * 60)

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\nFINAL RESULTS:")
        print(f"  ✅ Successfully updated: {successful} clients")
        print(f"  ❌ Failed: {failed} clients")

        if failed > 0:
            print(f"\nFailed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    print(
                        f"  • {client}: {result.get('error', 'Unknown error')}")

        if successful > 0:
            print(f"\nAll successful clients now have:")
            print(f"  • Individualized set-by-set progression goals")
            print(f"  • Rep progression goals (6->8->10->12->15) applied to each set")
            print(f"  • Weight increases at 15 reps with reset to 6")
            print(f"  • Proper gym equipment increments")
            print(
                f"  • Goals format: GOALS: S1: weightkg*reps | S2: weightkg*reps | S3: weightkg*reps")
            print(f"  • Each set progressed based on individual performance!")

    except Exception as e:
        logging.error(f"Error during set-by-set progression deployment: {e}")
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
