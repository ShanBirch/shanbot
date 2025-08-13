#!/usr/bin/env python3
"""
Smart Coach Complete V2 - Enhanced Version
- Reads actual workout names from Trainerize
- Better browser stability and tab management
- Improved exercise name fuzzy matching
- Single-client focused testing
"""

import json
import logging
from datetime import datetime, timedelta
from weekly_program_updater_fixed import TrainerizeAutomation
import re
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_coach_complete_v2.log'),
        logging.StreamHandler()
    ]
)


class SmartCoachCompleteV2:
    def __init__(self):
        self.progression_history = self.load_progression_history()
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        self.barbell_increments = 2.5

    def load_progression_history(self):
        """Load the progression history data"""
        try:
            with open('progression_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("progression_history.json not found")
            return {}
        except Exception as e:
            logging.error(f"Error loading progression history: {e}")
            return {}

    def get_client_latest_performance(self, client_name):
        """Get the most recent performance data for a client"""
        if client_name not in self.progression_history:
            logging.warning(f"No progression history found for {client_name}")
            return {}

        client_history = self.progression_history[client_name]
        if not client_history:
            return {}

        # Get the most recent entry
        latest_entry = max(client_history, key=lambda x: x['date'])
        return latest_entry.get('progressions', {})

    def parse_current_performance(self, current_reps_string):
        """Parse current performance from strings like 'S1: 20kgx9 | S2: 25kgx8'"""
        sets_data = []
        if not current_reps_string:
            return sets_data

        # Split by | to get individual sets
        set_parts = current_reps_string.split('|')

        for set_part in set_parts:
            set_part = set_part.strip()
            # Extract weight and reps using regex
            match = re.search(r'(\d+(?:\.\d+)?)kg[x*](\d+)', set_part)
            if match:
                weight = float(match.group(1))
                reps = int(match.group(2))
                sets_data.append({'weight': weight, 'reps': reps})

        return sets_data

    def apply_rep_progression_algorithm(self, current_reps):
        """Apply the 6->8->10->12->15 rep progression algorithm"""
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
            return 6  # Default start

    def get_next_weight(self, current_weight, exercise_name, increase_weight=False):
        """Get the next appropriate weight based on equipment type"""
        if not increase_weight:
            return current_weight

        # Determine if it's a dumbbell exercise
        is_dumbbell = any(keyword in exercise_name.lower() for keyword in
                          ['dumbbell', 'd.b', 'db', 'dumbell'])

        if is_dumbbell:
            # Find next dumbbell weight
            current_idx = None
            for i, weight in enumerate(self.dumbbell_weights):
                if weight >= current_weight:
                    current_idx = i
                    break

            if current_idx is not None and current_idx < len(self.dumbbell_weights) - 1:
                return self.dumbbell_weights[current_idx + 1]
            else:
                return current_weight + 2.5  # Fallback
        else:
            # Barbell/machine - add 2.5kg
            return current_weight + self.barbell_increments

    def analyze_exercise_with_performance_data(self, exercise_name, performance_data):
        """Analyze an exercise based on real performance data"""
        logging.info(f"Smart analysis for: {exercise_name}")

        if not performance_data:
            # No previous data - start with conservative defaults
            logging.info(
                f"  No previous data for {exercise_name} - starting with defaults")
            return {
                'goals': "GOALS: S1: 0kg*6 | S2: 0kg*6 | S3: 0kg*6",
                'reason': "No previous data - starting with 6 reps, coach will set weights manually",
                'sets': [
                    {'weight': 0, 'reps': 6,
                        'reason': 'Starting point - no previous data'},
                    {'weight': 0, 'reps': 6,
                        'reason': 'Starting point - no previous data'},
                    {'weight': 0, 'reps': 6,
                        'reason': 'Starting point - no previous data'}
                ]
            }

        current_weight = performance_data.get('current_weight', 0)
        current_reps_string = performance_data.get('current_reps', '')

        # Parse the current performance
        sets_performed = self.parse_current_performance(current_reps_string)

        if not sets_performed:
            # Fallback to single set data
            current_reps_str = performance_data.get('current_reps', '6')

            # Handle rep ranges like "6-7" or "8-10"
            if '-' in current_reps_str:
                # Take the higher number from the range
                current_reps = int(current_reps_str.split('-')[-1])
            else:
                # Extract first number from string
                match = re.search(r'\d+', current_reps_str)
                current_reps = int(match.group()) if match else 6

            sets_performed = [{'weight': current_weight, 'reps': current_reps}]

        logging.info(f"  Current performance: {sets_performed}")

        # Apply progression to each set individually
        next_week_sets = []

        for i, set_data in enumerate(sets_performed):
            current_set_weight = set_data['weight']
            current_set_reps = set_data['reps']

            # Apply rep progression algorithm
            next_reps = self.apply_rep_progression_algorithm(current_set_reps)

            # Determine if we need to increase weight (when reps reset to 6)
            increase_weight = (next_reps == 6 and current_set_reps >= 15)
            next_weight = self.get_next_weight(
                current_set_weight, exercise_name, increase_weight)

            reason = f"Set {i+1}: "
            if increase_weight:
                reason += f"Completed 15 reps, increased weight from {current_set_weight}kg to {next_weight}kg, reset to 6 reps"
            else:
                reason += f"Progressed reps from {current_set_reps} to {next_reps}"

            next_week_sets.append({
                'weight': next_weight,
                'reps': next_reps,
                'reason': reason
            })

        # Ensure we have at least 3 sets (pad with the last set's data if needed)
        while len(next_week_sets) < 3:
            last_set = next_week_sets[-1] if next_week_sets else {
                'weight': 0, 'reps': 6, 'reason': 'Default set'}
            next_week_sets.append({
                'weight': last_set['weight'],
                'reps': last_set['reps'],
                'reason': f"Set {len(next_week_sets) + 1}: Matched previous set"
            })

        # Format the goals string
        goals_parts = []
        # Max 4 sets for display
        for i, set_data in enumerate(next_week_sets[:4]):
            goals_parts.append(
                f"S{i+1}: {set_data['weight']}kg*{set_data['reps']}")

        goals_string = "GOALS: " + " | ".join(goals_parts)

        overall_reason = f"Applied set-by-set progression algorithm based on real performance data"

        logging.info(f"  Next week goals: {goals_string}")

        return {
            'goals': goals_string,
            'reason': overall_reason,
            'sets': next_week_sets
        }

    def get_actual_workouts_from_trainerize(self, automation, client_name):
        """Get the actual workout names from Trainerize for a client"""
        try:
            logging.info(
                f"Reading actual workout names from Trainerize for {client_name}...")

            # Navigate to client
            if not automation.navigate_to_client(client_name):
                logging.error(f"Failed to navigate to {client_name}")
                return []

            # Navigate to training program
            if not automation.navigate_to_training_program():
                logging.error(
                    f"Failed to navigate to training program for {client_name}")
                return []

            # Get available workouts using the debug function
            available_workouts = automation.debug_available_workouts()
            logging.info(
                f"Found actual workouts for {client_name}: {available_workouts}")

            return available_workouts

        except Exception as e:
            logging.error(
                f"Error getting actual workouts for {client_name}: {e}")
            return []

    def map_exercises_to_actual_workouts(self, exercises_by_performance, actual_workouts):
        """Map exercises from performance data to actual workout names"""
        mapped_workouts = {}

        # Create exercise to workout mapping based on exercise types
        exercise_type_mapping = {
            # Back exercises
            'back': ['Wide Grip Chin Up', 'Lat Pull Down', 'Lat Machine', 'bent over row', 'Cable Hammer Curls'],
            # Leg exercises
            'leg': ['Squat', 'Romanian Deadlift', 'Bulgarian Lunge', 'Calf Raise'],
            # Chest exercises
            'chest': ['Bench', 'Chest Press', 'Chest Dip', 'Tricep Pushdown', 'Chest fly'],
            # Core exercises
            'core': ['Plank', 'Crunch', 'Russian Twist', 'Dead Bug'],
            # Shoulder exercises
            'shoulder': ['Shoulder Press', 'Lateral Raise', 'Front Raise', 'Rear Delt']
        }

        # For each actual workout, try to match exercises
        for workout_name in actual_workouts:
            workout_name_lower = workout_name.lower()
            mapped_workouts[workout_name] = []

            # Check each exercise from performance data
            for exercise_name, performance_data in exercises_by_performance.items():
                exercise_lower = exercise_name.lower()

                # Direct workout name matching
                if any(keyword in workout_name_lower for keyword in ['back']) and any(keyword in exercise_lower for keyword in exercise_type_mapping['back']):
                    mapped_workouts[workout_name].append(
                        {'exercise_name': exercise_name, 'performance_data': performance_data})
                elif any(keyword in workout_name_lower for keyword in ['leg']) and any(keyword in exercise_lower for keyword in exercise_type_mapping['leg']):
                    mapped_workouts[workout_name].append(
                        {'exercise_name': exercise_name, 'performance_data': performance_data})
                elif any(keyword in workout_name_lower for keyword in ['chest', 'push']) and any(keyword in exercise_lower for keyword in exercise_type_mapping['chest']):
                    mapped_workouts[workout_name].append(
                        {'exercise_name': exercise_name, 'performance_data': performance_data})
                elif any(keyword in workout_name_lower for keyword in ['core']) and any(keyword in exercise_lower for keyword in exercise_type_mapping['core']):
                    mapped_workouts[workout_name].append(
                        {'exercise_name': exercise_name, 'performance_data': performance_data})
                elif any(keyword in workout_name_lower for keyword in ['shoulder']) and any(keyword in exercise_lower for keyword in exercise_type_mapping['shoulder']):
                    mapped_workouts[workout_name].append(
                        {'exercise_name': exercise_name, 'performance_data': performance_data})

        # Remove empty workouts
        mapped_workouts = {k: v for k, v in mapped_workouts.items() if v}

        logging.info(
            f"Mapped exercises to actual workouts: {list(mapped_workouts.keys())}")
        return mapped_workouts

    def generate_smart_progressions_with_real_workouts(self, automation, client_name):
        """Generate smart progressions using actual workout names from Trainerize"""
        logging.info(
            f"\n{'='*20} SMART COACH V2 ANALYSIS: {client_name} {'='*20}")

        # Get the client's latest performance data
        latest_performance = self.get_client_latest_performance(client_name)

        if not latest_performance:
            logging.warning(f"No performance data found for {client_name}")
            return {}

        # Get actual workout names from Trainerize
        actual_workouts = self.get_actual_workouts_from_trainerize(
            automation, client_name)

        if not actual_workouts:
            logging.warning(f"No actual workouts found for {client_name}")
            return {}

        # Map exercises to actual workouts
        mapped_workouts = self.map_exercises_to_actual_workouts(
            latest_performance, actual_workouts)

        # Generate progressions for each mapped workout
        workout_progressions = {}

        for workout_name, exercises in mapped_workouts.items():
            workout_progressions[workout_name] = []

            for exercise_info in exercises:
                exercise_name = exercise_info['exercise_name']
                performance_data = exercise_info['performance_data']

                # Analyze and generate progression for this exercise
                progression = self.analyze_exercise_with_performance_data(
                    exercise_name, performance_data)

                workout_progressions[workout_name].append({
                    'exercise_name': exercise_name,
                    'reps': progression['goals'],
                    'reason': progression['reason'],
                    'set_progressions': progression['sets']
                })

        logging.info(
            f"Generated smart progressions for {len(latest_performance)} exercises across {len(workout_progressions)} actual workouts")

        return workout_progressions

    def apply_smart_progressions_single_client(self, automation, client_name, progressions_data):
        """Apply smart progressions to a single client with enhanced error handling"""
        logging.info(
            f"\n{'='*20} APPLYING PROGRESSIONS: {client_name} {'='*20}")

        try:
            # Ensure we're in a clean state
            automation.close_all_other_tabs()

            # Navigate to client (already done, but ensure we're in the right place)
            current_url = automation.driver.current_url
            if client_name.lower().replace('_', '').replace(' ', '') not in current_url.lower():
                logging.info(
                    f"Re-navigating to {client_name} to ensure correct client")
                if not automation.navigate_to_client(client_name):
                    return {'status': 'failed', 'error': 'Failed to navigate to client'}

            # Navigate to training program
            if not automation.navigate_to_training_program():
                return {'status': 'failed', 'error': 'Failed to navigate to training program'}

            successful_workouts = 0
            failed_workouts = []

            # Process each workout
            for workout_name, exercises_data in progressions_data.items():
                logging.info(f"  Processing workout: {workout_name}")

                try:
                    # Click on the workout with enhanced matching
                    if not automation.find_and_click_workout_by_name(workout_name):
                        logging.warning(
                            f"    Could not find workout: {workout_name}")
                        failed_workouts.append(
                            f"{workout_name}: Workout not found")
                        continue

                    # Enter edit mode
                    if not automation.click_edit_workout():
                        logging.warning(
                            f"    Could not enter edit mode for: {workout_name}")
                        failed_workouts.append(
                            f"{workout_name}: Could not enter edit mode")
                        automation.driver.back()
                        continue

                    # Update each exercise with enhanced name matching
                    successful_exercises = 0
                    for exercise_data in exercises_data:
                        exercise_name = exercise_data['exercise_name']
                        new_goals = exercise_data['reps']

                        logging.info(f"      Updating: {exercise_name}")

                        # Try multiple variations of the exercise name
                        exercise_variations = [
                            exercise_name,
                            exercise_name.replace('D.B', 'Dumbbell'),
                            exercise_name.replace('Dumbbell', 'D.B'),
                            exercise_name.replace('/', ' /'),
                            exercise_name.replace('/ ', '/'),
                        ]

                        updated = False
                        for variation in exercise_variations:
                            if automation.update_exercise_goal(variation, new_goals):
                                logging.info(
                                    f"        ✅ Updated {exercise_name} (using variation: {variation})")
                                successful_exercises += 1
                                updated = True
                                break

                        if not updated:
                            logging.warning(
                                f"        ❌ Failed to update {exercise_name}")

                    # Save the workout
                    logging.info(f"    Saving workout: {workout_name}")
                    try:
                        save_button = automation.wait.until(automation.EC.element_to_be_clickable(
                            (automation.By.CSS_SELECTOR, "button[data-testid='save-button'], button[title='Save Workout'], button.save-button")))
                        automation.driver.execute_script(
                            "arguments[0].click();", save_button)
                        time.sleep(3)
                        logging.info(f"    ✅ Saved workout: {workout_name}")
                        successful_workouts += 1
                    except Exception as save_error:
                        logging.error(
                            f"    ❌ Error saving workout {workout_name}: {save_error}")
                        failed_workouts.append(f"{workout_name}: Save failed")

                    # Navigate back to program overview
                    automation.driver.back()
                    time.sleep(2)

                except Exception as workout_error:
                    logging.error(
                        f"  Error processing workout {workout_name}: {workout_error}")
                    failed_workouts.append(
                        f"{workout_name}: {str(workout_error)}")
                    # Try to get back to a stable state
                    try:
                        automation.driver.back()
                        time.sleep(2)
                    except:
                        pass

            # Return results
            if successful_workouts > 0:
                status = 'success' if not failed_workouts else 'partial_success'
                return {
                    'status': status,
                    'successful_workouts': successful_workouts,
                    'failed_workouts': failed_workouts,
                    'total_workouts': len(progressions_data)
                }
            else:
                return {
                    'status': 'failed',
                    'error': 'No workouts were successfully updated',
                    'failed_workouts': failed_workouts
                }

        except Exception as e:
            logging.error(f"Error applying progressions to {client_name}: {e}")
            return {'status': 'failed', 'error': str(e)}


def test_single_client(client_name="nicole_lynch"):
    """Test the Smart Coach V2 system with a single client"""

    print("=" * 60)
    print("SMART COACH COMPLETE V2 - SINGLE CLIENT TEST")
    print("=" * 60)
    print(f"Testing with client: {client_name}")
    print("Features:")
    print("  ✅ Reads actual workout names from Trainerize")
    print("  ✅ Enhanced browser stability and tab management")
    print("  ✅ Improved exercise name fuzzy matching")
    print("  ✅ Real performance data analysis")
    print("  ✅ Set-by-set progression algorithm")

    try:
        # Initialize systems
        automation = TrainerizeAutomation()
        coach = SmartCoachCompleteV2()

        # Login to Trainerize
        username = "shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("❌ Failed to login to Trainerize")
            return

        print("✅ Successfully logged into Trainerize!")

        # Generate smart progressions using actual workout names
        smart_progressions = coach.generate_smart_progressions_with_real_workouts(
            automation, client_name
        )

        if not smart_progressions:
            print(f"❌ No progressions generated for {client_name}")
            return

        # Show summary of generated progressions
        print(f"\n{'='*60}")
        print("SMART PROGRESSIONS GENERATED")
        print(f"{'='*60}")

        total_exercises = sum(len(exercises)
                              for exercises in smart_progressions.values())
        print(
            f"\n{client_name}: {total_exercises} exercises across {len(smart_progressions)} workouts")

        for workout_name, exercises in smart_progressions.items():
            print(f"\n  📋 {workout_name}: {len(exercises)} exercises")
            for exercise in exercises:
                print(f"    • {exercise['exercise_name']}: {exercise['reps']}")

        # Ask if user wants to apply
        response = input(
            f"\n🤖 Apply smart coach progressions to {client_name}? (y/n): ")
        if response.lower() == 'y':
            # Apply the progressions
            result = coach.apply_smart_progressions_single_client(
                automation, client_name, smart_progressions
            )

            # Show results
            print(f"\n{'='*60}")
            print("APPLICATION RESULTS")
            print(f"{'='*60}")

            if result['status'] == 'success':
                print(
                    f"✅ Successfully updated all workouts for {client_name}!")
                print(
                    f"   Workouts updated: {result['successful_workouts']}/{result['total_workouts']}")
            elif result['status'] == 'partial_success':
                print(f"⚠️  Partially successful for {client_name}")
                print(
                    f"   Successful workouts: {result['successful_workouts']}/{result['total_workouts']}")
                print(f"   Failed workouts: {result['failed_workouts']}")
            else:
                print(
                    f"❌ Failed to update {client_name}: {result.get('error', 'Unknown error')}")
                if 'failed_workouts' in result:
                    print(f"   Failed workouts: {result['failed_workouts']}")
        else:
            print("📋 Progressions generated but not applied.")

        # Save progressions for reference
        with open(f'smart_coach_v2_{client_name}_progressions.json', 'w') as f:
            json.dump({client_name: smart_progressions}, f, indent=2)
        print(
            f"💾 Progressions saved to smart_coach_v2_{client_name}_progressions.json")

    except Exception as e:
        logging.error(f"Error in smart coach V2 system: {e}")
        print(f"❌ Error: {e}")

    finally:
        try:
            automation.cleanup()
        except:
            pass


def main():
    """Main function - test with Nicole Lynch first"""
    test_single_client("nicole_lynch")


if __name__ == "__main__":
    main()
