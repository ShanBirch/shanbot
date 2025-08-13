import json
import sqlite3
from datetime import datetime


def sync_analysis_to_database():
    """Sync Instagram analysis data from JSON to SQLite database"""

    # File paths
    json_file = 'app/analytics_data_good.json'
    db_file = 'app/analytics_data_good.sqlite'

    print("🔄 Starting sync of Instagram analysis data...")
    print("=" * 60)

    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"✅ Loaded JSON data from {json_file}")
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return

    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print(f"✅ Connected to database {db_file}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return

    conversations = json_data.get('conversations', {})
    updated_count = 0
    skipped_count = 0
    error_count = 0

    print(f"📊 Processing {len(conversations)} users from JSON...")

    for user_key, user_data in conversations.items():
        if not user_data or not isinstance(user_data, dict):
            continue

        # Get Instagram username
        metrics = user_data.get('metrics', {})
        ig_username = metrics.get('ig_username')

        # If user_key is not numeric, it might be the ig_username itself
        if not ig_username and not user_key.isdigit():
            ig_username = user_key

        if not ig_username:
            continue

        # Check if this user has Instagram analysis in JSON
        client_analysis = metrics.get('client_analysis', {})
        if not client_analysis:
            continue

        # Check if it has the key Instagram analysis fields
        has_ig_analysis = any(key in client_analysis for key in [
            'interests', 'conversation_topics', 'posts_analyzed', 'lifestyle_indicators'
        ])

        if not has_ig_analysis:
            continue

        try:
            # Check if user exists in database
            cursor.execute(
                'SELECT ig_username FROM users WHERE ig_username = ?', (ig_username,))
            db_user = cursor.fetchone()

            if not db_user:
                print(
                    f"⚠️  User {ig_username} not found in database, skipping...")
                skipped_count += 1
                continue

            # Prepare the client analysis data
            client_analysis_json = json.dumps(client_analysis)

            # Also prepare bio data if it exists
            bio_data = client_analysis.get('profile_bio', {})
            bio_text = ""
            if bio_data:
                # Create a readable bio from the structured data
                name = bio_data.get('PERSON NAME', ig_username)
                interests = bio_data.get('INTERESTS', [])
                lifestyle = bio_data.get('LIFESTYLE', '')
                traits = bio_data.get('PERSONALITY TRAITS', [])

                bio_parts = []
                if name and name != ig_username:
                    bio_parts.append(f"Name: {name}")
                if interests:
                    bio_parts.append(f"Interests: {', '.join(interests[:3])}")
                if lifestyle:
                    bio_parts.append(f"Lifestyle: {lifestyle}")
                if traits:
                    bio_parts.append(f"Traits: {', '.join(traits[:3])}")

                bio_text = " | ".join(bio_parts)

            # Update the database
            cursor.execute('''
                UPDATE users 
                SET client_analysis_json = ?, bio = ?
                WHERE ig_username = ?
            ''', (client_analysis_json, bio_text, ig_username))

            if cursor.rowcount > 0:
                updated_count += 1
                if updated_count <= 10:  # Show first 10 updates
                    print(f"✅ Updated {ig_username}")
                elif updated_count == 11:
                    print("   ... (showing first 10, continuing silently)")
            else:
                print(f"⚠️  No rows updated for {ig_username}")

        except Exception as e:
            print(f"❌ Error updating {ig_username}: {e}")
            error_count += 1
            continue

    # Commit changes
    try:
        conn.commit()
        print(f"\n✅ Successfully committed all changes to database")
    except Exception as e:
        print(f"❌ Error committing changes: {e}")
        conn.rollback()
        return
    finally:
        conn.close()

    # Summary
    print("\n" + "=" * 60)
    print("📈 SYNC SUMMARY:")
    print(f"✅ Successfully updated: {updated_count} users")
    print(f"⚠️  Skipped (not in DB): {skipped_count} users")
    print(f"❌ Errors: {error_count} users")
    print(f"📊 Total processed: {updated_count + skipped_count + error_count}")

    if updated_count > 0:
        print(f"\n🎉 Instagram analysis data is now synced to your database!")
        print(
            f"   Your dashboard should now show analysis for {updated_count} more users.")

    return updated_count


if __name__ == "__main__":
    sync_analysis_to_database()
