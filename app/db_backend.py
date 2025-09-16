"""
Database backend router for Shanbot
===================================
Provides a small set of DB helper functions that transparently use
PostgreSQL on Render (when DATABASE_URL is set) and SQLite locally.

This avoids scattering direct driver calls across the codebase and
prevents mismatched schemas between modules.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger("shanbot_db_backend")


def is_postgres() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def _get_pg_conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set")
    conn = psycopg2.connect(database_url)
    return conn, conn.cursor(cursor_factory=RealDictCursor)


def _get_sqlite_conn():
    # Reuse the existing SQLite utils for a single connection instance
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection

    conn = get_db_connection()
    return conn, conn.cursor()


def add_message_to_history(ig_username: str, message_type: str, message_text: str, message_timestamp: Optional[str] = None) -> bool:
    """Insert a message row to `messages` in the active backend."""
    if not ig_username:
        return False

    try:
        if is_postgres():
            conn, cur = _get_pg_conn()
            try:
                # Ensure tables exist (idempotent)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                      id SERIAL PRIMARY KEY,
                      ig_username TEXT UNIQUE,
                      subscriber_id TEXT UNIQUE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                      id SERIAL PRIMARY KEY,
                      ig_username TEXT,
                      subscriber_id TEXT,
                      message_type TEXT,
                      message_text TEXT,
                      timestamp TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                # Try to fetch subscriber_id from users; tolerate missing row
                subscriber_id = None
                try:
                    cur.execute(
                        "SELECT subscriber_id FROM users WHERE ig_username = %s LIMIT 1",
                        (ig_username,),
                    )
                    row = cur.fetchone()
                    if row:
                        # RealDictCursor returns dict; default cursor returns tuple
                        try:
                            subscriber_id = (row or {}).get("subscriber_id")
                        except Exception:
                            subscriber_id = row[0]
                except Exception:
                    subscriber_id = None

                cur.execute(
                    """
                    INSERT INTO messages (ig_username, subscriber_id, timestamp, message_type, message_text)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (ig_username, subscriber_id, message_timestamp,
                     message_type, message_text),
                )
                conn.commit()
                return True
            finally:
                conn.close()
        else:
            # Delegate to existing SQLite helper for consistent behavior
            from app.dashboard_modules.dashboard_sqlite_utils import add_message_to_history as sqlite_add_msg

            sqlite_add_msg(
                ig_username=ig_username,
                message_type=message_type,
                message_text=message_text,
                message_timestamp=message_timestamp,
            )
            return True
    except Exception as e:
        logger.error(f"add_message_to_history failed: {e}")
        return False


