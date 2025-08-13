#!/usr/bin/env python3
"""
ACTUAL TRAINERIZE TEST - REAL SELENIUM AUTOMATION
This will actually log into your Trainerize and get real data
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


async def actual_trainerize_test():
    """
    REAL TEST: Actually log into Trainerize and extract Nicole's data
    """
    print("🔥 ACTUAL TRAINERIZE TEST - REAL AUTOMATION")
    print("=" * 60)
    print("This will ACTUALLY log into your Trainerize account!")
    print("=" * 60)

    # Your real credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

    # Configure Gemini
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

    driver = None

    try:
        print("\n🚀 STEP 1: Launching real Chrome browser...")

        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        chromedriver_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chromedriver-137\chromedriver-win64\chromedriver.exe"
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        print("✅ Chrome browser launched successfully")

        print("\n🔑 STEP 2: Actually logging into Trainerize...")

        # Real login
        driver.get("https://www.trainerize.com/login.aspx")
        wait = WebDriverWait(driver, 30)

        # First page
        print("   → Entering email on first page...")
        email_field = wait.until(
            EC.presence_of_element_located((By.ID, "t_email")))
        email_field.clear()
        email_field.send_keys(username)

        find_button = driver.find_element(
            By.CLASS_NAME, "tz-button--secondary")
        find_button.click()
        time.sleep(5)

        # Second page
        print("   → Completing login...")
        email_field2 = wait.until(
            EC.element_to_be_clickable((By.ID, "emailInput")))
        email_field2.clear()
        email_field2.send_keys(username)

        password_field = driver.find_element(By.ID, "passInput")
        password_field.clear()
        password_field.send_keys(password)

        signin_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='signIn-button']")))
        driver.execute_script("arguments[0].click();", signin_button)

        time.sleep(10)

        current_url = driver.current_url
        if "dashboard" in current_url.lower() or "clients" in current_url.lower():
            print("✅ Successfully logged into Trainerize!")
        else:
            print(f"❌ Login may have failed - URL: {current_url}")
            return {"success": False, "error": "Login failed"}

        print("\n🔍 STEP 3: Finding your real clients...")

        # Navigate to clients
        driver.get("https://www.trainerize.com/app/trainer/clients")
        time.sleep(5)

        # Take screenshot of client list
        driver.save_screenshot("real_client_list.png")

        # Use AI to analyze client list
        with open("real_client_list.png", 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        client_analysis_prompt = """
        Analyze this Trainerize clients page. 
        
        List all client names you can see on this page.
        Look for:
        - Client names in the list
        - Any search results
        - Profile names or cards
        
        Just list the names you can clearly see.
        """

        response = model.generate_content([
            client_analysis_prompt,
            {"inline_data": {"mime_type": "image/png", "data": image_data}}
        ])

        print("✅ Client list analyzed!")
        print("\n📋 REAL CLIENTS FOUND:")
        print("-" * 30)
        print(response.text)

        # Clean up
        if os.path.exists("real_client_list.png"):
            os.remove("real_client_list.png")

        print("\n🎯 REAL TEST RESULTS:")
        print("✅ Successfully logged into your actual Trainerize")
        print("✅ Accessed your real client list")
        print("✅ Used AI to analyze actual client data")
        print("✅ Proved the automation framework works!")

        return {
            "success": True,
            "clients_found": response.text,
            "proof": "Real Trainerize access achieved"
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"success": False, "error": str(e)}

    finally:
        if driver:
            print("\n🧹 Closing browser...")
            driver.quit()


def run_actual_test():
    """Run the actual test"""
    print("🎯 READY TO RUN ACTUAL TRAINERIZE TEST")
    print("This will really log into your account!")

    confirm = input("\nPress Enter to run ACTUAL test: ")

    result = asyncio.run(actual_trainerize_test())

    if result["success"]:
        print("\n🎉 ACTUAL TEST SUCCESSFUL!")
        print("🎯 'FULL CONTROL' PROVEN!")
    else:
        print(f"\n❌ Test failed: {result['error']}")


if __name__ == "__main__":
    run_actual_test()
