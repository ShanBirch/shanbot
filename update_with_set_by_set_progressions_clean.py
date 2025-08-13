#!/usr/bin/env python3
"""
Apply Set-by-Set Progressions to Trainerize
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
            "set_by_set_progressions.json not found. Run smart_coach_clean.py first.")
        return None
    except Exception as e:
        logging.error(f"Error loading set-by-set progressions: {e}")
        return None


def main():
    print("=" * 60)
    print("DYNAMICALLY DISCOVERING AND UPDATING ALL CLIENT WORKOUTS")
    print("=" * 60)

    # Load progression history to get all clients
    try:
        with open('progression_history.json', 'r') as f:
            progression_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: progression_history.json not found!")
        return

    # Filter out test clients and duplicates, get real client names
    real_clients = []
    for client_name in progression_data.keys():
        # Skip test/duplicate entries
        if client_name not in ['Test Client', 'rebecca_dangelo']:
            real_clients.append(client_name)

    print(f"Found {len(real_clients)} clients to update:")
    for i, client in enumerate(sorted(real_clients), 1):
        print(f"  {i}. {client}")

    print(f"\nThis script will now:")
    print(f"  1. Log into Trainerize")
    print(f"  2. For each client:")
    print(f"     - Navigate to their profile")
    print(f"     - Automatically discover all assigned workout programs")
    print(f"     - For each workout, discover all exercises")
    print(f"     - Update each exercise with progression goals based on performance data")
    print(f"     - If no performance data exists, set a default goal of 6 reps")
    print(f"  3. Process all {len(real_clients)} clients systematically")

    # Confirmation
    response = input(
        f"\n⚠️  PROCEED with updating all {len(real_clients)} clients? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Operation cancelled.")
        return

    # Initialize the automation
    automation = TrainerizeAutomation()

    try:
        # Login once for all clients
        print("\n🔐 Logging into Trainerize...")
        if not automation.login("shannonbirch@cocospersonaltraining.com", "cyywp7nyk2"):
            print("❌ Login failed!")
            return

        print("✅ Login successful!")

        # Process each client
        results = {}
        failed_clients = []

        for i, client_name in enumerate(sorted(real_clients), 1):
            print(f"\n{'='*60}")
            print(f"PROCESSING CLIENT {i}/{len(real_clients)}: {client_name}")
            print(f"{'='*60}")

            # Convert display name to database key format
            client_db_key = client_name.lower().replace(' ', '_')

            try:
                # Process this client's workouts
                automation.dynamically_update_client_workouts(client_db_key)
                results[client_name] = "✅ SUCCESS"
                print(f"✅ {client_name}: All workouts updated successfully!")

            except Exception as e:
                error_msg = f"❌ ERROR: {str(e)}"
                results[client_name] = error_msg
                failed_clients.append(client_name)
                logging.error(f"Failed to process {client_name}: {e}")
                print(f"❌ {client_name}: Failed - {str(e)}")

                # Continue to next client instead of stopping
                continue

        # Final summary
        print(f"\n{'='*60}")
        print("FINAL SUMMARY - ALL CLIENTS PROCESSED")
        print(f"{'='*60}")

        successful_clients = len(real_clients) - len(failed_clients)
        print(
            f"✅ Successfully updated: {successful_clients}/{len(real_clients)} clients")

        if failed_clients:
            print(f"❌ Failed clients: {len(failed_clients)}")
            for client in failed_clients:
                print(f"   - {client}")

        print("\n📊 Detailed Results:")
        for client, status in sorted(results.items()):
            print(f"   {client}: {status}")

        print(f"\n🎉 Multi-client workout update complete!")

    except Exception as e:
        logging.error(f"Critical error in main process: {e}")
        print(f"❌ Critical error: {e}")
    finally:
        automation.cleanup()


if __name__ == "__main__":
    main()
