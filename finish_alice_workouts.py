#!/usr/bin/env python3
"""
Finish updating Alice Forster's remaining workouts
Ensure proper saving and navigation between workouts
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_alice_remaining_workouts():
    """Get Alice's remaining workouts that need to be updated"""
    try:
        with open('all_clients_progressions.json', 'r') as f:
            all_progressions = json.load(f)
    except FileNotFoundError:
        print("❌ No progression data file found")
        return {}

    alice_workouts = all_progressions.get("Alice Forster", {})

    if not alice_workouts:
        print("❌ No Alice Forster data found")
        return {}

    print(f"📋 Alice's workouts to update:")
    for workout_name, exercises in alice_workouts.items():
        if exercises:  # Only show workouts with exercises
            print(f"  - {workout_name}: {len(exercises)} exercises")

    return alice_workouts


def update_alice_workouts():
    """Update Alice's workouts with proper saving and navigation"""

    print("=== FINISHING ALICE FORSTER'S WORKOUT UPDATES ===")

    # Get Alice's workout data
    alice_workouts = get_alice_remaining_workouts()

    if not alice_workouts:
        return

    # Filter to only valid workouts
    valid_workouts = {k: v for k, v in alice_workouts.items() if v}

    print(f"\n🎯 Total workouts to update: {len(valid_workouts)}")
    for workout_name in valid_workouts.keys():
        print(f"  ✓ {workout_name}")

    # Create Alice's data structure
    alice_data = {"Alice Forster": valid_workouts}

    # Run the workout updater
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

        print(
            f"\n🏋️ Processing Alice Forster's {len(valid_workouts)} workouts...")

        # Process Alice's workouts
        result = bot.process_multiple_clients(alice_data)

        if result:
            print("🎉 SUCCESS! All of Alice's workouts have been updated!")
            print(f"✅ Updated workouts: {list(valid_workouts.keys())}")
        else:
            print("❌ Failed to complete Alice's workout updates")

    except Exception as e:
        print(f"Error during Alice's update: {e}")
    finally:
        bot.cleanup()


def remove_inactive_clients():
    """Remove inactive clients from the progression data"""
    try:
        with open('all_clients_progressions.json', 'r') as f:
            all_progressions = json.load(f)
    except FileNotFoundError:
        print("❌ No progression data file found")
        return

    print("=== REMOVING INACTIVE CLIENTS ===")

    # List of inactive clients to remove
    inactive_clients = ["Kelly Smith"]  # Add more as needed

    # Remove inactive clients
    for client in inactive_clients:
        if client in all_progressions:
            del all_progressions[client]
            print(f"🗑️ Removed inactive client: {client}")
        else:
            print(f"ℹ️ Client {client} not found in data")

    # Save updated data
    with open('all_clients_progressions_filtered.json', 'w') as f:
        json.dump(all_progressions, f, indent=2)

    print(f"💾 Saved filtered data to: all_clients_progressions_filtered.json")
    print(f"📊 Active clients remaining: {len(all_progressions)}")

    for client_name in all_progressions.keys():
        print(f"  ✓ {client_name}")


if __name__ == "__main__":
    # First remove inactive clients
    remove_inactive_clients()

    print("\n" + "="*50 + "\n")

    # Then finish Alice's workouts
    update_alice_workouts()
