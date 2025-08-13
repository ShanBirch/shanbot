import sqlite3


def manual_workout_links():
    """Manually link known workout sessions to users"""
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Manual mappings based on what we can see
    manual_mappings = {
        'kristy_cooper': 'Kristyleecoop',
        'alice_forster': 'forster.alice',  # Based on sync output we saw earlier
        # Add more mappings as we identify them
    }

    print("=== MANUAL WORKOUT SESSION LINKING ===")

    total_updated = 0

    for client_key, ig_username in manual_mappings.items():
        # Check if the user exists
        cursor.execute(
            'SELECT COUNT(*) FROM users WHERE ig_username = ?', (ig_username,))
        user_exists = cursor.fetchone()[0] > 0

        if user_exists:
            # Update workout sessions
            cursor.execute('''
                UPDATE client_workout_sessions 
                SET ig_username = ? 
                WHERE client_name_key = ? AND ig_username IS NULL
            ''', (ig_username, client_key))

            updated_count = cursor.rowcount
            if updated_count > 0:
                print(
                    f"✅ Linked {client_key} -> {ig_username} ({updated_count} sessions)")
                total_updated += updated_count
            else:
                print(
                    f"⚠️  No sessions to update for {client_key} -> {ig_username}")
        else:
            print(f"❌ User {ig_username} not found in database")

    conn.commit()

    # Check results
    cursor.execute(
        'SELECT COUNT(*) FROM client_workout_sessions WHERE ig_username IS NOT NULL')
    total_linked = cursor.fetchone()[0]

    print(f"\n=== RESULTS ===")
    print(f"Total sessions updated: {total_updated}")
    print(f"Total sessions with ig_username: {total_linked}")

    # Show sample linked data
    if total_linked > 0:
        cursor.execute('''
            SELECT ig_username, workout_date, workout_name, client_name_key
            FROM client_workout_sessions 
            WHERE ig_username IS NOT NULL 
            ORDER BY workout_date DESC 
            LIMIT 5
        ''')

        examples = cursor.fetchall()
        print(f"\n=== SAMPLE LINKED SESSIONS ===")
        for ig_username, date, workout_name, client_key in examples:
            print(f"  {ig_username} | {date} | {workout_name}")

    conn.close()
    return total_linked > 0


if __name__ == "__main__":
    manual_workout_links()
