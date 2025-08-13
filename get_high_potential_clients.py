#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path so we can import the functions
sys.path.append(os.getcwd())

try:
    from identify_potential_clients import get_high_potential_clients, get_coaching_potential_category

    def get_real_high_potential_clients(min_score=70, limit=20):
        """Get real high potential clients from Shannon's dashboard"""
        try:
            print(
                f"🔍 Getting high potential clients with score >= {min_score}...")

            # Get high potential clients using Shannon's existing function
            clients = get_high_potential_clients(min_score=min_score)

            print(f"📊 Found {len(clients)} high potential clients")

            # Sort by score (highest first) and limit to requested number
            clients_sorted = sorted(
                clients, key=lambda x: x.get('score', 0), reverse=True)
            limited_clients = clients_sorted[:limit]

            print(f"🎯 Top {len(limited_clients)} high potential clients:")

            usernames = []
            for i, client in enumerate(limited_clients, 1):
                username = client.get('username', 'unknown')
                score = client.get('score', 0)
                category = client.get('category', 'Unknown')

                print(f"  {i:2d}. {username:<20} Score: {score:3d} ({category})")
                usernames.append(username)

            return usernames

        except Exception as e:
            print(f"❌ Error getting high potential clients: {e}")
            return []

    if __name__ == "__main__":
        # Get 20 high potential clients with score >= 70
        usernames = get_real_high_potential_clients(min_score=70, limit=20)

        print(
            f"\n🚀 Ready to use these {len(usernames)} usernames in the story bot!")
        print("Usernames list:", usernames)

except ImportError as e:
    print(f"❌ Could not import functions: {e}")
    print("Make sure identify_potential_clients.py is in the current directory")
