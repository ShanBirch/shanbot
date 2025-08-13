#!/usr/bin/env python3
"""
Extract conversations from the last 24 hours for easy reading
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta


def get_recent_conversations():
    """Get conversations from the last 24 hours"""
    db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    try:
        conn = sqlite3.connect(db_path)

        # Get messages from last 24 hours
        query = """
        SELECT ig_username, timestamp, type, text 
        FROM messages 
        WHERE datetime(timestamp) >= datetime('now', '-24 hours')
        ORDER BY timestamp ASC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            print("No conversations found in the last 24 hours")
            return

        print(f"=== CONVERSATIONS FROM LAST 24 HOURS ===")
        print(f"Found {len(df)} messages")
        print(f"From {df['timestamp'].min()} to {df['timestamp'].max()}")
        print("=" * 60)

        # Group by username and display conversations
        for username in df['ig_username'].unique():
            user_messages = df[df['ig_username'] == username]

            print(f"\n📱 CONVERSATION WITH: {username}")
            print(f"   ({len(user_messages)} messages)")
            print("-" * 50)

            for _, msg in user_messages.iterrows():
                timestamp = msg['timestamp']
                msg_type = "👤 USER" if msg['type'] == 'user' else "🤖 AI"
                text = str(msg['text'])

                print(f"{timestamp} | {msg_type}")
                print(f"   {text}")
                print()

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"recent_conversations_{timestamp}.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== CONVERSATIONS FROM LAST 24 HOURS ===\n")
            f.write(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total messages: {len(df)}\n")
            f.write("=" * 60 + "\n\n")

            for username in df['ig_username'].unique():
                user_messages = df[df['ig_username'] == username]

                f.write(f"\n📱 CONVERSATION WITH: {username}\n")
                f.write(f"   ({len(user_messages)} messages)\n")
                f.write("-" * 50 + "\n")

                for _, msg in user_messages.iterrows():
                    timestamp = msg['timestamp']
                    msg_type = "👤 USER" if msg['type'] == 'user' else "🤖 AI"
                    text = str(msg['text'])

                    f.write(f"{timestamp} | {msg_type}\n")
                    f.write(f"   {text}\n\n")

        print(f"\n💾 Conversations saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    get_recent_conversations()
