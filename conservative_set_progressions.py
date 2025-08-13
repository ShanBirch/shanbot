#!/usr/bin/env python3
"""
Conservative Set-by-Set Progression System
- Skips HIIT workouts entirely  
- Gradual warm-up set progression
- Conservative work set progression (only 1-2 main sets progress)
- Formats goals for Trainerize reps field
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta


def is_hiit_workout(workout_name):
    """Identify HIIT workouts that should be skipped"""
    hiit_keywords = [
        'hiit', 'cardio', 'conditioning', 'circuit', 'metcon',
        'metabolic', 'interval', 'tabata', 'emom', 'amrap'
    ]

    workout_lower = workout_name.lower()
    return any(keyword in workout_lower for keyword in hiit_keywords)


def get_exercise_type(exercise_name):
    """Determine exercise type for progression increments"""
    exercise_lower = exercise_name.lower()

    # Dumbbell exercises
    if any(keyword in exercise_lower for keyword in ['dumbbell', 'db', 'dumbell', 'hammer curls', 'bicep curl']):
        return 'dumbbell'

    # Barbell exercises
    if any(keyword in exercise_lower for keyword in ['barbell', 'bb', 'bench press', 'squat', 'deadlift']):
        return 'barbell'

    # Cable exercises
    if any(keyword in exercise_lower for keyword in ['cable', 'lat pull', 'seated row', 'tricep pushdown']):
        return 'cable'

    # Machine exercises
    if any(keyword in exercise_lower for keyword in ['machine', 'leg press', 'leg extension', 'seated']):
        return 'machine'

    # Bodyweight exercises
    if any(keyword in exercise_lower for keyword in ['chin up', 'pull up', 'push up', 'plank', 'hanging']):
        return 'bodyweight'

    return 'dumbbell'  # Default


def round_to_available_weight(weight, exercise_type):
    """Round weight to realistic gym equipment increments"""
    if exercise_type == 'dumbbell':
        return round(weight / 2.5) * 2.5
    elif exercise_type == 'barbell':
        return round(weight / 2.5) * 2.5
    elif exercise_type == 'cable':
        if weight <= 20:
            return round(weight / 2.5) * 2.5
        else:
            return round(weight / 5) * 5
    elif exercise_type == 'machine':
        return round(weight / 5) * 5
    elif exercise_type == 'bodyweight':
        return round(weight / 2.5) * 2.5
    else:
        return round(weight / 2.5) * 2.5


def format_set_goals_for_trainerize(current_weight, current_reps, exercise_name):
    """Generate and format conservative set goals for the Trainerize reps field"""

    exercise_type = get_exercise_type(exercise_name)
    weight = float(current_weight)
    reps = int(current_reps)

    # Calculate increments based on exercise type
    if exercise_type == 'dumbbell':
        increment = 1.25 if weight < 10 else 2.5
        warmup_multiplier = 0.7
    elif exercise_type == 'barbell':
        increment = 2.5 if weight < 40 else 5.0 if weight < 80 else 2.5
        warmup_multiplier = 0.75
    elif exercise_type == 'cable':
        increment = 2.5 if weight < 50 else 5.0
        warmup_multiplier = 0.7
    elif exercise_type == 'machine':
        increment = 5.0
        warmup_multiplier = 0.8
    elif exercise_type == 'bodyweight':
        increment = 2.5
        warmup_multiplier = 1.0  # Bodyweight stays same for warm-up
    else:
        increment = 2.5
        warmup_multiplier = 0.7

    # Calculate weights
    work_weight = round_to_available_weight(weight + increment, exercise_type)
    warmup_weight = round_to_available_weight(
        weight * warmup_multiplier, exercise_type)

    # Handle bodyweight exercises
    if weight == 0:  # Bodyweight
        warmup_weight = 0
        work_weight = round_to_available_weight(increment, exercise_type)

    # Format weight display
    def format_weight(w):
        if w == 0:
            return "BW"
        elif w == int(w):
            return f"{int(w)}kg"
        else:
            return f"{w}kg"

    # Create conservative 3-set progression
    set_goals = [
        # Warm-up (gradual increase)
        f"S1: {format_weight(warmup_weight)}x{reps}↗",
        # Work set (main progression)
        f"S2: {format_weight(work_weight)}x{reps}💪",
        f"S3: {format_weight(work_weight)}x{reps}💪"    # Work set (same as S2)
    ]

    return " | ".join(set_goals)


def create_conservative_progressions():
    """Create conservative set-by-set progressions for weight training only"""

    print("=== CREATING CONSERVATIVE SET-BY-SET PROGRESSIONS ===")
    print("🎯 Skipping HIIT workouts, focusing on weight training")
    print("📋 Conservative approach: warm-up progression + 2 work sets")

    # Load current progression data
    try:
        with open('smart_progressions.json', 'r') as f:
            current_data = json.load(f)
    except FileNotFoundError:
        print("❌ No smart_progressions.json found. Run smart_weight_progression.py first.")
        return

    conservative_progressions = {}
    skipped_hiit_count = 0
    total_processed_workouts = 0

    for client_name, workouts in current_data.items():
        print(f"\n📋 {client_name}:")
        conservative_progressions[client_name] = {}

        for workout_name, exercises in workouts.items():
            # Skip HIIT workouts
            if is_hiit_workout(workout_name):
                print(f"  ⏭️  Skipping HIIT workout: {workout_name}")
                skipped_hiit_count += 1
                continue

            print(f"  💪 Processing: {workout_name}")
            conservative_progressions[client_name][workout_name] = []
            total_processed_workouts += 1

            for exercise in exercises:
                exercise_name = exercise.get('exercise_name', '')
                current_weight = exercise.get('weight', '0')
                current_reps = exercise.get('reps', '0')

                # Generate conservative set goals formatted for Trainerize
                formatted_goals = format_set_goals_for_trainerize(
                    current_weight, current_reps, exercise_name
                )

                conservative_progressions[client_name][workout_name].append({
                    "action": "modify_goals",
                    "exercise_name": exercise_name,
                    "weight": current_weight,  # Keep for compatibility
                    "reps": formatted_goals,   # Set-by-set goals here
                })

                # Show sample (truncate long exercise names for display)
                display_name = exercise_name[:25] + \
                    "..." if len(exercise_name) > 25 else exercise_name
                print(f"    • {display_name}: {formatted_goals}")

    # Save conservative progressions
    with open('conservative_set_progressions.json', 'w') as f:
        json.dump(conservative_progressions, f, indent=2)

    print(f"\n💾 Saved conservative set progressions")
    print("📁 File: conservative_set_progressions.json")

    # Show summary
    total_exercises = sum(
        len(exercises)
        for workouts in conservative_progressions.values()
        for exercises in workouts.values()
    )

    print(f"\n🎯 SUMMARY:")
    print(f"  • {len(conservative_progressions)} clients")
    print(f"  • {total_processed_workouts} weight training workouts")
    print(f"  • {total_exercises} exercises with conservative set goals")
    print(f"  • {skipped_hiit_count} HIIT workouts skipped")
    print(f"\n💡 Each exercise has:")
    print(f"  • S1: Warm-up weight (gradual increase) ↗")
    print(f"  • S2: Work weight (main progression) 💪")
    print(f"  • S3: Work weight (same as S2) 💪")


if __name__ == "__main__":
    create_conservative_progressions()
