from progressive_overload_ai import ProgressiveOverloadAI, ExercisePerformance, WorkoutSet
from datetime import datetime, timedelta


def test_realistic_weight_increments():
    """Test that the Progressive Overload AI uses realistic weight increments"""

    ai = ProgressiveOverloadAI()

    # Test different exercise types
    test_exercises = [
        ("Dumbbell Bench Press", 20.0),
        ("Barbell Squat", 80.0),
        ("Cable Lat Pull Down", 45.0),
        ("Assisted Chin Up", 10.0)
    ]

    print("🏋️ Testing Realistic Weight Increments")
    print("=" * 50)

    for exercise_name, current_weight in test_exercises:
        # Get the realistic increment
        increment = ai.get_realistic_weight_increment(
            exercise_name, current_weight)

        print(f"\n💪 {exercise_name}")
        print(f"   Current Weight: {current_weight}kg")
        print(f"   Realistic Increment: {increment}kg")

        # Create mock performance data with high completion rate
        mock_performances = []
        for i in range(3):
            date = datetime.now() - timedelta(days=7*i)
            sets = [
                WorkoutSet(weight=current_weight, reps=10, completed=True),
                WorkoutSet(weight=current_weight, reps=10, completed=True),
                WorkoutSet(weight=current_weight, reps=9, completed=True)
            ]
            perf = ExercisePerformance(
                exercise_name=exercise_name,
                sets=sets,
                date=date,
                workout_type="Test"
            )
            mock_performances.append(perf)

        # Test fallback progression (since AI may fail due to quota)
        completion_rate = 0.95  # High completion rate
        decision = ai._fallback_progression_decision(
            exercise_name, current_weight, "10", completion_rate
        )

        print(f"   📈 Progression Decision:")
        print(f"      Action: {decision.action_type}")
        print(f"      New Weight: {decision.recommended_weight}kg")
        print(
            f"      Weight Change: +{decision.recommended_weight - current_weight}kg")
        print(f"      Reason: {decision.reason}")

        # Verify the increment is realistic
        weight_change = decision.recommended_weight - current_weight
        if abs(weight_change - increment) < 0.1:  # Allow small floating point differences
            print(f"   ✅ Correct increment used!")
        else:
            print(
                f"   ❌ Wrong increment! Expected {increment}kg, got {weight_change}kg")


if __name__ == "__main__":
    test_realistic_weight_increments()
