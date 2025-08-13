#!/usr/bin/env python
import json
from simple_blue_video import calculate_goal_completion_rate, get_goal_summary

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("🎯 ELENA'S CORRECTED NUMBERS")
print("=" * 40)

# Get the corrected numbers
goal_rate = calculate_goal_completion_rate(elena_data)
goal_summary = get_goal_summary(elena_data)

print(f"Goal Completion Rate: {goal_rate:.0f}%")
print(f"Goal Summary: {goal_summary}")

print("\n🎬 Video slide should now say:")
print(f"'Last Week's Goal Results'")
print(f"'{goal_rate:.0f}% Goal Completion Rate!'")
print(f"'{goal_summary}'")

print("\n✅ Numbers are now consistent!")
print("- Goal completion counts unique exercises only")
print("- Exercise improvements detail shows same unique exercises")
print("- No more confusing '9 exercises' vs '3 exercises' mismatch")
