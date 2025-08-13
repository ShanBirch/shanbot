#!/usr/bin/env python3
"""
Smart Coach Weekly System - Clean, Repeatable Weekly Program Updates
This system can run time and time again without issues.
"""

import json
import logging
from datetime import datetime
from weekly_program_updater_fixed import TrainerizeAutomation
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'smart_coach_weekly_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)


class SmartCoachWeeklySystem:
    def __init__(self):
        self.progression_history = self.load_progression_history()
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        self.barbell_increments = 2.5

        # Exercise name mappings for common mismatches
        self.exercise_name_mappings = {
            "Barbell Bench": ["Barbell Bench Press", "Bench Press", "Barbell Chest Press", "Barbell Bench"],
            "Dumbbell Chest Press": ["Dumbbell Bench Press", "DB Chest Press", "Chest Press", "Dumbbell Chest Press"],
            "Cable Chest Dip": ["Cable Dip", "Chest Dip", "Cable Chest Dips", "Cable Chest Dip"],
            "Rope Tricep Pushdown": ["Tricep Pushdown", "Cable Tricep Pushdown", "Rope Pushdown", "Rope Tricep Pushdown"],
            "Standing Calf Raise": ["Calf Raise", "Standing Calf Raise", "Standing Calf Raises"],
            "Wide Grip Chin Up/ Assisted Chin Up": ["Wide Grip Chin Up", "Assisted Chin Up", "Chin Up", "Wide Grip Chin Up/ Assisted Chin Up"],
            "D.B bent over row": ["Dumbbell Bent Over Row", "DB Bent Over Row", "Bent Over Row", "D.B bent over row"]
        }

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

        current_weight = performance_data.get('current_weight', 0)
        current_reps = int(performance_data.get('current_reps', '6'))

        # Apply rep progression algorithm
        next_reps = self.apply_rep_progression_algorithm(current_reps)

        # Determine if we need to increase weight (when reps reset to 6)
        increase_weight = (next_reps == 6 and current_reps >= 15)
        next_weight = self.get_next_weight(
            current_weight, exercise_name, increase_weight)

        # Create 3 sets with the same progression
        goals_string = f"GOALS: S1: {next_weight}kg*{next_reps} | S2: {next_weight}kg*{next_reps} | S3: {next_weight}kg*{next_reps}"

        reason = f"Progressed from {current_weight}kg x {current_reps} reps"
        if increase_weight:
            reason += f" -> increased weight to {next_weight}kg, reset to {next_reps} reps"
        else:
            reason += f" -> same weight, increased to {next_reps} reps"

        logging.info(f"  {reason}")
        logging.info(f"  Next week goals: {goals_string}")

        return {
            'goals': goals_string,
            'reason': reason
        }

    def create_logical_workout_groups(self, exercises_by_performance):
        """Create logical workout groups based on exercise types"""

        # Define exercise groupings based on common patterns
        workout_groups = {
            'Back Day': [
                'Wide Grip Chin Up/ Assisted Chin Up',
                'Lat Pull Down Wide Grip',
                'Lat Machine Standing Straight Arm',
                'D.B bent over row',
                'Cable Hammer Curls'
            ],
            'Leg Day': [
                'Barbell Back Squat Pause',
                'Dumbbell Romanian Deadlifts',
                'Bulgarian Lunge',
                'Standing Calf Raise'
            ],
            'Chest Day': [
                'Barbell Bench',
                'Dumbbell Chest Press',
                'Cable Chest Dip',
                'Rope Tricep Pushdown'
            ]
        }

        # Map exercises to workouts
        mapped_workouts = {}

        for workout_name, exercise_list in workout_groups.items():
            mapped_workouts[workout_name] = []

            for exercise_name in exercise_list:
                if exercise_name in exercises_by_performance:
                    performance_data = exercises_by_performance[exercise_name]
                    mapped_workouts[workout_name].append({
                        'exercise_name': exercise_name,
                        'performance_data': performance_data
                    })

        # Remove empty workouts
        mapped_workouts = {k: v for k, v in mapped_workouts.items() if v}

        logging.info(
            f"Created logical workout groups: {list(mapped_workouts.keys())}")
        return mapped_workouts

    def generate_smart_progressions(self, client_name):
        """Generate smart progressions using logical workout groupings"""
        logging.info(f"\n{'='*20} SMART COACH WEEKLY: {client_name} {'='*20}")

        # Get the client's latest performance data
        latest_performance = self.get_client_latest_performance(client_name)

        if not latest_performance:
            logging.warning(f"No performance data found for {client_name}")
            return {}

        logging.info(
            f"Found performance data for {len(latest_performance)} exercises")

        # Create logical workout groups
        mapped_workouts = self.create_logical_workout_groups(
            latest_performance)

        # Generate progressions for each workout
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
                    'reason': progression['reason']
                })

        logging.info(
            f"Generated smart progressions for {len(latest_performance)} exercises across {len(workout_progressions)} logical workouts")

        return workout_progressions

    def update_exercise_with_retry(self, automation, exercise_name, goals, max_retries=3):
        """Update exercise with robust retry logic and name matching"""

        # Get possible names for this exercise
        possible_names = self.exercise_name_mappings.get(
            exercise_name, [exercise_name])

        for attempt in range(max_retries):
            for name_variant in possible_names:
                try:
                    logging.info(
                        f"  Attempt {attempt + 1}: Trying '{name_variant}'...")
                    time.sleep(1)  # Brief pause for stability

                    if automation.update_exercise_goal(name_variant, goals):
                        logging.info(
                            f"  ✅ Successfully updated {name_variant}!")
                        return True, name_variant

                except Exception as e:
                    logging.warning(
                        f"  ❌ Error with '{name_variant}': {str(e)[:50]}...")
                    continue

            # If all name variants failed, wait and try again
            if attempt < max_retries - 1:
                logging.info(
                    f"  Attempt {attempt + 1} failed, waiting before retry...")
                time.sleep(3)

        return False, None

    def apply_progressions_to_trainerize(self, client_name, progressions_data):
        """Apply progressions to Trainerize with robust error handling"""

        results = {
            'client': client_name,
            'successful_workouts': 0,
            'total_workouts': len(progressions_data),
            'successful_exercises': 0,
            'total_exercises': sum(len(exercises) for exercises in progressions_data.values()),
            'failed_exercises': [],
            'status': 'pending'
        }

        try:
            # Initialize automation
            automation = TrainerizeAutomation()

            # Login
            logging.info("Logging into Trainerize...")
            if not automation.login("shannonbirch@cocospersonaltraining.com", "cyywp7nyk2"):
                results['status'] = 'failed'
                results['error'] = 'Login failed'
                return results

            # Navigate to client
            logging.info(f"Navigating to {client_name}...")
            if not automation.navigate_to_client(client_name):
                results['status'] = 'failed'
                results['error'] = 'Client navigation failed'
                return results

            # Navigate to training program
            if not automation.navigate_to_training_program():
                results['status'] = 'failed'
                results['error'] = 'Training program navigation failed'
                return results

            # Process each workout
            for workout_name, exercises in progressions_data.items():
                logging.info(f"\nProcessing workout: {workout_name}")

                try:
                    # Click on workout
                    if not automation.find_and_click_workout_by_name(workout_name):
                        logging.warning(
                            f"Could not find workout: {workout_name}")
                        results['failed_exercises'].extend(
                            [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])
                        continue

                    # Enter edit mode
                    if not automation.click_edit_workout():
                        logging.warning(
                            f"Could not enter edit mode for: {workout_name}")
                        results['failed_exercises'].extend(
                            [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])
                        continue

                    # Update each exercise
                    workout_success = True
                    for exercise in exercises:
                        exercise_name = exercise['exercise_name']
                        goals = exercise['reps']

                        success, used_name = self.update_exercise_with_retry(
                            automation, exercise_name, goals)

                        if success:
                            results['successful_exercises'] += 1
                            logging.info(f"    ✅ Updated {used_name}")
                        else:
                            results['failed_exercises'].append(
                                f"{workout_name} - {exercise_name}")
                            workout_success = False
                            logging.warning(
                                f"    ❌ Failed to update {exercise_name}")

                    # Save workout (simplified - just go back)
                    logging.info("  Navigating back to program...")
                    automation.driver.back()
                    time.sleep(3)

                    if workout_success:
                        results['successful_workouts'] += 1

                except Exception as e:
                    logging.error(
                        f"Error processing workout {workout_name}: {e}")
                    results['failed_exercises'].extend(
                        [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])

            # Determine final status
            if results['successful_exercises'] == results['total_exercises']:
                results['status'] = 'success'
            elif results['successful_exercises'] > 0:
                results['status'] = 'partial_success'
            else:
                results['status'] = 'failed'

        except Exception as e:
            logging.error(f"Critical error: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)

        finally:
            try:
                automation.cleanup()
            except:
                pass

        return results

    def run_weekly_update(self, client_name):
        """Run the complete weekly update for a client"""

        print("=" * 60)
        print("SMART COACH WEEKLY SYSTEM")
        print("=" * 60)
        print(f"Client: {client_name}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🧠 SMART FEATURES:")
        print("  ✅ Real performance data analysis")
        print("  ✅ 6→8→10→12→15→weight increase algorithm")
        print("  ✅ Equipment-specific weight increments")
        print("  ✅ Robust exercise name matching")
        print("  ✅ Retry logic for failed updates")
        print("  ✅ Comprehensive error handling")

        # Generate smart progressions
        progressions = self.generate_smart_progressions(client_name)

        if not progressions:
            print(f"❌ No progressions generated for {client_name}")
            return False

        # Show summary
        total_exercises = sum(len(exercises)
                              for exercises in progressions.values())
        print(f"\n📋 GENERATED PROGRESSIONS:")
        print(f"  Workouts: {len(progressions)}")
        print(f"  Total exercises: {total_exercises}")

        for workout_name, exercises in progressions.items():
            print(f"\n  🏋️ {workout_name}: {len(exercises)} exercises")
            for exercise in exercises:
                print(f"    • {exercise['exercise_name']}")
                print(f"      {exercise['reason']}")
                print(f"      {exercise['reps']}")

        # Ask for confirmation
        response = input(
            f"\n🤖 Apply these progressions to {client_name} in Trainerize? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return False

        # Apply to Trainerize
        print(f"\n🚀 Applying progressions to Trainerize...")
        results = self.apply_progressions_to_trainerize(
            client_name, progressions)

        # Show results
        print(f"\n{'='*60}")
        print("WEEKLY UPDATE RESULTS")
        print(f"{'='*60}")

        if results['status'] == 'success':
            print(f"✅ COMPLETE SUCCESS!")
            print(
                f"  All {results['total_exercises']} exercises updated successfully")
            print(f"  All {results['total_workouts']} workouts completed")
        elif results['status'] == 'partial_success':
            print(f"⚠️  PARTIAL SUCCESS")
            print(
                f"  Successfully updated: {results['successful_exercises']}/{results['total_exercises']} exercises")
            print(
                f"  Successfully completed: {results['successful_workouts']}/{results['total_workouts']} workouts")
            if results['failed_exercises']:
                print(
                    f"  Failed exercises: {', '.join(results['failed_exercises'])}")
        else:
            print(f"❌ FAILED")
            print(f"  Error: {results.get('error', 'Unknown error')}")
            if results['failed_exercises']:
                print(
                    f"  Failed exercises: {', '.join(results['failed_exercises'])}")

        # Save results for record keeping
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"weekly_update_results_{client_name.replace(' ', '_')}_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump({
                'client': client_name,
                'timestamp': timestamp,
                'progressions': progressions,
                'results': results
            }, f, indent=2)

        print(f"\n💾 Results saved to {results_file}")

        return results['status'] in ['success', 'partial_success']


def main():
    """Main function"""
    coach = SmartCoachWeeklySystem()
    coach.run_weekly_update("Nicole Lynch")


if __name__ == "__main__":
    main()
