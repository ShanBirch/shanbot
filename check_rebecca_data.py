import sqlite3
import json


def check_rebecca_data():
    db_path = r"app\analytics_data_good.sqlite"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get Rebecca's data
        cursor.execute("""
            SELECT workout_date, exercises_json, workout_name 
            FROM client_workout_sessions 
            WHERE client_name_key LIKE '%rebecca%' 
            ORDER BY workout_date DESC 
            LIMIT 3
        """)

        rows = cursor.fetchall()
        print(f"Found {len(rows)} sessions for Rebecca")

        for i, (date, exercises_json, workout_name) in enumerate(rows):
            print(f"\n--- Session {i+1}: {date} ({workout_name}) ---")

            try:
                data = json.loads(exercises_json)
                print(f"Data type: {type(data)}")

                if isinstance(data, dict):
                    print(f"Dict keys: {list(data.keys())[:5]}")
                    # Show first exercise details
                    for exercise_name, exercise_data in list(data.items())[:2]:
                        print(f"Exercise: {exercise_name}")
                        print(f"Exercise data: {exercise_data}")
                        break
                elif isinstance(data, list):
                    print(f"List length: {len(data)}")
                    if data:
                        print(f"First item: {data[0]}")

            except Exception as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw JSON (first 200 chars): {exercises_json[:200]}")

        conn.close()

    except Exception as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    check_rebecca_data()
