from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import subprocess
import sys
import json
import logging
import os
import re

class Action:
    def __init__(self, action_type, selector=None, by="css", text=None, wait=0, data_type="text", url=None):
        self.type = action_type
        self.selector = selector
        self.by = by
        self.text = text
        self.wait = wait
        self.data_type = data_type
        self.url = url

def find_element(driver, action, single=True):
    """Helper function to find elements with optional wait."""
    if action.wait > 0:
        try:
            WebDriverWait(driver, action.wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, action.selector)))
        except:
            return None # or raise exception

    if action.by == "css":
        if single:
            return driver.find_element(By.CSS_SELECTOR, action.selector)
        else:
            return driver.find_elements(By.CSS_SELECTOR, action.selector)
    elif action.by == "xpath":
       # xpath is much harder to use with find element, so its not being added here
        return None

def click_element(driver, action):
    element = find_element(driver, action)
    if element:
        element.click()

def enter_text(driver, action):
    element = find_element(driver, action)
    if element:
        element.send_keys(action.text)

def extract_data(driver, action):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    elements = soup.select(action.selector)
    data = []
    if action.data_type == "text":
        for element in elements:
            data.append(element.text)
    return data

def navigate(driver, action):
    driver.get(action.url)

def scroll_down(driver, scroll_height=500, delay=0.25):
    """Scroll down the webpage in increments, with a delay."""
    current_scroll = 0
    while current_scroll < driver.execute_script("return document.body.scrollHeight"):
       driver.execute_script(f"window.scrollTo(0, {current_scroll});")
       current_scroll += scroll_height
       time.sleep(delay)

def load_bot_script_from_file(file_path):
    bot_script = []
    try:
      with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue # skip empty lines
                parts = line.split(",")
                if len(parts) < 1:
                    continue
                action_type = parts[0].strip()
                selector = parts[1].strip() if len(parts) > 1 else None
                text = parts[2].strip() if len(parts) > 2 else None
                by = parts[3].strip() if len(parts) > 3 else "css"
                wait = int(parts[4].strip()) if len(parts) > 4 and parts[4].strip().isdigit() else 0
                data_type = parts[5].strip() if len(parts) > 5 else "text"
                url = parts[1].strip() if len(parts) > 1 and action_type == "navigate" else None
                bot_script.append({"action": action_type, "selector": selector, "text": text, "by": by, "wait": wait, "data_type": data_type, "url":url })
      return bot_script
    except Exception as e:
        print(f'An error occurred when reading the file: {e}')
        sys.exit()


def call_gemini(prompt, webdriver_path=""):
    """Placeholder function to simulate the call to Gemini."""
    print(f"Sending prompt to Gemini: {prompt}")
    if "generate a full python file" in prompt:
       return f"""from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import json

def click_element(driver, selector, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.click()
    except Exception as e:
        logging.error(f'click_element - {{e}}')

def enter_text(driver, selector, text, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(text)
    except Exception as e:
        logging.error(f'enter_text - {{e}}')

def extract_data(driver, selector, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        elements = soup.select(selector)
        for element in elements:
           print(element.text)
    except Exception as e:
       logging.error(f'extract_data - {{e}}')

def scroll_down(driver):
    current_scroll = 0
    while current_scroll < driver.execute_script("return document.body.scrollHeight"):
       driver.execute_script(f"window.scrollTo(0, {{current_scroll}});")
       current_scroll += 200
       time.sleep(0.15)

def run_bot():
    logging.basicConfig(filename='bot.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    webdriver_path = r'{webdriver_path}'
    service = Service(webdriver_path)
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
""".format(webdriver_path=webdriver_path)
    elif "Use this to debug the meta_bot.py script" in prompt:
        return """
        print("no changes to meta_bot.py")
        """
    return "Generated code by Gemini"

