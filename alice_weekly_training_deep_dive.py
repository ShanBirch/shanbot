#!/usr/bin/env python3
"""
ALICE FORSTER DEEP DIVE - Weekly Training Analysis
Goes deep into Alice's profile to find:
1. How many times she trained this week
2. What the specific workout names were
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


async def deep_dive_alice_training():
    """
    Deep dive into Alice Forster's training this week
    """
    print("🎯 ALICE FORSTER - WEEKLY TRAINING DEEP DIVE")
    print("=" * 55)
    print("Target: Find this week's training sessions and workout names")
    print("=" * 55)

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
        email_field2 = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#emailInput")))
        email_field2.clear()
        email_field2.send_keys(username)

        password_field = driver.find_element(By.CSS_SELECTOR, "#passInput")
        password_field.clear()
        password_field.send_keys(password)

        submit_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(10)
        print("✅ Login completed")

        print("\n🔍 STEP 3: Navigating to Alice Forster...")

        # Navigate to clients and find Alice
        clients_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'Clients')]")))
        driver.execute_script("arguments[0].click();", clients_link)
        time.sleep(5)

        # Search for Alice
        search_box = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder*='Search']")
        search_box.clear()
        search_box.send_keys("Alice Forster")
        time.sleep(3)

        # Click on Alice
        alice_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Alice Forster')]")))
        driver.execute_script("arguments[0].click();", alice_link)
        time.sleep(5)

        print("✅ Successfully accessed Alice Forster's profile")

        print("\n🏋️ STEP 4: Deep diving into workout details...")

        # Strategy 1: Look for workout history/schedule sections
        workout_sections = await explore_workout_sections(driver, model, wait)

        print("\n🔍 STEP 5: Analyzing this week's training data...")

        # Combine all findings
        training_analysis = await analyze_weekly_training(driver, model, workout_sections)

        print("\n🏆 ALICE'S WEEKLY TRAINING RESULTS:")
        print("=" * 60)
        print(training_analysis)
        print("=" * 60)

        return {
            "success": True,
            "client": "Alice Forster",
            "weekly_training": training_analysis
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("\n🧹 Closing browser...")
            driver.quit()


async def explore_workout_sections(driver, model, wait):
    """Explore different sections to find workout details"""
    print("   📊 Exploring workout sections...")

    sections_explored = []

    # Navigation options to try
    nav_options = [
        ("Workouts", ["Workouts", "Training", "Program"]),
        ("Schedule", ["Schedule", "Calendar"]),
        ("Progress", ["Progress", "History"]),
        ("Activity", ["Activity", "Feed"])
    ]

    for section_name, nav_terms in nav_options:
        print(f"     → Exploring {section_name}...")

        # Try to navigate to section
        section_accessed = False
        for nav_term in nav_terms:
            try:
                nav_element = driver.find_element(
                    By.XPATH, f"//a[contains(text(), '{nav_term}')]")
                driver.execute_script("arguments[0].click();", nav_element)
                time.sleep(4)
                section_accessed = True
                print(f"       ✅ Accessed {nav_term} section")
                break
            except NoSuchElementException:
                continue

        if section_accessed:
            # Take screenshot and analyze
            screenshot_path = f"alice_{section_name.lower()}_section.png"
            driver.save_screenshot(screenshot_path)

            # Analyze for workout information
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            analysis_prompt = f"""
            Analyze this {section_name} section for Alice Forster.
            
            I'm specifically looking for:
            1. Individual workout sessions from THIS WEEK
            2. Workout names/titles (like "Upper Body Strength", "Leg Day", etc.)
            3. Completion status (completed/scheduled/missed)
            4. Dates of workouts this week
            5. Any weekly summary or count
            
            Focus on THIS WEEK's data. Be very specific about:
            - How many workouts are shown for this week
            - What are the exact names of the workouts
            - Which ones are completed vs scheduled
            
            This is real data extraction - be precise!
            """

            try:
                response = model.generate_content([
                    analysis_prompt,
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ])

                section_data = {
                    "section": section_name,
                    "analysis": response.text,
                    "screenshot": screenshot_path
                }
                sections_explored.append(section_data)

                print(f"       📝 {section_name} analysis completed")

            except Exception as e:
                print(f"       ❌ Error analyzing {section_name}: {e}")

        # Try to scroll down to see more content
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

    return sections_explored


async def analyze_weekly_training(driver, model, sections_explored):
    """Analyze all sections to determine weekly training"""
    print("   🧮 Synthesizing weekly training data...")

    # Combine all section analyses
    all_analyses = ""
    for section in sections_explored:
        all_analyses += f"\n--- {section['section'].upper()} SECTION ---\n"
        all_analyses += section['analysis']
        all_analyses += "\n"

    # Final synthesis prompt
    synthesis_prompt = f"""
    Based on all the section analyses below, provide a definitive answer:

    QUESTION 1: How many times did Alice Forster train THIS WEEK?
    QUESTION 2: What were the exact names of the workouts she did THIS WEEK?

    Analyze all the data below and give me:
    1. A specific number: "Alice trained X times this week"
    2. A list of workout names: "Workout names: [list]"
    3. Completion status for each workout

    Be very specific and only count COMPLETED workouts from THIS WEEK.

    SECTION ANALYSES:
    {all_analyses}

    FINAL ANSWER FORMAT:
    - Training Sessions This Week: [NUMBER]
    - Completed Workouts: [LIST WITH NAMES]
    - Status Details: [COMPLETION INFO]
    """

    try:
        synthesis_response = model.generate_content(synthesis_prompt)

        # Clean up screenshots
        for section in sections_explored:
            if os.path.exists(section['screenshot']):
                os.remove(section['screenshot'])

        return synthesis_response.text

    except Exception as e:
        return f"Error synthesizing data: {str(e)}"


def run_alice_deep_dive():
    """Run Alice's weekly training deep dive"""
    print("🎯 ALICE FORSTER WEEKLY TRAINING DEEP DIVE")
    print("Going deep into her profile to find this week's training details...")

    confirm = input("\nPress Enter to start deep dive: ")

    print("\n🚀 STARTING DEEP DIVE...")
    result = asyncio.run(deep_dive_alice_training())

    print("\n" + "=" * 60)
    if result["success"]:
        print("🎉 DEEP DIVE SUCCESSFUL!")
        print("📊 ALICE'S WEEKLY TRAINING EXTRACTED!")
    else:
        print("❌ Deep dive issue:")
        print(f"   Error: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    run_alice_deep_dive()
