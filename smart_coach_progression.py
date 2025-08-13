#!/usr/bin/env python3
"""
Smart Coach Progression System
Analyzes real workout performance data and applies intelligent progression like a real coach would
"""

import json
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_coach_progression.log'),
        logging.StreamHandler()
    ]
)


class SmartCoachProgression:
    def __init__(self):
        self.progression_history = self.load_progression_history()
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        self.barbell_increments = 2.5  # Standard barbell/machine increment

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
            # Patterns like "S1: 20kgx9", "20kgx9", "S2: 25kg*8"
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

    def analyze_and_progress_exercise(self, exercise_name, performance_data):
        """Analyze an exercise and determine the next week's goals"""
        logging.info(f"Analyzing exercise: {exercise_name}")

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
            current_reps = int(performance_data.get('current_reps', '6').split()[
                               0]) if performance_data.get('current_reps') else 6
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

        overall_reason = f"Applied set-by-set progression algorithm (6→8→10→12→15→weight increase)"

        logging.info(f"  Next week goals: {goals_string}")

        return {
            'goals': goals_string,
            'reason': overall_reason,
            'sets': next_week_sets
        }

    def generate_smart_progressions_for_client(self, client_name):
        """Generate smart progressions for a specific client based on their actual performance"""
        logging.info(
            f"\n{'='*20} SMART COACH ANALYSIS: {client_name} {'='*20}")

        # Get the client's latest performance data
        latest_performance = self.get_client_latest_performance(client_name)

        if not latest_performance:
            logging.warning(f"No performance data found for {client_name}")
            return {}

        # Organize exercises by workout type
        workout_progressions = {}

        # Group exercises by likely workout (this is a simplified grouping)
        exercise_to_workout = {
            # Back Day exercises
            'Wide Grip Chin Up/ Assisted Chin Up': 'Back Day',
            'Lat Pull Down Wide Grip': 'Back Day',
            'Lat Machine Standing Straight Arm': 'Back Day',
            'D.B bent over row': 'Back Day',
            'Cable Hammer Curls': 'Back Day',

            # Leg Day exercises
            'Barbell Back Squat Pause': 'Leg Day',
            'Dumbbell Romanian Deadlifts': 'Leg Day',
            'Bulgarian Lunge': 'Leg Day',
            'Standing Calf Raise': 'Leg Day',

            # Chest Day exercises
            'Barbell Bench': 'Chest Day',
            'Dumbbell Chest Press': 'Chest Day',
            'Cable Chest Dip': 'Chest Day',
            'Rope Tricep Pushdown': 'Chest Day',
            'Barbell Bench Chest Press': 'Chest Day',
            'Incline Dumbbell Bench press': 'Chest Day',
            'Cable Chest fly': 'Chest Day'
        }

        # Process each exercise
        for exercise_name, performance_data in latest_performance.items():
            workout_name = exercise_to_workout.get(
                exercise_name, 'Weight Training')

            if workout_name not in workout_progressions:
                workout_progressions[workout_name] = []

            # Analyze and generate progression for this exercise
            progression = self.analyze_and_progress_exercise(
                exercise_name, performance_data)

            workout_progressions[workout_name].append({
                'exercise_name': exercise_name,
                'reps': progression['goals'],
                'reason': progression['reason'],
                'set_progressions': progression['sets']
            })

        logging.info(
            f"\nGenerated smart progressions for {len(latest_performance)} exercises across {len(workout_progressions)} workouts")

        return workout_progressions


if __name__ == "__main__":
    coach = SmartCoachProgression()

    # Test with Nicole's data
    nicole_performance = coach.get_client_latest_performance("Nicole Lynch")
    print("Nicole's latest performance:")
    for exercise, data in nicole_performance.items():
        print(f"  {exercise}: {data}")
        progression = coach.analyze_and_progress_exercise(exercise, data)
        print(f"    Next week: {progression['goals']}")
        print()
