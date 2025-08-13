#!/usr/bin/env python3
"""
Update ALL clients' workout goals with progressive overload
Based on their real workout data from the database
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from weekly_program_updater import TrainerizeAutomation

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_all_clients_with_workouts():
    """Get all clients who have workout data in the database"""
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        print("=== FINDING ALL CLIENTS WITH WORKOUT DATA ===")

        # Get all clients with recent workout sessions (last 30 days)
        recent_date = (datetime.now() - timedelta(days=30)
                       ).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT DISTINCT client_name_key, COUNT(*) as workout_count
            FROM client_workout_sessions 
            WHERE workout_date >= ?
            GROUP BY client_name_key
            ORDER BY workout_count DESC
        """, (recent_date,))

        clients = cursor.fetchall()

        print(f"Found {len(clients)} clients with recent workouts:")
        for client_key, count in clients:
            print(f"  - {client_key}: {count} workouts")

        conn.close()
        return [client[0] for client in clients]

    except Exception as e:
        print(f"Database error: {e}")
        return []


def transform_client_key_to_display_name(client_key):
    """Transform database client_key to display name for Trainerize"""
    # Convert 'alice_forster' to 'Alice Forster'
    name_parts = client_key.split('_')
    return ' '.join(word.capitalize() for word in name_parts)


def get_client_workout_progressions(client_key):
    """Get workout progressions for a specific client"""
    try:
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        print(f"\n=== ANALYZING {client_key.upper()} ===")

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
            print(f"  ❌ No recent workouts found for {client_key}")
            conn.close()
            return {}

        # Group workouts by name and get the most recent performance
        workout_progressions = {}

        for date, workout_name, exercises_json in workouts:
            if workout_name not in workout_progressions:
                exercises = json.loads(exercises_json)
                print(
                    f"  📅 {date} - {workout_name} ({len(exercises)} exercises)")

                workout_progressions[workout_name] = []

                for exercise in exercises:
                    exercise_name = exercise.get('name', 'Unknown')
                    sets = exercise.get('sets', [])

                    if sets and len(sets) > 0:
                        # Get the best set (highest weight or reps)
                        best_set = max(sets, key=lambda s: (
                            float(s.get('weight', 0)), int(s.get('reps', 0))))

                        weight = float(best_set.get('weight', 0))
                        reps = int(best_set.get('reps', 0))

                        if weight > 0 or reps > 0:  # Only include exercises with actual data
                            # Progressive overload logic
                            if weight > 0:
                                # Increase weight by 2.5kg (or 1.25kg for smaller weights)
                                increment = 1.25 if weight < 20 else 2.5
                                new_weight = str(weight + increment)
                            else:
                                new_weight = "2.5"  # Start with 2.5kg if no weight

                            # Increase reps by 1 (but cap at reasonable limits)
                            new_reps = str(min(reps + 1, 15)
                                           ) if reps > 0 else "8"

                            print(
                                f"    - {exercise_name}: {weight}kg x {reps} → {new_weight}kg x {new_reps}")

                            workout_progressions[workout_name].append({
                                "action": "modify_goals",
                                "exercise_name": exercise_name,
                                "weight": new_weight,
                                "reps": new_reps
                            })

        conn.close()
        return workout_progressions

    except Exception as e:
        print(f"Error getting progressions for {client_key}: {e}")
        return {}


def create_all_clients_progression_data():
    """Create progression data for all clients"""

    print("=== CREATING PROGRESSION DATA FOR ALL CLIENTS ===")

    # Get all clients
    client_keys = get_all_clients_with_workouts()

    if not client_keys:
        print("❌ No clients found with workout data")
        return {}

    all_progressions = {}

    for client_key in client_keys:
        display_name = transform_client_key_to_display_name(client_key)
        workout_progressions = get_client_workout_progressions(client_key)

        if workout_progressions:
            all_progressions[display_name] = workout_progressions
            print(
                f"  ✅ Created progressions for {display_name} ({len(workout_progressions)} workouts)")
        else:
            print(f"  ❌ No progressions created for {display_name}")

    print(f"\n🎯 TOTAL CLIENTS TO UPDATE: {len(all_progressions)}")
    return all_progressions


def update_all_clients_workouts():
    """Update workouts for all clients with progressive overload"""

    print("=== UPDATING ALL CLIENTS' WORKOUTS ===")

    # Get all progression data
    all_progressions = create_all_clients_progression_data()

    if not all_progressions:
        print("❌ No progression data to update")
        return

    # Save progression data to file for reference
    with open('all_clients_progressions.json', 'w') as f:
        json.dump(all_progressions, f, indent=2)
    print(f"💾 Saved progression data to: all_clients_progressions.json")

    # Run the workout updater
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    bot = TrainerizeAutomation()

    try:
        print("\n🔐 Logging in...")
        if not bot.login(username, password):
            print("❌ Login failed!")
            return
        print("✅ Login successful!")

        bot.handle_notification_popup()

        print(f"\n🏋️ Processing {len(all_progressions)} clients...")

        success_count = 0
        failure_count = 0

        for i, (client_name, workouts) in enumerate(all_progressions.items(), 1):
            print(f"\n--- {i}/{len(all_progressions)}: {client_name} ---")

            # Process one client at a time
            single_client_data = {client_name: workouts}

            try:
                result = bot.process_multiple_clients(single_client_data)
                if result:
                    success_count += 1
                    print(f"✅ Successfully updated {client_name}")
                else:
                    failure_count += 1
                    print(f"❌ Failed to update {client_name}")
            except Exception as e:
                failure_count += 1
                print(f"❌ Error updating {client_name}: {e}")

        print(f"\n🎉 BATCH UPDATE COMPLETE!")
        print(f"✅ Successful updates: {success_count}")
        print(f"❌ Failed updates: {failure_count}")
        print(
            f"📊 Success rate: {success_count}/{success_count + failure_count} ({100 * success_count / (success_count + failure_count):.1f}%)")

    except Exception as e:
        print(f"Error during batch update: {e}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    update_all_clients_workouts()
