from workout_utils import get_current_week_workouts, get_recent_workouts
import sys
sys.path.insert(0, 'app/dashboard_modules')


print("=== Testing with debug output ===")
print("Current week workouts:")
current = get_current_week_workouts('shane_minahan')
print(f"Result: {current['total_sessions']} sessions")

print("\nRecent workouts:")
recent = get_recent_workouts('shane_minahan')
print(f"Result: {len(recent)} sessions")
