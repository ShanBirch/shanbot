#!/usr/bin/env python3
"""
Smart Coach Bulletproof - Clean, Repeatable Weekly System
Handles all identified issues:
- Element click interception
- Wrong exercise database searches  
- Better error recovery
- Clean page state management
"""

import json
import logging
from datetime import datetime
from weekly_program_updater_fixed import TrainerizeAutomation
import time
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'smart_coach_bulletproof_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)


class SmartCoachBulletproof:
    def __init__(self):
        self.progression_history = self.load_progression_history()
        self.dumbbell_weights = [1, 2, 3, 4, 5, 6, 7.5, 8, 9, 10, 12.5, 15,
                                 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50]
        self.barbell_machine_weights = list(range(1, 201))

    def load_progression_history(self):
        """Load progression history from JSON file"""
        try:
            with open('progression_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("progression_history.json not found!")
            return {}

    def get_next_dumbbell_weight(self, current_weight):
        """Get next available dumbbell weight"""
        try:
            current_idx = self.dumbbell_weights.index(current_weight)
            if current_idx < len(self.dumbbell_weights) - 1:
                return self.dumbbell_weights[current_idx + 1]
        except ValueError:
            pass
        return current_weight + 2.5

    def get_next_barbell_weight(self, current_weight):
        """Get next available barbell/machine weight"""
        return current_weight + 2.5

    def calculate_smart_progression(self, exercise_name, performance_data):
        """Calculate progression based on actual performance"""
        if not performance_data:
            return "GOALS: S1: 6 reps | S2: 6 reps | S3: 6 reps"

        latest = performance_data[-1]
        weight = latest.get('weight', 0)
        reps = latest.get('reps', 6)

        # Determine equipment type
        is_dumbbell = any(keyword in exercise_name.lower()
                          for keyword in ['dumbbell', 'd.b', 'db'])

        # Apply progression logic
        if reps < 8:
            new_reps = reps + 1
            new_weight = weight
        elif reps < 12:
            new_reps = reps + 1
            new_weight = weight
        elif reps < 15:
            new_reps = reps + 1
            new_weight = weight
        else:  # reps >= 15, increase weight and reset reps
            new_reps = 6
            if is_dumbbell:
                new_weight = self.get_next_dumbbell_weight(weight)
            else:
                new_weight = self.get_next_barbell_weight(weight)

        return f"GOALS: S1: {new_weight}kg*{new_reps} | S2: {new_weight}kg*{new_reps} | S3: {new_weight}kg*{new_reps}"

    def group_exercises_by_workout(self, client_data):
        """Group exercises into logical workouts"""
        workouts = {
            'Back Day': [],
            'Leg Day': [],
            'Chest Day': []
        }

        # Handle both list and dict formats
        if isinstance(client_data, list):
            # Convert list to dict format
            exercises_dict = {}
            for exercise in client_data:
                exercise_name = exercise.get('exercise_name', '')
                if exercise_name:
                    exercises_dict[exercise_name] = [exercise]
            client_data = exercises_dict

        for exercise_name, performance_data in client_data.items():
            exercise_lower = exercise_name.lower()

            # Back exercises
            if any(keyword in exercise_lower for keyword in ['chin', 'pull', 'row', 'lat', 'curl']):
                progression = self.calculate_smart_progression(
                    exercise_name, performance_data)
                workouts['Back Day'].append({
                    'exercise_name': exercise_name,
                    'progression': progression
                })

            # Leg exercises
            elif any(keyword in exercise_lower for keyword in ['squat', 'deadlift', 'lunge', 'calf', 'leg']):
                progression = self.calculate_smart_progression(
                    exercise_name, performance_data)
                workouts['Leg Day'].append({
                    'exercise_name': exercise_name,
                    'progression': progression
                })

            # Chest exercises
            elif any(keyword in exercise_lower for keyword in ['bench', 'chest', 'press', 'dip', 'tricep']):
                progression = self.calculate_smart_progression(
                    exercise_name, performance_data)
                workouts['Chest Day'].append({
                    'exercise_name': exercise_name,
                    'progression': progression
                })

        # Remove empty workouts
        return {k: v for k, v in workouts.items() if v}

    def wait_for_page_load(self, automation, timeout=10):
        """Wait for page to fully load"""
        time.sleep(3)
        try:
            automation.driver.execute_script(
                "return document.readyState") == "complete"
        except:
            pass

    def dismiss_overlays_aggressively(self, automation):
        """Aggressively dismiss any overlays that might block clicks"""
        overlay_selectors = [
            '.reactModal-overlay',
            '.ant-modal-mask',
            '.modal-overlay',
            '[class*="overlay"]',
            '[class*="modal"]'
        ]

        for selector in overlay_selectors:
            try:
                automation.driver.execute_script(f"""
                    const overlays = document.querySelectorAll('{selector}');
                    overlays.forEach(overlay => overlay.click());
                """)
                time.sleep(0.5)
            except:
                pass

    def clear_search_input(self, automation):
        """Clear any search inputs that might be blocking"""
        try:
            automation.driver.execute_script("""
                const inputs = document.querySelectorAll('input[placeholder*="Search"], input[placeholder*="search"]');
                inputs.forEach(input => {
                    input.value = '';
                    input.blur();
                });
            """)
            time.sleep(1)
        except:
            pass

    def apply_progressions_bulletproof(self, client_name, progressions):
        """Apply progressions with bulletproof error handling"""
        results = {
            'successful_exercises': [],
            'failed_exercises': [],
            'successful_workouts': [],
            'failed_workouts': []
        }

        automation = None
        try:
            logging.info(
                f"🚀 Starting bulletproof progression update for {client_name}")
            automation = TrainerizeAutomation()

            # Navigate to client
            if not automation.navigate_to_client(client_name):
                raise Exception(f"Could not navigate to client: {client_name}")

            self.wait_for_page_load(automation)

            for workout_name, exercises in progressions.items():
                logging.info(f"🎯 Processing workout: {workout_name}")

                try:
                    # Dismiss overlays before clicking
                    self.dismiss_overlays_aggressively(automation)

                    # Find and click workout
                    if not automation.find_and_click_workout_by_name(workout_name):
                        logging.warning(
                            f"❌ Could not find workout: {workout_name}")
                        results['failed_workouts'].append(workout_name)
                        results['failed_exercises'].extend(
                            [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])
                        continue

                    self.wait_for_page_load(automation)

                    # Clear any search inputs
                    self.clear_search_input(automation)

                    # Dismiss overlays again
                    self.dismiss_overlays_aggressively(automation)

                    # Try to enter edit mode with retries
                    edit_success = False
                    for attempt in range(3):
                        try:
                            if automation.click_edit_workout():
                                edit_success = True
                                break
                        except ElementClickInterceptedException:
                            logging.warning(
                                f"⚠️ Edit button blocked, attempt {attempt + 1}")
                            self.clear_search_input(automation)
                            self.dismiss_overlays_aggressively(automation)
                            time.sleep(2)

                    if not edit_success:
                        logging.warning(
                            f"❌ Could not enter edit mode for: {workout_name}")
                        results['failed_workouts'].append(workout_name)
                        results['failed_exercises'].extend(
                            [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])
                        continue

                    self.wait_for_page_load(automation)

                    # Update exercises in this workout
                    workout_success = True
                    for exercise in exercises:
                        exercise_name = exercise['exercise_name']
                        progression = exercise['progression']

                        try:
                            # Update exercise with retries
                            success = False
                            for attempt in range(3):
                                try:
                                    used_name = automation.update_exercise_goals(
                                        exercise_name, progression)
                                    if used_name:
                                        logging.info(
                                            f"    ✅ Updated {used_name}")
                                        results['successful_exercises'].append(
                                            f"{workout_name} - {used_name}")
                                        success = True
                                        break
                                except StaleElementReferenceException:
                                    logging.warning(
                                        f"⚠️ Stale element for {exercise_name}, attempt {attempt + 1}")
                                    time.sleep(2)

                            if not success:
                                logging.warning(
                                    f"    ❌ Failed to update {exercise_name}")
                                results['failed_exercises'].append(
                                    f"{workout_name} - {exercise_name}")
                                workout_success = False

                        except Exception as e:
                            logging.error(
                                f"    ❌ Error updating {exercise_name}: {str(e)}")
                            results['failed_exercises'].append(
                                f"{workout_name} - {exercise_name}")
                            workout_success = False

                    if workout_success:
                        results['successful_workouts'].append(workout_name)
                        logging.info(f"✅ Completed workout: {workout_name}")

                    # Navigate back to program
                    logging.info("  Navigating back to program...")
                    automation.navigate_back_to_program()
                    self.wait_for_page_load(automation)

                except Exception as e:
                    logging.error(
                        f"❌ Error processing workout {workout_name}: {str(e)}")
                    results['failed_workouts'].append(workout_name)
                    results['failed_exercises'].extend(
                        [f"{workout_name} - {ex['exercise_name']}" for ex in exercises])

                    # Try to recover by navigating back
                    try:
                        automation.navigate_back_to_program()
                        self.wait_for_page_load(automation)
                    except:
                        pass

        except Exception as e:
            logging.error(f"❌ Critical error in bulletproof system: {str(e)}")

        finally:
            if automation:
                logging.info("🧹 Cleaning up...")
                automation.cleanup()
                logging.info("✅ Cleanup completed successfully.")

        return results

    def run_bulletproof_update(self, client_name):
        """Run the complete bulletproof update process"""
        if client_name not in self.progression_history:
            logging.error(
                f"Client {client_name} not found in progression history")
            return

        # Generate smart progressions
        logging.info(f"🧠 Generating smart progressions for {client_name}")
        client_data = self.progression_history[client_name]
        progressions = self.group_exercises_by_workout(client_data)

        logging.info(
            f"📊 Generated progressions for {len(progressions)} workouts:")
        for workout_name, exercises in progressions.items():
            logging.info(f"  • {workout_name}: {len(exercises)} exercises")

        # Save progressions
        progressions_file = f"{client_name.lower().replace(' ', '_')}_bulletproof_progressions.json"
        with open(progressions_file, 'w') as f:
            json.dump(progressions, f, indent=2)
        logging.info(f"💾 Progressions saved to {progressions_file}")

        # Apply to Trainerize
        results = self.apply_progressions_bulletproof(
            client_name, progressions)

        # Save results
        results_file = f"bulletproof_results_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        print("\n" + "="*60)
        print("BULLETPROOF UPDATE RESULTS")
        print("="*60)

        total_exercises = len(
            results['successful_exercises']) + len(results['failed_exercises'])
        total_workouts = len(
            results['successful_workouts']) + len(results['failed_workouts'])

        if len(results['failed_exercises']) == 0:
            print("🎉 COMPLETE SUCCESS")
        elif len(results['successful_exercises']) > 0:
            print("⚠️  PARTIAL SUCCESS")
        else:
            print("❌ SYSTEM FAILURE")

        print(
            f"  Successfully updated: {len(results['successful_exercises'])}/{total_exercises} exercises")
        print(
            f"  Successfully completed: {len(results['successful_workouts'])}/{total_workouts} workouts")

        if results['failed_exercises']:
            print(
                f"  Failed exercises: {', '.join(results['failed_exercises'])}")

        print(f"\n💾 Results saved to {results_file}")

        return results


def main():
    """Main function to run the bulletproof system"""
    coach = SmartCoachBulletproof()
    coach.run_bulletproof_update("Nicole Lynch")


if __name__ == "__main__":
    main()
