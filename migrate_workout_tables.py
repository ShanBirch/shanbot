#!/usr/bin/env python3
"""
Migrate existing workout tables to enhanced schema
Safely updates client_workout_sessions table to include new columns
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
    print("✅ Successfully imported SQLite utilities")
except ImportError as e:
    print(f"❌ Error importing SQLite utilities: {e}")
    sys.exit(1)


def migrate_workout_tables():
    """Migrate existing workout tables to enhanced schema"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        print("🔄 Starting workout table migration...")

        # Check current schema of client_workout_sessions
        cursor.execute("PRAGMA table_info(client_workout_sessions)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Existing columns: {existing_columns}")

        # Add new columns if they don't exist
        new_columns = [
            ("total_reps", "INTEGER DEFAULT 0"),
            ("total_sets", "INTEGER DEFAULT 0"),
            ("total_weight_lifted", "REAL DEFAULT 0"),
            ("workout_duration_minutes", "INTEGER"),
            ("session_notes", "TEXT"),
            ("raw_session_data", "TEXT"),
            ("updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ]

        for col_name, col_def in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE client_workout_sessions ADD COLUMN {col_name} {col_def}")
                    print(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Column {col_name} may already exist: {e}")

        # Create exercise_sessions table if it doesn't exist
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
        print("✅ Created exercise_sessions table")

        # Create weekly_goals table if it doesn't exist
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
        print("✅ Created weekly_goals table")

        # Create workout_progressions table if it doesn't exist
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
        print("✅ Created workout_progressions table")

        # Update existing records to populate new calculated fields
        print("🔄 Updating existing records with calculated values...")

        cursor.execute(
            "SELECT session_id, exercises_json FROM client_workout_sessions WHERE exercises_json IS NOT NULL")
        sessions = cursor.fetchall()

        for session_id, exercises_json in sessions:
            if exercises_json:
                try:
                    import json
                    exercises = json.loads(exercises_json)

                    total_reps = 0
                    total_sets = 0
                    total_weight_lifted = 0

                    # Calculate totals from exercises
                    for exercise in exercises:
                        if isinstance(exercise, dict) and 'sets' in exercise:
                            exercise_sets = exercise['sets']
                            if isinstance(exercise_sets, list):
                                total_sets += len(exercise_sets)
                                for set_data in exercise_sets:
                                    if isinstance(set_data, dict):
                                        try:
                                            reps = int(set_data.get('reps', 0)) if set_data.get(
                                                'reps') else 0
                                            weight = float(set_data.get('weight', 0)) if set_data.get(
                                                'weight') else 0
                                            total_reps += reps
                                            total_weight_lifted += (
                                                reps * weight)
                                        except (ValueError, TypeError):
                                            continue

                    # Update session with calculated values
                    cursor.execute("""
                    UPDATE client_workout_sessions 
                    SET total_reps = ?, total_sets = ?, total_weight_lifted = ?, updated_at = ?
                    WHERE session_id = ?
                    """, (total_reps, total_sets, total_weight_lifted, datetime.now().isoformat(), session_id))

                except Exception as e:
                    print(f"⚠️ Error processing session {session_id}: {e}")
                    continue

        # Create indexes for performance
        indexes = [
            ("idx_workout_sessions_client_date",
             "client_workout_sessions(client_name_key, workout_date)"),
            ("idx_exercise_sessions_client_exercise_date",
             "exercise_sessions(client_name_key, exercise_name, workout_date)"),
            ("idx_weekly_goals_client_week",
             "weekly_goals(client_name_key, week_identifier)")
        ]

        for index_name, index_def in indexes:
            try:
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                print(f"✅ Created index: {index_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Index {index_name} may already exist: {e}")

        conn.commit()
        print("✅ Migration completed successfully!")

        # Verify migration
        cursor.execute("PRAGMA table_info(client_workout_sessions)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Final columns: {final_columns}")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM client_workout_sessions")
        session_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM exercise_sessions")
        exercise_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM weekly_goals")
        goals_count = cursor.fetchone()[0]

        print(f"\n📊 Final record counts:")
        print(f"  - Workout sessions: {session_count}")
        print(f"  - Exercise sessions: {exercise_count}")
        print(f"  - Weekly goals: {goals_count}")

        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        if conn:
            conn.close()


def populate_exercise_sessions():
    """Populate exercise_sessions table from existing workout data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        print("🔄 Populating exercise_sessions table...")

        # Get all workout sessions with exercise data
        cursor.execute("""
        SELECT session_id, client_name_key, ig_username, workout_date, exercises_json 
        FROM client_workout_sessions 
        WHERE exercises_json IS NOT NULL AND exercises_json != ''
        """)

        sessions = cursor.fetchall()
        print(f"📋 Processing {len(sessions)} workout sessions...")

        for session_id, client_name_key, ig_username, workout_date, exercises_json in sessions:
            try:
                import json
                exercises = json.loads(exercises_json)

                for exercise in exercises:
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
                                        reps = int(set_data.get('reps', 0)) if set_data.get(
                                            'reps') else 0
                                        weight = float(set_data.get('weight', 0)) if set_data.get(
                                            'weight') else 0
                                        exercise_total_reps += reps
                                        max_weight = max(max_weight, weight)
                                        if weight > 0:
                                            total_weight += weight
                                            weight_count += 1
                                    except (ValueError, TypeError):
                                        continue

                            average_weight = total_weight / weight_count if weight_count > 0 else 0
                            total_volume = sum(
                                int(s.get('reps', 0)) *
                                float(s.get('weight', 0))
                                for s in exercise_sets
                                if isinstance(s, dict) and s.get('reps') and s.get('weight')
                            )

                            # Insert exercise session
                            cursor.execute("""
                            INSERT OR IGNORE INTO exercise_sessions 
                            (session_id, client_name_key, ig_username, workout_date, exercise_name, 
                             sets_json, total_reps, total_sets, max_weight, average_weight, total_volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                session_id, client_name_key, ig_username, workout_date,
                                exercise_name, json.dumps(
                                    exercise_sets), exercise_total_reps,
                                exercise_total_sets, max_weight, average_weight, total_volume
                            ))

            except Exception as e:
                print(f"⚠️ Error processing session {session_id}: {e}")
                continue

        conn.commit()

        # Count results
        cursor.execute("SELECT COUNT(*) FROM exercise_sessions")
        exercise_count = cursor.fetchone()[0]
        print(f"✅ Populated {exercise_count} exercise sessions")

        return True

    except Exception as e:
        print(f"❌ Error populating exercise sessions: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    """Main migration function"""
    print("🚀 Starting Workout Tables Migration")
    print("=" * 50)

    # Step 1: Migrate table schemas
    if not migrate_workout_tables():
        print("❌ Migration failed!")
        return False

    # Step 2: Populate exercise sessions
    if not populate_exercise_sessions():
        print("❌ Exercise session population failed!")
        return False

    print("\n✅ All migrations completed successfully!")
    print("📊 Your SQLite database now has comprehensive workout storage!")
    return True


if __name__ == "__main__":
    main()
