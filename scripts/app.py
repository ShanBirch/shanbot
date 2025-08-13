from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time
import logging
import pyautogui
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
import os
import openai
import base64


class TrainerizeAutomation:
    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Initializing Chrome...")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logging.info("Chrome initialized successfully!")
        self.openai_api_key = "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"  # Replace with your API key
        self.element_wait_time = 15  # increased wait time
        self.max_attempts = 3  # max attempts to find messages container
        # xpath for messages section
        self.messages_selector = "//div[contains(@class,'messages-view')]"
        self.user_name = "Shannon Birch"
        # css selector for individual message items
        self.message_item_selector = "[data-testid='thread_message_sidebar_button']"
        self.message_input_selector = "div[data-offset-key='55met-0-0']"
        self.message_bubble_selector = "//div[contains(@class, 'message-bubble')]"
        self.message_sender_selector = "//div[contains(@class, 'message_senderRow')]//label[contains(@class, 'tz-label--medium')]"
        self.message_body_selector = "//div[contains(@class, 'messageBody')]//p[contains(@class, 'tz-p')]"

        openai.api_key = self.openai_api_key

    def wait_for_page_load(self, extra_wait=3):
        """
        Wait for page to be fully loaded
        extra_wait: additional seconds to wait after page load
        """
        try:
            logging.info("Waiting for page to load completely...")
            self.wait.until(
                lambda driver: driver.execute_script(
                    "return document.readyState") == "complete"
            )
            time.sleep(extra_wait)  # Configurable extra wait time
            logging.info("Page fully loaded!")
            return True
        except Exception as e:
            logging.error(f"Error waiting for page load: {e}")
            return False

    def scroll_page(self):
        """
        Scroll the page down
        """
        logging.info("Scrolling page down...")
        html = self.driver.find_element(By.TAG_NAME, 'html')
        for _ in range(5):  # Press down arrow 5 times
            html.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)
        logging.info("Page scrolled!")

    def handle_cookie_dialog(self):
        """
        Try to handle any cookie consent dialogs
        """
        try:
            # Try to find and click accept button in cookie dialog
            accept_buttons = self.driver.find_elements(By.XPATH,
                                                       "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(@class, 'accept')]")
            for button in accept_buttons:
                try:
                    button.click()
                    logging.info("Clicked cookie accept button")
                    time.sleep(1)
                    return True
                except Exception as e:
                    logging.debug(f"Failed to click a cookie button: {e}")
                    continue

            # If no button found, try to remove the dialog using JavaScript
            self.driver.execute_script("""
                var elements = document.getElementsByClassName('ot-sdk-row');
                for(var i=0; i<elements.length; i++){
                    elements[i].remove();
                }
            """)
            logging.info("Removed cookie dialog via JavaScript")
            return True
        except Exception as e:
            logging.error(f"Error handling cookie dialog: {e}")
            return False

    def handle_popups(self):
        """
        Handle various popups that might appear after login
        """
        try:
            logging.info("Checking for popups...")
            # Handle Google Calendar popup
            try:
                got_it_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'GOT IT')]"))
                )
                got_it_button.click()
                logging.info("Closed Google Calendar popup")
            except:
                logging.info("No Google Calendar popup found")

            # Handle other potential popups
            popup_buttons = [
                "//button[contains(text(), 'Allow')]",
                "//button[contains(text(), 'Block')]",
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'Skip')]",
                "//button[contains(@class, 'close')]",
                "//div[contains(@class, 'close-button')]"
            ]

            for xpath in popup_buttons:
                try:
                    button = self.driver.find_element(By.XPATH, xpath)
                    button.click()
                    logging.info(f"Closed popup using {xpath}")
                    time.sleep(1)
                except Exception as e:
                    logging.debug(f"Failed to close popup with {xpath} : {e}")
                    continue

        except Exception as e:
            logging.error(f"Error handling popups: {e}")

    def login(self, username, password):
        """
        Navigate to Trainerize and login
        """
        try:
            logging.info("Navigating to Trainerize...")
            self.driver.get("https://www.trainerize.com/login.aspx")
            if not self.wait_for_page_load():
                raise Exception("Initial page failed to load completely")
            logging.info("Reached Trainerize website!")

            # Scroll down the page
            self.scroll_page()

            # Handle any cookie dialogs
            self.handle_cookie_dialog()

            # First page - Find URL
            logging.info("Looking for initial email field...")
            initial_email = self.wait.until(
                EC.presence_of_element_located((By.ID, "t_email"))
            )
            initial_email.clear()
            initial_email.send_keys(username)
            time.sleep(2)

            # Try to remove any overlays before clicking
            self.handle_cookie_dialog()

            # Click Find me button
            logging.info("Clicking Find me button...")
            try:
                find_button = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "tz-button--secondary"))
                )
                # Scroll button into view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", find_button)
                time.sleep(1)

                # Try JavaScript click first
                try:
                    self.driver.execute_script(
                        "arguments[0].click();", find_button)
                except:
                    find_button.click()
                logging.info("Clicked Find me button")
            except Exception as e:
                logging.error(f"Error clicking Find me button: {e}")
                raise

            # Wait for page transition
            # Longer wait for login page
            if not self.wait_for_page_load(extra_wait=15):
                raise Exception(
                    "Login page failed to load after clicking Find me")
            logging.info("Login page loaded successfully")

            # Second page - Main login form
            logging.info("Looking for main login email field...")
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "emailInput"))
            )
            email_input.clear()
            email_input.send_keys(username)
            logging.info("Email entered")

            # Enter password
            logging.info("Looking for password field...")
            password_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "passInput"))
            )
            password_input.clear()
            password_input.send_keys(password)
            logging.info("Password entered")

            # Wait for sign in button
            logging.info("Looking for Sign In button...")
            sign_in_button = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='signIn-button']"))
            )

            # Wait until button is enabled
            logging.info("Waiting for Sign In button to become enabled...")
            self.wait.until(
                lambda d: not sign_in_button.get_attribute("disabled"))
            logging.info("Sign In button is enabled")

            # Click sign in button using JavaScript
            self.driver.execute_script("arguments[0].click();", sign_in_button)
            logging.info("Clicked Sign In button")

            # Wait for final page load after login
            if not self.wait_for_page_load():
                raise Exception("Dashboard page failed to load after login")
            logging.info("Successfully logged in and loaded dashboard")

        except Exception as e:
            logging.error(f"Error during login process: {e}")
            self.driver.save_screenshot("error_screenshot.png")
            logging.error("Screenshot saved as 'error_screenshot.png'")
            raise

    def find_element_by_image(self, screenshot, template_path, threshold):
        """Finds the location of an element in a screenshot based on template matching."""
        template = cv2.imread(template_path)
        h, w, _ = template.shape

        # convert to greyscale (reduces the number of calculations)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(
            screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= threshold:
            return max_loc, w, h
        else:
            return None, 0, 0

    def click_element(self, element_location, element_width, element_height):
        """Moves the mouse to the center of an element and clicks."""
        x = element_location[0] + element_width // 2
        y = element_location[1] + element_height // 2
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()
        time.sleep(0.2)

    def capture_screenshot(self, driver, element=None):
        """Captures a screenshot using Selenium, either full page or specific element."""
        if element:
            location = element.location
            size = element.size
            screenshot = driver.get_screenshot_as_png()
            img = Image.open(BytesIO(screenshot))

            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']

            img = img.crop((left, top, right, bottom))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        else:
            screenshot = driver.get_screenshot_as_png()
            img = Image.open(BytesIO(screenshot))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def click_messages_button(self):
        """Clicks the messages button"""
        try:
            logging.info("Looking for messages button...")
            messages_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "nav_messages"))
            )
            messages_button.click()
            logging.info("Successfully clicked messages button")
            self.wait_for_page_load()
        except Exception as e:
            logging.error(f"Error clicking messages button: {e}")
            self.driver.save_screenshot("messages_error.png")
            raise

    def analyze_messages_with_chatgpt(self, message_text):
        """Uses ChatGPT to analyze messages"""
        try:
            logging.info("Sending messages to ChatGPT for analysis")
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # set model
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyze the following messages. If Shannon Birch was the last person to respond to any of the messages, respond with `no messages`. If Shannon Birch was not the last person to respond, then read all of the other users messages and create a response as a fitness coach. Be very brief.\n\n{message_text}"
                    }
                ],
                max_tokens=300,
            )

            logging.info("ChatGPT response received")
            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"Error analyzing messages with ChatGPT: {e}")
            self.driver.save_screenshot("chatgpt_error.png")
            logging.error("Screenshot saved as 'chatgpt_error.png'")
            return None

    def interact_with_new_messages(self, chatgpt_response, messages_list):
        """Interacts with the messages based on ChatGPT"""
        try:
            logging.info("Interacting with new messages...")
            if "no messages" in chatgpt_response.lower():
                logging.info("ChatGPT indicates there are no messages with `" +
                             self.user_name + "` as the last sender.")
                return
            else:
                logging.info(
                    "ChatGPT indicates there are messages, attempting to interact with them")

                if messages_list:
                    logging.info(
                        "found message rows, attempting to interact with them")
                    try:
                        # find the message content element by using the ancestor.
                        user_content = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH,
                             f"{self.messages_selector}//span[contains(text(),'{self.user_name}')]/ancestor::div[contains(@class,'ThreadlistItem')]")
                        ))
                        messages_list[0].click()
                        time.sleep(2)
                        all_messages = self.driver.find_elements(
                            By.XPATH, self.message_bubble_selector)  # get all messages
                        user_messages = []  # create a container to hold all user messages
                        last_message_sender = ""  # variable to store the last sender
                        for message in reversed(all_messages):
                            sender = message.find_element(
                                By.XPATH, ".//span[contains(@class, 'sender-name')]").text
                            message_text = message.find_element(
                                By.XPATH, "../..//div[contains(@class, 'messageBody')]//p").text  # get the message content

                            if sender == self.user_name:
                                last_message_sender = self.user_name
                                break  # stop looking at the messages
                            else:
                                # add the message to the list of messages.
                                user_messages.append(message_text)
                                last_message_sender = sender
                        if last_message_sender != self.user_name:
                            logging.info(
                                f"The last message was not from you, {self.user_name}, extracting user messages.")
                            combined_messages = "\n".join(user_messages)

                            response = self.analyze_messages_with_chatgpt(
                                combined_messages)
                            if response:
                                message_input = self.wait.until(
                                    EC.presence_of_element_located(
                                        (By.CSS_SELECTOR, self.message_input_selector))
                                )
                                self.input_text(message_input, response)
                                pyautogui.press('enter')
                                logging.info("ChatGPT response entered")

                            else:
                                logging.info(
                                    "ChatGPT could not create a response")
                            return
                    except Exception as e:
                        logging.error(
                            f"Error interacting with message row: {e}")

                else:
                    logging.info("No message rows were found.")
        except Exception as e:
            logging.error(f"Error interacting with messages: {e}")

    def input_text(self, element, text):
        """Inputs text into a given element"""
        element.click()
        time.sleep(0.1)  # give it a moment to register
        pyautogui.typewrite(text)
        time.sleep(0.1)

    def get_messages_list(self):
        """Gets the list of messages"""
        try:
            logging.info("Getting list of messages")
            messages = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, self.message_item_selector))
            )
            logging.info("Got message list successfully")
            return messages
        except Exception as e:
            logging.error(f"Error getting messages list: {e}")
            self.driver.save_screenshot("get_message_list_error.png")
            logging.error("Screenshot saved as get_message_list_error.png")
            return None


