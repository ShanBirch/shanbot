#!/usr/bin/env python3
"""
Simplified Weekly Program Updater
=================================

This script:
1. Gets client workout data from the database
2. Applies the 6->8->10->12->15 rep progression algorithm
3. Updates client workouts in Trainerize

Usage: python update_programs_simple.py
"""

import sqlite3
import json
import logging
import sys
from datetime import datetime, timedelta
from weekly_program_updater import TrainerizeAutomation

# Configure logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workout_updates.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)


class SimpleWorkoutUpdater:
    def __init__(self):
        self.db_path = 'app/analytics_data_good.sqlite'
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]

    def get_clients_with_workouts(self):
        """Get all clients who have recent workout data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get clients with workouts in the last 14 days
            cutoff_date = (datetime.now() - timedelta(days=14)
                           ).strftime('%Y-%m-%d')

            query = """
            SELECT DISTINCT client_name 
            FROM workout_sessions 
            WHERE date >= ? 
            AND exercises IS NOT NULL 
            AND exercises != ''
            ORDER BY client_name
            """

            cursor.execute(query, (cutoff_date,))
            clients = [row[0] for row in cursor.fetchall()]

            conn.close()
            logging.info(f"Found {len(clients)} clients with recent workouts")
            return clients

        except Exception as e:
            logging.error(f"Error getting clients: {e}")
            return []

    def get_client_progressions(self, client_name):
        """Get workout progressions for a specific client"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get latest workout data for this client
            query = """
            SELECT date, workout_name, exercises
            FROM workout_sessions 
            WHERE client_name = ? 
            AND exercises IS NOT NULL 
            AND exercises != ''
            ORDER BY date DESC
            LIMIT 5
            """

            cursor.execute(query, (client_name,))
            workouts = cursor.fetchall()
            conn.close()

            progressions = {}

            for date, workout_name, exercises_json in workouts:
                try:
                    exercises = json.loads(exercises_json)
                    workout_progressions = {}

                    for exercise in exercises:
                        exercise_name = exercise.get('name', '')
                        if not exercise_name:
                            continue

                        # Get current performance
                        sets = exercise.get('sets', [])
                        if not sets:
                            continue

                        # Find best set (highest reps)
                        best_reps = 0
                        current_weight = 0

                        for set_data in sets:
                            if isinstance(set_data, dict):
                                reps = set_data.get('reps', 0)
                                weight = set_data.get('weight', 0)
                                if reps > best_reps:
                                    best_reps = reps
                                    current_weight = weight

                        if best_reps == 0:
                            continue

                        # Apply progression algorithm
                        next_reps = self.apply_rep_progression(best_reps)
                        increase_weight = (next_reps == 6 and best_reps >= 15)
                        next_weight = self.get_next_weight(
                            current_weight, exercise_name, increase_weight)

                        workout_progressions[exercise_name] = {
                            'current_weight': current_weight,
                            'current_reps': best_reps,
                            'next_weight': next_weight,
                            'next_reps': next_reps,
                            'recommended_reps': f"GOALS: S1: {next_weight}kg*{next_reps} | S2: {next_weight}kg*{next_reps} | S3: {next_weight}kg*{next_reps}"
                        }

                        logging.info(
                            f"  {exercise_name}: {current_weight}kg x {best_reps} -> {next_weight}kg x {next_reps}")

                    if workout_progressions:
                        progressions[client_name] = [{
                            'date': date,
                            'progressions': workout_progressions
                        }]
                        break  # Use most recent workout with data

                except Exception as e:
                    logging.error(
                        f"Error processing workout for {client_name}: {e}")
                    continue

            return progressions

        except Exception as e:
            logging.error(f"Error getting progressions for {client_name}: {e}")
            return {}

    def apply_rep_progression(self, current_reps):
        """Apply the 6->8->10->12->15 rep progression algorithm"""
        if current_reps >= 15:
            return 6
        elif current_reps >= 12:
            return 15
        elif current_reps >= 10:
            return 12
        elif current_reps >= 8:
            return 10
        elif current_reps >= 6:
            return 8
        else:
            return 6

    def get_next_weight(self, current_weight, exercise_name, increase_weight=False):
        """Get the next appropriate weight based on equipment type"""
        if not increase_weight:
            return current_weight

        is_dumbbell = any(keyword in exercise_name.lower() for keyword in
                          ['dumbbell', 'd.b', 'db', 'dumbell'])

        if is_dumbbell:
            # Find next dumbbell weight
            for weight in self.dumbbell_weights:
                if weight > current_weight:
                    return weight
            return current_weight + 2.5
        else:
            # Barbell/machine increment
            return current_weight + 2.5

    def create_progression_file(self, all_progressions):
        """Create the progression_history.json file"""
        try:
            with open('progression_history.json', 'w') as f:
                json.dump(all_progressions, f, indent=2)

            # Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'progression_history_backup_{timestamp}.json'
            with open(backup_filename, 'w') as f:
                json.dump(all_progressions, f, indent=2)

            logging.info(
                f"Created progression_history.json with {len(all_progressions)} clients")
            logging.info(f"Backup saved as {backup_filename}")
            return True

        except Exception as e:
            logging.error(f"Error creating progression file: {e}")
            return False


