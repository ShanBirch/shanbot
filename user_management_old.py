"""User management and analytics functions."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import requests
from pathlib import Path
import re

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
ANALYTICS_FILE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
CHECKIN_REVIEWS_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"


def update_manychat_fields(subscriber_id: str, field_updates: Dict[str, str]) -> bool:
    """Update custom fields in ManyChat for a subscriber"""
    # Filter out None and empty string values
    filtered_updates = {
        k: v for k, v in field_updates.items() if v is not None and v != ""}
    if not filtered_updates:
        logger.info("No valid field updates to send to ManyChat.")
        return True  # Nothing to update, consider it success

    # Prepare the data using field_name
    field_data = [
        {"field_name": field_name, "field_value": value}
        for field_name, value in filtered_updates.items()
    ]
    data = {
        "subscriber_id": subscriber_id,
        "fields": field_data
    }

    headers = {
        "Authorization": f"Bearer {MANYCHAT_API_KEY}",
        "Content-Type": "application/json"
    }

    logger.info(
        f"Attempting to update ManyChat fields for subscriber {subscriber_id}: {list(filtered_updates.keys())}")
    logger.info(f"ManyChat API Request Payload: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            "https://api.manychat.com/fb/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )
        logger.info(
            f"ManyChat API response: {response.status_code} - {response.text[:500]}")
        response.raise_for_status()
        logger.info(
            f"Successfully updated ManyChat fields for subscriber {subscriber_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error updating ManyChat fields for subscriber {subscriber_id}: {e}", exc_info=True)
        if hasattr(e, 'response') and e.response is not None:
            logger.error(
                f"ManyChat Error Response Body: {e.response.text[:500]}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during ManyChat field update for {subscriber_id}: {e}", exc_info=True)
        return False


def update_analytics_data(
    ig_username: str,
    user_message: str,
    ai_response: str,
    subscriber_id: str,
    first_name: str,
    last_name: str,
    set_checkin_flow_false: Optional[bool] = None
) -> None:
    """Update analytics data for a user."""
    logger.info(
        f"---> [update_analytics_data] Attempting to update/create history for '{ig_username}' (ID: {subscriber_id})")

    try:
        # Read existing data
        try:
            with open(ANALYTICS_FILE_PATH, "r") as f:
                analytics_data = json.load(f)
                logger.info(
                    f"---> [update_analytics_data] Read existing data from {ANALYTICS_FILE_PATH}")
        except FileNotFoundError:
            logger.warning(
                f"---> [update_analytics_data] {ANALYTICS_FILE_PATH} not found. Creating new structure.")
            analytics_data = {"global_metrics": {}, "conversations": {}}
        except json.JSONDecodeError:
            logger.error(
                f"---> [update_analytics_data] Error decoding {ANALYTICS_FILE_PATH}. Cannot update.")
            return

        # Find or create user data
        conversations_data = analytics_data.get('conversations', {})
        if not isinstance(conversations_data, dict):
            logger.error(
                "---> [update_analytics_data] 'conversations' key is not a dictionary. Resetting.")
            conversations_data = {}
            analytics_data['conversations'] = conversations_data

        target_user_id = None
        target_user_data = None
        search_ig_username_lower = ig_username.strip().lower()

        # Search for existing user
        for user_id, user_data in conversations_data.items():
            if isinstance(user_data, dict):
                metrics_data = user_data.get("metrics", {})
                if isinstance(metrics_data, dict):
                    json_ig_username = metrics_data.get("ig_username", None)
                    if isinstance(json_ig_username, str) and json_ig_username.strip().lower() == search_ig_username_lower:
                        target_user_id = user_id
                        target_user_data = user_data
                        logger.info(
                            f"---> [update_analytics_data] Found user '{ig_username}' with ID '{target_user_id}'")
                        break

        current_timestamp_iso = datetime.now(timezone.utc).isoformat()

        # Create new user if not found
        if not target_user_id:
            logger.info(
                f"---> [update_analytics_data] User '{ig_username}' not found. Creating new profile.")
            target_user_id = subscriber_id
            target_user_data = {
                "metrics": {
                    "ig_username": ig_username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "conversation_history": [],
                    "journey_stage": {"current_stage": "Topic 1"},
                    "client_analysis": {
                        "profile_bio": "",
                        "interests": [],
                        "conversation_topics": []
                    },
                    "client_details": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "sex": "",
                        "fitness_goals": "",
                        "dietary_requirements": "",
                        "training_frequency": ""
                    },
                    "trial_week_1": False,
                    "is_in_checkin_flow": False,
                    "calorie_tracking": {
                        "daily_target": 2000,
                        "current_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "calories_consumed": 0,
                        "remaining_calories": 2000,
                        "macros": {
                            "protein": {"daily_target": 180, "consumed": 0, "remaining": 180},
                            "carbs": {"daily_target": 250, "consumed": 0, "remaining": 250},
                            "fats": {"daily_target": 65, "consumed": 0, "remaining": 65}
                        },
                        "meals_today": []
                    },
                    "first_message_timestamp": current_timestamp_iso,
                    "last_message_timestamp": current_timestamp_iso
                }
            }
            conversations_data[target_user_id] = target_user_data

        # Update conversation history
        if "metrics" not in target_user_data:
            target_user_data["metrics"] = {}
        metrics_dict = target_user_data["metrics"]

        if "conversation_history" not in metrics_dict:
            metrics_dict["conversation_history"] = []
        history_list = metrics_dict["conversation_history"]

        # Add messages to history
        if user_message:
            history_list.append({
                "timestamp": current_timestamp_iso,
                "type": "user",
                "text": user_message
            })

        if ai_response:
            history_list.append({
                "timestamp": current_timestamp_iso,
                "type": "ai",
                "text": ai_response
            })

        # Update timestamps
        metrics_dict["last_message_timestamp"] = current_timestamp_iso
        if not metrics_dict.get("first_message_timestamp"):
            metrics_dict["first_message_timestamp"] = current_timestamp_iso

        # Handle check-in flow reset
        if set_checkin_flow_false is True:
            metrics_dict['is_in_checkin_flow'] = False
            if 'checkin_type' in metrics_dict:
                metrics_dict['checkin_type'] = None

        # Save updated data
        try:
            with open(ANALYTICS_FILE_PATH, "w") as f:
                json.dump(analytics_data, f, indent=2)
                logger.info(
                    f"---> [update_analytics_data] Successfully wrote updated data")
        except IOError as e:
            logger.error(
                f"---> [update_analytics_data] Error writing to file: {e}")

    except Exception as e:
        logger.error(
            f"---> [update_analytics_data] Unexpected error during update: {e}", exc_info=True)


def find_latest_checkin_file(full_name: str) -> Optional[str]:
    """Find the latest check-in JSON file for a given full name."""
    try:
        if not full_name or not isinstance(full_name, str):
            logger.error(
                "[find_latest_checkin_file] Invalid full_name provided.")
            return None

        logger.info(
            f"[find_latest_checkin_file] Checking existence with os.path.exists for: {CHECKIN_REVIEWS_DIR}")
        if not os.path.exists(CHECKIN_REVIEWS_DIR):
            logger.error(
                f"[find_latest_checkin_file] os.path.exists failed for directory: {CHECKIN_REVIEWS_DIR}")
            return None

        checkin_dir_path = Path(CHECKIN_REVIEWS_DIR)
        if not checkin_dir_path.is_dir():
            logger.error(
                f"[find_latest_checkin_file] Check-in directory not found: {CHECKIN_REVIEWS_DIR}")
            return None

        # Try standard name order
        safe_name = full_name.replace(' ', '_').lower()
        filename_pattern = f"{safe_name}_*_fitness_wrapped_data.json"
        logger.info(
            f"[find_latest_checkin_file] Searching pattern for '{full_name}': {checkin_dir_path / filename_pattern}")
        files = list(checkin_dir_path.glob(filename_pattern))

        # Try swapped name order if no files found
        if not files:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                swapped_name = f"{name_parts[-1]} {name_parts[0]}"
                safe_name_swapped = swapped_name.replace(' ', '_').lower()
                filename_pattern_swapped = f"{safe_name_swapped}_*_fitness_wrapped_data.json"
                logger.info(
                    f"[find_latest_checkin_file] Trying swapped pattern for '{full_name}': {checkin_dir_path / filename_pattern_swapped}")
                files = list(checkin_dir_path.glob(filename_pattern_swapped))

        if not files:
            logger.warning(
                f"[find_latest_checkin_file] No check-in files found for '{full_name}' matching patterns.")
            return None

        # Extract dates and sort
        dated_files = []
        for f_path in files:
            try:
                filename = os.path.basename(f_path)
                date_str_match = re.search(r'_(\d{4}-\d{2}-\d{2})_', filename)
                if date_str_match:
                    date_str = date_str_match.group(1)
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    dated_files.append((file_date, f_path))
                else:
                    logger.warning(
                        f"[find_latest_checkin_file] Could not parse YYYY-MM-DD date from filename: {filename}")
            except (ValueError, IndexError, AttributeError) as e:
                logger.warning(
                    f"[find_latest_checkin_file] Error parsing date from file {f_path}: {e}")

        if not dated_files:
            logger.error(
                f"[find_latest_checkin_file] No files with parseable dates found for '{full_name}'")
            return None

        dated_files.sort(key=lambda x: x[0], reverse=True)
        latest_file_str = str(dated_files[0][1])
        logger.info(
            f"[find_latest_checkin_file] Found latest check-in file for '{full_name}': {latest_file_str}")
        return latest_file_str

    except Exception as e:
        logger.error(
            f"[find_latest_checkin_file] Error finding latest check-in file for '{full_name}': {e}", exc_info=True)
        return None


def load_json_data(file_path: str) -> Optional[Dict]:
    """Safely load JSON data from a file."""
    if not file_path or not os.path.exists(file_path):
        logger.error(
            f"[load_json_data] File not found or path is invalid: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info(
                f"[load_json_data] Successfully loaded JSON data from: {file_path}")
            return data
    except json.JSONDecodeError as e:
        logger.error(
            f"[load_json_data] Failed to decode JSON from {file_path}: {e}")
        return None
    except FileNotFoundError:
        logger.error(f"[load_json_data] File not found error for: {file_path}")
        return None
    except Exception as e:
        logger.error(
            f"[load_json_data] Unexpected error loading JSON from {file_path}: {e}", exc_info=True)
        return None


def format_conversation_history(history_list: List[Dict[str, str]]) -> str:
    """Formats the conversation history list into a readable string."""
    formatted_lines = []
    for entry in history_list:
        timestamp = entry.get("timestamp", "")
        msg_type = entry.get("type", "unknown").capitalize()
        text = entry.get("text", "")
        try:
            dt_object = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00"))
            formatted_ts = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_ts = timestamp

        formatted_lines.append(f"{formatted_ts} [{msg_type}]: {text}")
    return "\n".join(formatted_lines)
