import subprocess
import os
import io
import sys
import requests
import json
from time import sleep
import re
import uuid
import logging
import select

# Configure basic logging to a file
log_file = f"autofeedback_{uuid.uuid4()}.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_file,
                    filemode='w')


def run_and_get_output(script_path, log_file_path):
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
        stdout, stderr = "", ""

        start_time = time.time()
        while time.time() - start_time < 300:  # Increased timeout to 300 seconds
            ready = select.select([process.stdout, process.stderr], [], [], 1)[
                0]  # select ready file descriptors with 1 second timeout

            if process.stdout in ready:
                stdout += process.stdout.read()
            if process.stderr in ready:
                stderr += process.stderr.read()

            if process.poll() is not None:
                break

        if process.returncode is None:
            process.terminate()
            logging.error("Process timed out before completing")
            return "❌ Script timed out."

        combined_output = stdout + "\n" + stderr
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(combined_output)
        logging.info(f"Output saved to: {log_file_path}")
        return combined_output
    except Exception as e:
        logging.exception(f"Error running script: {e}")
        return f"❌ Error running script: {e}"


def upload_to_pastebin(file_path):
    """Uploads a file to Pastebin and returns the paste URL."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        pastebin_api_url = "https://pastebin.com/api/api_post.php"
        # Pastebin API key is embedded here
        api_dev_key = "MGYvkj54YYuOEDO69Zs5xv39DYkqfMLK"
        params = {
            'api_dev_key': api_dev_key,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_private': 1,  # 0=public, 1=unlisted, 2=private
            'api_paste_expire_date': '10M'  # Set to 10 minutes
        }
        response = requests.post(pastebin_api_url, data=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        paste_url = response.text
        logging.info(f"Uploaded {file_path} to Pastebin: {paste_url}")
        return paste_url
    except Exception as e:
        logging.exception(f"Error uploading to Pastebin: {e}")
        return None


def send_output_to_api(output, pastebin_links, code, html):
    """Sends output to API endpoint and returns response."""
    api_url = "http://127.0.0.1:5001/adjust-code"  # Replace with your API URL

    try:
        response = requests.post(
            api_url, json={"output": output, "pastebin_links": pastebin_links, "code": code, "html": html}, timeout=300)  # Increased Timeout to 300 seconds
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.exception(f"API request error: {e}")
        return None


def send_summary_to_api(code, output, pastebin_links):
    """Sends output to second API endpoint and returns response."""
    api_url = "http://127.0.0.1:5002/summarize-code"  # Replace with your API URL

    try:
        response = requests.post(
            api_url, json={"output": output, "pastebin_links": pastebin_links, "code": code}, timeout=300)  # Increased Timeout to 300 seconds
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.exception(f"API request error: {e}")
        return None


def save_code_to_file(script_path, adjusted_code):
    """Saves the adjusted code to the main script file."""
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(adjusted_code)
        logging.info(f"✔️ Adjusted code saved to {script_path}")
        return True
    except Exception as e:
        logging.exception(f"Error saving adjusted code: {e}")
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
    script_path = "trainerize.py"
    autofeedback_log_path = f"autofeedback_log_{uuid.uuid4()}.txt"
    trainerize_log_path = f"trainerize_log_{uuid.uuid4()}.txt"

    while True:
        print_step("RUNNING SCRIPT")
        output = run_and_get_output(script_path, trainerize_log_path)

        # Get the code from the script to pass to the api
        with open(script_path, 'r', encoding='utf-8') as file:
            code = file.read()

        # Get the html from the page
        trainerize_bot = None
        try:
            from trainerize import TrainerizeAutomation
            trainerize_bot = TrainerizeAutomation()
            trainerize_bot.driver.get(
                "https://cocosptstudio.trainerize.com/app/login")
            html = trainerize_bot.get_page_html()
        except Exception as e:
            logging.error(f"Error getting the html of the page : {e}")
            html = ""
        finally:
            if trainerize_bot:
                trainerize_bot.driver.quit()

        print_step("OUTPUT")
        print(output)

        print_step("FEEDBACK")

        pastebin_links = {}
        pastebin_links["autofeedback_log"] = upload_to_pastebin(
            autofeedback_log_path)
        pastebin_links["trainerize_log"] = upload_to_pastebin(
            trainerize_log_path)

        # Wait to ensure files exist
        if os.path.exists(autofeedback_log_path) and os.path.exists(trainerize_log_path):
            logging.info(
                f"Files exist: {autofeedback_log_path}, {trainerize_log_path}")
        else:
            logging.error("Files do not exist after running script")
            break

        api_response = send_output_to_api(output, pastebin_links, code, html)

        if api_response and 'adjusted_code' in api_response:
            adjusted_code = api_response['adjusted_code']

            summary_response = send_summary_to_api(
                code, output, pastebin_links)
            if summary_response and 'summary' in summary_response:
                summary = summary_response['summary']
                print_step("META API FEEDBACK")
                print(f"META API provided the following summary:\n{summary}")
            else:
                logging.error(
                    "Did not receive a valid response from the summary API")

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
