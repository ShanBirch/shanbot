import json
from datetime import datetime, timedelta
from progressive_overload_ai import ProgressiveOverloadAI, ExercisePerformance, WorkoutSet


def create_sample_workout_data():
    """Create realistic sample workout data for testing"""

    # Create 4 weeks of progressive workout data
    workout_data = []
    base_date = datetime.now() - timedelta(weeks=4)

    # Sample exercises with realistic progressions
    exercises = [
        {
            "name": "Barbell Bench Press",
            "base_weight": 80,
            "base_reps": 8,
            "workout_type": "Chest"
        },
        {
            "name": "Deadlift",
            "base_weight": 120,
            "base_reps": 5,
            "workout_type": "Back"
        },
        {
            "name": "Squat",
            "base_weight": 100,
            "base_reps": 8,
            "workout_type": "Legs"
        },
        {
            "name": "Overhead Press",
            "base_weight": 50,
            "base_reps": 10,
            "workout_type": "Shoulders"
        }
    ]

    # Generate 4 weeks of data (2 sessions per exercise per week)
    for week in range(4):
        for session in range(2):  # 2 sessions per week
            session_date = base_date + timedelta(weeks=week, days=session*3)

            for exercise in exercises:
                # Progressive increases over time
                weight_increase = week * 2.5  # 2.5kg per week
                current_weight = exercise["base_weight"] + weight_increase

                # Simulate some variation in performance
                if week == 3 and session == 1:  # Make last session challenging
                    reps_completed = exercise["base_reps"] - 1  # Fail one rep
                    completion_rate = 0.8
                else:
                    reps_completed = exercise["base_reps"]
                    completion_rate = 1.0

                # Create sets (typically 3 sets)
                sets = []
                for set_num in range(3):
                    # Slight variation in reps across sets
                    if set_num == 2:  # Last set might be harder
                        actual_reps = max(reps_completed - 1,
                                          exercise["base_reps"] - 2)
                        completed = completion_rate > 0.7
                    else:
                        actual_reps = reps_completed
                        completed = True

                    sets.append(WorkoutSet(
                        weight=current_weight,
                        reps=actual_reps,
                        completed=completed
                    ))

                # Create performance record
                performance = ExercisePerformance(
                    exercise_name=exercise["name"],
                    sets=sets,
                    date=session_date,
                    workout_type=exercise["workout_type"]
                )

                workout_data.append(performance)

    return workout_data


def main():
    print("🧪 Testing Progressive Overload AI with sample data...")

    # Create AI instance
    ai = ProgressiveOverloadAI()

    # Generate sample workout data
    print("📊 Generating sample workout data...")
    workout_data = create_sample_workout_data()
    print(f"✅ Created {len(workout_data)} exercise performances")

    # Analyze progressions
    print("🧠 Analyzing progression patterns...")
    progressions = ai.analyze_progression_patterns(workout_data)

    if not progressions:
        print("❌ Could not generate progression recommendations.")
        return

    print(f"🎯 Generated progressions for {len(progressions)} exercises")

    # Generate and display report
    client_name = "Test Client"
    report = ai.generate_progression_report(client_name, progressions)

    print("\n" + "="*80)
    print("📋 PROGRESSIVE OVERLOAD ANALYSIS REPORT")
    print("="*80)
    print(report)
    print("="*80)

    # Save progression history
    ai.save_progression_history(client_name, progressions)
    print(f"💾 Saved progression history to: {ai.progression_history_path}")

    # Show what the system would implement
    print("\n🔧 IMPLEMENTATION PREVIEW:")
    print("-" * 50)

    for exercise_name, decisions in progressions.items():
        decision = decisions[0]
        action_emoji = {
            "increase": "📈",
            "maintain": "⚖️",
            "decrease": "📉",
            "deload": "🔄"
        }.get(decision.action_type, "❓")

        print(f"{action_emoji} {exercise_name}:")
        print(
            f"   Weight: {decision.current_weight}kg → {decision.recommended_weight}kg")
        print(
            f"   Reps: {decision.current_reps} → {decision.recommended_reps}")
        print(f"   Confidence: {decision.confidence:.1%}")
        print(f"   Reason: {decision.reason}")
        print()

    print("🚀 This system would automatically update Trainerize programs!")
    print("💡 No other fitness platform has real-time AI progression like this.")


if __name__ == "__main__":
    main()
