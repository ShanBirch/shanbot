"""
Auto Instagram Analyzer
Monitors the database for new users and automatically runs Instagram analysis on them.
"""

import time
import threading
import logging
import sqlite3
import subprocess
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Set, Optional
import traceback

# Add the project root to sys.path for imports
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database utilities
try:
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
except ImportError as e:
    print(f"Warning: Could not import dashboard_sqlite_utils: {e}")

# Import the strict analysis checker
try:
    from anaylize_followers import has_complete_instagram_analysis_sqlite
except ImportError as e:
    print(f"Warning: Could not import analysis checker: {e}")
    # Fallback function if import fails

    def has_complete_instagram_analysis_sqlite(ig_username):
        return False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("auto_instagram_analyzer")

# Configuration
SQLITE_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite"
ANALYZER_SCRIPT_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\anaylize_followers.py"
# Check every 5 minutes (300 seconds) to process more users
CHECK_INTERVAL = 300
# Process max 25 new users per run (increased from 10 for faster processing)
MAX_USERS_PER_RUN = 25

# SAFETY: Add lock file to prevent multiple instances
LOCK_FILE_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\auto_analyzer.lock"


class AutoInstagramAnalyzer:
    def __init__(self):
        self.processed_usernames = set()
        self.failed_usernames = set()
        self.running = False
        self.last_check_time = datetime.now()

    def create_lock_file(self):
        """Create lock file to prevent multiple instances"""
        try:
            with open(LOCK_FILE_PATH, 'w') as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            logger.error(f"Failed to create lock file: {e}")
            return False

    def remove_lock_file(self):
        """Remove lock file when stopping"""
        try:
            if os.path.exists(LOCK_FILE_PATH):
                os.remove(LOCK_FILE_PATH)
        except Exception as e:
            logger.error(f"Failed to remove lock file: {e}")

    def is_already_running(self):
        """Check if another instance is already running"""
        try:
            if not os.path.exists(LOCK_FILE_PATH):
                return False

            # Read PID from lock file
            with open(LOCK_FILE_PATH, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is still running
            try:
                # This doesn't actually kill, just checks if process exists
                os.kill(pid, 0)
                return True  # Process is running
            except OSError:
                # Process is dead, remove stale lock file
                self.remove_lock_file()
                return False
        except Exception as e:
            logger.error(f"Error checking if already running: {e}")
            return False

    def get_new_dashboard_users(self) -> Set[str]:
        """Get Instagram usernames of new users in the dashboard that haven't been analyzed"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get ALL users with valid ig_usernames first, then filter using our strict checker
            cursor.execute("""
                SELECT DISTINCT ig_username
                FROM users 
                WHERE ig_username IS NOT NULL 
                AND ig_username != '' 
                AND ig_username NOT LIKE 'user_%'
                ORDER BY ig_username
            """)

            all_users = set()
            for row in cursor.fetchall():
                ig_username = row[0]

                # Skip obviously invalid usernames
                if ig_username.isdigit() or len(ig_username) < 2:
                    continue

                # Skip test/system usernames
                if ig_username in ['calorie_tracking', 'cocos_pt_studio']:
                    continue

                all_users.add(ig_username)

            conn.close()

            # Now filter using our strict analysis checker
            new_users = set()
            for ig_username in all_users:
                # Skip users we've already tried and failed
                if ig_username in self.failed_usernames:
                    continue

                # Use the strict checker to see if they really have complete analysis
                if not has_complete_instagram_analysis_sqlite(ig_username):
                    new_users.add(ig_username)

            logger.info(
                f"Checked {len(all_users)} total users, found {len(new_users)} needing Instagram analysis")
            if len(new_users) > 10:
                logger.info(
                    f"Sample users needing analysis: {list(list(new_users)[:10])}")
            else:
                logger.info(f"Users needing analysis: {list(new_users)}")

            return new_users

        except Exception as e:
            logger.error(f"Error getting new dashboard users: {e}")
            return set()

    def create_temporary_followers_file(self, usernames: Set[str]) -> str:
        """Create a temporary file with usernames for the analyzer script"""
        try:
            temp_file_path = os.path.join(
                project_root, "temp_dashboard_users.txt")

            with open(temp_file_path, 'w') as f:
                for username in usernames:
                    f.write(f"{username}\n")

            logger.info(
                f"Created temporary file with {len(usernames)} usernames: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            logger.error(f"Error creating temporary followers file: {e}")
            return None

    def run_analyzer_script(self, usernames: Set[str]) -> bool:
        """Run the analyze_followers script on the new usernames"""
        try:
            if not usernames:
                return True

            # Create temporary file with usernames
            temp_file = self.create_temporary_followers_file(usernames)
            if not temp_file:
                return False

            # Prepare command to run analyzer script
            cmd = [
                sys.executable,  # Python executable
                ANALYZER_SCRIPT_PATH,
                "--followers-list", temp_file
            ]

            logger.info(
                f"Running analyzer script with command: {' '.join(cmd)}")
            logger.info(f"Analyzing usernames: {list(usernames)}")

            # Set working directory to the script's directory
            working_dir = os.path.dirname(ANALYZER_SCRIPT_PATH)

            # Run the script
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info("Analyzer script completed successfully!")
                logger.info(f"Script output: {result.stdout}")

                # Mark these users as processed
                self.processed_usernames.update(usernames)

                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except:
                    pass

                return True
            else:
                logger.error(
                    f"Analyzer script failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                logger.error(f"Standard output: {result.stdout}")

                # Mark these users as failed
                self.failed_usernames.update(usernames)

                return False

        except subprocess.TimeoutExpired:
            logger.error("Analyzer script timed out after 1 hour")
            self.failed_usernames.update(usernames)
            return False
        except Exception as e:
            logger.error(f"Error running analyzer script: {e}")
            logger.error(traceback.format_exc())
            self.failed_usernames.update(usernames)
            return False

    def check_and_process_new_users(self):
        """Check for new users and process them"""
        try:
            logger.info(
                "Checking for new dashboard users needing Instagram analysis...")

            # Get new users
            new_users = self.get_new_dashboard_users()

            if not new_users:
                logger.info("No new users found needing analysis")
                return

            logger.info(
                f"Found {len(new_users)} new users needing analysis: {list(new_users)}")

            # Limit to MAX_USERS_PER_RUN to avoid rate limits
            users_to_process = list(new_users)[:MAX_USERS_PER_RUN]

            if len(users_to_process) < len(new_users):
                logger.info(
                    f"Processing first {len(users_to_process)} users to avoid rate limits")

            # Run the analyzer
            success = self.run_analyzer_script(set(users_to_process))

            if success:
                logger.info(
                    f"Successfully processed {len(users_to_process)} new users")
            else:
                logger.error(
                    f"Failed to process new users: {users_to_process}")

        except Exception as e:
            logger.error(f"Error in check_and_process_new_users: {e}")
            logger.error(traceback.format_exc())

    def start_monitoring(self):
        """Start the monitoring loop"""
        # Check if already running
        if self.is_already_running():
            logger.warning(
                "⚠️ Auto Instagram Analyzer is already running! Skipping this instance.")
            return

        # Create lock file
        if not self.create_lock_file():
            logger.error("Failed to create lock file. Cannot start analyzer.")
            return

        self.running = True
        logger.info("🚀 Auto Instagram Analyzer started!")
        logger.info(f"📊 Monitoring database: {SQLITE_PATH}")
        logger.info(f"🤖 Analyzer script: {ANALYZER_SCRIPT_PATH}")
        logger.info(f"⏰ Check interval: {CHECK_INTERVAL} seconds")
        logger.info(f"👥 Max users per run: {MAX_USERS_PER_RUN}")

        try:
            while self.running:
                try:
                    self.check_and_process_new_users()

                    # Wait for next check
                    time.sleep(CHECK_INTERVAL)

                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping...")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    logger.error(traceback.format_exc())
                    # Continue running even if there's an error
                    time.sleep(CHECK_INTERVAL)
        finally:
            # Always remove lock file when stopping
            self.remove_lock_file()
            self.running = False
            logger.info("Auto Instagram Analyzer stopped")

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        self.remove_lock_file()


def start_auto_analyzer_thread():
    """Start the auto analyzer in a background thread"""
    analyzer = AutoInstagramAnalyzer()

    def run_analyzer():
        try:
            analyzer.start_monitoring()
        except Exception as e:
            logger.error(f"Error in analyzer thread: {e}")

    thread = threading.Thread(target=run_analyzer, daemon=True)
    thread.start()
    logger.info("Auto Instagram Analyzer thread started")
    return thread


if __name__ == "__main__":
    # Test mode - run the analyzer once
    logger.info("=== AUTO INSTAGRAM ANALYZER TEST MODE ===")

    analyzer = AutoInstagramAnalyzer()

    # Check what users would be processed
    new_users = analyzer.get_new_dashboard_users()
    if new_users:
        print(f"\nFound {len(new_users)} users that need Instagram analysis:")
        for i, username in enumerate(new_users, 1):
            print(f"{i}. {username}")

        response = input(
            f"\nDo you want to run the analyzer on these {len(new_users)} users? (y/n): ")
        if response.lower() == 'y':
            analyzer.check_and_process_new_users()
        else:
            print("Skipped analysis")
    else:
        print("No users found that need Instagram analysis")
