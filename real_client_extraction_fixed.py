#!/usr/bin/env python3
"""
FIXED REAL CLIENT EXTRACTION - Alice Forster, Nicole Lynch, Sarika Ramani
Fixed navigation after login to find the correct clients page
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
    print("🎯 REAL CLIENT EXTRACTION (FIXED)")
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
        print("\n🚀 STEP 1: Launching Chrome...")

        # Optimized Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = ChromeService(executable_path=chromedriver_path)

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

        # Second page
        print("   → Completing login...")

        # Email field
        email_field2 = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#emailInput")))
        email_field2.clear()
        email_field2.send_keys(username)

        # Password field
        password_field = driver.find_element(By.CSS_SELECTOR, "#passInput")
        password_field.clear()
        password_field.send_keys(password)

        # Submit button
        submit_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
        driver.execute_script("arguments[0].click();", submit_button)

        # Wait for login completion
        time.sleep(10)

        print("✅ Login completed")

        print("\n🔍 STEP 3: Finding dashboard and clients...")

        # Take screenshot of current page to see where we landed
        driver.save_screenshot("current_page.png")

        # Let's analyze where we are first
        with open("current_page.png", 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        navigation_prompt = """
        Analyze this Trainerize page after login.
        
        I need to navigate to the clients list. Look for:
        1. Any navigation menu items like "Clients", "Members", "My Clients"
        2. Sidebar navigation options
        3. Main menu items
        4. Dashboard tiles or buttons that lead to clients
        
        Tell me exactly what navigation options you can see for getting to clients.
        """

        nav_response = model.generate_content([
            navigation_prompt,
            {"inline_data": {"mime_type": "image/png", "data": image_data}}
        ])

        print("✅ Navigation analysis completed!")
        print("\n📍 CURRENT PAGE ANALYSIS:")
        print("-" * 40)
        print(nav_response.text)
        print("-" * 40)

        # Try multiple navigation strategies
        print("\n🧭 STEP 4: Attempting to navigate to clients...")

        # Strategy 1: Look for Clients in main navigation
        nav_attempts = [
            "//a[contains(text(), 'Clients')]",
            "//a[contains(text(), 'Members')]",
            "//a[contains(text(), 'My Clients')]",
            "//div[contains(text(), 'Clients')]",
            "//span[contains(text(), 'Clients')]",
            "//button[contains(text(), 'Clients')]"
        ]

        clients_found = False
        for nav_xpath in nav_attempts:
            try:
                clients_link = wait.until(
                    EC.element_to_be_clickable((By.XPATH, nav_xpath)))
                driver.execute_script("arguments[0].click();", clients_link)
                time.sleep(5)
                clients_found = True
                print(f"✅ Found clients navigation: {nav_xpath}")
                break
            except TimeoutException:
                continue

        # Strategy 2: Try direct URL if navigation fails
        if not clients_found:
            print("   → Trying direct URL navigation...")
            potential_urls = [
                "https://www.trainerize.com/app/trainer/clients",
                "https://www.trainerize.com/app/clients",
                "https://www.trainerize.com/trainer/clients",
                "https://www.trainerize.com/dashboard/clients"
            ]

            for url in potential_urls:
                try:
                    driver.get(url)
                    time.sleep(5)

                    # Check if we're on a valid page (not error page)
                    if "can't find this page" not in driver.page_source.lower():
                        clients_found = True
                        print(f"✅ Successfully navigated to: {url}")
                        break
                except Exception:
                    continue

        if not clients_found:
            print("❌ Could not find clients navigation")
            return {"success": False, "error": "Could not navigate to clients page"}

        # Take screenshot of clients page
        print("\n📸 Taking screenshot of clients page...")
        driver.save_screenshot("clients_page.png")

        # Analyze the clients page
        with open("clients_page.png", 'rb') as f:
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
        3. List ALL client names you can clearly see on this page
        4. Is there a search box or way to filter clients?
        
        Be very specific about what you can actually see.
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

        # Try to find and access one of the target clients
        print("\n👤 STEP 5: Attempting to access client data...")

        # Try each client in order
        target_clients = ["Alice Forster", "Nicole Lynch", "Sarika Ramani"]
        accessed_client = None
        program_data = None

        for client_name in target_clients:
            print(f"   🔍 Looking for {client_name}...")

            client_found = await find_and_click_client(driver, client_name)
            if client_found:
                print(f"✅ Successfully accessed {client_name}'s profile!")
                accessed_client = client_name
                program_data = await extract_client_program_data(driver, model, client_name)
                break
            else:
                print(f"   ❌ Could not find {client_name}")

        # Clean up screenshots
        for file in ["current_page.png", "clients_page.png"]:
            if os.path.exists(file):
                os.remove(file)

        if accessed_client:
            print(f"\n🏆 {accessed_client.upper()}'S REAL PROGRAM DATA:")
            print("=" * 60)
            print(program_data)
            print("=" * 60)

            return {
                "success": True,
                "client_accessed": accessed_client,
                "program_data": program_data,
                "clients_found": response.text
            }
        else:
            return {
                "success": False,
                "error": "Could not access any of the target clients",
                "clients_found": response.text
            }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("\n🧹 Closing browser...")
            driver.quit()


async def find_and_click_client(driver, client_name):
    """Find and click on a specific client with multiple search strategies"""
    try:
        wait = WebDriverWait(driver, 10)

        # Strategy 1: Search box
        search_selectors = [
            "input[placeholder*='Search']",
            "input[type='search']",
            "input[placeholder*='Filter']",
            "input[placeholder*='Find']"
        ]

        for selector in search_selectors:
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, selector)
                search_box.clear()
                search_box.send_keys(client_name)
                time.sleep(3)
                print(f"   ✅ Used search box: {selector}")
                break
            except NoSuchElementException:
                continue

        # Strategy 2: Find client by exact name
        client_selectors = [
            f"//a[contains(text(), '{client_name}')]",
            f"//div[contains(text(), '{client_name}')]",
            f"//span[contains(text(), '{client_name}')]",
            f"//td[contains(text(), '{client_name}')]",
            f"//li[contains(text(), '{client_name}')]"
        ]

        for selector in client_selectors:
            try:
                client_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].click();", client_element)
                time.sleep(4)
                print(f"   ✅ Clicked client using: {selector}")
                return True
            except TimeoutException:
                continue

        # Strategy 3: Try first name only
        first_name = client_name.split()[0]
        for selector in client_selectors:
            try:
                modified_selector = selector.replace(client_name, first_name)
                client_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, modified_selector)))
                driver.execute_script("arguments[0].click();", client_element)
                time.sleep(4)
                print(f"   ✅ Clicked client using first name: {first_name}")
                return True
            except TimeoutException:
                continue

        return False

    except Exception as e:
        print(f"   ❌ Error finding {client_name}: {e}")
        return False


async def extract_client_program_data(driver, model, client_name):
    """Extract comprehensive program data for a client"""
    try:
        print(f"   📊 Extracting {client_name}'s comprehensive data...")

        # Wait for page to load
        time.sleep(3)

        # Navigate through different sections to get comprehensive data
        sections_to_check = [
            ("Program", ["Programs", "Workouts", "Training"]),
            ("Progress", ["Progress", "Stats", "Measurements"]),
            ("Schedule", ["Schedule", "Calendar", "Sessions"]),
            ("Overview", ["Overview", "Dashboard", "Summary"])
        ]

        all_data = []

        for section_name, nav_terms in sections_to_check:
            print(f"     → Checking {section_name} section...")

            # Try to navigate to this section
            section_found = False
            for nav_term in nav_terms:
                try:
                    nav_element = driver.find_element(
                        By.XPATH, f"//a[contains(text(), '{nav_term}')]")
                    driver.execute_script("arguments[0].click();", nav_element)
                    time.sleep(3)
                    section_found = True
                    print(f"       ✅ Found {nav_term} section")
                    break
                except NoSuchElementException:
                    continue

            # Take screenshot and analyze
            screenshot_path = f"{client_name.replace(' ', '_')}_{section_name}.png"
            driver.save_screenshot(screenshot_path)

            # Analyze with AI
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            analysis_prompt = f"""
            Analyze this {section_name} section for {client_name} in Trainerize.
            
            Extract ALL visible information including:
            1. Workout names and programs
            2. Exercise names, sets, reps, weights
            3. Dates and completion status
            4. Progress metrics (weight, measurements, etc.)
            5. Any scheduled sessions or appointments
            6. Notes or comments
            7. Performance data
            
            This is REAL client data. Be thorough and specific.
            Report only what you can clearly see in the image.
            """

            try:
                response = model.generate_content([
                    analysis_prompt,
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ])

                section_data = f"\n--- {section_name.upper()} SECTION ---\n{response.text}\n"
                all_data.append(section_data)

            except Exception as e:
                all_data.append(
                    f"\n--- {section_name.upper()} SECTION ---\nError analyzing: {str(e)}\n")

            # Clean up screenshot
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)

        # Combine all sections
        comprehensive_data = f"""
COMPREHENSIVE REAL DATA FOR {client_name.upper()}
{'=' * 60}
""" + "".join(all_data)

        return comprehensive_data

    except Exception as e:
        return f"Error extracting comprehensive data: {str(e)}"


def run_fixed_extraction():
    """Run the fixed real client data extraction"""
    print("🎯 FIXED REAL CLIENT EXTRACTION")
    print("Target: Alice Forster, Nicole Lynch, Sarika Ramani")

    confirm = input("\nPress Enter to run FIXED extraction: ")

    print("\n🚀 STARTING FIXED EXTRACTION...")
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
    run_fixed_extraction()
