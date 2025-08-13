#!/usr/bin/env python3

# Test the scenario: 4 sets programmed, only 3 completed
def test_scenario():
    print("SCENARIO: Client completed 3/4 sets of Lat Pulldown")
    print("=" * 50)

    # Data from database (what client actually did)
    completed_sets = [
        {"weight": 25, "reps": 10},  # Set 1
        {"weight": 25, "reps": 10},  # Set 2
        {"weight": 25, "reps": 8}    # Set 3
    ]

    # What the workout program calls for
    programmed_sets = 4

    # Progression algorithm result
    next_weight = 25
    next_reps = 12  # 10 -> 12 progression

    print(f"Completed sets: {len(completed_sets)}")
    print(f"Programmed sets: {programmed_sets}")
    print(f"Target sets: {max(programmed_sets, len(completed_sets))}")

    # OLD ALGORITHM (wrong):
    print(f"\nOLD ALGORITHM (WRONG):")
    old_goals = []
    for i in range(len(completed_sets)):  # Only 3 sets!
        old_goals.append(f"S{i+1}: {next_weight}kg*{next_reps}")
    print(f"Goals: {' | '.join(old_goals)}")
    print("❌ Problem: Missing Set 4!")

    # NEW ALGORITHM (correct):
    print(f"\nNEW ALGORITHM (CORRECT):")
    new_goals = []
    target_count = max(programmed_sets, len(completed_sets))

    for i in range(target_count):
        set_num = i + 1
        if i < len(completed_sets):
            # Use progression for completed sets
            new_goals.append(f"S{set_num}: {next_weight}kg*{next_reps}")
        else:
            # Use intelligent default for missing sets
            default_weight = next_weight - 5  # Slightly easier
            new_goals.append(f"S{set_num}: {default_weight}kg*{next_reps}")

    print(f"Goals: {' | '.join(new_goals)}")
    print("✅ Success: All 4 sets have goals!")

    print(f"\nEXPLANATION:")
    for i in range(target_count):
        set_num = i + 1
        if i < len(completed_sets):
            print(f"  Set {set_num}: Progression from completed data")
        else:
            print(
                f"  Set {set_num}: Intelligent default (client didn't complete)")


if __name__ == "__main__":
    test_scenario()
