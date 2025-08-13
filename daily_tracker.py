import json
import os
import logging
from datetime import datetime
import pytz
from typing import Dict, Any

logger = logging.getLogger("daily_tracker")

# File path constants
DAILY_TRACKER_FILE_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\daily_tracker.json"


def load_tracker_data() -> Dict:
    """Loads daily tracker data, returning default on error or not found."""
    default_data = {"last_reset_date": "1970-01-01", "users": {}}
    try:
        tracker_dir = os.path.dirname(DAILY_TRACKER_FILE_PATH)
        if not os.path.exists(tracker_dir):
            try:
                os.makedirs(tracker_dir)
                logger.info(
                    f"Created directory for tracker file: {tracker_dir}")
                return default_data
            except OSError as ose:
                logger.error(f"Error creating directory {tracker_dir}: {ose}")
                return default_data

        with open(DAILY_TRACKER_FILE_PATH, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict) or 'last_reset_date' not in data or 'users' not in data:
                logger.warning(
                    f"Invalid structure in {DAILY_TRACKER_FILE_PATH}. Returning default.")
                return default_data.copy()
            logger.info(
                f"Loaded daily tracker data. Last reset: {data.get('last_reset_date')}")
            return data
    except FileNotFoundError:
        logger.info(
            f"{DAILY_TRACKER_FILE_PATH} not found. Returning default structure.")
        return default_data.copy()
    except json.JSONDecodeError:
        logger.error(
            f"Error decoding JSON from {DAILY_TRACKER_FILE_PATH}. Returning default.")
        return default_data.copy()
    except Exception as e:
        logger.error(
            f"Unexpected error loading tracker data: {e}", exc_info=True)
        return default_data.copy()


def save_tracker_data(data: Dict):
    """Saves the tracker data dictionary to the JSON file."""
    try:
        tracker_dir = os.path.dirname(DAILY_TRACKER_FILE_PATH)
        if not os.path.exists(tracker_dir):
            try:
                os.makedirs(tracker_dir)
                logger.info(
                    f"Created directory for tracker file: {tracker_dir}")
            except OSError as ose:
                logger.error(
                    f"Error creating directory {tracker_dir} before saving: {ose}")
                return

        with open(DAILY_TRACKER_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
            logger.info("Successfully saved tracker data")
    except IOError as e:
        logger.error(
            f"Error writing tracker data to {DAILY_TRACKER_FILE_PATH}: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error saving tracker data: {e}", exc_info=True)


async def reset_daily_tracker() -> bool:
    """Resets all users' daily tracking data and updates the last reset date."""
    try:
        tracker_data = load_tracker_data()
        melbourne_now = datetime.now(pytz.timezone('Australia/Melbourne'))
        new_reset_date = melbourne_now.strftime('%Y-%m-%d')

        # Create backup
        backup_path = DAILY_TRACKER_FILE_PATH.replace(
            '.json', f'_backup_{melbourne_now.strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(backup_path, 'w') as f:
                json.dump(tracker_data, f, indent=2)
            logger.info(f"Created backup of tracker data: {backup_path}")
        except Exception as backup_e:
            logger.warning(f"Failed to create backup before reset: {backup_e}")

        tracker_data['last_reset_date'] = new_reset_date

        # Reset daily counters while preserving totals
        for user_id, user_data in tracker_data['users'].items():
            current_daily = {
                'calories': user_data.get('daily_calories_tracked', 0)
            }

            # Update totals
            user_data['total_calories_tracked'] = user_data.get(
                'total_calories_tracked', 0) + current_daily['calories']

            # Reset daily counters
            user_data.update({
                'daily_calories_tracked': 0,
                'last_daily_update': new_reset_date
            })

        save_tracker_data(tracker_data)
        logger.info(
            f"Successfully reset daily tracker. New reset date: {new_reset_date}")
        return True

    except Exception as e:
        logger.error(f"Failed to reset daily tracker: {e}", exc_info=True)
        return False


async def check_and_reset_tracker() -> bool:
    """Checks if daily tracker needs to be reset and performs reset if needed."""
    try:
        tracker_data = load_tracker_data()
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        current_time = datetime.now(melbourne_tz)

        last_reset = tracker_data.get('last_reset_date', '1970-01-01')
        try:
            last_reset_dt = datetime.strptime(last_reset, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0)
            last_reset_dt = melbourne_tz.localize(last_reset_dt)
            current_midnight = current_time.replace(
                hour=0, minute=0, second=0, microsecond=0)

            if current_midnight > last_reset_dt:
                logger.info(
                    f"Daily tracker reset needed. Last reset: {last_reset}")
                return await reset_daily_tracker()
            else:
                logger.debug(f"No reset needed. Last reset: {last_reset}")
                return True

        except ValueError as e:
            logger.error(
                f"Error parsing last reset date ({last_reset}), forcing reset: {e}")
            return await reset_daily_tracker()

    except Exception as e:
        logger.error(
            f"Error checking tracker reset status: {e}", exc_info=True)
        return False


async def increment_daily_counter(user_id: str, counter_type: str, increment: int = 1) -> bool:
    """Increments a specific daily counter for a user."""
    try:
        await check_and_reset_tracker()
        tracker_data = load_tracker_data()

        if user_id not in tracker_data['users']:
            tracker_data['users'][user_id] = {
                'daily_calories_tracked': 0,
                'total_calories_tracked': 0,
                'last_daily_update': datetime.now(pytz.timezone('Australia/Melbourne')).strftime('%Y-%m-%d')
            }

        if counter_type != 'calories':
            logger.error(f"Invalid counter type: {counter_type}")
            return False

        user_data = tracker_data['users'][user_id]
        user_data['daily_calories_tracked'] = user_data.get(
            'daily_calories_tracked', 0) + increment

        save_tracker_data(tracker_data)
        logger.info(
            f"Incremented calories counter for user {user_id} by {increment}")
        return True

    except Exception as e:
        logger.error(f"Error incrementing daily counter: {e}", exc_info=True)
        return False
