import json
import logging
from datetime import datetime, timezone
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_analytics_data(file_path):
    """Load the existing analytics data file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading analytics data: {e}")
        return None


def save_analytics_data(data, file_path):
    """Save the updated analytics data file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving analytics data: {e}")
        return False


def determine_engagement_level(user_data):
    """Determine engagement level based on message count."""
    user_messages = user_data.get("user_messages", 0)
    if user_messages >= 51:
        return "High"
    elif user_messages >= 11:
        return "Medium"
    elif user_messages >= 1:
        return "Low"
    return "None"


def update_analytics_structure():
    """Update the analytics data structure while preserving existing data."""
    file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\analytics_data.json"

    # Load existing data
    data = load_analytics_data(file_path)
    if not data:
        logger.error("Failed to load analytics data")
        return False

    # Create backup
    backup_path = file_path.replace(
        '.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    save_analytics_data(data, backup_path)
    logger.info(f"Created backup at {backup_path}")

    try:
        # Get conversations data
        conversations = data.get("conversations", {})

        # Update each conversation's structure
        for user_id, user_data in conversations.items():
            metrics = user_data.get("metrics", {})

            # Add engagement level if not present
            if "engagement_level" not in metrics:
                metrics["engagement_level"] = determine_engagement_level(
                    metrics)

            # Add trial status structure if not present
            if "trial_status" not in metrics:
                metrics["trial_status"] = {
                    "onboarding_completed": False,
                    "onboarding_date": None,
                    "trial_start_date": None,
                    "is_paying": False,
                    "payment_date": None,
                    "satisfaction_checks": []
                }

            # Add check-ins structure if not present
            if "check_ins" not in metrics:
                metrics["check_ins"] = {
                    "last_day1_checkin": None,
                    "last_weekly_checkin": None,
                    "last_weekend_review": None
                }

            # Update metrics in user_data
            user_data["metrics"] = metrics
            conversations[user_id] = user_data

        # Update conversations in main data structure
        data["conversations"] = conversations

        # Save updated data
        if save_analytics_data(data, file_path):
            logger.info("Successfully updated analytics data structure")
            return True
        else:
            logger.error("Failed to save updated analytics data")
            return False

    except Exception as e:
        logger.error(f"Error updating analytics structure: {e}")
        return False


def verify_structure():
    """Verify the updated structure for all conversations."""
    file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\analytics_data.json"
    data = load_analytics_data(file_path)
    if not data:
        return False

    try:
        conversations = data.get("conversations", {})
        for user_id, user_data in conversations.items():
            metrics = user_data.get("metrics", {})

            # Check required fields
            required_fields = {
                "engagement_level": str,
                "trial_status": dict,
                "check_ins": dict
            }

            for field, field_type in required_fields.items():
                if field not in metrics:
                    logger.error(f"Missing field '{field}' for user {user_id}")
                    return False
                if not isinstance(metrics[field], field_type):
                    logger.error(
                        f"Invalid type for field '{field}' for user {user_id}")
                    return False

            # Check trial_status structure
            trial_status = metrics["trial_status"]
            required_trial_fields = {
                "onboarding_completed": bool,
                "onboarding_date": (type(None), str),
                "trial_start_date": (type(None), str),
                "is_paying": bool,
                "payment_date": (type(None), str),
                "satisfaction_checks": list
            }

            for field, field_type in required_trial_fields.items():
                if field not in trial_status:
                    logger.error(
                        f"Missing trial_status field '{field}' for user {user_id}")
                    return False
                if not isinstance(trial_status[field], field_type) and not (isinstance(field_type, tuple) and isinstance(trial_status[field], field_type[0])):
                    logger.error(
                        f"Invalid type for trial_status field '{field}' for user {user_id}")
                    return False

        logger.info("Structure verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during structure verification: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting analytics structure update...")

    if update_analytics_structure():
        logger.info("Update completed. Starting verification...")
        if verify_structure():
            logger.info("Structure verification passed. Update successful!")
        else:
            logger.error("Structure verification failed!")
    else:
        logger.error("Update failed!")
