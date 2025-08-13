from checkin import TrainerizeAutomation
import traceback
import json
import time
import logging
import sys
from datetime import datetime, timedelta

# Calculate the date for last week
today = datetime.now().date()
LASTWEEK = today - timedelta(days=7)  # One week ago (e.g., March 3)
LASTWEEK_STR = LASTWEEK.strftime("%Y-%m-%d")
print(f"DEBUG: Last week's date calculated as {LASTWEEK_STR}")

# Override the calculate_workout_stats_for_date_range method to handle lastweek calculations


def calculate_workout_stats_for_date_range_lastweek(self, workout_data_list, start_date, end_date, target_exercises=None):
    """Modified version that works with last week's date range"""
    print(
        f"DEBUG: calculate_workout_stats_for_date_range_lastweek called with date range: {start_date} to {end_date}")
    return self.calculate_workout_stats_for_date_range(workout_data_list, start_date, end_date, target_exercises)

# Override the save_fitness_wrapped_data method to save with last week's date


def save_fitness_wrapped_data_lastweek(self, client_name, fitness_wrapped_data):
    """Modified version that saves data with lastweek's date in the filename"""
    # Use last week's date for the filename
    filename = f"{client_name}_{LASTWEEK_STR}_fitness_wrapped_data.json"

    try:
        with open(filename, 'w') as f:
            json.dump(fitness_wrapped_data, f, indent=4)
        logging.info(f"Saved last week's fitness wrapped data to {filename}")
        print(f"DEBUG: Successfully saved data to {filename}")
        return filename
    except Exception as e:
        logging.exception(
            f"Error saving last week's fitness wrapped data: {e}")
        print(f"DEBUG: Error saving data: {e}")
        return None

# Add a method to save all client data to a single file


def save_all_checkins_lastweek(self, client_data_dict):
    """Save all client data to a single JSON file with lastweek's date"""
    filename = f"all_clients_{LASTWEEK_STR}_fitness_wrapped_data.json"

    try:
        with open(filename, 'w') as f:
            json.dump(client_data_dict, f, indent=4)
        logging.info(
            f"Saved all clients last week's fitness wrapped data to {filename}")
        print(f"DEBUG: Successfully saved all client data to {filename}")
        return filename
    except Exception as e:
        logging.exception(
            f"Error saving all clients last week's fitness wrapped data: {e}")
        print(f"DEBUG: Error saving all client data: {e}")
        return None

# Override the prepare_fitness_wrapped_data method to use last week's date range


