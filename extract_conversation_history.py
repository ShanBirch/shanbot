#!/usr/bin/env python3
"""
Extract conversation history from the last 24 hours for analysis
This script connects to the SQLite database and extracts all conversations
from the last 24 hours to analyze Shanbot's conversation capabilities.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path - using same logic as dashboard_sqlite_utils.py


def get_db_path():
    """Get the database path with fallback logic"""
    # Try relative path first
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))
    db_path = os.path.join(app_dir, "analytics_data_good.sqlite")

    if os.path.exists(db_path):
        return db_path

    # Try finding shanbot directory
    current_dir = Path(os.getcwd())
    for parent in [current_dir] + list(current_dir.parents):
        if parent.name.lower() == "shanbot":
            db_path = os.path.join(
                str(parent), "app", "analytics_data_good.sqlite")
            if os.path.exists(db_path):
                return db_path

    # Fallback to known absolute path
    fallback_path = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite"
    if os.path.exists(fallback_path):
        return fallback_path

    raise FileNotFoundError("Could not find the SQLite database file")


def get_db_connection():
    """Get database connection"""
    db_path = get_db_path()
    logger.info(f"Using database: {db_path}")

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise


def extract_last_24h_conversations():
    """Extract all conversations from the last 7 days (expanded from 24h to ensure we get data)"""

    # Calculate 7 days ago to ensure we get some data
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    logger.info(
        f"Extracting conversations from {seven_days_ago} to {now}")

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Query for conversations in the last 7 days
        query = """
        SELECT 
            history_id,
            ig_username,
            message_type,
            message_text,
            timestamp
        FROM conversation_history
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp ASC
        """

        cursor.execute(query)
        conversations = cursor.fetchall()

        logger.info(
            f"Found {len(conversations)} messages in the last 7 days")

        # Convert to list of dictionaries for easy analysis
        conversation_data = []
        for row in conversations:
            conversation_data.append({
                'history_id': row['history_id'],
                'ig_username': row['ig_username'],
                'message_type': row['message_type'],  # 'user' or 'ai'
                'message_text': row['message_text'],
                'timestamp': row['timestamp']
            })

        return conversation_data

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def analyze_conversation_capabilities(conversations):
    """Analyze conversation capabilities from the data"""

    # Always return basic structure, even if no conversations
    analysis = {
        'total_messages': len(conversations),
        'users_count': len(set(c['ig_username'] for c in conversations)) if conversations else 0,
        'ai_responses': len([c for c in conversations if c['message_type'] == 'ai']),
        'user_messages': len([c for c in conversations if c['message_type'] == 'user']),
        'time_range': {
            'start': min(c['timestamp'] for c in conversations) if conversations else 'N/A',
            'end': max(c['timestamp'] for c in conversations) if conversations else 'N/A'
        }
    }

    if not conversations:
        logger.info("No conversations found in the specified time period")
        return analysis

    # Group conversations by user
    user_conversations = {}
    for conv in conversations:
        username = conv['ig_username']
        if username not in user_conversations:
            user_conversations[username] = []
        user_conversations[username].append(conv)

    analysis['user_conversations'] = user_conversations

    # Response length analysis for AI messages
    ai_messages = [c for c in conversations if c['message_type'] == 'ai']
    if ai_messages:
        word_counts = [len(c['message_text'].split()) for c in ai_messages]
        analysis['ai_response_stats'] = {
            'avg_words': sum(word_counts) / len(word_counts),
            'max_words': max(word_counts),
            'min_words': min(word_counts),
            'total_responses': len(ai_messages)
        }

    return analysis


def save_conversation_data(conversations, analysis):
    """Save conversation data and analysis to files"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw conversation data
    conversations_file = f"conversation_history_{timestamp}.json"
    with open(conversations_file, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    # Save analysis
    analysis_file = f"conversation_analysis_{timestamp}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # Save human-readable summary
    summary_file = f"conversation_summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("SHANBOT CONVERSATION ANALYSIS - LAST 7 DAYS\n")
        f.write("=" * 50 + "\n\n")
        f.write(
            f"Analysis generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("SUMMARY STATISTICS:\n")
        f.write(f"- Total messages: {analysis['total_messages']}\n")
        f.write(f"- Unique users: {analysis['users_count']}\n")
        f.write(f"- AI responses: {analysis['ai_responses']}\n")
        f.write(f"- User messages: {analysis['user_messages']}\n")
        f.write(
            f"- Time range: {analysis['time_range']['start']} to {analysis['time_range']['end']}\n\n")

        if 'ai_response_stats' in analysis:
            stats = analysis['ai_response_stats']
            f.write("AI RESPONSE ANALYSIS:\n")
            f.write(
                f"- Average words per response: {stats['avg_words']:.1f}\n")
            f.write(f"- Max words in response: {stats['max_words']}\n")
            f.write(f"- Min words in response: {stats['min_words']}\n")
            f.write(f"- Total AI responses: {stats['total_responses']}\n\n")

        f.write("CONVERSATIONS BY USER:\n")
        for username, user_convs in analysis['user_conversations'].items():
            f.write(f"\n{username} ({len(user_convs)} messages):\n")
            for conv in user_convs:
                f.write(
                    f"  [{conv['timestamp']}] {conv['message_type'].upper()}: {conv['message_text']}\n")

    logger.info(f"Saved conversation data to: {conversations_file}")
    logger.info(f"Saved analysis to: {analysis_file}")
    logger.info(f"Saved summary to: {summary_file}")

    return conversations_file, analysis_file, summary_file


def main():
    """Main function to extract and analyze conversation history"""

    logger.info("Starting conversation history extraction...")

    try:
        # Extract conversations
        conversations = extract_last_24h_conversations()

        # Analyze the data
        analysis = analyze_conversation_capabilities(conversations)

        # Save to files
        conv_file, analysis_file, summary_file = save_conversation_data(
            conversations, analysis)

        logger.info("Extraction complete!")
        logger.info(
            f"Files created: {conv_file}, {analysis_file}, {summary_file}")

        # Print quick summary
        print("\n" + "="*50)
        print("QUICK SUMMARY:")
        print(f"Total messages: {analysis['total_messages']}")
        print(f"Unique users: {analysis['users_count']}")
        print(f"AI responses: {analysis['ai_responses']}")
        print(f"User messages: {analysis['user_messages']}")

        if 'ai_response_stats' in analysis:
            print(
                f"Avg words per AI response: {analysis['ai_response_stats']['avg_words']:.1f}")

        print(f"\nDetailed analysis saved to: {summary_file}")
        print("="*50)

    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        raise


if __name__ == "__main__":
    main()
