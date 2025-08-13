#!/usr/bin/env python3
"""
Generate Set-by-Set Progressions with New Rep Algorithm
Analyzes each individual set and applies progression logic separately
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from progressive_overload_ai import ProgressiveOverloadAI

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class SetBySetProgressionGenerator:
    def __init__(self):
        self.ai = ProgressiveOverloadAI()
        self.logger = logging.getLogger(__name__)

    def get_next_dumbbell_weight(self, current_weight: float) -> float:
        """Get next dumbbell weight using gym increments"""
        dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15, 17.5,
                            20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        # Continue with +2.5kg increments after 50kg
        for w in dumbbell_weights:
            if w > current_weight:
                return w
        # Beyond 50kg, use +2.5kg increments
        return current_weight + 2.5

    def get_next_weight(self, current_weight: float, equipment_type: str) -> float:
        """Get next weight based on equipment type"""
        if equipment_type == 'dumbbell':
            return self.get_next_dumbbell_weight(current_weight)
        else:  # barbell or machine
            return current_weight + 2.5

    def determine_equipment_type(self, exercise_name: str) -> str:
        """Determine equipment type from exercise name"""
        exercise_lower = exercise_name.lower()
        if any(word in exercise_lower for word in ['dumbbell', 'db', 'alternating']):
            return 'dumbbell'
        elif any(word in exercise_lower for word in ['barbell', 'bb', 'bench press', 'squat', 'deadlift']):
            return 'barbell'
        else:
            return 'machine'  # default for cable, lat pull, seated, etc.

    def get_next_rep_target(self, current_target: int) -> int:
        """Get next rep target using 6→8→10→12→15 progression"""
        rep_progression = [6, 8, 10, 12, 15]
        for target in rep_progression:
            if current_target < target:
                return target
        return 15  # Max out at 15

    def analyze_set_progression(self, exercise_name: str, set_number: int,
                                current_weight: float, achieved_reps: int,
                                target_reps: int) -> Dict:
        """Analyze progression for a single set"""

        equipment_type = self.determine_equipment_type(exercise_name)

        # Progress if they achieved target reps or within 1 rep
        if achieved_reps >= (target_reps - 1):
            if target_reps < 15:
                # Increase reps
                next_target = self.get_next_rep_target(target_reps)
                return {
                    "weight": current_weight,
                    "reps": next_target,
                    "reason": f"S{set_number}: Achieved {achieved_reps} reps (target: {target_reps}). Progressing to {next_target} reps.",
                    "action": "increase_reps"
                }
            else:
                # At 15 reps, increase weight and reset to 6
                next_weight = self.get_next_weight(
                    current_weight, equipment_type)
                return {
                    "weight": next_weight,
                    "reps": 6,
                    "reason": f"S{set_number}: Achieved {achieved_reps} reps at 15 target. Increasing weight to {next_weight}kg and resetting to 6 reps.",
                    "action": "increase_weight"
                }
        else:
            # More than 1 rep below target, maintain
            return {
                "weight": current_weight,
                "reps": target_reps,
                "reason": f"S{set_number}: Achieved {achieved_reps} reps (target: {target_reps}). Need to be within 1 rep to progress.",
                "action": "maintain"
            }

    def generate_exercise_set_progressions(self, exercise_name: str, recent_performance) -> Optional[Dict]:
        """Generate set-by-set progression for an exercise"""

        if not recent_performance.sets or len(recent_performance.sets) == 0:
            return None

        set_progressions = []

        # Process up to 3 sets (S1, S2, S3)
        for i in range(min(3, len(recent_performance.sets))):
            workout_set = recent_performance.sets[i]
            set_number = i + 1

            if not workout_set.completed or workout_set.reps <= 0:
                continue

            # Infer target reps from achieved reps (find closest progression target)
            rep_progression = [6, 8, 10, 12, 15]
            target_reps = workout_set.reps

            # Find the appropriate target from our progression sequence
            for target in rep_progression:
                if workout_set.reps <= target:
                    target_reps = target
                    break
            else:
                target_reps = 15

            progression = self.analyze_set_progression(
                exercise_name=exercise_name,
                set_number=set_number,
                current_weight=workout_set.weight,
                achieved_reps=workout_set.reps,
                target_reps=target_reps
            )

            set_progressions.append(progression)

        if set_progressions:
            # Create Trainerize format goals
            set_goals = []
            for i, prog in enumerate(set_progressions):
                set_goals.append(f"S{i+1}: {prog['weight']}kg*{prog['reps']}")

            goals_format = f"GOALS: {' | '.join(set_goals)}"

            return {
                "action": "modify_goals",
                "exercise_name": exercise_name,
                # Use first set weight for compatibility
                "weight": str(set_progressions[0]['weight']),
                "reps": goals_format,  # Put full goals in reps field
                "set_progressions": set_progressions
            }

        return None

    def generate_client_progressions(self, client_name: str) -> Dict:
        """Generate set-by-set progressions for a client organized by workout"""

        self.logger.info(
            f"Generating set-by-set progressions for {client_name}...")

        # Load workout data
        workout_data = self.ai.load_client_workout_data_from_sqlite(
            client_name)

        if not workout_data:
            self.logger.warning(f"No workout data found for {client_name}")
            return {}

            # Group by workout name first, then by exercise
        workout_groups = {}
        for performance in workout_data:
            # Use workout_type instead of workout_name
            workout_name = performance.workout_type
            if workout_name not in workout_groups:
                workout_groups[workout_name] = {}

            exercise_name = performance.exercise_name
            if exercise_name not in workout_groups[workout_name]:
                workout_groups[workout_name][exercise_name] = []
            workout_groups[workout_name][exercise_name].append(performance)

        # Generate progressions organized by workout
        workout_progressions = {}

        for workout_name, exercise_groups in workout_groups.items():
            progressions = []

            for exercise_name, performances in exercise_groups.items():
                # Sort by date and get most recent
                performances.sort(key=lambda x: x.date)
                recent_performance = performances[-1]

                progression = self.generate_exercise_set_progressions(
                    exercise_name, recent_performance)
                if progression:
                    progressions.append(progression)
                    self.logger.info(
                        f"  ✅ Generated set-by-set progression for {exercise_name}")

            if progressions:
                workout_progressions[workout_name] = progressions

        return workout_progressions


def main():
    print("🏋️ Generating Set-by-Set Progressions with New Rep Algorithm...")

    # Load client names from fitness wrapped data files
    try:
        import glob
        checkin_dir = "output/checkin_reviews"
        fitness_files = glob.glob(f"{checkin_dir}/*_fitness_wrapped_data.json")

        client_names = []
        for file_path in fitness_files:
            # Extract client name from filename: ClientName_YYYY-MM-DD_fitness_wrapped_data.json
            filename = os.path.basename(file_path)
            client_name = filename.split('_fitness_wrapped_data.json')[0]

            # Remove date suffix if present (e.g., "Alice_Forster_2025-06-14" -> "Alice_Forster")
            import re
            client_name = re.sub(r'_\d{4}-\d{2}-\d{2}$', '', client_name)

            # Convert to database format (lowercase with underscores)
            db_client_name = client_name.lower()
            client_names.append(db_client_name)

        print(
            f"📋 Found {len(client_names)} clients from fitness wrapped data files")
        if client_names:
            print(f"   Clients: {', '.join(client_names[:5])}")
            if len(client_names) > 5:
                print(f"   ... and {len(client_names) - 5} more")
    except Exception as e:
        print(f"❌ Error loading client names: {e}")
        print("Using default client list.")
        client_names = ["Alice Forster", "Anna Somogyi", "Elena Green"]

    generator = SetBySetProgressionGenerator()
    all_client_progressions = {}

    for db_client_name in client_names:
        # Convert database name back to display name for Trainerize
        display_name = db_client_name.replace('_', ' ').title()
        print(f"\nProcessing {display_name} (DB: {db_client_name})...")

        progressions = generator.generate_client_progressions(db_client_name)

        if progressions:
            # Store using display name for Trainerize compatibility
            all_client_progressions[display_name] = progressions

            # Count total exercises across all workouts
            total_exercises = sum(len(exercises)
                                  for exercises in progressions.values())
            workout_count = len(progressions)
            print(
                f"  ✅ Generated {total_exercises} exercise progressions across {workout_count} workouts")
        else:
            print(f"  ⚠️ No progressions generated")

    # Save results in format compatible with weekly_program_updater
    with open('set_by_set_progressions.json', 'w') as f:
        json.dump(all_client_progressions, f, indent=2)

    print(f"\n📊 Summary:")
    print(f"  • {len(all_client_progressions)} clients processed")

    # Count total exercises and workouts
    total_exercises = 0
    total_workouts = 0
    for client_data in all_client_progressions.values():
        total_workouts += len(client_data)
        for workout_exercises in client_data.values():
            total_exercises += len(workout_exercises)

    print(f"  • {total_exercises} exercises with set-by-set progressions")
    print(f"  • {total_workouts} workouts across all clients")
    print(f"  💾 Saved to: set_by_set_progressions.json")

    # Show sample
    if all_client_progressions:
        sample_client = list(all_client_progressions.keys())[0]
        sample_workout = list(all_client_progressions[sample_client].keys())[0]
        sample_exercise = all_client_progressions[sample_client][sample_workout][0]
        print(
            f"\n📋 Sample set-by-set progression for {sample_client} - {sample_workout}:")
        print(
            f"  {sample_exercise['exercise_name']}: {sample_exercise['reps']}")

        # Show individual set details
        if 'set_progressions' in sample_exercise:
            for prog in sample_exercise['set_progressions']:
                print(f"    {prog['reason']}")


if __name__ == "__main__":
    main()