def prepare_fitness_wrapped_data_lastweek(self, client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis,
                                          steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data,
                                          workouts_completed_analysis, total_workout_stats_analysis, workout_data_list):
    """Modified version that uses last week's date range"""

    print("DEBUG: prepare_fitness_wrapped_data_lastweek called")
    print("Using LAST WEEK'S data range rather than this week")

    # Calculate last week's date range (7 days ago to 14 days ago)
    today = datetime.now().date()

    # Modified calculation (last week)
    end_date = today - timedelta(days=7)  # One week ago (e.g., March 3)
    # Two weeks ago (e.g., February 24)
    start_date = today - timedelta(days=14)

    # Calculate the week before last week for comparison
    prev_end_date = start_date  # Two weeks ago (February 24)
    # Three weeks ago (February 17)
    prev_start_date = today - timedelta(days=21)

    # Format dates for display
    start_day = start_date.strftime("%b %d")
    end_day = end_date.strftime("%b %d")
    date_range_str = f"{start_day} - {end_day}"

    # Debug the date ranges
    print(f"DEBUG: Current week date range: {start_date} to {end_date}")
    print(
        f"DEBUG: Previous week date range: {prev_start_date} to {prev_end_date}")

    # Extract stats for the current week (last week)
    current_week_stats = self.calculate_workout_stats_for_date_range(
        workout_data_list, start_date, end_date)

    # Extract stats for the previous week
    prev_week_stats = self.calculate_workout_stats_for_date_range(
        workout_data_list, prev_start_date, prev_end_date)

    # Debug the stats
    print(f"DEBUG: Current week stats: {current_week_stats}")
    print(f"DEBUG: Previous week stats: {prev_week_stats}")

    # Extract the stats we need (using tuple unpacking since it returns a tuple)
    try:
        # Unpack the tuples - adjust indices if needed based on the actual structure
        current_week_workouts, _, current_week_weight, current_week_reps, current_week_sets, _, current_week_workload = current_week_stats
        prev_week_workouts, _, prev_week_weight, prev_week_reps, prev_week_sets, _, prev_week_workload = prev_week_stats

        # Handle the case where workload might be a dictionary
        if isinstance(current_week_workload, dict):
            current_week_workload = 0
        if isinstance(prev_week_workload, dict):
            prev_week_workload = 0

        # Calculate changes
        workout_change = current_week_workouts - prev_week_workouts

        # Calculate percentage changes (handle division by zero)
        workout_change_percentage = int((workout_change / prev_week_workouts * 100)
                                        if prev_week_workouts > 0 else 0)

        workload_change_percentage = int((current_week_workload - prev_week_workload) /
                                         prev_week_workload * 100 if prev_week_workload > 0 else 0)

        # Debug calculations
        print(
            f"DEBUG: Workout change: {workout_change} ({workout_change_percentage}%)")
        print(
            f"DEBUG: Workload change: {current_week_workload - prev_week_workload} ({workload_change_percentage}%)")
    except Exception as e:
        print(f"DEBUG: Error processing stats: {e}")
        # Set default values if there's an issue
        current_week_workouts = 0
        workout_change = 0
        workout_change_percentage = 0
        workload_change_percentage = 0

    # Get top exercise for the current week period
    try:
        top_exercise = None
        # Try to find top exercises if method exists
        if hasattr(self, 'get_top_exercise_for_date_range'):
            top_exercise = self.get_top_exercise_for_date_range(
                workout_data_list, start_date, end_date)
        elif hasattr(self, 'find_top_performing_exercises'):
            top_exercises = self.find_top_performing_exercises(
                workout_data_list, start_date, end_date, prev_start_date, prev_end_date)
            if top_exercises and len(top_exercises) > 0:
                top_exercise = top_exercises[0]
    except Exception as e:
        print(f"DEBUG: Error getting top exercise: {e}")
        top_exercise = None

    # Build the result data with all the calculated values
    result = {
        "client_name": client_name,
        "date_range": date_range_str,
        "has_nutrition_data": nutrition_analysis is not None,
        "has_sleep_data": sleep_analysis is not None,
        "has_steps_data": steps_analysis is not None,
        "has_weight_data": bodyweight_analysis is not None,
        "has_photos": photos_analysis is not None,
        "weight_goal_text": weight_goal_text,
        "weekly_summary": weekly_summary_data,
        "workouts_completed_text": workouts_completed_analysis[0] if workouts_completed_analysis else None,
        "workouts_completed_trend": workouts_completed_analysis[1] if workouts_completed_analysis and len(workouts_completed_analysis) > 1 else "neutral",
        "workout_stats_text": total_workout_stats_analysis[0] if total_workout_stats_analysis else None,
        "workout_stats_trend": total_workout_stats_analysis[1] if total_workout_stats_analysis and len(total_workout_stats_analysis) > 1 else "neutral",
        "top_exercise": top_exercise,
        "total_workouts": current_week_workouts,
        "workout_change": workout_change,
        "workout_change_percentage": workout_change_percentage,
        "workload_change_percentage": workload_change_percentage
    }

    print(
        f"DEBUG: Prepared fitness wrapped data for {client_name} with date range {date_range_str}")
    return result


# Patch the TrainerizeAutomation class with our new methods
print("DEBUG: Saving original methods")
original_calculate = TrainerizeAutomation.calculate_workout_stats_for_date_range
original_save = TrainerizeAutomation.save_fitness_wrapped_data
original_prepare = TrainerizeAutomation.prepare_fitness_wrapped_data

