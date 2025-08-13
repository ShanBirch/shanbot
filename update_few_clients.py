#!/usr/bin/env python3
"""
Update progression goals for all clients with improved error handling and stability
"""

import json
import logging
import sys
from weekly_program_updater import TrainerizeAutomation

# Configure logging without emoji characters to avoid Windows console issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_few_clients.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def load_progression_data():
    """Load the fixed progression data"""
    try:
        with open('set_by_set_progressions_fixed.json', 'r') as f:
            data = json.load(f)
        logging.info(
            f"Loaded FIXED set-by-set progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error("set_by_set_progressions_fixed.json not found")
        return None


def update_all_clients():
    """Update progression goals for all clients with improved stability"""

    # Load progression data
    progression_data = load_progression_data()
    if not progression_data:
        return

        # Process ALL clients from the progression data
    selected_data = progression_data

    if not selected_data:
        logging.error("No matching clients found in progression data")
        return

    logging.info(
        f"Processing {len(selected_data)} clients: {list(selected_data.keys())}")

    automation = None
    try:
        # Initialize automation
        logging.info("Initializing TrainerizeAutomation...")
        automation = TrainerizeAutomation()

        # Login
        logging.info("Logging in to Trainerize...")
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            logging.error("Login failed")
            return

        logging.info("Login successful! Processing clients...")

        # Process the selected clients
        results = automation.process_multiple_clients(selected_data)

        # Print results
        logging.info("=== FINAL RESULTS ===")
        for client_name, result in results.items():
            status = result.get('status', 'unknown')
            logging.info(f"{client_name}: {status}")

            if 'workouts_processed' in result:
                for workout_name, workout_result in result['workouts_processed'].items():
                    exercises_updated = workout_result.get(
                        'exercises_updated', 0)
                    exercises_failed = workout_result.get(
                        'exercises_failed', 0)
                    logging.info(
                        f"  {workout_name}: {exercises_updated} updated, {exercises_failed} failed")

    except Exception as e:
        logging.error(f"Error during processing: {e}")

    finally:
        if automation:
            try:
                automation.cleanup()
                logging.info("Cleanup completed")
            except Exception as e:
                logging.warning(f"Error during cleanup: {e}")


if __name__ == "__main__":
    update_all_clients()
