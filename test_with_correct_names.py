#!/usr/bin/env python3
"""
Final test with correct exercise names
"""

from weekly_program_updater import TrainerizeAutomation


def test_with_correct_names():
    print("=== FINAL TEST WITH CORRECT EXERCISE NAMES ===")

    # Test data with CORRECT exercise names
    test_data = {
        "Shannon Birch": {
            "Back Day": [
                {"action": "modify_goals", "exercise_name": "Lat Pull Down Wide Grip",
                    "weight": "35", "reps": "8"}
            ],
            "Chest Day": [
                {"action": "modify_goals", "exercise_name": "Barbell Bench Chest Press",
                    "weight": "45", "reps": "10"}
            ]
        }
    }

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

        print("Starting processing with correct exercise names...")
        results = bot.process_multiple_clients(test_data)

        # Print results
        print("\n=== FINAL RESULTS ===")
        for client_name, client_results in results.items():
            print(f"\nClient: {client_name}")
            print(f"Status: {client_results.get('status', 'unknown')}")

            for key, value in client_results.items():
                if key not in ['status', 'error']:
                    print(f"  {key}: {value}")

        if results.get("Shannon Birch", {}).get("status") == "success":
            print("\n🎉🎉🎉 COMPLETE SUCCESS! 🎉🎉🎉")
            print("The weekly program updater is now working correctly!")
            print("✅ Navigation between workouts: FIXED")
            print("✅ Exercise goal modification: WORKING")
            print("✅ Multiple workouts processing: WORKING")
        else:
            print(
                f"\n❌ Status: {results.get('Shannon Birch', {}).get('status', 'unknown')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_with_correct_names()
