import json
import os
from datetime import datetime
import sqlite3

# Paths
ANALYTICS_JSON_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
ANALYTICS_SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
OUTPUT_FILE = "missing_instagram_analysis.txt"


def load_analytics_data():
    """Load analytics data from JSON file"""
    try:
        print(f"Loading analytics data from: {ANALYTICS_JSON_PATH}")
        with open(ANALYTICS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ Successfully loaded analytics JSON data")
        return data
    except FileNotFoundError:
        print(f"❌ Analytics file not found: {ANALYTICS_JSON_PATH}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading analytics data: {e}")
        return None


def load_sqlite_data():
    """Load user data from SQLite database"""
    try:
        print(f"Loading SQLite data from: {ANALYTICS_SQLITE_PATH}")
        conn = sqlite3.connect(ANALYTICS_SQLITE_PATH)
        cursor = conn.cursor()

        # First, let's check what columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print(f"Available columns: {[col[1] for col in columns]}")

        # Get all users with their ig_username using the correct column names
        cursor.execute(
            "SELECT rowid, ig_username, subscriber_id, first_name, last_name FROM users WHERE ig_username IS NOT NULL AND ig_username != ''")
        users = cursor.fetchall()

        conn.close()
        print(f"✅ Successfully loaded {len(users)} users from SQLite")
        return users
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading SQLite data: {e}")
        return []


def has_instagram_analysis(user_data):
    """Check if a user has Instagram analysis data"""
    if not isinstance(user_data, dict):
        return False

    metrics = user_data.get('metrics', {})
    if not isinstance(metrics, dict):
        return False

    # Check for client_analysis which is added by the Instagram analyzer
    client_analysis = metrics.get('client_analysis')
    if not client_analysis:
        return False

    # Verify it has the key fields that indicate a complete analysis
    required_fields = ['posts_analyzed', 'timestamp',
                       'interests', 'conversation_topics']
    if not isinstance(client_analysis, dict):
        return False

    return any(field in client_analysis for field in required_fields)


def get_ig_username_from_data(user_key, user_data):
    """Extract Instagram username from user data"""
    # First try from metrics if user_data exists
    if isinstance(user_data, dict):
        metrics = user_data.get('metrics', {})
        if isinstance(metrics, dict):
            ig_username = metrics.get('ig_username')
            if ig_username and isinstance(ig_username, str) and ig_username.strip():
                return ig_username.strip()

    # If user_key itself looks like an Instagram username (not numeric), use it
    if not user_key.isdigit() and isinstance(user_key, str) and user_key.strip():
        return user_key.strip()

    return None


def get_user_info_safely(user_data, field_path, default=''):
    """Safely get nested user data, handling None values"""
    if not isinstance(user_data, dict):
        return default

    try:
        result = user_data
        for field in field_path:
            result = result.get(field, {})
            if result is None:
                return default
        return result if result else default
    except (AttributeError, TypeError):
        return default


def identify_missing_instagram_analysis():
    """Main function to identify users missing Instagram analysis"""
    print("🔍 Identifying users missing Instagram analysis...")
    print("=" * 60)

    # Load analytics data
    analytics_data = load_analytics_data()
    if not analytics_data:
        return

    # Also load SQLite data for cross-reference
    sqlite_users = load_sqlite_data()
    # ig_username is index 1
    sqlite_usernames = {
        user[1].lower(): user for user in sqlite_users if user[1]}

    conversations = analytics_data.get('conversations', {})
    print(f"📊 Found {len(conversations)} total users in analytics data")

    users_with_analysis = []
    users_without_analysis = []
    missing_ig_usernames = []

    for user_key, user_data in conversations.items():
        # Skip if user_data is None
        if user_data is None:
            print(f"⚠️  Skipping user {user_key}: User data is None")
            continue

        ig_username = get_ig_username_from_data(user_key, user_data)

        if not ig_username:
            print(f"⚠️  Skipping user {user_key}: No Instagram username found")
            continue

        has_analysis = has_instagram_analysis(user_data)

        if has_analysis:
            analysis_timestamp = get_user_info_safely(
                user_data, ['metrics', 'client_analysis', 'timestamp'], 'Unknown')
            users_with_analysis.append({
                'key': user_key,
                'ig_username': ig_username,
                'analysis_timestamp': analysis_timestamp
            })
        else:
            first_name = get_user_info_safely(
                user_data, ['metrics', 'first_name'], '')
            last_name = get_user_info_safely(
                user_data, ['metrics', 'last_name'], '')
            subscriber_id = get_user_info_safely(
                user_data, ['metrics', 'subscriber_id'], '')

            users_without_analysis.append({
                'key': user_key,
                'ig_username': ig_username,
                'first_name': first_name,
                'last_name': last_name,
                'subscriber_id': subscriber_id
            })
            missing_ig_usernames.append(ig_username)

    # Print summary
    print("\n📈 ANALYSIS SUMMARY:")
    print(f"✅ Users WITH Instagram analysis: {len(users_with_analysis)}")
    print(f"❌ Users WITHOUT Instagram analysis: {len(users_without_analysis)}")
    print(f"📝 Instagram usernames to analyze: {len(missing_ig_usernames)}")

    # Show some examples of users with analysis
    if users_with_analysis:
        print(f"\n✅ Examples of users WITH analysis:")
        for user in users_with_analysis[:5]:
            timestamp_display = user['analysis_timestamp'][:10] if len(
                user['analysis_timestamp']) > 10 else user['analysis_timestamp']
            print(
                f"   - {user['ig_username']} (analyzed: {timestamp_display})")
        if len(users_with_analysis) > 5:
            print(f"   ... and {len(users_with_analysis) - 5} more")

    # Show users without analysis
    if users_without_analysis:
        print(f"\n❌ Users WITHOUT Instagram analysis:")
        for user in users_without_analysis[:10]:
            name = f"{user['first_name']} {user['last_name']}".strip()
            if not name:
                name = "No name"
            print(f"   - {user['ig_username']} ({name})")
        if len(users_without_analysis) > 10:
            print(f"   ... and {len(users_without_analysis) - 10} more")

    # Export missing usernames to file
    if missing_ig_usernames:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("# Instagram usernames missing analysis\n")
                f.write(
                    f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total usernames: {len(missing_ig_usernames)}\n\n")

                # Remove duplicates and sort
                for username in sorted(set(missing_ig_usernames)):
                    f.write(f"{username}\n")

            print(
                f"\n💾 Exported {len(set(missing_ig_usernames))} unique usernames to: {OUTPUT_FILE}")
            print(f"📁 File location: {os.path.abspath(OUTPUT_FILE)}")
            print("\n🚀 You can now run the analyze_followers.py script with:")
            print(
                f"   python anaylize_followers.py --followers-list {OUTPUT_FILE}")

        except Exception as e:
            print(f"❌ Error writing to file: {e}")
    else:
        print("\n🎉 All users already have Instagram analysis!")

    # Cross-reference with SQLite data
    print(f"\n🔄 Cross-referencing with SQLite database...")
    sqlite_missing = []
    for username in missing_ig_usernames:
        if username.lower() in sqlite_usernames:
            sqlite_user = sqlite_usernames[username.lower()]
            sqlite_missing.append({
                'ig_username': username,
                'id': sqlite_user[0],
                'subscriber_id': sqlite_user[2],
                'first_name': sqlite_user[3] or '',
                'last_name': sqlite_user[4] or ''
            })

    print(
        f"📊 {len(sqlite_missing)} users found in both analytics JSON and SQLite database")

    return {
        'total_users': len(conversations),
        'users_with_analysis': len(users_with_analysis),
        'users_without_analysis': len(users_without_analysis),
        'missing_usernames': list(set(missing_ig_usernames)),
        'output_file': OUTPUT_FILE
    }


if __name__ == "__main__":
    result = identify_missing_instagram_analysis()
    if result:
        print(
            f"\n✨ Analysis complete! Found {result['users_without_analysis']} users needing Instagram analysis.")
