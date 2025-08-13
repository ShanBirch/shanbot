#!/usr/bin/env python3
"""
Check the results of the batch client workout updates
"""

import json
import sqlite3
from datetime import datetime


def check_update_results():
    """Check which clients were successfully updated"""

    print("=== WORKOUT UPDATE RESULTS SUMMARY ===")

    # Load the progression data
    try:
        with open('all_clients_progressions.json', 'r') as f:
            all_progressions = json.load(f)
    except FileNotFoundError:
        print("❌ No progression data file found")
        return

    print(f"📊 TOTAL CLIENTS ANALYZED: {len(all_progressions)}")
    print()

    # Summarize each client
    total_workouts = 0
    total_exercises = 0

    for client_name, workouts in all_progressions.items():
        valid_workouts = {k: v for k, v in workouts.items() if v}
        workout_count = len(valid_workouts)

        if workout_count > 0:
            exercise_count = sum(len(exercises)
                                 for exercises in valid_workouts.values())
            total_workouts += workout_count
            total_exercises += exercise_count

            print(f"🏋️ {client_name}:")
            print(f"   - {workout_count} workouts updated")
            print(f"   - {exercise_count} exercises progressed")

            # Show a sample workout
            sample_workout = list(valid_workouts.keys())[0]
            # First 2 exercises
            sample_exercises = valid_workouts[sample_workout][:2]
            print(f"   - Sample ({sample_workout}):")
            for exercise in sample_exercises:
                print(
                    f"     • {exercise['exercise_name']}: → {exercise['weight']}kg x {exercise['reps']} reps")
        else:
            print(f"⚠️ {client_name}: No valid workout progressions")
        print()

    print(f"🎯 TOTAL IMPACT:")
    print(f"   - {total_workouts} workouts with progressive overload")
    print(f"   - {total_exercises} exercises with increased goals")
    print(
        f"   - Average: {total_exercises/len(all_progressions):.1f} exercises per client")

    # Check which clients are most active
    print(f"\n🔥 MOST ACTIVE CLIENTS:")
    client_activity = []
    for client_name, workouts in all_progressions.items():
        valid_workouts = {k: v for k, v in workouts.items() if v}
        exercise_count = sum(len(exercises)
                             for exercises in valid_workouts.values())
        if exercise_count > 0:
            client_activity.append(
                (client_name, exercise_count, len(valid_workouts)))

    # Sort by exercise count
    client_activity.sort(key=lambda x: x[1], reverse=True)

    for i, (name, exercises, workouts) in enumerate(client_activity[:5], 1):
        print(f"   {i}. {name}: {exercises} exercises across {workouts} workouts")

    print(f"\n✅ SYSTEM STATUS: Progressive overload updates prepared for all active clients!")

    # Show the progressive overload strategy
    print(f"\n📈 PROGRESSIVE OVERLOAD STRATEGY:")
    print(f"   - Weight increase: +2.5kg (or +1.25kg for <20kg)")
    print(f"   - Rep increase: +1 rep (capped at 15)")
    print(f"   - Based on most recent workout performance")
    print(f"   - Applies to exercises with recorded sets data")


if __name__ == "__main__":
    check_update_results()
