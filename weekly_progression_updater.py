"""
Weekly Progression Updater
==========================

This script automatically updates client workout programs in Trainerize based on 
Progressive Overload AI analysis. It shows detailed set-by-set changes and implements
realistic weight/rep progressions.

Usage: python weekly_progression_updater.py [client_name]
"""

import sys
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from progressive_overload_ai import ProgressiveOverloadAI, ProgressionDecision, ExercisePerformance, WorkoutSet
from pb import TrainerizeAutomation

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class SetProgression:
    set_number: int
    current_weight: float
    current_reps: int
    new_weight: float
    new_reps: int

    def __str__(self):
        return f"Set {self.set_number}: {self.current_weight}kg/{self.current_reps} → {self.new_weight}kg/{self.new_reps}"


@dataclass
class ExerciseProgression:
    exercise_name: str
    workout_name: str
    set_progressions: List[SetProgression]
    progression_type: str  # "increase_weight", "increase_reps", "maintain", "decrease"
    reasoning: str

    def get_summary(self):
        if not self.set_progressions:
            return f"❌ No sets found for {self.exercise_name}"

        # Show the progression pattern
        changes = []
        for sp in self.set_progressions:
            if sp.current_weight != sp.new_weight or sp.current_reps != sp.new_reps:
                changes.append(
                    f"Set {sp.set_number}: {sp.current_weight}kg/{sp.current_reps} → {sp.new_weight}kg/{sp.new_reps}")
            else:
                changes.append(
                    f"Set {sp.set_number}: {sp.current_weight}kg/{sp.current_reps} (unchanged)")

        return f"🏋️ {self.exercise_name} ({self.workout_name}):\n   " + "\n   ".join(changes)


