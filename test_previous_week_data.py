from workout_utils import get_current_week_workouts
from datetime import datetime, timedelta
import sqlite3
import json

# Let's manually test what would happen if we set the "current week" to be the week with data
# This simulates what the dashboard would show when there are workouts in both weeks

SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def test_week_with_data():
    """Test with a week that has actual workout data"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    # Set "current week" to the week with data (2025-05-18 to 2025-05-24)
    week_start_str = "2025-05-18"
    week_end_str = "2025-05-24"

    # Previous week would be 2025-05-11 to 2025-05-17
    prev_week_start_str = "2025-05-11"
    prev_week_end_str = "2025-05-17"

    print(f"Testing with 'current week': {week_start_str} to {week_end_str}")
    print(f"'Previous week': {prev_week_start_str} to {prev_week_end_str}")

    # Get workouts for "current week"
    cursor.execute('''
        SELECT workout_date, week_identifier, workout_name, exercises_json
        FROM client_workout_sessions 
        WHERE ig_username = "Kristyleecoop" 
        AND workout_date >= ?
        AND workout_date <= ?
        ORDER BY workout_date DESC
    ''', (week_start_str, week_end_str))

    current_week_sessions = cursor.fetchall()

    # Get workouts for "previous week"
    cursor.execute('''
        SELECT workout_date, week_identifier, workout_name, exercises_json
        FROM client_workout_sessions 
        WHERE ig_username = "Kristyleecoop" 
        AND workout_date >= ?
        AND workout_date <= ?
        ORDER BY workout_date DESC
    ''', (prev_week_start_str, prev_week_end_str))

    previous_week_sessions = cursor.fetchall()

    print(f"\nCurrent week sessions: {len(current_week_sessions)}")
    for session in current_week_sessions:
        print(f"  {session[0]} - {session[2]}")

    print(f"\nPrevious week sessions: {len(previous_week_sessions)}")
    for session in previous_week_sessions:
        print(f"  {session[0]} - {session[2]}")

    # Process previous week data for comparison
    prev_week_exercises = {}
    for session in previous_week_sessions:
        workout_date, week_id, workout_name, exercises_json = session
        try:
            exercises = json.loads(exercises_json)
            for exercise in exercises:
                exercise_name = exercise.get('name', 'Unknown')
                sets_data = exercise.get('sets', [])

                if sets_data:
                    max_weight = max(set_info.get('weight', 0)
                                     for set_info in sets_data)
                    total_reps = sum(set_info.get('reps', 0)
                                     for set_info in sets_data)

                    if exercise_name not in prev_week_exercises:
                        prev_week_exercises[exercise_name] = {
                            'max_weight': max_weight,
                            'total_reps': total_reps,
                            'sessions': 1
                        }
                    else:
                        # Update with best performance from previous week
                        prev_week_exercises[exercise_name]['max_weight'] = max(
                            prev_week_exercises[exercise_name]['max_weight'], max_weight)
                        prev_week_exercises[exercise_name]['total_reps'] = max(
                            prev_week_exercises[exercise_name]['total_reps'], total_reps)
                        prev_week_exercises[exercise_name]['sessions'] += 1
        except json.JSONDecodeError:
            continue

    print(f"\nPrevious week exercise summary:")
    for exercise_name, data in prev_week_exercises.items():
        print(
            f"  {exercise_name}: Max weight {data['max_weight']}kg, Max reps {data['total_reps']}")

    # Now check current week for improvements
    improvements = []
    for session in current_week_sessions:
        workout_date, week_id, workout_name, exercises_json = session
        try:
            exercises = json.loads(exercises_json)
            for exercise in exercises:
                exercise_name = exercise.get('name', 'Unknown')
                sets_data = exercise.get('sets', [])

                if sets_data and exercise_name in prev_week_exercises:
                    max_weight = max(set_info.get('weight', 0)
                                     for set_info in sets_data)
                    total_reps = sum(set_info.get('reps', 0)
                                     for set_info in sets_data)

                    prev_data = prev_week_exercises[exercise_name]

                    # Check weight improvement
                    if max_weight > prev_data['max_weight']:
                        weight_increase = max_weight - prev_data['max_weight']
                        improvements.append({
                            'exercise': exercise_name,
                            'type': 'weight',
                            'improvement': f"+{weight_increase}kg",
                            'from': prev_data['max_weight'],
                            'to': max_weight
                        })

                    # Check rep improvement
                    if total_reps > prev_data['total_reps']:
                        rep_increase = total_reps - prev_data['total_reps']
                        improvements.append({
                            'exercise': exercise_name,
                            'type': 'reps',
                            'improvement': f"+{rep_increase}",
                            'from': prev_data['total_reps'],
                            'to': total_reps
                        })
        except json.JSONDecodeError:
            continue

    print(f"\nImprovements detected: {len(improvements)}")
    for improvement in improvements:
        print(
            f"  • {improvement['exercise']}: {improvement['type']} {improvement['improvement']} (from {improvement['from']} to {improvement['to']})")

    conn.close()


if __name__ == "__main__":
    test_week_with_data()
