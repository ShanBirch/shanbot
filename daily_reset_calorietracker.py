import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from calorie_manager_calorietracker import CalorieTracker_CalorieTracker
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('calorie_tracker_reset')


class DailyReset_CalorieTracker:
    def __init__(self, analytics_file_path: str = None):
        """Initialize the daily reset manager."""
        self.analytics_file_path = analytics_file_path or r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        self.melbourne_tz = pytz.timezone('Australia/Melbourne')
        self.tracker = CalorieTracker_CalorieTracker(self.analytics_file_path)
        self.scheduler = BackgroundScheduler(timezone=self.melbourne_tz)

    def _get_active_users(self) -> list:
        """Get list of users with calorie tracking enabled."""
        try:
            with open(self.analytics_file_path, 'r') as f:
                analytics_data = json.load(f)

            active_users = []
            conversations = analytics_data.get('conversations', {})

            for user_id, data in conversations.items():
                if isinstance(data, dict) and 'metrics' in data:
                    metrics = data['metrics']
                    if isinstance(metrics, dict):
                        ig_username = metrics.get('ig_username')
                        if ig_username and 'calorie_tracking' in metrics:
                            active_users.append(ig_username)

            return active_users
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []

    def reset_all_users(self):
        """Reset tracking for all active users."""
        logger.info("Starting daily reset for all users...")
        active_users = self._get_active_users()

        for username in active_users:
            try:
                if self.tracker.reset_daily_tracking(username):
                    logger.info(f"Successfully reset tracking for {username}")
                else:
                    logger.error(f"Failed to reset tracking for {username}")
            except Exception as e:
                logger.error(f"Error resetting tracking for {username}: {e}")

        logger.info(f"Daily reset completed for {len(active_users)} users")

    def schedule_daily_reset(self):
        """Schedule the daily reset job for midnight Melbourne time."""
        try:
            # Add job to run at midnight Melbourne time
            self.scheduler.add_job(
                self.reset_all_users,
                'cron',
                hour=0,
                minute=0,
                timezone=self.melbourne_tz
            )

            self.scheduler.start()
            logger.info("Daily reset scheduler started successfully")

            # Log next run time
            next_run = self.scheduler.get_jobs()[0].next_run_time
            logger.info(f"Next reset scheduled for: {next_run}")

        except Exception as e:
            logger.error(f"Error scheduling daily reset: {e}")
            raise

    def stop_scheduler(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")


# Example usage and testing
if __name__ == "__main__":
    reset_manager = DailyReset_CalorieTracker()

    # Test immediate reset
    print("\nTesting immediate reset for all users:")
    reset_manager.reset_all_users()

    # Start the scheduler
    print("\nStarting scheduler for daily midnight resets:")
    reset_manager.schedule_daily_reset()

    try:
        # Keep the script running
        print("\nScheduler is running. Press Ctrl+C to exit.")
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        reset_manager.stop_scheduler()
        print("Scheduler stopped.")
