#!/usr/bin/env python
import json
from simple_blue_video import calculate_goal_completion_rate, get_goal_summary, get_exercise_improvement_details

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("🎯 ELENA'S CORRECTED GOAL COMPLETION ANALYSIS")
print("=" * 60)

# Test the corrected goal completion rate
goal_rate = calculate_goal_completion_rate(elena_data)
print(f"Goal Completion Rate: {goal_rate:.1f}%")

# Test the corrected goal summary
goal_summary = get_goal_summary(elena_data)
print(f"Goal Summary: {goal_summary}")

# Test exercise improvements
improvements = get_exercise_improvement_details(elena_data)
print(f"\nExercise Improvements ({len(improvements)} exercises):")
for i, improvement in enumerate(improvements, 1):
    print(f"{i}. {improvement}")

# Debug the unique exercises tracking
workout_breakdown = elena_data.get('workout_breakdown', [])
unique_exercises = {}

for workout in workout_breakdown:
    for session in workout.get('sessions_current_week', []):
        for exercise in session.get('exercises', []):
            exercise_name = exercise.get('name', '')
            workload_improvement = exercise.get(
                'workload_improvement_vs_previous', 0)
            current_workload = exercise.get('workload_current', 0)

            if current_workload <= 0:
                continue

            if exercise_name not in unique_exercises:
                unique_exercises[exercise_name] = workload_improvement
            else:
                unique_exercises[exercise_name] = max(
                    unique_exercises[exercise_name], workload_improvement)

print(f"\n📊 DEBUG - Unique Exercises Found:")
for name, improvement in unique_exercises.items():
    status = "IMPROVED" if improvement > 0 else "MAINTAINED" if improvement == 0 else "DECLINED"
    print(f"  {status}: {name} ({improvement:+.1f}%)")

improved_count = sum(1 for imp in unique_exercises.values() if imp > 0)
maintained_count = sum(1 for imp in unique_exercises.values() if imp == 0)
declined_count = sum(1 for imp in unique_exercises.values() if imp < 0)

print(f"\n📈 Summary:")
print(f"  Total unique exercises: {len(unique_exercises)}")
print(f"  Improved: {improved_count}")
print(f"  Maintained: {maintained_count}")
print(f"  Declined: {declined_count}")
