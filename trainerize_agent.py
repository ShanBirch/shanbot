# trainerize_agent.py
# Custom LLM-based Selenium REPL for TrainerizeAutomation
from checkin_new_1904 import TrainerizeAutomation
import os
import sys
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from openai import OpenAI
from google.auth import default
from google.auth.transport.requests import Request
import logging
import time

# Import your existing automation class
sys.path.append(os.path.dirname(__file__))

# Load Gemini API key with fallback
api_key = os.getenv(
    "OPENAI_API_KEY") or "AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y"

# Warn if no API key and set global module config
if not os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY not set, using default key from script.")
# Configure Vertex AI OpenAI-compatible endpoint
project_id = "fitness-videos-453120"  # Hardcoded project ID
location = os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"
# Use the OpenAPI endpoint for Vertex AI (v1beta1)
openai_api_base = f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi"

# Acquire OAuth2 access token using ADC
credentials, _ = default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"])
credentials.refresh(Request())
# Override api_key with the ADC token
api_key = credentials.token

# Instantiate the v1 OpenAI client for Gemini
client = OpenAI(
    api_key=api_key,
    base_url=openai_api_base,
)

# Launch Trainerize session and get driver + wait
automation = TrainerizeAutomation(openai_api_key=None)
driver = automation.driver
wait = automation.wait

# Stored Trainerize credentials (from checkin_new_1904)
USERNAME = "Shannonbirch@cocospersonaltraining.com"
PASSWORD = "cyywp7nyk2"

