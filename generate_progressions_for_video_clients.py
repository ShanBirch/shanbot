#!/usr/bin/env python3
"""
Generate progressions for clients who have videos
"""

import json
import os
from progressive_overload_ai import ProgressiveOverloadAI


def progression_to_dict(progression_decision):
    """Convert ProgressionDecision to dictionary"""
    return {
        'exercise_name': progression_decision.exercise_name,
        'current_weight': progression_decision.current_weight,
        'recommended_weight': progression_decision.recommended_weight,
        'current_reps': progression_decision.current_reps,
        'recommended_reps': progression_decision.recommended_reps,
        'reason': progression_decision.reason,
        'confidence': progression_decision.confidence,
        'action_type': progression_decision.action_type
    }


def main():
    # List of clients with videos
    clients = [
        'Alice Forster', 'Anna Somogyi', 'Claire Ruberu', 'Danny Birch',
        'Elena Green', 'Jen Frayne', 'Jo Foy', 'Jo Schiavetta',
        'Joan Coughlin', 'Kristy Cooper', 'Kylie Pinder',
        'Nicole Lynch', 'Raechel Muller'
    ]

    print(f'🏋️ Generating progressions for {len(clients)} clients...')

    ai = ProgressiveOverloadAI()
    all_progressions = {}

    for client in clients:
        print(f'Processing {client}...')
        try:
            workout_data = ai.load_client_workout_data(client, weeks_back=4)
            if workout_data:
                progressions = ai.analyze_progression_patterns(workout_data)
                if progressions:
                    # Convert ProgressionDecision objects to dictionaries
                    client_progressions = {}
                    for exercise_name, decisions in progressions.items():
                        client_progressions[exercise_name] = [
                            progression_to_dict(d) for d in decisions]

                    all_progressions[client.lower().replace(
                        ' ', '_')] = client_progressions
                    print(
                        f'  ✅ Generated {len(progressions)} exercise progressions')
                else:
                    print(f'  ⚠️ No progressions generated')
            else:
                print(f'  ⚠️ No workout data found')
        except Exception as e:
            print(f'  ❌ Error: {e}')

    print(f'\n📊 Total clients with progressions: {len(all_progressions)}')

    # Save progressions
    if all_progressions:
        with open('fresh_progressions.json', 'w') as f:
            json.dump(all_progressions, f, indent=2)
        print('✅ Saved progressions to fresh_progressions.json')

        # Show summary
        total_exercises = sum(len(client_data)
                              for client_data in all_progressions.values())
        print(
            f'📋 Summary: {len(all_progressions)} clients, {total_exercises} exercises')

        for client_key, exercises in all_progressions.items():
            client_name = client_key.replace('_', ' ').title()
            print(f'  • {client_name}: {len(exercises)} exercises')
    else:
        print('❌ No progressions to save')


if __name__ == "__main__":
    main()
