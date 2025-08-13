from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import logging
import tempfile
import shutil
import os
from datetime import datetime, timedelta, date
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
import re
import base64
from openai import OpenAI


class TrainerizeAutomation:
    def __init__(self, openai_api_key):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")

        self.chromedriver_path = "C:\\SeleniumDrivers\\chromedriver-win64\\chromedriver.exe"
        self.chrome_executable_path = "C:\\SeleniumDrivers\\chrome-win64\\chrome.exe"
        self.openai_api_key = openai_api_key

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={self.temp_user_data_dir}")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.binary_location = self.chrome_executable_path

        try:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logging.info("Chrome initialized successfully!")
            self.client = OpenAI(api_key=self.openai_api_key)
        except Exception as e:
            logging.error(f"Failed to initialize Chrome or OpenAI: {e}")
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            raise

    def handle_cookie_dialog(self):
        logging.info("Cookie dialog handling (placeholder - not clicking Accept).")
        time.sleep(2)

    def handle_notification_popup(self):
        try:
            logging.info("Checking for and handling 'Get notifications?' popup...")
            block_button_locator = (By.XPATH, "//button[contains(text(), 'Block')]")
            block_button = self.wait.until(EC.element_to_be_clickable(block_button_locator))
            block_button.click()
            logging.info("Clicked 'Block' on the notification popup.")
            time.sleep(1)
            return True
        except Exception as e:
            logging.warning(f"Notification popup not found or failed to handle: {e}")
            return False

    def login(self, username, password):
       try:
            logging.info("Navigating directly to Trainerize login page...")
            self.driver.get("https://www.trainerize.com/login.aspx")
            self.handle_cookie_dialog()
            logging.info("Scrolling down slightly...")
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
            logging.info("Waiting for page to load...")
            self.wait.until(EC.presence_of_element_located((By.ID, "t_email")))
            logging.info("Entering initial email...")
            email_field = self.driver.find_element(By.ID, "t_email")
            email_field.send_keys(username)
            logging.info("Clicking 'Find me' button...")
            find_me_button = self.driver.find_element(By.CLASS_NAME, "tz-button--secondary")
            find_me_button.click()
            time.sleep(2)
            logging.info("Waiting for the *second* email field (emailInput)...")
            self.wait.until(EC.presence_of_element_located((By.ID, "emailInput")))
            logging.info("Entering *full* email on second page...")
            email_field_second = self.driver.find_element(By.ID, "emailInput")
            email_field_second.send_keys(username)
            logging.info("Entering password...")
            password_field = self.driver.find_element(By.ID, "passInput")
            password_field.send_keys(password)
            logging.info("Clicking 'Sign In' button...")
            sign_in_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='signIn-button']")))
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            logging.info("Successfully logged in!")
            return True
       except Exception as e:
            logging.error(f"Error during login: {e}")
            return False

    def navigate_to_client(self, client_name):
        try:
            logging.info(f"Attempting to navigate to client: {client_name}")
            logging.info("Clicking the 'Clients' link in the sidebar...")
            clients_link_locator = (By.XPATH, "//a[.//*[local-name()='svg' and @name='outline/clients-new']]")
            try:
                clients_link = self.wait.until(EC.element_to_be_clickable(clients_link_locator))
                clients_link.click()
            except TimeoutException as te:
                logging.error(f"TimeoutException while waiting for Clients link: {te.msg}")
                raise
            time.sleep(2)
            logging.info("Entering client name into the search bar on the Clients page...")
            search_input_locator = (By.CSS_SELECTOR, "input[data-testid='baseGrid-topbar-searchInput']")
            search_input = self.wait.until(EC.presence_of_element_located(search_input_locator))
            search_input.send_keys(client_name)
            time.sleep(1)
            logging.info("Clicking on the client's name in the search results...")
            client_link_locator = (By.XPATH, f"//a[contains(text(), '{client_name}')]")
            client_link = self.wait.until(EC.element_to_be_clickable(client_link_locator))
            client_link.click()
            time.sleep(2)
            logging.info("Clicking the 'Open' button to switch into the client profile...")
            open_button_locator = (By.CSS_SELECTOR, "button[data-testid='clientProfileDialog-modalMenu-switchIntoClient']")
            open_button = self.wait.until(EC.element_to_be_clickable(open_button_locator))
            open_button.click()
            time.sleep(2)
            logging.info("Switching to the new tab...")
            original_window = self.driver.current_window_handle
            self.wait.until(EC.number_of_windows_to_be(2))
            for window_handle in self.driver.window_handles:
                if window_handle != original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            logging.info(f"Successfully navigated to client: {client_name} and switched to their profile tab.")
            return True
        except Exception as e:
            logging.error(f"Error navigating to client or switching tabs: {e}")
            return False
            
    def send_client_message(self, message_text):
        try:
            logging.info("Attempting to send a message to the client...")
            
            # Click on the message button using the text label
            logging.info("Looking for the message button...")
            # Try multiple approaches to find the message button
            try:
                # First try: Look for the label with "Message" text
                message_button_locator = (By.XPATH, "//label[contains(@class, 'tz-label') and contains(text(), 'Message')]")
                message_button = self.wait.until(EC.element_to_be_clickable(message_button_locator))
                message_button.click()
                logging.info("Clicked on the message button (label approach)")
            except Exception as e:
                logging.warning(f"Could not find message button using label: {e}")
                try:
                    # Second try: Look for SVG icon
                    message_button_locator = (By.XPATH, "//svg[@name='outline/messages/PM-message']/..")
                    message_button = self.wait.until(EC.element_to_be_clickable(message_button_locator))
                    message_button.click()
                    logging.info("Clicked on the message button (SVG approach)")
                except Exception as e2:
                    logging.warning(f"Could not find message button using SVG: {e2}")
                    # Third try: Look for any element containing 'message' text
                    message_button_locator = (By.XPATH, "//*[contains(text(), 'Message') or @*[contains(., 'message')]]")
                    message_button = self.wait.until(EC.element_to_be_clickable(message_button_locator))
                    message_button.click()
                    logging.info("Clicked on the message button (generic approach)")
            
            # Wait for message dialog to appear
            logging.info("Waiting for message dialog to load...")
            message_composer_locator = (By.CSS_SELECTOR, "div.messageComposer")
            self.wait.until(EC.visibility_of_element_located(message_composer_locator))
            
            # Focus on the message input area
            logging.info("Focusing on message input area...")
            # The DraftEditor component can be tricky to interact with - we'll try a few approaches
            
            # Try direct selector for the content editable div
            try:
                editor_locator = (By.CSS_SELECTOR, "div.public-DraftEditor-content")
                editor = self.wait.until(EC.element_to_be_clickable(editor_locator))
                self.driver.execute_script("arguments[0].click();", editor)
                time.sleep(1)
                
                # Use JavaScript to set the content (more reliable than send_keys for complex editors)
                logging.info("Typing message...")
                self.driver.execute_script("""
                    const editorDiv = document.querySelector('div.public-DraftEditor-content');
                    if (editorDiv) {
                        // Trigger focus event
                        editorDiv.focus();
                        
                        // Create and dispatch input event
                        const inputEvent = new InputEvent('input', {
                            bubbles: true,
                            cancelable: true,
                            data: arguments[0]
                        });
                        editorDiv.dispatchEvent(inputEvent);
                    }
                """, message_text)
                
                # Also try send_keys as a backup approach
                editor.send_keys(message_text)
                
            except Exception as e:
                logging.warning(f"First approach failed: {e}. Trying alternative method...")
                
                # Alternative approach using the placeholder element
                try:
                    placeholder_locator = (By.CSS_SELECTOR, "div.public-DraftEditorPlaceholder-inner")
                    placeholder = self.wait.until(EC.presence_of_element_located(placeholder_locator))
                    self.driver.execute_script("arguments[0].click();", placeholder)
                    
                    # After clicking placeholder, try to find the content editable again
                    editor_locator = (By.CSS_SELECTOR, "div.public-DraftEditor-content")
                    editor = self.wait.until(EC.element_to_be_clickable(editor_locator))
                    self.driver.execute_script("arguments[0].click();", editor)
                    
                    # Type the message with send_keys
                    editor.send_keys(message_text)
                except Exception as e2:
                    logging.error(f"Alternative approach also failed: {e2}")
                    raise
            
            # Wait a moment for the text to be entered
            time.sleep(2)
            
            # Look for and click the send button
            logging.info("Looking for send button...")
            send_button_locator = (By.XPATH, "//button[contains(@class, 'sendButton') or contains(@class, 'send-button') or contains(@data-testid, 'send')]")
            send_button = self.wait.until(EC.element_to_be_clickable(send_button_locator))
            send_button.click()
            
            logging.info("Message sent successfully!")
            time.sleep(2)  # Wait for the message to be sent
            return True
            
        except Exception as e:
            logging.error(f"Error sending message to client: {e}")
            return False

    def generate_client_review_message(self, client_name, week_start_date, week_end_date, 
                                    weight_data=None, workout_data=None):
        """
        Generates a formatted client review message with the provided data
        
        Parameters:
        client_name (str): The name of the client
        week_start_date (str): Start date of the review period in format DD/MM/YYYY
        week_end_date (str): End date of the review period in format DD/MM/YYYY
        weight_data (dict, optional): Dictionary with weight information (current, previous, change)
        workout_data (dict, optional): Dictionary with workout information
        
        Returns:
        str: Formatted review message
        """
        # Default values if no data provided
        if weight_data is None:
            weight_data = {
                "current": 83.5,
                "previous": 87,
                "change": -3.5
            }
        
        if workout_data is None:
            workout_data = {
                "total_workouts": 7,
                "completed_workouts": [
                    "Back and Triceps",
                    "Back and Triceps",
                    "Chest and Biceps",
                    "Chest and Biceps",
                    "Core and Arms",
                    "Core and Arms 2",
                    "Core and Arms 2"
                ],
                "total_weight": 40440.00,
                "total_reps": 1514,
                "total_sets": 152,
                "workload_change": 117.19
            }
        
        # Format the message
        message = f"Hey {client_name}! Here's your review for the week! :)\n\n"
        
        # Photos section
        message += "Photos: Didn't see any new progress pics this week. No worries, but if you can, snapping some regularly is super helpful to see how far you've come visually!\n\n"
        
        # Weight section
        weight_change_abs = abs(weight_data["change"])
        weight_direction = "down" if weight_data["change"] < 0 else "up"
        message += f"Weight: Weight's trending {weight_direction} nicely, that's awesome work! You're {weight_direction} {weight_change_abs} kg from {weight_data['previous']} to {weight_data['current']}! Keep doing what you're doing!\n\n"
        
        # Standard sections
        message += f"Food: No nutrition data this week, {client_name}. Tracking your food intake is the biggest step towards understanding your diet and achieving your goals! Maybe you could track it this week.\n\n"
        message += "Steps: No steps data this week. Remember, physical activity is so important for overall health. Tracking your steps can be a great way to stay motivated!\n\n"
        message += f"Sleep: No sleep data this week {client_name}. Consistently tracking your sleep helps us understand your recovery. Aiming for around 8 hours of sleep each night can significantly impact your progress and well-being! Try and make it a routine, bed at the same time and up at the same time everyday, this will help keep your internal body clock happy!\n\n"
        
        # Workout summary
        message += "Workout Summary\n"
        message += f"Total workouts for week of {week_start_date}-{week_end_date}: {workout_data['total_workouts']}\n"
        message += f"Workouts completed week of {week_start_date}-{week_end_date}:\n"
        
        # List all workouts
        for workout in workout_data["completed_workouts"]:
            message += f"- {workout}\n"
        
        # Workout stats
        message += f"--- Totals for week of {week_start_date}-{week_end_date}: ---\n"
        message += f"Total Weight Lifted: {workout_data['total_weight']:.2f} kg\n"
        message += f"Total Reps Done: {workout_data['total_reps']}\n"
        message += f"Total Sets Done: {workout_data['total_sets']}\n"
        
        # Workload change
        message += "--- Total Workload Change comparing previous week to current week:\n"
        message += f"Workload change vs previous week: {workout_data['workload_change']}%\n"
        message += "Love to see this increase in overall workload! Keep it coming!"
        
        return message

    def cleanup(self):
        """Properly clean up resources when done."""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            if hasattr(self, 'temp_user_data_dir') and os.path.exists(self.temp_user_data_dir):
                shutil.rmtree(self.temp_user_data_dir)
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


# Example usage
if __name__ == "__main__":
    # Replace with your actual API key
    openai_api_key = "your_openai_api_key_here"
    
    try:
        # Initialize automation
        automation = TrainerizeAutomation(openai_api_key)
        
        # Login to Trainerize
        if automation.login("shannonbirch@cocospersonaltraining.com", "cyywp7nyk"):
            # Navigate to client profile
            if automation.navigate_to_client("Shannon Birch"):
                # Generate client review message
                client_message = automation.generate_client_review_message(
                    "Shannon", 
                    "24/02/2025", 
                    "02/03/2025"
                )
                
                # Send the message
                automation.send_client_message(client_message)
                
                print("Client review message sent successfully!")
            else:
                print("Failed to navigate to client profile")
        else:
            print("Failed to login to Trainerize")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Always clean up resources
        if 'automation' in locals():
            automation.cleanup()