print("DEBUG: Applying patches")
TrainerizeAutomation.calculate_workout_stats_for_date_range_lastweek = calculate_workout_stats_for_date_range_lastweek
TrainerizeAutomation.save_fitness_wrapped_data_lastweek = save_fitness_wrapped_data_lastweek
TrainerizeAutomation.save_all_checkins_lastweek = save_all_checkins_lastweek
TrainerizeAutomation.prepare_fitness_wrapped_data_lastweek = prepare_fitness_wrapped_data_lastweek

# Main execution code
print("=" * 40)
print("=== RUNNING CHECKIN FOR LAST WEEK'S DATA ===")
print("=" * 40)

print("DEBUG: Starting main execution")

# Define client names
clients = [
    "Shane Minahan",
    "Shannon Birch",
    "Maysoon Shomali",
    "Adele Mills",
    "Alison Alvin",
    "Christina Astor",
    "Gabby Gabourie",
    "Kayla Kuefler",
    "Louise Craig",
    "Paul Mills",
    "Stephanie Banting"
]

# Login credentials
username = "Shannonbirch@cocospersonaltraining.com"
password = "cyywp7nyk"
gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

# Dict to store all client data
all_client_data = {}

if __name__ == "__main__":
    # Initialize the automation class
    automation = TrainerizeAutomation(gemini_api_key)

    try:
        # Login
        if not automation.login(username, password):
            print("Login failed! Exiting.")
            sys.exit(1)

        # Process each client
        for i, client_name in enumerate(clients, 1):
            print(f"\nProcessing client {i}/{len(clients)}: {client_name}")
            print(f"{'-'*50}")

            try:
                # Navigate to client
                if not automation.navigate_to_client(client_name):
                    print(
                        f"Could not navigate to client {client_name}. Skipping.")
                    continue

                # Get the data
                print("Getting data for client...")
                bodyweight_analysis = automation.analyze_bodyweight_graph()
                nutrition_analysis = automation.analyze_nutrition_graph()
                sleep_analysis = automation.analyze_sleep_graph()
                steps_analysis = automation.analyze_steps_graph()
                photos_analysis = automation.analyze_progress_photos()

                # Get weight goal
                print("Getting weight goal...")
                automation.navigate_to_goals_and_habits_tab()
                weight_goal_text = automation.get_current_weight_goal()

                # Process workouts
                print("Processing workouts...")
                workout_data_list = automation.process_workouts()
                if workout_data_list:
                    print(
                        f"Retrieved {len(workout_data_list)} workout records")

                    # Display workout statistics
                    automation.display_workout_statistics(workout_data_list)

                # Prepare and save the fitness data
                fitness_wrapped_data = automation.prepare_fitness_wrapped_data_lastweek(
                    client_name,
                    bodyweight_analysis,
                    nutrition_analysis,
                    sleep_analysis,
                    steps_analysis,
                    photos_analysis,
                    weight_goal_text,
                    {},  # weekly_summary_data (empty dict, not needed)
                    "",  # workouts_completed_analysis (not needed)
                    "",  # total_workout_stats_analysis (not needed)
                    workout_data_list
                )

                # Store in all_client_data
                all_client_data[client_name] = fitness_wrapped_data

                # Save the fitness data for this client
                saved_file = automation.save_fitness_wrapped_data_lastweek(
                    client_name, fitness_wrapped_data)
                print(
                    f"Successfully saved data for {client_name} to {saved_file}")

                # Navigate back to the clients list
                automation.navigate_back_to_clients_list()
            except Exception as e:
                print(f"Error processing client {client_name}: {e}")
                traceback.print_exc()
                # Try to navigate back to clients list to continue with the next client
                try:
                    automation.navigate_back_to_clients_list()
                except:
                    print("Could not navigate back to clients list.")

        # Save all client data to a single file
        print("\nSaving all client check-ins...")
        all_clients_file = automation.save_all_checkins_lastweek(
            all_client_data)
        print(f"Successfully saved all client check-ins to {all_clients_file}")

        print("\nAll clients processed. Cleaning up...")
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        traceback.print_exc()
    finally:
        # Always clean up resources
        automation.cleanup()
        print("Script execution complete.")
