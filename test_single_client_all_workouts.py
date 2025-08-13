#!/usr/bin/env python3
"""
Test processing a single client with multiple workouts
To debug the workout navigation issue
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def test_single_client_multiple_workouts():
    """Test with one client who has multiple workouts"""

    print("=== TESTING SINGLE CLIENT - MULTIPLE WORKOUTS ===")

    # Load the data
    try:
        with open('all_clients_progressions_filtered.json', 'r') as f:
            all_progressions = json.load(f)
    except FileNotFoundError:
        print("❌ No filtered progression data found")
        return

    # Pick a client who isn't Alice (to avoid the twice issue)
    # Let's use Nicole Lynch as she has 4 workouts
    test_client = "Nicole Lynch"

    if test_client not in all_progressions:
        print(f"❌ {test_client} not found in data")
        # Show available clients
        print("Available clients:")
        for client_name in all_progressions.keys():
            print(f"  - {client_name}")
        return

    # Get the client's workouts
    client_workouts = all_progressions[test_client]
    valid_workouts = {k: v for k, v in client_workouts.items() if v}

    print(f"📋 Testing {test_client}:")
    print(f"   - {len(valid_workouts)} workouts to process")
    for workout_name, exercises in valid_workouts.items():
        print(f"   - {workout_name}: {len(exercises)} exercises")

    # Create test data
    test_data = {test_client: valid_workouts}

    # Run the test
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    bot = TrainerizeAutomation()

    try:
        print("\n🔐 Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            return
        print("✅ Login successful!")

        bot.handle_notification_popup()

        print(f"\n🏋️ Processing {test_client}'s workouts...")

        # Process the client
        result = bot.process_multiple_clients(test_data)

        if result:
            print(f"🎉 SUCCESS! {test_client} updated successfully!")
        else:
            print(f"❌ Failed to update {test_client}")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_single_client_multiple_workouts()
