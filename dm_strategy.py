#!/usr/bin/env python3
"""
DM Strategy Script - Phase 2 of Outreach System
Sends personalized DMs to users we've already followed, with 24-48 hour delay
"""

import sqlite3
import time
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dm_strategy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class DMSender:
    def __init__(self):
        self.driver = None
        self.daily_dm_limit = 20  # Conservative limit
        self.follow_delay_hours = 24  # Wait 24 hours after following before DMing

        # Personalized message templates based on hashtag source - Shannon's authentic voice
        self.message_templates = {
            'vegan_fitness': [
                "Heya! Noticed you're into plant based fitness 🌱 How's your training going?",
                "Hey! Saw you're passionate about vegan fitness, that's solid! How long you been at it?",
                "Hey! Fellow plant based here 🌱 How do you find balancing nutrition and training?"
            ],
            'vegan_lifestyle': [
                "Heya! Love seeing another plant based person 🌱 How long you been vegan?",
                "Hey! Noticed you're passionate about plant based living, that's awesome! What got you into it?",
                "Hey! Fellow vegan here 🌱 Been vegetarian since birth myself, how's your journey been?"
            ],
            'fitness_general': [
                "Hey! Love your fitness content 💪 How's your training been going?",
                "Heya! Noticed you're into fitness, that's awesome! What's your current focus?",
                "Hey! Your fitness journey looks solid 💪 How long you been training?"
            ],
            'nutrition_focused': [
                "Hey! Love your approach to nutrition 🌱 What's your biggest focus right now?",
                "Heya! Noticed you're into clean eating, that's solid! How's it going for you?",
                "Hey! Your nutrition content is great 💚 What's been your biggest game changer?"
            ]
        }

    def get_hashtag_category(self, hashtag):
        """Categorize hashtags to select appropriate message template"""
        vegan_fitness_tags = ['follower_of_buff_vegans',
                              'follower_of_veganfitness', 'follower_of_strengthtraining']
        vegan_lifestyle_tags = ['follower_of_eatveganbabe', 'follower_of_vegan.daily.recipes', 'follower_of_therawadvantage',
                                'plantbasedlifestyle', 'follower_of_vancouverwithlove', 'follower_of_squeakybeanveg']
        nutrition_tags = ['follower_of_cleanfooddirtygirl',
                          'follower_of_elevatenutritionteam', 'follower_of_plantprotein', 'follower_of_tofoo']

        if hashtag in vegan_fitness_tags:
            return 'vegan_fitness'
        elif hashtag in vegan_lifestyle_tags:
            return 'vegan_lifestyle'
        elif hashtag in nutrition_tags:
            return 'nutrition_focused'
        else:
            return 'fitness_general'

    def get_personalized_message(self, hashtag):
        """Get a personalized message based on hashtag source"""
        category = self.get_hashtag_category(hashtag)
        return random.choice(self.message_templates[category])

    def setup_driver(self):
        """Initialize Chrome driver with stealth settings"""
        chrome_options = Options()
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "--user-data-dir=C:/Users/Shannon/AppData/Local/Google/Chrome/User Data Automation")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def login_to_instagram(self):
        """Login to Instagram - reusing login logic from follow_users.py"""
        try:
            logging.info("🔐 Navigating to login page...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            if "instagram.com/accounts/login" not in self.driver.current_url:
                logging.info("✅ Already logged in to Instagram")
                return True

            # Find and fill username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys("cocos_connected")

            # Find and fill password
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys("Shannonb3")

            # Click login
            login_button = self.driver.find_element(
                By.XPATH, "//button[@type='submit']")
            login_button.click()

            time.sleep(8)

            if "/accounts/login" not in self.driver.current_url:
                logging.info("✅ Login successful")
                return True

        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False

    def get_users_ready_for_dm(self):
        """Get users who were followed 24+ hours ago and haven't been DMed"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        # Calculate cutoff time (24 hours ago)
        cutoff_time = (datetime.now() -
                       timedelta(hours=self.follow_delay_hours)).isoformat()

        cursor.execute('''
            SELECT username, hashtag_found, followed_at
            FROM new_leads 
            WHERE followed_at IS NOT NULL 
            AND followed_at < ?
            AND (dm_sent_at IS NULL OR dm_sent_at = '')
            AND follow_status = 'followed'
            ORDER BY followed_at ASC
            LIMIT ?
        ''', (cutoff_time, self.daily_dm_limit))

        users = cursor.fetchall()
        conn.close()
        return users

    def send_dm(self, username, message):
        """Send a DM to a specific user"""
        try:
            # Navigate to user's profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 6))

            # Look for Message button
            message_selectors = [
                "//div[text()='Message']",
                "//button[contains(text(), 'Message')]",
                "[aria-label='Message']"
            ]

            message_button = None
            for selector in message_selectors:
                try:
                    if selector.startswith("//"):
                        message_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        message_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue

            if not message_button:
                logging.warning(
                    f"⚠️ Could not find Message button for @{username}")
                return False

            message_button.click()
            time.sleep(3)

            # Find message input field
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//textarea[@placeholder='Message...']"))
            )

            # Type message
            message_input.send_keys(message)
            time.sleep(2)

            # Send message
            send_button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Send')]")
            send_button.click()

            logging.info(f"✅ Successfully sent DM to @{username}")
            return True

        except Exception as e:
            logging.error(f"❌ Failed to send DM to @{username}: {str(e)}")
            return False

    def update_dm_status(self, username, success=True):
        """Update database with DM status"""
        conn = sqlite3.connect('app/analytics_data_good.sqlite')
        cursor = conn.cursor()

        if success:
            cursor.execute('''
                UPDATE new_leads 
                SET dm_sent_at = ?
                WHERE username = ?
            ''', (datetime.now().isoformat(), username))

        conn.commit()
        conn.close()

    def run_dm_session(self):
        """Main function to run DM session"""
        logging.info("[START] Starting DM session...")

        # Get users ready for DM
        users_ready = self.get_users_ready_for_dm()

        if not users_ready:
            logging.info(
                "📭 No users ready for DM (need 24h delay after following)")
            return

        logging.info(f"🎯 Found {len(users_ready)} users ready for DM")

        # Setup browser and login
        self.setup_driver()

        try:
            if not self.login_to_instagram():
                logging.error("❌ Failed to login. Stopping DM session.")
                return

            successful_dms = 0

            for username, hashtag, followed_at in users_ready:
                try:
                    # Get personalized message
                    message = self.get_personalized_message(hashtag)

                    logging.info(f"🔄 DMing @{username} (from #{hashtag})")
                    logging.info(f"📝 Message: {message[:50]}...")

                    success = self.send_dm(username, message)
                    self.update_dm_status(username, success)

                    if success:
                        successful_dms += 1

                    # Random delay between DMs (60-120 seconds)
                    delay = random.uniform(60, 120)
                    logging.info(
                        f"⏳ Waiting {delay:.1f} seconds before next DM...")
                    time.sleep(delay)

                except Exception as e:
                    logging.error(f"❌ Error processing @{username}: {str(e)}")
                    continue

            logging.info(
                f"✅ DM session complete! Successfully sent {successful_dms}/{len(users_ready)} DMs")

        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    dm_sender = DMSender()
    dm_sender.run_dm_session()
