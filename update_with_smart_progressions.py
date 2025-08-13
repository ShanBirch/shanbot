#!/usr/bin/env python3
"""
Update all clients using the smart progression data
With realistic weight increments based on exercise type
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_smart_progressions():
    """Load the smart progression data"""
    try:
        with open('smart_progressions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No smart progression data found. Run smart_weight_progression.py first.")
        return {}


def update_with_smart_progressions():
    """Update all clients using the smart progression system"""

    print("=== UPDATING CLIENTS WITH SMART PROGRESSIONS ===")

    # Load smart progression data
    all_progressions = load_smart_progressions()

    if not all_progressions:
        print("❌ No smart progression data found")
        return

    print(f"📋 Found smart progressions for {len(all_progressions)} clients:")

    # Show summary with realistic weights
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
    print("💡 Using realistic gym equipment weight increments!")

    # Get user confirmation
    response = input(
        f"\n🤔 Proceed with smart progression updates for all {len(all_progressions)} clients? (y/n): ")
    if response.lower() != 'y':
        print("❌ Update cancelled by user")
        return

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
            f"\n🏋️ Processing {len(all_progressions)} clients with smart progressions...")

        success_count = 0
        failure_count = 0

        for i, (client_name, workouts) in enumerate(all_progressions.items(), 1):
            print(f"\n{'='*60}")
            print(f"CLIENT {i}/{len(all_progressions)}: {client_name}")
            print(f"{'='*60}")

            # Filter to only valid workouts
            valid_workouts = {k: v for k, v in workouts.items() if v}

            if not valid_workouts:
                print(
                    f"  ⏭️ Skipping {client_name} - no valid workout progressions")
                continue

            print(f"  📝 {len(valid_workouts)} workouts to update:")
            for workout_name, exercises in valid_workouts.items():
                print(f"    • {workout_name}: {len(exercises)} exercises")
                # Show sample progression
                if exercises:
                    sample = exercises[0]
                    print(
                        f"      Sample: {sample['exercise_name']} → {sample['weight']}kg x {sample['reps']}")

            # Process this client
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

            print(f"  Status: {'✅ SUCCESS' if result else '❌ FAILED'}")

        # Final summary
        print(f"\n🎉 SMART PROGRESSION UPDATE COMPLETE!")
        print(f"✅ Successful updates: {success_count}")
        print(f"❌ Failed updates: {failure_count}")

        total_processed = success_count + failure_count
        if total_processed > 0:
            success_rate = 100 * success_count / total_processed
            print(
                f"📊 Success rate: {success_count}/{total_processed} ({success_rate:.1f}%)")

        if success_count > 0:
            print(f"\n🏆 SMART PROGRESSIONS DEPLOYED!")
            print(
                f"   • {success_count} clients now have realistic weight progressions")
            print(f"   • All weights align with actual gym equipment")
            print(f"   • Progression logic adapts to exercise type:")
            print(f"     - Dumbbells: 2.5kg increments")
            print(f"     - Barbells: 2.5-5kg increments based on weight")
            print(f"     - Cables: 2.5-5kg increments")
            print(f"     - Machines: 5kg increments")
            print(f"     - Bodyweight: 2.5kg assistance/added weight")

    except Exception as e:
        print(f"Error during smart progression update: {e}")
    finally:
        print(f"\n🧹 Cleaning up...")
        bot.cleanup()


if __name__ == "__main__":
    update_with_smart_progressions()
