#!/usr/bin/env python3
"""
Smart Coach Simple Test - Bypasses workout name detection
Uses logical exercise groupings based on Nicole's actual exercises
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_coach_simple_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class SmartCoachSimpleTest:
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
        try:
            latest_entry = max(client_history, key=lambda x: x['date'])
            return latest_entry.get('progressions', {})
        except (ValueError, TypeError):
            logging.error(
                f"Could not determine latest entry for {client_name} due to invalid data in progression_history.json")
            return {}

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

        # Check if performance_data is a dictionary, not a list
        if not isinstance(performance_data, dict):
            logging.warning(
                f"Performance data for {exercise_name} is not a valid dictionary. Skipping.")
            return {'goals': 'GOALS: Check logs, performance data invalid.', 'reason': 'Invalid data format'}

        current_weight = performance_data.get('current_weight', 0)
        try:
            current_reps = int(performance_data.get('current_reps', '6'))
        except (ValueError, TypeError):
            logging.warning(
                f"Could not convert performance_data reps '{performance_data.get('current_reps')}' to int. Defaulting to 6.")
            current_reps = 6

        # Apply rep progression algorithm
        next_reps = self.apply_rep_progression_algorithm(current_reps)

        # Determine if we need to increase weight (when reps reset to 6)
        increase_weight = (next_reps == 6 and current_reps >= 15)
        next_weight = self.get_next_weight(
            current_weight, exercise_name, increase_weight)

        # Create 3 sets with the same progression based on the single data point
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

        # Define exercise groupings based on Nicole's actual exercises
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
            ],
            'Core Day': [
                'Ab Crunch Machine',
                'Cable Crunches',
                'Leg Raises',
                'Plank',
                'Side Plank'
            ],
            'Shoulder Day': [
                'Dumbbell Shoulder Press',
                'Dumbbell Lateral Raises',
                'Dumbbell Front Raises',
                'Face Pulls',
                'Barbell Shrugs'
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
            f"Created logical workout groups: {str(list(mapped_workouts.keys()))}")
        return mapped_workouts

    def generate_smart_progressions(self, client_name):
        """Generate smart progressions using logical workout groupings"""
        logging.info(
            f"\n{'='*20} SMART COACH SIMPLE TEST: {client_name} {'='*20}")

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
                performance_data = exercise_info.get(
                    'performance_data')  # Use .get for safety

                # If no performance data, create a default goal
                if not performance_data:
                    logging.info(
                        f"No performance data for '{exercise_name}'. Creating default goal.")
                    progression = {
                        'goals': 'GOALS: S1: 0kg*6 | S2: 0kg*6 | S3: 0kg*6',
                        'reason': 'No performance data from last week. Starting with baseline.'
                    }
                else:
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


def test_nicole_lynch():
    """Test the Smart Coach system with Nicole Lynch using logical workout groups"""

    print("=" * 60)
    print("SMART COACH SIMPLE TEST - NICOLE LYNCH")
    print("=" * 60)
    print("Features:")
    print("  ✅ Uses logical workout groupings (Back Day, Leg Day, Chest Day)")
    print("  ✅ Real performance data analysis")
    print("  ✅ Set-by-set progression algorithm (6→8→10→12→15→weight increase)")
    print("  ✅ Equipment-specific weight increments")

    try:
        # Initialize smart coach
        coach = SmartCoachSimpleTest()

        # Generate smart progressions for Nicole Lynch
        smart_progressions = coach.generate_smart_progressions("Nicole Lynch")

        if not smart_progressions:
            print("❌ No progressions generated for Nicole Lynch")
            return

        # Show summary of generated progressions
        print(f"\n{'='*60}")
        print("SMART PROGRESSIONS GENERATED FOR NICOLE LYNCH")
        print(f"{'='*60}")

        total_exercises = sum(len(exercises)
                              for exercises in smart_progressions.values())
        print(
            f"Generated progressions for {total_exercises} exercises across {len(smart_progressions)} logical workouts:")

        # Save progressions to file
        output_filename = "set_by_set_progressions.json"
        # Restructure data to be client-centric
        client_centric_progressions = {
            "nicole_lynch": smart_progressions
        }

        with open(output_filename, 'w') as f:
            json.dump(client_centric_progressions, f, indent=4)
        print(f"\n✅ Progressions saved to {output_filename}")

        print("\nReady to apply these progressions to Trainerize using 'update_with_set_by_set_progressions_clean.py'")

    except Exception as e:
        logging.error(
            f"Error during Smart Coach test for Nicole Lynch: {e}", exc_info=True)
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    test_nicole_lynch()
