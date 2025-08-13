import sqlite3


def check_workout_links():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Check client_name_key values in workout sessions
    cursor.execute(
        'SELECT DISTINCT client_name_key FROM client_workout_sessions LIMIT 10')
    client_keys = [row[0] for row in cursor.fetchall()]
    print("Client name keys in workout sessions:")
    for key in client_keys:
        print(f"  {key}")

    # Check ig_usernames in users table
    cursor.execute(
        'SELECT DISTINCT ig_username FROM users WHERE ig_username IS NOT NULL LIMIT 10')
    ig_usernames = [row[0] for row in cursor.fetchall()]
    print(f"\nIG usernames in users table ({len(ig_usernames)} total):")
    for username in ig_usernames:
        print(f"  {username}")

    # Check if we can match by name
    cursor.execute(
        'SELECT first_name, last_name, ig_username FROM users WHERE ig_username IS NOT NULL LIMIT 10')
    user_names = cursor.fetchall()
    print(f"\nUser names and IG usernames:")
    for first, last, ig in user_names:
        full_name_key = f"{first}_{last}".lower().replace(' ', '_')
        print(f"  {first} {last} -> {ig} (potential key: {full_name_key})")

        # Check if this matches any client_name_key
        if full_name_key in [key.lower() for key in client_keys]:
            print(f"    ✅ MATCH FOUND with client_name_key!")

    # Try to find any workout sessions that might match
    print(f"\nTrying to match workout sessions with users...")
    for client_key in client_keys[:5]:  # Check first 5
        # Try different name formats
        name_parts = client_key.replace('_', ' ').split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]

            cursor.execute('''
                SELECT ig_username FROM users 
                WHERE LOWER(first_name) = ? AND LOWER(last_name) = ?
            ''', (first_name.lower(), last_name.lower()))

            match = cursor.fetchone()
            if match:
                ig_username = match[0]
                print(f"  {client_key} -> {ig_username}")

                # Update the workout session with ig_username
                cursor.execute('''
                    UPDATE client_workout_sessions 
                    SET ig_username = ? 
                    WHERE client_name_key = ?
                ''', (ig_username, client_key))
                print(f"    Updated {cursor.rowcount} workout sessions")

    conn.commit()

    # Check how many workout sessions now have ig_username
    cursor.execute(
        'SELECT COUNT(*) FROM client_workout_sessions WHERE ig_username IS NOT NULL')
    updated_count = cursor.fetchone()[0]
    print(f"\nWorkout sessions with ig_username after update: {updated_count}")

    conn.close()


if __name__ == "__main__":
    check_workout_links()
