#!/usr/bin/env python3

import json
import os


def check_analytics_structure():
    analytics_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        conversations = data.get('conversations', {})
        print(f"Total conversations: {len(conversations)}")

        # Check a few users to see their structure
        count = 0
        users_with_analysis = 0
        users_with_coaching = 0

        for username, user_data in conversations.items():
            if count >= 10:  # Check first 10 users
                break

            count += 1
            metrics = user_data.get('metrics', {})
            client_analysis = metrics.get('client_analysis', {})

            print(f"\nUser {count}: {username}")
            print(f"  Has client_analysis: {bool(client_analysis)}")

            if client_analysis:
                users_with_analysis += 1
                print(f"  Analysis keys: {list(client_analysis.keys())}")

                coaching_potential = client_analysis.get('coaching_potential')
                if coaching_potential:
                    users_with_coaching += 1
                    print(
                        f"  Has coaching analysis: Yes (Score: {coaching_potential.get('score', 'Unknown')})")
                else:
                    print(f"  Has coaching analysis: No")

                # Show interests if available
                interests = client_analysis.get('interests', [])
                if interests:
                    print(f"  Interests: {interests[:3]}...")  # Show first 3

        print(f"\nSummary:")
        print(f"  Users with client analysis: {users_with_analysis}")
        print(f"  Users with coaching analysis: {users_with_coaching}")

        if users_with_analysis > 0 and users_with_coaching == 0:
            print("\n🔍 Found users with client analysis but no coaching scores.")
            print("💡 You may need to run the coaching analysis first!")
            print("💡 Try running: from identify_potential_clients import analyze_all_followers_for_coaching; analyze_all_followers_for_coaching()")

        # Let's also check some actual usernames that have data
        usernames_with_data = []
        for username, user_data in conversations.items():
            metrics = user_data.get('metrics', {})
            client_analysis = metrics.get('client_analysis', {})
            if client_analysis and client_analysis.get('interests'):
                usernames_with_data.append(username)
                if len(usernames_with_data) >= 20:
                    break

        print(
            f"\n📋 Found {len(usernames_with_data)} users with analysis data:")
        for i, username in enumerate(usernames_with_data[:10], 1):
            print(f"  {i:2d}. {username}")

        if len(usernames_with_data) > 10:
            print(f"  ... and {len(usernames_with_data) - 10} more")

        return usernames_with_data

    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    usernames = check_analytics_structure()
