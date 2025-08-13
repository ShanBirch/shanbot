import sqlite3
import json


def check_missing_analysis():
    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get all users with Instagram usernames
    cursor.execute('''
        SELECT ig_username, subscriber_id, first_name, last_name, 
               client_analysis_json, metrics_json, bio
        FROM users 
        WHERE ig_username IS NOT NULL AND ig_username != ''
        ORDER BY ig_username
    ''')

    all_users = cursor.fetchall()
    print(f"📊 Total users with Instagram usernames: {len(all_users)}")

    users_missing_analysis = []
    users_with_analysis = []

    for user in all_users:
        ig_username, subscriber_id, first_name, last_name, client_analysis_json, metrics_json, bio = user

        # Check if they have client analysis data
        has_client_analysis = False
        if client_analysis_json and client_analysis_json != 'NULL':
            try:
                client_data = json.loads(client_analysis_json)
                # Check if it has Instagram analysis fields
                if any(key in client_data for key in ['interests', 'conversation_topics', 'posts_analyzed', 'lifestyle_indicators']):
                    has_client_analysis = True
            except:
                pass

        # Check metrics_json too
        has_metrics_analysis = False
        if metrics_json and metrics_json != 'NULL':
            try:
                metrics_data = json.loads(metrics_json)
                # Check if client_analysis exists in metrics
                if 'client_analysis' in metrics_data:
                    client_analysis = metrics_data['client_analysis']
                    if any(key in client_analysis for key in ['interests', 'conversation_topics', 'posts_analyzed', 'lifestyle_indicators']):
                        has_metrics_analysis = True
            except:
                pass

        name = f"{first_name or ''} {last_name or ''}".strip() or "No name"

        if has_client_analysis or has_metrics_analysis:
            users_with_analysis.append({
                'ig_username': ig_username,
                'name': name,
                'has_client_analysis': has_client_analysis,
                'has_metrics_analysis': has_metrics_analysis
            })
        else:
            users_missing_analysis.append({
                'ig_username': ig_username,
                'name': name,
                'subscriber_id': subscriber_id
            })

    print(f"✅ Users WITH Instagram analysis: {len(users_with_analysis)}")
    print(f"❌ Users WITHOUT Instagram analysis: {len(users_missing_analysis)}")

    if users_missing_analysis:
        print(f"\n❌ Users missing Instagram analysis:")
        for i, user in enumerate(users_missing_analysis[:20]):
            print(f"   {i+1:2d}. {user['ig_username']:<25} | {user['name']}")

        if len(users_missing_analysis) > 20:
            print(f"   ... and {len(users_missing_analysis) - 20} more")

        # Create a file with the usernames that need analysis
        missing_usernames = [user['ig_username']
                             for user in users_missing_analysis]
        with open('users_needing_analysis.txt', 'w') as f:
            for username in missing_usernames:
                f.write(f"{username}\n")
        print(
            f"\n💾 Saved {len(missing_usernames)} usernames to 'users_needing_analysis.txt'")

    conn.close()
    return users_missing_analysis


if __name__ == "__main__":
    check_missing_analysis()
