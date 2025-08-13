# Trainerize Automation System Overview

This document explains the purpose and interaction of the Python scripts used in the Trainerize automation project.

## Core Scripts

1.  **`trainerize_agent.py` (Main Controller / REPL)**
    *   **Purpose:** Acts as the central command interface. It takes natural language instructions from the user via a command-line REPL (Read-Eval-Print Loop).
    *   **Functionality:**
        *   Uses the Gemini language model (via an OpenAI-compatible Vertex AI endpoint) to interpret user commands and determine the appropriate action (function call).
        *   Defines a set of high-level functions (e.g., `login`, `navigate_to_client`, `add_exercise`) that the LLM can choose to call. These functions are defined using a schema (`FUNCTION_DEFS`) for the LLM.
        *   Most of these high-level functions act as *wrappers* that call the corresponding detailed implementation methods within the `TrainerizeAutomation` class.
        *   It initializes and uses an instance of `TrainerizeAutomation` imported from `checkin_new_1904.py`.
        *   Includes basic Selenium primitives (`click`, `type_text`, `navigate`) also exposed to the LLM.
        *   Handles the user input loop and executes the function calls selected by the LLM.

2.  **`checkin_new_1904.py` (Core Automation & Check-in Logic)**
    *   **Purpose:** Contains the most comprehensive `TrainerizeAutomation` class, providing the detailed Selenium logic for interacting with the Trainerize web application, focusing heavily on the client check-in process.
    *   **Functionality:**
        *   Handles robust login and navigation to specific client profiles.
        *   Includes methods to navigate to various data tabs (Progress Photos, Bodyweight, Nutrition, Sleep, Steps, Goals & Habits).
        *   Scrapes data points and graph information from these tabs.
        *   Performs analysis on the scraped data (e.g., calculating trends, identifying progress).
        *   Processes workout history (`process_workouts`) and calculates statistics.
        *   Integrates with Google Sheets API to read/write check-in related data.
        *   Integrates with Gemini API (`generate_checkin_review_content`, `generate_professional_checkin_review`) to generate summaries and client messages based on analyzed data.
        *   Generates PDF check-in review reports using `reportlab`.
        *   Includes utility functions (e.g., file cleanup, GraphQL interaction, date calculations).
        *   This is the primary class instantiated and used by `trainerize_agent.py`.

## Specialized Scripts (Potentially Standalone or Future Integration)

These scripts also contain `TrainerizeAutomation` classes but seem focused on specific, potentially less frequent tasks. They might be intended for standalone use or integration into the main agent later.

3.  **`scripts/pb.py` (Program Builder)**
    *   **Purpose:** Focused on *building* new, multi-week training programs from scratch.
    *   **Functionality:**
        *   Contains methods like `create_program` to initiate a new program structure.
        *   Includes functions to create specific workout days (`create_workout_back_day`, `create_workout_leg_day`, etc.) by adding sets of predefined exercises. Appears designed for bulk creation based on templates.

4.  **`scripts/pe.py` (Program Editor)**
    *   **Purpose:** Focused on *editing* existing workouts within a client's training program.
    *   **Functionality:**
        *   Contains methods for navigating to a specific workout (`navigate_to_training_program`, `click_workout`, `click_edit_workout`).
        *   Includes robust versions of `add_exercise` (handling search clearing, popups) and `remove_exercise` (using drag-and-drop simulation).
        *   Contains a very large, hardcoded list (`self.exercise_list`) for validating exercise names before attempting to add them.
        *   Also includes methods similar to `pb.py` for creating specific workout days, perhaps for modifying existing programs.

## Available Agent Commands

This is the list of functions the `trainerize_agent.py` script makes available to the underlying language model. You can often use natural language (like "log me in" or "go to John Doe's profile"), but knowing the specific function names can be helpful for more complex or precise instructions.

**Core Navigation & Interaction:**

*   `login()`: Log in to Trainerize using stored credentials.
*   `navigate(url)`: Navigate to the given URL.
*   `click(text)`: Click an element containing the given text.
*   `type_text(text, field)`: Type text into an input field (identified by id, name, or placeholder text).
*   `wait_for(text)`: Wait until an element containing the given text appears.
*   `press_space()`: Press the spacebar (useful for scrolling or advancing).
*   `scroll_down(pixels)`: Scroll down the page by a specific number of pixels.

**Client & Data Specific:**

*   `navigate_to_client(name)`: Navigate to a specific client's profile by their full name.
*   `scrape_workouts()`: Scrape workout data from the currently viewed client profile.
*   `send_initial_message_to(name)`: Send the initial pre-defined message to a client by name (requires the client's profile to be loaded).

**Workout Editing (within a specific workout):**

*   `navigate_to_training_program()`: Navigate to the 'Training Program' tab on the current client's profile.
*   `click_workout(workout_name)`: Click on a specific workout within the training program list.
*   `click_edit_workout()`: Click the 'Edit workout' button and then select 'Workout Builder'.
*   `remove_exercise(exercise_name)`: Remove an exercise from the workout currently being edited.
*   `add_exercise(exercise_name, sets, reps)`: Add an exercise (with sets/reps) to the workout currently being edited.

**Program Building (for creating new programs/workouts):**

*   `create_program(program_name)`: Create a new training program structure with the given name.
*   `click_program(program_name)`: Click on a specific program within the master program list.
*   `create_workout_back_day(program_name, exercises_list)`: Create and add exercises for a 'Back and Biceps' workout day within the specified program.
*   `create_workout_chest_tris_day(program_name, exercises_list)`: Create and add exercises for a 'Chest and Triceps' workout day.
*   `create_workout_shoulders_core_day(program_name, exercises_list)`: Create and add exercises for a 'Shoulders and Core' workout day.
*   `create_workout_leg_day(program_name, exercises_list)`: Create and add exercises for a 'Leg Day' workout.
*   `create_workout_arms_core_day(program_name, exercises_list)`: Create and add exercises for an 'Arms and Core' workout day.

## Overall Workflow (Agent-Driven)

1.  The user starts `trainerize_agent.py`.
2.  The user types a natural language command (e.g., "log in and go to Shannon Birch's profile").
3.  `trainerize_agent.py` sends this command to the Gemini LLM, along with the list of available functions (`FUNCTION_DEFS`).
4.  The LLM determines the appropriate function(s) to call (e.g., `login()`, then `navigate_to_client(name='Shannon Birch')`).
5.  `trainerize_agent.py` receives the function call instructions from the LLM.
6.  It executes the corresponding wrapper function defined within `trainerize_agent.py`.
7.  The wrapper function (e.g., `navigate_to_client`) calls the actual implementation method (e.g., `automation.navigate_to_client(...)`) on the `TrainerizeAutomation` instance that was created from `checkin_new_1904.py`.
8.  The method in `checkin_new_1904.py` uses Selenium (`self.driver`, `self.wait`) to perform the actions in the browser.
9.  The result (success/failure or data) is returned up the chain.
10. `trainerize_agent.py` prints the result and waits for the next user command.

**Note:** The `pb.py` and `pe.py` scripts don't seem to be directly called by the `trainerize_agent.py`'s main loop currently. Their functionality would need specific commands and potentially new wrapper functions in the agent to be invoked via the LLM. 