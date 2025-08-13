#!/usr/bin/env python
import json

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("🏋️ ELENA'S COMPLETE WORKOUT BREAKDOWN")
print("=" * 50)

workout_breakdown = elena_data.get('workout_breakdown', [])

for workout_idx, workout in enumerate(workout_breakdown):
    workout_name = workout.get('workout_name', f'Workout {workout_idx + 1}')
    sessions = workout.get('sessions_current_week', [])

    print(f"\n{'='*60}")
    print(f"🎯 WORKOUT: {workout_name}")
    print(f"{'='*60}")
    print(f"📅 Sessions this week: {len(sessions)}")

    # Get all unique exercises from this workout type
    all_exercises_in_workout = set()
    session_dates = []

    for session in sessions:
        session_date = session.get('date', 'Unknown')
        session_dates.append(session_date)
        exercises = session.get('exercises', [])

        for exercise in exercises:
            exercise_name = exercise.get('name', 'Unknown')
            all_exercises_in_workout.add(exercise_name)

    print(f"📅 Session dates: {', '.join(session_dates)}")
    print(
        f"📋 Total exercises in this workout: {len(all_exercises_in_workout)}")

    print(f"\n📝 EXERCISES IN THIS WORKOUT:")

    # Show exercises with their performance details
    for session_idx, session in enumerate(sessions):
        session_date = session.get('date', 'Unknown')
        print(f"\n  📅 Session {session_idx + 1} ({session_date}):")

        exercises = session.get('exercises', [])
        for exercise_idx, exercise in enumerate(exercises, 1):
            exercise_name = exercise.get('name', 'Unknown')
            workload_current = exercise.get('workload_current', 0)
            workload_improvement = exercise.get(
                'workload_improvement_vs_previous', 0)
            sets_current = exercise.get('sets_current', [])

            # Get performance details
            if sets_current:
                weights = [s.get('weight', 0) for s in sets_current]
                reps = [s.get('reps', 0) for s in sets_current]
                sets_count = len(sets_current)
                avg_weight = sum(weights) / len(weights) if weights else 0
                total_reps = sum(reps)

                performance = f"{sets_count} sets, {avg_weight:.1f}kg, {total_reps} total reps"
            else:
                performance = "No set data"

            # Status indicator
            if workload_improvement > 0:
                status = "🚀 IMPROVED"
            elif workload_improvement == 0:
                status = "💪 MAINTAINED"
            elif workload_improvement < 0:
                status = "📉 DECLINED"
            else:
                status = "❓ NO DATA"

            print(f"    {exercise_idx}. {exercise_name}")
            print(f"       {status} ({workload_improvement:+.1f}%)")
            print(f"       Performance: {performance}")

            if workload_current <= 0:
                print(f"       ⚠️ Zero workload - likely skipped or warm-up")

print(f"\n{'='*60}")
print(f"📊 WEEKLY SUMMARY")
print(f"{'='*60}")

# Overall stats
total_unique_exercises = set()
total_sessions = 0
workout_types = len(workout_breakdown)

for workout in workout_breakdown:
    sessions = workout.get('sessions_current_week', [])
    total_sessions += len(sessions)

    for session in sessions:
        for exercise in session.get('exercises', []):
            if exercise.get('workload_current', 0) > 0:
                total_unique_exercises.add(exercise.get('name', 'Unknown'))

print(f"🏋️ Total workout types: {workout_types}")
print(f"📅 Total sessions: {total_sessions}")
print(f"🎯 Total unique exercises: {len(total_unique_exercises)}")
print(
    f"💪 Elena trained {total_sessions//workout_types:.1f} times per workout type on average")
