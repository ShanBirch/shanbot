import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_workout_data():
    """Analyze the workout session data structure and create weekly summaries"""
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get all workout sessions with ig_username
    cursor.execute('''
        SELECT ig_username, workout_date, week_identifier, workout_name, exercises_json, client_name_key
        FROM client_workout_sessions 
        WHERE ig_username IS NOT NULL 
        ORDER BY ig_username, workout_date DESC
    ''')

    all_sessions = cursor.fetchall()
    print(f"Found {len(all_sessions)} workout sessions with ig_username")

    # Group by user and analyze
    user_workouts = defaultdict(list)
    for session in all_sessions:
        ig_username, workout_date, week_id, workout_name, exercises_json, client_name = session
        user_workouts[ig_username].append({
            'date': workout_date,
            'week': week_id,
            'name': workout_name,
            'exercises': exercises_json,
            'client_name': client_name
        })

    print(f"\nUsers with workout data: {len(user_workouts)}")
    for username in list(user_workouts.keys())[:5]:  # Show first 5 users
        print(f"  {username}: {len(user_workouts[username])} sessions")

    # Analyze a specific user's data in detail
    if user_workouts:
        sample_user = list(user_workouts.keys())[0]
        print(f"\n=== DETAILED ANALYSIS FOR: {sample_user} ===")

        user_sessions = user_workouts[sample_user]
        # Show first 2 sessions
        for i, session in enumerate(user_sessions[:2]):
            print(
                f"\n--- Session {i+1}: {session['date']} - {session['name']} ---")

            try:
                exercises = json.loads(session['exercises'])
                for exercise in exercises:
                    exercise_name = exercise.get('name', 'Unknown')
                    sets_data = exercise.get('sets', [])

                    if sets_data:  # Only show exercises with actual data
                        print(f"  {exercise_name}:")
                        for set_info in sets_data:
                            set_num = set_info.get('set', '?')
                            reps = set_info.get('reps', '?')
                            weight = set_info.get('weight', '?')
                            print(
                                f"    Set {set_num}: {reps} reps @ {weight}kg")
            except json.JSONDecodeError:
                print("    Error parsing exercises JSON")

    conn.close()


def get_current_week_workouts(ig_username):
    """Get current week's workout data for a specific user"""
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get current week identifier (ISO week format: YYYY-WXX)
    current_date = datetime.now()
    current_week = current_date.strftime('%Y-W%U')  # Year-Week format

    # Also check the previous week in case we're early in the week
    prev_week_date = current_date - timedelta(days=7)
    prev_week = prev_week_date.strftime('%Y-W%U')

    cursor.execute('''
        SELECT workout_date, week_identifier, workout_name, exercises_json
        FROM client_workout_sessions 
        WHERE ig_username = ? 
        AND (week_identifier = ? OR week_identifier = ?)
        ORDER BY workout_date DESC
    ''', (ig_username, current_week, prev_week))

    sessions = cursor.fetchall()
    conn.close()

    weekly_summary = {
        'total_sessions': len(sessions),
        'workouts': [],
        'exercise_progress': {},
        'week_identifier': current_week
    }

    for session in sessions:
        workout_date, week_id, workout_name, exercises_json = session

        try:
            exercises = json.loads(exercises_json)
            workout_data = {
                'date': workout_date,
                'name': workout_name,
                'exercises': []
            }

            for exercise in exercises:
                exercise_name = exercise.get('name', 'Unknown')
                sets_data = exercise.get('sets', [])

                if sets_data:  # Only include exercises with actual data
                    exercise_summary = {
                        'name': exercise_name,
                        'sets': len(sets_data),
                        'total_reps': sum(set_info.get('reps', 0) for set_info in sets_data),
                        'max_weight': max(set_info.get('weight', 0) for set_info in sets_data),
                        'avg_weight': sum(set_info.get('weight', 0) for set_info in sets_data) / len(sets_data),
                        'details': sets_data
                    }
                    workout_data['exercises'].append(exercise_summary)

                    # Track exercise progress
                    if exercise_name not in weekly_summary['exercise_progress']:
                        weekly_summary['exercise_progress'][exercise_name] = []

                    weekly_summary['exercise_progress'][exercise_name].append({
                        'date': workout_date,
                        'sets': len(sets_data),
                        'total_reps': exercise_summary['total_reps'],
                        'max_weight': exercise_summary['max_weight'],
                        'avg_weight': exercise_summary['avg_weight']
                    })

            weekly_summary['workouts'].append(workout_data)

        except json.JSONDecodeError:
            print(f"Error parsing exercises JSON for {workout_date}")

    return weekly_summary


def format_workout_summary_for_prompt(weekly_summary):
    """Format the weekly workout summary for use in AI prompts"""
    if not weekly_summary['workouts']:
        return "No workout data available for this week."

    summary_text = f"Weekly Workout Summary ({weekly_summary['week_identifier']}):\n"
    summary_text += f"Total Sessions: {weekly_summary['total_sessions']}\n\n"

    # List each workout session
    for i, workout in enumerate(weekly_summary['workouts'], 1):
        summary_text += f"Session {i} ({workout['date']}) - {workout['name']}:\n"

        for exercise in workout['exercises']:
            summary_text += f"  • {exercise['name']}: {exercise['sets']} sets, {exercise['total_reps']} total reps"
            if exercise['max_weight'] > 0:
                summary_text += f", max weight {exercise['max_weight']}kg"
            summary_text += "\n"
        summary_text += "\n"

    # Add progress insights
    progress_insights = []
    for exercise_name, sessions in weekly_summary['exercise_progress'].items():
        if len(sessions) > 1:
            # Compare first and last session for this exercise
            first_session = sessions[-1]  # Oldest (sessions are ordered DESC)
            last_session = sessions[0]   # Newest

            if last_session['max_weight'] > first_session['max_weight']:
                weight_increase = last_session['max_weight'] - \
                    first_session['max_weight']
                progress_insights.append(
                    f"Increased {exercise_name} weight by {weight_increase}kg")

            if last_session['total_reps'] > first_session['total_reps']:
                rep_increase = last_session['total_reps'] - \
                    first_session['total_reps']
                progress_insights.append(
                    f"Increased {exercise_name} total reps by {rep_increase}")

    if progress_insights:
        summary_text += "Progress This Week:\n"
        for insight in progress_insights:
            summary_text += f"  • {insight}\n"

    return summary_text


def test_workout_analysis():
    """Test the workout analysis functions"""
    print("=== TESTING WORKOUT ANALYSIS ===")

    # First run the general analysis
    analyze_workout_data()

    # Test with a specific user
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get a user with recent workout data
    cursor.execute('''
        SELECT DISTINCT ig_username 
        FROM client_workout_sessions 
        WHERE ig_username IS NOT NULL 
        AND workout_date >= date('now', '-14 days')
        LIMIT 1
    ''')

    result = cursor.fetchone()
    if result:
        test_user = result[0]
        print(f"\n=== TESTING WEEKLY SUMMARY FOR: {test_user} ===")

        weekly_data = get_current_week_workouts(test_user)
        formatted_summary = format_workout_summary_for_prompt(weekly_data)

        print("Raw weekly data:")
        print(json.dumps(weekly_data, indent=2, default=str))

        print("\nFormatted summary for AI prompt:")
        print(formatted_summary)
    else:
        print("No users with recent workout data found")

    conn.close()


if __name__ == "__main__":
    test_workout_analysis()
