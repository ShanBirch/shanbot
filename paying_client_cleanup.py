import sqlite3
import logging

logger = logging.getLogger(__name__)


def cleanup_paying_client_from_ad_flow(ig_username: str) -> bool:
    """
    Remove a user from ad flow when they become a paying client.

    Args:
        ig_username: Username to clean up

    Returns:
        bool: True if user was cleaned up, False otherwise
    """
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Check if user is in ad flow
        cursor.execute("""
            SELECT is_in_ad_flow, ad_script_state, lead_source
            FROM users 
            WHERE ig_username = ?
        """, (ig_username,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        is_in_ad_flow, ad_script_state, lead_source = result

        if is_in_ad_flow:
            # Remove from ad flow
            cursor.execute("""
                UPDATE users 
                SET is_in_ad_flow = 0, 
                    ad_script_state = 'completed',
                    lead_source = CASE 
                        WHEN lead_source = 'paid_plant_based_challenge' THEN 'paying_member'
                        ELSE lead_source 
                    END
                WHERE ig_username = ?
            """, (ig_username,))

            conn.commit()
            conn.close()

            logger.info(
                f"SUCCESS: Removed {ig_username} from ad flow (now paying client)")
            return True
        else:
            conn.close()
            return False

    except Exception as e:
        logger.error(
            f"ERROR: Error cleaning up {ig_username} from ad flow: {e}")
        return False
