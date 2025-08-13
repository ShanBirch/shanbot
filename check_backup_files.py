#!/usr/bin/env python3

import json
import os


def check_backup_files():
    files_to_check = [
        'app/analytics_data_good_backup.json',
        'app/analytics_data.json',
        'app/anakytics_Data_backup2105.json'
    ]

    for filepath in files_to_check:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                conversations = data.get('conversations', {})
                print(f"{filepath}: {len(conversations)} conversations")

                if len(conversations) > 0:
                    # Check for users with interests/analysis
                    users_with_data = []
                    # Check first 50
                    for username, user_data in list(conversations.items())[:50]:
                        metrics = user_data.get('metrics', {})
                        client_analysis = metrics.get('client_analysis', {})
                        interests = client_analysis.get('interests', [])

                        if interests:
                            users_with_data.append(username)

                    print(f"  Users with interests: {len(users_with_data)}")
                    if users_with_data:
                        print(f"  Examples: {users_with_data[:5]}")

                        # Return the best file for use
                        if len(users_with_data) >= 10:
                            return filepath, users_with_data[:20]

            except Exception as e:
                print(f"Error reading {filepath}: {e}")
        else:
            print(f"{filepath}: File not found")

    return None, []


if __name__ == "__main__":
    best_file, usernames = check_backup_files()
    if best_file and usernames:
        print(f"\n🎯 Best file to use: {best_file}")
        print(f"📋 Found {len(usernames)} users with data:")
        for i, username in enumerate(usernames, 1):
            print(f"  {i:2d}. {username}")
    else:
        print("\n❌ No suitable analytics file found with user data")
