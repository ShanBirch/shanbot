#!/usr/bin/env python3
"""
Workout Data Importer to SQLite
Monitors the checkin_reviews directory for new JSON files and automatically
imports detailed workout session data into the SQLite database for dashboard display.
"""

import json
import os
import sqlite3
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.dashboard_modules.dashboard_sqlite_utils import (
        get_db_connection,
        create_workout_tables_if_not_exist,
        save_workout_session,
        get_ig_username_by_name
    )
    print("✅ Successfully imported SQLite utility functions.")
except ImportError as e:
    print(f"❌ Error importing SQLite utilities: {e}")
    print("Please ensure dashboard_sqlite_utils.py is available in app/dashboard_modules/")
    sys.exit(1)

# Configuration
CHECKIN_REVIEWS_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"
PROCESSED_FILES_LOG = "processed_workout_files.json"
CHECK_INTERVAL = 30  # seconds
MAX_FILE_AGE_DAYS = 7  # Only process files from last 7 days

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workout_data_importer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('workout_importer')


class WorkoutDataImporter:
    def __init__(self):
        self.processed_files = self.load_processed_files()
        self.checkin_dir = Path(CHECKIN_REVIEWS_DIR)

    def load_processed_files(self) -> Dict[str, str]:
        """Load the record of previously processed files"""
        try:
            if os.path.exists(PROCESSED_FILES_LOG):
                with open(PROCESSED_FILES_LOG, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load processed files log: {e}")
        return {}

    def save_processed_files(self):
        """Save the record of processed files"""
        try:
            with open(PROCESSED_FILES_LOG, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed files log: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        """Get hash of file to detect changes"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def find_new_json_files(self) -> List[Path]:
        """Find new or changed fitness_wrapped_data JSON files"""
        if not self.checkin_dir.exists():
            logger.warning(
                f"Checkin reviews directory not found: {self.checkin_dir}")
            return []

        new_files = []
        cutoff_date = datetime.now() - timedelta(days=MAX_FILE_AGE_DAYS)

        for json_file in self.checkin_dir.glob("*_fitness_wrapped_data.json"):
            # Check file age
            file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                continue

            file_path_str = str(json_file)
            current_hash = self.get_file_hash(json_file)

            # Check if file is new or changed
            if (file_path_str not in self.processed_files or
                    self.processed_files[file_path_str] != current_hash):
                new_files.append(json_file)
                logger.info(f"Found new/changed file: {json_file.name}")

        return new_files

    def extract_client_name_from_filename(self, filename: str) -> str:
        """Extract client name from fitness_wrapped_data filename"""
        # Format: ClientName_YYYY-MM-DD_fitness_wrapped_data.json
        base_name = filename.replace('_fitness_wrapped_data.json', '')
        # Remove date suffix (last part after last underscore that looks like a date)
        parts = base_name.split('_')
        if len(parts) >= 3 and len(parts[-1]) == 2 and len(parts[-2]) == 2 and len(parts[-3]) == 4:
            # Last 3 parts look like YYYY-MM-DD, remove them
            client_name = '_'.join(parts[:-3]).replace('_', ' ')
        else:
            # Fallback: take everything before the last underscore
            client_name = '_'.join(parts[:-1]).replace('_', ' ')

        return client_name.strip()

    def parse_workout_data(self, fitness_data: Dict) -> List[Dict]:
        """Extract workout sessions from fitness_wrapped_data"""
        workout_sessions = []

        # Get workout data list
        workout_data_list = fitness_data.get('workout_data_list', [])
        if not workout_data_list:
            logger.info("No workout_data_list found in fitness data")
            return workout_sessions

        for workout in workout_data_list:
            try:
                # Extract basic workout info
                workout_name = workout.get('workout_name', 'Unknown Workout')
                workout_date = workout.get('date', '')

                # Parse workout date
                workout_datetime = None
                if workout_date:
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                            try:
                                workout_datetime = datetime.strptime(
                                    workout_date, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(
                            f"Could not parse date '{workout_date}': {e}")

                if not workout_datetime:
                    logger.warning(
                        f"Skipping workout with invalid date: {workout_date}")
                    continue

                # Extract exercises
                exercises = workout.get('exercises', [])
                if not exercises:
                    logger.info(
                        f"No exercises found for workout: {workout_name}")
                    continue

                # Create workout session record
                session = {
                    'workout_name': workout_name,
                    'workout_date': workout_datetime.strftime('%Y-%m-%d'),
                    'exercises': exercises,
                    'raw_workout_data': workout  # Store full workout data as JSON
                }

                workout_sessions.append(session)

            except Exception as e:
                logger.error(f"Error parsing workout data: {e}")
                continue

        return workout_sessions

    def import_workout_sessions(self, client_name: str, workout_sessions: List[Dict], ig_username: Optional[str] = None):
        """Import workout sessions into SQLite database"""
        if not workout_sessions:
            logger.info(f"No workout sessions to import for {client_name}")
            return

        try:
            # Get database connection
            conn = get_db_connection()
            if not conn:
                logger.error("Could not connect to database")
                return

            # Create workout tables if they don't exist
            create_workout_tables_if_not_exist(conn)

            # Get or determine ig_username
            if not ig_username:
                ig_username = get_ig_username_by_name(client_name)
                if not ig_username:
                    logger.warning(
                        f"Could not find ig_username for {client_name}, using client name")
                    ig_username = client_name.lower().replace(' ', '_')

            # Import each workout session
            imported_count = 0
            for session in workout_sessions:
                try:
                    # Prepare workout session data for database
                    workout_session_data = {
                        'ig_username': ig_username,
                        'client_name': client_name,
                        'workout_name': session['workout_name'],
                        'workout_date': session['workout_date'],
                        'exercises': session['exercises'],
                        'raw_data': json.dumps(session['raw_workout_data']),
                        'imported_at': datetime.now().isoformat(),
                        'source': 'fitness_wrapped_data_auto_import'
                    }

                    # Save to database
                    if save_workout_session(conn, workout_session_data):
                        imported_count += 1
                    else:
                        logger.warning(
                            f"Failed to save workout session: {session['workout_name']} on {session['workout_date']}")

                except Exception as e:
                    logger.error(f"Error importing workout session: {e}")
                    continue

            conn.close()
            logger.info(
                f"✅ Successfully imported {imported_count}/{len(workout_sessions)} workout sessions for {client_name}")

        except Exception as e:
            logger.error(
                f"Error importing workout sessions for {client_name}: {e}")

    def process_json_file(self, json_file: Path):
        """Process a single JSON file and import workout data"""
        try:
            logger.info(f"Processing file: {json_file.name}")

            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                fitness_data = json.load(f)

            # Extract client name
            client_name = self.extract_client_name_from_filename(
                json_file.name)
            logger.info(f"Extracted client name: {client_name}")

            # Get ig_username if available in the data
            ig_username = fitness_data.get('ig_username')

            # Parse workout data
            workout_sessions = self.parse_workout_data(fitness_data)
            logger.info(f"Found {len(workout_sessions)} workout sessions")

            # Import to database
            self.import_workout_sessions(
                client_name, workout_sessions, ig_username)

            # Mark file as processed
            file_hash = self.get_file_hash(json_file)
            self.processed_files[str(json_file)] = file_hash
            self.save_processed_files()

        except Exception as e:
            logger.error(f"Error processing file {json_file}: {e}")

    def run_once(self):
        """Run one iteration of file checking and processing"""
        logger.info("Checking for new workout data files...")

        new_files = self.find_new_json_files()
        if not new_files:
            logger.info("No new files found")
            return

        logger.info(f"Found {len(new_files)} new/changed files to process")

        for json_file in new_files:
            self.process_json_file(json_file)

    def run_monitor(self):
        """Run continuous monitoring"""
        logger.info(f"🚀 Starting workout data importer monitor...")
        logger.info(f"📁 Monitoring directory: {self.checkin_dir}")
        logger.info(f"⏱️  Check interval: {CHECK_INTERVAL} seconds")
        logger.info(f"📅 Processing files from last {MAX_FILE_AGE_DAYS} days")

        try:
            while True:
                self.run_once()
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import workout data from JSON files to SQLite database')
    parser.add_argument('--once', action='store_true',
                        help='Run once instead of continuous monitoring')
    parser.add_argument('--file', type=str,
                        help='Process a specific JSON file')
    parser.add_argument('--days', type=int, default=7,
                        help=f'Maximum age of files to process (default: 7 days)')

    args = parser.parse_args()

    # Update configuration based on arguments
    global MAX_FILE_AGE_DAYS
    if args.days:
        MAX_FILE_AGE_DAYS = args.days

    importer = WorkoutDataImporter()

    if args.file:
        # Process specific file
        file_path = Path(args.file)
        if file_path.exists():
            logger.info(f"Processing specific file: {file_path}")
            importer.process_json_file(file_path)
        else:
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
    elif args.once:
        # Run once
        logger.info("Running one-time import...")
        importer.run_once()
    else:
        # Run continuous monitoring
        importer.run_monitor()


if __name__ == "__main__":
    main()