# --- Function definitions for the model (OpenAI function calling) ---
FUNCTION_DEFS = [
    {"name": "login", "description": "Log in to Trainerize using stored credentials",
        "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "navigate", "description": "Navigate to the given URL", "parameters": {
        "type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "click", "description": "Click an element containing the given text", "parameters": {
        "type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "type_text", "description": "Type text into an input field", "parameters": {"type": "object",
                                                                                         "properties": {"text": {"type": "string"}, "field": {"type": "string"}}, "required": ["text", "field"]}},
    {"name": "wait_for", "description": "Wait until an element containing the given text appears",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "press_space", "description": "Press the spacebar to scroll or advance",
        "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "scroll_down", "description": "Scroll down the page by a number of pixels", "parameters": {
        "type": "object", "properties": {"pixels": {"type": "integer"}}, "required": ["pixels"]}},
    {"name": "navigate_to_client", "description": "Navigate to a client's profile by name", "parameters": {
        "type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "scrape_workouts", "description": "Scrape workout data from the current client profile",
        "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "send_initial_message_to", "description": "Send the initial message to a client by name",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    # workout editing flows
    {"name": "navigate_to_training_program", "description": "Navigate to the 'Training Program' tab",
        "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "click_workout", "description": "Click on a workout by name", "parameters": {
        "type": "object", "properties": {"workout_name": {"type": "string"}}, "required": ["workout_name"]}},
    {"name": "click_edit_workout", "description": "Click the 'Edit workout' button and then select Workout Builder",
        "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "remove_exercise", "description": "Remove an exercise from the current workout by name", "parameters": {
        "type": "object", "properties": {"exercise_name": {"type": "string"}}, "required": ["exercise_name"]}},
    {"name": "add_exercise", "description": "Add an exercise to the current workout", "parameters": {"type": "object", "properties": {
        "exercise_name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}, "required": ["exercise_name", "sets", "reps"]}},
    {"name": "create_program", "description": "Create a new training program by name", "parameters": {
        "type": "object", "properties": {"program_name": {"type": "string"}}, "required": ["program_name"]}},
    {"name": "click_program", "description": "Click on a program by name", "parameters": {
        "type": "object", "properties": {"program_name": {"type": "string"}}, "required": ["program_name"]}},
    {"name": "create_workout_back_day", "description": "Create and build a 'Back and Biceps' workout in the given program", "parameters": {"type": "object", "properties": {"program_name": {"type": "string"},
                                                                                                                                                                            "exercises_list": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}}}}, "required": ["program_name", "exercises_list"]}},
    {"name": "create_workout_chest_tris_day", "description": "Create and build a 'Chest and Triceps' workout in the given program", "parameters": {"type": "object", "properties": {"program_name": {"type": "string"},
                                                                                                                                                                                    "exercises_list": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}}}}, "required": ["program_name", "exercises_list"]}},
    {"name": "create_workout_shoulders_core_day", "description": "Create and build a 'Shoulders and Core' workout in the given program", "parameters": {"type": "object", "properties": {"program_name": {"type": "string"},
                                                                                                                                                                                         "exercises_list": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}}}}, "required": ["program_name", "exercises_list"]}},
    {"name": "create_workout_leg_day", "description": "Create and build a 'Leg Day' workout in the given program", "parameters": {"type": "object", "properties": {"program_name": {"type": "string"}, "exercises_list": {
        "type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}}}}, "required": ["program_name", "exercises_list"]}},
    {"name": "create_workout_arms_core_day", "description": "Create and build an 'Arms and Core' workout in the given program", "parameters": {"type": "object", "properties": {"program_name": {"type": "string"},
                                                                                                                                                                                "exercises_list": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "sets": {"type": "string"}, "reps": {"type": "string"}}}}}, "required": ["program_name", "exercises_list"]}},
    # --- New Composite Function Definition ---
    {
        "name": "build_full_program_for_client",
        "description": "Builds a complete multi-day training program for a specified client, including navigating, creating the program structure, and adding defined workout days.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "The full name of the client."},
                "program_name": {"type": "string", "description": "The desired name for the new training program."},
                "workout_definitions": {
                    "type": "array",
                    "description": "A list defining the workouts to create. Each item should specify the type of day and the exercises.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_type": {
                                "type": "string",
                                "description": "Type of workout day. Supported values: 'back', 'chest_tris', 'shoulders_core', 'legs', 'arms_core'."
                            },
                            "exercises_list": {
                                "type": "array",
                                "description": "List of exercises for this day.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Name of the exercise."},
                                        "sets": {"type": "string", "description": "Number of sets (e.g., '3')."},
                                        "reps": {"type": "string", "description": "Number of reps (e.g., '12')."}
                                    },
                                    "required": ["name", "sets", "reps"]
                                }
                            }
                        },
                        "required": ["day_type", "exercises_list"]
                    }
                }
            },
            "required": ["client_name", "program_name", "workout_definitions"]
        }
    },
    # --- New Composite Function Definition (Edit Workout) ---
    {
        "name": "edit_client_workout",
        "description": "Edits a specific workout for a client by adding or removing an exercise.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "The full name of the client whose program needs editing."},
                "workout_name": {"type": "string", "description": "The exact name of the workout to edit (e.g., 'Back and Biceps Day')."},
                "action": {"type": "string", "enum": ["add", "remove"], "description": "The action to perform: 'add' or 'remove' exercise."},
                "exercise_details": {
                    "type": "object",
                    "description": "Details of the exercise to add or remove.",
                    "properties": {
                        "exercise_name": {"type": "string", "description": "The full name of the exercise."},
                        "sets": {"type": "string", "description": "Number of sets (required for 'add', e.g., '3')."},
                        "reps": {"type": "string", "description": "Number of reps (required for 'add', e.g., '12')."}
                    },
                    "required": ["exercise_name"]
                }
            },
            "required": ["client_name", "workout_name", "action", "exercise_details"]
        }
    }
    # --- End New Composite Function Definition ---
]

# --- Additional primitives for Trainerize flows ---


def press_space():
    """Press the spacebar to scroll or advance."""
    ActionChains(driver).send_keys(Keys.SPACE).perform()


def scroll_down(pixels: int = 300):
    """Scroll down the page by given pixels."""
    driver.execute_script(f"window.scrollBy(0, {pixels});")


def navigate_to_client(name: str):
    """Navigate to client profile by name."""
    success = automation.navigate_to_client(name)
    print(f"navigate_to_client returned {success}")
    return success


def scrape_workouts():
    """Scrape workouts from current client."""
    data = automation.process_workouts()
    print(data)
    return data


def send_initial_message_to(name: str):
    """Send initial message to client."""
    success = automation.send_initial_message(name)
    print(f"send_initial_message_to returned {success}")
    return success


