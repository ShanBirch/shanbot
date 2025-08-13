#!/usr/bin/env python3
"""
Quick script to check Alice's workout data for progression analysis
"""

import sqlite3
import json
from datetime import datetime, timedelta


def check_alice_data():
    print("🔍 CHECKING ALICE'S WORKOUT DATA")
    print("=" * 50)

    try:
        # Connect to database
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [x[0] for x in cursor.fetchall()]
        print(f"📋 Available tables: {tables}")

        # Check for workout sessions table
        if 'client_workout_sessions' in tables:
            # Count total workout sessions
            cursor.execute("SELECT COUNT(*) FROM client_workout_sessions")
            total_sessions = cursor.fetchone()[0]
            print(f"💪 Total workout sessions in DB: {total_sessions}")

            # Check for Alice specifically (different name formats)
            alice_variants = ['alice_forster', 'Alice Forster',
                              'alice forster', 'Alice_Forster']

            for variant in alice_variants:
                cursor.execute(
                    "SELECT COUNT(*) FROM client_workout_sessions WHERE client_name_key = ?", (variant,))
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"✅ Found {count} sessions for '{variant}'")

                    # Get sample of Alice's data
                    cursor.execute("""
                        SELECT workout_date, workout_name, exercises_json 
                        FROM client_workout_sessions 
                        WHERE client_name_key = ? 
                        ORDER BY workout_date DESC 
                        LIMIT 3
                    """, (variant,))

                    recent_workouts = cursor.fetchall()
                    print(f"📅 Recent workouts for {variant}:")
                    for date, name, exercises in recent_workouts:
                        try:
                            exercises_data = json.loads(
                                exercises) if exercises else {}
                            exercise_count = len(exercises_data) if isinstance(
                                exercises_data, dict) else 0
                            print(
                                f"  - {date}: {name} ({exercise_count} exercises)")
                        except:
                            print(f"  - {date}: {name} (JSON parse error)")
                else:
                    print(f"❌ No sessions found for '{variant}'")

            # Check all distinct client names
            cursor.execute(
                "SELECT DISTINCT client_name_key FROM client_workout_sessions LIMIT 20")
            all_clients = [x[0] for x in cursor.fetchall()]
            print(f"\n👥 Sample client names in DB: {all_clients[:10]}")

        else:
            print("❌ No client_workout_sessions table found!")

        # Check if there's exercise performance data table
        if 'exercise_performances' in tables:
            cursor.execute("SELECT COUNT(*) FROM exercise_performances")
            perf_count = cursor.fetchone()[0]
            print(f"🏋️ Total exercise performances: {perf_count}")

            # Check for Alice in exercise performances
            for variant in alice_variants:
                cursor.execute(
                    "SELECT COUNT(*) FROM exercise_performances WHERE client_name = ?", (variant,))
                count = cursor.fetchone()[0]
                if count > 0:
                    print(
                        f"✅ Found {count} exercise performances for '{variant}'")
                    break

        conn.close()

    except Exception as e:
        print(f"❌ Error checking database: {e}")


def check_recent_checkin_data():
    print("\n🔍 CHECKING RECENT CHECK-IN DATA")
    print("=" * 50)

    try:
        import os
        checkin_dir = "output/checkin_reviews"

        if os.path.exists(checkin_dir):
            files = [f for f in os.listdir(checkin_dir) if f.startswith(
                'Alice_Forster') and f.endswith('.json')]
            print(f"📁 Found {len(files)} Alice Forster check-in files")

            for file in files[-3:]:  # Last 3 files
                filepath = os.path.join(checkin_dir, file)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    workout_data = data.get('workout_data_list', [])
                    print(f"📄 {file}: {len(workout_data)} workout sessions")

                    # Show sample workout data
                    if workout_data:
                        sample = workout_data[0]
                        print(
                            f"  Sample: {sample.get('workout_name', 'Unknown')} on {sample.get('date', 'Unknown date')}")
                        exercises = sample.get('exercises', {})
                        print(f"  Exercises: {len(exercises)} total")

                except Exception as e:
                    print(f"  ❌ Error reading {file}: {e}")
        else:
            print("❌ No checkin_reviews directory found")

    except Exception as e:
        print(f"❌ Error checking check-in data: {e}")


if __name__ == "__main__":
    check_alice_data()
    check_recent_checkin_data()

    print("\n💡 DIAGNOSIS:")
    print("If Alice's data isn't found, the issue could be:")
    print("1. Name format mismatch (underscore vs space vs case)")
    print("2. Workout data not saved to SQLite properly")
    print("3. Progressive Overload AI looking in wrong table/format")
    print("4. Recent check-in data not imported to database yet")

# Load Alice's fitness wrapped data
with open('output/checkin_reviews/Alice_Forster_2025-06-14_fitness_wrapped_data.json', 'r') as f:
    data = json.load(f)

print("Keys in Alice's data:", list(data.keys()))

if 'workout_data' in data:
    print("Workout names:", list(data['workout_data'].keys()))

    # Show first workout structure
    first_workout = list(data['workout_data'].keys())[0]
    print(f"First workout '{first_workout}' structure:")
    print(f"  Keys: {list(data['workout_data'][first_workout].keys())}")
else:
    print("No workout_data found")
