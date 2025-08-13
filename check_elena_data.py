#!/usr/bin/env python
import json

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("🔍 ELENA'S DATA STRUCTURE EXAMINATION")
print("=" * 50)

# Check top-level keys
print("📋 Top-level keys in Elena's data:")
for key in elena_data.keys():
    print(f"  • {key}")

# Look specifically at workout breakdown
workout_breakdown = elena_data.get('workout_breakdown', [])
print(f"\n📊 Workout breakdown contains {len(workout_breakdown)} items")

if workout_breakdown:
    print(f"\n🔍 First workout breakdown item structure:")
    first_item = workout_breakdown[0]
    for key, value in first_item.items():
        if isinstance(value, list):
            print(f"  • {key}: list with {len(value)} items")
        else:
            print(f"  • {key}: {type(value).__name__}")

    # Look at sessions
    if 'sessions_current_week' in first_item:
        sessions = first_item['sessions_current_week']
        print(f"\n📅 Sessions structure ({len(sessions)} sessions):")

        if sessions:
            first_session = sessions[0]
            print(f"  First session keys: {list(first_session.keys())}")

            if 'exercises' in first_session:
                exercises = first_session['exercises']
                print(f"  Exercises in first session: {len(exercises)}")

                if exercises:
                    first_exercise = exercises[0]
                    print(f"  First exercise structure:")
                    for key, value in first_exercise.items():
                        print(f"    - {key}: {value}")

# Simple count from our original analysis
unique_exercises = set()
total_instances = 0

for workout in workout_breakdown:
    for session in workout.get('sessions_current_week', []):
        for exercise in session.get('exercises', []):
            exercise_name = exercise.get('name', '')
            current_workload = exercise.get('workload_current', 0)

            if current_workload > 0:  # Only count meaningful exercises
                unique_exercises.add(exercise_name)
                total_instances += 1

print(f"\n🎯 QUICK COUNT:")
print(f"  Total exercise instances: {total_instances}")
print(f"  Unique exercises: {len(unique_exercises)}")
print(f"  Unique exercise names: {sorted(unique_exercises)}")
