import sqlite3
import json
import os
from datetime import datetime, timedelta

# Define the path to your SQLite database
DB_PATH = "app/analytics_data_good.sqlite"
REPORT_FILE_PATH = "conversation_analysis_report.txt"


def get_table_schema(table_name: str):
    """
    Connects to the SQLite database and prints the schema of the specified table.
    """
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        schema_info = cursor.fetchall()

        if not schema_info:
            print(f"No schema found for table: {table_name}")
            return

        print(f"--- Schema for table: {table_name} ---")
        print("{:<5} {:<20} {:<15} {:<10} {:<10} {:<10}".format(
            "CID", "Name", "Type", "Not Null", "Default", "PK"))
        print("-" * 75)
        for col in schema_info:
            # Handle None values for default column gracefully
            default_value = str(col[4]) if col[4] is not None else "NULL"
            print("{:<5} {:<20} {:<15} {:<10} {:<10} {:<10}".format(
                col[0], col[1], col[2], bool(
                    col[3]), default_value, bool(col[5])
            ))
        print("-" * 75)

    except sqlite3.Error as e:
        print(f"Database error while fetching schema: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching schema: {e}")
    finally:
        if conn:
            conn.close()


def analyze_conversations():
    """
    Connects to the SQLite database, fetches conversation history for yesterday and today,
    and saves it to a file in a structured, readable format for analysis.
    """
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Calculate yesterday's and today's dates for filtering
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        today_str = today.strftime("%Y-%m-%d 00:00:00")
        yesterday_str = yesterday.strftime("%Y-%m-%d 00:00:00")

        output_lines = []
        output_lines.append("-" * 20)
        output_lines.append(
            f"Conversation Analysis Report (From {yesterday.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')})")
        output_lines.append("-" * 20)

        output_lines.append(
            "--- Attempting to fetch all conversation messages for yesterday and today ---")
        cursor.execute("""
            SELECT
                ig_username,
                type as message_type,
                text as message_text,
                timestamp
            FROM
                messages
            WHERE
                timestamp >= ? AND timestamp < ?
            ORDER BY
                ig_username, timestamp ASC
        """, (yesterday_str, (today + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")))

        messages = cursor.fetchall()

        if not messages:
            output_lines.append(
                "No messages found for the specified date range.")
        else:
            conversations_by_user = {}
            for msg in messages:
                username = msg['ig_username']
                if username not in conversations_by_user:
                    conversations_by_user[username] = []
                conversations_by_user[username].append({
                    "sender": msg['message_type'],
                    "text": msg['message_text'],
                    "timestamp": msg['timestamp']
                })

            for ig_username, conversation_list in conversations_by_user.items():
                output_lines.append("\n" + "="*80 + "\n")
                output_lines.append(
                    f"--- Conversations for Instagram User: @{ig_username} ---")
                for msg in conversation_list:
                    sender = msg.get("sender", "Unknown")
                    text = msg.get("text", "")
                    timestamp = msg.get("timestamp", "No Timestamp")
                    output_lines.append(f"[{timestamp}] {sender}: {text}")
                output_lines.append("-" * 50)

        with open(REPORT_FILE_PATH, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        print(f"Conversation analysis saved to {REPORT_FILE_PATH}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Optionally, you can still print schema to console if needed for debugging
    # get_table_schema("messages")
    # print("\n" + "="*80 + "\n")
    analyze_conversations()