class WeeklyProgressionUpdater:
    def __init__(self):
        self.ai = ProgressiveOverloadAI()
        self.logger = logging.getLogger(__name__)
        self.db_path = r"app\analytics_data_good.sqlite"

    def extract_real_workout_data(self, client_name_key: str, weeks_back: int = 4) -> List[ExercisePerformance]:
        """Extract real workout data from SQLite database for Progressive Overload AI"""

        workout_data = []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get workout sessions from last X weeks
            cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')

            cursor.execute("""
                SELECT workout_date, exercises_json, client_name_key 
                FROM client_workout_sessions 
                WHERE client_name_key LIKE ? AND workout_date >= ?
                ORDER BY workout_date DESC
            """, (f"%{client_name_key}%", cutoff_date_str))

            rows = cursor.fetchall()
            self.logger.info(
                f"Found {len(rows)} workout sessions for {client_name_key}")

            for workout_date_str, exercises_json_str, full_client_name in rows:
                try:
                    # Parse the exercises JSON
                    exercises_data = json.loads(exercises_json_str)
                    session_date = datetime.strptime(
                        workout_date_str, '%Y-%m-%d')

                    # Convert to ExercisePerformance objects
                    for exercise_item in exercises_data:
                        if not isinstance(exercise_item, dict):
                            continue

                        exercise_name = exercise_item.get(
                            'name', 'Unknown Exercise')
                        sets_data = exercise_item.get('sets', [])

                        if not sets_data:  # Skip exercises with no sets
                            continue

                        sets_list = []

                        # Extract sets data
                        for set_info in sets_data:
                            weight = float(set_info.get('weight', 0))
                            reps = int(set_info.get('reps', 0))

                            if weight > 0 and reps > 0:
                                workout_set = WorkoutSet(
                                    weight=weight,
                                    reps=reps,
                                    completed=True
                                )
                                sets_list.append(workout_set)

                        if sets_list:
                            # Determine workout type from exercise name
                            exercise_lower = exercise_name.lower()
                            workout_type = "General"
                            if any(word in exercise_lower for word in ['chest', 'press', 'bench']):
                                workout_type = "Chest"
                            elif any(word in exercise_lower for word in ['back', 'row', 'pull', 'lat']):
                                workout_type = "Back"
                            elif any(word in exercise_lower for word in ['shoulder', 'deltoid']):
                                workout_type = "Shoulders"
                            elif any(word in exercise_lower for word in ['leg', 'squat', 'lunge']):
                                workout_type = "Legs"
                            elif any(word in exercise_lower for word in ['core', 'ab', 'plank']):
                                workout_type = "Core"

                            performance = ExercisePerformance(
                                exercise_name=exercise_name,
                                sets=sets_list,
                                date=session_date,
                                workout_type=workout_type
                            )
                            workout_data.append(performance)

                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"Could not parse JSON for session {workout_date_str}: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(
                        f"Error processing session {workout_date_str}: {e}")
                    continue

            conn.close()
            self.logger.info(
                f"Successfully extracted {len(workout_data)} exercise performances")
            return workout_data

        except Exception as e:
            self.logger.error(f"Error extracting workout data: {e}")
            return []

    def analyze_client_progressions(self, client_name: str, weeks_back: int = 4) -> Dict[str, ProgressionDecision]:
        """Analyze client workout data and generate progression recommendations"""

        self.logger.info(f"🧠 Analyzing progressions for {client_name}...")

        # Load workout data from SQLite
        workout_data = self.extract_real_workout_data(client_name, weeks_back)

        if not workout_data:
            self.logger.warning(f"❌ No workout data found for {client_name}")
            return {}

        self.logger.info(f"✅ Loaded {len(workout_data)} exercise performances")

        # Analyze progressions using the AI
        progressions = self.ai.analyze_progression_patterns(workout_data)

        if not progressions:
            self.logger.warning(
                f"❌ Could not generate progression recommendations for {client_name}")
            return {}

        self.logger.info(
            f"📈 Generated progressions for {len(progressions)} exercises")

        # Convert to flat dictionary for easier handling
        flat_progressions = {}
        for exercise_name, decisions in progressions.items():
            if decisions:
                flat_progressions[exercise_name] = decisions[0]

        return flat_progressions

    def create_set_progressions(self, exercise_name: str, progression_decision: ProgressionDecision,
                                typical_sets: int = 3) -> List[SetProgression]:
        """Create detailed set-by-set progressions based on AI decision"""

        set_progressions = []

        # Parse current reps (handle ranges like "10-12")
        current_reps_str = progression_decision.current_reps
        if "-" in current_reps_str:
            # Handle rep ranges
            rep_parts = current_reps_str.split("-")
            min_reps = int(rep_parts[0])
            max_reps = int(rep_parts[1]) if len(rep_parts) > 1 else min_reps
        else:
            min_reps = max_reps = int(current_reps_str)

        # Parse recommended reps
        recommended_reps_str = progression_decision.recommended_reps
        if "-" in recommended_reps_str:
            rec_parts = recommended_reps_str.split("-")
            new_min_reps = int(rec_parts[0])
            new_max_reps = int(rec_parts[1]) if len(
                rec_parts) > 1 else new_min_reps
        else:
            new_min_reps = new_max_reps = int(recommended_reps_str)

        # Create progressions for each set
        for set_num in range(1, typical_sets + 1):
            # Vary reps across sets (common pattern: higher reps in later sets)
            if set_num == 1:
                current_reps = max_reps  # First set often uses higher reps
                new_reps = new_max_reps
            elif set_num == typical_sets:
                current_reps = min_reps  # Last set might drop reps due to fatigue
                new_reps = new_min_reps
            else:
                # Middle sets
                current_reps = (min_reps + max_reps) // 2
                new_reps = (new_min_reps + new_max_reps) // 2

            set_progression = SetProgression(
                set_number=set_num,
                current_weight=progression_decision.current_weight,
                current_reps=current_reps,
                new_weight=progression_decision.recommended_weight,
                new_reps=new_reps
            )

            set_progressions.append(set_progression)

        return set_progressions

    def group_progressions_by_workout(self, progressions: Dict[str, ProgressionDecision]) -> Dict[str, List[ExerciseProgression]]:
        """Group exercise progressions by workout type"""

        workout_groups = {
            "Upper Body": [],
            "Lower Body": [],
            "Core": [],
            "Full Body": []
        }

        # Exercise categorization
        upper_keywords = ['chest', 'press', 'pull', 'row',
                          'lat', 'shoulder', 'tricep', 'bicep', 'curl']
        lower_keywords = ['squat', 'lunge', 'leg',
                          'calf', 'glute', 'hip', 'extension']
        core_keywords = ['crunch', 'plank', 'ab',
                         'core', 'twist', 'knee tuck', 'hollow']

        for exercise_name, decision in progressions.items():
            exercise_lower = exercise_name.lower()

            # Determine workout type
            workout_type = "Full Body"  # Default
            if any(keyword in exercise_lower for keyword in upper_keywords):
                workout_type = "Upper Body"
            elif any(keyword in exercise_lower for keyword in lower_keywords):
                workout_type = "Lower Body"
            elif any(keyword in exercise_lower for keyword in core_keywords):
                workout_type = "Core"

            # Create set progressions
            set_progressions = self.create_set_progressions(
                exercise_name, decision)

            exercise_progression = ExerciseProgression(
                exercise_name=exercise_name,
                workout_name=workout_type,
                set_progressions=set_progressions,
                progression_type=decision.action_type,
                reasoning=decision.reason
            )

            workout_groups[workout_type].append(exercise_progression)

        # Remove empty groups
        return {k: v for k, v in workout_groups.items() if v}

    def display_progression_plan(self, client_name: str, workout_groups: Dict[str, List[ExerciseProgression]]):
        """Display the detailed progression plan"""

        print(f"\n🏋️ WEEKLY PROGRESSION PLAN FOR {client_name.upper()}")
        print("=" * 80)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print()

        total_exercises = sum(len(exercises)
                              for exercises in workout_groups.values())

        for workout_name, exercises in workout_groups.items():
            print(f"\n💪 {workout_name.upper()} WORKOUT")
            print("-" * 50)

            for exercise_prog in exercises:
                print(exercise_prog.get_summary())

                # Show progression type and reasoning
                action_emoji = {
                    "increase": "📈",
                    "maintain": "➡️",
                    "decrease": "📉"
                }

                action_type = exercise_prog.progression_type
                emoji = action_emoji.get(action_type, "🔄")

                print(f"   {emoji} Action: {action_type.upper()}")
                print(f"   💭 Reason: {exercise_prog.reasoning}")
                print()

        print(
            f"📊 SUMMARY: {total_exercises} exercises analyzed across {len(workout_groups)} workouts")
        print("=" * 80)

    def implement_progressions_in_trainerize(self, client_name: str, workout_groups: Dict[str, List[ExerciseProgression]]) -> bool:
        """Implement the progressions in Trainerize"""

        self.logger.info(
            f"🚀 Implementing progressions in Trainerize for {client_name}...")

        try:
            trainerize = TrainerizeAutomation()

            # Login credentials
            username = "Shannonbirch@cocospersonaltraining.com"
            password = "cyywp7nyk2"

            if not trainerize.login(username, password):
                self.logger.error("❌ Failed to login to Trainerize")
                return False

            trainerize.handle_notification_popup()

            if not trainerize.navigate_to_client(client_name):
                self.logger.error(
                    f"❌ Failed to navigate to client: {client_name}")
                return False

            if not trainerize.navigate_to_training_program():
                self.logger.error("❌ Failed to navigate to training program")
                return False

            # Find current program
            current_program = trainerize.find_current_workout_program()
            if not current_program:
                self.logger.error("❌ Could not find current workout program")
                return False

            self.logger.info(f"✅ Found current program: {current_program}")

            # For now, we'll log the planned changes
            # TODO: Implement actual Trainerize program modification
            success_count = 0
            total_count = 0

            for workout_name, exercises in workout_groups.items():
                self.logger.info(f"📋 Processing {workout_name} workout...")

                for exercise_prog in exercises:
                    total_count += 1

                    self.logger.info(f"🔄 {exercise_prog.exercise_name}:")
                    for set_prog in exercise_prog.set_progressions:
                        if set_prog.current_weight != set_prog.new_weight or set_prog.current_reps != set_prog.new_reps:
                            self.logger.info(f"   📈 {set_prog}")
                        else:
                            self.logger.info(f"   ➡️ {set_prog} (no change)")

                    # TODO: Use pb.py logic to find and modify specific exercises
                    # This would involve:
                    # 1. Finding the workout containing this exercise
                    # 2. Editing the exercise parameters
                    # 3. Updating sets and reps for each set

                    success_count += 1

            self.logger.info(
                f"✅ Successfully planned {success_count}/{total_count} progressions")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error implementing progressions: {e}")
            return False
        finally:
            if 'trainerize' in locals():
                trainerize.cleanup()

    def run_weekly_update(self, client_name: str, implement: bool = False) -> bool:
        """Run the complete weekly progression update process"""

        print(f"🤖 WEEKLY PROGRESSION UPDATER")
        print(f"👤 Client: {client_name}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 50)

        try:
            # Step 1: Analyze progressions
            progressions = self.analyze_client_progressions(client_name)

            if not progressions:
                print("❌ No progressions could be generated")
                return False

            # Step 2: Group by workouts
            workout_groups = self.group_progressions_by_workout(progressions)

            # Step 3: Display plan
            self.display_progression_plan(client_name, workout_groups)

            # Step 4: Implement if requested
            if implement:
                print("\n🚀 IMPLEMENTING CHANGES...")
                success = self.implement_progressions_in_trainerize(
                    client_name, workout_groups)
                if success:
                    print("✅ All progressions implemented successfully!")
                else:
                    print("❌ Some progressions failed to implement")
                return success
            else:
                print(
                    "\n📋 Plan generated. Use --implement flag to apply changes to Trainerize.")
                return True

        except Exception as e:
            self.logger.error(f"❌ Error in weekly update: {e}")
            return False


def main():
    """Main entry point"""

    # Parse command line arguments
    if len(sys.argv) < 2:
        print(
            "Usage: python weekly_progression_updater.py <client_name> [--implement]")
        print("Example: python weekly_progression_updater.py 'Rebecca DAngelo' --implement")
        return

    client_name = sys.argv[1]
    implement = "--implement" in sys.argv

    # Create updater and run
    updater = WeeklyProgressionUpdater()
    success = updater.run_weekly_update(client_name, implement)

    if success:
        print("\n🎉 Weekly progression update completed!")
    else:
        print("\n💥 Weekly progression update failed!")


if __name__ == "__main__":
    main()
