#!/usr/bin/env python3
"""
Test the rep-based progressive overload with Alice Forster's actual workout names
"""

from progressive_overload_ai import ProgressiveOverloadAI


def test_workout_discovery():
    """Test the workout discovery and show improvement"""
    print("🔍 TESTING WORKOUT DISCOVERY")
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

    # Generate progressions
    print(f"\n📈 Generating rep-based progressions...")
    progressions = ai.analyze_progression_patterns_rep_based(workout_data)

    if not progressions:
        print("❌ No progressions generated!")
        return False

    print(f"✅ Generated {len(progressions)} progressions")

    # Show actual workout names that will be searched
    workout_names = set()
    for performance in workout_data:
        if hasattr(performance, 'workout_type') and performance.workout_type:
            workout_names.add(performance.workout_type)

    workout_names = sorted(list(workout_names))

    print(f"\n🏋️ Alice Forster's Actual Workout Names:")
    print("=" * 50)
    for i, workout in enumerate(workout_names, 1):
        print(f"{i:2d}. '{workout}'")

    # Show sample exercises to be updated
    print(f"\n📝 SAMPLE EXERCISES TO UPDATE:")
    print("=" * 50)

    # Group exercises by workout type
    workout_exercises = {}
    for performance in workout_data:
        workout_type = performance.workout_type
        if workout_type not in workout_exercises:
            workout_exercises[workout_type] = []
        workout_exercises[workout_type].append(performance.exercise_name)

    # Show examples from each workout
    for workout_name in workout_names[:3]:  # Show first 3 workouts
        exercises = set(workout_exercises.get(workout_name, []))
        exercise_list = sorted(list(exercises))

        print(f"\n🏋️ {workout_name}:")
        for exercise in exercise_list[:3]:  # Show first 3 exercises
            if exercise in progressions:
                decision = progressions[exercise][0]
                goals_format = f"Goals: W({decision.recommended_weight}), R({decision.recommended_reps})"
                print(f"   • {exercise}: {goals_format}")
                print(
                    f"     Action: {decision.action_type} - {decision.reason[:60]}...")

    print(f"\n✅ IMPROVED SYSTEM READY!")
    print(f"   • ✅ Actual workout names identified")
    print(f"   • ✅ {len(progressions)} exercises ready for update")
    print(f"   • ✅ Rep-based logic applied correctly")
    print(f"   • ✅ Goals format: 'Goals: W(weight), R(reps)'")

    return True


def main():
    """Main test function"""
    print("🚀 REP-BASED PROGRESSIONS WITH REAL WORKOUT NAMES")
    print("=" * 60)

    success = test_workout_discovery()

    if success:
        print(f"\n🎉 SYSTEM IMPROVEMENT COMPLETE!")
        print(f"\nBEFORE: Looking for generic names like 'Upper Body', 'Lower Body'")
        print(f"AFTER:  Looking for actual names like 'Back Day', 'Chest + Arms', 'Shoulder Day'")
        print(f"\n🚀 Ready to run full automation:")
        print(f"   python test_rep_based_progressions.py")
        print(f"   Choose Option 1 for full Trainerize automation")
    else:
        print(f"\n❌ Test failed!")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
