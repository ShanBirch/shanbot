"""
Test script for the Background Bio Fetcher
Run this to test bio fetching for specific users
"""

from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
from background_bio_fetcher import BackgroundBioFetcher
import logging
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_bio_fetcher")


def test_bio_fetcher():
    """Test the bio fetcher with a few sample users"""
    logger.info("=== TESTING BACKGROUND BIO FETCHER ===")

    # Check database for users without bios
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ig_username 
            FROM users 
            WHERE ig_username IS NOT NULL 
            AND ig_username != '' 
            AND ig_username NOT LIKE 'user_%'
            AND (
                metrics_json IS NULL 
                OR json_extract(metrics_json, '$.bio_text') IS NULL
                OR json_extract(metrics_json, '$.bio_text') = ''
            )
            LIMIT 3
        """)

        users_to_test = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not users_to_test:
            logger.info(
                "No users found without bio data. All users already have bios!")
            return

        logger.info(
            f"Found {len(users_to_test)} users for testing: {users_to_test}")

        # Create bio fetcher instance
        fetcher = BackgroundBioFetcher()

        try:
            # Setup browser
            if not fetcher.setup_browser():
                logger.error("Failed to setup browser")
                return

            # Login to Instagram
            if not fetcher.login_to_instagram():
                logger.error("Failed to login to Instagram")
                return

            # Test with the first user
            test_username = users_to_test[0]
            logger.info(f"\n=== TESTING WITH USER: {test_username} ===")

            success = fetcher.process_user_bio(test_username)

            if success:
                logger.info(
                    f"✅ Successfully processed bio for {test_username}")

                # Check if data was saved
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT json_extract(metrics_json, '$.bio_text') as bio_text,
                           json_extract(metrics_json, '$.conversation_topics') as topics
                    FROM users 
                    WHERE ig_username = ?
                """, (test_username,))

                result = cursor.fetchone()
                if result and result[0]:
                    logger.info(f"Bio found in database: {result[0][:100]}...")
                    if result[1]:
                        logger.info(f"Conversation topics: {result[1]}")
                else:
                    logger.warning("Bio data not found in database")
                conn.close()

            else:
                logger.error(f"❌ Failed to process bio for {test_username}")

        finally:
            fetcher.stop()

    except Exception as e:
        logger.error(f"Error during testing: {e}")


def run_single_user_test(username: str):
    """Test bio fetching for a specific user"""
    logger.info(f"=== TESTING BIO FETCH FOR: {username} ===")

    fetcher = BackgroundBioFetcher()

    try:
        if not fetcher.setup_browser():
            logger.error("Failed to setup browser")
            return

        if not fetcher.login_to_instagram():
            logger.error("Failed to login to Instagram")
            return

        success = fetcher.process_user_bio(username)

        if success:
            logger.info(f"✅ Successfully processed bio for {username}")
        else:
            logger.error(f"❌ Failed to process bio for {username}")

    finally:
        fetcher.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific user
        username = sys.argv[1]
        run_single_user_test(username)
    else:
        # Test with users from database
        test_bio_fetcher()
