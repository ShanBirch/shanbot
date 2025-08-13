import json
import os
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_directory(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def load_analytics_data():
    """Load the analytics data from JSON file"""
    analytics_file = "analytics_data.json"
    try:
        with open(analytics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(
                f"Successfully loaded analytics data from {analytics_file}")
            return data
    except FileNotFoundError:
        logger.error(f"Analytics file not found: {analytics_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding analytics file: {e}")
        return None


def create_user_file(user_id, user_data, output_dir):
    """Create individual JSON file for a user"""
    filename = f"user_{user_id}.json"
    file_path = os.path.join(output_dir, filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Created user file: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error creating file for user {user_id}: {e}")
        return False


def split_analytics():
    """Split analytics data into individual user files"""
    # Load analytics data
    analytics_data = load_analytics_data()
    if not analytics_data:
        logger.error("Failed to load analytics data")
        return

    # Create output directory
    output_dir = "by_user"
    ensure_directory(output_dir)

    # Get conversation metrics
    conversation_metrics = analytics_data.get('conversation_metrics', {})
    if not conversation_metrics:
        logger.error("No conversation metrics found in analytics data")
        return

    # Track statistics
    total_users = 0
    successful_writes = 0
    users_with_ig = 0
    users_with_bio = 0
    users_with_convos = 0

    # Process each user
    for user_id, user_data in conversation_metrics.items():
        # Only process users with Instagram usernames
        ig_username = user_data.get('ig_username')
        if not ig_username:
            continue

        total_users += 1
        users_with_ig += 1

        # Count users with bio and conversations
        if user_data.get('bio'):
            users_with_bio += 1
        if user_data.get('conversation_history'):
            users_with_convos += 1

        # Ensure we have the basic user data structure
        user_file_data = {
            'ig_username': ig_username,
            'metrics': {
                'total_messages': user_data.get('total_messages', 0),
                'user_messages': user_data.get('user_messages', 0),
                'ai_messages': user_data.get('ai_messages', 0),
                'ai_questions': user_data.get('ai_questions', 0),
                'user_responses_to_ai_question': user_data.get('user_responses_to_ai_question', 0),
                'question_response_rate': user_data.get('question_response_rate', 0),
                'avg_response_time': user_data.get('avg_response_time', 0)
            },
            'bio': user_data.get('bio', ''),
            'interests': user_data.get('interests', []),
            'personality_traits': user_data.get('personality_traits', []),
            'conversation_history': user_data.get('conversation_history', []),
            'has_bio': bool(user_data.get('bio')),
            'has_conversations': bool(user_data.get('conversation_history'))
        }

        # Create user file
        if create_user_file(ig_username, user_file_data, output_dir):
            successful_writes += 1

    # Log summary
    logger.info(f"""
Split Analytics Summary:
----------------------
Total users processed: {total_users}
Users with Instagram usernames: {users_with_ig}
Users with bios: {users_with_bio}
Users with conversations: {users_with_convos}
Successful writes: {successful_writes}
Failed writes: {total_users - successful_writes}
Output directory: {os.path.abspath(output_dir)}
""")


if __name__ == "__main__":
    split_analytics()
