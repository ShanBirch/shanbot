import json
import pprint
from datetime import datetime


def analyze_analytics_structure():
    """Analyze the structure of analytics_data_good.json to understand workout data format"""

    analytics_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

    try:
        with open(analytics_path, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)

        print("📊 Analytics Data Structure Analysis")
        print("=" * 50)

        # Top level structure
        print("Top level keys:", list(analytics_data.keys()))

        if "conversations" in analytics_data:
            conversations = analytics_data["conversations"]
            print(f"Number of conversations: {len(conversations)}")

            # Look at first few users to understand structure
            sample_users = list(conversations.items())[:3]

            for i, (uid, user_data) in enumerate(sample_users):
                print(f"\n--- User {i+1} (UID: {uid[:10]}...) ---")

                if "metrics" in user_data:
                    metrics = user_data["metrics"]
                    print("Metrics keys:", list(metrics.keys()))

                    # Look for username/identifier
                    if "ig_username" in metrics:
                        print(
                            f"Instagram username: {metrics.get('ig_username')}")
                    if "full_name" in metrics:
                        print(f"Full name: {metrics.get('full_name')}")

                # Look for workout-related data
                print("User data keys:", list(user_data.keys()))

                # Check for workout data in various places
                for key in ["weekly_summaries", "workout_logs", "checkins", "workouts", "fitness_data"]:
                    if key in user_data:
                        data = user_data[key]
                        if isinstance(data, dict):
                            print(
                                f"  {key}: dict with keys {list(data.keys())[:5]}...")
                        elif isinstance(data, list):
                            print(f"  {key}: list with {len(data)} items")
                            if data and isinstance(data[0], dict):
                                print(
                                    f"    First item keys: {list(data[0].keys())}")
                        else:
                            print(f"  {key}: {type(data)}")

                # Look for specific workout mentions
                if "weekly_summaries" in user_data:
                    weekly_summaries = user_data["weekly_summaries"]
                    if isinstance(weekly_summaries, dict):
                        print(
                            f"  Weekly summaries: {len(weekly_summaries)} weeks")
                        # Look at a sample week
                        for week_key, week_data in list(weekly_summaries.items())[:2]:
                            print(
                                f"    Week {week_key}: {list(week_data.keys()) if isinstance(week_data, dict) else type(week_data)}")
                            if isinstance(week_data, dict):
                                for subkey in ["workouts", "exercises", "training", "fitness"]:
                                    if subkey in week_data:
                                        print(
                                            f"      Found {subkey}: {type(week_data[subkey])}")

                print("-" * 30)
                if i >= 2:  # Only show first 3 users
                    break

        # Look for specific users we might want to test with
        print("\n🔍 Looking for specific users...")
        if "conversations" in analytics_data:
            for uid, user_data in analytics_data["conversations"].items():
                metrics = user_data.get("metrics", {})
                username = metrics.get("ig_username", "").lower()
                full_name = metrics.get("full_name", "").lower()

                # Look for Shannon or any user with workout data
                if any(name in username + full_name for name in ["shannon", "birch"]):
                    print(f"Found potential user: {username} / {full_name}")
                    print(f"  User data keys: {list(user_data.keys())}")

                    # Check for workout data
                    has_workout_data = False
                    for key in ["weekly_summaries", "workout_logs", "checkins"]:
                        if key in user_data and user_data[key]:
                            has_workout_data = True
                            print(f"  Has {key}: {type(user_data[key])}")

                    if has_workout_data:
                        print(f"  ✅ This user has workout data!")
                    else:
                        print(f"  ❌ No workout data found")

    except Exception as e:
        print(f"Error analyzing analytics data: {e}")


if __name__ == "__main__":
    analyze_analytics_structure()
