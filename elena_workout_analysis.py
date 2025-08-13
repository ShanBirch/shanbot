#!/usr/bin/env python
import json

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("💪 ELENA'S DETAILED WORKOUT ANALYSIS")
print("=" * 50)

workout_breakdown = elena_data.get('workout_breakdown', [])

# Track unique exercises and their performance
exercise_performance = {}

for workout in workout_breakdown:
    for session in workout.get('sessions_current_week', []):
        session_date = session.get('date', 'Unknown date')
        print(f"\n📅 Session: {session_date}")

        for exercise in session.get('exercises', []):
            exercise_name = exercise.get('name', '')
            workload_improvement = exercise.get(
                'workload_improvement_vs_previous', 0)
            current_workload = exercise.get('workload_current', 0)
            sets_current = exercise.get('sets_current', [])

            # Skip exercises with no meaningful workload
            if current_workload <= 0:
                continue

            # Track best performance for each unique exercise
            if exercise_name not in exercise_performance:
                exercise_performance[exercise_name] = {
                    'improvement': workload_improvement,
                    'sets': sets_current,
                    'sessions': [session_date]
                }
            else:
                exercise_performance[exercise_name]['sessions'].append(
                    session_date)
                if workload_improvement > exercise_performance[exercise_name]['improvement']:
                    exercise_performance[exercise_name]['improvement'] = workload_improvement
                    exercise_performance[exercise_name]['sets'] = sets_current

            # Show this session's performance
            if workload_improvement > 0:
                status = "🚀 IMPROVED"
            elif workload_improvement == 0:
                status = "💪 MAINTAINED"
            else:
                status = "📉 DECLINED"

            # Get weight/reps info
            if sets_current:
                weights = [s.get('weight', 0) for s in sets_current]
                reps = [s.get('reps', 0) for s in sets_current]
                avg_weight = sum(weights) / len(weights) if weights else 0
                total_reps = sum(reps)

                performance_detail = f"{avg_weight:.1f}kg x {total_reps} total reps"
            else:
                performance_detail = "No set data"

            print(
                f"  {status}: {exercise_name} ({workload_improvement:+.1f}%) - {performance_detail}")

print(f"\n🎯 OVERALL PERFORMANCE SUMMARY")
print("=" * 50)

improved_exercises = []
maintained_exercises = []
declined_exercises = []

for exercise_name, data in exercise_performance.items():
    improvement = data['improvement']
    sessions_count = len(set(data['sessions']))  # Unique sessions

    if improvement > 0:
        improved_exercises.append((exercise_name, improvement, sessions_count))
    elif improvement == 0:
        maintained_exercises.append(
            (exercise_name, improvement, sessions_count))
    else:
        declined_exercises.append((exercise_name, improvement, sessions_count))

print(f"\n🚀 EXERCISES THAT IMPROVED ({len(improved_exercises)}):")
for exercise, improvement, sessions in improved_exercises:
    print(f"  • {exercise}: +{improvement:.1f}% (appeared in {sessions} session{'s' if sessions > 1 else ''})")

print(f"\n💪 EXERCISES MAINTAINED ({len(maintained_exercises)}):")
for exercise, improvement, sessions in maintained_exercises:
    print(f"  • {exercise}: {improvement:+.1f}% (appeared in {sessions} session{'s' if sessions > 1 else ''})")

print(f"\n📉 EXERCISES THAT DECLINED ({len(declined_exercises)}):")
for exercise, improvement, sessions in declined_exercises:
    print(f"  • {exercise}: {improvement:.1f}% (appeared in {sessions} session{'s' if sessions > 1 else ''})")

print(f"\n📊 WHAT HIT:")
if improved_exercises:
    best_exercise = max(improved_exercises, key=lambda x: x[1])
    print(f"  🎯 Best performer: {best_exercise[0]} (+{best_exercise[1]:.1f}%)")
    print(f"  🔥 {len(improved_exercises)} exercises showed improvement")

print(f"\n📊 WHAT DIDN'T HIT:")
if declined_exercises:
    worst_exercise = min(declined_exercises, key=lambda x: x[1])
    print(
        f"  ⚠️  Biggest decline: {worst_exercise[0]} ({worst_exercise[1]:.1f}%)")
    print(f"  📉 {len(declined_exercises)} exercises declined")

print(f"\n🎯 TOTAL UNIQUE EXERCISES: {len(exercise_performance)}")
