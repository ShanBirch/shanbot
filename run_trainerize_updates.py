#!/usr/bin/env python3
"""
Run Trainerize Updates
======================

This script uses the existing progression_history.json file 
to update all client workouts in Trainerize.

Usage: python run_trainerize_updates.py
"""

import json
import logging
import sys
from weekly_program_updater import TrainerizeAutomation

# Configure logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trainerize_updates.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)


def load_progression_history():
    """Load the existing progression_history.json file"""
    try:
        with open('progression_history.json', 'r') as f:
            data = json.load(f)
        print(f"Loaded progression data for {len(data)} clients")
        return data
    except FileNotFoundError:
        print("ERROR: progression_history.json not found!")
        print("Please run the data analysis first to create this file.")
        return None
    except Exception as e:
        print(f"Error loading progression history: {e}")
        return None


def main():
    print("=" * 60)
    print("TRAINERIZE WORKOUT UPDATER")
    print("=" * 60)

    # Load existing progression data
    progression_data = load_progression_history()
    if not progression_data:
        return

    # Show summary
    total_exercises = 0
    for client_data in progression_data.values():
        if isinstance(client_data, list) and len(client_data) > 0:
            progressions = client_data[0].get('progressions', {})
            total_exercises += len(progressions)

    print(f"\nProgression Summary:")
    print(f"  - {len(progression_data)} clients")
    print(f"  - {total_exercises} exercises to update")
    print(f"  - Algorithm: 6->8->10->12->15 reps, then increase weight")

    # Show client list
    print(f"\nClients to update:")
    for client_name in progression_data.keys():
        display_name = client_name.replace('_', ' ').title()
        print(f"  - {display_name}")

    # Confirm before proceeding
    response = input(
        f"\nProceed with updating all {len(progression_data)} clients in Trainerize? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    # Initialize Trainerize automation
    print("\nInitializing Trainerize automation...")
    try:
        automation = TrainerizeAutomation()

        # Login credentials
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        print("Logging into Trainerize...")
        if not automation.login(username, password):
            print("ERROR: Failed to login to Trainerize")
            return

        print("SUCCESS: Logged into Trainerize!")

        # Process all clients
        print(f"\nProcessing {len(progression_data)} clients...")
        results = automation.process_multiple_clients(progression_data)

        # Show final results
        print("\n" + "=" * 60)
        print("TRAINERIZE UPDATE COMPLETE")
        print("=" * 60)

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\nFinal Results:")
        print(f"  Successfully updated: {successful} clients")
        print(f"  Failed: {failed} clients")

        if successful > 0:
            print(f"\nSuccessfully updated clients:")
            for client, result in results.items():
                if result.get('status') == 'success':
                    display_name = client.replace('_', ' ').title()
                    print(f"  - {display_name}")

        if failed > 0:
            print(f"\nFailed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    display_name = client.replace('_', ' ').title()
                    error = result.get('error', 'Unknown error')
                    print(f"  - {display_name}: {error}")

        print(f"\nAll successful clients now have updated workout progressions!")
        print(f"Next steps: Your clients will see their new goals in Trainerize.")

    except Exception as e:
        logging.error(f"Error during Trainerize automation: {e}")
        print(f"ERROR: {e}")

    finally:
        # Cleanup
        try:
            automation.cleanup()
            print("\nCleanup completed.")
        except:
            pass


if __name__ == "__main__":
    main()
