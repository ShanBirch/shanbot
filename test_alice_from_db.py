#!/usr/bin/env python3
"""
Test Alice Forster with real data from SQLite database
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
from weekly_program_updater import TrainerizeAutomation


def get_alice_workout_data():
    """Extract Alice Forster's workout data from SQLite"""
    try:
        conn = sqlite3.connect('analytics_data_good.sqlite')
        cursor = conn.cursor()

        # First, let's see what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Available tables:", tables)

        # Look for Alice's data in workout tables
        # Try different possible client identifiers
        alice_identifiers = ['alice_forster',
                             'Alice Forster', 'alice forster', 'Alice_Forster']

        alice_data = []

        for table_name in ['workout_sessions', 'workouts', 'client_workouts', 'analytics_data']:
            try:
                # Check if table exists
                cursor.execute(f"SELECT * FROM {table_name[0]} LIMIT 1")

                # Try to find Alice's data
                for identifier in alice_identifiers:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name[0]} WHERE client_name LIKE ? OR ig_username LIKE ?",
                                       (f'%{identifier}%', f'%{identifier}%'))
                        results = cursor.fetchall()
                        if results:
                            print(
                                f"\nFound {len(results)} records for Alice in {table_name[0]}")
                            # Get column names
                            cursor.execute(
                                f"PRAGMA table_info({table_name[0]})")
                            columns = [col[1] for col in cursor.fetchall()]

                            # Convert to dictionaries
                            for row in results:
                                record = dict(zip(columns, row))
                                alice_data.append(record)
                            break
                    except Exception as e:
                        continue

            except Exception as e:
                continue

        conn.close()
        return alice_data

    except Exception as e:
        print(f"Error accessing SQLite database: {e}")
        return []


def analyze_alice_progression(workout_data):
    """Analyze Alice's workout data to determine progressions"""
    if not workout_data:
        print("No workout data found for Alice")
        return None

    print(f"\nAnalyzing {len(workout_data)} workout records for Alice...")

    # Group exercises by name and analyze progression
    exercise_groups = defaultdict(list)

    for record in workout_data:
        # Extract exercise information from the record
        exercise_name = record.get('exercise_name', '')
        weight = record.get('weight', 0)
        reps = record.get('reps', 0)
        date = record.get('date', record.get('workout_date', ''))

        if exercise_name and weight and reps:
            exercise_groups[exercise_name].append({
                'weight': float(weight) if weight else 0,
                'reps': int(reps) if reps else 0,
                'date': date
            })

    # Generate progressions based on recent performance
    progressions = {}

    for exercise_name, performances in exercise_groups.items():
        if len(performances) >= 2:
            # Sort by date and get recent performance
            performances.sort(key=lambda x: x['date'], reverse=True)
            recent = performances[0]

            # Simple progression logic: increase weight by 2.5kg or reps by 1
            new_weight = recent['weight'] + 2.5
            new_reps = recent['reps']

            # If weight is getting too high, increase reps instead
            if new_weight > recent['weight'] * 1.2:
                new_weight = recent['weight']
                new_reps = min(recent['reps'] + 1, 15)

            progressions[exercise_name] = {
                'current_weight': recent['weight'],
                'current_reps': recent['reps'],
                'new_weight': str(int(new_weight)),
                'new_reps': str(new_reps)
            }

    return progressions


def create_alice_test_data():
    """Create test data for Alice based on actual database analysis"""
    print("=== ALICE FORSTER DATABASE ANALYSIS ===")

    # Get Alice's data from database
    workout_data = get_alice_workout_data()

    if workout_data:
        print("\nSample records:")
        for i, record in enumerate(workout_data[:3]):
            print(f"Record {i+1}: {record}")

        # Analyze progressions
        progressions = analyze_alice_progression(workout_data)

        if progressions:
            print(
                f"\nGenerated progressions for {len(progressions)} exercises:")
            for exercise, prog in progressions.items():
                print(
                    f"  {exercise}: {prog['current_weight']}kg/{prog['current_reps']} → {prog['new_weight']}kg/{prog['new_reps']}")

            # Create workout groups (you'll need to categorize exercises)
            # For now, let's create a sample structure
            return create_workout_structure_from_progressions(progressions)
        else:
            print("Could not generate progressions from database data")
    else:
        print("No data found in database, using sample data for Alice")

    # Fallback: Create sample data for Alice
    return {
        "Alice Forster": {
            "Upper Body": [
                {"action": "modify_goals", "exercise_name": "Lat Pull Down Wide Grip",
                    "weight": "30", "reps": "10"},
                {"action": "modify_goals", "exercise_name": "Barbell Bench Chest Press",
                    "weight": "40", "reps": "8"}
            ],
            "Lower Body": [
                {"action": "modify_goals", "exercise_name": "Leg Press",
                    "weight": "80", "reps": "12"},
                {"action": "modify_goals", "exercise_name": "Romanian Deadlift",
                    "weight": "35", "reps": "10"}
            ]
        }
    }


