from workout_utils import get_current_week_workouts
from datetime import datetime
import json

print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
print(f"Current week: {datetime.now().strftime('%Y-W%U')}")

# Test with Kristyleecoop
result = get_current_week_workouts('Kristyleecoop')
print(f"\nKristy's workout data:")
print(f"Sessions this week: {result['total_sessions']}")
print(
    f"Week range: {result.get('week_start', 'N/A')} to {result.get('week_end', 'N/A')}")

if result['workouts']:
    print("\nWorkout sessions:")
    for i, workout in enumerate(result['workouts'], 1):
        print(f"  {i}. {workout['date']} - {workout['name']}")

if result.get('improvements'):
    print(f"\nImprovements detected: {len(result['improvements'])}")
    for improvement in result['improvements']:
        print(
            f"  • {improvement['exercise']}: {improvement['type']} {improvement['improvement']} (from {improvement['from']} to {improvement['to']})")
else:
    print("\nNo improvements detected")

print(f"\nFull result structure:")
print(json.dumps(result, indent=2, default=str))
