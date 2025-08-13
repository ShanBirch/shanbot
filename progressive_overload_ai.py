import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import statistics
import google.generativeai as genai
from pb import TrainerizeAutomation
import sqlite3
import time

# Configure Gemini AI
genai.configure(api_key="AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k")


@dataclass
class WorkoutSet:
    weight: float
    reps: int
    rpe: Optional[int] = None  # Rate of Perceived Exertion (1-10)
    completed: bool = True


@dataclass
class ExercisePerformance:
    exercise_name: str
    sets: List[WorkoutSet]
    date: datetime
    workout_type: str
    total_volume: float = 0

    def __post_init__(self):
        self.total_volume = sum(
            s.weight * s.reps for s in self.sets if s.completed)


@dataclass
class ProgressionDecision:
    exercise_name: str
    current_weight: float
    recommended_weight: float
    current_reps: str
    recommended_reps: str
    reason: str
    confidence: float  # 0-1
    action_type: str  # "increase", "maintain", "decrease", "deload"


class ProgressiveOverloadAI:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.analytics_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        self.progression_history_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\progression_history.json"
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.db_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

    def load_client_workout_data_from_sqlite(self, client_name: str, weeks_back: int = 4) -> List[ExercisePerformance]:
        """Load workout data directly from SQLite database"""
        try:
            workout_data = []
            cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert client name to the format used in client_name_key
            client_key = client_name.lower().replace(' ', '_')

            # Query workout sessions for this client
            cursor.execute("""
                SELECT workout_date, workout_name, exercises_json 
                FROM client_workout_sessions 
                WHERE client_name_key = ? OR client_name_key LIKE ?
                ORDER BY workout_date DESC
            """, (client_key, f"%{client_key.split('_')[0]}%"))

            sessions = cursor.fetchall()
            self.logger.info(
                f"Found {len(sessions)} workout sessions for {client_name}")

            for workout_date_str, workout_name, exercises_json in sessions:
                try:
                    # Parse workout date
                    workout_date = datetime.strptime(
                        workout_date_str, '%Y-%m-%d')

                    # Skip if outside date range
                    if workout_date < cutoff_date:
                        continue

                    # Parse exercises JSON
                    exercises = json.loads(exercises_json)

                    # Convert to ExercisePerformance objects
                    for exercise_data in exercises:
                        if not isinstance(exercise_data, dict):
                            continue

                        exercise_name = exercise_data.get('name', 'Unknown')
                        sets_data = exercise_data.get('sets', [])

                        if not isinstance(sets_data, list):
                            continue

                        sets = []
                        for set_data in sets_data:
                            if not isinstance(set_data, dict):
                                continue

                            try:
                                weight = float(set_data.get('weight', 0))
                                reps = int(set_data.get('reps', 0))

                                if weight > 0 and reps > 0:
                                    sets.append(WorkoutSet(
                                        weight=weight,
                                        reps=reps,
                                        completed=True
                                    ))
                            except (ValueError, TypeError):
                                continue

                        if sets:
                            performance = ExercisePerformance(
                                exercise_name=exercise_name,
                                sets=sets,
                                date=workout_date,
                                workout_type=workout_name
                            )
                            workout_data.append(performance)

                except Exception as e:
                    self.logger.warning(f"Error parsing workout session: {e}")
                    continue

            conn.close()
            self.logger.info(
                f"Loaded {len(workout_data)} exercise performances from SQLite for {client_name}")
            return workout_data

        except Exception as e:
            self.logger.error(
                f"Error loading workout data from SQLite for {client_name}: {e}")
            return []

    def load_client_workout_data(self, client_name: str, weeks_back: int = 4) -> List[ExercisePerformance]:
        """Extract workout data from analytics for the specified client"""
        try:
            # First try to load from SQLite database
            workout_data = self.load_client_workout_data_from_sqlite(
                client_name, weeks_back)
            if workout_data:
                return workout_data

            # Fallback to JSON analytics file
            with open(self.analytics_path, 'r', encoding='utf-8') as f:
                analytics_data = json.load(f)

            workout_data = []
            cutoff_date = datetime.now() - timedelta(weeks=weeks_back)

            # Find client in analytics
            for uid, user_data in analytics_data.get("conversations", {}).items():
                metrics = user_data.get("metrics", {})
                if metrics.get("ig_username", "").lower() == client_name.lower():

                    # Extract workout sessions from weekly summaries or workout logs
                    workout_sessions = self._extract_workout_sessions(
                        user_data)

                    for session in workout_sessions:
                        if session['date'] >= cutoff_date:
                            performance = self._parse_workout_session(session)
                            if performance:
                                workout_data.extend(performance)

            self.logger.info(
                f"Loaded {len(workout_data)} exercise performances for {client_name}")
            return workout_data

        except Exception as e:
            self.logger.error(
                f"Error loading workout data for {client_name}: {e}")
            return []

    def _extract_workout_sessions(self, user_data: dict) -> List[dict]:
        """Extract workout sessions from user analytics data"""
        sessions = []

        # Look for workout data in various places in the analytics
        weekly_summaries = user_data.get("weekly_summaries", None)
        workout_logs = user_data.get("workout_logs", None)

        # Process weekly summaries if available and is a dictionary
        if isinstance(weekly_summaries, dict):
            for week_key, week_data in weekly_summaries.items():
                # Explicitly check if week_data is a dictionary
                if not isinstance(week_data, dict):
                    self.logger.warning(
                        f"Expected dictionary for week_data in weekly_summaries for key {week_key}, got {type(week_data)}. Skipping.")
                    continue

                # Check if week_data has 'workouts' key and if it's iterable (should be a list)
                if "workouts" in week_data:
                    workouts_list_in_week = week_data["workouts"]
                    if isinstance(workouts_list_in_week, list):
                        for workout in workouts_list_in_week:
                            # Explicitly check if workout is a dictionary
                            if isinstance(workout, dict):
                                date_str = workout.get("date", "2024-01-01")
                                try:
                                    workout_date = datetime.strptime(
                                        date_str, "%Y-%m-%d")
                                except ValueError:
                                    self.logger.warning(
                                        f"Invalid date format in weekly summary workout: {date_str}. Defaulting to 2024-01-01.")
                                    workout_date = datetime.strptime(
                                        "2024-01-01", "%Y-%m-%d")  # Default date

                                # Ensure exercises is a list, default to empty list
                                exercises_list = workout.get("exercises", [])
                                if not isinstance(exercises_list, list):
                                    self.logger.warning(
                                        f"Expected list for exercises in weekly summary workout, got {type(exercises_list)}. Defaulting to empty list.")
                                    exercises_list = []  # Use empty list if not a list

                                sessions.append({
                                    "date": workout_date,
                                    "workout_type": workout.get("type", "Unknown"),
                                    "exercises": exercises_list
                                })
                            else:
                                self.logger.warning(
                                    f"Expected dictionary for workout in weekly summary, got {type(workout)}. Skipping workout.")
                    else:
                        self.logger.warning(
                            f"Expected list for workouts in weekly summary for key {week_key}, got {type(workouts_list_in_week)}. Skipping weekly summary entry.")

        # Process direct workout logs if available and is a list
        if isinstance(workout_logs, list):
            for workout_log in workout_logs:
                # Explicitly check if workout_log is a dictionary
                if isinstance(workout_log, dict):
                    date_str = workout_log.get("date", "2024-01-01")
                    try:
                        workout_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        self.logger.warning(
                            f"Invalid date format in workout logs: {date_str}. Defaulting to 2024-01-01.")
                        workout_date = datetime.strptime(
                            "2024-01-01", "%Y-%m-%d")  # Default date

                    # Ensure exercises is a list, default to empty list
                    exercises_list = workout_log.get("exercises", [])
                    if not isinstance(exercises_list, list):
                        self.logger.warning(
                            f"Expected list for exercises in workout logs, got {type(exercises_list)}. Defaulting to empty list.")
                        exercises_list = []  # Use empty list if not a list

                    sessions.append({
                        "date": workout_date,
                        "workout_type": workout_log.get("type", "Unknown"),
                        "exercises": exercises_list
                    })
                else:
                    self.logger.warning(
                        f"Expected dictionary for workout log, got {type(workout_log)}. Skipping workout log entry.")

        return sessions

    def _parse_workout_session(self, session: dict) -> List[ExercisePerformance]:
        """Parse a workout session into ExercisePerformance objects"""
        performances = []

        # Ensure session is a dictionary and has a 'date' key with a datetime value
        if not isinstance(session, dict) or 'date' not in session or not isinstance(session['date'], datetime):
            self.logger.warning(
                f"Invalid session data format, missing date, or invalid date type: {session}. Skipping session parsing.")
            return []

        # Ensure session.get("exercises") returns a list, default to empty list
        exercises_data = session.get("exercises", [])
        if not isinstance(exercises_data, list):
            self.logger.warning(
                f"Expected list for session exercises, got {type(exercises_data)}. Skipping session parsing.")
            return []  # Return empty list if exercises data is not a list

        for exercise_data in exercises_data:
            # Explicitly check if exercise_data is a dictionary
            if not isinstance(exercise_data, dict):
                self.logger.warning(
                    f"Expected dictionary for exercise_data, got {type(exercise_data)}. Skipping exercise.")
                continue

            exercise_name = exercise_data.get("name", "Unknown Exercise")
            # Ensure exercise_data.get("sets") returns a list, default to empty list
            sets_data = exercise_data.get("sets", [])
            if not isinstance(sets_data, list):
                self.logger.warning(
                    f"Expected list for sets_data for exercise {exercise_name}, got {type(sets_data)}. Skipping sets.")
                sets_data = []  # Use empty list if not a list

            sets = []
            # Explicitly check if set_data is a dictionary
            for set_data in sets_data:
                if isinstance(set_data, dict):
                    # Use .get() with None as default for safety before casting
                    weight_val = set_data.get("weight", None)
                    try:
                        weight = float(
                            weight_val) if weight_val is not None else 0.0
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"Invalid weight format for exercise {exercise_name}, set {set_data.get('set', 'N/A')}: {weight_val}. Defaulting to 0.0.")
                        weight = 0.0

                    reps_val = set_data.get("reps", None)
                    try:
                        reps = int(reps_val) if reps_val is not None else 0
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"Invalid reps format for exercise {exercise_name}, set {set_data.get('set', 'N/A')}: {reps_val}. Defaulting to 0.")
                        reps = 0

                    completed = set_data.get("completed", True)
                    rpe = set_data.get("rpe", None)  # RPE can be None

                    # Only add set if weight and reps are positive
                    if weight > 0 and reps > 0:
                        sets.append(WorkoutSet(weight=weight,
                                    reps=reps, rpe=rpe, completed=completed))
                else:
                    self.logger.warning(
                        f"Expected dictionary for set data for exercise {exercise_name}, got {type(set_data)}. Skipping set.")

            if sets:
                # Ensure session date exists and is a datetime object (checked at function start)
                performance = ExercisePerformance(
                    exercise_name=exercise_name,
                    sets=sets,
                    date=session["date"],
                    workout_type=session.get("workout_type", "Unknown")
                )
                performances.append(performance)

        return performances

    def analyze_progression_patterns(self, workout_data: List[ExercisePerformance]) -> Dict[str, List[ProgressionDecision]]:
        """Analyze workout data and determine optimal progressions for each exercise"""

        # Group by exercise
        exercise_groups = {}
        for performance in workout_data:
            if performance.exercise_name not in exercise_groups:
                exercise_groups[performance.exercise_name] = []
            exercise_groups[performance.exercise_name].append(performance)

        progression_decisions = {}

        for exercise_name, performances in exercise_groups.items():
            # Sort by date
            performances.sort(key=lambda x: x.date)

            if len(performances) < 2:
                continue  # Need at least 2 sessions to analyze progression

            decision = self._analyze_single_exercise_progression(
                exercise_name, performances)
            if decision:
                progression_decisions[exercise_name] = [decision]

        return progression_decisions

    def _analyze_single_exercise_progression(self, exercise_name: str, performances: List[ExercisePerformance]) -> Optional[ProgressionDecision]:
        """Analyze progression for a single exercise"""

        # Get recent performance metrics
        recent_sessions = performances[-3:]  # Last 3 sessions
        latest_session = performances[-1]

        # Calculate progression metrics
        volume_trend = self._calculate_volume_trend(performances)
        completion_rate = self._calculate_completion_rate(recent_sessions)
        intensity_trend = self._calculate_intensity_trend(performances)

        # Get current training parameters
        current_weight = self._get_typical_weight(latest_session)
        current_reps = self._get_typical_reps(latest_session)

        # Use AI to make progression decision
        decision = self._ai_progression_decision(
            exercise_name=exercise_name,
            current_weight=current_weight,
            current_reps=current_reps,
            volume_trend=volume_trend,
            completion_rate=completion_rate,
            intensity_trend=intensity_trend,
            recent_performances=recent_sessions
        )

        return decision

    def _calculate_volume_trend(self, performances: List[ExercisePerformance]) -> float:
        """Calculate volume trend over time (positive = increasing)"""
        if len(performances) < 2:
            return 0.0

        volumes = [p.total_volume for p in performances]

        # Simple linear trend calculation
        x_values = list(range(len(volumes)))
        if len(volumes) == 1:
            return 0.0

        # Calculate slope
        n = len(volumes)
        sum_x = sum(x_values)
        sum_y = sum(volumes)
        sum_xy = sum(x * y for x, y in zip(x_values, volumes))
        sum_x2 = sum(x * x for x in x_values)

        if (n * sum_x2 - sum_x * sum_x) == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope

    def _calculate_completion_rate(self, performances: List[ExercisePerformance]) -> float:
        """Calculate percentage of sets completed successfully"""
        total_sets = 0
        completed_sets = 0

        for performance in performances:
            for workout_set in performance.sets:
                total_sets += 1
                if workout_set.completed:
                    completed_sets += 1

        return completed_sets / total_sets if total_sets > 0 else 0.0

    def _calculate_intensity_trend(self, performances: List[ExercisePerformance]) -> float:
        """Calculate trend in training intensity (weight used)"""
        if len(performances) < 2:
            return 0.0

        # Get average weight per session
        avg_weights = []
        for performance in performances:
            weights = [
                s.weight for s in performance.sets if s.completed and s.weight > 0]
            if weights:
                avg_weights.append(sum(weights) / len(weights))

        if len(avg_weights) < 2:
            return 0.0

        # Calculate trend
        recent_avg = statistics.mean(avg_weights[-2:])
        earlier_avg = statistics.mean(
            avg_weights[:-2]) if len(avg_weights) > 2 else avg_weights[0]

        return (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0.0

    def _get_typical_weight(self, performance: ExercisePerformance) -> float:
        """Get the typical weight used in latest session"""
        weights = [
            s.weight for s in performance.sets if s.completed and s.weight > 0]
        return statistics.mode(weights) if weights else 0.0

    def _get_typical_reps(self, performance: ExercisePerformance) -> str:
        """Get the typical rep count used in latest session - always returns a specific number"""
        reps = [s.reps for s in performance.sets if s.completed and s.reps > 0]
        if not reps:
            return "10"

        # Use the most common rep count (mode), fallback to average
        try:
            most_common_reps = statistics.mode(reps)
            return str(most_common_reps)
        except statistics.StatisticsError:
            # If no mode exists, use average rounded to nearest whole number
            avg_reps = round(sum(reps) / len(reps))
            return str(avg_reps)

    def _ai_progression_decision(self, exercise_name: str, current_weight: float, current_reps: str,
                                 volume_trend: float, completion_rate: float, intensity_trend: float,
                                 recent_performances: List[ExercisePerformance]) -> ProgressionDecision:
        """Use AI to make intelligent progression decisions based on rep progression
        (customized: only increase reps OR weight, never both; use gym increments)"""

        # Helper for dumbbell increments
        def get_next_dumbbell_weight(current_weight):
            dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15, 17.5,
                                20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
            for w in dumbbell_weights:
                if w > current_weight:
                    return w
            return current_weight  # maxed out

        def get_next_weight(current_weight, equipment_type):
            if equipment_type == 'dumbbell':
                return get_next_dumbbell_weight(current_weight)
            else:  # barbell or machine
                return current_weight + 2.5

        # Determine equipment type
        exercise_lower = exercise_name.lower()
        if any(word in exercise_lower for word in ['dumbbell', 'db', 'alternating']):
            equipment_type = 'dumbbell'
        elif any(word in exercise_lower for word in ['barbell', 'bb', 'bench press', 'squat', 'deadlift']):
            equipment_type = 'barbell'
        elif any(word in exercise_lower for word in ['machine', 'cable', 'lat pull', 'seated', 'leg press']):
            equipment_type = 'machine'
        else:
            equipment_type = 'barbell'  # fallback

        # Get the most recent performance
        latest_performance = recent_performances[-1]
        completed_reps = [
            s.reps for s in latest_performance.sets if s.completed and s.reps > 0]
        sets_completed = sum(1 for s in latest_performance.sets if s.completed)
        total_sets = len(latest_performance.sets)

        # If no completed reps, maintain
        if not completed_reps or sets_completed < total_sets:
            return ProgressionDecision(
                exercise_name=exercise_name,
                current_weight=current_weight,
                recommended_weight=current_weight,
                current_reps=current_reps,
                recommended_reps=current_reps,
                reason="Not all sets completed. Maintaining weight and reps.",
                confidence=0.7,
                action_type="maintain"
            )

        # Use the minimum reps achieved across all sets (to be practical but still challenging)
        min_reps_achieved = min(completed_reps)
        current_target_reps = int(
            current_reps) if current_reps.isdigit() else 6

        # Progress if they're close to target (within 1-2 reps) or exceeded it
        # This makes progression more practical - if they hit 7 when target was 8, still progress
        if min_reps_achieved >= (current_target_reps - 1):
            if current_target_reps < 15:
                # If they hit exactly the target or more, increase by 2
                # If they're 1 rep below target, only increase by 1
                if min_reps_achieved >= current_target_reps:
                    next_reps = min(current_target_reps + 2, 15)
                else:
                    # They're 1 rep below target, so just go to the next single increment
                    next_reps = min(current_target_reps + 1, 15)

                return ProgressionDecision(
                    exercise_name=exercise_name,
                    current_weight=current_weight,
                    recommended_weight=current_weight,
                    current_reps=str(current_target_reps),
                    recommended_reps=str(next_reps),
                    reason=f"Achieved {min_reps_achieved} reps (target: {current_target_reps}). Progressing to {next_reps} reps.",
                    confidence=0.9,
                    action_type="increase_reps"
                )
            else:
                # At 15 reps, increase weight (using correct increment), reset reps to 6
                next_weight = get_next_weight(current_weight, equipment_type)
                return ProgressionDecision(
                    exercise_name=exercise_name,
                    current_weight=current_weight,
                    recommended_weight=next_weight,
                    current_reps=str(current_target_reps),
                    recommended_reps="6",
                    reason=f"Achieved {min_reps_achieved} reps at 15 target. Increasing weight to {next_weight}kg and resetting to 6 reps.",
                    confidence=0.95,
                    action_type="increase_weight"
                )
        else:
            # More than 1 rep below target, maintain current level
            return ProgressionDecision(
                exercise_name=exercise_name,
                current_weight=current_weight,
                recommended_weight=current_weight,
                current_reps=str(current_target_reps),
                recommended_reps=str(current_target_reps),
                reason=f"Achieved {min_reps_achieved} reps (target: {current_target_reps}). Need to be within 1 rep to progress.",
                confidence=0.7,
                action_type="maintain"
            )

    def implement_progressions(self, client_name: str, progressions: Dict[str, List[ProgressionDecision]]) -> bool:
        """Automatically implement progression decisions in Trainerize using smart exercise-to-workout mapping"""

        try:
            # Import pb.py here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from pb import TrainerizeAutomation

            trainerize = TrainerizeAutomation()

            # Login credentials
            username = "Shannonbirch@cocospersonaltraining.com"
            password = "cyywp7nyk2"

            if not trainerize.login(username, password):
                self.logger.error("Failed to login to Trainerize")
                return False

            time.sleep(2)
            trainerize.handle_notification_popup()

            if not trainerize.navigate_to_client(client_name):
                self.logger.error(
                    f"Failed to navigate to client: {client_name}")
                return False

            if not trainerize.navigate_to_training_program():
                self.logger.error("Failed to navigate to training program")
                return False

            # Find current program
            current_program = trainerize.find_current_workout_program()
            if not current_program:
                self.logger.error("Could not find current workout program")
                return False

            self.logger.info(f"Found program: {current_program}")

            # SMART APPROACH: Create exercise-to-workout mapping from actual data
            self.logger.info(
                "Creating exercise-to-workout mapping from client data...")

            # Load client's workout data to map exercises to workouts
            workout_data = self.load_client_workout_data(client_name)
            exercise_workout_map = {}

            for performance in workout_data:
                exercise_name = performance.exercise_name
                workout_type = performance.workout_type
                if exercise_name not in exercise_workout_map:
                    exercise_workout_map[exercise_name] = workout_type
                    self.logger.info(f"  {exercise_name} → {workout_type}")

            # Group progressions by workout for efficient updates
            workout_progressions = {}
            for exercise_name, decisions in progressions.items():
                workout_name = exercise_workout_map.get(exercise_name)

                if workout_name:
                    if workout_name not in workout_progressions:
                        workout_progressions[workout_name] = []
                    workout_progressions[workout_name].append(
                        (exercise_name, decisions[0]))
                    self.logger.info(
                        f"✅ Will update {exercise_name} in workout '{workout_name}'")
                else:
                    self.logger.warning(
                        f"⚠️  No workout mapping found for {exercise_name}")

            self.logger.info(f"\n📊 UPDATE PLAN:")
            for workout_name, exercises in workout_progressions.items():
                self.logger.info(
                    f"  {workout_name}: {len(exercises)} exercises")

            # Process each workout systematically
            success_count = 0
            total_count = len(progressions)

            for workout_name, exercise_progressions in workout_progressions.items():
                self.logger.info(f"\n🏋️  Processing workout: {workout_name}")

                try:
                    # Navigate to this specific workout
                    if trainerize.find_and_click_workout_by_name(workout_name):
                        self.logger.info(f"✅ Opened workout: {workout_name}")

                        # Enter edit mode for this workout
                        if trainerize.click_edit_workout():
                            self.logger.info(
                                f"✅ Entered edit mode for {workout_name}")

                            # Update all exercises in this workout
                            workout_success_count = 0
                            for exercise_name, decision in exercise_progressions:
                                self.logger.info(
                                    f"  Updating {exercise_name}:")
                                self.logger.info(
                                    f"    Current: W({decision.current_weight}), R({decision.current_reps})")
                                self.logger.info(
                                    f"    New: W({decision.recommended_weight}), R({decision.recommended_reps})")

                                # Update the exercise goals
                                if trainerize.modify_exercise_goals(
                                    exercise_name,
                                    decision.recommended_weight,
                                    decision.recommended_reps
                                ):
                                    self.logger.info(
                                        f"  ✅ Updated {exercise_name}")
                                    workout_success_count += 1
                                    success_count += 1
                                else:
                                    self.logger.error(
                                        f"  ❌ Failed to update {exercise_name}")

                            # Save the workout with all changes
                            if workout_success_count > 0:
                                if trainerize.save_workout():
                                    self.logger.info(
                                        f"✅ Saved workout '{workout_name}' with {workout_success_count} updates")
                                else:
                                    self.logger.error(
                                        f"❌ Failed to save workout '{workout_name}'")
                                    success_count -= workout_success_count  # Rollback success count

                            # Navigate back to program view for next workout
                            trainerize.navigate_to_training_program()
                            time.sleep(2)  # Allow page to load

                        else:
                            self.logger.error(
                                f"❌ Failed to enter edit mode for {workout_name}")
                    else:
                        self.logger.error(
                            f"❌ Could not find workout: {workout_name}")

                except Exception as e:
                    self.logger.error(
                        f"❌ Error processing workout {workout_name}: {e}")
                    try:
                        trainerize.navigate_to_training_program()
                    except:
                        pass
                    continue

            self.logger.info(f"\n🎯 IMPLEMENTATION COMPLETE:")
            self.logger.info(
                f"   ✅ {success_count}/{total_count} exercises updated")
            self.logger.info(
                f"   📊 {len(workout_progressions)} workouts processed")

            return success_count > 0

        except Exception as e:
            self.logger.error(f"Error implementing progressions: {e}")
            return False
        finally:
            if 'trainerize' in locals():
                trainerize.cleanup()

    def calculate_rep_based_progression(self, exercise_name: str, recent_performances: List[ExercisePerformance]) -> ProgressionDecision:
        """Calculate progression using rep-based logic:
        - If client achieves target reps, increase by 2 reps
        - If they hit 15 reps, add 2.5kg and reset to 6 reps
        """

        if not recent_performances:
            return ProgressionDecision(
                exercise_name=exercise_name,
                current_weight=0,
                recommended_weight=0,
                current_reps="8",
                recommended_reps="8",
                reason="No recent performance data available",
                confidence=0.0,
                action_type="maintain"
            )

        # Get the most recent performance
        latest_performance = recent_performances[-1]

        # Get current weight and reps from the latest performance
        current_weights = [
            s.weight for s in latest_performance.sets if s.completed]
        current_weight = max(current_weights) if current_weights else 0

        # Get the actual reps achieved in the last session
        achieved_reps = [
            s.reps for s in latest_performance.sets if s.completed]
        max_achieved_reps = max(achieved_reps) if achieved_reps else 0
        avg_achieved_reps = sum(achieved_reps) / \
            len(achieved_reps) if achieved_reps else 0

        # Get target reps (assume it's in the current_reps field or default to 8)
        try:
            # Try to extract target from current reps if it's in "Goals: W(x), R(y)" format
            current_reps_str = latest_performance.sets[0].reps if latest_performance.sets else "8"
            if isinstance(current_reps_str, str) and "R(" in current_reps_str:
                import re
                match = re.search(r'R\((\d+)\)', current_reps_str)
                target_reps = int(match.group(1)) if match else 8
            else:
                target_reps = int(current_reps_str) if str(
                    current_reps_str).isdigit() else 8
        except:
            target_reps = 8

        self.logger.info(
            f"{exercise_name}: Target={target_reps}, Achieved={max_achieved_reps}, Avg={avg_achieved_reps:.1f}")

        # Rep-based progression logic
        if max_achieved_reps >= 15:
            # Hit 15 reps - increase weight by 2.5kg and reset to 6 reps
            new_weight = current_weight + 2.5
            new_reps = 6
            reason = f"Hit {max_achieved_reps} reps (≥15), increasing weight by 2.5kg and resetting to 6 reps"
            action_type = "increase_weight"
            confidence = 0.9

        elif avg_achieved_reps >= target_reps:
            # Achieved target reps - increase by 2 reps
            new_weight = current_weight
            new_reps = target_reps + 2
            reason = f"Achieved target {target_reps} reps (avg: {avg_achieved_reps:.1f}), increasing target by 2"
            action_type = "increase_reps"
            confidence = 0.8

        elif avg_achieved_reps >= target_reps * 0.8:
            # Close to target (80%+) - maintain current
            new_weight = current_weight
            new_reps = target_reps
            reason = f"Close to target ({avg_achieved_reps:.1f}/{target_reps}), maintaining current goals"
            action_type = "maintain"
            confidence = 0.7

        else:
            # Struggling with current weight - reduce by 2.5kg
            new_weight = max(current_weight - 2.5, 2.5)  # Don't go below 2.5kg
            new_reps = target_reps
            reason = f"Struggling with current weight ({avg_achieved_reps:.1f}/{target_reps}), reducing weight by 2.5kg"
            action_type = "decrease_weight"
            confidence = 0.8

        return ProgressionDecision(
            exercise_name=exercise_name,
            current_weight=current_weight,
            recommended_weight=new_weight,
            current_reps=str(target_reps),
            recommended_reps=str(new_reps),
            reason=reason,
            confidence=confidence,
            action_type=action_type
        )

    def analyze_progression_patterns_rep_based(self, workout_data: List[ExercisePerformance]) -> Dict[str, List[ProgressionDecision]]:
        """Analyze progression patterns using rep-based logic"""

        if not workout_data:
            self.logger.warning("No workout data provided for analysis")
            return {}

        # Group exercises by name
        exercise_groups = {}
        for performance in workout_data:
            exercise_name = performance.exercise_name
            if exercise_name not in exercise_groups:
                exercise_groups[exercise_name] = []
            exercise_groups[exercise_name].append(performance)

        # Sort each group by date
        for exercise_name in exercise_groups:
            exercise_groups[exercise_name].sort(key=lambda x: x.date)

        progressions = {}

        for exercise_name, performances in exercise_groups.items():
            # Use rep-based progression logic
            decision = self.calculate_rep_based_progression(
                exercise_name, performances)
            progressions[exercise_name] = [decision]

            self.logger.info(
                f"Progression for {exercise_name}: {decision.action_type} - {decision.reason}")

        return progressions

    def save_progression_history(self, client_name: str, progressions: Dict[str, List[ProgressionDecision]]):
        """Save progression decisions to history file"""
        try:
            # Load existing history
            try:
                with open(self.progression_history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = {}

            # Add new progressions
            if client_name not in history:
                history[client_name] = []

            entry = {
                "date": datetime.now().isoformat(),
                "progressions": {}
            }

            for exercise_name, decisions in progressions.items():
                entry["progressions"][exercise_name] = {
                    "current_weight": decisions[0].current_weight,
                    "recommended_weight": decisions[0].recommended_weight,
                    "current_reps": decisions[0].current_reps,
                    "recommended_reps": decisions[0].recommended_reps,
                    "reason": decisions[0].reason,
                    "confidence": decisions[0].confidence,
                    "action_type": decisions[0].action_type
                }

            history[client_name].append(entry)

            # Save updated history
            with open(self.progression_history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)

            self.logger.info(f"Saved progression history for {client_name}")

        except Exception as e:
            self.logger.error(f"Error saving progression history: {e}")

    def generate_progression_report(self, client_name: str, progressions: Dict[str, List[ProgressionDecision]]) -> str:
        """Generate a human-readable report of progression decisions"""

        report = f"# Progressive Overload Report for {client_name}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        if not progressions:
            report += "No progression decisions made - insufficient workout data.\n"
            return report

        report += "## Progression Decisions\n\n"

        for exercise_name, decisions in progressions.items():
            decision = decisions[0]  # Take first decision

            report += f"### {exercise_name}\n"
            report += f"**Action:** {decision.action_type.title()}\n"
            report += f"**Weight:** {decision.current_weight}kg → {decision.recommended_weight}kg\n"
            report += f"**Reps:** {decision.current_reps} → {decision.recommended_reps}\n"
            report += f"**Confidence:** {decision.confidence:.1%}\n"
            report += f"**Reasoning:** {decision.reason}\n\n"

        # Summary statistics
        action_counts = {}
        total_confidence = 0

        for decisions in progressions.values():
            action = decisions[0].action_type
            action_counts[action] = action_counts.get(action, 0) + 1
            total_confidence += decisions[0].confidence

        avg_confidence = total_confidence / len(progressions)

        report += "## Summary\n"
        report += f"- Total exercises analyzed: {len(progressions)}\n"
        report += f"- Average confidence: {avg_confidence:.1%}\n"

        for action, count in action_counts.items():
            report += f"- {action.title()}: {count} exercises\n"

        return report

    def get_realistic_weight_increment(self, exercise_name: str, current_weight: float) -> float:
        """Determine realistic weight increment based on exercise type and current weight"""
        exercise_lower = exercise_name.lower()

        # Dumbbell exercises - typically 2.5kg or 5kg increments
        if any(word in exercise_lower for word in ['dumbbell', 'db', 'alternating']):
            if current_weight < 15:
                return 2.5  # Smaller increments for lighter weights
            else:
                return 5.0  # Standard dumbbell increment

        # Barbell exercises - typically 2.5kg total (1.25kg per side) or 5kg total
        elif any(word in exercise_lower for word in ['barbell', 'bb', 'bench press', 'squat', 'deadlift']):
            if current_weight < 60:
                return 2.5  # Smaller increments for lighter barbells
            else:
                return 5.0  # Standard barbell increment

        # Machine exercises - typically 5kg or 10kg increments
        elif any(word in exercise_lower for word in ['machine', 'cable', 'lat pull', 'seated', 'leg press']):
            if current_weight < 30:
                return 5.0   # Smaller machine increments
            else:
                return 10.0  # Standard machine increment

        # Bodyweight exercises or assisted exercises
        elif any(word in exercise_lower for word in ['bodyweight', 'assisted', 'chin up', 'pull up', 'push up']):
            return 2.5  # Small weight addition for bodyweight progressions

        # Default case - assume dumbbell-like progression
        else:
            if current_weight < 20:
                return 2.5
            else:
                return 5.0

    def calculate_progression(self, exercise_name: str, recent_performances: List[ExercisePerformance]) -> ProgressionDecision:
        """Calculate smart progression with realistic weight increments"""

        if not recent_performances:
            return ProgressionDecision(
                exercise_name=exercise_name,
                action="maintain",
                reasoning="No recent performance data available"
            )

        # Get last 3 performances for trend analysis
        last_performance = recent_performances[-1]
        trend_performances = recent_performances[-3:] if len(
            recent_performances) >= 3 else recent_performances

        # Calculate completion rates
        total_sets = sum(len(p.sets) for p in trend_performances)
        completed_sets = sum(len([s for s in p.sets if s.completed])
                             for p in trend_performances)
        completion_rate = completed_sets / total_sets if total_sets > 0 else 0

        # Get current weight (from most recent performance)
        current_weights = [
            s.weight for s in last_performance.sets if s.completed]
        current_weight = max(current_weights) if current_weights else 0

        # Get realistic increment for this exercise
        weight_increment = self.get_realistic_weight_increment(
            exercise_name, current_weight)

        # Progressive overload logic with realistic increments
        if completion_rate >= 0.9:  # 90%+ completion rate
            return ProgressionDecision(
                exercise_name=exercise_name,
                action="increase_weight",
                new_weight=current_weight + weight_increment,
                reasoning=f"Excellent completion rate ({completion_rate:.1%}). Increasing weight by {weight_increment}kg."
            )

        elif completion_rate >= 0.7:  # 70-89% completion rate
            # Check if they're hitting target reps consistently
            target_reps = trend_performances[-1].sets[0].reps if trend_performances[-1].sets else 8
            recent_reps = [s.reps for p in trend_performances[-2:]
                           for s in p.sets if s.completed]
            avg_reps = sum(recent_reps) / \
                len(recent_reps) if recent_reps else 0

            if avg_reps >= target_reps * 0.9:  # Getting close to target reps
                return ProgressionDecision(
                    exercise_name=exercise_name,
                    action="increase_reps",
                    new_reps=target_reps + 1,
                    reasoning=f"Good completion rate ({completion_rate:.1%}) and hitting reps. Adding 1 rep before weight increase."
                )
            else:
                return ProgressionDecision(
                    exercise_name=exercise_name,
                    action="maintain",
                    reasoning=f"Moderate completion rate ({completion_rate:.1%}). Maintain current load."
                )

        elif completion_rate >= 0.5:  # 50-69% completion rate
            return ProgressionDecision(
                exercise_name=exercise_name,
                action="decrease_weight",
                # Don't go below one increment
                new_weight=max(current_weight -
                               weight_increment, weight_increment),
                reasoning=f"Low completion rate ({completion_rate:.1%}). Decreasing weight by {weight_increment}kg for better form."
            )

        else:  # Below 50% completion rate
            return ProgressionDecision(
                exercise_name=exercise_name,
                action="decrease_weight",
                new_weight=max(current_weight - (weight_increment * 2),
                               weight_increment),  # Bigger decrease
                reasoning=f"Very low completion rate ({completion_rate:.1%}). Reducing weight significantly for proper form."
            )


def main():
    """Example usage of the Progressive Overload AI system with rep-based logic"""

    ai = ProgressiveOverloadAI()

    # Example client
    client_name = "Shannon Birch"  # Replace with actual client name

    print(f"🏋️ Analyzing rep-based progression for {client_name}...")

    # Load workout data
    workout_data = ai.load_client_workout_data(client_name, weeks_back=4)

    if not workout_data:
        print(
            "❌ No workout data found. Make sure client has logged workouts in the system.")
        return

    print(f"✅ Loaded {len(workout_data)} exercise performances")

    # Analyze progressions using rep-based logic
    progressions = ai.analyze_progression_patterns_rep_based(workout_data)

    if not progressions:
        print("❌ Could not generate progression recommendations.")
        return

    print(
        f"🧠 Generated rep-based progressions for {len(progressions)} exercises")

    # Generate report
    report = ai.generate_progression_report(client_name, progressions)
    print("\n" + "="*60)
    print(report)
    print("="*60)

    # Save progression history
    ai.save_progression_history(client_name, progressions)

    # Ask if user wants to implement changes
    implement = input(
        "\n🤖 Do you want to implement these changes in Trainerize? (y/n): ").lower().strip()

    if implement == 'y' or implement == 'yes':
        print("🚀 Implementing progressions in Trainerize...")
        print("This will:")
        print("  1. Login to Trainerize")
        print("  2. Navigate to the client's program")
        print("  3. Find each exercise across different workouts")
        print("  4. Update goals in format: Goals: W(weight), R(reps)")
        print("  5. Save changes")

        confirm = input("\nContinue? (y/n): ").lower().strip()
        if confirm == 'y' or confirm == 'yes':
            success = ai.implement_progressions(client_name, progressions)
            if success:
                print("✅ Successfully implemented progressions!")
            else:
                print("❌ Failed to implement some or all progressions.")
        else:
            print("❌ Implementation cancelled by user.")
    else:
        print("📋 Progressions saved to history only. Use option 1 to implement later.")

    print("\n🎯 Rep-based progression logic:")
    print("  • If client hits 15+ reps: +2.5kg weight, reset to 6 reps")
    print("  • If client achieves target reps: +2 reps")
    print("  • If client is close (80%+): maintain current")
    print("  • If struggling: -2.5kg weight")


if __name__ == "__main__":
    main()
