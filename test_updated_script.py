#!/usr/bin/env python3

# Test the updated ClientDataManager
from potential_clients_story_commentor import ClientDataManager
import sys
sys.path.append('.')


# Initialize the data manager
db_manager = ClientDataManager()

# Test different thresholds
print("Testing different coaching score thresholds:")
for threshold in [90, 80, 70, 60, 50]:
    clients = db_manager.get_high_potential_clients(threshold)
    print(f"Score >= {threshold}: Found {len(clients)} clients")

    if clients:
        print(f"  Top 3 clients:")
        for i, client in enumerate(clients[:3]):
            print(
                f"    {i+1}. {client['ig_username']} (Score: {client['score']})")
        print()

print("Testing with threshold 70:")
target_clients = db_manager.get_high_potential_clients(70)
if target_clients:
    print(f"Found {len(target_clients)} clients with score >= 70")
    print("\nSample client details:")
    client = target_clients[0]
    print(f"Username: {client['ig_username']}")
    print(f"Score: {client['score']}")
    print(f"Category: {client['category']}")
    print(f"Interests: {client['interests']}")
    print(f"Conversation topics: {client['conversation_topics']}")
else:
    print("No clients found with score >= 70")
