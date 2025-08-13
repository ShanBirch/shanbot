#!/usr/bin/env python3
"""
Manual Training Program Click Helper
====================================

This script helps manually click the Training Program link if the automation gets stuck.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time


def find_existing_chrome_session():
    """Try to connect to existing Chrome session"""
    try:
        # Try to connect to existing session on common debug ports
        for port in range(9222, 9232):
            try:
                options = Options()
                options.add_experimental_option(
                    "debuggerAddress", f"localhost:{port}")
                driver = webdriver.Chrome(options=options)
                print(f"Connected to existing Chrome session on port {port}")
                return driver
            except:
                continue
        return None
    except Exception as e:
        print(f"Could not connect to existing Chrome session: {e}")
        return None


def click_training_program():
    """Click the Training Program link"""
    driver = find_existing_chrome_session()

    if not driver:
        print("Could not connect to existing Chrome session")
        print("The automation script should handle this automatically")
        return

    try:
        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        # Wait for and click Training Program
        print("Looking for Training Program link...")

        training_program_selectors = [
            "//a[@data-testid='leftNavMenu-item-trainingProgram']",
            "//a[contains(@title, 'Training Program')]",
            "//a[contains(text(), 'Training Program')]",
            "//a[@id='nav_training_program']"
        ]

        for i, selector in enumerate(training_program_selectors, 1):
            try:
                print(f"Trying selector {i}: {selector}")
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"Found Training Program link with selector {i}")
                element.click()
                print("Successfully clicked Training Program!")
                time.sleep(3)
                print("New URL:", driver.current_url)
                return True
            except Exception as e:
                print(f"Selector {i} failed: {e}")
                continue

        print("Could not find Training Program link with any selector")

        # Try to find all navigation links for debugging
        print("\nAvailable navigation links:")
        nav_links = driver.find_elements(
            By.XPATH, "//nav//a | //div[contains(@class, 'nav')]//a")
        for link in nav_links[:10]:  # Show first 10
            text = link.text.strip()
            href = link.get_attribute('href')
            if text:
                print(f"  - {text}: {href}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Don't close the driver as it's part of the main automation
        print("Helper script completed")


if __name__ == "__main__":
    click_training_program()
