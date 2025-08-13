#!/usr/bin/env python
import json
from simple_blue_video import get_exercise_improvement_details

# Load Elena's data
with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
    elena_data = json.load(f)

print("🎯 ELENA'S EXERCISE IMPROVEMENT DETAILS")
print("=" * 50)

improvements = get_exercise_improvement_details(elena_data)

print(f"Found {len(improvements)} unique improved exercises:")
for i, improvement in enumerate(improvements, 1):
    print(f"{i}. {improvement}")

print("\nThis should match what appears on the Exercise Improvements Detail slide!")