def login():
    """Log in to Trainerize using stored credentials."""
    success = automation.login(USERNAME, PASSWORD)
    print(f"login returned {success}")
    return success


# --- Workout editing wrappers ---


def navigate_to_training_program():
    """Navigate to the Training Program tab."""
    success = automation.navigate_to_training_program()
    print(f"navigate_to_training_program returned {success}")
    return success


def click_workout(workout_name: str):
    """Click on a workout with the given name."""
    success = automation.click_workout(workout_name)
    print(f"click_workout returned {success}")
    return success


def click_edit_workout():
    """Click the 'Edit workout' button and select 'Workout Builder'."""
    success = automation.click_edit_workout()
    print(f"click_edit_workout returned {success}")
    return success


def remove_exercise(exercise_name: str):
    """Remove the specified exercise from the current workout."""
    success = automation.remove_exercise(exercise_name)
    print(f"remove_exercise returned {success}")
    return success


def add_exercise(exercise_name: str, sets: str, reps: str):
    """Add the specified exercise with sets and reps to the current workout."""
    success = automation.add_exercise(exercise_name, sets, reps)
    print(f"add_exercise returned {success}")
    return success

# --- Program builder & editor wrappers ---


def create_program(program_name: str):
    """Create a new training program by name."""
    success = automation.create_program(program_name)
    print(f"create_program returned {success}")
    return success


def click_program(program_name: str):
    """Click on a program with the given name."""
    success = automation.click_program(program_name)
    print(f"click_program returned {success}")
    return success


def create_workout_back_day(program_name: str, exercises_list: list):
    """Create and build a 'Back and Biceps' workout in the given program."""
    success = automation.create_workout_back_day(program_name, exercises_list)
    print(f"create_workout_back_day returned {success}")
    return success


def create_workout_chest_tris_day(program_name: str, exercises_list: list):
    """Create and build a 'Chest and Triceps' workout in the given program."""
    success = automation.create_workout_chest_tris_day(
        program_name, exercises_list)
    print(f"create_workout_chest_tris_day returned {success}")
    return success


def create_workout_shoulders_core_day(program_name: str, exercises_list: list):
    """Create and build a 'Shoulders and Core' workout in the given program."""
    success = automation.create_workout_shoulders_core_day(
        program_name, exercises_list)
    print(f"create_workout_shoulders_core_day returned {success}")
    return success


def create_workout_leg_day(program_name: str, exercises_list: list):
    """Create and build a 'Leg Day' workout in the given program."""
    success = automation.create_workout_leg_day(program_name, exercises_list)
    print(f"create_workout_leg_day returned {success}")
    return success


def create_workout_arms_core_day(program_name: str, exercises_list: list):
    """Create and build an 'Arms and Core' workout in the given program."""
    success = automation.create_workout_arms_core_day(
        program_name, exercises_list)
    print(f"create_workout_arms_core_day returned {success}")
    return success