def add_response_to_review_queue(
    *,
    user_ig_username: str,
    user_subscriber_id: Optional[str],
    incoming_message_text: str,
    incoming_message_timestamp: Optional[str],
    generated_prompt_text: str,
    proposed_response_text: str,
    prompt_type: str = "general_chat",
    status: str = "pending_review",
) -> Optional[int]:
    """Insert a review item to the active backend and return the new ID."""
    try:
        if is_postgres():
            conn, cur = _get_pg_conn()
            try:
                # Ensure tables exist (idempotent)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pending_reviews (
                      id SERIAL PRIMARY KEY,
                      user_ig_username TEXT,
                      user_subscriber_id TEXT,
                      subscriber_id TEXT,
                      incoming_message_text TEXT,
                      incoming_message_timestamp TEXT,
                      generated_prompt_text TEXT,
                      proposed_response_text TEXT,
                      user_message TEXT,
                      ai_response_text TEXT,
                      final_response_text TEXT,
                      prompt_type TEXT,
                      status TEXT DEFAULT 'pending',
                      created_timestamp TEXT,
                      reviewed_timestamp TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                cur.execute(
                    """
                    INSERT INTO pending_reviews
                      (user_ig_username, user_subscriber_id, incoming_message_text, proposed_response_text,
                       prompt_type, status, incoming_message_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_ig_username,
                        user_subscriber_id,
                        incoming_message_text,
                        proposed_response_text,
                        prompt_type,
                        status,
                        incoming_message_timestamp,
                    ),
                )
                new_id = cur.fetchone()["id"]
                conn.commit()
                return int(new_id)
            finally:
                conn.close()
        else:
            # Delegate to existing SQLite helper (supports kwargs)
            from app.dashboard_modules.dashboard_sqlite_utils import add_response_to_review_queue as sqlite_add_review

            return sqlite_add_review(
                user_ig_username=user_ig_username,
                user_subscriber_id=user_subscriber_id,
                incoming_message_text=incoming_message_text,
                incoming_message_timestamp=incoming_message_timestamp,
                generated_prompt_text=generated_prompt_text,
                proposed_response_text=proposed_response_text,
                prompt_type=prompt_type,
                status=status,
            )
    except Exception as e:
        logger.error(f"add_response_to_review_queue failed: {e}")
        return None


def set_user_ad_flow(
    *,
    ig_username: str,
    subscriber_id: Optional[str],
    scenario: int,
    next_state: str,
    lead_source: str = "paid_plant_based_challenge",
) -> bool:
    """Create or update a user row with ad flow flags in the active backend."""
    try:
        if is_postgres():
            conn, cur = _get_pg_conn()
            try:
                # Ensure table exists (idempotent)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                      id SERIAL PRIMARY KEY,
                      ig_username TEXT UNIQUE,
                      subscriber_id TEXT UNIQUE,
                      first_name TEXT,
                      last_name TEXT,
                      client_status TEXT DEFAULT 'Not a Client',
                      journey_stage TEXT DEFAULT 'Initial Inquiry',
                      is_onboarding BOOLEAN DEFAULT FALSE,
                      is_in_checkin_flow_mon BOOLEAN DEFAULT FALSE,
                      is_in_checkin_flow_wed BOOLEAN DEFAULT FALSE,
                      is_in_ad_flow BOOLEAN DEFAULT FALSE,
                      last_interaction_timestamp TEXT,
                      profile_bio_text TEXT,
                      interests_json TEXT DEFAULT '[]',
                      conversation_topics_json TEXT DEFAULT '[]',
                      client_analysis_json TEXT DEFAULT '{}',
                      goals_text TEXT,
                      current_fitness_level_text TEXT,
                      injuries_limitations_text TEXT,
                      preferred_workout_types_text TEXT,
                      lifestyle_factors_text TEXT,
                      engagement_preferences_text TEXT,
                      meal_plan_summary TEXT,
                      weekly_workout_summary TEXT,
                      ad_script_state TEXT,
                      ad_scenario INTEGER,
                      lead_source TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # Upsert by ig_username
                cur.execute(
                    """
                    INSERT INTO users (ig_username, subscriber_id, is_in_ad_flow, ad_script_state, ad_scenario, lead_source)
                    VALUES (%s, %s, TRUE, %s, %s, %s)
                    ON CONFLICT (ig_username)
                    DO UPDATE SET
                      subscriber_id = COALESCE(EXCLUDED.subscriber_id, users.subscriber_id),
                      is_in_ad_flow = TRUE,
                      ad_script_state = EXCLUDED.ad_script_state,
                      ad_scenario = EXCLUDED.ad_scenario,
                      lead_source = EXCLUDED.lead_source,
                      updated_at = CURRENT_TIMESTAMP
                    """,
                    (ig_username, subscriber_id, next_state, scenario, lead_source),
                )
                conn.commit()
                return True
            finally:
                conn.close()
        else:
            # SQLite path mirrors the existing logic
            import sqlite3
            from app.dashboard_modules.dashboard_sqlite_utils import SQLITE_DB_PATH

            conn = sqlite3.connect(SQLITE_DB_PATH)
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT ig_username FROM users WHERE ig_username = ?",
                    (ig_username,),
                )
                if not cur.fetchone():
                    cur.execute(
                        """
                        INSERT INTO users (ig_username, subscriber_id, lead_source, is_in_ad_flow, ad_script_state, ad_scenario)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (ig_username, subscriber_id, lead_source,
                         True, next_state, scenario),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE users
                        SET lead_source = ?, is_in_ad_flow = ?, ad_script_state = ?, ad_scenario = ?
                        WHERE ig_username = ?
                        """,
                        (lead_source, True, next_state, scenario, ig_username),
                    )
                conn.commit()
                return True
            finally:
                conn.close()
    except Exception as e:
        logger.error(f"set_user_ad_flow failed: {e}")
        return False