def main():
    print("=" * 60)
    print("SIMPLE WEEKLY PROGRAM UPDATER")
    print("=" * 60)

    updater = SimpleWorkoutUpdater()

    # Get all clients with recent workouts
    clients = updater.get_clients_with_workouts()
    if not clients:
        print("No clients found with recent workout data.")
        return

    print(f"\nFound {len(clients)} clients with recent workouts:")
    for client in clients:
        print(f"  - {client}")

    # Get progressions for all clients
    print("\nAnalyzing workout progressions...")
    all_progressions = {}

    for client in clients:
        print(f"\nProcessing {client}...")
        progressions = updater.get_client_progressions(client)
        if progressions:
            all_progressions.update(progressions)
            exercise_count = len(progressions[client][0]['progressions'])
            print(f"  Created progressions for {exercise_count} exercises")
        else:
            print(f"  No progressions created")

    if not all_progressions:
        print("No progressions created. Exiting.")
        return

    # Create progression file
    if not updater.create_progression_file(all_progressions):
        print("Failed to create progression file. Exiting.")
        return

    print(f"\nProgression Summary:")
    print(f"  - {len(all_progressions)} clients with progressions")
    total_exercises = sum(len(data[0]['progressions'])
                          for data in all_progressions.values())
    print(f"  - {total_exercises} exercises with new goals")
    print(f"  - Algorithm: 6->8->10->12->15 reps, then +weight and reset to 6")

    # Ask to proceed with Trainerize updates
    response = input(
        f"\nProceed with updating all {len(all_progressions)} clients in Trainerize? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    # Run Trainerize automation
    print("\nStarting Trainerize automation...")
    try:
        automation = TrainerizeAutomation()

        # Login credentials
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        print("Logging into Trainerize...")
        if not automation.login(username, password):
            print("Failed to login to Trainerize")
            return

        print("Successfully logged in!")

        # Process all clients
        results = automation.process_multiple_clients(all_progressions)

        # Show results
        print("\n" + "=" * 60)
        print("PROGRAM UPDATE COMPLETE")
        print("=" * 60)

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\nResults:")
        print(f"  Successfully updated: {successful} clients")
        print(f"  Failed: {failed} clients")

        if failed > 0:
            print(f"\nFailed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    print(
                        f"  - {client}: {result.get('error', 'Unknown error')}")

        print(f"\nAll successful clients now have updated workout goals!")

    except Exception as e:
        logging.error(f"Error during Trainerize automation: {e}")
        print(f"Error: {e}")

    finally:
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
