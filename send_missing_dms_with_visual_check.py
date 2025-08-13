#!/usr/bin/env python3
"""
Send DMs to users who followed back but never received a message.
Includes Gemini visual verification to ensure inbox is empty before sending.
"""
import google.generativeai as genai
from check_daily_follow_backs import DailyFollowBackChecker
import sys
import os
import sqlite3
import time
import tempfile
import base64
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add the project directory to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Import Gemini

# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
MODEL_NAME = "gemini-2.5-flash-lite-preview-06-17"
genai.configure(api_key=GEMINI_API_KEY)


class EnhancedDMSender(DailyFollowBackChecker):
    """Enhanced DM sender with visual verification"""

    def __init__(self):
        super().__init__()
        self.model = genai.GenerativeModel(MODEL_NAME)

    def take_screenshot(self, filename_prefix="inbox_check"):
        """Take a screenshot and return the file path"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                tempfile.gettempdir(), f"{filename_prefix}_{timestamp}.png")

            if self.driver.save_screenshot(screenshot_path):
                print(f"📸 Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                print("❌ Failed to save screenshot")
                return None
        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            return None

    def analyze_inbox_with_gemini(self, screenshot_path, username):
        """Use Gemini to analyze if the inbox is empty"""
        try:
            if not os.path.exists(screenshot_path):
                print(f"❌ Screenshot file not found: {screenshot_path}")
                return False, "Screenshot file not found"

            # Upload the image to Gemini
            uploaded_file = genai.upload_file(
                path=screenshot_path, display_name=f"inbox_check_{username}")

            prompt = f"""
Look at this Instagram DM inbox screenshot for user '{username}'.

I need you to determine if this inbox is COMPLETELY EMPTY (no messages have been sent yet).

IMPORTANT CRITERIA:
- If you see ANY previous messages (from Shannon or the user), return "HAS_MESSAGES"
- If the inbox shows "No messages" or appears completely empty with no conversation history, return "EMPTY_INBOX"
- If you see a message composition area but no previous messages, return "EMPTY_INBOX"

Look carefully for:
- Any message bubbles or chat history
- Any text indicating previous conversations
- Time stamps from previous messages
- Profile pictures with message threads

Respond with ONLY one of these exact phrases:
- "EMPTY_INBOX" - if there are no previous messages at all
- "HAS_MESSAGES" - if there are any previous messages visible

Username being checked: {username}
"""

            response = self.model.generate_content([uploaded_file, prompt])

            # Clean up uploaded file
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass

            if response and response.text:
                result = response.text.strip().upper()
                print(f"🤖 Gemini analysis for {username}: {result}")

                if "EMPTY_INBOX" in result:
                    return True, "Inbox is empty - safe to send DM"
                elif "HAS_MESSAGES" in result:
                    return False, "Inbox has previous messages - skipping"
                else:
                    print(f"⚠️ Unexpected Gemini response: {result}")
                    return False, f"Unexpected response: {result}"
            else:
                print("❌ No response from Gemini")
                return False, "No response from Gemini"

        except Exception as e:
            print(f"❌ Gemini analysis error: {e}")
            return False, f"Analysis error: {str(e)}"

    def navigate_to_user_dm(self, username):
        """Navigate to a specific user's DM inbox"""
        try:
            print(f"🔍 Navigating to {username}'s DM inbox...")

            # Go to Instagram DMs
            dm_url = "https://www.instagram.com/direct/inbox/"
            self.driver.get(dm_url)
            time.sleep(3)

            # Handle any popups
            self.handle_dm_interface_popups()

            # Search for the user
            search_box_selectors = [
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
                'input[placeholder*="search"]',
                'div[role="textbox"]'
            ]

            search_box = None
            for selector in search_box_selectors:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue

            if not search_box:
                print("❌ Could not find search box")
                return False

            # Clear and type username
            search_box.clear()
            time.sleep(1)
            search_box.send_keys(username)
            time.sleep(2)

            # Look for the user in search results
            user_selectors = [
                f'div[role="button"]:has-text("{username}")',
                f'span:has-text("{username}")',
                f'a[href*="{username}"]'
            ]

            # Wait for search results and click the user
            try:
                # Try to find the user in search results
                user_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//span[contains(text(), '{username}')]"))
                )
                user_element.click()
                time.sleep(3)
                print(f"✅ Successfully navigated to {username}'s DM")
                return True
            except:
                print(f"❌ Could not find {username} in search results")
                return False

        except Exception as e:
            print(f"❌ Error navigating to {username}'s DM: {e}")
            return False

    def send_dm_with_verification(self, username, message):
        """Send DM with visual verification that inbox is empty"""
        try:
            print(f"\n🔄 Processing {username} with visual verification...")

            # Navigate to user's DM inbox
            if not self.navigate_to_user_dm(username):
                return False, "Failed to navigate to DM inbox"

            # Take screenshot of the inbox
            screenshot_path = self.take_screenshot(f"inbox_check_{username}")
            if not screenshot_path:
                return False, "Failed to take screenshot"

            # Analyze with Gemini
            is_empty, analysis_result = self.analyze_inbox_with_gemini(
                screenshot_path, username)

            # Clean up screenshot
            try:
                os.remove(screenshot_path)
            except:
                pass

            if not is_empty:
                print(f"⏭️ Skipping {username}: {analysis_result}")
                return False, f"Inbox not empty: {analysis_result}"

            print(
                f"✅ Inbox verified empty for {username} - proceeding with DM")

            # Send the DM using the existing method
            dm_success = self.send_dm_to_user(username, message)

            if dm_success:
                return True, "DM sent successfully after verification"
            else:
                return False, "DM sending failed after verification"

        except Exception as e:
            print(f"❌ Error in send_dm_with_verification for {username}: {e}")
            return False, f"Verification error: {str(e)}"


