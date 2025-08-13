import sys
import argparse
import sqlite3
import time
import random
from datetime import datetime, timedelta
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os
import shutil
import tempfile
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Import the DailyFollowBackChecker class
from check_daily_follow_backs import DailyFollowBackChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('missed_dms_simple.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class SimpleMissedDMSender(DailyFollowBackChecker):
    """Simplified version that bypasses New message button by going directly to DM URLs"""

    def __init__(self, username="cocos_connected", password="Shannonb3"):
        super().__init__(username, password, analyze_profiles=False)

    def send_dm_direct_url(self, username, message):
        """Send DM by navigating directly to Instagram's DM URL format"""
        try:
            # Try Instagram's direct DM URL format
            dm_url = f"https://www.instagram.com/direct/t/{username}/"
            logging.info(f"🎯 Navigating directly to DM URL: {dm_url}")

            self.driver.get(dm_url)
            time.sleep(5)  # Wait for page to load

            # Check if we're in a DM interface
            dm_indicators = [
                "//div[@aria-label='Message'][@contenteditable='true']",
                "//div[@role='textbox'][@contenteditable='true']",
                "//textarea[@placeholder='Message...']",
                "//div[contains(@class, 'x1iyjqo2') and @contenteditable='true']"
            ]

            message_input = None
            for selector in dm_indicators:
                try:
                    message_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if message_input and message_input.is_displayed():
                        logging.info(
                            f"✅ Found DM interface with selector: {selector}")
                        break
                except:
                    continue

            if message_input:
                # We're in a DM interface, try to send the message
                logging.info(f"💬 Typing message: {message}")

                # Try different input methods
                input_methods = [
                    "javascript_innerHTML",
                    "direct_send_keys",
                    "actions_send_keys"
                ]

                input_success = False
                for method in input_methods:
                    try:
                        if method == "javascript_innerHTML":
                            self.driver.execute_script(
                                "arguments[0].focus();", message_input)
                            time.sleep(0.5)
                            self.driver.execute_script(
                                "arguments[0].innerHTML = arguments[1];", message_input, message)
                            # Trigger input event
                            self.driver.execute_script("""
                                var event = new Event('input', { bubbles: true });
                                arguments[0].dispatchEvent(event);
                            """, message_input)

                        elif method == "direct_send_keys":
                            message_input.click()
                            time.sleep(0.5)
                            message_input.clear()
                            message_input.send_keys(message)

                        elif method == "actions_send_keys":
                            ActionChains(self.driver).move_to_element(
                                message_input).click().perform()
                            time.sleep(0.5)
                            message_input.send_keys(message)

                        time.sleep(1)

                        # Check if message was entered
                        entered_text = message_input.get_attribute(
                            'value') or message_input.text or message_input.get_attribute('textContent')
                        if entered_text and message.lower() in str(entered_text).lower():
                            logging.info(
                                f"✅ Message entered successfully using {method}")
                            input_success = True
                            break

                    except Exception as e:
                        logging.debug(f"Input method {method} failed: {e}")
                        continue

                if input_success:
                    # Try to send the message
                    send_methods = [
                        "enter_key",
                        "send_button"
                    ]

                    for send_method in send_methods:
                        try:
                            if send_method == "enter_key":
                                message_input.send_keys(Keys.RETURN)
                                logging.info("✅ Message sent using Enter key")
                                time.sleep(3)
                                return True

                            elif send_method == "send_button":
                                send_selectors = [
                                    "//div[@aria-label='Send'][@role='button']",
                                    "//button[@aria-label='Send']",
                                    "//div[@role='button']//svg[@aria-label='Send']/..",
                                    "//button[contains(text(), 'Send')]"
                                ]

                                for selector in send_selectors:
                                    try:
                                        send_button = WebDriverWait(self.driver, 3).until(
                                            EC.element_to_be_clickable(
                                                (By.XPATH, selector))
                                        )
                                        send_button.click()
                                        logging.info(
                                            f"✅ Message sent using Send button: {selector}")
                                        time.sleep(3)
                                        return True
                                    except:
                                        continue

                        except Exception as e:
                            logging.debug(
                                f"Send method {send_method} failed: {e}")
                            continue

                    logging.warning(
                        f"⚠️ Message entered but failed to send for @{username}")
                    return False
                else:
                    logging.warning(
                        f"⚠️ Failed to enter message for @{username}")
                    return False
            else:
                logging.warning(
                    f"⚠️ Direct DM URL didn't work for @{username}, trying profile approach")
                # Fallback to profile approach
                return self.send_dm_via_profile(username, message)

        except Exception as e:
            logging.error(
                f"❌ Error in direct DM approach for @{username}: {e}")
            return False

    def send_dm_via_profile(self, username, message):
        """Fallback method: Send DM via user's profile page"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            logging.info(f"🔄 Fallback: Navigating to profile: {profile_url}")

            self.driver.get(profile_url)
            time.sleep(3)

            # Look for Message button on profile
            message_button_selectors = [
                "//div[@role='button']//span[text()='Message']/..",
                "//button[contains(text(), 'Message')]",
                "//div[contains(text(), 'Message')][@role='button']"
            ]

            for selector in message_button_selectors:
                try:
                    message_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    message_button.click()
                    logging.info(
                        f"✅ Clicked Message button on profile: {selector}")
                    time.sleep(3)

                    # Now look for message input (skip the "New message" button complexity)
                    message_input_selectors = [
                        "//div[@aria-label='Message'][@contenteditable='true']",
                        "//div[@role='textbox'][@contenteditable='true']",
                        "//textarea[@placeholder='Message...']"
                    ]

                    for input_selector in message_input_selectors:
                        try:
                            message_input = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, input_selector))
                            )
                            if message_input and message_input.is_displayed():
                                logging.info(
                                    f"✅ Found message input: {input_selector}")

                                # Type and send message
                                message_input.click()
                                time.sleep(0.5)
                                message_input.send_keys(message)
                                time.sleep(1)
                                message_input.send_keys(Keys.RETURN)

                                logging.info(
                                    f"✅ Message sent via profile approach to @{username}")
                                time.sleep(3)
                                return True

                        except:
                            continue

                    logging.warning(
                        f"⚠️ Message button clicked but couldn't find input for @{username}")
                    return False

                except:
                    continue

            logging.warning(
                f"⚠️ Could not find Message button on profile for @{username}")
            return False

        except Exception as e:
            logging.error(f"❌ Error in profile approach for @{username}: {e}")
            return False

    def get_users_who_followed_back_but_no_dm(self, days_back=7):
        """Get users who followed back but never received their DMs"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, follow_back_checked_at, followed_at, dm_status
            FROM processing_queue 
            WHERE follow_back_status = 'yes' 
            AND (dm_status IS NULL OR dm_status != 'sent')
            AND follow_back_checked_at >= date('now', '-' || ? || ' days')
            ORDER BY follow_back_checked_at DESC
        """, (days_back,))

        users = cursor.fetchall()
        conn.close()

        return {user[0]: {
            'checked_at': user[1],
            'followed_at': user[2],
            'dm_status': user[3]
        } for user in users}

    def run_simple_dm_campaign(self):
        """Send DMs using the simplified approach"""
        logging.info("🚀 Starting Simple Missed DM Campaign...")

        # Get users who need DMs
        users_needing_dms = self.get_users_who_followed_back_but_no_dm(
            days_back=7)

        if not users_needing_dms:
            logging.info(
                "📭 No users found who followed back but missed their DMs!")
            return

        logging.info(
            f"Found {len(users_needing_dms)} users who followed back but never received their DMs")

        # Setup driver and login
        self.setup_driver()

        try:
            if not self.login_to_instagram():
                logging.error(
                    "❌ Failed to login. Stopping missed DM campaign.")
                return

            # Quick popup dismissal
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Not Now')]"))
                ).click()
                logging.info("Dismissed popup")
            except:
                pass

            time.sleep(2)

            # Determine account mode for DM generation
            account_mode = 'local' if self.username == 'cocos_pt_studio' else 'online'

            dms_sent_count = 0
            failed_count = 0
            processed_count = 0

            for username, user_info in users_needing_dms.items():
                processed_count += 1
                logging.info(
                    f"📊 Processing {processed_count}/{len(users_needing_dms)}: @{username}")

                try:
                    # Generate DM message
                    dm_message = self.generate_dm_message(
                        username, account_mode)

                    # Try simplified DM approach
                    if self.send_dm_direct_url(username, dm_message):
                        # Store DM in conversation history
                        self.store_dm_in_conversation_history(
                            username, dm_message)

                        # Update database
                        self.update_dm_status(username, dm_message, 'sent')
                        dms_sent_count += 1

                        logging.info(
                            f"✅ Simple DM sent successfully to @{username}")

                        # Delay between successful DMs
                        delay = random.uniform(30, 45)
                        logging.info(
                            f"⏳ Waiting {delay:.1f}s before next DM...")
                        time.sleep(delay)

                    else:
                        self.update_dm_status(username, dm_message, 'failed')
                        failed_count += 1
                        logging.warning(
                            f"❌ Failed to send simple DM to @{username}")

                except Exception as e:
                    logging.error(
                        f"❌ Critical error processing @{username}: {e}")
                    self.update_dm_status(username, "", 'failed')
                    failed_count += 1
                    continue

            # Final report
            logging.info("\n" + "="*50)
            logging.info("📋 SIMPLE MISSED DM CAMPAIGN REPORT")
            logging.info("="*50)
            logging.info(f"Total Users Found: {len(users_needing_dms)}")
            logging.info(f"Users Processed: {processed_count}")
            logging.info(f"DMs Sent Successfully: {dms_sent_count}")
            logging.info(f"Failed DMs: {failed_count}")
            logging.info(
                f"Success Rate: {(dms_sent_count/len(users_needing_dms)*100):.1f}%")
            logging.info("="*50)

        except Exception as e:
            logging.critical(
                f"Critical error in simple missed DM campaign: {e}")
        finally:
            self.teardown_driver()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Send DMs to users who followed back but never received their DMs (Simple Version)')
    parser.add_argument('--account', type=str, choices=['local', 'online'], default='online',
                        help='Account mode: "local" for @cocos_pt_studio, "online" for @cocos_connected')
    args = parser.parse_args()

    # Set credentials based on account mode
    if args.account == 'local':
        username = "cocos_pt_studio"
        print(f"🏠 LOCAL MODE: Sending missed DMs for @{username}")
    else:
        username = "cocos_connected"
        print(f"🌱 ONLINE MODE: Sending missed DMs for @{username}")

    sender = SimpleMissedDMSender(username=username)
    sender.run_simple_dm_campaign()
