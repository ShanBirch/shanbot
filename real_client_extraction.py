#!/usr/bin/env python3
"""
REAL CLIENT EXTRACTION - Alice Forster, Nicole Lynch, Sarika Ramani
This will find your actual clients and extract their real data
"""

import asyncio
import time
import os
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import google.generativeai as genai


async def extract_real_client_data():
    """
    REAL EXTRACTION: Find Alice, Nicole, and Sarika and get their actual data
    """
    print("🎯 REAL CLIENT EXTRACTION")
    print("=" * 50)
    print("Target Clients:")
    print("• Alice Forster")
    print("• Nicole Lynch")
    print("• Sarika Ramani")
    print("=" * 50)

    # Your credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # Configure Gemini
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

    driver = None

    try:
        print("\n🚀 STEP 1: Launching Chrome with optimized settings...")

        # Optimized Chrome options to avoid errors
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = ChromeService(executable_path=chromedriver_path)

        # Create driver with improved error handling
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()

        print("✅ Chrome launched successfully")

        print("\n🔑 STEP 2: Logging into Trainerize...")

        # Navigate to login
        driver.get("https://www.trainerize.com/login.aspx")
        wait = WebDriverWait(driver, 25)

        # First page
        print("   → First page login...")
        email_field = wait.until(
            EC.presence_of_element_located((By.ID, "t_email")))
        email_field.clear()
        email_field.send_keys(username)

        find_button = driver.find_element(
            By.CLASS_NAME, "tz-button--secondary")
        find_button.click()
        time.sleep(6)

        # Second page with fallback strategies
        print("   → Completing login...")

        # Email field (try multiple selectors)
        email_entered = False
        email_selectors = ["#emailInput",
                           "input[type='email']", "input[placeholder*='Email']"]
        for selector in email_selectors:
            try:
                email_field2 = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                email_field2.clear()
                email_field2.send_keys(username)
                email_entered = True
                break
            except TimeoutException:
                continue

        if not email_entered:
            return {"success": False, "error": "Could not enter email on second page"}

        # Password field
        password_entered = False
        password_selectors = ["#passInput", "input[type='password']"]
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                password_field.clear()
                password_field.send_keys(password)
                password_entered = True
                break
            except NoSuchElementException:
                continue

        if not password_entered:
            return {"success": False, "error": "Could not enter password"}

        # Submit button
        submit_clicked = False
        submit_selectors = ["[data-testid='signIn-button']",
                            "button[type='submit']", "button:contains('SIGN IN')"]
        for selector in submit_selectors:
            try:
                if "contains" in selector:
                    submit_button = driver.find_element(
                        By.XPATH, f"//button[contains(text(), 'SIGN IN')]")
                else:
                    submit_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                driver.execute_script("arguments[0].click();", submit_button)
                submit_clicked = True
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not submit_clicked:
            return {"success": False, "error": "Could not click submit button"}

        # Wait for login
        time.sleep(10)

        print("✅ Login completed")

        print("\n🔍 STEP 3: Finding your real clients...")

        # Navigate to clients
        driver.get("https://www.trainerize.com/app/trainer/clients")
        time.sleep(6)

        # Take screenshot of client list
        driver.save_screenshot("client_list.png")

        # Analyze with AI to find our target clients
        with open("client_list.png", 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        client_search_prompt = """
        Analyze this Trainerize clients page screenshot.
        
        I'm looking specifically for these clients:
        - Alice Forster
        - Nicole Lynch
        - Sarika Ramani
        
        Please tell me:
        1. Which of these three clients can you see on this page?
        2. Are there any variations of their names (like "Alice F." or "Nicole L.")?
        3. List any other client names you can clearly see
        
        Be specific about what you can actually see.
        """

        response = model.generate_content([
            client_search_prompt,
            {"inline_data": {"mime_type": "image/png", "data": image_data}}
        ])

        print("✅ Client list analyzed!")

        print("\n📋 CLIENT SEARCH RESULTS:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)

        # Try to click on Alice Forster first (most likely to exist based on system docs)
        print("\n👤 STEP 4: Attempting to access Alice Forster's data...")

        alice_found = await find_and_click_client(driver, "Alice Forster")

        if alice_found:
            print("✅ Successfully accessed Alice Forster's profile!")

            # Extract Alice's program data
            program_data = await extract_client_program_data(driver, model, "Alice Forster")

            print("\n🏆 ALICE FORSTER'S REAL PROGRAM DATA:")
            print("=" * 50)
            print(program_data)
            print("=" * 50)

            result = {
                "success": True,
                "client_accessed": "Alice Forster",
                "program_data": program_data,
                "clients_found": response.text
            }
        else:
            # Try Nicole Lynch as backup
            print("   → Alice not found, trying Nicole Lynch...")
            nicole_found = await find_and_click_client(driver, "Nicole Lynch")

            if nicole_found:
                print("✅ Successfully accessed Nicole Lynch's profile!")
                program_data = await extract_client_program_data(driver, model, "Nicole Lynch")

                result = {
                    "success": True,
                    "client_accessed": "Nicole Lynch",
                    "program_data": program_data,
                    "clients_found": response.text
                }
            else:
                result = {
                    "success": False,
                    "error": "Could not access any of the target clients",
                    "clients_found": response.text
                }

        # Clean up
        if os.path.exists("client_list.png"):
            os.remove("client_list.png")

        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("\n🧹 Closing browser...")
            driver.quit()


async def find_and_click_client(driver, client_name):
    """Find and click on a specific client"""
    try:
        wait = WebDriverWait(driver, 15)

        # Try to search for the client first
        search_selectors = [
            "input[placeholder*='Search']", "input[type='search']"]
        for selector in search_selectors:
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, selector)
                search_box.clear()
                search_box.send_keys(client_name)
                time.sleep(3)
                break
            except NoSuchElementException:
                continue

        # Try to find and click the client
        client_selectors = [
            f"//a[contains(text(), '{client_name}')]",
            f"//div[contains(text(), '{client_name}')]",
            f"//span[contains(text(), '{client_name}')]",
            # Try first name only
            f"//*[contains(text(), '{client_name.split()[0]}')]"
        ]

        for selector in client_selectors:
            try:
                client_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].click();", client_element)
                time.sleep(5)
                return True
            except TimeoutException:
                continue

        return False

    except Exception as e:
        print(f"   ❌ Error finding {client_name}: {e}")
        return False


