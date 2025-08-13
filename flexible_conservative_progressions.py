#!/usr/bin/env python3
"""
Flexible Conservative Set-by-Set Progression System
- Handles variable set counts (3, 4, 5+ sets)
- Skips HIIT workouts entirely  
- Conservative progression based on actual set structure
"""

import json
from collections import defaultdict
from datetime import datetime


def save_to_progression_history(trainerize_progressions):
    """Save flexible progressions to progression_history.json for weekly tracking"""
    history_path = "progression_history.json"

    try:
        # Load existing history
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = {}

        # Convert our flexible progressions to progression history format
        current_time = datetime.now().isoformat()

        for client_name, workouts in trainerize_progressions.items():
            if client_name not in history:
                history[client_name] = []

            # Create entry for this client
            entry = {
                "date": current_time,
                "progressions": {}
            }

            # Extract exercise data from all workouts
            for workout_name, exercises in workouts.items():
                for exercise_data in exercises:
                    exercise_name = exercise_data.get('exercise_name', '')
                    weight = float(exercise_data.get('weight', 0))
                    reps_goals = exercise_data.get('reps', '')

                    # Parse the flexible goals to extract target info
                    if ' | ' in reps_goals:
                        # Extract work set info (S2 typically)
                        work_sets = [s for s in reps_goals.split(
                            ' | ') if 'S2:' in s or 'S3:' in s]
                        if work_sets:
                            work_set = work_sets[0]
                            # Extract weight and reps from format like "S2: 15kgx11"
                            if 'x' in work_set:
                                weight_part = work_set.split(
                                    ':')[1].strip().split('x')[0]
                                reps_part = work_set.split('x')[1]
                                try:
                                    target_weight = float(weight_part.replace(
                                        'kg', '').replace('BW', '0'))
                                    target_reps = reps_part
                                except:
                                    target_weight = weight
                                    target_reps = "10-12"
                            else:
                                target_weight = weight
                                target_reps = "10-12"
                        else:
                            target_weight = weight
                            target_reps = "10-12"
                    else:
                        target_weight = weight
                        target_reps = "10-12"

                    entry["progressions"][exercise_name] = {
                        "current_weight": weight,
                        "recommended_weight": target_weight,
                        "current_reps": target_reps,
                        "recommended_reps": reps_goals,
                        "reason": "Flexible conservative progression with set-by-set goals",
                        "confidence": 0.85,
                        "action_type": "flexible_progression"
                    }

            # Only add entry if there are progressions
            if entry["progressions"]:
                history[client_name].append(entry)

        # Save updated history
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)

    except Exception as e:
        print(f"⚠️  Warning: Could not save to progression history: {e}")


def is_hiit_workout(workout_name):
    """Identify HIIT workouts that should be skipped"""
    hiit_keywords = ['hiit', 'cardio', 'conditioning', 'circuit', 'metcon']
    return any(keyword in workout_name.lower() for keyword in hiit_keywords)


def get_exercise_type(exercise_name):
    """Determine exercise type for progression increments"""
    exercise_lower = exercise_name.lower()
    if any(keyword in exercise_lower for keyword in ['dumbbell', 'db', 'dumbell', 'hammer curls', 'bicep curl']):
        return 'dumbbell'
    elif any(keyword in exercise_lower for keyword in ['barbell', 'bb', 'bench press', 'squat', 'deadlift']):
        return 'barbell'
    elif any(keyword in exercise_lower for keyword in ['cable', 'lat pull', 'seated row', 'tricep pushdown']):
        return 'cable'
    elif any(keyword in exercise_lower for keyword in ['machine', 'leg press', 'leg extension', 'seated']):
        return 'machine'
    elif any(keyword in exercise_lower for keyword in ['chin up', 'pull up', 'push up', 'plank', 'hanging']):
        return 'bodyweight'
    return 'dumbbell'


def round_to_available_weight(weight, exercise_type):
    """Round weight to realistic gym equipment increments"""
    if exercise_type == 'dumbbell':
        return round(weight / 2.5) * 2.5
    elif exercise_type == 'barbell':
        return round(weight / 2.5) * 2.5
    elif exercise_type == 'cable':
        return round(weight / 2.5) * 2.5 if weight <= 20 else round(weight / 5) * 5
    elif exercise_type == 'machine':
        return round(weight / 5) * 5
    else:
        return round(weight / 2.5) * 2.5


def analyze_exercise_sets(exercise_data):
    """Analyze the set structure for an exercise"""
    sets_by_exercise = defaultdict(list)

    for item in exercise_data:
        exercise_name = item.get('exercise_name', '')
        set_number = item.get('set_number', 1)
        weight = float(item.get('weight', 0))
        reps = int(item.get('reps', 0))

        sets_by_exercise[exercise_name].append({
            'set_number': set_number,
            'weight': weight,
            'reps': reps
        })

    # Sort sets by set number for each exercise
    for exercise_name in sets_by_exercise:
        sets_by_exercise[exercise_name].sort(key=lambda x: x['set_number'])

    return dict(sets_by_exercise)


