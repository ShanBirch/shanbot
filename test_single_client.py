#!/usr/bin/env python3
"""
Minimal test script for debugging the weekly program updater
Tests just one client with one workout to isolate issues
"""

import logging
from weekly_program_updater_debug import DebugTrainerizeAutomation


def main():
    print("=== MINIMAL TEST - SINGLE CLIENT, SINGLE WORKOUT ===")
    print("This will test the navigation between workouts step by step")
    print()

    # Minimal test data
    test_data = {
        "Shannon Birch": {
            "Back Day": [
                {"action": "modify_goals", "exercise_name": "Lat Pulldown",
                    "weight": "35", "reps": "8"}
            ]
        }
    }

    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    trainerize_bot = DebugTrainerizeAutomation()

    try:
        print("Step 1: Login")
        if not trainerize_bot.login(username, password):
            print("❌ Login failed!")
            return
        print("✅ Login successful!")

        print("\nStep 2: Handle notifications")
        trainerize_bot.handle_notification_popup()

        print("\nStep 3: Navigate to client")
        client_name = "Shannon Birch"
        if not trainerize_bot.navigate_to_client(client_name):
            print(f"❌ Failed to navigate to client: {client_name}")
            return
        print(f"✅ Navigated to client: {client_name}")

        print("\nStep 4: Navigate to training program")
        if not trainerize_bot.navigate_to_training_program():
            print("❌ Failed to navigate to training program")
            return
        print("✅ Navigated to training program")

        print("\nStep 5: Find current program")
        current_program = trainerize_bot.find_current_workout_program()
        if not current_program:
            print("❌ Could not find current program")
            return
        print(f"✅ Found current program: {current_program}")

        print("\nStep 6: Click program")
        if not trainerize_bot.click_program(current_program):
            print(f"❌ Failed to click program: {current_program}")
            return
        print(f"✅ Clicked program: {current_program}")

        print("\nStep 7: Process single workout")
        workout_name = "Back Day"
        actions = test_data["Shannon Birch"]["Back Day"]

        success = trainerize_bot.enhanced_process_single_workout(
            workout_name, actions)

        if success:
            print(f"✅ Successfully processed workout: {workout_name}")
        else:
            print(f"❌ Failed to process workout: {workout_name}")

        print(f"\nDebug files saved to: {trainerize_bot.debug_folder}")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        logging.error(f"Test error: {e}")

    finally:
        input("\nPress Enter to cleanup and exit...")
        trainerize_bot.cleanup()


if __name__ == "__main__":
    main()
