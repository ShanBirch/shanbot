#!/usr/bin/env python3
"""
Apply Flexible Conservative Progressions to Trainerize
- Uses flexible_conservative_progressions.json
- Better error handling and login management
- Handles variable set counts
"""

import json
import time
import logging
from weekly_program_updater import TrainerizeAutomation

# Configure logging without unicode issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flexible_progressions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def load_flexible_progressions():
    """Load the flexible conservative progression data"""
    try:
        with open('flexible_conservative_progressions.json', 'r') as f:
            data = json.load(f)
        logging.info(f"Loaded flexible progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error(
            "flexible_conservative_progressions.json not found. Run flexible_conservative_progressions.py first.")
        return None
    except Exception as e:
        logging.error(f"Error loading flexible progressions: {e}")
        return None


def main():
    print("=" * 60)
    print("APPLYING FLEXIBLE CONSERVATIVE SET-BY-SET PROGRESSIONS")
    print("=" * 60)

    # Load flexible progression data
    progressions_data = load_flexible_progressions()
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

    print(f"\nFLEXIBLE PROGRESSION SUMMARY:")
    print(f"  • {len(progressions_data)} clients")
    print(f"  • {total_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with flexible set goals")
    print(f"\nProgression structure:")
    print(f"  • S1: Conservative warm-up (arrow up)")
    print(f"  • S2-S3: Progressive work sets (muscle)")
    print(f"  • S4+: Volume maintenance sets (chart)")

    # Confirm before proceeding
    response = input(
        f"\nApply flexible progressions to all {len(progressions_data)} clients? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    # Initialize the automation system
    try:
        print("\nInitializing automation system...")
        automation = TrainerizeAutomation()

        print("Starting login process...")
        if not automation.login("Shannonbirch@cocospersonaltraining.com", "cyywp7nyk2"):
            print("❌ Failed to login to Trainerize")
            return
        print("✅ Successfully logged in!")

        # Process all clients with flexible progressions
        print("Processing clients with flexible progressions...")
        results = automation.process_multiple_clients(progressions_data)

        # Show final results
        print("\n" + "=" * 60)
        print("FLEXIBLE PROGRESSION DEPLOYMENT COMPLETE")
        print("=" * 60)

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\nFINAL RESULTS:")
        print(f"  Successfully updated: {successful} clients")
        print(f"  Failed: {failed} clients")

        if failed > 0:
            print(f"\nFailed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    print(
                        f"  • {client}: {result.get('error', 'Unknown error')}")

        print(f"\nAll successful clients now have:")
        print(f"  • Flexible set-by-set progression goals")
        print(f"  • Warm-up -> Work -> Volume set structure")
        print(f"  • Adapts to 3, 4, 5+ set exercises automatically")
        print(f"  • Conservative and realistic progressions")

    except Exception as e:
        logging.error(f"Error during flexible progression deployment: {e}")
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check internet connection")
        print("2. Verify Trainerize credentials")
        print("3. Try closing all browser windows first")
        print("4. Run the script again")

    finally:
        # Cleanup
        try:
            automation.cleanup()
            print("\nCleaned up automation resources")
        except:
            pass


if __name__ == "__main__":
    main()
