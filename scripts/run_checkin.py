import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Default list of clients
DEFAULT_CLIENTS = [
    "Shannon Birch", "Ben Pryke", "Alice Forster", "Sarika Ramani",
    "Helen Forster", "Nicole Lynch", "Conor Beveridge", "Rebecca DAngelo",
    "Rick Preston", "Claire Ruberu", "Kylie Pinder", "Jo Foy",
    "Manny Le-ray", "Tony Strupl", "Heath Kilgour", "Anna Somogyi",
    "Danny Birch", "MJ Devine", "Ben Norman", "Adri Rivera",
    "Amanda Buckingham", "Naman Tiwari", "Kelly Smith", "Shane Minahan"
]


def run_check_in(client_names, openai_api_key=None):
    """Run the check-in process and return paths to the generated JSON files"""
    try:
        # Import the TrainerizeAutomation class
        from checkin import TrainerizeAutomation

        # Define credentials
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk"

        logging.info(f"Starting check-in for {len(client_names)} clients")

        # Initialize the TrainerizeAutomation
        trainerize_bot = TrainerizeAutomation(openai_api_key)
        json_files = []

        try:
            # Login
            if not trainerize_bot.login(username, password):
                logging.error("Login failed")
                return []

            logging.info("Login successful")

            # Process each client
            for i, client_name in enumerate(client_names, 1):
                logging.info(
                    f"Processing client {i}/{len(client_names)}: {client_name}")

                try:
                    if trainerize_bot.navigate_to_client(client_name):
                        logging.info(
                            f"Successfully navigated to client: {client_name}")

                        # Get weight goal
                        trainerize_bot.navigate_to_goals_and_habits_tab()
                        weight_goal_text = trainerize_bot.get_current_weight_goal()

                        # Analyze bodyweight
                        trainerize_bot.click_progress_tab()
                        trainerize_bot.click_biometrics()
                        bodyweight_analysis = trainerize_bot.analyze_bodyweight_graph()

                        # Analyze nutrition (if available)
                        try:
                            trainerize_bot.navigate_to_nutrition_graphs()
                            nutrition_analysis = trainerize_bot.analyze_nutrition_graph()
                        except Exception as e:
                            logging.warning(
                                f"Failed to analyze nutrition for {client_name}: {e}")
                            nutrition_analysis = {
                                "has_data": False, "message": "No nutrition data available"}

                        # Analyze sleep (if available)
                        try:
                            trainerize_bot.navigate_to_sleep_graphs()
                            sleep_analysis = trainerize_bot.analyze_sleep_graph()
                        except Exception as e:
                            logging.warning(
                                f"Failed to analyze sleep for {client_name}: {e}")
                            sleep_analysis = {"has_data": False,
                                              "message": "No sleep data available"}

                        # Analyze steps (if available)
                        try:
                            trainerize_bot.navigate_to_steps_graphs()
                            steps_analysis = trainerize_bot.analyze_steps_graph()
                        except Exception as e:
                            logging.warning(
                                f"Failed to analyze steps for {client_name}: {e}")
                            steps_analysis = {"has_data": False,
                                              "message": "No steps data available"}

                        # Analyze progress photos (if available)
                        try:
                            trainerize_bot.click_progress_photos_tab()
                            photos_analysis = trainerize_bot.analyze_progress_photos()
                        except Exception as e:
                            logging.warning(
                                f"Failed to analyze photos for {client_name}: {e}")
                            photos_analysis = {
                                "has_data": False, "message": "No progress photos available"}

                        # Process workouts
                        trainerize_bot.click_review_by_workout()
                        weekly_summary_data, workout_data_list = trainerize_bot.process_workouts()

                        # Perform workout analyses
                        workout_completed_analysis = trainerize_bot.analyze_workouts_completed_this_week(
                            weekly_summary_data)
                        total_workout_stats_analysis = trainerize_bot.analyze_total_workout_stats(
                            weekly_summary_data)
                        workload_increase_analysis = trainerize_bot.analyze_workload_increase(
                            weekly_summary_data)

                        # Get default target exercises if not specified
                        target_exercises = [
                            "Squat", "Deadlift", "Bench Press", "Shoulder Press"]
                        specific_exercises_analysis = trainerize_bot.analyze_specific_exercises(
                            weekly_summary_data, target_exercises)

                        # Create personalized message
                        personalized_message = trainerize_bot.generate_personalized_message(
                            bodyweight_analysis, nutrition_analysis, sleep_analysis)

                        # Extract/process data for additional insights
                        # Weight history and goal extraction
                        weight_history = trainerize_bot.extract_weight_history(
                            bodyweight_analysis)
                        weight_goal = trainerize_bot.extract_weight_goal(
                            weight_goal_text)

                        # Make prediction if we have both history and goal
                        if weight_history and weight_goal:
                            prediction = trainerize_bot.predict_future_progress(
                                weight_history, weight_goal)
                        else:
                            prediction = None

                        # Find top-performing exercises
                        top_exercises = trainerize_bot.find_top_performing_exercises(
                            workout_data_list,
                            weekly_summary_data.get("current_week_start_date"),
                            weekly_summary_data.get("current_week_end_date"),
                            weekly_summary_data.get(
                                "previous_week_start_date"),
                            weekly_summary_data.get("previous_week_end_date")
                        )

                        # Prepare recommendations
                        if specific_exercises_analysis.get("recommendations"):
                            exercise_recommendation = specific_exercises_analysis["recommendations"][
                                0] if specific_exercises_analysis["recommendations"] else ""
                        else:
                            exercise_recommendation = ""

                        # Generate and save Fitness Wrapped data
                        fitness_wrapped_data = trainerize_bot.prepare_fitness_wrapped_data(
                            client_name, bodyweight_analysis, nutrition_analysis, sleep_analysis,
                            steps_analysis, photos_analysis, weight_goal_text, weekly_summary_data,
                            workout_completed_analysis, total_workout_stats_analysis, workout_data_list
                        )

                        # Add today's date to the filename
                        today_str = datetime.now().strftime('%Y-%m-%d')
                        json_filename = f"{client_name.replace(' ', '_')}_{today_str}_fitness_wrapped_data.json"

                        # Save the data to a JSON file
                        with open(json_filename, 'w') as f:
                            json.dump(fitness_wrapped_data, f, indent=2)

                        logging.info(
                            f"JSON file created for {client_name}: {json_filename}")
                        json_files.append((client_name, json_filename))

                        # Navigate back to clients list for the next client
                        if not trainerize_bot.navigate_back_to_clients_list():
                            logging.warning(
                                f"Failed to navigate back to clients list after processing {client_name}")
                            # Try to go directly to the clients page as a fallback
                            try:
                                trainerize_bot.driver.get(
                                    "https://www.trainerize.com/Clients.aspx")
                                time.sleep(5)  # Give page time to load
                            except:
                                logging.error(
                                    "Failed to navigate back to clients list. Attempting to continue anyway.")
                    else:
                        logging.error(
                            f"Failed to navigate to client: {client_name}")

                except Exception as e:
                    logging.exception(
                        f"Error processing client {client_name}: {e}")
                    logging.info(f"Continuing with next client...")
                    # Try to go back to clients list
                    try:
                        trainerize_bot.driver.get(
                            "https://www.trainerize.com/Clients.aspx")
                        time.sleep(5)  # Give page time to load
                    except:
                        pass

            return json_files

        except Exception as e:
            logging.exception(f"Error during check-in process: {e}")
            return []

        finally:
            # Clean up
            logging.info("Cleaning up TrainerizeAutomation resources")
            trainerize_bot.cleanup()

    except ImportError as e:
        logging.error(f"Failed to import TrainerizeAutomation: {e}")
        logging.error("Make sure checkin.py is in the current directory")
        return []


