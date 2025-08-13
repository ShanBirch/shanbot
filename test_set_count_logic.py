#!/usr/bin/env python3
"""
Test Set Count Logic
===================

This script demonstrates how the improved algorithm handles the scenario where:
- The workout is programmed for 4 sets
- The client only completed 3 sets  
- We still want to give them goals for all 4 sets

Usage: python test_set_count_logic.py
"""


def test_set_count_scenarios():
    """Test different set count scenarios"""

    print("🧪 TESTING SET COUNT LOGIC")
    print("=" * 50)

    # Simulate the algorithm logic
    def generate_smart_set_goals(target_set_count, completed_sets, next_weight, next_reps, is_bodyweight):
        """Generate goals for ALL target sets"""
        goals = []
        completed_count = len(completed_sets)

        for i in range(target_set_count):
            set_num = i + 1

            if i < completed_count:
                # This set was completed - use progression logic
                if is_bodyweight:
                    goals.append(f"S{set_num}: {next_reps}")
                else:
                    goals.append(f"S{set_num}: {next_weight}kg*{next_reps}")
            else:
                # This set was NOT completed - use intelligent default
                if is_bodyweight:
                    default_reps = max(6, next_reps - 2)  # Slightly easier
                    goals.append(f"S{set_num}: {default_reps}")
                else:
                    if next_weight > 10:
                        default_weight = next_weight - 5  # Reduce weight
                        goals.append(
                            f"S{set_num}: {default_weight}kg*{next_reps}")
                    else:
                        default_reps = max(6, next_reps - 2)  # Reduce reps
                        goals.append(
                            f"S{set_num}: {next_weight}kg*{default_reps}")

        return " | ".join(goals)

    # Test scenarios
    scenarios = [
        {
            "name": "Lat Pulldown - Completed 3/4 sets",
            "exercise": "Lat Pulldown",
            "completed_sets": [
                {"weight": 25, "reps": 10},
                {"weight": 25, "reps": 10},
                {"weight": 25, "reps": 8}
            ],
            "programmed_sets": 4,
            "next_weight": 25,
            "next_reps": 12,
            "is_bodyweight": False
        },
        {
            "name": "Push Ups - Completed 2/4 sets",
            "exercise": "Push Up",
            "completed_sets": [
                {"weight": 0, "reps": 12},
                {"weight": 0, "reps": 10}
            ],
            "programmed_sets": 4,
            "next_weight": 0,
            "next_reps": 15,
            "is_bodyweight": True
        },
        {
            "name": "Bicep Curl - Completed 4/3 sets (extra set)",
            "exercise": "Dumbbell Bicep Curl",
            "completed_sets": [
                {"weight": 15, "reps": 8},
                {"weight": 15, "reps": 8},
                {"weight": 15, "reps": 6},
                {"weight": 12.5, "reps": 8}  # Drop set
            ],
            "programmed_sets": 3,
            "next_weight": 17.5,
            "next_reps": 10,
            "is_bodyweight": False
        }
    ]

    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}")
        print("-" * 40)
        print(f"Exercise: {scenario['exercise']}")
        print(f"Completed Sets: {len(scenario['completed_sets'])}")
        print(f"Programmed Sets: {scenario['programmed_sets']}")
        print(
            f"Target Sets: {max(scenario['programmed_sets'], len(scenario['completed_sets']))}")

        print(f"\nCompleted Set Data:")
        for i, set_data in enumerate(scenario['completed_sets'], 1):
            if scenario['is_bodyweight']:
                print(f"  Set {i}: {set_data['reps']} reps")
            else:
                print(
                    f"  Set {i}: {set_data['weight']}kg × {set_data['reps']} reps")

        # Generate goals
        target_set_count = max(
            scenario['programmed_sets'], len(scenario['completed_sets']))
        goals = generate_smart_set_goals(
            target_set_count,
            scenario['completed_sets'],
            scenario['next_weight'],
            scenario['next_reps'],
            scenario['is_bodyweight']
        )

        print(f"\n✅ Generated Goals: {goals}")
        print(f"💡 Logic:")

        completed_count = len(scenario['completed_sets'])
        for i in range(target_set_count):
            set_num = i + 1
            if i < completed_count:
                print(
                    f"   Set {set_num}: Used progression (client completed this set)")
            else:
                print(
                    f"   Set {set_num}: Used intelligent default (client didn't complete this set)")


def test_historical_set_detection():
    """Test how we detect programmed set counts from historical data"""

    print(f"\n\n🔍 TESTING HISTORICAL SET COUNT DETECTION")
    print("=" * 50)

    # Simulate historical data
    historical_data = {
        "Lat Pulldown": [4, 4, 3, 4, 4, 3, 4],  # Usually 4 sets, sometimes 3
        "Push Up": [3, 3, 3, 3, 2, 3, 3],       # Usually 3 sets, once only 2
        "Bench Press": [4, 4, 4, 4, 4, 4, 4],   # Always 4 sets
    }

    print("Historical Set Count Data:")
    for exercise, counts in historical_data.items():
        # Find most common (mode)
        mode_count = max(set(counts), key=counts.count)
        print(f"  {exercise}: {counts} → Programmed: {mode_count} sets")

        # Show the logic
        unique_counts = list(set(counts))
        for count in unique_counts:
            frequency = counts.count(count)
            percentage = (frequency / len(counts)) * 100
            marker = " ← MOST COMMON" if count == mode_count else ""
            print(
                f"    {count} sets: {frequency}/{len(counts)} times ({percentage:.1f}%){marker}")


if __name__ == "__main__":
    test_set_count_scenarios()
    test_historical_set_detection()

    print(f"\n\n🎯 SUMMARY")
    print("=" * 50)
    print("✅ Algorithm now handles:")
    print("   • Clients who complete fewer sets than programmed")
    print("   • Clients who do extra sets beyond programmed")
    print("   • Intelligent defaults for missing sets")
    print("   • Historical data analysis to detect intended set counts")
    print("   • Different strategies for bodyweight vs weighted exercises")
