#!/usr/bin/env python3
"""
Program Adjuster - Automated Trainerize Workout Updates
Reads the workout recommendations from video analysis and implements them in Trainerize.
This ensures what's promised in the video gets automatically implemented in the client's program.

The process:
1. Read client data (same JSON used for video generation)
2. Extract Progressive Overload recommendations 
3. Use Trainerize automation to implement changes
4. Update weights, reps, and exercises as recommended
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Import our existing Trainerize automation modules
try:
    from pe import TrainerizeAutomation as ProgramBuilder
    from pb import TrainerizeAutomation as ProgramModifier
except ImportError as e:
    print(f"❌ Error importing Trainerize modules: {e}")
    print("Make sure pe.py and pb.py are in the same directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('program_adjuster.log'),
        logging.StreamHandler()
    ]
)


class ProgressiveOverloadAdjuster:
    def __init__(self, coach_email="Shannonbirch@cocospersonaltraining.com", coach_password="cyywp7nyk2"):
        self.coach_email = coach_email
        self.coach_password = coach_password
        self.trainerize_bot = None

    def analyze_client_recommendations(self, client_data):
        """Extract workout recommendations from client data"""
        recommendations = {
            "client_name": client_data.get("name", "Unknown"),
            "email": client_data.get("email", ""),
            "progressions": [],
            "deloads": [],
            "maintenance": [],
            "new_exercises": [],
            "remove_exercises": []
        }

        # Check for Progressive Overload analysis
        progression_analysis = client_data.get("progression_analysis", {})

        if progression_analysis.get("has_progression_data"):
            # Extract progressions for next week
            next_week_progressions = progression_analysis.get(
                "next_week_progressions", [])

            for progression in next_week_progressions:
                exercise_name = progression.get("exercise", "")
                action = progression.get("action", "")
                current_sets = progression.get("current_sets", 3)
                current_reps = progression.get("current_reps", 12)
                new_sets = progression.get("new_sets", current_sets)
                new_reps = progression.get("new_reps", current_reps)
                reasoning = progression.get("reasoning", "")

                recommendation = {
                    "exercise": exercise_name,
                    "action": action,
                    "current_sets": current_sets,
                    "current_reps": current_reps,
                    "new_sets": new_sets,
                    "new_reps": new_reps,
                    "reasoning": reasoning
                }

                if action == "increase_reps" or action == "increase_weight":
                    recommendations["progressions"].append(recommendation)
                elif action == "deload":
                    recommendations["deloads"].append(recommendation)
                elif action == "maintain":
                    recommendations["maintenance"].append(recommendation)

        # Check for exercise modifications
        workout_modifications = client_data.get("workout_modifications", {})
        if workout_modifications.get("add_exercises"):
            recommendations["new_exercises"] = workout_modifications["add_exercises"]
        if workout_modifications.get("remove_exercises"):
            recommendations["remove_exercises"] = workout_modifications["remove_exercises"]

        return recommendations

    def connect_to_trainerize(self):
        """Initialize connection to Trainerize"""
        try:
            logging.info("🔗 Connecting to Trainerize...")
            self.trainerize_bot = ProgramModifier()

            if self.trainerize_bot.login(self.coach_email, self.coach_password):
                self.trainerize_bot.handle_notification_popup()
                logging.info("✅ Successfully connected to Trainerize")
                return True
            else:
                logging.error("❌ Failed to login to Trainerize")
                return False

        except Exception as e:
            logging.error(f"❌ Error connecting to Trainerize: {e}")
            return False

    def navigate_to_client_program(self, client_name):
        """Navigate to the client's workout program"""
        try:
            logging.info(f"📍 Navigating to client: {client_name}")

            if not self.trainerize_bot.navigate_to_client(client_name):
                logging.error(f"❌ Failed to navigate to client: {client_name}")
                return False

            if not self.trainerize_bot.navigate_to_training_program():
                logging.error(
                    f"❌ Failed to navigate to training program for {client_name}")
                return False

            # Find current program
            current_program = self.trainerize_bot.find_current_workout_program()
            if current_program:
                logging.info(f"📋 Found current program: {current_program}")
                return current_program
            else:
                logging.warning(
                    f"⚠️ No current program found for {client_name}")
                return None

        except Exception as e:
            logging.error(f"❌ Error navigating to client program: {e}")
            return None

    def implement_progression(self, progression, program_name):
        """Implement a single progression recommendation"""
        try:
            exercise = progression["exercise"]
            action = progression["action"]
            new_sets = progression["new_sets"]
            new_reps = progression["new_reps"]
            reasoning = progression["reasoning"]

            logging.info(f"🎯 Implementing progression for {exercise}")
            logging.info(f"   Action: {action}")
            logging.info(f"   New sets/reps: {new_sets}x{new_reps}")
            logging.info(f"   Reasoning: {reasoning}")

            # Find and click the program
            if not self.trainerize_bot.click_program(program_name):
                logging.error(f"❌ Failed to click program: {program_name}")
                return False

            # Find the workout containing this exercise
            # For now, try common workout types based on exercise name
            workout_types = self.determine_workout_type(exercise)

            workout_found = False
            for workout_type in workout_types:
                if self.trainerize_bot.click_workout_fuzzy(workout_type):
                    logging.info(f"📋 Opened {workout_type} workout")

                    # Enter edit mode
                    if self.trainerize_bot.click_edit_workout():
                        logging.info("✏️ Entered workout edit mode")

                        # Remove the exercise with old parameters
                        if self.trainerize_bot.remove_exercise(exercise):
                            logging.info(
                                f"🗑️ Removed old version of {exercise}")

                            # Add the exercise with new parameters
                            if self.trainerize_bot.add_exercise(exercise, str(new_sets), str(new_reps)):
                                logging.info(
                                    f"➕ Added {exercise} with {new_sets}x{new_reps}")

                                # Save the workout
                                if self.trainerize_bot.save_workout():
                                    logging.info(
                                        f"💾 Saved workout with updated {exercise}")
                                    workout_found = True
                                    break
                                else:
                                    logging.error("❌ Failed to save workout")
                            else:
                                logging.error(
                                    f"❌ Failed to add updated {exercise}")
                        else:
                            logging.warning(
                                f"⚠️ Could not remove {exercise}, it may not exist in this workout")
                    else:
                        logging.error("❌ Failed to enter edit mode")
                else:
                    logging.debug(
                        f"🔍 {workout_type} workout not found, trying next...")

            if not workout_found:
                logging.warning(
                    f"⚠️ Could not find workout containing {exercise}")
                return False

            return True

        except Exception as e:
            logging.error(
                f"❌ Error implementing progression for {progression['exercise']}: {e}")
            return False

    def determine_workout_type(self, exercise_name):
        """Determine likely workout types based on exercise name"""
        exercise_lower = exercise_name.lower()

        # Exercise to workout type mapping
        workout_mappings = {
            "chest": ["bench", "chest", "press", "fly", "dip"],
            "back": ["row", "pull", "lat", "chin", "deadlift"],
            "shoulder": ["shoulder", "lateral", "overhead", "military", "arnold"],
            "leg": ["squat", "lunge", "leg", "calf", "quad", "hamstring"],
            "core": ["crunch", "plank", "abs", "core", "twist"]
        }

        likely_workouts = []

        for workout_type, keywords in workout_mappings.items():
            if any(keyword in exercise_lower for keyword in keywords):
                likely_workouts.append(workout_type)

        # Default order if no specific match
        if not likely_workouts:
            likely_workouts = ["back", "chest", "shoulder", "leg", "core"]

        return likely_workouts

    def implement_all_recommendations(self, recommendations):
        """Implement all workout recommendations for a client"""
        client_name = recommendations["client_name"]

        try:
            # Navigate to client program
            program_name = self.navigate_to_client_program(client_name)
            if not program_name:
                return False

            total_changes = 0
            successful_changes = 0

            # Implement progressions
            for progression in recommendations["progressions"]:
                total_changes += 1
                if self.implement_progression(progression, program_name):
                    successful_changes += 1

            # Implement deloads
            for deload in recommendations["deloads"]:
                total_changes += 1
                if self.implement_progression(deload, program_name):  # Same process
                    successful_changes += 1

            # Log summary
            logging.info(f"📊 Program adjustment summary for {client_name}:")
            logging.info(f"   Total changes attempted: {total_changes}")
            logging.info(f"   Successful changes: {successful_changes}")
            logging.info(
                f"   Success rate: {successful_changes/total_changes*100:.1f}%" if total_changes > 0 else "   No changes to implement")

            return successful_changes > 0

        except Exception as e:
            logging.error(
                f"❌ Error implementing recommendations for {client_name}: {e}")
            return False

    def process_client_file(self, client_data_file):
        """Process a single client data file and implement recommendations"""
        try:
            logging.info(f"📂 Processing client file: {client_data_file}")

            # Load client data
            with open(client_data_file, 'r') as f:
                client_data = json.load(f)

            client_name = client_data.get("name", "Unknown")
            logging.info(f"👤 Processing recommendations for: {client_name}")

            # Analyze recommendations
            recommendations = self.analyze_client_recommendations(client_data)

            # Check if there are any recommendations to implement
            total_recommendations = (
                len(recommendations["progressions"]) +
                len(recommendations["deloads"]) +
                len(recommendations["new_exercises"]) +
                len(recommendations["remove_exercises"])
            )

            if total_recommendations == 0:
                logging.info(
                    f"ℹ️ No workout recommendations found for {client_name}")
                return True

            logging.info(
                f"📋 Found {total_recommendations} recommendations for {client_name}")
            logging.info(
                f"   Progressions: {len(recommendations['progressions'])}")
            logging.info(f"   Deloads: {len(recommendations['deloads'])}")
            logging.info(
                f"   New exercises: {len(recommendations['new_exercises'])}")
            logging.info(
                f"   Remove exercises: {len(recommendations['remove_exercises'])}")

            # Implement recommendations
            success = self.implement_all_recommendations(recommendations)

            if success:
                logging.info(
                    f"✅ Successfully processed recommendations for {client_name}")
            else:
                logging.warning(
                    f"⚠️ Some recommendations failed for {client_name}")

            return success

        except Exception as e:
            logging.error(
                f"❌ Error processing client file {client_data_file}: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.trainerize_bot:
            self.trainerize_bot.cleanup()


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python program_adjuster.py <client_data_file>")
        print("   or: python program_adjuster.py --all")
        return 1

    # Initialize the adjuster
    adjuster = ProgressiveOverloadAdjuster()

    try:
        # Connect to Trainerize
        if not adjuster.connect_to_trainerize():
            print("❌ Failed to connect to Trainerize")
            return 1

        if sys.argv[1] == "--all":
            # Process all client files from checkin output
            checkin_dir = Path("output/checkin_reviews")
            if not checkin_dir.exists():
                print(f"❌ Checkin directory not found: {checkin_dir}")
                return 1

            # Find all recent client data files
            today = datetime.now().strftime('%Y-%m-%d')
            client_files = list(checkin_dir.glob(
                f"*_{today}_fitness_wrapped_data.json"))

            if not client_files:
                # Try yesterday's files
                from datetime import datetime, timedelta
                yesterday = (datetime.now() - timedelta(days=1)
                             ).strftime('%Y-%m-%d')
                client_files = list(checkin_dir.glob(
                    f"*_{yesterday}_fitness_wrapped_data.json"))

            if not client_files:
                print("❌ No recent client data files found")
                return 1

            print(f"🔄 Processing {len(client_files)} client files...")

            successful = 0
            for client_file in client_files:
                if adjuster.process_client_file(str(client_file)):
                    successful += 1

            print(f"\n📊 Program Adjustment Summary:")
            print(f"   Files processed: {len(client_files)}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {len(client_files) - successful}")

        else:
            # Process single client file
            client_file = sys.argv[1]
            if not os.path.exists(client_file):
                print(f"❌ Client file not found: {client_file}")
                return 1

            success = adjuster.process_client_file(client_file)
            if success:
                print("✅ Program adjustments completed successfully")
            else:
                print("❌ Program adjustments failed")
                return 1

    except KeyboardInterrupt:
        print("\n⏹️ Program adjustment interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return 1
    finally:
        adjuster.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
