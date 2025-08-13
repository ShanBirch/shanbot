from workout_utils import get_current_week_workouts
from datetime import datetime

print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
print(f"Current week: {datetime.now().strftime('%Y-W%U')}")

result = get_current_week_workouts('Kristyleecoop')
print(f"\nSessions this week: {result['total_sessions']}")

print("\nWorkout sessions:")
for i, workout in enumerate(result['workouts'], 1):
    print(f"  {i}. {workout['date']} - {workout['name']}")

print(f"\nWeek identifier: {result['week_identifier']}")
