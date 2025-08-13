import sqlite3
import json
from datetime import date, timedelta
from collections import defaultdict
import logging

DB_PATH = 'app/analytics_data_good.sqlite'


def get_last_two_weeks_workouts():
    """Fetches all client workout data from the last two calendar weeks."""
    today = date.today()
    start_of_period = today - timedelta(days=today.weekday() + 14)
    end_of_period = today - timedelta(days=today.weekday() + 1)

    print(
        f"Fetching workouts from {start_of_period} to {end_of_period} for goal setting...")

    workouts_by_client = defaultdict(list)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
        SELECT client_name_key, ig_username, workout_date, exercises_json, workout_name
        FROM client_workout_sessions
        WHERE date(workout_date) BETWEEN ? AND ?
        ORDER BY client_name_key, workout_date
        """
        cursor.execute(query, (start_of_period.isoformat(),
                       end_of_period.isoformat()))
        rows = cursor.fetchall()

        if not rows:
            print("No workouts found for the last two weeks.")
            return None

        for row in rows:
            client_key = row['ig_username'] if row['ig_username'] else row['client_name_key']
            try:
                workouts_by_client[client_key].append({
                    'date': row['workout_date'],
                    'workout_type': row['workout_name'],
                    'exercises': json.loads(row['exercises_json'])
                })
            except (json.JSONDecodeError, TypeError):
                logging.warning(
                    f"Could not parse exercises_json for {client_key} on {row['workout_date']}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()
    return workouts_by_client


def calculate_progressive_overload_goals(all_workouts):
    """
    Calculates new weekly goals by finding the single best performance for each exercise
    across all provided workouts (e.g., from the last two weeks).
    """
    new_goals = []
    best_performances = {}  # Key: exercise_name, Value: {best_set, workout_type, num_sets}

    def get_new_rep_target(reps):
        if 6 <= reps <= 7:
            return 8
        if 8 <= reps <= 9:
            return 10
        if 10 <= reps <= 11:
            return 12
        if 12 <= reps <= 14:
            return 15
        return None

    # First, iterate through all workouts to find the absolute best performance for each exercise
    for workout in all_workouts:
        for exercise in workout.get('exercises', []):
            exercise_name = exercise.get('name')
            if not exercise_name or not isinstance(exercise.get('sets'), list) or not exercise['sets']:
                continue

            # Find the best set within the current exercise entry
            current_best_set = max(exercise['sets'], key=lambda s: (
                s.get('weight', 0), s.get('reps', 0)))

            if exercise_name not in best_performances:
                best_performances[exercise_name] = {
                    'best_set': current_best_set,
                    'workout_type': workout.get('workout_type', 'General'),
                    'num_sets': len(exercise['sets'])
                }
            else:
                # Compare with the existing best set for this exercise across all workouts
                existing_best_set = best_performances[exercise_name]['best_set']
                current_weight = current_best_set.get('weight', 0)
                current_reps = current_best_set.get('reps', 0)
                existing_weight = existing_best_set.get('weight', 0)
                existing_reps = existing_best_set.get('reps', 0)

                if (current_weight > existing_weight) or \
                   (current_weight == existing_weight and current_reps > existing_reps):
                    # Found a new best performance
                    best_performances[exercise_name]['best_set'] = current_best_set
                    best_performances[exercise_name]['workout_type'] = workout.get(
                        'workout_type', 'General')
                    best_performances[exercise_name]['num_sets'] = len(
                        exercise['sets'])

    # Now, calculate goals based on these overall best performances
    for exercise_name, performance_data in best_performances.items():
        best_set = performance_data['best_set']
        last_reps = best_set.get('reps', 0)
        last_weight = best_set.get('weight', 0)
        target_sets = performance_data['num_sets']

        new_target_reps = get_new_rep_target(last_reps)
        new_target_weight = last_weight

        if new_target_reps is None or last_reps >= 15:
            new_target_reps = 6
            new_target_weight += 2.5

        goal = {
            "workout_name": performance_data['workout_type'],
            "exercise_name": exercise_name,
            "target_reps": new_target_reps,
            "target_weight": new_target_weight,
            "target_sets": target_sets,
            "notes": f"Last period's best set: {last_reps} reps at {last_weight}kg."
        }
        new_goals.append(goal)

    return new_goals


def update_client_goals(client_key, week_identifier, goals):
    """Clears old goals and inserts new progressive overload goals for the week."""
    if not goals:
        print("  - No new goals to update.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Clear existing goals for the week
        cursor.execute("""
            DELETE FROM weekly_goals 
            WHERE (ig_username = ? OR client_name_key = ?) AND week_identifier = ? AND status = 'active'
        """, (client_key, client_key, week_identifier))
        print(
            f"  - Cleared {cursor.rowcount} old active goals for week {week_identifier}.")

        # Insert new goals
        for goal in goals:
            cursor.execute("""
                INSERT INTO weekly_goals 
                    (client_name_key, ig_username, week_identifier, workout_name, exercise_name, target_reps, target_weight, target_sets, goal_type, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_key, client_key, week_identifier, goal['workout_name'], goal['exercise_name'], goal['target_reps'], goal['target_weight'], goal['target_sets'], 'progressive_overload', 'active', goal['notes']))

        conn.commit()
        print(f"  - Successfully inserted {len(goals)} new goals.")
    except sqlite3.Error as e:
        print(f"  - Database error during goal update for {client_key}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    all_client_workouts = get_last_two_weeks_workouts()

    if all_client_workouts:
        today = date.today()
        current_week_start_dt = today - timedelta(days=today.weekday())

        current_week_identifier = f"{current_week_start_dt.year}-W{current_week_start_dt.isocalendar()[1]:02d}"

        print(
            f"\n--- Updating Client Programs for Week: {current_week_identifier} ---")

        for client, workouts in all_client_workouts.items():
            print(f"\n--- Processing: {client} ---")

            new_goals = calculate_progressive_overload_goals(workouts)

            update_client_goals(client, current_week_identifier, new_goals)

            if new_goals:
                print("  ✨ New Goals Set:")
                for goal in new_goals:
                    print(
                        f"    - {goal['exercise_name']}: {goal['target_sets']} sets of {goal['target_reps']} reps at {goal['target_weight']}kg")

        print("\n\n✅ All client programs have been updated with new weekly goals.")
