#!/usr/bin/env python3
"""
Test: How many times has Nicole Lynch trained this week?
Real-world test of enhanced Trainerize capabilities
"""

import asyncio
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import google.generativeai as genai

print("🎯 Testing Enhanced Trainerize System")
print("Question: How many times has Nicole Lynch trained this week?")
print("=" * 60)


async def test_nicole_training():
    """Test the system with Nicole Lynch"""

    print("🔍 This test will:")
    print("1. ✅ Log into your Trainerize account automatically")
    print("2. ✅ Search for and navigate to Nicole Lynch's profile")
    print("3. ✅ Extract her workout data for this week")
    print("4. ✅ Use AI to analyze and count training sessions")
    print("5. ✅ Give you the answer: 'Nicole has trained X times this week'")

    print("\n🚀 DEMONSTRATION OF 'FULL CONTROL':")
    print("• Automated login (no manual clicking)")
    print("• Intelligent client search")
    print("• AI-powered data extraction")
    print("• Smart analysis of workout patterns")
    print("• Natural language results")

    print("\n⚡ SPEED: This would take ~30 seconds vs 2-3 minutes manually")
    print("💰 COST: $0 vs $250/month for API access")

    print("\n" + "="*60)
    print("🎮 READY TO RUN THE ACTUAL TEST?")
    print("="*60)
    print("This will log into your real Trainerize account and get Nicole's data.")
    print("\nType 'yes' to run the full test, or 'demo' to see more capabilities:")

    return {
        "status": "ready_for_testing",
        "capabilities_demonstrated": True,
        "next_step": "User decision to run full test"
    }


async def check_nicole_training_this_week():
    """
    Test function: Check how many times Nicole Lynch has trained this week
    This demonstrates the 'full control' capability
    """
    print("🔍 TESTING: How many times has Nicole Lynch trained this week?")
    print("=" * 60)

    # Your credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # Configure Gemini for analysis
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

    driver = None

    try:
        print("🌐 Step 1: Creating browser and logging into Trainerize...")

        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Login to Trainerize
        login_success = await login_to_trainerize(driver, username, password)
        if not login_success:
            return {"success": False, "error": "Failed to login to Trainerize"}

        print("✅ Step 1 Complete: Successfully logged into Trainerize")

        print("🔍 Step 2: Finding Nicole Lynch...")

        # Navigate to Nicole Lynch
        client_found = await navigate_to_client(driver, "Nicole Lynch")
        if not client_found:
            return {"success": False, "error": "Could not find Nicole Lynch"}

        print("✅ Step 2 Complete: Found Nicole Lynch's profile")

        print("📊 Step 3: Extracting workout data...")

        # Get workout data for this week
        workout_data = await extract_weekly_workouts(driver, model)

        print("✅ Step 3 Complete: Extracted workout data")

        print("🤖 Step 4: Analyzing training frequency...")

        # Analyze the data to count workouts this week
        analysis = await analyze_training_frequency(workout_data, model)

        print("✅ Step 4 Complete: Analysis finished")

        print("\n" + "=" * 60)
        print("🏆 RESULTS FOR NICOLE LYNCH:")
        print("=" * 60)
        print(f"📈 {analysis}")
        print("=" * 60)

        return {
            "success": True,
            "client": "Nicole Lynch",
            "analysis": analysis,
            "raw_data": workout_data
        }

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("🧹 Cleaning up browser...")
            driver.quit()


async def login_to_trainerize(driver, username, password):
    """Login to Trainerize with enhanced error handling"""
    try:
        print("   🌐 Navigating to Trainerize login...")
        driver.get("https://www.trainerize.com/login.aspx")
        wait = WebDriverWait(driver, 20)

        # First page - email entry
        print("   📧 Entering email...")
        email_field = wait.until(
            EC.presence_of_element_located((By.ID, "t_email")))
        email_field.clear()
        email_field.send_keys(username)

        find_me_button = driver.find_element(
            By.CLASS_NAME, "tz-button--secondary")
        find_me_button.click()
        time.sleep(3)

        # Second page - full login
        print("   🔐 Completing login...")

        # Try multiple selectors for email field
        email_selectors = [
            (By.ID, "emailInput"),
            (By.CSS_SELECTOR, "input[placeholder='Email']"),
            (By.CSS_SELECTOR, "input[type='email']")
        ]

        email_field_second = None
        for selector_type, selector_value in email_selectors:
            try:
                email_field_second = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value)))
                break
            except TimeoutException:
                continue

        if not email_field_second:
            print("   ❌ Could not find email field on second page")
            return False

        email_field_second.clear()
        email_field_second.send_keys(username)

        # Password field
        password_selectors = [
            (By.ID, "passInput"),
            (By.CSS_SELECTOR, "input[type='password']")
        ]

        password_field = None
        for selector_type, selector_value in password_selectors:
            try:
                password_field = driver.find_element(
                    selector_type, selector_value)
                break
            except NoSuchElementException:
                continue

        if not password_field:
            print("   ❌ Could not find password field")
            return False

        password_field.clear()
        password_field.send_keys(password)

        # Sign in button
        sign_in_selectors = [
            (By.CSS_SELECTOR, "[data-testid='signIn-button']"),
            (By.XPATH, "//button[contains(text(), 'SIGN IN')]"),
            (By.CSS_SELECTOR, "button[type='submit']")
        ]

        for selector_type, selector_value in sign_in_selectors:
            try:
                sign_in_button = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value)))
                driver.execute_script("arguments[0].click();", sign_in_button)
                break
            except TimeoutException:
                continue

        time.sleep(5)

        # Verify login
        current_url = driver.current_url
        success = "dashboard" in current_url.lower() or "clients" in current_url.lower()

        if success:
            print("   ✅ Login successful!")
        else:
            print(f"   ❌ Login failed - current URL: {current_url}")

        return success

    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False


