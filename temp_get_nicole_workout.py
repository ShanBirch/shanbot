import sqlite3
import json
from datetime import date, timedelta

DB_PATH = 'app/analytics_data_good.sqlite'


def get_nicoles_last_leg_day():
    """Fetches Nicole Lynch's most recent Leg Day workout from last week."""
    today = date.today()
    start_of_last_week = today - timedelta(days=today.weekday() + 7)
    end_of_last_week = start_of_last_week + timedelta(days=6)

    print(
        f"Searching for Nicole Lynch's Leg Day between {start_of_last_week} and {end_of_last_week}...")

    workout_details = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT workout_date, workout_name, exercises_json
        FROM client_workout_sessions
        WHERE (client_name_key = 'nicole_lynch' OR ig_username = 'nicole_lynch')
          AND date(workout_date) BETWEEN ? AND ?
          AND workout_name LIKE '%Leg%'
        ORDER BY workout_date DESC
        LIMIT 1
        """
        cursor.execute(query, (start_of_last_week.isoformat(),
                       end_of_last_week.isoformat()))
        row = cursor.fetchone()

        if row:
            workout_details = {
                "date": row["workout_date"],
                "name": row["workout_name"],
                "exercises": json.loads(row["exercises_json"])
            }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

    return workout_details


if __name__ == '__main__':
    workout = get_nicoles_last_leg_day()

    if workout:
        print(f"\n--- Nicole Lynch's Last Leg Day ---")
        print(f"Date: {workout['date']}")
        print(f"Workout: {workout['name']}")
        print("-" * 35)

        for exercise in workout['exercises']:
            print(f"\n  Exercise: {exercise.get('name', 'Unknown Exercise')}")
            if exercise.get('sets'):
                for s in exercise['sets']:
                    print(
                        f"    - Set {s.get('set')}: {s.get('reps')} reps at {s.get('weight')}kg")
            else:
                print("    - No sets recorded for this exercise.")
    else:
        print("\nCould not find a Leg Day workout for Nicole Lynch last week.")
