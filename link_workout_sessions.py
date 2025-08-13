import sqlite3
import json


def link_workout_sessions():
    """Link workout sessions to users by matching client_name_key with user names"""
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    print("=== LINKING WORKOUT SESSIONS TO USERS ===")

    # Get all users with names
    cursor.execute('''
        SELECT ig_username, first_name, last_name 
        FROM users 
        WHERE ig_username IS NOT NULL 
        AND first_name IS NOT NULL 
        AND last_name IS NOT NULL
    ''')
    users = cursor.fetchall()

    print(f"Found {len(users)} users with names")

    # Get all unique client_name_keys from workout sessions
    cursor.execute(
        'SELECT DISTINCT client_name_key FROM client_workout_sessions')
    client_keys = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(client_keys)} unique client name keys")

    matches_found = 0

    # Try to match each client_name_key with users
    for client_key in client_keys:
        # Parse the client_name_key (format: firstname_lastname)
        name_parts = client_key.replace('_', ' ').split()
        if len(name_parts) >= 2:
            first_name = name_parts[0].lower()
            last_name = name_parts[-1].lower()

            # Look for matching user
            for ig_username, user_first, user_last in users:
                if (user_first.lower() == first_name and
                        user_last.lower() == last_name):

                    print(
                        f"✅ MATCH: {client_key} -> {ig_username} ({user_first} {user_last})")

                    # Update workout sessions with ig_username
                    cursor.execute('''
                        UPDATE client_workout_sessions 
                        SET ig_username = ? 
                        WHERE client_name_key = ? AND ig_username IS NULL
                    ''', (ig_username, client_key))

                    updated_count = cursor.rowcount
                    if updated_count > 0:
                        print(f"    Updated {updated_count} workout sessions")
                        matches_found += 1
                    break

    conn.commit()

    # Check final results
    cursor.execute(
        'SELECT COUNT(*) FROM client_workout_sessions WHERE ig_username IS NOT NULL')
    total_linked = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM client_workout_sessions')
    total_sessions = cursor.fetchone()[0]

    print(f"\n=== RESULTS ===")
    print(f"Total workout sessions: {total_sessions}")
    print(f"Sessions with ig_username: {total_linked}")
    print(f"New matches found: {matches_found}")

    # Show some examples of linked data
    cursor.execute('''
        SELECT ig_username, workout_date, workout_name, client_name_key
        FROM client_workout_sessions 
        WHERE ig_username IS NOT NULL 
        ORDER BY workout_date DESC 
        LIMIT 5
    ''')

    examples = cursor.fetchall()
    if examples:
        print(f"\n=== SAMPLE LINKED SESSIONS ===")
        for ig_username, date, workout_name, client_key in examples:
            print(f"  {ig_username} | {date} | {workout_name} | {client_key}")

    conn.close()
    return total_linked > 0


if __name__ == "__main__":
    link_workout_sessions()
