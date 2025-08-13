#!/usr/bin/env python3
"""
Inspect workouts to see what exercises actually exist
"""

from weekly_program_updater import TrainerizeAutomation
from selenium.webdriver.common.by import By


def inspect_workouts():
    print("=== WORKOUT INSPECTOR ===")
    print("This will show what exercises exist in each workout")

    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    bot = TrainerizeAutomation()

    try:
        print("Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            return
        print("✅ Login successful!")

        bot.handle_notification_popup()

        # Navigate to client and program
        print("Navigating to Shannon Birch...")
        if not bot.navigate_to_client("Shannon Birch"):
            print("❌ Client navigation failed")
            return

        if not bot.navigate_to_training_program():
            print("❌ Training program navigation failed")
            return

        current_program = bot.find_current_workout_program()
        if not current_program:
            print("❌ No current program found")
            return
        print(f"Found program: {current_program}")

        if not bot.click_program(current_program):
            print("❌ Program click failed")
            return

        # Inspect each workout
        workouts_to_inspect = ["Back Day", "Chest Day"]

        for workout_name in workouts_to_inspect:
            print(f"\n=== INSPECTING {workout_name} ===")

            # Click workout
            if not bot.find_and_click_workout_by_name(workout_name):
                print(f"❌ Could not find workout: {workout_name}")
                continue

            # Enter edit mode
            if not bot.click_edit_workout():
                print(f"❌ Could not enter edit mode for: {workout_name}")
                continue

            # Wait for builder to load
            import time
            time.sleep(3)

            # Find all exercises in the workout
            try:
                exercise_elements = bot.driver.find_elements(
                    By.XPATH, "//div[@class='exerciseList-exercise__name ']")

                if exercise_elements:
                    print(
                        f"Found {len(exercise_elements)} exercises in {workout_name}:")
                    for i, element in enumerate(exercise_elements, 1):
                        exercise_name = element.text
                        title = element.get_attribute('title')
                        print(
                            f"  {i}. Name: '{exercise_name}' | Title: '{title}'")
                else:
                    print(f"❌ No exercises found in {workout_name}")

            except Exception as e:
                print(f"❌ Error finding exercises: {e}")

            # Navigate back to program
            if not bot.navigate_back_to_program():
                print("❌ Failed to navigate back")
                break

        print("\n=== INSPECTION COMPLETE ===")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        input("Press Enter to cleanup...")
        bot.cleanup()


if __name__ == "__main__":
    inspect_workouts()
