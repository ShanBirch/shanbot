"""
Conversation Strategy A/B Testing Module
Handles A/B testing and conversation strategy selection based on relationship context
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ConversationStrategy:
    def __init__(self):
        self.db_path = "app/analytics_data_good.sqlite"

    def get_vegan_approach_type(self, ig_username: str) -> str:
        """
        A/B test assignment based on username hash for consistent assignment
        Returns: 'rapport_first' or 'direct'
        """
        # Create consistent hash of username
        hash_obj = hashlib.md5(ig_username.lower().encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Split 50/50 based on hash
        if hash_int % 2 == 0:
            return 'rapport_first'  # Group A: Current 3-phase approach
        else:
            return 'direct'         # Group B: Direct vegan approach

    def is_fresh_vegan_contact(self, ig_username: str) -> bool:
        """
        Determine if this is a fresh vegan contact eligible for A/B testing

        Fresh contact criteria (UPDATED):
        - User has fresh_lead flag = 1 in processing_queue table (from check_daily_follow_backs)
        - Conversation history < 3 messages total
        - This ensures only legitimate vegan leads from our lead generation get A/B testing
        """
        try:
            # Criterion 1: Check if user is marked as fresh lead in database
            fresh_lead_status = self.check_fresh_lead_status(ig_username)
            if not fresh_lead_status:
                logger.debug(
                    f"{ig_username} not marked as fresh lead - skipping A/B testing")
                return False

            # Criterion 2: Message count < 3 (very fresh contact)
            # Get conversation history from database
            history, metrics_dict, user_id = self.get_user_data_simple(
                ig_username)

            total_messages = len(history) if history else 0
            if total_messages >= 3:
                logger.info(
                    f"{ig_username} has {total_messages} messages (>= 3) - not fresh contact for A/B testing")
                return False

            logger.info(
                f"{ig_username} qualifies as fresh vegan contact (fresh_lead=1, {total_messages} messages)")
            return True

        except Exception as e:
            logger.error(
                f"Error checking fresh contact status for {ig_username}: {e}")
            return False  # Default to not fresh if error

    def check_fresh_lead_status(self, ig_username: str) -> bool:
        """
        Check if user is marked as fresh lead in processing_queue table
        Returns True if fresh_lead = 1, False otherwise
        """
        try:
            # First check if we're using Postgres and processing_queue table doesn't exist
            import os
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                # On Postgres - processing_queue table doesn't exist there
                # Return False (not a fresh lead) to avoid errors
                logger.debug(
                    f"Postgres mode - skipping fresh lead check for {ig_username}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if processing_queue table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='processing_queue'
            """)
            table_exists = cursor.fetchone()

            if not table_exists:
                logger.debug(
                    f"processing_queue table doesn't exist - skipping fresh lead check for {ig_username}")
                conn.close()
                return False

            cursor.execute("""
                SELECT fresh_lead FROM processing_queue 
                WHERE username = ?
            """, (ig_username,))

            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 1:
                logger.debug(f"✅ {ig_username} is marked as fresh lead")
                return True
            else:
                logger.debug(
                    f"❌ {ig_username} not marked as fresh lead (or not found)")
                return False

        except Exception as e:
            logger.error(
                f"Error checking fresh lead status for {ig_username}: {e}")
            return False

    def get_conversation_strategy(self, ig_username: str) -> Dict[str, str]:
        """
        Main function to determine conversation strategy for a user

        Returns:
        {
            'strategy': 'fresh_vegan_direct' | 'fresh_vegan_rapport' | 'established_relationship' | 'general_chat',
            'approach_type': 'direct' | 'rapport_first' | 'standard',
            'reasoning': 'explanation of why this strategy was chosen'
        }
        """
        try:
            # First check if this is a fresh vegan contact
            is_fresh = self.is_fresh_vegan_contact(ig_username)

            if is_fresh:
                # Fresh vegan contact - apply A/B testing
                approach_type = self.get_vegan_approach_type(ig_username)

                if approach_type == 'direct':
                    return {
                        'strategy': 'fresh_vegan_direct',
                        'approach_type': 'direct',
                        'reasoning': f'Fresh vegan contact assigned to Group B (Direct) via A/B test'
                    }
                else:
                    return {
                        'strategy': 'fresh_vegan_rapport',
                        'approach_type': 'rapport_first',
                        'reasoning': f'Fresh vegan contact assigned to Group A (Rapport First) via A/B test'
                    }
            else:
                # Established relationship - use standard approach
                return {
                    'strategy': 'established_relationship',
                    'approach_type': 'standard',
                    'reasoning': 'Established relationship - using standard conversation flow'
                }

        except Exception as e:
            logger.error(f"Error determining strategy for {ig_username}: {e}")
            return {
                'strategy': 'general_chat',
                'approach_type': 'standard',
                'reasoning': 'Error occurred - defaulting to general chat'
            }

    def get_user_data_simple(self, ig_username: str) -> Tuple[List[Dict], Dict, Optional[str]]:
        """
        Simplified version of get_user_data to avoid circular imports
        Returns conversation history, metrics dict, and user_id
        """
        try:
            # Try to import from webhook_handlers
            from webhook_handlers import get_user_data
            return get_user_data(ig_username, None)
        except ImportError:
            # Fallback: direct database access
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get conversation history
                cursor.execute("""
                    SELECT timestamp, message_type as type, message_text as text
                    FROM conversation_history 
                    WHERE ig_username = ? 
                    ORDER BY timestamp ASC
                """, (ig_username,))

                history = [dict(row) for row in cursor.fetchall()]

                # Basic metrics dict (minimal for fresh contact detection)
                metrics_dict = {
                    'ig_username': ig_username,
                    'trial_status': 'Initial Contact',
                    'journey_stage': {'current_stage': 'Topic 1'}
                }

                conn.close()
                return history, metrics_dict, ig_username

            except Exception as e:
                logger.error(
                    f"Error in direct database access for {ig_username}: {e}")
                return [], {}, None

    def log_strategy_usage(self, ig_username: str, strategy_info: Dict[str, str], message_context: str = ""):
        """
        Log which strategy was used for analytics and debugging
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'ig_username': ig_username,
                'strategy': strategy_info['strategy'],
                'approach_type': strategy_info['approach_type'],
                'reasoning': strategy_info['reasoning'],
                # First 100 chars of user message
                'message_context': message_context[:100]
            }

            logger.info(
                f"Strategy used for {ig_username}: {strategy_info['strategy']} ({strategy_info['approach_type']})")

            # Could save to database or file for analytics
            # For now, just log it

        except Exception as e:
            logger.error(f"Error logging strategy usage: {e}")


# Global instance
conversation_strategy = ConversationStrategy()


def get_conversation_strategy_for_user(ig_username: str) -> Dict[str, str]:
    """
    Convenience function to get conversation strategy for a user
    """
    return conversation_strategy.get_conversation_strategy(ig_username)


def is_fresh_vegan_contact(ig_username: str) -> bool:
    """
    Convenience function to check if user is a fresh vegan contact
    """
    return conversation_strategy.is_fresh_vegan_contact(ig_username)


def log_strategy_usage(ig_username: str, strategy_info: Dict[str, str], message_context: str = ""):
    """
    Convenience function to log strategy usage
    """
    return conversation_strategy.log_strategy_usage(ig_username, strategy_info, message_context)


def log_strategy_to_database(ig_username: str, strategy: str, is_fresh_vegan: bool = True):
    """
    Log strategy assignment to database for A/B testing analytics
    """
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_strategy_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                strategy TEXT NOT NULL,
                is_fresh_vegan INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Insert the log entry
        cursor.execute("""
            INSERT INTO conversation_strategy_log (username, strategy, is_fresh_vegan, timestamp)
            VALUES (?, ?, ?, ?)
        """, (ig_username, strategy, 1 if is_fresh_vegan else 0, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        logger.info(f"Logged strategy assignment: {ig_username} -> {strategy}")
        return True

    except Exception as e:
        logger.error(f"Error logging strategy to database: {e}")
        return False


def get_strategy_analytics():
    """
    Get comprehensive analytics about A/B test performance
    Returns dictionary with test metrics and statistics
    """
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_strategy_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                strategy TEXT NOT NULL,
                is_fresh_vegan INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Get total counts by strategy
        cursor.execute("""
            SELECT 
                strategy,
                COUNT(*) as count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen
            FROM conversation_strategy_log 
            WHERE is_fresh_vegan = 1 
            GROUP BY strategy
        """)
        strategy_counts = cursor.fetchall()

        # Get recent activity (last 10 entries)
        cursor.execute("""
            SELECT username, strategy, timestamp, is_fresh_vegan
            FROM conversation_strategy_log 
            WHERE is_fresh_vegan = 1
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_logs = cursor.fetchall()

        # Get daily counts for the last 7 days
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                strategy,
                COUNT(*) as count
            FROM conversation_strategy_log 
            WHERE is_fresh_vegan = 1 
                AND timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp), strategy
            ORDER BY date DESC
        """)
        daily_counts = cursor.fetchall()

        # Calculate totals and percentages
        total_users = sum(row['count'] for row in strategy_counts)
        group_a_count = next((row['count'] for row in strategy_counts if row['strategy'] in [
                             'rapport_first', 'fresh_vegan_rapport']), 0)
        group_b_count = next((row['count'] for row in strategy_counts if row['strategy'] in [
                             'direct', 'fresh_vegan_direct']), 0)

        # Calculate test duration
        start_date = None
        days_running = 0
        if strategy_counts:
            earliest_date = min(row['first_seen']
                                for row in strategy_counts if row['first_seen'])
            if earliest_date:
                start_date = datetime.fromisoformat(
                    earliest_date.split('.')[0]).strftime('%Y-%m-%d')
                days_running = (
                    datetime.now() - datetime.fromisoformat(earliest_date.split('.')[0])).days

        # Get today's new users
        cursor.execute("""
            SELECT COUNT(*) as today_count
            FROM conversation_strategy_log 
            WHERE is_fresh_vegan = 1 
                AND DATE(timestamp) = DATE('now')
        """)
        today_result = cursor.fetchone()
        new_users_today = today_result['today_count'] if today_result else 0

        conn.close()

        # Format recent logs for display
        formatted_recent_logs = []
        for log in recent_logs:
            formatted_recent_logs.append({
                'username': log['username'],
                'strategy': log['strategy'],
                'timestamp': log['timestamp'],
                'is_fresh_vegan': bool(log['is_fresh_vegan'])
            })

        return {
            'total_users': total_users,
            'group_a_count': group_a_count,
            'group_b_count': group_b_count,
            'days_running': days_running,
            'start_date': start_date,
            'new_users_today': new_users_today,
            'recent_logs': formatted_recent_logs,
            'daily_counts': [dict(row) for row in daily_counts]
        }

    except Exception as e:
        logger.error(f"Error getting strategy analytics: {e}")
        return {
            'total_users': 0,
            'group_a_count': 0,
            'group_b_count': 0,
            'days_running': 0,
            'start_date': None,
            'new_users_today': 0,
            'recent_logs': [],
            'daily_counts': []
        }


def disable_fresh_vegan_for_trial_members():
    """
    Automatically disable fresh vegan status for users who have become trial members or paying clients.
    This ensures they are excluded from vegan auto mode processing.

    Returns:
        int: Number of users updated
    """
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        cursor = conn.cursor()

        # Find users who are still marked as fresh vegan but have become trial/paying members
        # Join conversation_strategy_log with user_metrics to check trial status
        query = """
        SELECT DISTINCT csl.username, csl.id
        FROM conversation_strategy_log csl
        JOIN user_metrics um ON csl.username = um.ig_username
        WHERE csl.is_fresh_vegan = 1
        AND (
            JSON_EXTRACT(um.metrics_json, '$.journey_stage.trial_start_date') IS NOT NULL
            OR JSON_EXTRACT(um.metrics_json, '$.journey_stage.is_paying_client') = 1
        )
        """

        cursor.execute(query)
        users_to_update = cursor.fetchall()

        updated_count = 0

        for username, log_id in users_to_update:
            # Update the conversation strategy log to disable fresh vegan status
            cursor.execute("""
                UPDATE conversation_strategy_log 
                SET is_fresh_vegan = 0
                WHERE id = ?
            """, (log_id,))

            logger.info(
                f"🔄 Disabled fresh vegan status for trial/paying member: {username}")
            updated_count += 1

        conn.commit()
        conn.close()

        if updated_count > 0:
            logger.info(
                f"✅ Updated {updated_count} users - removed from fresh vegan auto mode")

        return updated_count

    except Exception as e:
        logger.error(
            f"Error disabling fresh vegan status for trial members: {e}")
        return 0


def check_and_cleanup_vegan_eligibility(ig_username: str) -> bool:
    """
    Check if a specific user should be removed from fresh vegan status
    and update if they've become a trial/paying member.

    Args:
        ig_username: Username to check

    Returns:
        bool: True if user was updated (removed from fresh vegan), False otherwise
    """
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        cursor = conn.cursor()

        # Check if user is marked as fresh vegan
        cursor.execute("""
            SELECT id FROM conversation_strategy_log 
            WHERE username = ? AND is_fresh_vegan = 1
        """, (ig_username,))

        vegan_entry = cursor.fetchone()
        if not vegan_entry:
            conn.close()
            return False  # Not marked as fresh vegan

        # Check if they've become trial/paying member
        cursor.execute("""
            SELECT metrics_json FROM user_metrics 
            WHERE ig_username = ?
        """, (ig_username,))

        metrics_row = cursor.fetchone()
        if not metrics_row:
            conn.close()
            return False

        import json
        metrics = json.loads(metrics_row[0])
        journey_stage = metrics.get('journey_stage', {})

        has_trial_date = journey_stage.get('trial_start_date') is not None
        is_paying = journey_stage.get('is_paying_client', False)

        if has_trial_date or is_paying:
            # Update to disable fresh vegan status
            cursor.execute("""
                UPDATE conversation_strategy_log 
                SET is_fresh_vegan = 0
                WHERE id = ?
            """, (vegan_entry[0],))

            conn.commit()
            conn.close()

            status = "paying client" if is_paying else "trial member"
            logger.info(
                f"🔄 Removed {ig_username} from fresh vegan auto mode (now {status})")
            return True

        conn.close()
        return False

    except Exception as e:
        logger.error(
            f"Error checking vegan eligibility for {ig_username}: {e}")
        return False


# Convenience functions for external use
def run_vegan_eligibility_cleanup() -> int:
    """
    Run the bulk cleanup of vegan eligibility for trial/paying members.
    This can be called manually or on a schedule.

    Returns:
        int: Number of users updated
    """
    return disable_fresh_vegan_for_trial_members()
