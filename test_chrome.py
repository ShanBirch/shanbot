#!/usr/bin/env python3
"""
Test Chrome and Selenium Setup
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os


def test_chrome_setup():
    print("Testing Chrome and Selenium setup...")

    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless for testing
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Check if Chrome binary exists
    chrome_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome-win64\chrome.exe"
    if os.path.exists(chrome_path):
        print(f"✓ Chrome binary found at: {chrome_path}")
        chrome_options.binary_location = chrome_path
    else:
        print(f"✗ Chrome binary not found at: {chrome_path}")
        print("Using system Chrome...")

    try:
        # Create driver
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✓ Successfully loaded page: {title}")

        # Clean up
        driver.quit()
        print("✓ Chrome test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Chrome test failed: {e}")
        return False


if __name__ == "__main__":
    test_chrome_setup()
