#!/usr/bin/env python3
"""
Test Alice Forster with her REAL workout data from the database
"""

import sqlite3
import json
from weekly_program_updater import TrainerizeAutomation


def get_alice_real_workouts():
    """Get Alice's actual workout names and exercises from the database"""
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        print("=== EXTRACTING ALICE'S REAL WORKOUT DATA ===")

        # Get Alice's recent workouts
        cursor.execute("""
            SELECT workout_date, workout_name, exercises_json 
            FROM client_workout_sessions 
            WHERE client_name_key = 'alice_forster' 
            ORDER BY workout_date DESC 
            LIMIT 5
        """)

        workouts = cursor.fetchall()
        workout_data = {}

        for date, workout_name, exercises_json in workouts:
            exercises = json.loads(exercises_json)
            print(f"\n📅 {date} - {workout_name}:")

            workout_data[workout_name] = []

            for exercise in exercises:
                exercise_name = exercise.get('name', 'Unknown')
                sets = exercise.get('sets', [])

                if sets:
                    # Get the latest set data for progression
                    latest_set = sets[-1] if sets else {}
                    weight = latest_set.get('weight', '20')  # Default weight
                    reps = latest_set.get('reps', '8')       # Default reps

                    print(
                        f"  - {exercise_name}: {len(sets)} sets (last: {weight}kg x {reps} reps)")

                    # Create progression: increase weight by 2.5kg or reps by 1
                    new_weight = str(float(weight) + 2.5) if weight else "22.5"
                    new_reps = str(int(reps) + 1) if reps else "9"

                    workout_data[workout_name].append({
                        "action": "modify_goals",
                        "exercise_name": exercise_name,
                        "weight": new_weight,
                        "reps": new_reps
                    })
                else:
                    print(f"  - {exercise_name}: No sets data")

        conn.close()
        return workout_data

    except Exception as e:
        print(f"Database error: {e}")
        return {}


def create_alice_progression_data():
    """Create progression data for Alice based on her real workouts"""

    workout_data = get_alice_real_workouts()

    if not workout_data:
        print("❌ No workout data found for Alice")
        return None

    # Focus on her most recent workout (Back Day)
    progression_data = {
        "Alice Forster": {
            "Back Day": workout_data.get("Back Day", [
                {"action": "modify_goals", "exercise_name": "Lat Pull Down Wide Grip",
                    "weight": "37.5", "reps": "9"}
            ])
        }
    }

    print(f"\n🎯 CREATED PROGRESSION DATA FOR ALICE:")
    print(json.dumps(progression_data, indent=2))

    return progression_data


def test_alice_with_real_data():
    """Test the workout updater with Alice's real workout data"""

    print("=== TESTING ALICE WITH REAL WORKOUT DATA ===")

    # Get Alice's real progression data
    progression_data = create_alice_progression_data()

    if not progression_data:
        return

    # Run the workout updater
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    bot = TrainerizeAutomation()

    try:
        print("\n1. Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            return
        print("✅ Login successful!")

        bot.handle_notification_popup()

        print("\n2. Processing Alice's workout progressions...")
        result = bot.process_multiple_clients(progression_data)

        if result:
            print(
                "🎉 SUCCESS! Alice's workouts have been updated with progressive overload!")
        else:
            print("❌ Failed to update Alice's workouts")

    except Exception as e:
        print(f"Error during workout update: {e}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_alice_with_real_data()
