#!/usr/bin/env python3
"""
Simple navigation test - just test going back from workout to program
"""

from weekly_program_updater import TrainerizeAutomation
import time


def test_navigation():
    print("=== NAVIGATION TEST ===")

    bot = TrainerizeAutomation()

    try:
        # Login
        print("1. Logging in...")
        if not bot.login("Shannonbirch@cocospersonaltraining.com", "cyywp7nyk2"):
            print("❌ Login failed")
            return
        print("✅ Login successful")

        bot.handle_notification_popup()

        # Navigate to client
        print("2. Navigate to Shannon Birch...")
        if not bot.navigate_to_client("Shannon Birch"):
            print("❌ Client navigation failed")
            return
        print("✅ Client navigation successful")

        # Navigate to training program
        print("3. Navigate to training program...")
        if not bot.navigate_to_training_program():
            print("❌ Training program navigation failed")
            return
        print("✅ Training program navigation successful")

        # Find and click program
        print("4. Find current program...")
        current_program = bot.find_current_workout_program()
        if not current_program:
            print("❌ No current program found")
            return
        print(f"✅ Found program: {current_program}")

        print("5. Click program...")
        if not bot.click_program(current_program):
            print("❌ Program click failed")
            return
        print("✅ Program clicked")

        # Now test the navigation issue
        print("6. Click a workout...")
        if not bot.find_and_click_workout_by_name("Back Day"):
            print("❌ Workout click failed")
            return
        print("✅ Workout clicked")

        print("Current URL:", bot.driver.current_url)
        input("Press Enter after you see the workout page...")

        # THIS IS THE PROBLEM AREA - test different ways to get back
        print("7. Testing navigation back to program...")

        # Try URL navigation first (most reliable)
        current_url = bot.driver.current_url
        if "/workout/" in current_url:
            program_url = current_url.split("/workout/")[0]
            print(f"Navigating back to: {program_url}")
            bot.driver.get(program_url)
            time.sleep(3)
            print("✅ URL navigation successful")
            print("New URL:", bot.driver.current_url)
        else:
            print("❌ URL navigation failed - no workout in URL")

        input("Press Enter to continue to next workout...")

        # Try clicking another workout
        print("8. Click second workout...")
        if not bot.find_and_click_workout_by_name("Chest Day"):
            print("❌ Second workout click failed")
        else:
            print("✅ Second workout clicked")

        input("Press Enter to finish...")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_navigation()
