#!/usr/bin/env python3
"""
Connect Real SQLite Data to Progressive Overload AI
Test the system with actual workout data
"""

import sqlite3
import json
from datetime import datetime
from progressive_overload_ai import ProgressiveOverloadAI, ExercisePerformance, WorkoutSet


def load_real_workout_data(client_name_key, limit=10):
    """Load real workout data from SQLite database"""

    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get workout sessions for specific client
    query = """
    SELECT workout_date, week_identifier, workout_name, exercises_json, created_at
    FROM client_workout_sessions 
    WHERE client_name_key = ?
    ORDER BY workout_date ASC
    LIMIT ?
    """

    cursor.execute(query, (client_name_key, limit))
    sessions = cursor.fetchall()

    print(f"🏋️ Found {len(sessions)} workout sessions for {client_name_key}")

    # Convert to the format expected by Progressive Overload AI
    workout_data = []

    for session in sessions:
        workout_date, week_id, workout_name, exercises_json, created_at = session

        try:
            exercises = json.loads(exercises_json)

            # Convert string date to datetime object
            if isinstance(workout_date, str):
                workout_date_obj = datetime.strptime(workout_date, '%Y-%m-%d')
            else:
                workout_date_obj = workout_date

            # Create workout session data
            session_data = {
                'date': workout_date_obj,  # Now using datetime object
                'workout_type': workout_name,
                'exercises': []
            }

            # Process each exercise
            for exercise in exercises:
                if exercise.get('sets'):  # Only include exercises with actual set data
                    exercise_data = {
                        'name': exercise['name'],
                        'sets': exercise['sets']
                    }
                    session_data['exercises'].append(exercise_data)

            # Only add session if it has exercises with data
            if session_data['exercises']:
                workout_data.append(session_data)
                print(
                    f"  ✅ {workout_date}: {workout_name} - {len(session_data['exercises'])} exercises")
            else:
                print(
                    f"  ⚠️  {workout_date}: {workout_name} - No exercise data")

        except json.JSONDecodeError as e:
            print(f"  ❌ Error parsing JSON for {workout_date}: {e}")
        except ValueError as e:
            print(f"  ❌ Error parsing date {workout_date}: {e}")

    conn.close()
    return workout_data


def process_workout_data_directly(workout_data):
    """Process workout data directly into ExercisePerformance objects"""

    performances = []

    for session in workout_data:
        session_date = session['date']
        workout_type = session['workout_type']

        for exercise in session['exercises']:
            exercise_name = exercise['name']
            sets_data = exercise['sets']

            # Create WorkoutSet objects for this exercise
            workout_sets = []
            for set_data in sets_data:
                try:
                    workout_set = WorkoutSet(
                        weight=float(set_data.get('weight', 0)),
                        reps=int(set_data.get('reps', 0)),
                        rpe=set_data.get('rpe'),  # Optional
                        completed=True  # Assume completed if data exists
                    )
                    workout_sets.append(workout_set)
                except (ValueError, TypeError) as e:
                    print(
                        f"  ⚠️ Error processing set data for {exercise_name}: {e}")
                    continue

            # Create ExercisePerformance object if we have valid sets
            if workout_sets:
                try:
                    performance = ExercisePerformance(
                        exercise_name=exercise_name,
                        sets=workout_sets,
                        date=session_date,
                        workout_type=workout_type
                    )
                    performances.append(performance)
                except Exception as e:
                    print(
                        f"  ⚠️ Error creating ExercisePerformance for {exercise_name}: {e}")
                    continue

    return performances


def test_progressive_overload_with_real_data():
    """Test the Progressive Overload AI with real database data"""

    print("🧠 TESTING PROGRESSIVE OVERLOAD AI WITH REAL DATA")
    print("=" * 60)

    # Initialize the AI system
    ai = ProgressiveOverloadAI()

    # Load real data for Rebecca D'Angelo
    client_name = "rebecca_dangelo"
    workout_data = load_real_workout_data(client_name, limit=20)

    if not workout_data:
        print("❌ No workout data found!")
        return

    print(f"\n📊 Processing {len(workout_data)} workout sessions...")

    # Process the workout data directly into ExercisePerformance objects
    performances = process_workout_data_directly(workout_data)

    print(f"✅ Processed {len(performances)} exercise performances")

    if not performances:
        print("❌ No valid exercise performances found!")
        return

    # Show sample performances
    print(f"\n📋 Sample performances:")
    for i, perf in enumerate(performances[:5]):
        # Get the first set for display
        first_set = perf.sets[0] if perf.sets else None
        if first_set:
            print(f"  {i+1}. {perf.exercise_name}: {first_set.weight}kg x {first_set.reps} reps ({len(perf.sets)} sets) on {perf.date.strftime('%Y-%m-%d')}")
        else:
            print(
                f"  {i+1}. {perf.exercise_name}: No sets data on {perf.date.strftime('%Y-%m-%d')}")

    # Analyze progressions
    print("\n🔍 ANALYZING PROGRESSIONS...")
    progressions = ai.analyze_progression_patterns(performances)

    if progressions:
        print(
            f"🎯 Found progression recommendations for {len(progressions)} exercises:")

        for exercise_name, decisions in progressions.items():
            decision = decisions[0]
            print(f"\n💪 **{exercise_name}**")
            print(
                f"   Current: {decision.current_weight}kg x {decision.current_reps}")
            print(
                f"   Recommended: {decision.recommended_weight}kg x {decision.recommended_reps}")
            print(f"   Action: {decision.action_type.upper()}")
            print(f"   Confidence: {decision.confidence:.1%}")
            print(f"   Reason: {decision.reason}")

        # Generate and save report
        print("\n📝 GENERATING REPORT...")
        report = ai.generate_progression_report(client_name, progressions)

        # Save report to file
        report_filename = f"progression_report_{client_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"💾 Report saved to: {report_filename}")

        # Save progression history
        ai.save_progression_history(client_name, progressions)
        print("💾 Progression history updated")

    else:
        print("⚠️ No progressions recommended (need more data)")

    print("\n✅ Progressive Overload AI testing complete!")


def show_available_clients():
    """Show all available clients in the database"""

    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    query = """
    SELECT client_name_key, COUNT(*) as session_count, 
           MIN(workout_date) as first_workout, 
           MAX(workout_date) as last_workout
    FROM client_workout_sessions 
    GROUP BY client_name_key
    ORDER BY session_count DESC
    """

    cursor.execute(query)
    clients = cursor.fetchall()

    print("👥 AVAILABLE CLIENTS:")
    print("-" * 60)

    for client_name, session_count, first_workout, last_workout in clients:
        print(f"• {client_name}")
        print(f"  Sessions: {session_count}")
        print(f"  Period: {first_workout} to {last_workout}")
        print()

    conn.close()


if __name__ == "__main__":
    print("🗄️ PROGRESSIVE OVERLOAD AI - REAL DATA CONNECTOR")
    print("=" * 60)

    # Show available clients
    show_available_clients()

    # Test with real data
    test_progressive_overload_with_real_data()
