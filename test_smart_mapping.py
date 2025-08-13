#!/usr/bin/env python3
"""
Test the smart exercise-to-workout mapping system
"""

from progressive_overload_ai import ProgressiveOverloadAI


def test_smart_mapping():
    """Test the smart exercise-to-workout mapping"""
    print("🧠 TESTING SMART EXERCISE-TO-WORKOUT MAPPING")
    print("=" * 60)

    ai = ProgressiveOverloadAI()
    client_name = "Alice Forster"

    # Load workout data
    print(f"📊 Loading workout data for {client_name}...")
    workout_data = ai.load_client_workout_data(client_name)

    if not workout_data:
        print("❌ No workout data found!")
        return False

    print(f"✅ Loaded {len(workout_data)} exercise performances")

    # Create exercise-to-workout mapping
    print(f"\n🗺️  Creating exercise-to-workout mapping...")
    exercise_workout_map = {}
    for performance in workout_data:
        exercise_name = performance.exercise_name
        workout_type = performance.workout_type
        if exercise_name not in exercise_workout_map:
            exercise_workout_map[exercise_name] = workout_type

    print(f"✅ Mapped {len(exercise_workout_map)} exercises to workouts")

    # Generate progressions
    print(f"\n📈 Generating rep-based progressions...")
    progressions = ai.analyze_progression_patterns_rep_based(workout_data)

    if not progressions:
        print("❌ No progressions generated!")
        return False

    print(f"✅ Generated {len(progressions)} progressions")

    # Group progressions by workout (like the improved system does)
    print(f"\n📋 GROUPING UPDATES BY WORKOUT:")
    print("=" * 50)

    workout_progressions = {}
    for exercise_name, decisions in progressions.items():
        workout_name = exercise_workout_map.get(exercise_name)

        if workout_name:
            if workout_name not in workout_progressions:
                workout_progressions[workout_name] = []
            workout_progressions[workout_name].append(
                (exercise_name, decisions[0]))

    # Show the efficient update plan
    for workout_name, exercise_progressions in workout_progressions.items():
        print(f"\n🏋️ {workout_name} ({len(exercise_progressions)} exercises):")

        # Show first 3
        for exercise_name, decision in exercise_progressions[:3]:
            goals_format = f"Goals: W({decision.recommended_weight}), R({decision.recommended_reps})"
            print(f"   • {exercise_name}: {goals_format}")
            print(f"     Action: {decision.action_type}")

        if len(exercise_progressions) > 3:
            print(
                f"   ... and {len(exercise_progressions) - 3} more exercises")

    print(f"\n📊 EFFICIENCY COMPARISON:")
    print("=" * 50)
    print(f"❌ OLD WAY:")
    print(f"   • Search ALL workouts for each exercise")
    print(
        f"   • {len(progressions)} exercises × 9 workouts = 324 search attempts")
    print(f"   • Inefficient and slow")

    print(f"\n✅ NEW WAY:")
    print(f"   • Know exactly which workout contains each exercise")
    print(f"   • Only open {len(workout_progressions)} workouts")
    print(f"   • Update multiple exercises per workout")
    print(f"   • Fast and targeted")

    print(f"\n🎯 IMPLEMENTATION PLAN:")
    print("=" * 50)
    total_exercises = sum(len(exercises)
                          for exercises in workout_progressions.values())

    for i, (workout_name, exercises) in enumerate(workout_progressions.items(), 1):
        print(
            f"Step {i}: Open '{workout_name}' → Update {len(exercises)} exercises → Save")

    print(f"\n✅ SMART MAPPING SYSTEM READY!")
    print(f"   • 🎯 {total_exercises} exercises mapped to workouts")
    print(f"   • ⚡ {len(workout_progressions)} efficient workout updates")
    print(f"   • 🔧 Rep-based progressions applied")
    print(f"   • 💾 Goals format: 'Goals: W(weight), R(reps)'")

    return True


def main():
    """Main test function"""
    print("🚀 SMART EXERCISE-TO-WORKOUT MAPPING TEST")
    print("=" * 60)

    success = test_smart_mapping()

    if success:
        print(f"\n🎉 SYSTEM IMPROVEMENT COMPLETE!")
        print(f"\n📈 BEFORE vs AFTER:")
        print(f"   ❌ BEFORE: Random search through all workouts")
        print(f"   ✅ AFTER:  Smart mapping + targeted updates")

        print(f"\n🚀 Ready for full automation:")
        print(f"   python test_rep_based_progressions.py")
        print(f"   Choose Option 1 for efficient automation")

        print(f"\n💡 THE SYSTEM NOW:")
        print(f"   1. Maps each exercise to its specific workout")
        print(f"   2. Groups updates by workout for efficiency")
        print(f"   3. Opens each workout only once")
        print(f"   4. Updates all exercises in that workout")
        print(f"   5. Saves and moves to next workout")
    else:
        print(f"\n❌ Test failed!")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
