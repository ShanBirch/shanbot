#!/usr/bin/env python3
"""
Comprehensive Workout Storage System for SQLite
Ensures all workout data is properly stored, tracked, and accumulated over time.
Includes weekly goals storage and complete workout session data.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
    print("✅ Successfully imported SQLite utilities")
except ImportError as e:
    print(f"❌ Error importing SQLite utilities: {e}")
    sys.exit(1)


class ComprehensiveWorkoutStorage:
    def __init__(self):
        self.db_path = r"app\analytics_data_good.sqlite"

    def create_enhanced_workout_tables(self):
        """Create comprehensive workout storage tables"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Enhanced client_workout_sessions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_workout_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name_key TEXT NOT NULL,
                ig_username TEXT,
                workout_date TEXT NOT NULL,
                week_identifier TEXT NOT NULL,
                workout_name TEXT,
                exercises_json TEXT,
                raw_session_data TEXT,
                total_reps INTEGER DEFAULT 0,
                total_sets INTEGER DEFAULT 0,
                total_weight_lifted REAL DEFAULT 0,
                workout_duration_minutes INTEGER,
                session_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Enhanced exercises table with full details
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercise_sessions (
                exercise_session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                client_name_key TEXT NOT NULL,
                ig_username TEXT,
                workout_date TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                sets_json TEXT NOT NULL,
                total_reps INTEGER DEFAULT 0,
                total_sets INTEGER DEFAULT 0,
                max_weight REAL DEFAULT 0,
                average_weight REAL DEFAULT 0,
                total_volume REAL DEFAULT 0,
                exercise_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES client_workout_sessions(session_id)
            )
            """)

            # Weekly goals table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name_key TEXT NOT NULL,
                ig_username TEXT,
                week_identifier TEXT NOT NULL,
                workout_name TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                target_weight REAL,
                target_reps INTEGER,
                target_sets INTEGER,
                goal_type TEXT DEFAULT 'progression',
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                achieved_at TEXT,
                notes TEXT
            )
            """)

            # Workout progression tracking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workout_progressions (
                progression_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name_key TEXT NOT NULL,
                ig_username TEXT,
                exercise_name TEXT NOT NULL,
                week_identifier TEXT NOT NULL,
                previous_performance TEXT,
                current_performance TEXT,
                progression_type TEXT,
                improvement_percentage REAL,
                progression_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create indexes for performance
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workout_sessions_client_date 
            ON client_workout_sessions(client_name_key, workout_date)
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_exercise_sessions_client_exercise_date 
            ON exercise_sessions(client_name_key, exercise_name, workout_date)
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_weekly_goals_client_week 
            ON weekly_goals(client_name_key, week_identifier)
            """)

            conn.commit()
            logger.info(
                "✅ Successfully created enhanced workout storage tables")
            return True

        except Exception as e:
            logger.error(f"❌ Error creating enhanced workout tables: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def store_comprehensive_workout_session(self, client_name: str, session_data: Dict, ig_username: Optional[str] = None):
        """Store comprehensive workout session data with full exercise details"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Prepare client name key
            client_name_key = client_name.lower().replace(' ', '_').replace("'", "")

            # Parse workout date
            workout_date_str = session_data.get('date')
            if isinstance(workout_date_str, str):
                try:
                    workout_date_obj = datetime.strptime(
                        workout_date_str, '%Y-%m-%d')
                except ValueError:
                    try:
                        workout_date_obj = datetime.strptime(
                            workout_date_str, '%d %b %Y')
                    except ValueError:
                        logger.error(
                            f"Could not parse date: {workout_date_str}")
                        return False
            else:
                workout_date_obj = workout_date_str

            workout_date_iso = workout_date_obj.strftime('%Y-%m-%d')
            iso_year, iso_week, _ = workout_date_obj.isocalendar()
            week_identifier = f"{iso_year}-W{iso_week:02d}"

            workout_name = session_data.get('workout_type', 'Unknown Workout')
            exercises_list = session_data.get('exercises', [])

            # Calculate session totals
            total_reps = 0
            total_sets = 0
            total_weight_lifted = 0

            for exercise in exercises_list:
                if isinstance(exercise, dict) and 'sets' in exercise:
                    exercise_sets = exercise['sets']
                    if isinstance(exercise_sets, list):
                        total_sets += len(exercise_sets)
                        for set_data in exercise_sets:
                            if isinstance(set_data, dict):
                                reps = set_data.get('reps', 0)
                                weight = set_data.get('weight', 0)
                                try:
                                    reps = int(reps) if reps else 0
                                    weight = float(weight) if weight else 0
                                    total_reps += reps
                                    total_weight_lifted += (reps * weight)
                                except (ValueError, TypeError):
                                    continue

            # Insert or update workout session
            cursor.execute("""
            INSERT OR REPLACE INTO client_workout_sessions 
            (client_name_key, ig_username, workout_date, week_identifier, workout_name, 
             exercises_json, raw_session_data, total_reps, total_sets, total_weight_lifted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_name_key, ig_username, workout_date_iso, week_identifier,
                workout_name, json.dumps(
                    exercises_list), json.dumps(session_data),
                total_reps, total_sets, total_weight_lifted
            ))

            session_id = cursor.lastrowid

            # Store individual exercise sessions
            for exercise in exercises_list:
                if isinstance(exercise, dict) and 'name' in exercise and 'sets' in exercise:
                    exercise_name = exercise['name']
                    exercise_sets = exercise['sets']

                    if isinstance(exercise_sets, list) and exercise_sets:
                        # Calculate exercise statistics
                        exercise_total_reps = 0
                        exercise_total_sets = len(exercise_sets)
                        max_weight = 0
                        total_weight = 0
                        weight_count = 0

                        for set_data in exercise_sets:
                            if isinstance(set_data, dict):
                                try:
                                    reps = int(set_data.get('reps', 0))
                                    weight = float(set_data.get('weight', 0))
                                    exercise_total_reps += reps
                                    max_weight = max(max_weight, weight)
                                    if weight > 0:
                                        total_weight += weight
                                        weight_count += 1
                                except (ValueError, TypeError):
                                    continue

                        average_weight = total_weight / weight_count if weight_count > 0 else 0
                        total_volume = sum(
                            int(s.get('reps', 0)) * float(s.get('weight', 0))
                            for s in exercise_sets
                            if isinstance(s, dict) and s.get('reps') and s.get('weight')
                        )

                        # Insert exercise session
                        cursor.execute("""
                        INSERT OR REPLACE INTO exercise_sessions 
                        (session_id, client_name_key, ig_username, workout_date, exercise_name, 
                         sets_json, total_reps, total_sets, max_weight, average_weight, total_volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            session_id, client_name_key, ig_username, workout_date_iso,
                            exercise_name, json.dumps(
                                exercise_sets), exercise_total_reps,
                            exercise_total_sets, max_weight, average_weight, total_volume
                        ))

            conn.commit()
            logger.info(
                f"✅ Stored comprehensive workout session for {client_name} on {workout_date_iso}")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing comprehensive workout session: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def store_weekly_goals(self, client_name: str, goals_data: Dict, ig_username: Optional[str] = None):
        """Store weekly goals in SQLite database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            client_name_key = client_name.lower().replace(' ', '_').replace("'", "")

            # Get current week identifier
            now = datetime.now()
            iso_year, iso_week, _ = now.isocalendar()
            week_identifier = f"{iso_year}-W{iso_week:02d}"

            # Store goals for each workout type
            for workout_name, exercises in goals_data.items():
                for exercise_goal in exercises:
                    if isinstance(exercise_goal, dict) and 'exercise_name' in exercise_goal:
                        cursor.execute("""
                        INSERT OR REPLACE INTO weekly_goals 
                        (client_name_key, ig_username, week_identifier, workout_name, exercise_name, 
                         target_weight, target_reps, goal_type, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            client_name_key, ig_username, week_identifier, workout_name,
                            exercise_goal['exercise_name'],
                            float(exercise_goal.get('weight', 0)) if exercise_goal.get(
                                'weight', '').replace('.', '').isdigit() else None,
                            int(exercise_goal.get('reps', 0)) if exercise_goal.get(
                                'reps', '').isdigit() else None,
                            'weekly_progression', 'active'
                        ))

            conn.commit()
            logger.info(
                f"✅ Stored weekly goals for {client_name} (week {week_identifier})")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing weekly goals: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def import_fitness_wrapped_data(self, json_file_path: str):
        """Import fitness wrapped data from JSON file to comprehensive storage"""
        try:
            with open(json_file_path, 'r') as f:
                fitness_data = json.load(f)

            client_name = fitness_data.get('name')
            if not client_name:
                logger.error("No client name found in fitness data")
                return False

            # Try to find IG username (you might need to implement this lookup)
            ig_username = None  # You can implement lookup logic here

            # Import workout sessions
            workout_data = fitness_data.get('workout_data', [])
            if workout_data:
                for session in workout_data:
                    self.store_comprehensive_workout_session(
                        client_name, session, ig_username)
                logger.info(
                    f"✅ Imported {len(workout_data)} workout sessions for {client_name}")

            return True

        except Exception as e:
            logger.error(f"❌ Error importing fitness wrapped data: {e}")
            return False

    def import_weekly_goals_from_json(self, goals_file_path: str = "weekly_progressions.json"):
        """Import weekly goals from JSON file to SQLite"""
        try:
            if not os.path.exists(goals_file_path):
                logger.warning(f"Goals file not found: {goals_file_path}")
                return False

            with open(goals_file_path, 'r') as f:
                goals_data = json.load(f)

            for client_key, client_goals in goals_data.items():
                # Convert client key back to readable name if needed
                client_name = client_key.replace('_', ' ').title()
                self.store_weekly_goals(client_name, client_goals)

            logger.info(
                f"✅ Imported weekly goals for {len(goals_data)} clients")
            return True

        except Exception as e:
            logger.error(f"❌ Error importing weekly goals: {e}")
            return False

    def get_client_workout_history(self, client_name: str, weeks_back: int = 8):
        """Get comprehensive workout history for a client"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            client_name_key = client_name.lower().replace(' ', '_').replace("'", "")
            cutoff_date = (datetime.now() -
                           timedelta(weeks=weeks_back)).strftime('%Y-%m-%d')

            # Get workout sessions
            cursor.execute("""
            SELECT workout_date, workout_name, total_reps, total_sets, total_weight_lifted,
                   exercises_json, raw_session_data
            FROM client_workout_sessions 
            WHERE client_name_key = ? AND workout_date >= ?
            ORDER BY workout_date DESC
            """, (client_name_key, cutoff_date))

            sessions = cursor.fetchall()

            # Get exercise details
            cursor.execute("""
            SELECT workout_date, exercise_name, total_reps, total_sets, max_weight, 
                   average_weight, total_volume, sets_json
            FROM exercise_sessions 
            WHERE client_name_key = ? AND workout_date >= ?
            ORDER BY workout_date DESC, exercise_name
            """, (client_name_key, cutoff_date))

            exercises = cursor.fetchall()

            # Get current goals
            cursor.execute("""
            SELECT workout_name, exercise_name, target_weight, target_reps, status
            FROM weekly_goals 
            WHERE client_name_key = ? AND status = 'active'
            ORDER BY workout_name, exercise_name
            """, (client_name_key,))

            goals = cursor.fetchall()

            return {
                'sessions': sessions,
                'exercises': exercises,
                'goals': goals,
                'client_name': client_name,
                'weeks_analyzed': weeks_back
            }

        except Exception as e:
            logger.error(f"❌ Error getting workout history: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def run_comprehensive_import(self, checkin_reviews_dir: str = "output/checkin_reviews"):
        """Run comprehensive import of all available data"""
        try:
            logger.info("🚀 Starting comprehensive workout data import...")

            # 1. Create enhanced tables
            if not self.create_enhanced_workout_tables():
                return False

            # 2. Import weekly goals
            self.import_weekly_goals_from_json()

            # 3. Import all recent fitness wrapped data
            if os.path.exists(checkin_reviews_dir):
                json_files = [f for f in os.listdir(
                    checkin_reviews_dir) if f.endswith('_fitness_wrapped_data.json')]
                logger.info(
                    f"Found {len(json_files)} fitness wrapped data files")

                for json_file in json_files:
                    file_path = os.path.join(checkin_reviews_dir, json_file)
                    self.import_fitness_wrapped_data(file_path)

            logger.info("✅ Comprehensive import completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Error in comprehensive import: {e}")
            return False


def main():
    """Main function to run comprehensive workout storage setup"""
    print("🏋️ Comprehensive Workout Storage System")
    print("=" * 60)

    storage_system = ComprehensiveWorkoutStorage()

    # Run comprehensive import
    success = storage_system.run_comprehensive_import()

    if success:
        print("✅ All workout data has been imported and organized in SQLite!")
        print("\n📊 Database now contains:")
        print("  - client_workout_sessions: Complete workout sessions")
        print("  - exercise_sessions: Detailed exercise data")
        print("  - weekly_goals: Current and historical goals")
        print("  - workout_progressions: Progress tracking")

        # Test with Alice
        print("\n🧪 Testing with Alice Forster...")
        history = storage_system.get_client_workout_history("Alice Forster")
        if history:
            print(f"  ✅ Found {len(history['sessions'])} sessions")
            print(f"  ✅ Found {len(history['exercises'])} exercise records")
            print(f"  ✅ Found {len(history['goals'])} active goals")
        else:
            print("  ❌ No data found for Alice")
    else:
        print("❌ Import failed - check logs for details")


if __name__ == "__main__":
    main()