# --- Composite Function for Full Program Build ---
def build_full_program_for_client(client_name: str, program_name: str, workout_definitions: list):
    """Builds a full multi-day program for a specific client."""
    logging.info(f"Starting full program build for {client_name}: '{program_name}'")
    results = []

    # 1. Navigate to client
    success = navigate_to_client(client_name)
    results.append({"step": "navigate_to_client", "success": success})
    if not success:
        logging.error("Failed to navigate to client. Aborting program build.")
        return results
    time.sleep(2) # Allow page load

    # 2. Navigate to Training Program tab
    success = navigate_to_training_program()
    results.append({"step": "navigate_to_training_program", "success": success})
    if not success:
        logging.error("Failed to navigate to training program tab. Aborting program build.")
        return results
    time.sleep(2) # Allow page load

    # 3. Create the program structure
    success = create_program(program_name)
    results.append({"step": "create_program", "success": success})
    if not success:
        logging.error("Failed to create program structure. Aborting program build.")
        return results
    time.sleep(2) # Allow action to complete

    # 4. Add workout days based on definitions
    for workout_def in workout_definitions:
        day_type = workout_def.get("day_type")
        exercises = workout_def.get("exercises_list")
        if not day_type or not exercises:
            logging.warning(f"Skipping invalid workout definition: {workout_def}")
            results.append({"step": f"add_workout_{day_type}", "success": False, "reason": "Invalid definition"})
            continue

        logging.info(f"Adding workout for day type: {day_type}")
        day_success = False
        step_name = f"create_workout_{day_type}_day"
        try:
            if day_type == "back":
                day_success = create_workout_back_day(program_name, exercises)
            elif day_type == "chest_tris":
                day_success = create_workout_chest_tris_day(program_name, exercises)
            elif day_type == "shoulders_core":
                day_success = create_workout_shoulders_core_day(program_name, exercises)
            elif day_type == "legs": # Assuming 'legs' maps to 'leg_day'
                day_success = create_workout_leg_day(program_name, exercises)
                step_name = "create_workout_leg_day" # Correct step name
            elif day_type == "arms_core":
                day_success = create_workout_arms_core_day(program_name, exercises)
            else:
                logging.warning(f"Unsupported day_type: {day_type}")
                results.append({"step": step_name, "success": False, "reason": f"Unsupported day type: {day_type}"})
                continue # Skip to next workout definition

            results.append({"step": step_name, "success": day_success})
            if not day_success:
                logging.error(f"Failed to create workout for {day_type}. Continuing with next day.")
            time.sleep(2) # Allow action to complete

        except Exception as e:
             logging.error(f"Error creating workout for {day_type}: {e}")
             results.append({"step": step_name, "success": False, "reason": str(e)})

    logging.info(f"Finished full program build for {client_name}. Results: {results}")
    return results

# --- Composite Function for Editing Workout ---
def edit_client_workout(client_name: str, workout_name: str, action: str, exercise_details: dict):
    """Edits a specific workout within a client's training program (adds or removes an exercise)."""
    logging.info(f"Starting workout edit for {client_name}, workout '{workout_name}'. Action: {action}")
    results = []

    # 1. Navigate to client
    success = navigate_to_client(client_name)
    results.append({"step": "navigate_to_client", "success": success})
    if not success:
        logging.error("Failed to navigate to client. Aborting workout edit.")
        return results
    time.sleep(2) # Allow page load

    # 2. Navigate to Training Program tab
    success = navigate_to_training_program()
    results.append({"step": "navigate_to_training_program", "success": success})
    if not success:
        logging.error("Failed to navigate to training program tab. Aborting workout edit.")
        return results
    time.sleep(2) # Allow page load

    # 3. Click the target workout
    # TODO: Add logic here if workout_name needs mapping (e.g., "back day" -> "Back and Biceps")
    actual_workout_name = workout_name # Assume exact name for now
    success = click_workout(actual_workout_name)
    results.append({"step": "click_workout", "success": success})
    if not success:
        logging.error(f"Failed to click workout '{actual_workout_name}'. Aborting workout edit.")
        return results
    time.sleep(2) # Allow page load

    # 4. Click Edit Workout
    success = click_edit_workout()
    results.append({"step": "click_edit_workout", "success": success})
    if not success:
        logging.error("Failed to click edit workout. Aborting workout edit.")
        return results
    time.sleep(3) # Allow builder to load

    # 5. Perform the action (add or remove)
    step_name = f"{action}_exercise"
    action_success = False
    exercise_name = exercise_details.get("exercise_name")

    if not exercise_name:
        logging.error("Exercise name missing from details.")
        results.append({"step": step_name, "success": False, "reason": "Missing exercise name"})
        return results

    try:
        if action.lower() == "add":
            sets = exercise_details.get("sets")
            reps = exercise_details.get("reps")
            if not sets or not reps:
                logging.error("Sets or reps missing for add action.")
                results.append({"step": step_name, "success": False, "reason": "Missing sets/reps for add"})
                return results
            action_success = add_exercise(exercise_name, sets, reps)

        elif action.lower() == "remove":
            action_success = remove_exercise(exercise_name)
        else:
            logging.error(f"Unsupported action: {action}")
            results.append({"step": step_name, "success": False, "reason": f"Unsupported action: {action}"})
            return results

        results.append({"step": step_name, "success": action_success})
        if not action_success:
             logging.error(f"Failed to {action} exercise '{exercise_name}'.")
        time.sleep(2) # Allow action to complete

    except Exception as e:
        logging.error(f"Error performing {action} for exercise '{exercise_name}': {e}")
        results.append({"step": step_name, "success": False, "reason": str(e)})

    # TODO: Add logic here to click a 'Save' or 'Done' button if necessary after editing.

    logging.info(f"Finished workout edit for {client_name}. Results: {results}")
    return results


