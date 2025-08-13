import json
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics_aggregator")


def aggregate_analytics():
    """Aggregate analytics from all user files into a global analytics file"""
    user_dir = Path(__file__).parent / 'app' / 'by_user'
    output_file = Path(__file__).parent / 'analytics_data.json'

    if not user_dir.exists():
        logger.error(f"User directory not found: {user_dir}")
        return

    global_metrics = {
        "total_users": 0,
        "total_messages": 0,
        "user_messages": 0,
        "ai_messages": 0,
        "coaching_inquiries": 0,
        "signups": 0,
        "questions_asked": 0,
        "user_responses": 0,
        "response_rate": 0,
        "users_with_ig": 0
    }

    conversation_metrics = {}
    processed = 0
    skipped = 0

    # Process each user file
    for file in user_dir.glob('user_*.json'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metrics = data.get('metrics', {}).get('metrics', {})

                # Only process users with Instagram usernames
                ig_username = metrics.get('ig_username')
                if ig_username:
                    global_metrics["users_with_ig"] += 1
                    global_metrics["total_users"] += 1

                    # Aggregate message counts
                    global_metrics["total_messages"] += metrics.get(
                        "total_messages", 0)
                    global_metrics["user_messages"] += metrics.get(
                        "user_messages", 0)
                    global_metrics["ai_messages"] += metrics.get(
                        "ai_messages", 0)

                    # Track engagement metrics
                    global_metrics["coaching_inquiries"] += metrics.get(
                        "coaching_inquiry_count", 0)
                    global_metrics["signups"] += 1 if metrics.get(
                        "signup_recorded", False) else 0
                    global_metrics["questions_asked"] += metrics.get(
                        "ai_questions", 0)
                    global_metrics["user_responses"] += metrics.get(
                        "user_responses_to_ai_question", 0)

                    # Store individual metrics
                    conversation_metrics[ig_username] = {
                        "metrics": metrics,
                        "conversation_history": metrics.get("conversation_history", [])
                    }

                    processed += 1
                else:
                    skipped += 1

        except Exception as e:
            logger.error(f"Error processing file {file.name}: {e}")
            skipped += 1
            continue

    # Calculate response rate
    if global_metrics["questions_asked"] > 0:
        global_metrics["response_rate"] = (
            global_metrics["user_responses"] / global_metrics["questions_asked"]) * 100

    # Create final analytics data
    analytics_data = {
        "global_metrics": global_metrics,
        "conversation_metrics": conversation_metrics
    }

    # Write to file with UTF-8 encoding
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2, ensure_ascii=False)
        logger.info(
            f"Successfully processed {processed} users ({skipped} skipped)")
        logger.info(f"Analytics data written to {output_file}")
        logger.info(f"Global metrics: {global_metrics}")
    except Exception as e:
        logger.error(f"Error writing analytics file: {e}")


if __name__ == "__main__":
    aggregate_analytics()
