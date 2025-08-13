#!/usr/bin/env python3
"""
Process New Followers Script
============================

Processes a list of new Instagram followers by:
1. Checking if they exist in database
2. Adding them if missing  
3. Checking if they've been messaged
4. Analyzing their profiles/bios
5. Generating and sending personalized DMs
6. Recording everything in the database

Based on check_daily_follow_backs.py infrastructure
"""

import os
import sys
import sqlite3
import time
import random
import argparse
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import tempfile
import shutil
from selenium.webdriver.common.action_chains import ActionChains

# Import from existing check_daily_follow_backs.py infrastructure
try:
    from check_daily_follow_backs import DailyFollowBackChecker
    print("✅ Successfully imported DailyFollowBackChecker")
except ImportError as e:
    print(f"❌ Failed to import DailyFollowBackChecker: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_new_followers.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class NewFollowerProcessor(DailyFollowBackChecker):
    """Extends DailyFollowBackChecker to process new followers from a provided list"""

    def __init__(self, username="cocos_connected", password="Shannonb3"):
        super().__init__(username, password, analyze_profiles=True)

    def check_existing_conversation(self, username):
        """Check if there's already a conversation thread with this user - DATABASE FIRST, then web interface"""
        try:
            logging.info(
                f"🔍 Checking for existing conversation with @{username}...")

            # 🆕 STEP 1: Check database conversation history FIRST
            conn = None
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()

                # --- Updated logic: check BOTH legacy conversation_history table *and* the new messages table ---

                # 1️⃣ messages table (primary)
                cursor.execute("""
                    SELECT COUNT(*) FROM messages 
                    WHERE LOWER(ig_username) = LOWER(?)
                """, (username,))

                msg_table_count = cursor.fetchone()[0]

                # 2️⃣ conversation_history table (legacy-compat)
                cursor.execute("""
                    SELECT COUNT(*) FROM conversation_history 
                    WHERE LOWER(ig_username) = LOWER(?) 
                    AND message_text IS NOT NULL 
                    AND TRIM(message_text) != ''
                """, (username,))

                conv_hist_count = cursor.fetchone()[0]

                total_db_msgs = msg_table_count + conv_hist_count

                if total_db_msgs > 0:
                    logging.info(
                        f"✅ Found {total_db_msgs} existing messages in database for @{username} (messages: {msg_table_count}, conversation_history: {conv_hist_count}) – skipping duplicate DM")
                    return True

                # 3️⃣ processing_queue dm_status check (case-insensitive)
                cursor.execute("""
                    SELECT dm_status FROM processing_queue 
                    WHERE LOWER(username) = LOWER(?) 
                    AND dm_status IN ('sent', 'delivered', 'already_messaged')
                """, (username,))

                dm_status_result = cursor.fetchone()
                if dm_status_result:
                    logging.info(
                        f"✅ Found existing DM status '{dm_status_result[0]}' in database for @{username} – skipping")
                    return True

                logging.info(
                    f"📋 No existing conversation found in database for @{username}")

            except Exception as db_error:
                logging.warning(
                    f"⚠️ Database check error for @{username}: {db_error}")
                # Continue to web check if database fails
            finally:
                if conn:
                    conn.close()

            # 🔍 STEP 2: Check web interface for existing conversation (as backup)
            # Only check web interface if database didn't find anything
            logging.info(
                f"🌐 Checking web interface for existing conversation with @{username}...")

            # Look for message indicators on the current Instagram page
            existing_conversation_selectors = [
                # Check for message bubbles/conversation history
                "//div[contains(@class, 'message') or contains(@class, 'bubble')]",
                # Message text containers
                "//div[@role='gridcell']//div[contains(@class, 'x1lliihq')]",
                "//div[contains(@data-testid, 'message')]",
                # Check for conversation thread indicators
                "//div[contains(@class, 'conversation') or contains(@class, 'thread')]",
                # Look for any existing message content (common Shannon greetings)
                "//div[@role='main']//div[contains(text(), 'Heya') or contains(text(), 'Hey') or contains(text(), 'Thanks') or contains(text(), 'plant based')]",
                # Check for message status indicators
                "//div[contains(@aria-label, 'Seen') or contains(@aria-label, 'Delivered')]",
                # Look for sent message indicators
                "//div[contains(@class, 'x1i10hfl') and contains(text(), 'plant')]",
                # More comprehensive message detection
                "//div[@role='main']//div[contains(text(), 'follow back') or contains(text(), 'how long')]"
            ]

            for selector in existing_conversation_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                element_text = element.text.strip()
                                logging.info(
                                    f"✅ Found existing conversation element on web interface for @{username}: '{element_text[:50]}...'")
                                return True
                except Exception:
                    continue

            logging.info(
                f"📭 No existing conversation found on web interface for @{username}")
            return False

        except Exception as e:
            logging.warning(
                f"⚠️ Error checking conversation with @{username}: {e}")
            return False

    def send_dm_to_user(self, username, message):
        """IMPROVED: Enhanced DM sending with conversation checking and better input detection"""
        import time
        start_time = time.time()  # Fresh timer for DM sending only
        MAX_DM_TIME = 120  # 2 minutes should be enough for just DM sending

        max_retries = 2
        for retry_attempt in range(max_retries):
            try:
                # Check time limit
                if time.time() - start_time > MAX_DM_TIME:
                    logging.warning(f"⏰ DM timeout for @{username} - aborting")
                    return False

                if retry_attempt > 0:
                    logging.info(
                        f"🔄 Retry attempt {retry_attempt + 1} for DM to @{username}")
                    time.sleep(random.uniform(3, 5))

                logging.info(f"💬 Sending DM to @{username}...")

                # Quick driver health check
                try:
                    current_url = self.driver.current_url
                    logging.debug(f"Current URL before DM: {current_url}")
                except Exception as driver_error:
                    logging.error(
                        f"❌ Driver appears unresponsive: {driver_error}")
                    return False

                # Navigate to profile
                profile_url = f"https://www.instagram.com/{username}/"
                try:
                    self.driver.get(profile_url)
                    time.sleep(random.uniform(2, 4))
                except Exception as nav_error:
                    logging.error(
                        f"❌ Navigation error for @{username}: {nav_error}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Minimal modal cleanup
                for cleanup_attempt in range(2):
                    if time.time() - start_time > MAX_DM_TIME:
                        break
                    try:
                        self.close_any_modal()
                        time.sleep(0.5)
                    except Exception:
                        pass

                time.sleep(2)  # Page load wait

                # Find and click Message button
                message_selectors = [
                    "//button[contains(text(), 'Message')]",
                    "//div[contains(text(), 'Message')][@role='button']",
                    "//button[@aria-label='Message']",
                    "//a[contains(@href, 'direct/')]",
                    "//div[@role='button'][contains(., 'Message')]"
                ]

                message_button = None
                for attempt in range(3):
                    if time.time() - start_time > MAX_DM_TIME:
                        break

                    for selector in message_selectors:
                        try:
                            message_button = WebDriverWait(self.driver, 4).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            if message_button and message_button.is_displayed():
                                break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if message_button:
                        break

                    # Try scrolling to find Message button
                    try:
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)
                        self.driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight / 3);")
                        time.sleep(1)
                    except Exception:
                        pass

                if not message_button:
                    logging.warning(
                        f"❌ Could not find Message button for @{username}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Click Message button
                click_success = False
                for click_method in ["javascript", "direct"]:
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", message_button)
                        time.sleep(0.5)

                        if click_method == "javascript":
                            self.driver.execute_script(
                                "arguments[0].click();", message_button)
                        elif click_method == "direct":
                            message_button.click()

                        click_success = True
                        logging.info(
                            f"✅ Message button clicked using {click_method}")
                        break
                    except Exception as click_error:
                        logging.debug(
                            f"⚠️ {click_method} click failed: {click_error}")
                        continue

                if not click_success:
                    logging.warning(
                        f"❌ All click methods failed for @{username}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Wait longer for DM interface to load properly
                logging.info(f"⏳ Waiting for DM interface to load...")
                time.sleep(random.uniform(5, 8))

                # Handle DM interface popups
                try:
                    logging.info(
                        f"🔍 Checking for DM interface popups for @{username}...")
                    dm_popups_found = self.handle_dm_interface_popups()
                    if dm_popups_found:
                        logging.info(
                            f"🎯 Successfully handled {dm_popups_found} DM interface popup(s) for @{username}")
                        time.sleep(3)
                except Exception as popup_error:
                    logging.warning(
                        f"⚠️ Error handling DM popups for @{username}: {popup_error}")

                # Quick modal cleanup only
                try:
                    # Only try ESC key for speed
                    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                except Exception:
                    pass

                # 🆕 CHECK FOR EXISTING CONVERSATION
                if self.check_existing_conversation(username):
                    logging.warning(
                        f"⚠️ Existing conversation found with @{username} - skipping to avoid duplicate message")
                    return 'already_messaged'  # Special return value

                # Enhanced DM interface detection and debugging
                logging.info(f"⏳ Waiting for message interface to be ready...")

                # First, check what page we're actually on
                current_url = self.driver.current_url
                logging.info(
                    f"🔍 Current URL after Message click: {current_url}")

                # Take a screenshot for debugging if needed
                try:
                    screenshot_path = f"debug_dm_interface_{username}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logging.info(f"📸 Screenshot saved: {screenshot_path}")
                except:
                    pass

                # Enhanced waiting with multiple potential indicators
                dm_interface_ready = False
                for wait_attempt in range(3):
                    try:
                        logging.info(
                            f"🔍 Waiting for DM interface (attempt {wait_attempt + 1}/3)...")

                        # Wait for any of these DM interface indicators
                        WebDriverWait(self.driver, 10).until(
                            EC.any_of(
                                # Direct message interface elements
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@role='main']//form")),
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@role='main']//textarea")),
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[@role='main']//div[@contenteditable='true']")),
                                # Instagram-specific DM containers
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[contains(@class, 'x7r02ix')]")),
                                EC.presence_of_element_located(
                                    (By.XPATH, "//div[contains(@class, 'x1gzqxud')]")),
                                # Direct messaging indicators
                                EC.presence_of_element_located(
                                    (By.XPATH, "//*[contains(text(), 'Message') or contains(text(), 'Send message')]")),
                                # URL change indicators
                                EC.url_contains("direct"),
                                EC.url_contains("t/")
                            )
                        )

                        dm_interface_ready = True
                        logging.info(
                            f"✅ DM interface appears ready for @{username}")
                        break

                    except TimeoutException:
                        logging.warning(
                            f"⚠️ DM interface wait attempt {wait_attempt + 1} failed")

                        # Check if we need to handle additional popups
                        try:
                            self.handle_dm_interface_popups()
                            time.sleep(2)
                        except:
                            pass

                if not dm_interface_ready:
                    logging.warning(
                        f"⚠️ DM interface not ready after all attempts for @{username}")

                    # Debug: Check what's actually on the page
                    try:
                        page_title = self.driver.title
                        current_url = self.driver.current_url
                        logging.info(f"🔍 Page title: {page_title}")
                        logging.info(f"🔍 Final URL: {current_url}")

                        # Look for any form elements
                        all_forms = self.driver.find_elements(
                            By.TAG_NAME, "form")
                        logging.info(
                            f"🔍 Found {len(all_forms)} form elements on page")

                        # Look for any textareas
                        all_textareas = self.driver.find_elements(
                            By.TAG_NAME, "textarea")
                        logging.info(
                            f"🔍 Found {len(all_textareas)} textarea elements on page")

                        # Look for contenteditable divs
                        all_contenteditable = self.driver.find_elements(
                            By.XPATH, "//div[@contenteditable='true']")
                        logging.info(
                            f"🔍 Found {len(all_contenteditable)} contenteditable elements on page")

                    except Exception as debug_error:
                        logging.warning(f"⚠️ Debug info failed: {debug_error}")

                # ENHANCED message input detection with more comprehensive selectors
                # 🎯 ENHANCED message input selectors based on followup_manager (proven working)
                message_input_selectors = [
                    "//div[@role='textbox']",  # Primary Instagram DM input
                    # Main contenteditable approach
                    "//div[@contenteditable='true']",
                    # Aria-label based
                    "//div[contains(@aria-label, 'Message')]",
                    # Classic textarea
                    "//textarea[@placeholder='Message...']",
                    # Placeholder divs
                    "//div[contains(@placeholder, 'Message')]",
                    # Additional Instagram-specific patterns
                    "//div[@aria-label='Message']",  # Direct match
                    "//div[@contenteditable='true'][@aria-label='Message']",
                    "//form//div[@contenteditable='true']",
                    "//div[@role='main']//div[@contenteditable='true']",
                    # Fallbacks
                    "//textarea[@aria-label='Message']",
                    "//input[@placeholder='Message...']"
                ]

                message_input = None

                # FAST input detection - we know exactly what to look for
                logging.info(f"🔍 Fast search for Instagram message input...")

                # Reduced attempts since we have better detection
                for input_attempt in range(3):
                    # Remove premature timeout check - let selectors try first

                    logging.info(
                        f"🔍 Looking for message input (attempt {input_attempt + 1}/3)...")

                    # 🎯 FAST & TARGETED: Try direct selectors we know work
                    fast_selectors = [
                        # Instagram's exact pattern
                        "//div[@aria-label='Message' and @role='textbox']",
                        "//div[@aria-label='Message']",  # Fallback
                        "//div[@role='textbox']",  # Another fallback
                        # General contenteditable
                        "//div[@contenteditable='true' and contains(@aria-label, 'message')]"
                    ]

                    for i, selector in enumerate(fast_selectors):
                        try:
                            elements = self.driver.find_elements(
                                By.XPATH, selector)
                            logging.info(
                                f"   Fast selector {i+1}: Found {len(elements)} elements")

                            for element in elements:
                                try:
                                    if element.is_displayed():
                                        # Quick check - skip search elements
                                        aria_label = element.get_attribute(
                                            'aria-label') or ''
                                        if 'search' not in aria_label.lower():
                                            message_input = element
                                            logging.info(
                                                f"✅ FOUND MESSAGE INPUT! Using fast selector #{i+1}: {selector}")
                                            break
                                except Exception:
                                    continue
                            if message_input:
                                break
                        except Exception:
                            continue

                    if message_input:
                        break

                    # Brief wait before retry
                    if input_attempt < 2:  # Don't wait after last attempt
                        logging.info(
                            f"   No input found, waiting 2s before retry...")
                        time.sleep(2)

                if not message_input:
                    logging.warning(
                        f"❌ Could not find message input for @{username}")

                    # Debug: Log available elements
                    try:
                        all_inputs = self.driver.find_elements(
                            By.XPATH, "//textarea | //input | //div[@contenteditable='true']")
                        logging.info(
                            f"🔍 Found {len(all_inputs)} input elements on page:")
                        # Show first 5
                        for i, elem in enumerate(all_inputs[:5]):
                            try:
                                tag = elem.tag_name
                                placeholder = elem.get_attribute(
                                    'placeholder') or 'none'
                                aria_label = elem.get_attribute(
                                    'aria-label') or 'none'
                                classes = elem.get_attribute('class') or 'none'
                                logging.info(
                                    f"   Input {i+1}: {tag}, placeholder='{placeholder}', aria-label='{aria_label}', class='{classes[:50]}...'")
                            except:
                                pass
                    except:
                        pass

                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # 🎯 ENHANCED message typing using followup_manager approach
                logging.info(f"📝 Typing message using proven methods...")

                # Click to focus the input
                try:
                    message_input.click()
                    time.sleep(1)
                    logging.info("✅ Clicked and focused message input")
                except Exception as focus_error:
                    logging.warning(f"⚠️ Click focus failed: {focus_error}")

                # Try to clear any existing text
                try:
                    if message_input.tag_name.lower() == 'textarea':
                        message_input.clear()
                    elif message_input.get_attribute('contenteditable') == 'true':
                        # For contenteditable divs (Instagram's message input)
                        self.driver.execute_script(
                            "arguments[0].textContent = '';", message_input)
                    else:
                        message_input.clear()
                    logging.info("✅ Cleared existing text")
                except Exception:
                    logging.debug("Could not clear existing text")

                input_success = False

                # Method 1: ActionChains character-by-character (followup_manager approach)
                try:
                    logging.info(
                        "🎯 Trying ActionChains method (character-by-character)...")
                    actions = ActionChains(self.driver)
                    actions.move_to_element(message_input).click().pause(1)

                    # Type character by character with small delays
                    for char in message:
                        actions.send_keys(char).pause(0.1)

                    actions.perform()
                    logging.info("✅ Typed message using ActionChains")

                    time.sleep(1)

                    # Verify text was entered
                    try:
                        if message_input.tag_name.lower() == 'textarea':
                            entered_text = message_input.get_attribute(
                                'value') or message_input.text
                        else:
                            entered_text = message_input.get_attribute(
                                'textContent') or message_input.text

                        if message.lower() in str(entered_text).lower():
                            input_success = True
                            logging.info(
                                f"✅ Message typed successfully with ActionChains: '{entered_text[:50]}...'")
                        else:
                            logging.warning(
                                f"⚠️ ActionChains verification failed. Expected: '{message[:30]}...', Got: '{str(entered_text)[:30]}...'")
                    except Exception as verify_error:
                        logging.debug(
                            f"ActionChains verification error: {verify_error}")

                except Exception as actionchains_error:
                    logging.warning(
                        f"⚠️ ActionChains method failed: {actionchains_error}")

                # Method 2: Direct send_keys (if ActionChains failed)
                if not input_success:
                    try:
                        logging.info("🎯 Trying direct send_keys method...")
                        message_input.click()
                        time.sleep(0.5)
                        message_input.clear()
                        message_input.send_keys(message)
                        time.sleep(1)

                        # Verify
                        try:
                            if message_input.tag_name.lower() == 'textarea':
                                entered_text = message_input.get_attribute(
                                    'value') or message_input.text
                            else:
                                entered_text = message_input.get_attribute(
                                    'textContent') or message_input.text

                            if message.lower() in str(entered_text).lower():
                                input_success = True
                                logging.info(
                                    f"✅ Message typed successfully with direct send_keys: '{entered_text[:50]}...'")
                        except Exception:
                            pass

                    except Exception as direct_error:
                        logging.warning(
                            f"⚠️ Direct send_keys method failed: {direct_error}")

                # Method 3: JavaScript injection (last resort)
                if not input_success:
                    try:
                        logging.info("🎯 Trying JavaScript injection method...")
                        if message_input.get_attribute('contenteditable') == 'true':
                            self.driver.execute_script(
                                "arguments[0].textContent = arguments[1];", message_input, message)
                        else:
                            self.driver.execute_script(
                                "arguments[0].value = arguments[1];", message_input, message)
                        time.sleep(1)

                        input_success = True
                        logging.info(
                            "✅ Message typed successfully with JavaScript injection")

                    except Exception as js_error:
                        logging.warning(
                            f"⚠️ JavaScript injection method failed: {js_error}")

                if not input_success:
                    logging.warning(
                        f"❌ All input methods failed for @{username}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

                # Enhanced message sending
                send_success = False

                # Method 1: Try Enter key first (most reliable)
                try:
                    message_input.send_keys(Keys.RETURN)
                    send_success = True
                    logging.info(f"✅ Message sent using Enter key")
                except Exception as enter_error:
                    logging.debug(f"Enter key failed: {enter_error}")

                # Method 2: Send button with enhanced selectors
                if not send_success and time.time() - start_time < MAX_DM_TIME:
                    send_selectors = [
                        "//button[contains(text(), 'Send')]",
                        "//div[contains(text(), 'Send')][@role='button']",
                        "//button[@aria-label='Send message']",
                        "//div[@role='button'][contains(., 'Send')]",
                        "//button[contains(@data-testid, 'send')]"
                    ]

                    for selector in send_selectors:
                        try:
                            send_button = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            send_button.click()
                            send_success = True
                            logging.info(f"✅ Message sent using Send button")
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                if send_success:
                    time.sleep(random.uniform(2, 4))
                    total_time = time.time() - start_time
                    logging.info(
                        f"✅ DM sent to @{username}: '{message}' (took {total_time:.1f}s)")
                    return True
                else:
                    logging.warning(
                        f"❌ All send methods failed for @{username}")
                    if retry_attempt < max_retries - 1:
                        continue
                    return False

            except Exception as dm_error:
                logging.error(
                    f"❌ Error in DM attempt {retry_attempt + 1} for @{username}: {dm_error}")
                if retry_attempt < max_retries - 1:
                    # Quick recovery
                    try:
                        self.driver.get("https://www.instagram.com/")
                        time.sleep(3)
                    except Exception:
                        pass
                    continue
                return False

        # If all retries failed
        total_time = time.time() - start_time
        logging.error(
            f"❌ All retry attempts failed for @{username} (took {total_time:.1f}s)")
        return False

    def get_user_from_database(self, username):
        """Check if user exists in database and return their info"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT username, followed_at, follow_back_status, dm_status, dm_message 
                FROM processing_queue 
                WHERE username = ?
            """, (username,))

            result = cursor.fetchone()
            if result:
                return {
                    'username': result[0],
                    'followed_at': result[1],
                    'follow_back_status': result[2],
                    'dm_status': result[3],
                    'dm_message': result[4],
                    'exists': True
                }
            else:
                return {'exists': False}

        except Exception as e:
            logging.error(f"❌ Error checking database for @{username}: {e}")
            return {'exists': False}
        finally:
            if conn:
                conn.close()

    def add_user_to_database(self, username, followed_at=None):
        """Add a new user to the processing_queue table"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Use current time if no follow date provided
            if not followed_at:
                followed_at = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO processing_queue 
                (username, followed_at, follow_back_status, fresh_lead)
                VALUES (?, ?, 'yes', 1)
            """, (username, followed_at))

            conn.commit()
            logging.info(f"✅ Added @{username} to database as new follower")
            return True

        except sqlite3.IntegrityError:
            logging.info(f"ℹ️ @{username} already exists in database")
            return False
        except Exception as e:
            logging.error(f"❌ Error adding @{username} to database: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_user_follow_back_status(self, username):
        """Update user to show they followed back (since they're in the follower list)"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE processing_queue 
                SET follow_back_status = 'yes', 
                    follow_back_checked_at = ?,
                    fresh_lead = 1
                WHERE username = ?
            """, (datetime.now().isoformat(), username))

            conn.commit()
            logging.info(f"✅ Updated @{username} follow-back status to 'yes'")
            return True

        except Exception as e:
            logging.error(
                f"❌ Error updating follow-back status for @{username}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def process_follower_list(self, follower_usernames, max_users=None, start_from=0):
        """
        Process a list of Instagram followers

        Args:
            follower_usernames: List of usernames to process
            max_users: Maximum number of users to process (None = all)
            start_from: Index to start from (for resuming)
        """

        logging.info(f"🚀 Starting New Follower Processing...")
        logging.info(
            f"📊 Total followers to process: {len(follower_usernames)}")
        if max_users:
            logging.info(f"📏 Limited to: {max_users} users")
        if start_from > 0:
            logging.info(f"🔄 Starting from index: {start_from}")

        # Initialize database schema
        self.ensure_fresh_lead_column()

        # Setup browser
        self.setup_driver()

        try:
            # Login to Instagram
            if not self.login_to_instagram():
                logging.error("❌ Failed to login. Stopping processing.")
                return

            # Determine account mode for DM generation
            account_mode = 'local' if self.username == 'cocos_pt_studio' else 'online'
            logging.info(f"🎯 Account mode: {account_mode}")

            # Process statistics
            stats = {
                'total_processed': 0,
                'already_in_db': 0,
                'newly_added': 0,
                'already_messaged': 0,
                'bio_analyzed': 0,
                'dms_sent': 0,
                'errors': 0
            }

            # Apply limits
            users_to_process = follower_usernames[start_from:]
            if max_users:
                users_to_process = users_to_process[:max_users]

            logging.info(f"🎯 Processing {len(users_to_process)} users...")

            for i, username in enumerate(users_to_process):
                user_start_time = time.time()
                current_index = start_from + i

                logging.info(f"\n{'='*60}")
                logging.info(f"🔄 Processing #{current_index + 1}: @{username}")
                logging.info(f"{'='*60}")

                try:
                    # Step 1: Check if user exists in database
                    user_info = self.get_user_from_database(username)

                    if user_info['exists']:
                        stats['already_in_db'] += 1
                        logging.info(f"📋 @{username} already in database")

                        # Check if already messaged
                        if user_info.get('dm_status') in ['sent', 'delivered']:
                            stats['already_messaged'] += 1
                            logging.info(
                                f"💬 @{username} already messaged, skipping")
                            stats['total_processed'] += 1
                            continue

                        # 🆕 ADDITIONAL SAFETY CHECK: Check conversation_history table
                        # This catches users who have messages but missing dm_status in processing_queue
                        conn = None
                        try:
                            conn = self.get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT COUNT(*) FROM conversation_history 
                                WHERE ig_username = ? 
                                AND message_text IS NOT NULL 
                                AND message_text != ''
                                AND message_text LIKE '%plant%'
                            """, (username,))
                            existing_messages = cursor.fetchone()[0]

                            if existing_messages > 0:
                                stats['already_messaged'] += 1
                                logging.info(
                                    f"💬 @{username} has {existing_messages} existing messages in conversation_history - skipping to prevent duplicates")

                                # Update dm_status to reflect this
                                cursor.execute("""
                                    UPDATE processing_queue 
                                    SET dm_status = 'already_messaged'
                                    WHERE username = ?
                                """, (username,))
                                conn.commit()

                                stats['total_processed'] += 1
                                continue

                        except Exception as conv_check_error:
                            logging.warning(
                                f"⚠️ Conversation history check error for @{username}: {conv_check_error}")
                        finally:
                            if conn:
                                conn.close()

                        # Update follow-back status since they're in our follower list
                        self.update_user_follow_back_status(username)

                    else:
                        # Step 2: Add new user to database
                        if self.add_user_to_database(username):
                            stats['newly_added'] += 1
                            logging.info(
                                f"🆕 @{username} added to database as new follower")
                        else:
                            logging.warning(
                                f"⚠️ Could not add @{username} to database")

                    # Step 3: Analyze their profile (bio, posts, etc.)
                    logging.info(f"🔍 Analyzing profile for @{username}...")

                    # Check driver health before analysis
                    if not self.restart_driver_if_needed():
                        logging.error(
                            f"❌ Driver unhealthy for @{username}, skipping")
                        stats['errors'] += 1
                        continue

                    bio_analysis_success = self.analyze_user_profile(username)
                    if bio_analysis_success:
                        stats['bio_analyzed'] += 1
                        logging.info(
                            f"📊 Bio analysis completed for @{username}")
                    else:
                        logging.warning(
                            f"⚠️ Bio analysis failed for @{username}, continuing anyway")

                    # Wait between analysis and DM
                    time.sleep(random.uniform(5, 10))

                    # Step 4: Generate personalized DM
                    logging.info(f"💬 Generating DM for @{username}...")
                    dm_message = self.generate_dm_message(
                        username, account_mode)
                    logging.info(f"📝 Generated message: '{dm_message}'")

                    # Step 5: Send DM
                    # Check driver health before DM
                    if not self.restart_driver_if_needed():
                        logging.error(
                            f"❌ Driver unhealthy before DM to @{username}")
                        self.update_dm_status(
                            username, dm_message, 'failed_driver_error')
                        stats['errors'] += 1
                        continue

                    # Reset timer for DM sending (bio analysis can take 10+ minutes)
                    dm_result = self.send_dm_to_user(username, dm_message)

                    if dm_result == True:
                        # Store DM in conversation history
                        self.store_dm_in_conversation_history(
                            username, dm_message)

                        # Update database
                        self.update_dm_status(username, dm_message, 'sent')
                        stats['dms_sent'] += 1

                        logging.info(f"✅ DM sent successfully to @{username}")

                        # Wait between DMs
                        delay = random.uniform(30, 60)
                        logging.info(
                            f"⏳ Waiting {delay:.1f}s before next user...")
                        time.sleep(delay)

                    elif dm_result == 'already_messaged':
                        # Existing conversation found - mark as already messaged
                        self.update_dm_status(username, "", 'already_messaged')
                        stats['already_messaged'] += 1
                        logging.info(
                            f"💬 @{username} already has conversation history - skipped duplicate message")

                    else:
                        # Failed to send DM
                        self.update_dm_status(username, dm_message, 'failed')
                        logging.warning(f"❌ Failed to send DM to @{username}")
                        stats['errors'] += 1

                    stats['total_processed'] += 1

                    # Progress update every 10 users
                    if (i + 1) % 10 == 0:
                        logging.info(f"\n📊 Progress Update:")
                        logging.info(
                            f"   Processed: {stats['total_processed']}")
                        logging.info(f"   DMs sent: {stats['dms_sent']}")
                        logging.info(f"   Errors: {stats['errors']}")

                except Exception as user_error:
                    logging.error(
                        f"❌ Error processing @{username}: {user_error}")
                    stats['errors'] += 1
                    continue
                finally:
                    user_total_time = time.time() - user_start_time
                    logging.info(
                        f"🕒 Processing @{username} took {user_total_time:.1f}s")

            # Final report
            logging.info(f"\n{'='*60}")
            logging.info(f"📊 FINAL PROCESSING REPORT")
            logging.info(f"{'='*60}")
            logging.info(f"Total users processed: {stats['total_processed']}")
            logging.info(f"Already in database: {stats['already_in_db']}")
            logging.info(f"Newly added to database: {stats['newly_added']}")
            logging.info(
                f"Already messaged (database): {stats['already_messaged']}")
            logging.info(f"Bio analyses completed: {stats['bio_analyzed']}")
            logging.info(f"DMs sent successfully: {stats['dms_sent']}")
            logging.info(f"Errors encountered: {stats['errors']}")

            # Enhanced messaging summary
            total_messaging_attempts = stats['dms_sent'] + \
                stats['already_messaged'] + stats['errors']
            if total_messaging_attempts > 0:
                success_rate = (stats['dms_sent'] /
                                total_messaging_attempts) * 100
                logging.info(f"\n📈 MESSAGING STATISTICS:")
                logging.info(f"Messaging attempts: {total_messaging_attempts}")
                logging.info(f"Success rate: {success_rate:.1f}%")
                logging.info(
                    f"Duplicate prevention: {stats['already_messaged']} users already had conversations")

            # Save results
            self._save_processing_results({
                'timestamp': datetime.now().isoformat(),
                'account_username': self.username,
                'account_mode': account_mode,
                'total_followers_provided': len(follower_usernames),
                'start_index': start_from,
                'max_users_limit': max_users,
                'stats': stats,
                'status': 'completed'
            })

        except Exception as e:
            logging.critical(f"❌ Critical error during processing: {e}")
        finally:
            self.teardown_driver()

    def _save_processing_results(self, results):
        """Save processing results to JSON file"""
        try:
            import json
            results_file = "new_follower_processing_results.json"

            # Load existing results
            existing_results = []
            if os.path.exists(results_file):
                try:
                    with open(results_file, 'r') as f:
                        existing_results = json.load(f)
                except json.JSONDecodeError:
                    existing_results = []

            # Add new result
            existing_results.insert(0, results)
            existing_results = existing_results[:10]  # Keep last 10

            # Save
            with open(results_file, 'w') as f:
                json.dump(existing_results, f, indent=2)

            logging.info(f"📁 Results saved to {results_file}")

        except Exception as e:
            logging.error(f"❌ Failed to save results: {e}")


def main():
    # The comprehensive list of followers from Shannon's screenshots
    follower_usernames = [
        'activista',
        '_foradamatrix',
        '_kasantoss_',
        '_parth_1407',
        '100.charity',
        '5889.amine',
        '777_healing_gods_way',
        'a.living.vegan',
        'alanapurceno',
        'ambixoхо_',
        'animals__supporter',
        'aqd2laylaa',
        'asemanenilgun000',
        'ashleyjane429',
        'atheist_vegan',
        'beingbea',
        'berryofstraw',
        'bipedorasurado',
        'black_monkey_go_green',
        'briyapapaya',
        'ca_ra6807',
        'caballerofredynino',
        'cactushonestus',
        'canipetyourdo9',
        'chris_vgn_',
        'christyloves_nature',
        'crimsonedge11',
        'cyribeiro',
        'danda_rionewyork_vegan',
        'darnz',
        'davidfoerster83',
        'diananana_isabel',
        'do.you.vegan.lift.bro',
        'dogs_lover_shelter_account_',
        'durango_girl74',
        'eatyerveggies00',
        'elticovegano',
        'eri_linay',
        'evelynolivaress',
        'fit.vegan.soulmates',
        'fitness_withv21',
        'fitpunkveganchic420',
        'flowerlea44',
        'food_healthy_samira',
        'franciseatsplants',
        'from_scratch0709',
        'furrymunchies.lb',
        'geordiemichaelnic',
        'gpunk74',
        'grantdelilah',
        'grateful_vegan_sunflower',
        'hairguyone1',
        'henry_ngwena_av',
        'hopefulosmosis',
        'iapiisk',
        'iicandii9',
        'interstellarwitch',
        'iwant_tofu',
        'izasobiech',
        'juliehiltonvfta',
        'karivegan8',
        'karolina_bln91',
        'kitgie_fta_163',
        'leahsimoneingham',
        'life.in.fullcolour',
        'like_the_doll_',
        'lilith_is_a_punk',
        'littlecardiffkitchen',
        'livingthat_lablife',
        'lizzie.loves.veg',
        'lozzy8619',
        'lycornh',
        'madly_delicious',
        'mama_mareille',
        'mandi.lea.wilson',
        'marissussmilch',
        'millie_millz83',
        'myvegventures',
        'neferedari',
        'new_horizon_8990',
        'nocturnalcypress',
        'onekdj75',
        'pablocl391',
        'pamyveganstyle',
        'pawperffct',
        'pikapikapixi',
        'pivotwithplants',
        'plantbasedprieta',
        'pluumeria',
        'prettythickveganchick',
        'productividad.calidad95162',
        'quetzallijhonson',
        'ralphguerino2',
        'reinnota',
        'rina269_',
        'rizuraimagar',
        'sahil_8920_',
        'sam_sash',
        'sassafras_with_class',
        'sasuusecret',
        'shesamuraidonna',
        'sisterdelphi',
        'sonia_sheryl',
        'soniasiahpoosh',
        'soyboygainz',
        'sproutandseeds',
        'susanne_v_269',
        'taste_tess',
        'tattooedvegan444',
        'tepsu2',
        'that.vegan.powerlifter',
        'thechiphale',
        'thegeorgiavegan',
        'thesoulfullyvegan',
        'theveganinheels',
        'thompson.robin',
        'tofuteppista',
        'tunangmania',
        'vegancoupleuk',
        'vegancrossfitover65',
        'vegan_fashion_repository',
        'vegan_garden_aesthetic',
        'vegan.grunge',
        'vegan.neen',
        'vegan_porvida',
        'veganaenmcbo',
        'veganbeavercheve',
        'veganelle1',
        'veganer_widerstand',
        'veganhomer',
        'veganinbirkenhead',
        'veganomurciano',
        'vegansoccermom_',
        'vegassistant',
        'veganterf269',
        'vegnamo',
        'velvetkvinde',
        'vgnsocial.app',
        'vicki_123123',
        'violent_deliight',
        'westvirginiaveganfoodie',
        'xcharlybarleyx',
        'xchloe.wardx',
        'yabanks',
        'yalnizgezenin',
        'yeglife20'
    ]

    parser = argparse.ArgumentParser(
        description='Process new Instagram followers')
    parser.add_argument('--account', type=str, choices=['local', 'online'], default='online',
                        help='Account mode: "local" for @cocos_pt_studio, "online" for @cocos_connected')
    parser.add_argument('--max-users', type=int, default=None,
                        help='Maximum number of users to process')
    parser.add_argument('--start-from', type=int, default=0,
                        help='Index to start from (for resuming)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be processed without actually doing it')

    args = parser.parse_args()

    # Set credentials based on account mode
    if args.account == 'local':
        username = "cocos_pt_studio"
        print(f"🏠 LOCAL MODE: Processing followers for @{username}")
    else:
        username = "cocos_connected"
        print(f"🌱 ONLINE MODE: Processing followers for @{username}")

    print(f"\n📊 FOLLOWER PROCESSING PLAN:")
    print(f"   Total followers provided: {len(follower_usernames)}")
    if args.max_users:
        print(f"   Limited to: {args.max_users} users")
    if args.start_from > 0:
        print(f"   Starting from index: {args.start_from}")
    print(f"   Dry run: {'Yes' if args.dry_run else 'No'}")

    if args.dry_run:
        print(f"\n🔍 DRY RUN - Would process these users:")
        users_to_show = follower_usernames[args.start_from:]
        if args.max_users:
            users_to_show = users_to_show[:args.max_users]
        for i, user in enumerate(users_to_show[:20]):  # Show first 20
            print(f"   {args.start_from + i + 1:3d}. @{user}")
        if len(users_to_show) > 20:
            print(f"   ... and {len(users_to_show) - 20} more")
        return

    # Confirm before processing
    users_to_process = follower_usernames[args.start_from:]
    if args.max_users:
        users_to_process = users_to_process[:args.max_users]

    print(f"\n⚠️ About to process {len(users_to_process)} followers.")
    print(f"This will analyze profiles, generate DMs, and send messages.")
    confirm = input("Continue? (y/N): ").strip().lower()

    if confirm != 'y':
        print("❌ Processing cancelled.")
        return

    # Start processing
    processor = NewFollowerProcessor(username=username)
    processor.process_follower_list(
        follower_usernames,
        max_users=args.max_users,
        start_from=args.start_from
    )


if __name__ == "__main__":
    main()
