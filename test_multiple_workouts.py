#!/usr/bin/env python3
"""
Test the fixed multiple workout processing
"""

from weekly_program_updater import TrainerizeAutomation


def test_multiple_workouts():
    print("=== TESTING MULTIPLE WORKOUTS ===")
    print("This will test processing 2 workouts in sequence")

    # Test data with 2 workouts
    test_data = {
        "Shannon Birch": {
            "Back Day": [
                {"action": "modify_goals", "exercise_name": "Lat Pulldown",
                    "weight": "35", "reps": "8"}
            ],
            "Chest Day": [
                {"action": "modify_goals", "exercise_name": "Bench Press",
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

        print("Starting multiple client processing...")
        results = bot.process_multiple_clients(test_data)

        # Print results
        print("\n=== RESULTS ===")
        for client_name, client_results in results.items():
            print(f"\nClient: {client_name}")
            print(f"Status: {client_results.get('status', 'unknown')}")

            for key, value in client_results.items():
                if key not in ['status', 'error']:
                    print(f"  {key}: {value}")

        if results.get("Shannon Birch", {}).get("status") == "success":
            print("\n🎉 SUCCESS! Multiple workouts processed correctly!")
        else:
            print("\n❌ FAILED! Check the results above.")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_multiple_workouts()
