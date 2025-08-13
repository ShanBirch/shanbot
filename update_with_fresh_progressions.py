#!/usr/bin/env python3
"""
Apply Fresh Progressions to Trainerize
Uses the trainerize_progressions.json file with new rep progression algorithm
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
        logging.FileHandler('fresh_progressions.log'),
        logging.StreamHandler()
    ]
)


def load_fresh_progressions():
    """Load the fresh progression data"""
    try:
        with open('trainerize_progressions.json', 'r') as f:
            data = json.load(f)
        logging.info(
            f"✅ Loaded fresh progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error(
            "❌ trainerize_progressions.json not found. Run convert_progressions_for_trainerize.py first.")
        return None
    except Exception as e:
        logging.error(f"❌ Error loading fresh progressions: {e}")
        return None


def main():
    print("=" * 60)
    print("🎯 APPLYING FRESH REP PROGRESSION ALGORITHM")
    print("=" * 60)

    # Load fresh progression data
    progressions_data = load_fresh_progressions()
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

    print(f"\n📊 FRESH PROGRESSION SUMMARY:")
    print(f"  • {len(progressions_data)} clients")
    print(f"  • {total_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with new goals")
    print(f"\n💡 New Set-by-Set Rep Progression Algorithm:")
    print(f"  • 6→8→10→12→15 reps progression applied to EACH SET individually")
    print(f"  • At 15 reps: increase weight, reset to 6 reps")
    print(f"  • Dumbbell increments: 1,2,3,4,5,6,7.5,8,9,10,12.5,15,17.5,20,22.5,25...")
    print(f"  • Barbell/Machine: +2.5kg increments")
    print(f"  • Goals format: GOALS: S1: 20kg*10 | S2: 22.5kg*6 | S3: 20kg*8 (individualized!)")

    # Show client breakdown
    print(f"\n👥 Clients to update:")
    for client_name, workouts in progressions_data.items():
        exercise_count = sum(len(exercises) for exercises in workouts.values())
        print(f"  • {client_name}: {exercise_count} exercises")

    # Confirm before proceeding
    response = input(
        f"\n🚀 Apply fresh progressions to all {len(progressions_data)} clients? (y/n): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return

    # Initialize the automation system
    try:
        automation = TrainerizeAutomation()

        # Login to Trainerize
        print("🔐 Logging into Trainerize...")
        username = "shannon@shannonbirch.com"
        password = "Shanbot123!"

        if not automation.login(username, password):
            print("❌ Failed to login to Trainerize")
            return

        print("✅ Successfully logged into Trainerize!")

        # Process all clients with fresh progressions
        results = automation.process_multiple_clients(progressions_data)

        # Show final results
        print("\n" + "=" * 60)
        print("🎯 FRESH PROGRESSION DEPLOYMENT COMPLETE")
        print("=" * 60)

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\n📊 FINAL RESULTS:")
        print(f"  ✅ Successfully updated: {successful} clients")
        print(f"  ❌ Failed: {failed} clients")

        if failed > 0:
            print(f"\n❌ Failed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    print(
                        f"  • {client}: {result.get('error', 'Unknown error')}")

        print(f"\n💪 All successful clients now have:")
        print(f"  • Rep progression goals (6→8→10→12→15)")
        print(f"  • Weight increases at 15 reps with reset to 6")
        print(f"  • Proper gym equipment increments")
        print(f"  • Goals format: GOALS: S1: weightkg*reps | S2: weightkg*reps | S3: weightkg*reps")

    except Exception as e:
        logging.error(
            f"❌ Error during fresh progression deployment: {e}")
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
