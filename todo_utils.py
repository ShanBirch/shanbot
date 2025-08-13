import json
from datetime import datetime, timezone
import logging
import os

def add_todo_item(ig_username: str, client_name: str, task_description: str, status: str = "pending"):
    """Adds a 'to do' or completed action item to the analytics data file."""
    analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
    logger = logging.getLogger("manychat_webhook")
    log_prefix = "[add_todo_item]" if status == "pending" else "[log_completed_action]"
    logger.info(
        f"---> {log_prefix} Logging item for {ig_username}: {task_description} (Status: {status})")
    try:
        # 1. Read existing data
        try:
            with open(analytics_file_path, "r") as f:
                analytics_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(
                f"Could not load analytics data from {analytics_file_path} to add todo item. Initializing.")
            analytics_data = {"global_metrics": {}, "conversations": {
            }, "action_items": []}  # Initialize structure

        # 2. Ensure 'action_items' list exists
        if "action_items" not in analytics_data or not isinstance(analytics_data["action_items"], list):
            analytics_data["action_items"] = []
            logger.warning(
                "---> [add_todo_item] Initialized 'action_items' list.")

        # 3. Create and append new task
        new_task = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ig_username": ig_username,
            "client_name": client_name or ig_username,  # Use username as fallback
            "task_description": task_description,
            "status": status  # Use the provided status
        }
        analytics_data["action_items"].append(new_task)
        logger.info(f"---> {log_prefix} Appended new item.")

        # 4. Write back to file
        try:
            with open(analytics_file_path, "w") as f:
                json.dump(analytics_data, f, indent=2)
            logger.info(
                f"---> {log_prefix} Successfully saved updated analytics data.")
        except IOError as e:
            logger.error(
                f"---> {log_prefix} Error writing updated analytics data: {e}")

    except Exception as e:
        logger.error(f"---> {log_prefix} Unexpected error: {e}", exc_info=True) 