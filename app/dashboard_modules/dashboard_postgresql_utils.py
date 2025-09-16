# app/dashboard_modules/dashboard_postgresql_utils.py (cloud deployment)
import logging
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("shanbot_db_postgres")


def get_db_connection():
    """Get PostgreSQL database connection from environment variable."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not found - using stub mode")
        return None

    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None


def init_database():
    """Initialize PostgreSQL tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    ig_username VARCHAR(255) UNIQUE NOT NULL,
                    subscriber_id VARCHAR(255),
                    metrics_json JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    ig_username VARCHAR(255) NOT NULL,
                    message_type VARCHAR(100) NOT NULL,
                    message_text TEXT NOT NULL,
                    message_timestamp VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create review_queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_queue (
                    review_id SERIAL PRIMARY KEY,
                    user_ig_username VARCHAR(255) NOT NULL,
                    user_subscriber_id VARCHAR(255),
                    incoming_message_text TEXT,
                    incoming_message_timestamp VARCHAR(255),
                    generated_prompt_text TEXT,
                    proposed_response_text TEXT,
                    prompt_type VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'pending_review',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create nutrition_targets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nutrition_targets (
                    id SERIAL PRIMARY KEY,
                    ig_username VARCHAR(255) UNIQUE NOT NULL,
                    targets_json JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Database tables initialized successfully")
            return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def add_response_to_review_queue(user_ig_username: str, user_subscriber_id: str,
                                 incoming_message_text: str, incoming_message_timestamp: str,
                                 generated_prompt_text: str, proposed_response_text: str,
                                 prompt_type: str, status: str = 'pending_review') -> Optional[int]:
    """Add response to review queue."""
    conn = get_db_connection()
    if not conn:
        logger.info(
            f"Stub: Adding response to review queue for {user_ig_username} (status: {status})")
        return 1

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO review_queue 
                (user_ig_username, user_subscriber_id, incoming_message_text, incoming_message_timestamp,
                 generated_prompt_text, proposed_response_text, prompt_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING review_id
            """, (user_ig_username, user_subscriber_id, incoming_message_text, incoming_message_timestamp,
                  generated_prompt_text, proposed_response_text, prompt_type, status))

            review_id = cursor.fetchone()['review_id']
            conn.commit()
            logger.info(
                f"Added response to review queue for {user_ig_username} with ID {review_id}")
            return review_id

    except Exception as e:
        logger.error(f"Failed to add response to review queue: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def add_message_to_history(ig_username: str, message_type: str, message_text: str, message_timestamp: str):
    """Add message to history."""
    conn = get_db_connection()
    if not conn:
        logger.info(
            f"Stub: Adding message to history for {ig_username} (type: {message_type})")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO messages (ig_username, message_type, message_text, message_timestamp)
                VALUES (%s, %s, %s, %s)
            """, (ig_username, message_type, message_text, message_timestamp))

            conn.commit()
            logger.info(f"Added message to history for {ig_username}")

    except Exception as e:
        logger.error(f"Failed to add message to history: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_nutrition_targets(ig_username: str) -> Optional[Dict]:
    """Get nutrition targets for user."""
    conn = get_db_connection()
    if not conn:
        logger.info(f"Stub: Getting nutrition targets for {ig_username}")
        return {}

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT targets_json FROM nutrition_targets WHERE ig_username = %s
            """, (ig_username,))

            row = cursor.fetchone()
            return row['targets_json'] if row else None

    except Exception as e:
        logger.error(f"Failed to get nutrition targets: {e}")
        return None
    finally:
        conn.close()


def upsert_nutrition_targets(ig_username: str, targets: Dict):
    """Upsert nutrition targets for user."""
    conn = get_db_connection()
    if not conn:
        logger.info(
            f"Stub: Upserting nutrition targets for {ig_username}: {targets}")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO nutrition_targets (ig_username, targets_json, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (ig_username) 
                DO UPDATE SET targets_json = EXCLUDED.targets_json, updated_at = CURRENT_TIMESTAMP
            """, (ig_username, json.dumps(targets)))

            conn.commit()
            logger.info(f"Upserted nutrition targets for {ig_username}")

    except Exception as e:
        logger.error(f"Failed to upsert nutrition targets: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_user_metrics_json(ig_username: str) -> Optional[Dict]:
    """Get user metrics."""
    conn = get_db_connection()
    if not conn:
        logger.info(f"Stub: Getting user metrics for {ig_username}")
        return {}

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT metrics_json FROM users WHERE ig_username = %s
            """, (ig_username,))

            row = cursor.fetchone()
            return row['metrics_json'] if row else {}

    except Exception as e:
        logger.error(f"Failed to get user metrics: {e}")
        return {}
    finally:
        conn.close()


def set_user_metrics_json_field(ig_username: str, field: str, value: Any):
    """Set specific field in user metrics."""
    conn = get_db_connection()
    if not conn:
        logger.info(
            f"Stub: Setting user metric field {field} for {ig_username} to {value}")
        return

    try:
        with conn.cursor() as cursor:
            # Upsert user record and update specific field
            cursor.execute("""
                INSERT INTO users (ig_username, metrics_json, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (ig_username) 
                DO UPDATE SET 
                    metrics_json = COALESCE(users.metrics_json, '{}') || %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (ig_username, json.dumps({field: value}), json.dumps({field: value})))

            conn.commit()
            logger.info(f"Set user metric field {field} for {ig_username}")

    except Exception as e:
        logger.error(f"Failed to set user metric field: {e}")
        conn.rollback()
    finally:
        conn.close()


def user_has_nutrition_profile(ig_username: str) -> bool:
    """Check if user has nutrition profile."""
    metrics = get_user_metrics_json(ig_username)
    nutrition = metrics.get('nutrition_profile', {}) if metrics else {}
    return bool(nutrition and nutrition.get('weight_kg') and nutrition.get('height_cm'))


def set_user_in_calorie_flow(ig_username: str, in_flow: bool):
    """Set user's calorie flow status."""
    set_user_metrics_json_field(ig_username, 'is_in_calorie_flow', in_flow)


def is_user_in_calorie_flow(ig_username: str) -> bool:
    """Check if user is in calorie flow."""
    metrics = get_user_metrics_json(ig_username)
    return metrics.get('is_in_calorie_flow', False) if metrics else False


def upsert_user_nutrition_profile(ig_username: str, sex: Optional[str], dob: Optional[str],
                                  age: Optional[int], height_cm: Optional[int], weight_kg: Optional[int],
                                  activity_level: Optional[str], main_goal: Optional[str]):
    """Upsert user nutrition profile."""
    profile = {
        'sex': sex,
        'dob': dob,
        'age': age,
        'height_cm': height_cm,
        'weight_kg': weight_kg,
        'activity_level': activity_level,
        'main_goal': main_goal
    }
    set_user_metrics_json_field(ig_username, 'nutrition_profile', profile)


def log_meal_and_update_calorie_tracking(ig_username: str, meal_description: str, calories: int, protein: int, carbs: int, fats: int):
    """Log meal and update daily calorie tracking."""
    conn = get_db_connection()
    if not conn:
        logger.info(
            f"Stub: Logging meal for {ig_username}: {meal_description} ({calories} cals)")
        return

    try:
        # Get current metrics
        current_metrics = get_user_metrics_json(ig_username) or {}
        nutrition = current_metrics.get('nutrition', {})

        # Update daily totals
        nutrition.setdefault('daily_calories', 0)
        nutrition.setdefault('daily_protein', 0)
        nutrition.setdefault('daily_carbs', 0)
        nutrition.setdefault('daily_fats', 0)

        nutrition['daily_calories'] += calories
        nutrition['daily_protein'] += protein
        nutrition['daily_carbs'] += carbs
        nutrition['daily_fats'] += fats

        # Update metrics
        set_user_metrics_json_field(ig_username, 'nutrition', nutrition)

        logger.info(f"Logged meal for {ig_username}: {meal_description}")

    except Exception as e:
        logger.error(f"Failed to log meal: {e}")


def get_calorie_summary_text(ig_username: str) -> str:
    """Get calorie summary text."""
    targets = get_nutrition_targets(ig_username) or {}
    metrics = get_user_metrics_json(ig_username) or {}
    nutrition = metrics.get('nutrition', {})

    target_cals = targets.get('target_calories', 0)
    current_cals = nutrition.get('daily_calories', 0)
    remaining_cals = target_cals - current_cals

    return f"You've logged {current_cals}/{target_cals} cals today. {remaining_cals} left!"


def rename_last_meal(ig_username: str, new_name: str) -> bool:
    """Rename the last meal (stub implementation)."""
    logger.info(f"Stub: Renaming last meal for {ig_username} to {new_name}")
    return True


def reset_daily_calorie_tracking_if_new_day(ig_username: str):
    """Reset daily calorie tracking if new day."""
    logger.info(
        f"Stub: Resetting daily calorie tracking for {ig_username} if new day")
    pass


# Initialize database on import
init_database()





