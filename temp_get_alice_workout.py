import sqlite3
import json
from datetime import date, timedelta

DB_PATH = 'app/analytics_data_good.sqlite'


def get_alices_last_chest_day():
    """Fetches Alice Forster's most recent Chest Day workout from last week."""
    today = date.today()
    start_of_last_week = today - timedelta(days=today.weekday() + 7)
    end_of_last_week = start_of_last_week + timedelta(days=6)

    print(
        f"Searching for Alice Forster's Chest Day between {start_of_last_week} and {end_of_last_week}...")

    workout_details = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
        SELECT workout_date, workout_name, exercises_json
        FROM client_workout_sessions
        WHERE (client_name_key = 'alice_forster' OR ig_username = 'alice_forster')
          AND date(workout_date) BETWEEN ? AND ?
          AND workout_name LIKE '%Chest%'
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
    workout = get_alices_last_chest_day()

    if workout:
        print(f"\n--- Alice Forster's Last Chest Day ---")
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
        print("\nCould not find a Chest Day workout for Alice Forster last week.")
