import sqlite3
import json
import traceback

DB_PATH = 'app/analytics_data_good.sqlite'


def migrate_history():
    """
    Migrates conversation history from a JSON object in the 'users' table
    to the 'conversation_history' table with detailed logging.
    """
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("Database connection successful.")

    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Found {user_count} total users in the 'users' table.")

        if user_count == 0:
            print("No users found. Aborting migration.")
            return

        cursor.execute("DELETE FROM conversation_history")
        conn.commit()
        print(
            f"Cleared {cursor.rowcount} records from conversation_history table.")

        cursor.execute("SELECT ig_username, conversation_history FROM users")
        users = cursor.fetchall()

        print(f"Starting migration for {len(users)} users...")
        total_messages_migrated = 0

        for i, user in enumerate(users):
            ig_username = user['ig_username']
            history_json = user['conversation_history']

            if not history_json:
                continue

            try:
                history = json.loads(history_json)
                if not isinstance(history, list):
                    print(
                        f"  - Skipping @{ig_username}: conversation_history is not a list.")
                    continue

                for message in history:
                    msg_type = message.get('message_type')
                    msg_text = message.get('message_text')
                    msg_time = message.get('timestamp')

                    if not all([msg_type, msg_text, msg_time]):
                        continue

                    cursor.execute("""
                        INSERT INTO conversation_history (ig_username, message_type, message_text, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (ig_username, msg_type, msg_text, msg_time))
                    total_messages_migrated += 1

                if (i + 1) % 100 == 0:
                    print(f"  Processed {i+1}/{len(users)} users...")

            except (json.JSONDecodeError, TypeError):
                # This will catch malformed JSON
                continue
            except Exception as e:
                print(f"An error occurred processing user @{ig_username}: {e}")

        conn.commit()
        print(
            f"\n✅ Migration complete. Successfully migrated {total_messages_migrated} messages for {len(users)} users.")

    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")
        print(traceback.format_exc())
    finally:
        print("Closing database connection.")
        conn.close()


if __name__ == "__main__":
    migrate_history()
