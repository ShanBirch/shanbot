#!/usr/bin/env python3
"""
Test script for the rep-based progressive overload system.
This will analyze a client's workout data and optionally implement progressions in Trainerize.
"""

from progressive_overload_ai import ProgressiveOverloadAI
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_client_progression(client_name):
    """Test the rep-based progression system for a specific client."""

    print("="*80)
    print(f"🏋️  REP-BASED PROGRESSIVE OVERLOAD SYSTEM")
    print(f"🎯 Client: {client_name}")
    print("="*80)

    ai = ProgressiveOverloadAI()

    print(f"\n📊 Loading workout data for {client_name}...")

    # Load workout data (try SQLite first, fallback to JSON)
    workout_data = ai.load_client_workout_data(client_name, weeks_back=4)

    if not workout_data:
        print("❌ No workout data found!")
        print("💡 Make sure:")
        print(f"   • Client '{client_name}' exists in the database")
        print("   • They have logged workouts in the last 4 weeks")
        print("   • Database file 'analytics_data_good.sqlite' exists")
        return False

    print(f"✅ Loaded {len(workout_data)} exercise performances")

    # Show some sample data
    print(f"\n📋 Sample exercises found:")
    exercise_names = list(set([perf.exercise_name for perf in workout_data]))
    for i, exercise in enumerate(exercise_names[:5]):
        print(f"   {i+1}. {exercise}")
    if len(exercise_names) > 5:
        print(f"   ... and {len(exercise_names) - 5} more exercises")

    print(f"\n🧠 Analyzing rep-based progressions...")

    # Analyze progressions using rep-based logic
    progressions = ai.analyze_progression_patterns_rep_based(workout_data)

    if not progressions:
        print("❌ Could not generate progression recommendations.")
        return False

    print(f"✅ Generated progressions for {len(progressions)} exercises")

    # Display summary
    print(f"\n📈 PROGRESSION SUMMARY:")
    action_counts = {}
    for exercise_name, decisions in progressions.items():
        action = decisions[0].action_type
        action_counts[action] = action_counts.get(action, 0) + 1

    for action, count in action_counts.items():
        emoji = {"increase_weight": "⬆️🔩", "increase_reps": "⬆️🔢",
                 "maintain": "➡️", "decrease_weight": "⬇️🔩"}.get(action, "❓")
        print(f"   {emoji} {action.replace('_', ' ').title()}: {count} exercises")

    # Generate detailed report
    report = ai.generate_progression_report(client_name, progressions)
    print("\n" + "="*80)
    print("📋 DETAILED PROGRESSION REPORT")
    print("="*80)
    print(report)
    print("="*80)

    # Save progression history
    ai.save_progression_history(client_name, progressions)
    print(f"💾 Progression history saved")

    # Ask if user wants to implement changes
    print(f"\n🤖 IMPLEMENTATION OPTIONS:")
    print(f"   1. 🚀 Implement in Trainerize (Full automation)")
    print(f"   2. 📋 Save report only (Manual review)")
    print(f"   3. ❌ Exit")

    choice = input("\nEnter your choice (1/2/3): ").strip()

    if choice == "1":
        print(f"\n🚀 TRAINERIZE IMPLEMENTATION")
        print(f"This will automatically update {client_name}'s program with:")

        for exercise_name, decisions in progressions.items():
            decision = decisions[0]
            print(
                f"   • {exercise_name}: Goals: W({decision.recommended_weight}), R({decision.recommended_reps})")

        print(f"\n⚠️  IMPORTANT:")
        print(f"   • Make sure Trainerize is not open in another browser")
        print(f"   • This will modify the client's actual program")
        print(f"   • Changes cannot be easily undone")

        confirm = input(
            f"\n✅ Proceed with implementation? (y/n): ").lower().strip()

        if confirm in ['y', 'yes']:
            print(f"\n🔄 Starting Trainerize automation...")
            success = ai.implement_progressions(client_name, progressions)

            if success:
                print(f"\n✅ SUCCESS! Progressions implemented in Trainerize!")
                print(f"🎯 Goals format: 'Goals: W(weight), R(reps)'")
                print(f"📱 Client will see these goals in their workouts")
            else:
                print(f"\n❌ FAILED! Some or all progressions could not be implemented.")
                print(f"📋 Check the logs for details")
        else:
            print(f"\n❌ Implementation cancelled")

    elif choice == "2":
        print(f"\n📋 Report saved to progression history")
        print(f"💡 You can manually review and implement these changes")

    else:
        print(f"\n👋 Exiting...")

    print(f"\n🎯 REP-BASED LOGIC SUMMARY:")
    print(f"   • Hit 15+ reps: +2.5kg weight, reset to 6 reps")
    print(f"   • Achieve target reps: +2 reps")
    print(f"   • Close to target (80%+): maintain current")
    print(f"   • Struggling (<80%): -2.5kg weight")

    return True


def main():
    """Main function to run the test."""

    print("🏋️  REP-BASED PROGRESSIVE OVERLOAD TESTER")
    print("="*50)

    # Default client (change this to test different clients)
    default_client = "Alice Forster"

    client_name = input(
        f"Enter client name (or press Enter for '{default_client}'): ").strip()
    if not client_name:
        client_name = default_client

    success = test_client_progression(client_name)

    if not success:
        print(f"\n💡 Try testing with a different client or check data availability")


if __name__ == "__main__":
    main()
