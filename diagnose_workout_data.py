#!/usr/bin/env python3
"""
Diagnose workout data storage issues for progression updater
"""

import sqlite3
import json


def diagnose_alice_workouts():
    print("🔍 DIAGNOSING ALICE'S WORKOUT DATA STORAGE")
    print("=" * 60)

    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Get Alice's recent workout sessions with full details
        cursor.execute("""
            SELECT workout_date, workout_name, exercises_json 
            FROM client_workout_sessions 
            WHERE client_name_key = 'alice_forster' 
            ORDER BY workout_date DESC 
            LIMIT 3
        """)

        sessions = cursor.fetchall()
        print(f"📊 Found {len(sessions)} recent Alice sessions")

        for i, (date, name, exercises_json) in enumerate(sessions, 1):
            print(f"\n🏋️ Session {i}: {date} - {name}")
            print(
                f"   Raw data length: {len(exercises_json) if exercises_json else 0} characters")

            if exercises_json:
                print(f"   Raw data preview: {exercises_json[:200]}...")

                try:
                    exercises_data = json.loads(exercises_json)
                    print(f"   Parsed data type: {type(exercises_data)}")

                    if isinstance(exercises_data, dict):
                        print(f"   Dict keys: {list(exercises_data.keys())}")
                        if exercises_data:
                            # Check first exercise
                            first_key = list(exercises_data.keys())[0]
                            first_exercise = exercises_data[first_key]
                            print(
                                f"   First exercise ({first_key}): {type(first_exercise)}")
                            if isinstance(first_exercise, dict):
                                print(
                                    f"   Exercise structure: {list(first_exercise.keys())}")

                    elif isinstance(exercises_data, list):
                        print(f"   List length: {len(exercises_data)}")
                        if exercises_data:
                            print(f"   First item: {type(exercises_data[0])}")
                            if isinstance(exercises_data[0], dict):
                                print(
                                    f"   First item keys: {list(exercises_data[0].keys())}")

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                except Exception as e:
                    print(f"   ❌ Error parsing data: {e}")
            else:
                print("   ❌ No exercise data stored")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def check_checkin_vs_database():
    print("\n🔍 COMPARING CHECK-IN DATA VS DATABASE")
    print("=" * 60)

    try:
        # Check the recent check-in data
        import os
        checkin_file = "output/checkin_reviews/Alice_Forster_2025-06-07_fitness_wrapped_data.json"

        if os.path.exists(checkin_file):
            with open(checkin_file, 'r') as f:
                checkin_data = json.load(f)

            workout_data_list = checkin_data.get('workout_data_list', [])
            print(
                f"📄 Check-in file workout sessions: {len(workout_data_list)}")

            if workout_data_list:
                # Show sample workout from check-in
                sample = workout_data_list[0]
                print(f"📋 Sample workout from check-in:")
                print(f"   Date: {sample.get('date', 'Unknown')}")
                print(f"   Name: {sample.get('workout_name', 'Unknown')}")
                exercises = sample.get('exercises', {})
                print(f"   Exercises: {len(exercises)} total")

                if exercises:
                    # Show first exercise
                    first_exercise_name = list(exercises.keys())[0]
                    first_exercise_data = exercises[first_exercise_name]
                    print(f"   First exercise: {first_exercise_name}")
                    print(f"   Exercise data: {first_exercise_data}")

            else:
                print("❌ No workout sessions in check-in data either!")
                # Check what's in the file
                print(f"📄 Check-in file keys: {list(checkin_data.keys())}")

                # Look for other workout-related data
                for key, value in checkin_data.items():
                    if 'workout' in key.lower() or 'exercise' in key.lower():
                        print(
                            f"   {key}: {type(value)} - {len(value) if isinstance(value, (list, dict, str)) else value}")

        else:
            print("❌ No recent check-in file found")

    except Exception as e:
        print(f"❌ Error checking check-in data: {e}")


def check_progressive_overload_expectations():
    print("\n🔍 CHECKING PROGRESSIVE OVERLOAD AI EXPECTATIONS")
    print("=" * 60)

    try:
        # Check what format Progressive Overload AI expects
        from progressive_overload_ai import ProgressiveOverloadAI

        ai = ProgressiveOverloadAI()
        print("✅ Progressive Overload AI imported successfully")

        # Try to load Alice's data the way the AI does
        print("📊 Attempting to load Alice's data via Progressive Overload AI...")
        workout_data = ai.load_client_workout_data(
            "Alice Forster", weeks_back=4)
        print(
            f"   Result: {len(workout_data) if workout_data else 0} workout sessions found")

        if workout_data:
            sample = workout_data[0]
            print(f"   Sample workout structure: {type(sample)}")
            if hasattr(sample, '__dict__'):
                print(f"   Sample attributes: {list(sample.__dict__.keys())}")

        # Also try with different name formats
        for name_format in ["alice_forster", "alice forster"]:
            workout_data = ai.load_client_workout_data(
                name_format, weeks_back=4)
            print(
                f"   '{name_format}': {len(workout_data) if workout_data else 0} sessions")

    except Exception as e:
        print(f"❌ Error with Progressive Overload AI: {e}")


if __name__ == "__main__":
    diagnose_alice_workouts()
    check_checkin_vs_database()
    check_progressive_overload_expectations()

    print("\n💡 SUMMARY:")
    print("The issue is likely one of these:")
    print("1. Workout data is stored but in wrong JSON format")
    print("2. Check-in script isn't saving exercise details to database")
    print("3. Progressive Overload AI expects different data structure")
    print("4. Name format mismatch between systems")
