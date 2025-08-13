import os
import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import the original TrainerizeAutomation class
from weekly_program_updater import TrainerizeAutomation as BaseTrainerizeAutomation


class DebugTrainerizeAutomation(BaseTrainerizeAutomation):
    def __init__(self):
        super().__init__()
        self.debug_mode = True
        self.screenshot_counter = 0
        self.create_debug_folder()
        self.setup_enhanced_logging()

    def create_debug_folder(self):
        """Create a debug folder with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_folder = f"debug_session_{timestamp}"
        os.makedirs(self.debug_folder, exist_ok=True)
        logging.info(f"Debug folder created: {self.debug_folder}")

    def setup_enhanced_logging(self):
        """Setup enhanced logging for debugging"""
        debug_log_file = os.path.join(self.debug_folder, "debug_log.txt")

        # Create a file handler for debug logs
        file_handler = logging.FileHandler(debug_log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger = logging.getLogger()
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)

    def take_debug_screenshot(self, description=""):
        """Take a screenshot for debugging purposes"""
        try:
            self.screenshot_counter += 1
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"screenshot_{self.screenshot_counter:03d}_{timestamp}_{description}.png"
            filepath = os.path.join(self.debug_folder, filename)

            self.driver.save_screenshot(filepath)
            logging.info(f"Debug screenshot saved: {filename}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to take screenshot: {e}")
            return None

    def wait_for_user_input(self, message=""):
        """Pause execution and wait for user input in debug mode"""
        if self.debug_mode:
            current_url = self.driver.current_url
            print(f"\n{'='*60}")
            print(f"DEBUG PAUSE: {message}")
            print(f"Current URL: {current_url}")
            print(f"Screenshot saved to: {self.debug_folder}")
            print("Options:")
            print("  [Enter] - Continue")
            print("  'c' - Continue without further pauses")
            print("  's' - Take screenshot")
            print("  'q' - Quit")
            print(f"{'='*60}")

            self.take_debug_screenshot(f"pause_{message.replace(' ', '_')}")

            user_input = input("Your choice: ").strip().lower()

            if user_input == 'c':
                self.debug_mode = False
                print("Debug mode disabled. Script will continue without pauses.")
            elif user_input == 's':
                self.take_debug_screenshot("manual_request")
                print("Screenshot taken.")
            elif user_input == 'q':
                print("User requested quit.")
                return False

        return True

    def enhanced_navigate_back_to_program(self):
        """Navigate back to the program view after editing a workout"""
        try:
            logging.info("Attempting to navigate back to program view...")
            self.take_debug_screenshot("before_navigate_back")

            # Multiple strategies to get back to program view
            navigation_strategies = [
                # Strategy 1: Click the back button if it exists
                {
                    "name": "Back Button",
                    "locator": (By.CSS_SELECTOR, "button[data-testid*='back'], button[title*='Back'], .back-button"),
                    "method": "click"
                },
                # Strategy 2: Click on the program name/breadcrumb
                {
                    "name": "Program Breadcrumb",
                    "locator": (By.XPATH, "//nav//a[contains(@href, 'program')] | //breadcrumb//a"),
                    "method": "click"
                },
                # Strategy 3: Navigate directly via URL manipulation
                {
                    "name": "URL Navigation",
                    "method": "url_navigate"
                },
                # Strategy 4: Use browser back
                {
                    "name": "Browser Back",
                    "method": "browser_back"
                }
            ]

            for strategy in navigation_strategies:
                try:
                    logging.info(
                        f"Trying navigation strategy: {strategy['name']}")

                    if strategy["method"] == "click":
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(strategy["locator"])
                        )
                        element.click()
                        time.sleep(2)

                    elif strategy["method"] == "url_navigate":
                        current_url = self.driver.current_url
                        if "/workout/" in current_url:
                            # Extract the program part of the URL
                            program_url = current_url.split("/workout/")[0]
                            logging.info(f"Navigating to: {program_url}")
                            self.driver.get(program_url)
                            time.sleep(3)

                    elif strategy["method"] == "browser_back":
                        self.driver.back()
                        time.sleep(2)

                    # Check if navigation was successful
                    current_url = self.driver.current_url
                    if "/workout/" not in current_url and ("program" in current_url.lower() or "training" in current_url.lower()):
                        logging.info(
                            f"Successfully navigated back using: {strategy['name']}")
                        self.take_debug_screenshot("successful_navigate_back")
                        return True

                except TimeoutException:
                    logging.info(
                        f"Strategy {strategy['name']} failed - element not found")
                    continue
                except Exception as e:
                    logging.warning(f"Strategy {strategy['name']} failed: {e}")
                    continue

            logging.error("All navigation strategies failed")
            self.take_debug_screenshot("navigate_back_failed")
            return False

        except Exception as e:
            logging.error(f"Error in enhanced_navigate_back_to_program: {e}")
            self.take_debug_screenshot("navigate_back_error")
            return False

    def enhanced_process_single_workout(self, workout_name, actions):
        """Enhanced version of process_single_workout with better debugging"""
        try:
            logging.info(f"=== PROCESSING WORKOUT: {workout_name} ===")
            self.take_debug_screenshot(
                f"start_workout_{workout_name.replace(' ', '_')}")

            if not self.wait_for_user_input(f"About to process workout: {workout_name}"):
                return False

            # Find and click the workout
            logging.info(
                f"Step 1: Finding and clicking workout: {workout_name}")
            if not self.find_and_click_workout_by_name(workout_name):
                logging.error(
                    f"Failed to find and click workout: {workout_name}")
                self.take_debug_screenshot(
                    f"failed_find_workout_{workout_name.replace(' ', '_')}")
                return False

            self.take_debug_screenshot(
                f"clicked_workout_{workout_name.replace(' ', '_')}")

            if not self.wait_for_user_input(f"Clicked workout {workout_name}, about to enter edit mode"):
                return False

            # Enter edit mode
            logging.info(
                f"Step 2: Entering edit mode for workout: {workout_name}")
            if not self.click_edit_workout():
                logging.error(
                    f"Failed to enter edit mode for workout: {workout_name}")
                self.take_debug_screenshot(
                    f"failed_edit_mode_{workout_name.replace(' ', '_')}")
                return False

            self.take_debug_screenshot(
                f"edit_mode_{workout_name.replace(' ', '_')}")

            if not self.wait_for_user_input(f"Entered edit mode, about to process {len(actions)} actions"):
                return False

            # Process all actions
            logging.info(f"Step 3: Processing {len(actions)} actions")
            all_actions_successful = True

            for i, action_item in enumerate(actions, 1):
                action_type = action_item.get('action')
                exercise_name = action_item.get('exercise_name')

                if not action_type or not exercise_name:
                    logging.warning(
                        f"Skipping invalid action item: {action_item}")
                    all_actions_successful = False
                    continue

                logging.info(
                    f"Action {i}/{len(actions)}: {action_type.upper()} '{exercise_name}'")
                self.take_debug_screenshot(
                    f"before_action_{i}_{action_type}_{exercise_name.replace(' ', '_')}")

                if not self.wait_for_user_input(f"About to perform action {i}: {action_type} on {exercise_name}"):
                    return False

                if action_type == "add":
                    sets = action_item.get('sets', '3')
                    reps = action_item.get('reps', '12')
                    success = self.add_exercise(exercise_name, sets, reps)

                elif action_type == "remove":
                    success = self.remove_exercise(exercise_name)

                elif action_type == "modify_goals":
                    weight = action_item.get('weight', '0')
                    reps = action_item.get('reps', '0')
                    success = self.modify_exercise_goals(
                        exercise_name, weight, reps)

                else:
                    logging.error(f"Unknown action type: {action_type}")
                    success = False

                if not success:
                    logging.error(
                        f"Failed action {i}: {action_type} '{exercise_name}'")
                    self.take_debug_screenshot(
                        f"failed_action_{i}_{action_type}_{exercise_name.replace(' ', '_')}")
                    all_actions_successful = False
                else:
                    logging.info(
                        f"Successful action {i}: {action_type} '{exercise_name}'")
                    self.take_debug_screenshot(
                        f"success_action_{i}_{action_type}_{exercise_name.replace(' ', '_')}")

            # Save the workout
            logging.info(f"Step 4: Saving workout: {workout_name}")
            if not self.wait_for_user_input(f"About to save workout {workout_name}"):
                return False

            if not self.save_workout():
                logging.error(f"Failed to save workout: {workout_name}")
                self.take_debug_screenshot(
                    f"failed_save_{workout_name.replace(' ', '_')}")
                all_actions_successful = False
            else:
                logging.info(f"Successfully saved workout: {workout_name}")
                self.take_debug_screenshot(
                    f"saved_workout_{workout_name.replace(' ', '_')}")

            # Navigate back to program view for next workout
            logging.info(f"Step 5: Navigating back to program view")
            if not self.wait_for_user_input("About to navigate back to program view"):
                return False

            if not self.enhanced_navigate_back_to_program():
                logging.error("Failed to navigate back to program view")
                self.take_debug_screenshot("failed_navigate_back_to_program")
                # Don't return False here - might still be able to continue

            self.take_debug_screenshot(
                f"completed_workout_{workout_name.replace(' ', '_')}")
            logging.info(f"=== COMPLETED WORKOUT: {workout_name} ===")

            return all_actions_successful

        except Exception as e:
            logging.error(f"Error processing workout {workout_name}: {e}")
            self.take_debug_screenshot(
                f"error_workout_{workout_name.replace(' ', '_')}")
            return False


def create_test_data():
    """Create minimal test data for debugging"""
    return {
        "Shannon Birch": {
            "Back Day": [
                {"action": "modify_goals", "exercise_name": "Lat Pulldown",
                    "weight": "30", "reps": "10"}
            ],
            "Chest Day": [
                {"action": "modify_goals", "exercise_name": "Bench Press",
                    "weight": "40", "reps": "8"}
            ]
        }
    }


def main():
    """Main function for testing"""
    print("=== WEEKLY PROGRAM UPDATER - DEBUG MODE ===")
    print("This debug version will:")
    print("1. Take screenshots at each step")
    print("2. Pause for user confirmation")
    print("3. Log everything to debug files")
    print("4. Help identify where the script gets stuck")
    print()

    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    # Use test data for debugging
    client_progression_data = create_test_data()

    trainerize_bot = DebugTrainerizeAutomation()

    try:
        print("Attempting login...")
        if trainerize_bot.login(username, password):
            print("Login successful!")
            trainerize_bot.handle_notification_popup()

            print("Starting batch processing...")
            results = trainerize_bot.process_multiple_clients(
                client_progression_data)

            # Print results
            print("\n=== DEBUG SESSION RESULTS ===")
            for client_name, client_results in results.items():
                print(f"\nClient: {client_name}")
                print(f"Status: {client_results.get('status', 'unknown')}")

                for key, value in client_results.items():
                    if key not in ['status', 'error']:
                        print(f"  {key}: {value}")

            print(f"\nDebug files saved to: {trainerize_bot.debug_folder}")

        else:
            print("Login failed!")

    except Exception as e:
        logging.error(f"Debug session error: {e}")
        print(f"Error occurred: {e}")

    finally:
        input("Press Enter to cleanup and exit...")
        trainerize_bot.cleanup()


if __name__ == "__main__":
    main()
