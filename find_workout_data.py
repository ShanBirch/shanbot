import json
from datetime import datetime


def find_users_with_workout_data():
    """Find users with actual workout data to test Progressive Overload AI"""

    analytics_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"

    try:
        with open(analytics_path, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)

        print("🔍 Searching for users with workout data...")
        print("=" * 60)

        users_with_workouts = []

        if "conversations" in analytics_data:
            for uid, user_data in analytics_data["conversations"].items():
                metrics = user_data.get("metrics", {})
                username = metrics.get("ig_username", "Unknown")

                # Check various places for workout data
                has_workout_program = "workout_program" in user_data
                has_weekly_summaries = "weekly_summaries" in user_data
                has_workout_logs = "workout_logs" in user_data

                if has_workout_program or has_weekly_summaries or has_workout_logs:
                    user_info = {
                        "uid": uid,
                        "username": username,
                        "has_workout_program": has_workout_program,
                        "has_weekly_summaries": has_weekly_summaries,
                        "has_workout_logs": has_workout_logs
                    }

                    # Get more details about workout data
                    if has_workout_program:
                        workout_program = user_data["workout_program"]
                        user_info["workout_program_keys"] = list(workout_program.keys()) if isinstance(
                            workout_program, dict) else str(type(workout_program))

                    if has_weekly_summaries:
                        weekly_summaries = user_data["weekly_summaries"]
                        user_info["weekly_summaries_count"] = len(
                            weekly_summaries) if isinstance(weekly_summaries, dict) else 0

                    users_with_workouts.append(user_info)

        print(f"Found {len(users_with_workouts)} users with workout data:")
        print()

        for i, user in enumerate(users_with_workouts[:10]):  # Show first 10
            print(f"📊 User {i+1}: {user['username']}")
            print(f"   UID: {user['uid'][:15]}...")

            if user['has_workout_program']:
                print(
                    f"   ✅ Has workout_program: {user.get('workout_program_keys', 'N/A')}")

            if user['has_weekly_summaries']:
                print(
                    f"   ✅ Has weekly_summaries: {user.get('weekly_summaries_count', 0)} weeks")

            if user['has_workout_logs']:
                print(f"   ✅ Has workout_logs")

            print()

        # Pick a specific user to analyze in detail
        if users_with_workouts:
            print("🔬 Detailed analysis of first user with workout data:")
            print("=" * 60)

            selected_user = users_with_workouts[0]
            uid = selected_user['uid']
            user_data = analytics_data["conversations"][uid]

            print(f"User: {selected_user['username']}")
            print(f"All user data keys: {list(user_data.keys())}")

            # Analyze workout_program structure
            if "workout_program" in user_data:
                workout_program = user_data["workout_program"]
                print(f"\n📋 Workout Program Structure:")
                if isinstance(workout_program, dict):
                    for key, value in workout_program.items():
                        print(f"   {key}: {type(value)}")
                        if isinstance(value, dict) and len(value) < 10:
                            print(f"      Content: {value}")
                        elif isinstance(value, list) and len(value) < 5:
                            print(f"      Content: {value}")
                        elif isinstance(value, list):
                            print(f"      List with {len(value)} items")
                            if value and isinstance(value[0], dict):
                                print(
                                    f"      First item keys: {list(value[0].keys())}")

                else:
                    print(f"   Type: {type(workout_program)}")
                    print(f"   Content: {workout_program}")

            # Analyze weekly_summaries structure
            if "weekly_summaries" in user_data:
                weekly_summaries = user_data["weekly_summaries"]
                print(f"\n📊 Weekly Summaries Structure:")
                if isinstance(weekly_summaries, dict):
                    print(f"   Number of weeks: {len(weekly_summaries)}")
                    # Look at first week
                    first_week_key = list(weekly_summaries.keys())[
                        0] if weekly_summaries else None
                    if first_week_key:
                        first_week = weekly_summaries[first_week_key]
                        print(
                            f"   Sample week ({first_week_key}): {list(first_week.keys()) if isinstance(first_week, dict) else type(first_week)}")

                        if isinstance(first_week, dict):
                            for key, value in first_week.items():
                                if "workout" in key.lower() or "exercise" in key.lower():
                                    print(f"      {key}: {type(value)}")
                                    if isinstance(value, list) and value:
                                        print(
                                            f"         Sample: {value[0] if len(str(value[0])) < 100 else str(value[0])[:100] + '...'}")

        return users_with_workouts[0] if users_with_workouts else None

    except Exception as e:
        print(f"Error finding workout data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    selected_user = find_users_with_workout_data()

    if selected_user:
        print(
            f"\n🎯 RECOMMENDATION: Test Progressive Overload AI with user '{selected_user['username']}'")
        print(f"   This user has the most complete workout data structure.")
    else:
        print("\n❌ No users found with workout data. May need to check check-in data structure.")
