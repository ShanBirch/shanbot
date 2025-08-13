#!/usr/bin/env python3
"""
Apply Set-by-Set Progressions to Trainerize
Uses the set_by_set_progressions.json file with correct GOALS format
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


def load_conservative_progressions():
    """Load the set-by-set progression data with correct format"""
    try:
        with open('set_by_set_progressions.json', 'r') as f:
            data = json.load(f)
        logging.info(
            f"✅ Loaded set-by-set progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error(
            "❌ set_by_set_progressions.json not found. Run generate_set_by_set_progressions.py first.")
        return None
    except Exception as e:
        logging.error(f"❌ Error loading set-by-set progressions: {e}")
        return None


def main():
    print("=" * 60)
    print("🎯 APPLYING SET-BY-SET PROGRESSIONS")
    print("=" * 60)

    # Load set-by-set progression data
    progressions_data = load_conservative_progressions()
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

    print(f"\n📊 SET-BY-SET PROGRESSION SUMMARY:")
    print(f"  • {len(progressions_data)} clients")
    print(f"  • {total_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with individualized set goals")
    print(f"\n💡 Each exercise has personalized set-by-set goals:")
    print(f"  • Format: GOALS: S1: 20kg*9 | S2: 25kg*12 | S3: 25kg*12")
    print(f"  • Each set progresses based on individual performance")
    print(f"  • Smart weight increments based on equipment type")

    # Confirm before proceeding
    response = input(
        f"\n🚀 Apply set-by-set progressions to all {len(progressions_data)} clients? (y/n): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return

    # Initialize the automation system
    try:
        automation = TrainerizeAutomation()

        # Process all clients with conservative progressions
        results = automation.process_multiple_clients(progressions_data)

        # Show final results
        print("\n" + "=" * 60)
        print("🎯 SET-BY-SET PROGRESSION DEPLOYMENT COMPLETE")
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
        print(f"  • Individualized set-by-set progression goals")
        print(f"  • Format: GOALS: S1: 20kg*9 | S2: 25kg*12 | S3: 25kg*12")
        print(f"  • Each set progresses based on individual performance")
        print(f"  • Smart weight increments based on equipment type")

    except Exception as e:
        logging.error(
            f"❌ Error during conservative progression deployment: {e}")
        print(f"❌ Error: {e}")

    finally:
        # Cleanup
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