def create_conservative_set_progression(sets_data, exercise_name):
    """Create conservative progression for variable set counts"""

    exercise_type = get_exercise_type(exercise_name)
    num_sets = len(sets_data)

    # Calculate conservative increments
    increments = {
        'dumbbell': 1.25, 'barbell': 2.5, 'cable': 2.5,
        'machine': 5.0, 'bodyweight': 2.5
    }
    warmup_multipliers = {
        'dumbbell': 0.7, 'barbell': 0.75, 'cable': 0.7,
        'machine': 0.8, 'bodyweight': 1.0
    }

    increment = increments.get(exercise_type, 2.5)
    warmup_multiplier = warmup_multipliers.get(exercise_type, 0.7)

    set_goals = []

    for i, set_data in enumerate(sets_data):
        set_number = i + 1
        current_weight = set_data['weight']
        current_reps = set_data['reps']

        if set_number == 1:
            # First set: Conservative warm-up
            if current_weight == 0:
                new_weight = 0
            else:
                new_weight = round_to_available_weight(
                    current_weight * warmup_multiplier, exercise_type)
            goal_type = "warm-up"

        elif set_number <= 2 or (set_number <= 3 and num_sets <= 4):
            # Main work sets: Progressive overload
            new_weight = round_to_available_weight(
                current_weight + increment, exercise_type)
            goal_type = "work"

        else:
            # Later sets: Maintain weight for volume
            new_weight = current_weight
            goal_type = "volume"

        # Handle bodyweight exercises
        if current_weight == 0 and goal_type == "work":
            new_weight = round_to_available_weight(increment, exercise_type)

        # Format weight display
        if new_weight == 0:
            weight_str = "BW"
        elif new_weight == int(new_weight):
            weight_str = f"{int(new_weight)}kg"
        else:
            weight_str = f"{new_weight}kg"

        # Clean format without indicators
        type_indicator = ""

        set_goals.append(
            f"S{set_number}: {weight_str}x{current_reps}{type_indicator}")

    return " | ".join(set_goals)


def create_flexible_conservative_progressions():
    """Create conservative progressions that adapt to actual set counts"""

    print("=" * 70)
    print("🎯 CREATING FLEXIBLE CONSERVATIVE SET-BY-SET PROGRESSIONS")
    print("=" * 70)
    print("📋 Adapts to actual set counts (3, 4, 5+ sets)")

    # Load original progression data
    try:
        with open('smart_progressions.json', 'r') as f:
            original_data = json.load(f)
    except FileNotFoundError:
        print("❌ No smart_progressions.json found. Run smart_weight_progression.py first.")
        return

    flexible_progressions = {}
    skipped_hiit_count = 0
    total_processed_workouts = 0
    total_exercises = 0

    for client_name, workouts in original_data.items():
        print(f"\n📋 {client_name}:")
        flexible_progressions[client_name] = {}

        for workout_name, exercise_data in workouts.items():
            # Skip HIIT workouts
            if is_hiit_workout(workout_name):
                print(f"  ⏭️  Skipping HIIT workout: {workout_name}")
                skipped_hiit_count += 1
                continue

            print(f"  -> Processing: {workout_name}")

            # Analyze set structure for this workout
            exercises_by_name = analyze_exercise_sets(exercise_data)

            flexible_progressions[client_name][workout_name] = []
            total_processed_workouts += 1

            for exercise_name, sets_data in exercises_by_name.items():
                num_sets = len(sets_data)

                # Generate flexible conservative progression
                formatted_goals = create_conservative_set_progression(
                    sets_data, exercise_name)

                # Get representative weight/reps for compatibility
                rep_weight = sets_data[0]['weight'] if sets_data else 0

                flexible_progressions[client_name][workout_name].append({
                    "action": "modify_goals",
                    "exercise_name": exercise_name,
                    "weight": str(rep_weight),
                    "reps": formatted_goals,
                    "num_sets": num_sets
                })

                total_exercises += 1

                # Show sample
                display_name = exercise_name[:25] + \
                    "..." if len(exercise_name) > 25 else exercise_name
                print(
                    f"    • {display_name} ({num_sets} sets): {formatted_goals}")

    # Save flexible conservative progressions
    with open('flexible_conservative_progressions.json', 'w') as f:
        json.dump(flexible_progressions, f, indent=2)

    print(f"\n💾 Saved flexible conservative progressions")
    print("📁 File: flexible_conservative_progressions.json")

    # Also save to progression history for weekly analysis tracking
    save_to_progression_history(flexible_progressions)
    print("📈 Saved to progression history for weekly tracking")

    print(f"\n🎯 SUMMARY:")
    print(f"  • {len(flexible_progressions)} clients")
    print(f"  • {total_processed_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with flexible set goals")
    print(f"  • {skipped_hiit_count} HIIT workouts skipped")
    print(f"\n💡 Flexible progression structure:")
    print(f"  • S1: Conservative warm-up (w)")
    print(f"  • S2-S3: Progressive work sets (W)")
    print(f"  • S4+: Volume maintenance sets (v)")


if __name__ == "__main__":
    create_flexible_conservative_progressions()
