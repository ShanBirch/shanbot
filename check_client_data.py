import sqlite3
from workout_utils import get_current_week_workouts, format_workout_summary_for_prompt
from datetime import datetime, date, timedelta
from typing import Optional, Tuple

# --- Configuration ---
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

# List of client names from your check-in files (approximated from the image)
# Format: "FirstName_LastName" or "FirstName LastName"
CLIENT_NAMES = [
    "Alice_Forster",
    "Anna_Somogyi",
    "Claire_Ruberu",
    "Danny_Birch",
    "Elena_Green",
    "Jo_Foy",  # Assuming Foy is the last name
    "Kelly_Smith",
    "Kristy_Cooper",  # Already know this one
    "Kylie_Pinder",
    "Nicole_Lynch",
    "Rebecca_DAngelo",  # Handle D'Angelo style names
    "Rick_Preston",
    "Sarika_Ramani",
    "Shane_Minahan",
    "Tony_Strupl"  # Assuming Strupl is the last name
]

# Specific known IG usernames if the file name differs significantly
KNOWN_IG_USERNAMES = {
    "Kristy_Cooper": "kristyleecoop",
    "Kelly_Smith": "kelstar"
}


def get_ig_username_from_db(original_name_str: str) -> Optional[str]:
    """Queries the SQLite database for ig_username using various strategies, prioritizing direct match of original_name_str."""
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        search_terms = []
        original_name_lower = original_name_str.lower()

        # Priority 1: Check against KNOWN_IG_USERNAMES map
        if original_name_str in KNOWN_IG_USERNAMES:
            search_terms.append(KNOWN_IG_USERNAMES[original_name_str].lower())

        # Priority 2: Original name string from CLIENT_NAMES as potential ig_username
        search_terms.append(original_name_lower)  # e.g., kristy_cooper
        search_terms.append(original_name_lower.replace(
            "_", ""))  # e.g., kristycooper
        search_terms.append(original_name_lower.replace(
            "_", "."))  # e.g., kristy.cooper

        # Attempt to parse first/last for fallback search against name columns
        parsed_first_name, parsed_last_name = parse_name(original_name_str)

        # Remove duplicates by converting to set and back to list
        unique_search_terms = list(set(search_terms))

        # Query for ig_username based on search_terms
        if unique_search_terms:
            placeholders_ig = ",".join(["lower(?)"] * len(unique_search_terms))
            sql_query_ig = f"SELECT ig_username FROM users WHERE lower(ig_username) IN ({placeholders_ig}) LIMIT 1"
            cursor.execute(sql_query_ig, unique_search_terms)
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]

        # Fallback Strategy: Match on parsed first and last names (if both exist and are not null in DB)
        if parsed_first_name and parsed_last_name:
            # This query is more likely to work if first_name and last_name columns are actually populated
            cursor.execute("""SELECT ig_username FROM users 
                           WHERE lower(first_name) = lower(?) AND lower(last_name) = lower(?) 
                           AND first_name IS NOT NULL AND last_name IS NOT NULL LIMIT 1""",
                           (parsed_first_name, parsed_last_name))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]

        # Fallback for single parsed name (e.g. if original was "JoFoy" and parsed to first="JoFoy", last=None)
        # This might happen if CLIENT_NAMES has entries like "ClientNameOnly"
        if parsed_first_name and not parsed_last_name:
            single_name_lower = parsed_first_name.lower()
            cursor.execute("""SELECT ig_username FROM users 
                               WHERE lower(ig_username) = lower(?) 
                                  OR (lower(first_name) = lower(?) AND last_name IS NULL)
                                  OR (lower(last_name) = lower(?) AND first_name IS NULL) LIMIT 1""",
                           (single_name_lower, single_name_lower, single_name_lower))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]

    except sqlite3.Error as e:
        print(f"Database error searching for '{original_name_str}': {e}")
    finally:
        if conn:
            conn.close()
    return None


def parse_name(client_name_str: str) -> Tuple[Optional[str], Optional[str]]:
    """Parses a client name string (FirstName_LastName or FirstName LastName) into first and last names."""
    parts = client_name_str.replace("_", " ").strip().split(
        " ", 1)  # Split only on the first space for last name
    if not parts:
        return None, None
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


def main():
    # --- FOR TESTING THE DATE DISCREPANCY ---
    # Set a fixed date for testing get_current_week_workouts behavior
    # This should be a Sunday to match the scenario described
    fixed_test_date = date(2025, 5, 25)
    print(
        f"--- Client Workout Data Check (Fixed Test Date: {fixed_test_date.strftime('%Y-%m-%d %A')}) ---")
    # --- END TESTING DATE ---
    print(f"Database: {SQLITE_PATH}\n")

    found_clients = 0
    clients_with_workouts = 0

    for name_str in CLIENT_NAMES:
        print(f"\nProcessing: '{name_str}'")
        parsed_first_name, parsed_last_name = parse_name(name_str)

        if parsed_first_name:
            print(
                f"  Parsed: First='{parsed_first_name}', Last='{parsed_last_name if parsed_last_name else 'N/A'}'")
        else:
            print(f"  Could not parse name for '{name_str}'. Skipping.")
            continue

        # Pass original_name_str for more flexible matching
        ig_username = get_ig_username_from_db(name_str)

        if ig_username:
            print(f"  ACCOUNT FOUND: ig_username = '{ig_username}'")
            found_clients += 1
            try:
                # Call get_current_week_workouts normally (it uses current date internally)
                workout_data = get_current_week_workouts(ig_username)
                if workout_data and workout_data.get('total_sessions', 0) > 0:
                    clients_with_workouts += 1
                    print(
                        f"  Workout Summary (Week: {workout_data.get('week_start')} to {workout_data.get('week_end')}):")
                    prompt_summary = format_workout_summary_for_prompt(
                        workout_data)
                    for line in prompt_summary.splitlines():
                        print(f"    {line}")
                elif workout_data:
                    # Corrected print statement for no workout sessions
                    # Calculate the previous week based on the fixed_test_date
                    start_of_test_week = fixed_test_date - \
                        timedelta(days=fixed_test_date.weekday())
                    # Start of the week *before* the fixed_test_date's week
                    week_start_display = start_of_test_week - \
                        timedelta(days=7)
                    week_end_display = week_start_display + \
                        timedelta(days=6)  # End of that previous week
                    print(
                        f"  No workout sessions found for '{ig_username}' in the week {week_start_display.strftime('%Y-%m-%d')} to {week_end_display.strftime('%Y-%m-%d')} (based on test date {fixed_test_date.strftime('%Y-%m-%d %A')}).")
                else:
                    print(
                        f"  Could not retrieve workout data for '{ig_username}'. It might be an old account or data issue.")
            except Exception as e:
                print(
                    f"  Error fetching workout data for '{ig_username}': {e}")
        else:
            print(
                f"  ACCOUNT NOT FOUND for '{name_str}' (parsed as First: {parsed_first_name}, Last: {parsed_last_name if parsed_last_name else 'N/A'}).")

    print(f"\n--- Summary ---")
    print(f"Total clients processed: {len(CLIENT_NAMES)}")
    print(f"Accounts found in database: {found_clients}")
    print(
        f"Clients with workout data for the week determined by test date: {clients_with_workouts}")
    print(f"--- End of Report ---")


if __name__ == "__main__":
    main()
