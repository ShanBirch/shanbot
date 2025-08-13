#!/usr/bin/env python3
"""
Extract conversation data from the actual conversation tables
Found conversations in response_review_queue and scheduled_responses tables
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


def extract_conversations_from_all_tables():
    """Extract conversations from all available tables"""

    conn = get_db_connection()
    conversations = []

    try:
        cursor = conn.cursor()

        # Extract from response_review_queue
        logger.info("Extracting from response_review_queue...")
        cursor.execute("""
            SELECT 
                user_ig_username,
                incoming_message_text,
                proposed_response_text,
                incoming_message_timestamp,
                status,
                'review_queue' as source
            FROM response_review_queue
            ORDER BY incoming_message_timestamp DESC
        """)

        review_queue_data = cursor.fetchall()
        logger.info(
            f"Found {len(review_queue_data)} conversations in response_review_queue")

        for row in review_queue_data:
            conversations.append({
                'username': row['user_ig_username'],
                'user_message': row['incoming_message_text'],
                'ai_response': row['proposed_response_text'],
                'timestamp': row['incoming_message_timestamp'],
                'status': row['status'],
                'source': row['source']
            })

        # Extract from scheduled_responses
        logger.info("Extracting from scheduled_responses...")
        cursor.execute("""
            SELECT 
                user_ig_username,
                incoming_message_text,
                response_text,
                incoming_message_timestamp,
                status,
                'scheduled' as source
            FROM scheduled_responses
            ORDER BY incoming_message_timestamp DESC
        """)

        scheduled_data = cursor.fetchall()
        logger.info(
            f"Found {len(scheduled_data)} conversations in scheduled_responses")

        for row in scheduled_data:
            conversations.append({
                'username': row['user_ig_username'],
                'user_message': row['incoming_message_text'],
                'ai_response': row['response_text'],
                'timestamp': row['incoming_message_timestamp'],
                'status': row['status'],
                'source': row['source']
            })

        logger.info(f"Total conversations extracted: {len(conversations)}")
        return conversations

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def analyze_conversation_capabilities(conversations):
    """Analyze Shanbot's conversation capabilities"""

    if not conversations:
        logger.info("No conversations found")
        return {}

    # Sort by timestamp
    conversations.sort(key=lambda x: x['timestamp'], reverse=True)

    analysis = {
        'total_conversations': len(conversations),
        'unique_users': len(set(c['username'] for c in conversations)),
        'data_sources': {
            'review_queue': len([c for c in conversations if c['source'] == 'review_queue']),
            'scheduled': len([c for c in conversations if c['source'] == 'scheduled'])
        },
        'time_range': {
            'latest': conversations[0]['timestamp'] if conversations else 'N/A',
            'earliest': conversations[-1]['timestamp'] if conversations else 'N/A'
        }
    }

    # Group by user
    user_conversations = {}
    for conv in conversations:
        username = conv['username']
        if username not in user_conversations:
            user_conversations[username] = []
        user_conversations[username].append(conv)

    analysis['user_conversations'] = user_conversations

    # Analyze AI response lengths
    ai_responses = [c['ai_response']
                    for c in conversations if c['ai_response']]
    if ai_responses:
        word_counts = [len(response.split()) for response in ai_responses]
        analysis['ai_response_stats'] = {
            'total_responses': len(ai_responses),
            'avg_words': sum(word_counts) / len(word_counts),
            'max_words': max(word_counts),
            'min_words': min(word_counts),
            'responses_over_15_words': len([wc for wc in word_counts if wc > 15]),
            'responses_under_5_words': len([wc for wc in word_counts if wc < 5])
        }

    # Get most active users
    user_activity = [(username, len(convs))
                     for username, convs in user_conversations.items()]
    user_activity.sort(key=lambda x: x[1], reverse=True)
    analysis['most_active_users'] = user_activity[:10]

    return analysis


