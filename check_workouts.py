#!/usr/bin/env python3
"""
Check actual workout names for Alice Forster using the progressive overload system
"""

from progressive_overload_ai import ProgressiveOverloadAI


def check_workout_names():
    """Get the actual workout names used by Alice Forster"""
    try:
        ai = ProgressiveOverloadAI()
        client_name = "Alice Forster"

        print(f"🏋️ Loading workout data for {client_name}...")
        workout_data = ai.load_client_workout_data(client_name)

        if not workout_data:
            print("❌ No workout data found!")
            return []

        print(f"✅ Loaded {len(workout_data)} exercise performances")

        # Extract unique workout names
        workout_names = set()
        for performance in workout_data:
            if hasattr(performance, 'workout_type') and performance.workout_type:
                workout_names.add(performance.workout_type)

        # Convert to sorted list
        workout_names = sorted(list(workout_names))

        print(f"\n🏋️ {client_name}'s Actual Workout Names:")
        print("=" * 60)

        if workout_names:
            for i, workout in enumerate(workout_names, 1):
                print(f"{i:2d}. '{workout}'")
        else:
            print("No workout names found!")

        print(f"\n📊 Total unique workout types: {len(workout_names)}")

        # Also show some exercise examples for each workout
        print(f"\n📋 Exercise Examples by Workout:")
        print("=" * 60)

        workout_exercises = {}
        for performance in workout_data:
            workout_type = performance.workout_type
            if workout_type not in workout_exercises:
                workout_exercises[workout_type] = set()
            workout_exercises[workout_type].add(performance.exercise_name)

        for workout_name in workout_names:
            exercises = sorted(list(workout_exercises.get(workout_name, [])))
            print(f"\n📋 {workout_name}:")
            for exercise in exercises[:5]:  # Show first 5 exercises
                print(f"   • {exercise}")
            if len(exercises) > 5:
                print(f"   ... and {len(exercises) - 5} more exercises")

        return workout_names

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    workout_names = check_workout_names()

    if workout_names:
        print(f"\n🔧 SOLUTION: Update the implement_progressions function")
        print("Replace the common_workout_names list with:")
        print("common_workout_names = [")
        for workout in workout_names:
            print(f'    "{workout}",')
        print("]")
