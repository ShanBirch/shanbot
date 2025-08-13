#!/usr/bin/env python3
"""
Check Client Workout Data
========================

This script checks what client workout data is available in the database
and shows a preview of what progressions would be applied.

Usage: python check_client_workout_data.py
"""

import sqlite3
import json
from datetime import datetime, timedelta


class ClientWorkoutChecker:
    def __init__(self):
        self.db_path = 'app/analytics_data_good.sqlite'
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]

    def get_all_clients_with_workouts(self):
        """Get all clients who have workout data in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            print("=== CHECKING DATABASE FOR CLIENT WORKOUT DATA ===")

            # Get all clients with workout sessions in the last 30 days
            recent_date = (datetime.now() - timedelta(days=30)
                           ).strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT DISTINCT client_name_key, COUNT(*) as workout_count,
                       MIN(workout_date) as first_workout,
                       MAX(workout_date) as last_workout
                FROM client_workout_sessions 
                WHERE workout_date >= ?
                GROUP BY client_name_key
                ORDER BY workout_count DESC
            """, (recent_date,))

            clients = cursor.fetchall()

            print(
                f"\nFound {len(clients)} clients with recent workouts (last 30 days):")
            print("-" * 80)

            for client_key, count, first_workout, last_workout in clients:
                display_name = self.transform_client_key_to_display_name(
                    client_key)
                print(f"• {display_name} ({client_key})")
                print(f"  Workouts: {count}")
                print(f"  Period: {first_workout} to {last_workout}")
                print()

            conn.close()
            return [client[0] for client in clients]

        except Exception as e:
            print(f"Database error: {e}")
            return []

    def transform_client_key_to_display_name(self, client_key):
        """Transform database client_key to display name for Trainerize"""
        name_parts = client_key.split('_')
        return ' '.join(word.capitalize() for word in name_parts)

    def apply_rep_progression_algorithm(self, current_reps):
        """Apply the 6->8->10->12->15 rep progression algorithm"""
        try:
            current_reps = int(current_reps)
        except (ValueError, TypeError):
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
            return current_weight + 2.5

    def preview_client_progressions(self, client_key, show_details=True):
        """Preview what progressions would be applied for a specific client"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            display_name = self.transform_client_key_to_display_name(
                client_key)
            print(f"\n=== PROGRESSION PREVIEW: {display_name.upper()} ===")

            # Get client's recent workouts (last 14 days)
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
                print(f"  ❌ No recent workouts found for {client_key}")
                conn.close()
                return 0

            exercise_progressions = {}
            total_exercises = 0

            for date, workout_name, exercises_json in workouts:
                try:
                    exercises = json.loads(exercises_json)
                    if show_details:
                        print(
                            f"  📅 {date} - {workout_name} ({len(exercises)} exercises)")

                    for exercise in exercises:
                        exercise_name = exercise.get('name', 'Unknown')
                        sets = exercise.get('sets', [])

                        if sets and len(sets) > 0 and exercise_name not in exercise_progressions:
                            # Get the best set (highest weight or reps)
                            best_set = max(sets, key=lambda s: (
                                float(s.get('weight', 0)), int(s.get('reps', 0))))

                            current_weight = float(best_set.get('weight', 0))
                            current_reps = int(best_set.get('reps', 0))

                            if current_weight > 0 and current_reps > 0:
                                # Apply smart progression algorithm
                                next_reps = self.apply_rep_progression_algorithm(
                                    current_reps)
                                increase_weight = (
                                    next_reps == 6 and current_reps >= 15)
                                next_weight = self.get_next_weight(
                                    current_weight, exercise_name, increase_weight)

                                exercise_progressions[exercise_name] = {
                                    'current_weight': current_weight,
                                    'current_reps': current_reps,
                                    'next_weight': next_weight,
                                    'next_reps': next_reps,
                                    'increase_weight': increase_weight
                                }

                                if show_details:
                                    print(
                                        f"    - {exercise_name}: {current_weight}kg x {current_reps} → {next_weight}kg x {next_reps}")

                                total_exercises += 1

                except json.JSONDecodeError:
                    if show_details:
                        print(f"    ⚠️ Could not parse exercises for {date}")
                    continue

            conn.close()

            if total_exercises > 0:
                print(f"  ✅ {total_exercises} exercises would be progressed")
            else:
                print(f"  ❌ No exercises found for progression")

            return total_exercises

        except Exception as e:
            print(f"  ❌ Error analyzing {client_key}: {e}")
            return 0

    def show_progression_summary(self):
        """Show a summary of all clients and their progression potential"""
        print("🏋️ CLIENT WORKOUT DATA ANALYSIS")
        print("=" * 60)

        # Get all clients
        client_keys = self.get_all_clients_with_workouts()

        if not client_keys:
            print("❌ No clients found with workout data")
            return

        print(f"\n📊 PROGRESSION SUMMARY FOR {len(client_keys)} CLIENTS:")
        print("=" * 60)

        total_exercises = 0
        clients_with_data = 0

        for client_key in client_keys:
            exercise_count = self.preview_client_progressions(
                client_key, show_details=False)
            if exercise_count > 0:
                clients_with_data += 1
                total_exercises += exercise_count

        print(f"\n🎯 SUMMARY:")
        print(f"  • Total clients with workout data: {len(client_keys)}")
        print(f"  • Clients with progressable exercises: {clients_with_data}")
        print(
            f"  • Total exercises that would be progressed: {total_exercises}")
        print(f"\n📋 Algorithm: 6→8→10→12→15 reps (then +weight, reset to 6)")
        print(f"💪 Weight increments: Dumbbell sequence / +2.5kg for barbell/machine")

        return len(client_keys), clients_with_data, total_exercises

    def show_detailed_client_analysis(self, client_name=None):
        """Show detailed analysis for a specific client or all clients"""
        if client_name:
            # Convert display name to client_key format
            client_key = client_name.lower().replace(' ', '_')
            self.preview_client_progressions(client_key, show_details=True)
        else:
            client_keys = self.get_all_clients_with_workouts()
            for client_key in client_keys:
                self.preview_client_progressions(client_key, show_details=True)


def main():
    """Main function"""
    checker = ClientWorkoutChecker()

    print("What would you like to do?")
    print("1. Show summary of all clients")
    print("2. Show detailed analysis for all clients")
    print("3. Show detailed analysis for a specific client")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        checker.show_progression_summary()
    elif choice == '2':
        print("\n" + "=" * 80)
        print("DETAILED ANALYSIS FOR ALL CLIENTS")
        print("=" * 80)
        checker.show_detailed_client_analysis()
    elif choice == '3':
        client_name = input(
            "Enter client name (e.g., 'Alice Forster'): ").strip()
        if client_name:
            checker.show_detailed_client_analysis(client_name)
        else:
            print("No client name provided")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
