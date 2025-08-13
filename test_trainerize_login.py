#!/usr/bin/env python3
"""
Simple test script to verify Trainerize login and navigation
"""

import logging
import time
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_trainerize_login.log'),
        logging.StreamHandler()
    ]
)


def test_trainerize_login():
    """Test basic Trainerize login and navigation"""

    automation = None
    try:
        logging.info("=== TESTING TRAINERIZE LOGIN ===")

        # Initialize automation
        logging.info("Initializing TrainerizeAutomation...")
        automation = TrainerizeAutomation()

        # Test login
        logging.info("Attempting to login to Trainerize...")
        import os
        username = os.getenv('TRAINERIZE_USERNAME',
                             'Shannonbirch@cocospersonaltraining.com')
        password = os.getenv('TRAINERIZE_PASSWORD', 'cyywp7nyk2')

        # Let user know what credentials we're using
        logging.info(f"Using username: {username}")

        if not automation.login(username, password):
            logging.error("❌ LOGIN FAILED")
            return False

        logging.info("✅ LOGIN SUCCESSFUL")

        # Test navigation to clients
        logging.info("Testing navigation to clients page...")
        time.sleep(3)  # Wait for page to load

        # Check current URL
        current_url = automation.driver.current_url
        logging.info(f"Current URL after login: {current_url}")

        # Try to navigate to clients
        try:
            clients_link = automation.driver.find_element(
                automation.By.XPATH, "//a[@href='/clients' or contains(@href, 'clients')]"
            )
            logging.info(
                f"Found clients link: {clients_link.get_attribute('href')}")
            clients_link.click()
            time.sleep(3)

            new_url = automation.driver.current_url
            logging.info(f"URL after clicking clients: {new_url}")

            if 'clients' in new_url.lower():
                logging.info("✅ SUCCESSFULLY NAVIGATED TO CLIENTS PAGE")
                return True
            else:
                logging.error("❌ FAILED TO NAVIGATE TO CLIENTS PAGE")
                return False

        except Exception as e:
            logging.error(f"❌ ERROR FINDING CLIENTS LINK: {e}")
            return False

    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR: {e}")
        return False

    finally:
        if automation:
            try:
                automation.cleanup()
                logging.info("✅ CLEANUP COMPLETED")
            except:
                logging.warning("⚠️ CLEANUP HAD ISSUES")


if __name__ == "__main__":
    success = test_trainerize_login()
    if success:
        print("\n🎉 TEST PASSED: Trainerize login and navigation working!")
    else:
        print("\n❌ TEST FAILED: Issues with Trainerize login/navigation")