def create_workout_structure_from_progressions(progressions):
    """Convert exercise progressions into workout structure"""
    # Categorize exercises into workout types
    upper_body_keywords = ['pull', 'press', 'chest',
                           'shoulder', 'arm', 'bicep', 'tricep', 'lat', 'row']
    lower_body_keywords = ['squat', 'leg',
                           'deadlift', 'lunge', 'calf', 'glute', 'hip']

    workout_structure = {"Alice Forster": {}}
    upper_exercises = []
    lower_exercises = []
    other_exercises = []

    for exercise_name, prog in progressions.items():
        exercise_lower = exercise_name.lower()

        action = {
            "action": "modify_goals",
            "exercise_name": exercise_name,
            "weight": prog['new_weight'],
            "reps": prog['new_reps']
        }

        if any(keyword in exercise_lower for keyword in upper_body_keywords):
            upper_exercises.append(action)
        elif any(keyword in exercise_lower for keyword in lower_body_keywords):
            lower_exercises.append(action)
        else:
            other_exercises.append(action)

    # Assign to workouts
    if upper_exercises:
        workout_structure["Alice Forster"]["Upper Body"] = upper_exercises
    if lower_exercises:
        workout_structure["Alice Forster"]["Lower Body"] = lower_exercises
    if other_exercises:
        workout_structure["Alice Forster"]["General"] = other_exercises

    return workout_structure


def test_alice_workout_updater():
    """Test the workout updater with Alice's data"""
    print("\n=== TESTING ALICE FORSTER WORKOUT UPDATER ===")

    # Get Alice's test data
    test_data = create_alice_test_data()

    if not test_data.get("Alice Forster"):
        print("❌ No test data generated for Alice")
        return

    print(f"\nTest data structure:")
    for client, workouts in test_data.items():
        print(f"Client: {client}")
        for workout_name, actions in workouts.items():
            print(f"  {workout_name}: {len(actions)} actions")
            for action in actions:
                print(
                    f"    - {action['action']}: {action['exercise_name']} → {action.get('weight', 'N/A')}kg/{action.get('reps', 'N/A')}")

    # First, let's inspect Alice's actual workouts to get correct names
    print("\n=== INSPECTING ALICE'S ACTUAL WORKOUTS ===")

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

        # Navigate to Alice
        print("Navigating to Alice Forster...")
        if not bot.navigate_to_client("Alice Forster"):
            print("❌ Could not navigate to Alice Forster")
            return
        print("✅ Navigated to Alice Forster")

        if not bot.navigate_to_training_program():
            print("❌ Training program navigation failed")
            return

        current_program = bot.find_current_workout_program()
        if not current_program:
            print("❌ No current program found for Alice")
            return
        print(f"✅ Found Alice's program: {current_program}")

        if not bot.click_program(current_program):
            print("❌ Program click failed")
            return

        # Find Alice's actual workouts
        print("\nInspecting Alice's workouts...")

        # Try to find common workout names
        workout_names_to_try = ["Upper Body", "Lower Body", "Full Body", "Strength", "Cardio",
                                "Push", "Pull", "Legs", "Arms", "Back", "Chest"]

        alice_workouts = []
        for workout_name in workout_names_to_try:
            if bot.find_and_click_workout_by_name(workout_name):
                alice_workouts.append(workout_name)
                print(f"✅ Found workout: {workout_name}")
                bot.navigate_back_to_program()
            else:
                print(f"❌ Workout not found: {workout_name}")

        if alice_workouts:
            print(f"\nAlice's available workouts: {alice_workouts}")

            # Create updated test data with correct workout names
            updated_test_data = {"Alice Forster": {}}

            # Use the first available workout for testing
            if alice_workouts:
                first_workout = alice_workouts[0]
                updated_test_data["Alice Forster"][first_workout] = [
                    {"action": "modify_goals", "exercise_name": "Lat Pull Down Wide Grip",
                        "weight": "35", "reps": "8"}
                ]

                print(f"\nTesting with updated data structure:")
                print(
                    f"Alice Forster -> {first_workout}: modify Lat Pull Down Wide Grip")

                # Now test the actual workout updater
                print(f"\n=== RUNNING WORKOUT UPDATER FOR ALICE ===")
                results = bot.process_multiple_clients(updated_test_data)

                # Print results
                print("\n=== ALICE RESULTS ===")
                for client_name, client_results in results.items():
                    print(f"Client: {client_name}")
                    print(f"Status: {client_results.get('status', 'unknown')}")

                    for key, value in client_results.items():
                        if key not in ['status', 'error']:
                            print(f"  {key}: {value}")

                if results.get("Alice Forster", {}).get("status") == "success":
                    print("\n🎉 SUCCESS! Alice's workout updated successfully!")
                else:
                    print(
                        f"\n❌ Failed. Status: {results.get('Alice Forster', {}).get('status', 'unknown')}")
        else:
            print("❌ Could not find any workouts for Alice")

    except Exception as e:
        print(f"❌ Error during Alice test: {e}")

    finally:
        bot.cleanup()


if __name__ == "__main__":
    test_alice_workout_updater()
