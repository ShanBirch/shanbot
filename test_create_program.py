from pe import TrainerizeAutomation
import time
import logging
import os

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_create_program.log"),
        logging.StreamHandler()
    ]
)


def test_create_program():
    logging.info("=== STARTING TEST_CREATE_PROGRAM ===")

    # Make sure screenshots directory exists
    os.makedirs("debug_screenshots", exist_ok=True)

    # Initialize TrainerizeAutomation
    bot = TrainerizeAutomation()

    try:
        # Login
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        logging.info("Logging in...")
        login_success = bot.login(username, password)
        bot.driver.save_screenshot("debug_screenshots/after_login.png")

        if not login_success:
            logging.error("Login failed")
            return

        logging.info("Login successful")

        # Handle notification popup
        bot.handle_notification_popup()
        bot.driver.save_screenshot(
            "debug_screenshots/after_notification_popup.png")

        # Add new client
        logging.info("Adding new test client...")
        email = "test_client@example.com"
        first_name = "Test"
        last_name = "Client"

        client_added = bot.add_new_client(email, first_name, last_name)
        bot.driver.save_screenshot("debug_screenshots/after_add_client.png")

        if not client_added:
            logging.error("Failed to add client")
            return

        logging.info("Client added successfully")

        # Navigate to Training Program
        logging.info("Navigating to Training Program tab...")
        time.sleep(5)  # Extra wait for page to stabilize

        if not bot.navigate_to_training_program():
            logging.error("Failed to navigate to Training Program tab")
            return

        bot.driver.save_screenshot(
            "debug_screenshots/training_program_tab.png")
        logging.info("Successfully navigated to Training Program tab")

        # Define a simple chest day workout
        chest_exercises = [
            {'name': 'Barbell Bench Press', 'sets': '3', 'reps': '10'},
            {'name': 'Incline Dumbbell Press', 'sets': '3', 'reps': '10'}
        ]

        # Attempt to create program with EXTRA LONG timeouts
        # Modify the WebDriverWait timeout
        bot.wait._timeout = 60  # Increase timeout to 60 seconds

        logging.info("Attempting to create program with 60-second timeout...")
        program_name = "Test Program"

        # Take screenshot before starting
        bot.driver.save_screenshot(
            "debug_screenshots/before_create_program.png")

        # Test if '+ Add next' button is visible and clickable
        try:
            logging.info("Checking if '+ Add next' button exists...")
            add_next_button = bot.driver.find_elements(
                "css selector", "p.tz-p.color--blue.clickable")
            if add_next_button:
                logging.info(
                    f"Found {len(add_next_button)} matching elements: {[e.text for e in add_next_button]}")
                for i, btn in enumerate(add_next_button):
                    logging.info(
                        f"Button {i+1} HTML: {btn.get_attribute('outerHTML')}")
                    logging.info(
                        f"Button {i+1} displayed: {btn.is_displayed()}")
            else:
                logging.error("No '+ Add next' buttons found")

            # Take page source for debugging
            with open("debug_screenshots/page_source.html", "w", encoding="utf-8") as f:
                f.write(bot.driver.page_source)

        except Exception as e:
            logging.error(f"Error checking for '+ Add next' button: {e}")

        # Try different selectors for the "+ Add next" button
        selectors = [
            "p.tz-p.color--blue.clickable",
            "p.color--blue.clickable",
            "p.clickable",
            "div.section-row p.clickable",
            "//p[contains(@class, 'color--blue') and contains(@class, 'clickable')]",
            "//p[text()='+ Add next']"
        ]

        clicked = False
        for selector in selectors:
            try:
                logging.info(f"Trying selector: {selector}")

                if selector.startswith("//"):
                    # XPath
                    elements = bot.driver.find_elements("xpath", selector)
                else:
                    # CSS
                    elements = bot.driver.find_elements(
                        "css selector", selector)

                if elements:
                    logging.info(
                        f"Found {len(elements)} elements with selector {selector}")

                    for i, element in enumerate(elements):
                        try:
                            logging.info(f"Checking element {i+1}")
                            if element.is_displayed():
                                logging.info(
                                    f"Element {i+1} is displayed, text: '{element.text}'")
                                bot.driver.execute_script(
                                    "arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)
                                bot.driver.save_screenshot(
                                    f"debug_screenshots/before_click_{i+1}.png")

                                # Try JavaScript click
                                logging.info("Attempting JavaScript click...")
                                bot.driver.execute_script(
                                    "arguments[0].click();", element)
                                time.sleep(2)

                                logging.info("Taking screenshot after click")
                                bot.driver.save_screenshot(
                                    f"debug_screenshots/after_click_{i+1}.png")

                                # Check if modal appeared by looking for Create Program button
                                try:
                                    create_program_buttons = bot.driver.find_elements(
                                        "xpath", "//span[text()='Create Program']/ancestor::button")
                                    if create_program_buttons:
                                        logging.info(
                                            "Success! Create Program button found after click")
                                        clicked = True
                                        break
                                except Exception as ce:
                                    logging.warning(
                                        f"Error checking for Create Program button: {ce}")
                            else:
                                logging.info(f"Element {i+1} is not displayed")
                        except Exception as ee:
                            logging.warning(f"Error with element {i+1}: {ee}")

                    if clicked:
                        break
                else:
                    logging.info(f"No elements found with selector {selector}")
            except Exception as e:
                logging.warning(f"Error with selector {selector}: {e}")

        if not clicked:
            logging.error("Could not click '+ Add next' with any selector")

        # Continue with regular create_program attempt
        result = bot.create_program(
            program_name, chest_exercises=chest_exercises)
        bot.driver.save_screenshot(
            "debug_screenshots/after_create_program.png")

        if result:
            logging.info("Program created successfully!")
        else:
            logging.error("Failed to create program")

    except Exception as e:
        logging.exception(f"Error in test_create_program: {e}")
    finally:
        logging.info("Test complete, cleaning up...")
        bot.cleanup()


if __name__ == "__main__":
    test_create_program()