def save_conversation_data(conversations, analysis):
    """Save conversation data and analysis to files"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw conversation data
    conversations_file = f"shanbot_conversations_{timestamp}.json"
    with open(conversations_file, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)

    # Save analysis
    analysis_file = f"shanbot_analysis_{timestamp}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # Save human-readable report
    report_file = f"shanbot_capability_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("SHANBOT CONVERSATION CAPABILITY ANALYSIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(
            f"Analysis generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("OVERVIEW:\n")
        f.write(f"- Total conversations: {analysis['total_conversations']}\n")
        f.write(f"- Unique users: {analysis['unique_users']}\n")
        f.write(f"- Data sources: {analysis['data_sources']}\n")
        f.write(
            f"- Time range: {analysis['time_range']['earliest']} to {analysis['time_range']['latest']}\n\n")

        if 'ai_response_stats' in analysis:
            stats = analysis['ai_response_stats']
            f.write("AI RESPONSE ANALYSIS:\n")
            f.write(f"- Total AI responses: {stats['total_responses']}\n")
            f.write(
                f"- Average words per response: {stats['avg_words']:.1f}\n")
            f.write(f"- Longest response: {stats['max_words']} words\n")
            f.write(f"- Shortest response: {stats['min_words']} words\n")
            f.write(
                f"- Responses over 15 words: {stats['responses_over_15_words']} ({stats['responses_over_15_words']/stats['total_responses']*100:.1f}%)\n")
            f.write(
                f"- Responses under 5 words: {stats['responses_under_5_words']} ({stats['responses_under_5_words']/stats['total_responses']*100:.1f}%)\n\n")

        f.write("MOST ACTIVE USERS:\n")
        for username, count in analysis['most_active_users']:
            f.write(f"- {username}: {count} conversations\n")

        f.write("\n" + "="*60 + "\n")
        f.write("SAMPLE CONVERSATIONS:\n")
        f.write("="*60 + "\n\n")

        # Show sample conversations from top users
        sample_count = 0
        for username, user_convs in analysis['user_conversations'].items():
            if sample_count >= 5:  # Limit to 5 users
                break

            f.write(f"\nUSER: {username} ({len(user_convs)} conversations)\n")
            f.write("-" * 40 + "\n")

            # Show most recent 3 conversations for this user
            recent_convs = sorted(
                user_convs, key=lambda x: x['timestamp'], reverse=True)[:3]
            for i, conv in enumerate(recent_convs, 1):
                f.write(f"\nConversation {i} ({conv['timestamp']}):\n")
                f.write(f"USER: {conv['user_message']}\n")
                f.write(f"SHANBOT: {conv['ai_response']}\n")
                f.write(
                    f"(Source: {conv['source']}, Status: {conv['status']})\n")

            sample_count += 1

    logger.info(f"Saved conversation data to: {conversations_file}")
    logger.info(f"Saved analysis to: {analysis_file}")
    logger.info(f"Saved report to: {report_file}")

    return conversations_file, analysis_file, report_file


def main():
    """Main function to extract and analyze conversation data"""

    logger.info("Starting Shanbot conversation analysis...")

    try:
        # Extract conversations from all available tables
        conversations = extract_conversations_from_all_tables()

        # Analyze the data
        analysis = analyze_conversation_capabilities(conversations)

        # Save to files
        conv_file, analysis_file, report_file = save_conversation_data(
            conversations, analysis)

        logger.info("Analysis complete!")
        logger.info(
            f"Files created: {conv_file}, {analysis_file}, {report_file}")

        # Print quick summary
        print("\n" + "="*60)
        print("SHANBOT CONVERSATION CAPABILITY SUMMARY")
        print("="*60)
        print(f"Total conversations: {analysis['total_conversations']}")
        print(f"Unique users: {analysis['unique_users']}")
        print(f"Data sources: {analysis['data_sources']}")

        if 'ai_response_stats' in analysis:
            stats = analysis['ai_response_stats']
            print(f"AI responses: {stats['total_responses']}")
            print(f"Avg words per response: {stats['avg_words']:.1f}")
            print(
                f"Responses over 15 words: {stats['responses_over_15_words']} ({stats['responses_over_15_words']/stats['total_responses']*100:.1f}%)")

        print(f"\nMost active users:")
        for username, count in analysis['most_active_users'][:5]:
            print(f"  - {username}: {count} conversations")

        print(f"\nDetailed report saved to: {report_file}")
        print("="*60)

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()
