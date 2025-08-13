#!/usr/bin/env python
import json

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("📊 ELENA'S EXERCISE COUNT")
print("=" * 30)

workout_breakdown = elena_data.get('workout_breakdown', [])

total_exercise_instances = 0
unique_exercises = set()
session_count = 0

for workout_idx, workout in enumerate(workout_breakdown):
    workout_name = workout.get('workout_name', f'Workout {workout_idx + 1}')
    sessions = workout.get('sessions_current_week', [])

    print(f"\n🏋️ {workout_name}:")

    for session_idx, session in enumerate(sessions):
        session_count += 1
        session_date = session.get('date', 'Unknown')
        exercises = session.get('exercises', [])

        # Count exercises with meaningful workload
        meaningful_exercises = []
        for exercise in exercises:
            workload = exercise.get('workload_current', 0)
            if workload > 0:
                meaningful_exercises.append(exercise.get('name', 'Unknown'))
                unique_exercises.add(exercise.get('name', 'Unknown'))
                total_exercise_instances += 1

        print(
            f"  📅 Session {session_date}: {len(meaningful_exercises)} exercises")
        for ex in meaningful_exercises:
            print(f"    • {ex}")

print(f"\n🎯 FINAL TOTALS:")
print(f"  📋 Total exercise instances: {total_exercise_instances}")
print(f"  🎯 Unique exercises: {len(unique_exercises)}")
print(f"  📅 Total sessions: {session_count}")

print(f"\n📝 All unique exercises Elena performed:")
for i, exercise in enumerate(sorted(unique_exercises), 1):
    print(f"  {i}. {exercise}")