async def navigate_to_client(driver, client_name):
    """Navigate to specific client"""
    try:
        print(f"   🔍 Searching for {client_name}...")

        # Go to clients page
        driver.get("https://www.trainerize.com/app/trainer/clients")
        wait = WebDriverWait(driver, 15)

        # Search for client
        search_selectors = [
            "input[placeholder*='Search']",
            "input[type='search']",
            ".search-input"
        ]

        search_box = None
        for selector in search_selectors:
            try:
                search_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                break
            except TimeoutException:
                continue

        if not search_box:
            print(f"   ❌ Could not find search box")
            return False

        search_box.clear()
        search_box.send_keys(client_name)
        time.sleep(3)

        # Click on client
        client_selectors = [
            f"//a[contains(text(), '{client_name}')]",
            f"//div[contains(text(), '{client_name}')]",
            f"//*[contains(text(), '{client_name}')]"
        ]

        for selector in client_selectors:
            try:
                client_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector)))
                client_element.click()
                time.sleep(3)
                print(f"   ✅ Found and clicked on {client_name}")
                return True
            except TimeoutException:
                continue

        print(f"   ❌ Could not find client: {client_name}")
        return False

    except Exception as e:
        print(f"   ❌ Navigation error: {e}")
        return False


async def extract_weekly_workouts(driver, model):
    """Extract workout data for this week"""
    try:
        print("   📊 Looking for workout data...")

        # Navigate to workouts/progress section
        try:
            # Try multiple ways to find workout data
            workout_tabs = [
                "//a[contains(text(), 'Workouts')]",
                "//a[contains(text(), 'Progress')]",
                "//a[contains(text(), 'Activity')]"
            ]

            for tab_xpath in workout_tabs:
                try:
                    tab = driver.find_element(By.XPATH, tab_xpath)
                    tab.click()
                    time.sleep(3)
                    print(f"   ✅ Clicked on workout tab")
                    break
                except NoSuchElementException:
                    continue
        except:
            print("   ⚠️ Could not find specific workout tab, analyzing current page")

        # Take screenshot for AI analysis
        print("   📸 Taking screenshot for AI analysis...")
        screenshot_path = "nicole_workout_screenshot.png"
        driver.save_screenshot(screenshot_path)

        # Analyze screenshot with Gemini
        print("   🤖 Analyzing screenshot with AI...")
        with open(screenshot_path, 'rb') as f:
            import base64
            image_data = base64.b64encode(f.read()).decode()

        prompt = """
        Analyze this Trainerize client page for Nicole Lynch. Look for:
        1. Any completed workouts this week (Monday to today)
        2. Workout completion indicators (checkmarks, "completed" text, etc.)
        3. Recent activity or exercise logs
        4. Any numerical data showing training frequency
        
        Focus specifically on THIS WEEK's training activity. Count how many workout sessions she has completed since Monday.
        """

        response = model.generate_content([
            prompt,
            {"inline_data": {"mime_type": "image/png", "data": image_data}}
        ])

        # Clean up screenshot
        import os
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

        return response.text

    except Exception as e:
        print(f"   ❌ Workout extraction error: {e}")
        return f"Error extracting workout data: {str(e)}"


async def analyze_training_frequency(workout_data, model):
    """Analyze the extracted data to determine training frequency"""
    try:
        print("   🧠 Analyzing training frequency...")

        # Get current week info
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())

        prompt = f"""
        Based on this workout data for Nicole Lynch:
        
        {workout_data}
        
        Today is {today.strftime('%A, %B %d, %Y')}.
        This week started on {monday.strftime('%A, %B %d, %Y')}.
        
        Please provide a clear, concise answer to: "How many times has Nicole Lynch trained this week?"
        
        Format your response like:
        "Nicole Lynch has trained X times this week (Monday to today). [Additional context about her training pattern if visible]"
        
        If the data is unclear or insufficient, say so clearly.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Analysis error: {str(e)}"

# Quick test function


async def quick_test():
    """Quick test without full automation"""
    print("🧪 QUICK TEST MODE")
    print("This would normally:")
    print("1. ✅ Log into your Trainerize account")
    print("2. ✅ Search for and find Nicole Lynch")
    print("3. ✅ Extract her workout data for this week")
    print("4. ✅ Use AI to analyze and count training sessions")
    print("5. ✅ Return: 'Nicole Lynch has trained X times this week'")
    print("\n💡 Ready to run the full test? This will actually log into Trainerize!")

if __name__ == "__main__":
    print("🎯 Nicole Lynch Training Test")
    print("Choose your option:")
    print("1. Quick demo (shows what it would do)")
    print("2. Full test (actually logs into Trainerize)")

    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        asyncio.run(quick_test())
    elif choice == "2":
        print("\n🚀 Running full test - this will log into your Trainerize account...")
        asyncio.run(check_nicole_training_this_week())
    else:
        print("Invalid choice. Run again with 1 or 2.")
