#!/usr/bin/env python3
"""
Smart weight progression system that understands gym equipment
Makes realistic weight increases based on exercise type
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from weekly_program_updater import TrainerizeAutomation


def get_exercise_type(exercise_name):
    """Determine exercise type based on name"""
    exercise_lower = exercise_name.lower()

    # Dumbbell exercises
    dumbbell_keywords = ['dumbbell', 'db', 'dumbell',
                         'arnold', 'hammer curls', 'bicep curl', 'chest fly']
    if any(keyword in exercise_lower for keyword in dumbbell_keywords):
        return 'dumbbell'

    # Barbell exercises
    barbell_keywords = ['barbell', 'bb',
                        'bench press', 'squat', 'deadlift', 'row']
    if any(keyword in exercise_lower for keyword in barbell_keywords):
        return 'barbell'

    # Cable exercises
    cable_keywords = ['cable', 'lat pull',
                      'seated row', 'tricep pushdown', 'face pull']
    if any(keyword in exercise_lower for keyword in cable_keywords):
        return 'cable'

    # Machine exercises
    machine_keywords = ['machine', 'leg press',
                        'leg extension', 'leg curl', 'seated']
    if any(keyword in exercise_lower for keyword in machine_keywords):
        return 'machine'

    # Bodyweight exercises
    bodyweight_keywords = ['chin up', 'pull up', 'push up', 'plank', 'hanging']
    if any(keyword in exercise_lower for keyword in bodyweight_keywords):
        return 'bodyweight'

    # Default to dumbbell for unknown exercises
    return 'dumbbell'


def round_to_available_weight(weight, exercise_type):
    """Round weight to realistic gym equipment increments"""

    if exercise_type == 'dumbbell':
        # Dumbbell increments: 2.5kg steps
        # Available: 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, etc.
        return round(weight / 2.5) * 2.5

    elif exercise_type == 'barbell':
        # Barbell increments: 2.5kg steps (1.25kg plates each side)
        return round(weight / 2.5) * 2.5

    elif exercise_type == 'cable':
        # Cable machines: usually 5kg increments, some 2.5kg
        if weight <= 20:
            # Smaller increments for lighter weights
            return round(weight / 2.5) * 2.5
        else:
            return round(weight / 5) * 5     # 5kg increments for heavier

    elif exercise_type == 'machine':
        # Machine increments: usually 5kg steps
        return round(weight / 5) * 5

    elif exercise_type == 'bodyweight':
        # Bodyweight with added weight: 2.5kg increments
        return round(weight / 2.5) * 2.5

    else:
        # Default: 2.5kg increments
        return round(weight / 2.5) * 2.5


def smart_weight_progression(current_weight, current_reps, exercise_name):
    """Calculate smart weight progression based on exercise type and performance"""

    exercise_type = get_exercise_type(exercise_name)
    current_weight = float(current_weight)
    current_reps = int(current_reps)

    # Determine increment based on exercise type and current weight
    if exercise_type == 'dumbbell':
        if current_weight < 10:
            increment = 1.25  # Smaller increments for light weights
        else:
            increment = 2.5

    elif exercise_type == 'barbell':
        if current_weight < 40:
            increment = 2.5
        elif current_weight < 80:
            increment = 5.0   # Bigger jumps for intermediate weights
        else:
            increment = 2.5   # Smaller increments for heavy weights

    elif exercise_type == 'cable':
        increment = 2.5 if current_weight < 50 else 5.0

    elif exercise_type == 'machine':
        increment = 5.0

    elif exercise_type == 'bodyweight':
        if current_weight == 0:
            increment = 2.5   # Start with assistance or added weight
        else:
            increment = 2.5

    else:
        increment = 2.5

    # Calculate new weight
    new_weight = current_weight + increment

    # Round to available equipment
    new_weight = round_to_available_weight(new_weight, exercise_type)

    # Calculate new reps (slight increase, capped appropriately)
    if current_reps < 6:
        new_reps = current_reps + 1   # Lower rep ranges - add 1
    elif current_reps < 12:
        new_reps = current_reps + 1   # Mid rep ranges - add 1
    else:
        new_reps = min(current_reps + 1, 15)  # Higher reps - cap at 15

    return str(new_weight), str(new_reps), exercise_type


def create_smart_progression_data():
    """Create progression data with smart weight increases"""
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        print("=== CREATING SMART PROGRESSION DATA ===")

        # Get all clients with recent workouts
        recent_date = (datetime.now() - timedelta(days=14)
                       ).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT DISTINCT client_name_key, COUNT(*) as workout_count
            FROM client_workout_sessions 
            WHERE workout_date >= ?
            GROUP BY client_name_key
            ORDER BY workout_count DESC
        """, (recent_date,))

        clients = cursor.fetchall()
        print(f"Found {len(clients)} clients with recent workouts")

        all_progressions = {}

        for client_key, _ in clients:
            if client_key == 'kelly_smith':  # Skip inactive clients
                continue

            display_name = ' '.join(word.capitalize()
                                    for word in client_key.split('_'))

            # Get client's recent workouts
            cursor.execute("""
                SELECT workout_date, workout_name, exercises_json 
                FROM client_workout_sessions 
                WHERE client_name_key = ? AND workout_date >= ?
                ORDER BY workout_date DESC 
                LIMIT 10
            """, (client_key, recent_date))

            workouts = cursor.fetchall()

            if not workouts:
                continue

            print(f"\n📋 {display_name}:")
            workout_progressions = {}

            for date, workout_name, exercises_json in workouts:
                if workout_name not in workout_progressions:
                    exercises = json.loads(exercises_json)

                    workout_progressions[workout_name] = []

                    for exercise in exercises:
                        exercise_name = exercise.get('name', 'Unknown')
                        sets = exercise.get('sets', [])

                        if sets and len(sets) > 0:
                            # Get the best set
                            best_set = max(sets, key=lambda s: (
                                float(s.get('weight', 0)), int(s.get('reps', 0))))

                            weight = best_set.get('weight', 0)
                            reps = best_set.get('reps', 0)

                            if (weight and float(weight) > 0) or (reps and int(reps) > 0):
                                # Use smart progression
                                new_weight, new_reps, exercise_type = smart_weight_progression(
                                    weight, reps, exercise_name)

                                print(f"  {exercise_name} ({exercise_type}):")
                                print(
                                    f"    {weight}kg x {reps} → {new_weight}kg x {new_reps}")

                                workout_progressions[workout_name].append({
                                    "action": "modify_goals",
                                    "exercise_name": exercise_name,
                                    "weight": new_weight,
                                    "reps": new_reps
                                })

            if workout_progressions:
                all_progressions[display_name] = workout_progressions

        conn.close()

        # Save the smart progression data
        with open('smart_progressions.json', 'w') as f:
            json.dump(all_progressions, f, indent=2)

        print(
            f"\n💾 Saved smart progression data for {len(all_progressions)} clients")

        return all_progressions

    except Exception as e:
        print(f"Error creating smart progressions: {e}")
        return {}


def test_smart_progressions():
    """Test the smart progression system"""

    print("=== TESTING SMART PROGRESSIONS ===")

    # Test cases
    test_exercises = [
        ("Dumbbell Bicep Curl", "10", "10"),
        ("Barbell Bench Press", "60", "6"),
        ("Cable Lat Pulldown", "45", "8"),
        ("Leg Press Machine", "100", "12"),
        ("Wide Grip Chin Up", "0", "8")
    ]

    for exercise_name, weight, reps in test_exercises:
        new_weight, new_reps, exercise_type = smart_weight_progression(
            weight, reps, exercise_name)
        print(
            f"{exercise_name} ({exercise_type}): {weight}kg x {reps} → {new_weight}kg x {new_reps}")


if __name__ == "__main__":
    # Test the smart progression system
    test_smart_progressions()

    print("\n" + "="*50 + "\n")

    # Create smart progression data
    create_smart_progression_data()