def generate_bot(bot_script, webdriver_path, file_path):
    template = """from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import json

def click_element(driver, selector, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.click()
    except Exception as e:
        logging.error(f'click_element - {{e}}')

def enter_text(driver, selector, text, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(text)
    except Exception as e:
        logging.error(f'enter_text - {{e}}')

def extract_data(driver, selector, wait):
    try:
        WebDriverWait(driver, wait, timeout=10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        elements = soup.select(selector)
        for element in elements:
           print(element.text)
    except Exception as e:
       logging.error(f'extract_data - {{e}}')

def scroll_down(driver):
    current_scroll = 0
    while current_scroll < driver.execute_script("return document.body.scrollHeight"):
       driver.execute_script(f"window.scrollTo(0, {current_scroll});")
       current_scroll += 200
       time.sleep(0.15)

def run_bot():
    logging.basicConfig(filename='bot.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    webdriver_path = r'""" + webdriver_path + """'
    service = Service(webdriver_path)
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
"""
    with open(file_path, 'w') as f:
        f.write(template)
        for item in bot_script:
            action = item['action']
            selector = item.get('selector')
            text = item.get('text')
            wait = item.get('wait', 0)
            data_type = item.get('data_type', 'text')
            by = item.get('by', 'css')
            url = item.get('url')
            f.write(f"        # Action: {action}, selector: {selector}, wait: {wait}, data_type:{data_type}, by: {by}, text: {text}, url:{url}\n")
            if action == 'navigate':
                f.write(f"        driver.get('{url}')\n")
            elif action == 'scroll_down':
                f.write(f"        scroll_down(driver)\n")
            elif action == 'click':
                if selector:
                   f.write(f"        click_element(driver, '''{selector}''', {wait})\n")
            elif action == 'enter_text':
                 if selector and text:
                     f.write(f"        enter_text(driver, '''{selector}''', '''{text}''', {wait})\n")
            elif action == 'extract_data':
                if selector:
                    f.write(f"        extract_data(driver, '''{selector}''', {wait})\n")
        f.write("""    except Exception as e:
        logging.error(f'An error occurred: {e}')
    finally:
        driver.quit()

if __name__ == '__main__':
    run_bot()
""")


def analyze_logs(log_output):
    errors = []
    for line in log_output.splitlines():
        if "error" in line.lower():
            errors.append(line)
    return errors

def update_bot_script(bot_script, errors):
    updated_script = bot_script[:]  # Create a copy to avoid modifying original
    for error_message in errors:
      print(f"Error: {error_message}")
      match = re.search(r'"selector":\s*"([^"]+)"', error_message)
      if match:
          selector = match.group(1)
          print(f"   Selector found: {selector}")
          for i, action in enumerate(updated_script):
              if action.get("selector") == selector:
                    print(f"        Updating wait time for action: {action}")
                    updated_script[i]["wait"] = action.get("wait", 0) + 2
                    print(f"       New action : {updated_script[i]}")
                    break
    return updated_script
    
def update_bot_script_file(file_path, bot_script):
    with open(file_path, 'w') as f:
        for item in bot_script:
            action = item.get("action")
            selector = item.get("selector")
            text = item.get("text")
            by = item.get("by")
            wait = item.get("wait")
            data_type = item.get("data_type")
            url = item.get("url")
            line = f"{action},{selector},{text},{by},{wait},{data_type},{url}"
            line = ",".join(filter(None,[action, selector, text, by, str(wait), data_type, url]))
            f.write(line + "\n")


# Set options to run in headless mode (you can comment this out to see the browser)
chrome_options = Options()
#chrome_options.add_argument("--headless")

# Set the path to your chromedriver
webdriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"  # Raw string for Windows paths

# Create a service object
service = Service(webdriver_path)

# Start the browser
driver = webdriver.Chrome(service=service, options=chrome_options)

# Get the file path from the command line
if len(sys.argv) < 2:
    print("Please provide a bot script file path as an argument")
    sys.exit()

script_file_path = sys.argv[1]
bot_script = load_bot_script_from_file(script_file_path)


max_iterations = 3
for i in range(max_iterations):
    print(f"Starting iteration: {i}")
    file_path = "generated_bot.py"
    prompt = f"Here is a bot script in CSV format. Use this to generate a full python file that can navigate a website using Selenium: \\n{bot_script}"
    gemini_code = call_gemini(prompt, webdriver_path)
    with open(file_path, 'w') as f:
        f.write(gemini_code)
    process = subprocess.Popen(["python", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # Output the stdout and stderr of the generated script to the meta_bot
    print("stdout: " + stdout.decode('utf-8'))
    print("stderr: " + stderr.decode('utf-8'))
    errors = analyze_logs(stderr.decode('utf-8'))
    if not errors:
        print("No Errors Found, bot finished successfully")
        break
    else:
       print(f"Errors Found, attempting to update script")
       prompt = f"Here is the stderr that I received when running the bot script. Use this to debug the meta_bot.py script, and output the new code: \\n{stderr.decode('utf-8')}"
       gemini_code = call_gemini(prompt)
       with open("meta_bot.py", 'w') as f:
           f.write(gemini_code)
       bot_script = update_bot_script(bot_script, errors)
       update_bot_script_file(script_file_path, bot_script)

driver.quit()