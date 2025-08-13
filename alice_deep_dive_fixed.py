#!/usr/bin/env python3
"""
ALICE FORSTER DEEP DIVE - FIXED
Clicks OPEN button to access full dashboard, then navigates through tabs
to find this week's training sessions and workout names
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


async def alice_training_deep_dive_fixed():
    """
    FIXED: Click OPEN button and navigate through Alice's dashboard tabs
    """
    print("🎯 ALICE FORSTER - FIXED DEEP DIVE")
    print("=" * 50)
    print("Strategy: OPEN button → Dashboard → Calendar/Program tabs")
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

        print("✅ Accessed Alice Forster's profile")

        print("\n🚪 STEP 4: Clicking OPEN button to access full dashboard...")

        # Look for and click the OPEN button
        open_button_found = False
        open_selectors = [
            "//button[contains(text(), 'OPEN')]",
            "//a[contains(text(), 'OPEN')]",
            "//div[contains(text(), 'OPEN')]",
            "button[data-testid*='open']",
            "button[class*='open']"
        ]

        for selector in open_selectors:
            try:
                if selector.startswith("//"):
                    open_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    open_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                driver.execute_script("arguments[0].click();", open_button)
                time.sleep(5)
                open_button_found = True
                print(f"✅ Clicked OPEN button using: {selector}")
                break
            except TimeoutException:
                continue

        if not open_button_found:
            print("❌ Could not find OPEN button, trying to proceed anyway...")

        print("\n📊 STEP 5: Navigating through dashboard tabs...")

        # Now navigate through the dashboard tabs to find workout details
        dashboard_data = await explore_dashboard_tabs(driver, model, wait)

        print("\n🔍 STEP 6: Analyzing Alice's weekly training...")

        # Synthesize the findings
        weekly_training = await synthesize_weekly_training(dashboard_data, model)

        print("\n🏆 ALICE'S WEEKLY TRAINING RESULTS:")
        print("=" * 60)
        print(weekly_training)
        print("=" * 60)

        return {
            "success": True,
            "client": "Alice Forster",
            "weekly_training": weekly_training
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("\n🧹 Closing browser...")
            driver.quit()


async def explore_dashboard_tabs(driver, model, wait):
    """Explore the dashboard tabs to find workout details"""
    print("   🗂️ Exploring dashboard tabs...")

    dashboard_data = []

    # Dashboard tabs to explore
    tabs_to_check = [
        ("Calendar", ["Calendar", "Schedule"]),
        ("Program", ["Program", "Workouts", "Training"]),
        ("Progress", ["Progress", "History"]),
        ("Activity", ["Activity", "Feed", "Log"])
    ]

    for tab_name, tab_selectors in tabs_to_check:
        print(f"     → Exploring {tab_name} tab...")

        # Try to click on the tab
        tab_clicked = False
        for selector_text in tab_selectors:
            try:
                tab_element = driver.find_element(
                    By.XPATH, f"//a[contains(text(), '{selector_text}')]")
                driver.execute_script("arguments[0].click();", tab_element)
                time.sleep(4)
                tab_clicked = True
                print(f"       ✅ Clicked {selector_text} tab")
                break
            except NoSuchElementException:
                try:
                    tab_element = driver.find_element(
                        By.XPATH, f"//button[contains(text(), '{selector_text}')]")
                    driver.execute_script("arguments[0].click();", tab_element)
                    time.sleep(4)
                    tab_clicked = True
                    print(f"       ✅ Clicked {selector_text} button")
                    break
                except NoSuchElementException:
                    continue

        if tab_clicked:
            # Scroll to see all content
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            # Take screenshot
            screenshot_path = f"alice_{tab_name.lower()}_tab.png"
            driver.save_screenshot(screenshot_path)

            # Analyze with AI
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            analysis_prompt = f"""
            Analyze this {tab_name} tab for Alice Forster in Trainerize.
            
            I need to find out specifically:
            1. How many times Alice trained THIS WEEK?
            2. What were the exact names of the workouts she did THIS WEEK?
            
            Look for:
            - Individual workout sessions with specific names
            - Completion dates from this week
            - Workout titles like "Upper Body", "Lower Body", "Cardio", etc.
            - Any calendar entries or scheduled workouts
            - Completion status (completed vs missed)
            
            Be very specific about:
            - The exact count of completed workouts this week
            - The precise names/titles of each workout
            - The dates they were completed
            
            This is real client data - be accurate!
            """

            try:
                response = model.generate_content([
                    analysis_prompt,
                    {"inline_data": {"mime_type": "image/png", "data": image_data}}
                ])

                tab_data = {
                    "tab": tab_name,
                    "analysis": response.text,
                    "screenshot": screenshot_path
                }
                dashboard_data.append(tab_data)

                print(f"       📝 {tab_name} analysis completed")

            except Exception as e:
                print(f"       ❌ Error analyzing {tab_name}: {e}")
        else:
            print(f"       ❌ Could not access {tab_name} tab")

    return dashboard_data


async def synthesize_weekly_training(dashboard_data, model):
    """Synthesize all dashboard data to answer the specific questions"""
    print("   🧮 Synthesizing training data...")

    # Combine all analyses
    all_data = ""
    for tab in dashboard_data:
        all_data += f"\n--- {tab['tab'].upper()} TAB ---\n"
        all_data += tab['analysis']
        all_data += "\n"

    # Final answer prompt
    final_prompt = f"""
    Based on all the dashboard tab analyses below, provide the definitive answers:

    QUESTION 1: How many times did Alice Forster train THIS WEEK?
    QUESTION 2: What were the exact names of the workouts she did THIS WEEK?

    Look through all the data and provide:
    1. A specific number: "Alice trained [X] times this week"
    2. A list of workout names: "Workout names: [exact titles]"
    3. Which days she trained: "Training days: [dates]"

    Only count COMPLETED workouts from THIS WEEK (not scheduled/missed ones).

    ALL DASHBOARD DATA:
    {all_data}

    FINAL ANSWER (be very specific):
    """

    try:
        final_response = model.generate_content(final_prompt)

        # Clean up screenshots
        for tab in dashboard_data:
            if os.path.exists(tab['screenshot']):
                os.remove(tab['screenshot'])

        return final_response.text

    except Exception as e:
        return f"Error synthesizing final answer: {str(e)}"


def run_alice_fixed_dive():
    """Run the fixed Alice deep dive"""
    print("🎯 ALICE FORSTER - FIXED DEEP DIVE")
    print("Will click OPEN button and explore dashboard tabs")

    confirm = input("\nPress Enter to start FIXED deep dive: ")

    print("\n🚀 STARTING FIXED DEEP DIVE...")
    result = asyncio.run(alice_training_deep_dive_fixed())

    print("\n" + "=" * 60)
    if result["success"]:
        print("🎉 FIXED DEEP DIVE SUCCESSFUL!")
        print("📊 ALICE'S WEEKLY TRAINING DETAILS EXTRACTED!")
    else:
        print("❌ Fixed deep dive issue:")
        print(f"   Error: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    run_alice_fixed_dive()
