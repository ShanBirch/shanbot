#!/usr/bin/env python3
"""
Update clients one by one to avoid repeating workouts
Process each client completely before moving to the next
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_active_clients_data():
    """Load the filtered progression data for active clients"""
    try:
        with open('all_clients_progressions_filtered.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No filtered progression data found")
        return {}


def update_single_client(client_name, workouts, bot):
    """Update a single client's workouts"""
    print(f"\n🎯 PROCESSING: {client_name}")

    # Filter to only valid workouts
    valid_workouts = {k: v for k, v in workouts.items() if v}

    if not valid_workouts:
        print(f"  ⏭️ Skipping {client_name} - no valid workout progressions")
        return False

    print(f"  📝 {len(valid_workouts)} workouts to update:")
    for workout_name, exercises in valid_workouts.items():
        print(f"    • {workout_name}: {len(exercises)} exercises")

    # Create single client data structure
    single_client_data = {client_name: valid_workouts}

    try:
        # Process this client's workouts
        result = bot.process_multiple_clients(single_client_data)

        if result:
            print(f"✅ Successfully updated {client_name}")
            return True
        else:
            print(f"❌ Failed to update {client_name}")
            return False

    except Exception as e:
        print(f"❌ Error updating {client_name}: {e}")
        return False


def update_clients_sequentially():
    """Update all clients one by one sequentially"""

    print("=== UPDATING CLIENTS ONE BY ONE ===")

    # Load active clients data
    all_progressions = load_active_clients_data()

    if not all_progressions:
        print("❌ No progression data found")
        return

    # Show what we're about to process
    print(f"📋 Found {len(all_progressions)} active clients to process:")
    for i, (client_name, workouts) in enumerate(all_progressions.items(), 1):
        valid_workouts = {k: v for k, v in workouts.items() if v}
        workout_count = len(valid_workouts)
        exercise_count = sum(len(exercises)
                             for exercises in valid_workouts.values())
        print(
            f"  {i}. {client_name}: {workout_count} workouts, {exercise_count} exercises")

    # Get user confirmation
    response = input(
        f"\n🤔 Proceed with updating all {len(all_progressions)} clients? (y/n): ")
    if response.lower() != 'y':
        print("❌ Update cancelled by user")
        return

    # Initialize the bot once
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

        # Process each client one by one
        success_count = 0
        failure_count = 0

        for i, (client_name, workouts) in enumerate(all_progressions.items(), 1):
            print(f"\n{'='*60}")
            print(f"CLIENT {i}/{len(all_progressions)}: {client_name}")
            print(f"{'='*60}")

            result = update_single_client(client_name, workouts, bot)

            if result:
                success_count += 1
            else:
                failure_count += 1

            print(f"  Status: {'✅ SUCCESS' if result else '❌ FAILED'}")

            # Small pause between clients
            if i < len(all_progressions):
                print(f"\n⏳ Preparing for next client...")

        # Final summary
        print(f"\n🎉 ALL CLIENTS PROCESSED!")
        print(f"✅ Successful updates: {success_count}")
        print(f"❌ Failed updates: {failure_count}")

        total_processed = success_count + failure_count
        if total_processed > 0:
            success_rate = 100 * success_count / total_processed
            print(
                f"📊 Success rate: {success_count}/{total_processed} ({success_rate:.1f}%)")

        if success_count > 0:
            print(f"\n🏆 MISSION ACCOMPLISHED!")
            print(
                f"   • {success_count} clients updated with progressive overload")
            print(f"   • All workout goals increased for continued progress")
            print(f"   • System ready for weekly automated updates")

    except Exception as e:
        print(f"Error during client updates: {e}")
    finally:
        print(f"\n🧹 Cleaning up...")
        bot.cleanup()


if __name__ == "__main__":
    update_clients_sequentially()