async def extract_client_program_data(driver, model, client_name):
    """Extract program data for a client"""
    try:
        print(f"   📊 Extracting {client_name}'s program data...")

        # Try to navigate to program/workout sections
        nav_options = ["Programs", "Workouts", "Schedule", "Progress"]
        for nav_text in nav_options:
            try:
                nav_element = driver.find_element(
                    By.XPATH, f"//a[contains(text(), '{nav_text}')]")
                driver.execute_script("arguments[0].click();", nav_element)
                time.sleep(4)
                break
            except NoSuchElementException:
                continue

        # Scroll and take screenshot
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)

        screenshot_path = f"{client_name.replace(' ', '_')}_program.png"
        driver.save_screenshot(screenshot_path)

        # Analyze with AI
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        analysis_prompt = f"""
        Analyze this Trainerize page for {client_name}.
        
        Extract and report:
        1. All workout names/titles visible in their program
        2. Any scheduled workouts or sessions
        3. Recent workout history if visible
        4. Exercise names from any visible workouts
        5. Sets, reps, weights if visible
        
        Focus on concrete, specific information you can see.
        This is REAL data from an actual Trainerize account.
        """

        response = model.generate_content([
            analysis_prompt,
            {"inline_data": {"mime_type": "image/png", "data": image_data}}
        ])

        # Clean up
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

        return response.text

    except Exception as e:
        return f"Error extracting program data: {str(e)}"


def run_real_extraction():
    """Run the real client data extraction"""
    print("🎯 READY TO EXTRACT REAL CLIENT DATA")
    print("Target: Alice Forster, Nicole Lynch, Sarika Ramani")

    confirm = input(
        "\nPress Enter to extract REAL data from your Trainerize: ")

    print("\n🚀 STARTING REAL EXTRACTION...")
    result = asyncio.run(extract_real_client_data())

    print("\n" + "=" * 60)
    if result["success"]:
        print("🎉 REAL DATA EXTRACTION SUCCESSFUL!")
        print(f"🎯 Successfully accessed: {result['client_accessed']}")
        print("💡 'FULL CONTROL' PROVEN WITH ACTUAL CLIENT DATA!")
    else:
        print("❌ Extraction issue:")
        print(f"   Error: {result['error']}")
        if 'clients_found' in result:
            print("\n📋 Clients visible on page:")
            print(result['clients_found'])
    print("=" * 60)


if __name__ == "__main__":
    run_real_extraction()
