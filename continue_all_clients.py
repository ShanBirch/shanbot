#!/usr/bin/env python3
"""
Continue updating ALL clients' workout goals with progressive overload
Using the existing progression data and better name handling
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_progression_data():
    """Load the existing progression data"""
    try:
        with open('all_clients_progressions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No progression data file found. Run update_all_clients.py first.")
        return {}


def get_client_name_mappings():
    """Define mappings for client names that might not match exactly"""
    return {
        "Kelly Smith": "Kelly Smith",  # Try exact first
        "Alice Forster": "Alice Forster",
        "Kylie Pinder": "Kylie Pinder",
        "Nicole Lynch": "Nicole Lynch",
        "Shane Minahan": "Shane Minahan",
        "Kristy Cooper": "Kristy Cooper",
        "Anna Somogyi": "Anna Somogyi",
        "Elena Green": "Elena Green",
        "Raechel Muller": "Raechel Muller",
        "Jen Frayne": "Jen Frayne",
        "Jo Schiavetta": "Jo Schiavetta"
    }


def update_remaining_clients():
    """Update all clients from the progression data"""

    print("=== CONTINUING CLIENT WORKOUT UPDATES ===")

    # Load progression data
    all_progressions = load_progression_data()

    if not all_progressions:
        print("❌ No progression data found")
        return

    print(f"📋 Found progression data for {len(all_progressions)} clients")

    # Show what we have
    for client_name, workouts in all_progressions.items():
        # Count non-empty workouts
        workout_count = len([w for w in workouts.values() if w])
        print(f"  - {client_name}: {workout_count} workouts")

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

        print(f"\n🏋️ Processing {len(all_progressions)} clients...")

        success_count = 0
        failure_count = 0
        skipped_count = 0

        for i, (client_name, workouts) in enumerate(all_progressions.items(), 1):
            print(f"\n--- {i}/{len(all_progressions)}: {client_name} ---")

            # Skip clients with no workout progressions
            valid_workouts = {k: v for k, v in workouts.items() if v}
            if not valid_workouts:
                print(
                    f"  ⏭️ Skipping {client_name} - no valid workout progressions")
                skipped_count += 1
                continue

            print(
                f"  📝 {len(valid_workouts)} workouts to update: {list(valid_workouts.keys())}")

            # Process one client at a time
            single_client_data = {client_name: valid_workouts}

            try:
                result = bot.process_multiple_clients(single_client_data)
                if result:
                    success_count += 1
                    print(f"✅ Successfully updated {client_name}")
                else:
                    failure_count += 1
                    print(f"❌ Failed to update {client_name}")
            except Exception as e:
                failure_count += 1
                print(f"❌ Error updating {client_name}: {e}")

        print(f"\n🎉 BATCH UPDATE COMPLETE!")
        print(f"✅ Successful updates: {success_count}")
        print(f"❌ Failed updates: {failure_count}")
        print(f"⏭️ Skipped (no data): {skipped_count}")

        total_processed = success_count + failure_count
        if total_processed > 0:
            success_rate = 100 * success_count / total_processed
            print(
                f"📊 Success rate: {success_count}/{total_processed} ({success_rate:.1f}%)")

    except Exception as e:
        print(f"Error during batch update: {e}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    update_remaining_clients()