if __name__ == '__main__':
    # Example Usage
    username = "shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk"  # Replace with your password

    trainerize_bot = TrainerizeAutomation()
    # Replace with login page URL
    trainerize_bot.driver.get("https://cocosptstudio.trainerize.com/app/login")
    trainerize_bot.login(username, password)
    trainerize_bot.click_messages_button()
    # Get the list of messages
    messages_list = trainerize_bot.get_messages_list()
    if not messages_list:
        logging.error("Could not load message list, exiting.")
        trainerize_bot.driver.quit()
        exit()
    # Click first Message
    logging.info("Clicking the first message")
    messages_list[0].click()  # clicking on first message
    time.sleep(2)  # give it a moment to load.
    # get the last message sender
    try:
        last_message_sender = trainerize_bot.wait.until(EC.presence_of_element_located(
            (By.XPATH, trainerize_bot.last_message_sender_selector))).text
        logging.info(f"Last message sender: {last_message_sender}")

        if last_message_sender != trainerize_bot.user_name:
            logging.info(
                "Last message was not from user, attempting to respond.")

            # get all messages, and loop from the bottom to the top.
            all_messages = trainerize_bot.driver.find_elements(
                By.XPATH, trainerize_bot.message_bubble_selector)
            user_messages = []
            for message in reversed(all_messages):
                # get the sender for this specific message.
                sender = message.find_element(
                    By.XPATH, ".//span[contains(@class, 'sender-name')]").text
                if sender == trainerize_bot.user_name:
                    break
                else:
                    # add this message content to the other user list
                    user_messages.append(message.find_element(
                        By.XPATH, "../..//div[contains(@class, 'messageBody')]//p").text)

            combined_messages = "\n".join(user_messages)

            chatgpt_response = trainerize_bot.analyze_messages_with_chatgpt(
                combined_messages)
            if chatgpt_response:
                trainerize_bot.interact_with_new_messages(
                    chatgpt_response, messages_list)
        else:
            logging.info(
                f"The last message was from you, {trainerize_bot.user_name}, skipping message.")
    except Exception as e:
        logging.error(f"Error during message analysis: {e}")
        trainerize_bot.driver.save_screenshot("message_analysis_error.png")
        logging.error(f"Screenshot saved as message_analysis_error.png")
    logging.info("Automation completed successfully!")
    logging.info("Browser will stay open until you press Enter.")
    logging.info(
        "You can use this time to inspect the page with DevTools (F12)")
    input("Press Enter when you're ready to close the browser...")
    logging.info("Closing browser...")
    trainerize_bot.driver.quit()
    logging.info("Browser closed. Script complete.")
