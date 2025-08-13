#!/usr/bin/env python3
"""
Demo script showing the rep-based progressive overload system.
This demonstrates the logic without requiring actual client data.
"""

from progressive_overload_ai import ProgressiveOverloadAI, ExercisePerformance, WorkoutSet
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_demo_data():
    """Create demo workout data to test the progression logic."""

    # Create sample workout data for different scenarios
    exercises_data = []

    # Scenario 1: Client hitting 15+ reps (should increase weight, reset reps)
    bench_sets = [
        WorkoutSet(weight=60, reps=15, completed=True),
        WorkoutSet(weight=60, reps=14, completed=True),
        WorkoutSet(weight=60, reps=16, completed=True)
    ]
    exercises_data.append(ExercisePerformance(
        exercise_name="Bench Press",
        sets=bench_sets,
        date=datetime.now() - timedelta(days=1),
        workout_type="Push"
    ))

    # Scenario 2: Client achieving target reps (should increase reps)
    squat_sets = [
        WorkoutSet(weight=80, reps=10, completed=True),
        WorkoutSet(weight=80, reps=10, completed=True),
        WorkoutSet(weight=80, reps=9, completed=True)
    ]
    exercises_data.append(ExercisePerformance(
        exercise_name="Squat",
        sets=squat_sets,
        date=datetime.now() - timedelta(days=2),
        workout_type="Legs"
    ))

    # Scenario 3: Client close to target (should maintain)
    row_sets = [
        WorkoutSet(weight=50, reps=8, completed=True),
        WorkoutSet(weight=50, reps=7, completed=True),
        WorkoutSet(weight=50, reps=8, completed=True)
    ]
    exercises_data.append(ExercisePerformance(
        exercise_name="Dumbbell Row",
        sets=row_sets,
        date=datetime.now() - timedelta(days=1),
        workout_type="Pull"
    ))

    # Scenario 4: Client struggling (should decrease weight)
    ohp_sets = [
        WorkoutSet(weight=40, reps=5, completed=True),
        WorkoutSet(weight=40, reps=4, completed=True),
        WorkoutSet(weight=40, reps=6, completed=True)
    ]
    exercises_data.append(ExercisePerformance(
        exercise_name="Overhead Press",
        sets=ohp_sets,
        date=datetime.now() - timedelta(days=1),
        workout_type="Push"
    ))

    return exercises_data


def demo_rep_based_progressions():
    """Demonstrate the rep-based progression system."""

    print("="*80)
    print("🏋️  REP-BASED PROGRESSIVE OVERLOAD DEMO")
    print("="*80)

    print("\n📊 Creating demo workout data...")
    workout_data = create_demo_data()

    print(f"✅ Created {len(workout_data)} exercise performances")

    # Show the demo data
    print("\n📋 Demo scenarios:")
    for i, exercise in enumerate(workout_data, 1):
        avg_reps = sum(s.reps for s in exercise.sets) / len(exercise.sets)
        avg_weight = sum(s.weight for s in exercise.sets) / len(exercise.sets)
        print(
            f"   {i}. {exercise.exercise_name}: {avg_weight}kg × {avg_reps:.1f} reps avg")

    print("\n🧠 Analyzing rep-based progressions...")

    ai = ProgressiveOverloadAI()

    # Analyze progressions using rep-based logic
    progressions = ai.analyze_progression_patterns_rep_based(workout_data)

    if not progressions:
        print("❌ Could not generate progression recommendations.")
        return False

    print(f"✅ Generated progressions for {len(progressions)} exercises")

    # Display detailed results
    print("\n" + "="*80)
    print("📈 PROGRESSION RECOMMENDATIONS")
    print("="*80)

    for exercise_name, decisions in progressions.items():
        decision = decisions[0]

        print(f"\n🏋️  {exercise_name}")
        print(
            f"   Current: W({decision.current_weight}kg), R({decision.current_reps})")
        print(
            f"   ➡️  New: W({decision.recommended_weight}kg), R({decision.recommended_reps})")
        print(f"   🎯 Action: {decision.action_type.replace('_', ' ').title()}")
        print(f"   💭 Reason: {decision.reason}")
        print(f"   📊 Confidence: {decision.confidence:.1%}")

        # Show what would be written in Trainerize
        goals_format = f"Goals: W({decision.recommended_weight}), R({decision.recommended_reps})"
        print(f"   📱 Trainerize format: {goals_format}")

    # Summary statistics
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)

    action_counts = {}
    for decisions in progressions.values():
        action = decisions[0].action_type
        action_counts[action] = action_counts.get(action, 0) + 1

    for action, count in action_counts.items():
        emoji_map = {
            "increase_weight": "⬆️🔩",
            "increase_reps": "⬆️🔢",
            "maintain": "➡️",
            "decrease_weight": "⬇️🔩"
        }
        emoji = emoji_map.get(action, "❓")
        print(f"   {emoji} {action.replace('_', ' ').title()}: {count} exercises")

    print(f"\n🎯 REP-BASED LOGIC RULES:")
    print(f"   • Hit 15+ reps: +2.5kg weight, reset to 6 reps")
    print(f"   • Achieve target reps: +2 reps")
    print(f"   • Close to target (80%+): maintain current")
    print(f"   • Struggling (<80%): -2.5kg weight")

    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Run with real client data: python test_rep_based_progressions.py")
    print(f"   2. Choose option 1 to implement in Trainerize")
    print(f"   3. Goals will be set as: 'Goals: W(weight), R(reps)'")

    return True


def main():
    """Main function to run the demo."""

    print("🎯 This demo shows how the rep-based progression system works")
    print("💡 It uses sample data to demonstrate the different scenarios")

    input("\nPress Enter to continue...")

    success = demo_rep_based_progressions()

    if success:
        print(f"\n✅ Demo completed successfully!")
        print(f"💡 Try running the real system with: python test_rep_based_progressions.py")
    else:
        print(f"\n❌ Demo failed")


if __name__ == "__main__":
    main()
