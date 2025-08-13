#!/usr/bin/env python3
"""
Weekly Program Updater for All Clients
=====================================

This script:
1. Gets all client data from the SQLite database
2. Applies the smart progression algorithm (6->8->10->12->15 reps)
3. Creates the progression_history.json file in the expected format
4. Runs the weekly_program_updater for all clients

Usage: python run_weekly_program_updater_all_clients.py
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            'weekly_updater_all_clients.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class WeeklyProgressionSystem:
    def __init__(self):
        self.db_path = 'app/analytics_data_good.sqlite'
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        self.barbell_increments = 2.5

    def get_all_clients_with_workouts(self):
        """Get all clients who have workout data in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logging.info("=== FINDING ALL CLIENTS WITH WORKOUT DATA ===")

            # Get all clients with recent workout sessions (last 30 days)
            recent_date = (datetime.now() - timedelta(days=30)
                           ).strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT DISTINCT client_name_key, COUNT(*) as workout_count,
                       MAX(workout_date) as last_workout
                FROM client_workout_sessions 
                WHERE workout_date >= ?
                GROUP BY client_name_key
                ORDER BY workout_count DESC
            """, (recent_date,))

            clients = cursor.fetchall()

            logging.info(f"Found {len(clients)} clients with recent workouts:")
            for client_key, count, last_workout in clients:
                logging.info(
                    f"  - {client_key}: {count} workouts (last: {last_workout})")

            conn.close()
            return [client[0] for client in clients]

        except Exception as e:
            logging.error(f"Database error: {e}")
            return []

    def transform_client_key_to_display_name(self, client_key):
        """Transform database client_key to display name for Trainerize"""
        # Convert 'alice_forster' to 'Alice Forster'
        name_parts = client_key.split('_')
        return ' '.join(word.capitalize() for word in name_parts)

    def apply_rep_progression_algorithm(self, current_reps):
        """Apply the 6->8->10->12->15 rep progression algorithm"""
        try:
            current_reps = int(current_reps)
        except (ValueError, TypeError):
            logging.warning(
                f"Could not convert current_reps '{current_reps}' to int. Defaulting to 6.")
            current_reps = 6

        if current_reps >= 15:
            return 6  # Reset to 6 when reaching 15
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
            current_idx = None
            for i, weight in enumerate(self.dumbbell_weights):
                if weight >= current_weight:
                    current_idx = i
                    break
            if current_idx is not None and current_idx < len(self.dumbbell_weights) - 1:
                return self.dumbbell_weights[current_idx + 1]
            else:
                return current_weight + 2.5
        else:
            return current_weight + self.barbell_increments

    def get_client_workout_progressions(self, client_key):
        """Get workout progressions for a specific client with smart progression algorithm"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logging.info(f"\n=== ANALYZING {client_key.upper()} ===")

            # Get client's recent workouts (last 14 days to get most current data)
            recent_date = (datetime.now() - timedelta(days=14)
                           ).strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT workout_date, workout_name, exercises_json 
                FROM client_workout_sessions 
                WHERE client_name_key = ? AND workout_date >= ?
                ORDER BY workout_date DESC 
                LIMIT 10
            """, (client_key, recent_date))

            workouts = cursor.fetchall()

            if not workouts:
                logging.info(f"  No recent workouts found for {client_key}")
                conn.close()
                return {}

            # IMPROVEMENT: Also get programmed workout structure to detect intended set counts
            programmed_set_counts = self.get_programmed_set_counts(
                client_key, cursor)

            # Process exercises and apply smart progression
            exercise_progressions = {}

            for date, workout_name, exercises_json in workouts:
                try:
                    exercises = json.loads(exercises_json)
                    logging.info(
                        f"  {date} - {workout_name} ({len(exercises)} exercises)")

                    for exercise in exercises:
                        exercise_name = exercise.get('name', 'Unknown')
                        completed_sets = exercise.get('sets', [])

                        if completed_sets and len(completed_sets) > 0 and exercise_name not in exercise_progressions:
                            # IMPROVEMENT: Get programmed set count vs completed set count
                            completed_set_count = len(completed_sets)
                            programmed_set_count = programmed_set_counts.get(
                                exercise_name, completed_set_count)

                            # Use the higher of programmed vs completed (in case they did extra sets)
                            target_set_count = max(
                                programmed_set_count, completed_set_count)

                            logging.info(
                                f"    - {exercise_name}: Completed {completed_set_count} sets, Programmed {programmed_set_count} sets, Target {target_set_count} sets")

                            # Get the best completed set for progression data
                            best_set = max(completed_sets, key=lambda s: (
                                float(s.get('weight', 0)), int(s.get('reps', 0))))

                            current_weight = float(best_set.get('weight', 0))
                            current_reps = int(best_set.get('reps', 0))

                            # IMPROVEMENT: Check if this is a bodyweight exercise
                            is_bodyweight = self.is_bodyweight_exercise(
                                exercise_name, current_weight)

                            if current_reps > 0:  # Only need reps > 0, weight can be 0 for bodyweight
                                # Apply smart progression algorithm
                                next_reps = self.apply_rep_progression_algorithm(
                                    current_reps)
                                increase_weight = (
                                    next_reps == 6 and current_reps >= 15 and not is_bodyweight)
                                next_weight = self.get_next_weight(
                                    current_weight, exercise_name, increase_weight) if not is_bodyweight else 0

                                # IMPROVEMENT: Generate goals for ALL target sets (completed + missing)
                                recommended_reps = self.generate_smart_set_goals(
                                    target_set_count, completed_sets, next_weight, next_reps, is_bodyweight)

                                # Create the progression entry
                                exercise_progressions[exercise_name] = {
                                    'current_weight': current_weight,
                                    'current_reps': str(current_reps),
                                    'recommended_weight': next_weight,
                                    'recommended_reps': recommended_reps,
                                    'set_count': target_set_count,
                                    'completed_sets': completed_set_count,
                                    'programmed_sets': programmed_set_count,
                                    'is_bodyweight': is_bodyweight,
                                    'reason': f"Progressive overload: {self.format_exercise_display(current_weight, current_reps, is_bodyweight)} → {self.format_exercise_display(next_weight, next_reps, is_bodyweight)} ({target_set_count} sets)",
                                    'confidence': 0.8,
                                    'action_type': 'progression'
                                }

                                logging.info(
                                    f"    - {exercise_name}: {self.format_exercise_display(current_weight, current_reps, is_bodyweight)} -> {self.format_exercise_display(next_weight, next_reps, is_bodyweight)} ({target_set_count} sets)")

                except json.JSONDecodeError:
                    logging.warning(
                        f"Could not parse exercises for {client_key} on {date}")
                    continue

            conn.close()
            return exercise_progressions

        except Exception as e:
            logging.error(f"Error getting progressions for {client_key}: {e}")
            return {}

    def get_programmed_set_counts(self, client_key, cursor):
        """Get the programmed/intended set counts for exercises from workout templates or historical data"""
        try:
            logging.info(
                f"  Detecting programmed set counts for {client_key}...")

            # Strategy: Look at historical data to find the MOST COMMON set count for each exercise
            # This represents the "programmed" workout structure
            cursor.execute("""
                SELECT exercises_json 
                FROM client_workout_sessions 
                WHERE client_name_key = ?
                ORDER BY workout_date DESC 
                LIMIT 20
            """, (client_key,))

            historical_workouts = cursor.fetchall()
            # {exercise_name: [set_count1, set_count2, ...]}
            exercise_set_counts = {}

            for (exercises_json,) in historical_workouts:
                try:
                    exercises = json.loads(exercises_json)
                    for exercise in exercises:
                        exercise_name = exercise.get('name', 'Unknown')
                        sets = exercise.get('sets', [])
                        set_count = len(sets)

                        if exercise_name not in exercise_set_counts:
                            exercise_set_counts[exercise_name] = []
                        exercise_set_counts[exercise_name].append(set_count)

                except json.JSONDecodeError:
                    continue

            # Find the most common (mode) set count for each exercise
            programmed_counts = {}
            for exercise_name, counts in exercise_set_counts.items():
                if counts:
                    # Get the most common set count
                    mode_count = max(set(counts), key=counts.count)
                    programmed_counts[exercise_name] = mode_count
                    logging.info(
                        f"    - {exercise_name}: Most common set count = {mode_count} (from {counts})")

            return programmed_counts

        except Exception as e:
            logging.warning(f"Error detecting programmed set counts: {e}")
            return {}

    def generate_smart_set_goals(self, target_set_count, completed_sets, next_weight, next_reps, is_bodyweight):
        """Generate goals for ALL target sets, using progression logic for completed sets and intelligent defaults for missing sets"""
        goals = []

        # Strategy:
        # - For sets that were completed: Use progression from their data
        # - For sets that weren't completed: Use intelligent defaults based on the exercise

        completed_count = len(completed_sets)

        for i in range(target_set_count):
            set_num = i + 1

            if i < completed_count:
                # This set was completed - use progression logic
                if is_bodyweight:
                    goals.append(f"S{set_num}: {next_reps}")
                else:
                    goals.append(f"S{set_num}: {next_weight}kg*{next_reps}")
            else:
                # This set was NOT completed - use intelligent default
                if is_bodyweight:
                    # For bodyweight, reduce reps slightly for missing sets
                    default_reps = max(6, next_reps - 2)  # Slightly easier
                    goals.append(f"S{set_num}: {default_reps}")
                else:
                    # For weighted, reduce weight or reps slightly for missing sets
                    if next_weight > 10:
                        default_weight = next_weight - 5  # Reduce weight
                        goals.append(
                            f"S{set_num}: {default_weight}kg*{next_reps}")
                    else:
                        default_reps = max(6, next_reps - 2)  # Reduce reps
                        goals.append(
                            f"S{set_num}: {next_weight}kg*{default_reps}")

        return " | ".join(goals)

    def is_bodyweight_exercise(self, exercise_name, current_weight):
        """Determine if an exercise is bodyweight based on name and weight data"""
        bodyweight_keywords = [
            'push up', 'pushup', 'pull up', 'pullup', 'chin up', 'chinup',
            'dip', 'plank', 'burpee', 'jumping jack', 'mountain climber',
            'squat jump', 'lunge', 'bodyweight', 'air squat', 'wall sit',
            'calf raise', 'sit up', 'situp', 'crunch', 'leg raise'
        ]

        exercise_lower = exercise_name.lower()

        # Check if exercise name contains bodyweight keywords
        name_indicates_bodyweight = any(
            keyword in exercise_lower for keyword in bodyweight_keywords)

        # Check if weight is consistently 0 (indicating bodyweight)
        weight_indicates_bodyweight = current_weight == 0

        return name_indicates_bodyweight or weight_indicates_bodyweight

    def format_exercise_display(self, weight, reps, is_bodyweight):
        """Format exercise display for logging"""
        if is_bodyweight:
            return f"{reps} reps"
        else:
            return f"{weight}kg x {reps}"

    def create_progression_history_file(self):
        """Create the progression_history.json file for all clients"""
        logging.info("=== CREATING PROGRESSION HISTORY FILE ===")

        # Get all clients
        client_keys = self.get_all_clients_with_workouts()

        if not client_keys:
            logging.error("No clients found with workout data")
            return False

        progression_history = {}

        for client_key in client_keys:
            display_name = self.transform_client_key_to_display_name(
                client_key)
            exercise_progressions = self.get_client_workout_progressions(
                client_key)

            if exercise_progressions:
                # Create the progression history entry
                progression_history[display_name] = [{
                    'date': datetime.now().isoformat(),
                    'progressions': exercise_progressions
                }]
                logging.info(
                    f"  Created progressions for {display_name} ({len(exercise_progressions)} exercises)")
            else:
                logging.info(f"  No progressions created for {display_name}")

        # Save progression history file
        with open('progression_history.json', 'w') as f:
            json.dump(progression_history, f, indent=2)

        logging.info(
            f"Saved progression_history.json with {len(progression_history)} clients")

        # Also save a backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"progression_history_backup_{timestamp}.json"
        with open(backup_filename, 'w') as f:
            json.dump(progression_history, f, indent=2)

        logging.info(f"Saved backup: {backup_filename}")
        return True

    def run_weekly_program_updater(self):
        """Run the weekly program updater for all clients"""
        logging.info("=== RUNNING WEEKLY PROGRAM UPDATER ===")

        # Load progression history to get client list
        try:
            with open('progression_history.json', 'r') as f:
                progression_history = json.load(f)
        except FileNotFoundError:
            logging.error(
                "progression_history.json not found! Run create_progression_history_file() first")
            return False

        if not progression_history:
            logging.error("No clients in progression history")
            return False

        # Create the data structure expected by weekly_program_updater
        clients_data = {}
        for client_display_name in progression_history.keys():
            # Empty dict - the updater will discover workouts dynamically
            clients_data[client_display_name] = {}

        logging.info(
            f"Preparing to update {len(clients_data)} clients: {list(clients_data.keys())}")

        # Initialize the automation system
        automation = TrainerizeAutomation()

        try:
            # Login to Trainerize
            logging.info("Logging into Trainerize...")
            username = "Shannonbirch@cocospersonaltraining.com"
            password = "cyywp7nyk2"

            if not automation.login(username, password):
                logging.error("Failed to login to Trainerize")
                return False

            logging.info("Successfully logged into Trainerize!")
            automation.handle_notification_popup()

            # Process all clients
            results = automation.process_multiple_clients(clients_data)

            # Show final results
            logging.info("\n" + "=" * 60)
            logging.info("WEEKLY PROGRAM UPDATE COMPLETE")
            logging.info("=" * 60)

            successful = sum(1 for result in results.values()
                             if result.get('status') == 'success')
            failed = len(results) - successful

            logging.info(f"\nFINAL RESULTS:")
            logging.info(f"  Successfully updated: {successful} clients")
            logging.info(f"  Failed: {failed} clients")

            if failed > 0:
                logging.info(f"\nFailed clients:")
                for client, result in results.items():
                    if result.get('status') != 'success':
                        logging.info(
                            f"  • {client}: {result.get('error', 'Unknown error')}")

            logging.info(f"\nAll successful clients now have:")
            logging.info(f"  • Smart progressive overload applied")
            logging.info(
                f"  • Rep progression (6->8->10->12->15) with weight increases")
            logging.info(
                f"  • Equipment-specific increments (dumbbell vs barbell)")
            logging.info(
                f"  • Goals format: GOALS: S1: weightkg*reps | S2: weightkg*reps | S3: weightkg*reps")

            return successful > 0

        except Exception as e:
            logging.error(f"Error during weekly program update: {e}")
            return False

        finally:
            # Cleanup
            try:
                automation.cleanup()
            except:
                pass


def main():
    """Main function to run the complete weekly program update process"""
    print("🏋️ WEEKLY PROGRAM UPDATER FOR ALL CLIENTS")
    print("=" * 60)
    print("This script will:")
    print("  1. Get all client data from the database")
    print("  2. Apply smart progression algorithm (6->8->10->12->15 reps)")
    print("  3. Create progression_history.json file")
    print("  4. Run weekly_program_updater for all clients")
    print("=" * 60)

    system = WeeklyProgressionSystem()

    # Step 1: Create progression history file
    print("\nSTEP 1: Creating progression history from database...")
    if not system.create_progression_history_file():
        print("Failed to create progression history file")
        return

    # Step 2: Run the weekly program updater
    print("\nSTEP 2: Running weekly program updater...")

    # Confirm before proceeding
    response = input(
        "\nProceed with updating all client workouts in Trainerize? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return

    if system.run_weekly_program_updater():
        print("\nWeekly program update completed successfully!")
    else:
        print("\nWeekly program update failed!")


if __name__ == "__main__":
    main()
