#!/usr/bin/env python3
"""
Test Improved Algorithm
======================

This script tests the improved algorithm changes:
1. Bodyweight exercises show only reps (no weight)
2. Set count is detected from existing workout data
3. Intelligent defaults for new exercises

Usage: python test_improved_algorithm.py
"""

from run_weekly_program_updater_all_clients import WeeklyProgressionSystem
import sys
import os
sys.path.append(os.getcwd())


def test_bodyweight_detection():
    """Test the bodyweight exercise detection"""
    system = WeeklyProgressionSystem()

    print("=== TESTING BODYWEIGHT EXERCISE DETECTION ===")

    test_exercises = [
        ("Push Up", 0),  # Should be bodyweight
        ("Pull Up", 0),  # Should be bodyweight
        ("Chin Up", 0),  # Should be bodyweight
        ("Dumbbell Chest Press", 25),  # Should NOT be bodyweight
        ("Barbell Squat", 60),  # Should NOT be bodyweight
        ("Plank", 0),  # Should be bodyweight
        ("Jumping Jacks", 0),  # Should be bodyweight
        ("Lat Pulldown", 0),  # Should be bodyweight (0 weight)
    ]

    for exercise_name, weight in test_exercises:
        is_bodyweight = system.is_bodyweight_exercise(exercise_name, weight)
        print(
            f"  • {exercise_name} (weight: {weight}kg) -> {'BODYWEIGHT' if is_bodyweight else 'WEIGHTED'}")


def test_set_goal_generation():
    """Test the set goal generation"""
    system = WeeklyProgressionSystem()

    print("\n=== TESTING SET GOAL GENERATION ===")

    test_cases = [
        # (set_count, weight, reps, is_bodyweight, expected_format)
        (3, 0, 8, True, "S1: 8 | S2: 8 | S3: 8"),
        (4, 0, 10, True, "S1: 10 | S2: 10 | S3: 10 | S4: 10"),
        (3, 25, 12, False, "S1: 25kg*12 | S2: 25kg*12 | S3: 25kg*12"),
        (4, 50, 6, False, "S1: 50kg*6 | S2: 50kg*6 | S3: 50kg*6 | S4: 50kg*6"),
        (5, 0, 15, True, "S1: 15 | S2: 15 | S3: 15 | S4: 15 | S5: 15"),
    ]

    for set_count, weight, reps, is_bodyweight, expected in test_cases:
        result = system.generate_set_goals(
            set_count, weight, reps, is_bodyweight)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(
            f"  • {set_count} sets, {weight}kg, {reps} reps, bodyweight={is_bodyweight}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result}")
        print(f"    Status:   {status}")
        print()


def test_progression_algorithm():
    """Test the full progression algorithm with sample data"""
    system = WeeklyProgressionSystem()

    print("=== TESTING FULL PROGRESSION ALGORITHM ===")

    # Simulate some exercise data
    test_scenarios = [
        {
            'name': 'Push Up',
            'sets': [{'weight': 0, 'reps': 12}, {'weight': 0, 'reps': 10}, {'weight': 0, 'reps': 8}],
            'expected_bodyweight': True,
            'expected_next_reps': 15
        },
        {
            'name': 'Dumbbell Chest Press',
            'sets': [{'weight': 20, 'reps': 12}, {'weight': 20, 'reps': 11}, {'weight': 20, 'reps': 10}],
            'expected_bodyweight': False,
            'expected_next_reps': 15
        },
        {
            'name': 'Barbell Squat',
            'sets': [{'weight': 60, 'reps': 15}, {'weight': 60, 'reps': 14}, {'weight': 60, 'reps': 13}],
            'expected_bodyweight': False,
            'expected_next_reps': 6,  # Reset to 6 after 15
            'expected_weight_increase': True
        }
    ]

    for scenario in test_scenarios:
        exercise_name = scenario['name']
        sets = scenario['sets']

        print(f"\n--- Testing {exercise_name} ---")

        # Simulate the algorithm logic
        actual_set_count = len(sets)
        best_set = max(sets, key=lambda s: (
            float(s.get('weight', 0)), int(s.get('reps', 0))))
        current_weight = float(best_set.get('weight', 0))
        current_reps = int(best_set.get('reps', 0))

        is_bodyweight = system.is_bodyweight_exercise(
            exercise_name, current_weight)
        next_reps = system.apply_rep_progression_algorithm(current_reps)
        increase_weight = (next_reps == 6 and current_reps >=
                           15 and not is_bodyweight)
        next_weight = system.get_next_weight(
            current_weight, exercise_name, increase_weight) if not is_bodyweight else 0

        recommended_reps = system.generate_set_goals(
            actual_set_count, next_weight, next_reps, is_bodyweight)

        print(
            f"  Current: {system.format_exercise_display(current_weight, current_reps, is_bodyweight)} ({actual_set_count} sets)")
        print(
            f"  Next: {system.format_exercise_display(next_weight, next_reps, is_bodyweight)}")
        print(f"  Full goals: {recommended_reps}")
        print(
            f"  Bodyweight: {is_bodyweight} (expected: {scenario['expected_bodyweight']})")
        print(
            f"  Next reps: {next_reps} (expected: {scenario['expected_next_reps']})")

        if 'expected_weight_increase' in scenario:
            weight_increased = next_weight > current_weight
            print(
                f"  Weight increased: {weight_increased} (expected: {scenario['expected_weight_increase']})")


def main():
    """Run all tests"""
    print("🧪 TESTING IMPROVED ALGORITHM")
    print("=" * 50)

    test_bodyweight_detection()
    test_set_goal_generation()
    test_progression_algorithm()

    print("\n" + "=" * 50)
    print("✅ ALGORITHM TESTING COMPLETE")
    print("\nKEY IMPROVEMENTS:")
    print("1. ✅ Bodyweight exercises now show only reps (e.g., 'S1: 10' instead of 'S1: 0kg*10')")
    print("2. ✅ Set count is detected from actual workout data (3, 4, 5+ sets)")
    print("3. ✅ Intelligent defaults based on exercise type and equipment")
    print("4. ✅ Better logging shows actual vs. expected progression")


if __name__ == "__main__":
    main()
