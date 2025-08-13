#!/usr/bin/env python3
"""
Complete Smart Coach System
Uses real performance data to generate intelligent progressions and applies them to Trainerize
"""

import json
import logging
from datetime import datetime, timedelta
from weekly_program_updater_fixed import TrainerizeAutomation
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_coach_complete.log'),
        logging.StreamHandler()
    ]
)


class SmartCoachComplete:
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
                import re
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
            progression = self.analyze_exercise_with_performance_data(
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

    def generate_smart_progressions_for_all_clients(self):
        """Generate smart progressions for all clients with performance data"""
        all_client_progressions = {}

        print("=" * 60)
        print("COMPLETE SMART COACH PROGRESSION SYSTEM")
        print("=" * 60)
        print("Analyzing real workout performance and applying intelligent progression...")

        # Get all clients with progression history
        clients_with_data = list(self.progression_history.keys())

        print(
            f"\nFound performance data for {len(clients_with_data)} clients:")
        for client in clients_with_data:
            print(f"  • {client}")

        # Generate progressions for each client
        for client_name in clients_with_data:
            progressions = self.generate_smart_progressions_for_client(
                client_name)
            if progressions:
                all_client_progressions[client_name] = progressions

        return all_client_progressions

    def save_smart_progressions(self, progressions, filename='smart_coach_complete_progressions.json'):
        """Save the generated smart progressions"""
        try:
            with open(filename, 'w') as f:
                json.dump(progressions, f, indent=2)
            logging.info(f"Smart progressions saved to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving smart progressions: {e}")
            return False


def main():
    """Main function to run the complete smart coach system"""

    # Initialize the smart coach system
    coach = SmartCoachComplete()

    # Generate smart progressions for all clients
    smart_progressions = coach.generate_smart_progressions_for_all_clients()

    if not smart_progressions:
        print("No client data found to generate progressions")
        return

    # Save the smart progressions
    coach.save_smart_progressions(smart_progressions)

    # Show summary
    print(f"\n{'='*60}")
    print("SMART COACH PROGRESSION SUMMARY")
    print(f"{'='*60}")

    total_exercises = 0
    for client_name, workouts in smart_progressions.items():
        client_exercises = sum(len(exercises)
                               for exercises in workouts.values())
        total_exercises += client_exercises
        print(
            f"\n{client_name}: {client_exercises} exercises across {len(workouts)} workouts")

        for workout_name, exercises in workouts.items():
            print(f"  • {workout_name}: {len(exercises)} exercises")
            for exercise in exercises[:3]:  # Show first 3 exercises
                print(f"    - {exercise['exercise_name']}: {exercise['reps']}")
            if len(exercises) > 3:
                print(f"    ... and {len(exercises) - 3} more exercises")

    print(
        f"\nTotal: {len(smart_progressions)} clients, {total_exercises} exercises")
    print(f"\n🎯 Smart Coach Features:")
    print(f"  • Real performance data analyzed")
    print(f"  • Set-by-set progression algorithm (6→8→10→12→15→weight increase)")
    print(f"  • Equipment-specific weight increments (dumbbells vs barbells)")
    print(f"  • Missing exercise data handled gracefully")
    print(f"  • Intelligent workout grouping")

    # Ask if user wants to apply these progressions
    response = input(
        f"\nApply smart coach progressions to Trainerize? (y/n): ")
    if response.lower() == 'y':
        apply_smart_progressions(smart_progressions)


def apply_smart_progressions(progressions_data):
    """Apply the smart progressions to Trainerize"""
    print("\nApplying smart coach progressions to Trainerize...")

    try:
        automation = TrainerizeAutomation()

        # Login to Trainerize
        username = "shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            print("Failed to login to Trainerize")
            return

        print("Successfully logged into Trainerize!")

        # Process all clients with smart progressions
        results = automation.process_multiple_clients(progressions_data)

        # Show results
        print(f"\n{'='*60}")
        print("SMART COACH DEPLOYMENT COMPLETE")
        print(f"{'='*60}")

        successful = sum(1 for result in results.values()
                         if result.get('status') == 'success')
        failed = len(results) - successful

        print(f"\nResults:")
        print(f"  ✅ Successfully updated: {successful} clients")
        print(f"  ❌ Failed: {failed} clients")

        if failed > 0:
            print(f"\nFailed clients:")
            for client, result in results.items():
                if result.get('status') != 'success':
                    print(
                        f"  • {client}: {result.get('error', 'Unknown error')}")

        print(f"\n🎯 Smart Coach System Applied:")
        print(f"  • Real performance data analyzed")
        print(f"  • Set-by-set progression algorithm applied")
        print(f"  • Intelligent weight progression based on actual performance")
        print(f"  • Missing exercise data handled gracefully")

    except Exception as e:
        logging.error(f"Error applying smart progressions: {e}")
        print(f"Error: {e}")

    finally:
        try:
            automation.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