# --- Primitive functions exposed to the LLM ---


def navigate(url: str):
    """Navigate to the given URL."""
    driver.get(url)


def click(text: str):
    """Click a visible element containing the given text."""
    elem = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//*[contains(text(), '{text}') or contains(@aria-label, '{text}')]")))
    elem.click()


def type_text(text: str, field: str):
    """Type text into an input matched by id, name, or placeholder."""
    locator = (
        By.XPATH, f"//input[@id='{field}' or @name='{field}' or contains(@placeholder,'{field}')]")
    elem = wait.until(EC.presence_of_element_located(locator))
    elem.clear()
    elem.send_keys(text)


def wait_for(text: str):
    """Wait until an element containing the given text appears."""
    wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]")
                                              ))


# --- LLM interaction prompt ---
SYSTEM_PROMPT = '''
You are a Selenium automation assistant for the Trainerize web interface.
You have these Python functions available:
  - navigate(url)
  - click(text)
  - type_text(text, field)
  - wait_for(text)
  - login(): log in using stored credentials (USERNAME/PASSWORD)
  - press_space(): press the spacebar to scroll/advance
  - scroll_down(pixels): scroll down by a number of pixels
  - navigate_to_client(name): navigate to a client's profile
  - scrape_workouts(): retrieve workout data for the current client
  - send_initial_message_to(name): send the initial message to a client
Examples:
  # Instruction: browse to Shannon Birch's profile - send a direct message saying hey bro we on
  navigate_to_client("Shannon Birch")
  type_text("hey bro we on", "Type your message")
  click("Send")

For each subsequent user instruction, output only a valid Python snippet that uses these functions to perform the requested action. Do not include any explanations or markdown.
'''


def main():
    print("Trainerize Custom Agent ready. Type 'exit' to quit.")
    print("You can call primitives directly, e.g. login(), navigate_to_client('Name'), or use English prompts.")
    while True:
        instruction = input(">>> ")
        if instruction.strip().lower() in ("exit", "quit"):
            break
        # Special pattern: browse to <name>'s profile and message
        import re
        m = re.match(
            r"browse to ([^']+)'s profile\s*-\s*send (?:him|her|them) a direct message saying (.+)", instruction, re.IGNORECASE)
        if m:
            name = m.group(1).strip()  # e.g. 'Shannon Birch'
            text = m.group(2).strip()
            print(
                f"Pattern match: navigate_to_client('{name}'); type_text('{text}', 'Type your message'); click('Send')")
            navigate_to_client(name)
            type_text(text, "Type your message")
            click("Send")
            continue
        # Use OpenAI chat completions with function calling
        resp = client.chat.completions.create(
            model="google/gemini-2.0-flash",
            messages=[{"role": "user", "content": instruction}],
            functions=FUNCTION_DEFS,
            function_call="auto"
        )
        # Print the full response for debugging
        print(f"Full API Response: {resp}")
        # Extract assistant message
        message = resp.choices[0].message
        # Check if the model responded with tool calls (OpenAI v1+ format)
        if message.tool_calls:
            # Assuming only one tool call for now
            tool_call = message.tool_calls[0]
            name = tool_call.function.name
            args_str = tool_call.function.arguments
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                print(f"Error: Could not decode arguments: {args_str}")
                continue  # Skip to next loop iteration if args are invalid

            # Call the primitive
            try:
                result = globals()[name](**args)
                print(f"{name} returned: {result}")
            except Exception as e:
                print(f"Error calling {name}(): {e}")
        else:
            # No function call; print the assistant's text
            print(message.content)

    # Clean up
    automation.cleanup()


if __name__ == "__main__":
    main()