def send_missing_dms_with_visual_check():
    print("🔄 Sending DMs with Gemini visual verification...")

    # Get users who need DMs (all 52: failed + never attempted)
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    c.execute("""
        SELECT username, followed_at, follow_back_checked_at, dm_status
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending' OR dm_status LIKE '%failed%')
        ORDER BY follow_back_checked_at DESC
    """)

    users_needing_dms = c.fetchall()
    conn.close()

    if not users_needing_dms:
        print("✅ No users need DMs - all caught up!")
        return

    print(f"📋 Found {len(users_needing_dms)} users who need DMs:")
    # Show first 10
    for username, followed_at, checked_at, dm_status in users_needing_dms[:10]:
        status_display = dm_status if dm_status else "NULL"
        print(
            f"  • {username} (followed: {followed_at[:10]}, status: {status_display})")

    if len(users_needing_dms) > 10:
        print(f"  ... and {len(users_needing_dms) - 10} more")

    # Confirm before proceeding
    response = input(
        f"\n🤖 Send DMs to these {len(users_needing_dms)} users with Gemini verification? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled by user")
        return

    # Initialize the enhanced sender
    sender = EnhancedDMSender()

    try:
        # Setup Instagram driver
        try:
            sender.setup_driver()
            if not sender.driver:
                print("❌ Failed to setup Instagram driver")
                return
            print("✅ Instagram driver setup successful")
        except Exception as e:
            print(f"❌ Failed to setup Instagram driver: {e}")
            return

        if not sender.login_to_instagram():
            print("❌ Failed to login to Instagram")
            return

        success_count = 0
        skipped_count = 0
        failed_count = 0

        # Process each user
        for username, followed_at, checked_at, current_dm_status in users_needing_dms:
            try:
                # Generate personalized DM
                dm_message = sender.generate_dm_message(username, "business")

                # Send DM with visual verification
                success, result_message = sender.send_dm_with_verification(
                    username, dm_message)

                if success:
                    # Mark as fresh lead and store conversation
                    sender.mark_user_as_fresh_lead(username)
                    sender.store_dm_in_conversation_history(
                        username, dm_message)

                    # Update DM status in database
                    sender.update_dm_status(username, dm_message, "sent")

                    print(f"✅ {username}: DM sent successfully")
                    success_count += 1

                elif "Inbox not empty" in result_message:
                    # Update status to show it was skipped due to existing messages
                    sender.update_dm_status(
                        username, "", "skipped_has_messages")
                    print(f"⏭️ {username}: Skipped - {result_message}")
                    skipped_count += 1

                else:
                    # Update status to show it failed
                    sender.update_dm_status(
                        username, dm_message, f"failed_verification: {result_message}")
                    print(f"❌ {username}: Failed - {result_message}")
                    failed_count += 1

                # Small delay between users
                time.sleep(2)

            except Exception as e:
                print(f"❌ Error processing {username}: {e}")
                sender.update_dm_status(
                    username, "", f"failed_exception: {str(e)}")
                failed_count += 1

        print(f"\n📊 FINAL RESULTS:")
        print(f"   ✅ Successfully sent: {success_count}")
        print(f"   ⏭️ Skipped (has messages): {skipped_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📈 Total processed: {len(users_needing_dms)}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        # Always cleanup
        sender.teardown_driver()


if __name__ == "__main__":
    send_missing_dms_with_visual_check()
