import sqlite3
import re
import json
from datetime import datetime

DB_PATH = 'app/analytics_data_good.sqlite'


def find_email(text):
    """Finds the first email address in a string."""
    match = re.search(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group(0) if match else None


def fix_challenge_entries():
    """
    Scans conversation history for emails and updates user records
    to correctly tag them as plant-based challenge leads.
    """
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("Database connection successful.")

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM conversation_history WHERE message_type = 'user'")
        total_messages = cursor.fetchone()[0]
        print(
            f"Found {total_messages} total user messages in conversation_history.")

        if total_messages == 0:
            print("No user messages found to scan. Exiting.")
            return

        cursor.execute(
            "SELECT ig_username, message_text FROM conversation_history WHERE message_type = 'user'")
        messages = cursor.fetchall()
        print(f"Scanning {len(messages)} user messages for emails...")

        updated_users = []
        processed_users = set()

        for message in messages:
            ig_username = message['ig_username']
            if not ig_username or ig_username in processed_users:
                continue

            email = find_email(message['message_text'])
            if email:
                user_cursor = conn.cursor()
                user_cursor.execute(
                    "SELECT challenge_email FROM users WHERE ig_username = ?", (ig_username,))
                user_data = user_cursor.fetchone()

                if user_data and user_data['challenge_email']:
                    processed_users.add(ig_username)
                    continue

                print(
                    f"Found email '{email}' for @{ig_username}. Updating record...")
                update_cursor = conn.cursor()
                update_cursor.execute("""
                    UPDATE users
                    SET lead_source = 'plant_based_challenge', challenge_email = ?, 
                        challenge_type = 'vegan', ad_script_state = 'step5', 
                        is_in_ad_flow = 1, challenge_signup_date = ?
                    WHERE ig_username = ?
                """, (email, datetime.now().isoformat(), ig_username))

                if update_cursor.rowcount > 0:
                    updated_users.append(ig_username)
                    print(f"  -> Successfully updated @{ig_username}")
                else:
                    print(
                        f"  -> FAILED to update @{ig_username}. User may not exist in 'users' table.")

                processed_users.add(ig_username)

        conn.commit()
        if updated_users:
            print(
                f"\n✅ Successfully updated {len(updated_users)} users: {updated_users}")
        else:
            print("\nNo new users needed an update.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("Closing database connection.")
        conn.close()


if __name__ == "__main__":
    fix_challenge_entries()
