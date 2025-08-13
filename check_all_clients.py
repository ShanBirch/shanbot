#!/usr/bin/env python3

from identify_potential_clients import get_high_potential_clients


def check_all_clients():
    try:
        # Get all clients regardless of score
        clients = get_high_potential_clients(min_score=0)
        print(f"Total clients found: {len(clients)}")

        if clients:
            # Sort by score (highest first)
            sorted_clients = sorted(
                clients, key=lambda x: x.get('score', 0), reverse=True)

            print("\nTop 20 clients by score:")
            for i, client in enumerate(sorted_clients[:20], 1):
                username = client.get('username', 'unknown')
                score = client.get('score', 0)
                category = client.get('category', 'Unknown')
                print(f"{i:2d}. {username:<25} Score: {score:3d} ({category})")

            # Get clients with score >= 50 for the bot
            high_scoring = [
                c for c in sorted_clients if c.get('score', 0) >= 50]
            print(f"\nClients with score >= 50: {len(high_scoring)}")

            if high_scoring:
                usernames = [c.get('username') for c in high_scoring[:20]]
                print("\nUsernames for bot (score >= 50):")
                print(usernames)
                return usernames
        else:
            print("No clients found in analytics data")
            return []

    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    usernames = check_all_clients()
