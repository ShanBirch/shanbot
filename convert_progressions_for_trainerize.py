#!/usr/bin/env python3
"""
Convert fresh progressions to Trainerize update format
"""

import json


def main():
    # Load fresh progressions
    with open('fresh_progressions.json', 'r') as f:
        fresh_data = json.load(f)

    # Convert to Trainerize format
    trainerize_format = {}

    for client_key, exercises in fresh_data.items():
        client_name = client_key.replace('_', ' ').title()
        trainerize_format[client_name] = {}

        # Group exercises by workout type (we'll put them all in "Weight Training" for now)
        workout_name = "Weight Training"
        trainerize_format[client_name][workout_name] = []

        for exercise_name, decisions in exercises.items():
            if decisions:  # Should have at least one decision
                decision = decisions[0]  # Take the first decision

                # Create the action for Trainerize
                action = {
                    "action": "modify_goals",
                    "exercise_name": exercise_name,
                    "weight": str(decision['recommended_weight']),
                    "reps": str(decision['recommended_reps'])
                }

                trainerize_format[client_name][workout_name].append(action)

    # Save in the format expected by update_with_conservative_progressions.py
    with open('trainerize_progressions.json', 'w') as f:
        json.dump(trainerize_format, f, indent=2)

    # Show summary
    total_clients = len(trainerize_format)
    total_exercises = sum(len(workouts[list(workouts.keys())[0]])
                          for workouts in trainerize_format.values())

    print(f"✅ Converted progressions for Trainerize update:")
    print(f"   📊 {total_clients} clients")
    print(f"   🏋️ {total_exercises} exercises")
    print(f"   💾 Saved to: trainerize_progressions.json")

    print(f"\n👥 Clients ready for update:")
    for client_name, workouts in trainerize_format.items():
        exercise_count = len(workouts[list(workouts.keys())[0]])
        print(f"   • {client_name}: {exercise_count} exercises")


if __name__ == "__main__":
    main()
