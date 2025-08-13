#!/usr/bin/env python3

import json


def find_coaching_scores():
    try:
        with open('app/analytics_data_good_backup.json', 'r') as f:
            data = json.load(f)

        print("=== Looking for coaching scores ===")

        conversations = data.get('conversations', {})
        print(f"Total conversations: {len(conversations)}")

        # Look for users with coaching potential scores
        high_potential_users = []

        for user_id, convo_data in conversations.items():
            metrics = convo_data.get('metrics', {})
            ig_username = metrics.get('ig_username', user_id)

            # Look for coaching-related fields
            coaching_fields = {}
            for key, value in metrics.items():
                if 'coaching' in key.lower() or 'potential' in key.lower() or 'score' in key.lower():
                    coaching_fields[key] = value

            # Check client analysis
            client_analysis = metrics.get('client_analysis', {})
            if client_analysis:
                print(f"\nUser: {ig_username}")
                print(
                    f"  Client analysis keys: {list(client_analysis.keys())}")

                # Look for coaching score or potential
                coaching_score = None
                for key, value in client_analysis.items():
                    if 'coaching' in key.lower() or 'potential' in key.lower() or 'score' in key.lower():
                        print(f"  {key}: {value}")
                        if isinstance(value, (int, float)) and value >= 70:
                            coaching_score = value

                if coaching_score:
                    high_potential_users.append({
                        'username': ig_username,
                        'score': coaching_score,
                        'user_id': user_id
                    })

                # Look at profile bio for interests
                profile_bio = client_analysis.get('profile_bio', {})
                if profile_bio and profile_bio.get('INTERESTS'):
                    interests = profile_bio.get('INTERESTS', [])
                    if any('fitness' in str(interest).lower() or 'health' in str(interest).lower()
                           for interest in interests):
                        print(f"  Fitness interests: {interests}")

        print(f"\n=== High Potential Users (score >= 70) ===")
        for user in high_potential_users:
            print(f"  {user['username']}: {user['score']}")

        # If no scoring found, let's look at conversation topics as a proxy
        if not high_potential_users:
            print("\n=== Looking for fitness-interested users ===")
            fitness_users = []

            count = 0
            for user_id, convo_data in conversations.items():
                if count >= 20:  # Limit output
                    break

                metrics = convo_data.get('metrics', {})
                ig_username = metrics.get('ig_username', user_id)

                # Check for fitness indicators
                fitness_indicators = []

                if metrics.get('coaching_inquiry_count', 0) > 0:
                    fitness_indicators.append('coaching_inquiry')
                if metrics.get('weight_loss_mentioned', False):
                    fitness_indicators.append('weight_loss')
                if metrics.get('muscle_gain_mentioned', False):
                    fitness_indicators.append('muscle_gain')
                if metrics.get('vegan_topic_mentioned', False):
                    fitness_indicators.append('vegan')

                client_analysis = metrics.get('client_analysis', {})
                if client_analysis:
                    interests = client_analysis.get(
                        'profile_bio', {}).get('INTERESTS', [])
                    for interest in interests:
                        if any(term in str(interest).lower() for term in ['fitness', 'health', 'gym', 'workout', 'nutrition']):
                            fitness_indicators.append('fitness_interests')
                            break

                if fitness_indicators:
                    fitness_users.append({
                        'username': ig_username,
                        'indicators': fitness_indicators,
                        'user_id': user_id
                    })
                    count += 1

            print(f"Found {len(fitness_users)} fitness-interested users:")
            for user in fitness_users[:20]:  # Show first 20
                print(f"  {user['username']}: {user['indicators']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    find_coaching_scores()
