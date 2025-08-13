import json
import os
import sqlite3
import datetime
import sys

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_ANALYTICS_FILE = os.path.join(
    SCRIPT_DIR, "app", "analytics_data_good.json")

# --- Add necessary paths for imports ---
# Add the main 'shanbot' directory to sys.path to find 'anaylize_followers'
# and 'app.dashboard_modules.dashboard_sqlite_utils'
sys.path.append(SCRIPT_DIR)
# Also add the 'app' directory if 'dashboard_modules' is directly under it and SCRIPT_DIR is 'shanbot'
sys.path.append(os.path.join(SCRIPT_DIR, "app"))


# --- Imports from project files ---
try:
    from app.dashboard_modules.dashboard_sqlite_utils import (
        get_db_connection,
        save_metrics_to_sqlite,
        create_user_table_if_not_exists
    )
    # We need has_complete_instagram_analysis_sqlite from anaylize_followers.py
    # To avoid complex relative import issues in a standalone script,
    # we'll copy a simplified version of the function here or ensure SCRIPT_DIR is correct.
    # For now, let's assume anaylize_followers is in SCRIPT_DIR.
    from anaylize_followers import has_complete_instagram_analysis_sqlite as check_sqlite_completion
    print("Successfully imported helper functions.")
except ImportError as e:
    print(f"Error importing helper functions: {e}")
    print("Please ensure migrate_json_to_sqlite.py is in the 'shanbot' directory,")
    print("and that anaylize_followers.py is also in the 'shanbot' directory,")
    print("and dashboard_sqlite_utils.py is in 'app/dashboard_modules/'.")
    sys.exit(1)


def migrate_data():
    """Migrates Instagram follower analysis from JSON to SQLite if not already present in SQLite."""
    print("--- Starting JSON to SQLite Migration ---")

    # 1. Initialize SQLite Database and Tables
    try:
        conn = get_db_connection()
        create_user_table_if_not_exists(conn)
        conn.close()
        print("✅ SQLite database and 'users' table initialized.")
    except Exception as e:
        print(f"❌ Error initializing SQLite database: {e}")
        return

    # 2. Load JSON Data
    if not os.path.exists(JSON_ANALYTICS_FILE):
        print(f"❌ JSON analytics file not found at: {JSON_ANALYTICS_FILE}")
        return
    try:
        with open(JSON_ANALYTICS_FILE, 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)
        print(f"✅ Successfully loaded JSON data from: {JSON_ANALYTICS_FILE}")
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON file: {e}")
        return
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return

    conversations = analytics_data.get("conversations", {})
    if not conversations:
        print("No 'conversations' data found in JSON. Nothing to migrate.")
        return

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Found {len(conversations)} users in JSON. Processing migration...")

    for ig_username_json, user_data_json in conversations.items():
        if not isinstance(user_data_json, dict):
            print(
                f"⚠️ Skipping user {ig_username_json}: user_data is not a dictionary.")
            error_count += 1
            continue

        metrics_json = user_data_json.get("metrics", {})
        if not isinstance(metrics_json, dict):
            print(
                f"⚠️ Skipping user {ig_username_json}: metrics data is not a dictionary.")
            error_count += 1
            continue

        client_analysis_json = metrics_json.get("client_analysis")

        # The username from the top-level key might be a ManyChat ID or an IG username.
        # Prefer 'ig_username' from within metrics if available.
        actual_ig_username = metrics_json.get("ig_username", ig_username_json)

        # Skip if the actual_ig_username looks like a numeric ID (ManyChat ID)
        if actual_ig_username.isdigit():
            print(
                f"ℹ️ Skipping numeric ID {actual_ig_username} from JSON (likely a ManyChat ID, not an IG username).")
            skipped_count += 1
            continue

        if client_analysis_json and isinstance(client_analysis_json, dict):
            # Check if this user already has a complete analysis in SQLite
            if check_sqlite_completion(actual_ig_username):
                print(
                    f"ℹ️ Skipping '{actual_ig_username}': Already has complete analysis in SQLite.")
                skipped_count += 1
            else:
                print(
                    f"⏳ Migrating '{actual_ig_username}' from JSON to SQLite...")
                try:
                    # Prepare metrics_data structure for save_metrics_to_sqlite
                    # This needs to match what update_analytics_sqlite in anaylize_followers.py expects
                    metrics_data_for_sqlite = {
                        'ig_username': actual_ig_username,  # Ensure this is the correct IG username
                        'client_analysis': client_analysis_json,  # The actual analysis data
                        'timestamp': client_analysis_json.get('timestamp', datetime.datetime.now().isoformat()),
                        'posts_analyzed': client_analysis_json.get('posts_analyzed', 0),
                        'interests': client_analysis_json.get('interests', []),
                        'lifestyle_indicators': client_analysis_json.get('lifestyle_indicators', []),
                        'recent_activities': client_analysis_json.get('recent_activities', []),
                        'post_summaries': client_analysis_json.get('post_summaries', []),
                        'conversation_topics': client_analysis_json.get('conversation_topics', []),
                        'profile_bio': client_analysis_json.get('profile_bio', {}),
                        'analysis_source': 'instagram_follower_analyzer_migrated_from_json'  # Migration source
                    }

                    # Add any other top-level fields from JSON's metrics if they should be preserved
                    # For example, if there are other fields like 'subscriber_id', 'first_name', etc. at the same level as 'client_analysis'
                    for key, value in metrics_json.items():
                        if key not in metrics_data_for_sqlite and key != 'client_analysis':
                            metrics_data_for_sqlite[key] = value

                    if save_metrics_to_sqlite(actual_ig_username, metrics_data_for_sqlite):
                        print(
                            f"✅ Successfully migrated '{actual_ig_username}'.")
                        migrated_count += 1
                    else:
                        print(
                            f"❌ Failed to save migrated data for '{actual_ig_username}' to SQLite.")
                        error_count += 1
                except Exception as e:
                    print(
                        f"❌ Error during migration for '{actual_ig_username}': {e}")
                    error_count += 1
        else:
            # print(f"ℹ️ No 'client_analysis' data found for user '{actual_ig_username}' in JSON. Skipping migration for this user.")
            # This case will be handled by the main anaylize_followers.py script if the user is in followers list
            pass  # Don't increment skipped_count here, as they weren't eligible for migration

    print("\n--- Migration Summary ---")
    print(f"Total users processed from JSON: {len(conversations)}")
    print(f"Successfully migrated to SQLite: {migrated_count}")
    print(f"Skipped (already in SQLite or numeric ID): {skipped_count}")
    print(f"Errors during migration: {error_count}")
    print("--- Migration Complete ---")


if __name__ == "__main__":
    migrate_data()
