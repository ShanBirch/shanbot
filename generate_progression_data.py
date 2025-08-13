import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict


def get_latest_workout_data():
    """Extract the latest workout data from the SQLite database"""
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get all workout sessions from the last 2 weeks
    cursor.execute("""
        SELECT client_name_key, workout_name, exercises_json, workout_date, week_identifier
        FROM client_workout_sessions 
        WHERE workout_date >= date('now', '-14 days')
        ORDER BY client_name_key, workout_name, workout_date DESC
    """)

    workout_data = cursor.fetchall()
    conn.close()

    return workout_data


def analyze_exercise_progression(exercise_data, exercise_name):
    """Analyze progression for a specific exercise and suggest next week's goals"""
    if not exercise_data or 'sets' not in exercise_data:
        return None

    sets = exercise_data['sets']
    if not sets:
        return None

    # Get the latest performance
    latest_sets = [s for s in sets if s.get(
        'weight', 0) > 0 or s.get('reps', 0) > 0]
    if not latest_sets:
        return None

    # Calculate average weight and reps from latest session
    total_weight = sum(s.get('weight', 0) for s in latest_sets)
    total_reps = sum(s.get('reps', 0) for s in latest_sets)
    avg_weight = total_weight / len(latest_sets) if latest_sets else 0
    avg_reps = total_reps / len(latest_sets) if latest_sets else 0

    # Simple progression logic
    if avg_weight > 0:  # Weight-based exercise
        # Increase weight by 2.5kg if they completed all reps
        if avg_reps >= 8:  # Assuming 8+ reps means they can handle more weight
            new_weight = avg_weight + 2.5
            # Reduce reps slightly with increased weight
            new_reps = max(6, int(avg_reps - 2))
        else:
            new_weight = avg_weight  # Keep same weight
            new_reps = min(12, int(avg_reps + 1))  # Try to increase reps
    else:  # Bodyweight exercise
        new_weight = "bodyweight"
        new_reps = min(15, int(avg_reps + 1))  # Increase reps for bodyweight

    return {
        "action": "modify_goals",
        "exercise_name": exercise_name,
        "weight": str(int(new_weight)) if isinstance(new_weight, (int, float)) else new_weight,
        "reps": str(new_reps)
    }


def generate_progression_data():
    """Generate progression data for all clients based on their latest workouts"""
    workout_data = get_latest_workout_data()

    # Group by client and workout
    client_workouts = defaultdict(lambda: defaultdict(list))

    for client_name_key, workout_name, exercises_json, workout_date, week_identifier in workout_data:
        try:
            exercises = json.loads(exercises_json)
            client_workouts[client_name_key][workout_name].append({
                'exercises': exercises,
                'date': workout_date,
                'week': week_identifier
            })
        except json.JSONDecodeError:
            print(
                f"Error parsing exercises for {client_name_key} - {workout_name}")
            continue

    # Generate progression recommendations
    progression_data = {}

    for client_name, workouts in client_workouts.items():
        progression_data[client_name] = {}

        for workout_name, sessions in workouts.items():
            if not sessions:
                continue

            # Get the most recent session
            latest_session = max(sessions, key=lambda x: x['date'])
            exercises = latest_session['exercises']

            workout_progressions = []

            for exercise in exercises:
                exercise_name = exercise.get('name', '')
                if not exercise_name:
                    continue

                progression = analyze_exercise_progression(
                    exercise, exercise_name)
                if progression:
                    workout_progressions.append(progression)

            if workout_progressions:
                progression_data[client_name][workout_name] = workout_progressions

    return progression_data


def save_progression_data(data, filename='weekly_progressions.json'):
    """Save progression data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Progression data saved to {filename}")


def print_progression_summary(data):
    """Print a summary of the generated progression data"""
    print("\n=== PROGRESSION DATA SUMMARY ===")

    for client_name, workouts in data.items():
        print(f"\nClient: {client_name}")
        for workout_name, actions in workouts.items():
            print(f"  Workout: {workout_name}")
            for action in actions:
                if action['action'] == 'modify_goals':
                    print(
                        f"    - {action['exercise_name']}: {action['weight']}kg x {action['reps']} reps")
                else:
                    print(
                        f"    - {action['action']}: {action['exercise_name']}")


if __name__ == "__main__":
    print("Generating workout progression data from database...")

    try:
        progression_data = generate_progression_data()

        if progression_data:
            print_progression_summary(progression_data)
            save_progression_data(progression_data)

            # Also save a backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"weekly_progressions_backup_{timestamp}.json"
            save_progression_data(progression_data, backup_filename)

            print(
                f"\nGenerated progression data for {len(progression_data)} clients")
            print("Ready to use with weekly_program_updater.py!")
        else:
            print("No workout data found in the database.")

    except Exception as e:
        print(f"Error generating progression data: {e}")
        import traceback
        traceback.print_exc()