def generate_videos(json_files):
    """Generate videos for each client using the simple_blue_video.py script"""
    try:
        # Use the simple_blue_video.py script for video generation
        logging.info("Running simple_blue_video.py to generate videos...")

        cmd = [sys.executable, "simple_blue_video.py"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info("Videos generated successfully!")
                logging.info(result.stdout)
                return True
            else:
                logging.error(f"Error generating videos: {result.stderr}")
                return False

        except Exception as e:
            logging.exception(f"Error running simple_blue_video.py: {e}")
            return False

    except Exception as e:
        logging.exception(f"Error in generate_videos: {e}")
        return False


def main():
    """Main function to run the complete workflow"""
    parser = argparse.ArgumentParser(
        description="Run check-ins and generate fitness wrapped videos")
    parser.add_argument("--clients", nargs="+",
                        help="List of specific client names to process (if not specified, uses all clients)")
    parser.add_argument("--skip-check-in", action="store_true",
                        help="Skip the check-in process and use existing JSON files")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API key for OpenAI/Gemini (if not provided, will use the default in checkin.py)")
    args = parser.parse_args()

    # Determine which clients to process
    if args.clients:
        client_names = args.clients
    else:
        client_names = DEFAULT_CLIENTS

    logging.info(
        f"Will process {len(client_names)} clients: {', '.join(client_names)}")

    # Step 1: Collect data (if not skipped)
    if not args.skip_check_in:
        logging.info("=== STARTING CHECK-IN PROCESS ===")
        json_files = run_check_in(client_names, args.api_key)

        if not json_files:
            logging.error(
                "No data files were created during check-in. Cannot generate videos.")
            return
    else:
        logging.info(
            "=== SKIPPING CHECK-IN PROCESS (USING EXISTING JSON FILES) ===")

    # Step 2: Generate videos using simple_blue_video.py
    logging.info("=== STARTING VIDEO GENERATION ===")
    # We don't need to pass json_files as simple_blue_video will find them
    success = generate_videos([])

    # Step 3: Show results
    logging.info("\n" + "="*70)
    logging.info(f"{'PROCESSING SUMMARY':^70}")
    logging.info("="*70)

    if not args.skip_check_in:
        logging.info(f"Clients processed: {len(json_files)}")
        logging.info(f"JSON files created: {len(json_files)}")

        if json_files:
            logging.info("\nCreated JSON files:")
            for i, (client_name, json_file) in enumerate(json_files, 1):
                logging.info(f"  {i}. {client_name}: {json_file}")

    if success:
        logging.info("\nVideos should be available in the 'output' directory")
    else:
        logging.info(
            "\nThere were errors during video generation. Check the logs above.")

    logging.info(
        "\nTo generate videos from the JSON files without running check-ins again,")
    logging.info("run: python run_checkin.py --skip-check-in")

    logging.info("="*70)


if __name__ == "__main__":
    main()
