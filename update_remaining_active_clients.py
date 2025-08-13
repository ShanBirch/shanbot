#!/usr/bin/env python3
"""
Update remaining active clients' workout goals 
Using the filtered progression data (excluding inactive clients)
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


def update_all_active_clients():
    """Update workouts for all active clients"""

    print("=== UPDATING ALL ACTIVE CLIENTS' WORKOUTS ===")

    # Load active clients data
    all_progressions = load_active_clients_data()

    if not all_progressions:
        print("❌ No progression data found")
        return

    print(f"📋 Found {len(all_progressions)} active clients:")

    # Show summary
    total_workouts = 0
    total_exercises = 0

    for client_name, workouts in all_progressions.items():
        valid_workouts = {k: v for k, v in workouts.items() if v}
        workout_count = len(valid_workouts)
        exercise_count = sum(len(exercises)
                             for exercises in valid_workouts.values())

        total_workouts += workout_count
        total_exercises += exercise_count

        print(
            f"  - {client_name}: {workout_count} workouts, {exercise_count} exercises")

    print(f"\n🎯 TOTAL: {total_workouts} workouts, {total_exercises} exercises")

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

        print(f"\n🏋️ Processing {len(all_progressions)} active clients...")

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

            print(f"  📝 {len(valid_workouts)} workouts to update:")
            for workout_name in valid_workouts.keys():
                exercise_count = len(valid_workouts[workout_name])
                print(f"    • {workout_name}: {exercise_count} exercises")

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

        # Final summary
        if success_count > 0:
            print(f"\n🏆 MISSION ACCOMPLISHED!")
            print(
                f"   • {success_count} clients updated with progressive overload")
            print(f"   • All workout goals increased for continued progress")
            print(f"   • System ready for weekly automated updates")

    except Exception as e:
        print(f"Error during batch update: {e}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    update_all_active_clients()
