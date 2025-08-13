#!/usr/bin/env python3
"""
Calculate Elena's actual goal completion rate from workout data
"""

import json
import time


def main():
    print("🎯 ELENA'S GOAL COMPLETION ANALYSIS")
    print("=" * 50)

    # Load Elena's data
    with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
        data = json.load(f)

    workout_breakdown = data.get('workout_breakdown', [])

    total_exercises = 0
    improved = 0
    maintained = 0
    declined = 0

    exercises_list = []

    for workout in workout_breakdown:
        for session in workout.get('sessions_current_week', []):
            for exercise in session.get('exercises', []):
                exercise_name = exercise.get('name', '')
                workload_improvement = exercise.get(
                    'workload_improvement_vs_previous', 0)
                current_workload = exercise.get('workload_current', 0)

                # Skip exercises with no meaningful workload
                if current_workload <= 0:
                    continue

                total_exercises += 1
                exercises_list.append({
                    'name': exercise_name,
                    'improvement': workload_improvement,
                    'workload': current_workload
                })

                if workload_improvement > 0:
                    improved += 1
                    print(
                        f"✅ IMPROVED: {exercise_name} (+{workload_improvement:.1f}%)")
                elif workload_improvement == 0:
                    maintained += 1
                    print(f"🔄 MAINTAINED: {exercise_name} (0%)")
                else:
                    declined += 1
                    print(
                        f"📉 DECLINED: {exercise_name} ({workload_improvement:.1f}%)")

    print(f"\n📊 SUMMARY:")
    print(f"Total exercises: {total_exercises}")
    print(f"Improved: {improved}")
    print(f"Maintained: {maintained}")
    print(f"Declined: {declined}")

    # Calculate goal completion (improved + 50% credit for maintained)
    goals_met = improved + (maintained * 0.5)
    goal_completion_rate = (goals_met / total_exercises) * \
        100 if total_exercises > 0 else 0

    print(f"\n🎯 GOAL COMPLETION RATE: {goal_completion_rate:.1f}%")
    print(f"Goals met: {goals_met:.1f} out of {total_exercises}")

    # What should be in the video slide
    print(f"\n🎬 VIDEO SLIDE SHOULD SHOW:")
    print(f"'Last Week's Goal Results'")
    print(f"'{goal_completion_rate:.0f}% Goal Completion Rate!'")
    if improved > 0:
        print(f"'You IMPROVED {improved} exercises! 🔥'")
    if maintained > 0:
        print(f"'You MAINTAINED {maintained} exercises 💪'")

    # Pause to ensure output is complete
    time.sleep(0.1)


if __name__ == "__main__":
    main()
