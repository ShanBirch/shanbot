#!/usr/bin/env python
import json

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("📊 ELENA'S EXERCISE COUNT BREAKDOWN")
print("=" * 40)

workout_breakdown = elena_data.get('workout_breakdown', [])

# Count everything
total_exercise_instances = 0
unique_exercises = set()
session_count = 0

print("📅 SESSION BREAKDOWN:")
for workout in workout_breakdown:
    for session in workout.get('sessions_current_week', []):
        session_count += 1
        session_date = session.get('date', 'Unknown date')
        exercises_in_session = len(session.get('exercises', []))

        print(
            f"  Session {session_count} ({session_date}): {exercises_in_session} exercises")

        for exercise in session.get('exercises', []):
            exercise_name = exercise.get('name', '')
            current_workload = exercise.get('workload_current', 0)

            # Skip exercises with no meaningful workload
            if current_workload <= 0:
                continue

            total_exercise_instances += 1
            unique_exercises.add(exercise_name)

print(f"\n🎯 TOTALS:")
print(f"  📋 Total exercise instances: {total_exercise_instances}")
print(f"  🎯 Unique exercises: {len(unique_exercises)}")
print(f"  📅 Total sessions: {session_count}")
print(
    f"  📊 Average exercises per session: {total_exercise_instances/session_count:.1f}")

print(f"\n📝 UNIQUE EXERCISE LIST:")
for i, exercise in enumerate(sorted(unique_exercises), 1):
    print(f"  {i}. {exercise}")
