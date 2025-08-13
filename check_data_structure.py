import json

# Load the analytics data
with open('app/analytics_data_good.json', 'r') as f:
    data = json.load(f)

print("Top level keys:", list(data.keys()))

# Check if conversations exist
if 'conversations' in data:
    conversations = data['conversations']
    print(f"Number of conversations: {len(conversations)}")

    # Get first few usernames
    usernames = list(conversations.keys())[:3]
    print("Sample usernames:", usernames)

    # Check structure of first user
    if usernames:
        first_user = conversations[usernames[0]]
        print("First user keys:", list(first_user.keys()))

        # Check for metrics
        if 'metrics' in first_user:
            metrics = first_user['metrics']
            print("Metrics keys:", list(metrics.keys()))

            # Check for client_analysis
            if 'client_analysis' in metrics:
                client_analysis = metrics['client_analysis']
                print("Client analysis keys:", list(client_analysis.keys()))

                # Check for coaching_potential
                if 'coaching_potential' in client_analysis:
                    coaching_potential = client_analysis['coaching_potential']
                    print("Coaching potential:", coaching_potential)

                    if 'score' in coaching_potential:
                        score = coaching_potential['score']
                        print(f"Coaching score: {score}")

                        # Count users with score >= 70
                        high_score_count = 0
                        for username, user_data in conversations.items():
                            try:
                                score = user_data['metrics']['client_analysis']['coaching_potential']['score']
                                if score >= 70:
                                    high_score_count += 1
                            except (KeyError, TypeError):
                                continue

                        print(f"Users with score >= 70: {high_score_count}")
else:
    print("No 'conversations' key found in data")
