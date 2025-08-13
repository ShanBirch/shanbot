import subprocess
import os
import io
import sys
import requests
import json
from time import sleep
import re


def run_and_get_output(script_path):
    """Runs a Python script and returns its combined output."""
    try:
        process = subprocess.Popen(
            ["python", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Set the PYTHONIOENCODING
            env={"PYTHONIOENCODING": "utf-8", **os.environ},
        )
        stdout, stderr = process.communicate(
            timeout=300)  # Increased timeout to 300s
        return stdout + "\n" + stderr
    except subprocess.TimeoutExpired:
        return "❌ Script timed out."
    except Exception as e:
        return f"❌ Error running script: {e}"


def send_output_to_api(output):
    """Sends output to API endpoint and returns response."""
    api_url = "http://127.0.0.1:5001/adjust-code"  # Replace with your API URL

    try:
        response = requests.post(
            api_url, json={"output": output}, timeout=300)  # Increased Timeout to 300 seconds
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {e}")
        return None


def save_code_to_file(script_path, adjusted_code):
    """Saves the adjusted code to the main script file."""
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(adjusted_code)
        print(f"✔️ Adjusted code saved to {script_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving adjusted code: {e}")
        return False


def is_code_like(text):
    """
    Checks if the text looks like code.
    This is a heuristic, not foolproof.
    """
    code_keywords = [
        'def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'try:', 'except:'
    ]
    for keyword in code_keywords:
        if keyword in text:
            return True
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*.+$', text, re.MULTILINE):
        return True
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*\([^\)]*\)\s*(:\s*.*)?$', text, re.MULTILINE):
        return True
    return False


def main():
    script_path = "trainerize.py"  # Changed to trainerize.py
    # Set the encoding to UTF-8 for standard output and standard error
    sys.stdout = io.TextIOWrapper(
        sys.stdout.detach(), encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.detach(), encoding='utf-8', errors='replace')

    while True:
        print_step("RUNNING SCRIPT")
        output = run_and_get_output(script_path)

        print_step("OUTPUT")
        print(output)

        print_step("FEEDBACK")

        api_response = send_output_to_api(output)

        if api_response and 'adjusted_code' in api_response:
            adjusted_code = api_response['adjusted_code']
            print_step("API FEEDBACK")
            print(
                f"API provided the following adjusted code:\n{adjusted_code[:500]}...")

            if is_code_like(adjusted_code):
                if save_code_to_file(script_path, adjusted_code):
                    print("✔️ Re-running script with adjusted code")
                else:
                    print("❌ Could not save adjusted code, ending.")
                    break
            else:
                print(
                    "❌ API did not provide valid code. Please review the output and try again.")
                if input("Press Enter to re-run or 'quit' to exit").lower() == 'quit':
                    break
        else:
            print("❌ No valid adjusted code received from API")
            if input("Press Enter to re-run or 'quit' to exit").lower() == 'quit':
                break


def print_step(message):
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
