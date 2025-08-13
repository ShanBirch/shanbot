#!/usr/bin/env python3
"""
Check Alice Forster's workout progression analysis
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
    print("✅ Successfully imported SQLite utilities")
except ImportError as e:
    print(f"❌ Error importing SQLite utilities: {e}")
    sys.exit(1)


def analyze_alice_progress():
    """Analyze Alice's recent workout progress"""

    print('🏋️ ALICE FORSTER - WORKOUT PROGRESSION ANALYSIS')
    print('=' * 65)

    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate date ranges
    today = datetime.now()
    current_week_start = (
        today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    last_week_start = (
        today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
    last_week_end = (today - timedelta(days=today.weekday() + 1)
                     ).strftime('%Y-%m-%d')

    print(f'📅 Current Week Start: {current_week_start}')
    print(f'📅 Last Week: {last_week_start} to {last_week_end}')
    print()

    # 1. Get all Alice's recent workout sessions
    print('📊 RECENT WORKOUT SESSIONS:')
    print('-' * 40)

    cursor.execute('''
        SELECT workout_date, workout_name, total_reps, total_sets, total_weight_lifted
        FROM client_workout_sessions 
        WHERE client_name_key = ? 
        ORDER BY workout_date DESC
        LIMIT 15
    ''', ('alice_forster',))

    sessions = cursor.fetchall()

    if sessions:
        last_week_sessions = []
        total_sessions = len(sessions)

        for session in sessions:
            workout_date, workout_name, total_reps, total_sets, total_weight = session
            session_date = datetime.strptime(workout_date, '%Y-%m-%d')

            # Mark if it's from last week
            is_last_week = last_week_start <= workout_date <= last_week_end
            week_marker = " ⭐ LAST WEEK" if is_last_week else ""

            print(f'📅 {workout_date} - {workout_name}')
            print(
                f'   💪 {total_sets} sets | {total_reps} reps | {total_weight:.1f}kg total{week_marker}')

            if is_last_week:
                last_week_sessions.append(session)
            print()

        print(
            f'🎯 LAST WEEK SUMMARY: {len(last_week_sessions)} workout sessions')
        if last_week_sessions:
            total_last_week_volume = sum(s[4] for s in last_week_sessions)
            total_last_week_reps = sum(s[2] for s in last_week_sessions)
            total_last_week_sets = sum(s[3] for s in last_week_sessions)

            print(f'   📈 Total Volume: {total_last_week_volume:.1f}kg')
            print(f'   📈 Total Reps: {total_last_week_reps}')
            print(f'   📈 Total Sets: {total_last_week_sets}')
        print()

    # 2. Get exercise-level details for last week
    print('🎯 LAST WEEK EXERCISE BREAKDOWN:')
    print('-' * 45)

    cursor.execute('''
        SELECT workout_date, exercise_name, total_reps, total_sets, max_weight, 
               average_weight, total_volume
        FROM exercise_sessions 
        WHERE client_name_key = ? 
        AND workout_date BETWEEN ? AND ?
        ORDER BY workout_date DESC, total_volume DESC
    ''', ('alice_forster', last_week_start, last_week_end))

    exercises = cursor.fetchall()

    if exercises:
        print(f'Found {len(exercises)} exercise performances:')
        print()

        # Group by exercise name for analysis
        exercise_summary = {}
        for exercise in exercises:
            workout_date, exercise_name, total_reps, total_sets, max_weight, avg_weight, total_volume = exercise

            if exercise_name not in exercise_summary:
                exercise_summary[exercise_name] = {
                    'sessions': 0,
                    'total_reps': 0,
                    'total_sets': 0,
                    'max_weight': 0,
                    'total_volume': 0,
                    'dates': []
                }

            exercise_summary[exercise_name]['sessions'] += 1
            exercise_summary[exercise_name]['total_reps'] += total_reps
            exercise_summary[exercise_name]['total_sets'] += total_sets
            exercise_summary[exercise_name]['max_weight'] = max(
                exercise_summary[exercise_name]['max_weight'], max_weight)
            exercise_summary[exercise_name]['total_volume'] += total_volume
            exercise_summary[exercise_name]['dates'].append(workout_date)

            print(f'📅 {workout_date} - {exercise_name}')
            print(f'   💪 {total_sets} sets, {total_reps} reps')
            print(
                f'   ⚖️ Max: {max_weight}kg, Avg: {avg_weight:.1f}kg, Volume: {total_volume:.1f}kg')
            print()

        # Show summary by exercise
        print('📊 EXERCISE SUMMARY (Last Week):')
        print('-' * 35)
        for exercise_name, summary in sorted(exercise_summary.items(), key=lambda x: x[1]['total_volume'], reverse=True):
            print(f'🏋️ {exercise_name}')
            print(
                f'   📈 {summary["sessions"]} sessions, {summary["total_sets"]} sets, {summary["total_reps"]} reps')
            print(f'   💪 Max weight: {summary["max_weight"]}kg')
            print(f'   📊 Total volume: {summary["total_volume"]:.1f}kg')
            print()

    else:
        print('❌ No exercise data found for last week')

    conn.close()

    # 3. Compare with progression targets
    print('\n🎯 PROGRESSION TARGETS COMPARISON:')
    print('-' * 45)

    try:
        with open('weekly_progressions.json', 'r') as f:
            progressions = json.load(f)

        alice_progressions = progressions.get('alice_forster', {})

        if alice_progressions:
            print(
                f'Found progression targets for {len(alice_progressions)} workout categories:')
            print()

            for workout_category, exercises in alice_progressions.items():
                print(f'💪 {workout_category.upper()}:')
                for exercise_target in exercises:
                    exercise_name = exercise_target.get(
                        'exercise_name', 'Unknown')
                    target_weight = exercise_target.get('weight', 'N/A')
                    target_reps = exercise_target.get('reps', 'N/A')

                    print(f'   🎯 {exercise_name}')
                    print(
                        f'      Target: {target_weight}kg x {target_reps} reps')

                    # Try to match with actual performance
                    if exercises and exercise_name in exercise_summary:
                        actual = exercise_summary[exercise_name]
                        print(
                            f'      Actual: {actual["max_weight"]}kg max, {actual["total_reps"]} total reps')

                        # Simple comparison
                        try:
                            if target_weight != 'bodyweight' and target_weight != 'N/A':
                                target_weight_num = float(target_weight)
                                if actual["max_weight"] >= target_weight_num:
                                    print(f'      ✅ WEIGHT TARGET MET!')
                                else:
                                    difference = target_weight_num - \
                                        actual["max_weight"]
                                    print(
                                        f'      📈 {difference:.1f}kg to target')
                        except:
                            pass
                    else:
                        print(f'      ❓ No recent performance data')
                    print()
                print()
        else:
            print('❌ No progression targets found for Alice')

    except FileNotFoundError:
        print('❌ weekly_progressions.json file not found')
    except Exception as e:
        print(f'❌ Error loading progression data: {e}')


if __name__ == "__main__":
    analyze_alice_progress()
