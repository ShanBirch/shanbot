#!/usr/bin/env python3
"""
Potential Clients Story Commentor
Targets high-potential fitness clients by analyzing their Instagram stories and sending personalized DMs.

This script:
1. Reads from Shannon's dashboard SQLite database
2. Filters for leads with coaching scores >= 70
3. Views their stories and analyzes content with Gemini AI
4. Sends contextual DMs to engage potential fitness clients

Created for Shannon's Coco's Connected fitness business
"""

import json
import os
import time
import random
import logging
import traceback
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    ElementClickInterceptedException, StaleElementReferenceException,
    InvalidSessionIdException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import threading
import uuid
import re
import sqlite3
import base64
from collections import Counter
import msvcrt

# Configuration
CONFIG = {
    "instagram_url": "https://www.instagram.com",
    # Path for ChromeDriver
    "chromedriver_path": "C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
    "results_dir": "potential_clients_results",
    "processed_users_file": "processed_potential_clients.json",
    "target_users_file": "target_potential_clients.json",
    # This will be the JSON for campaign analytics
    "analytics_file": "app/analytics_data_good.json",
    # Read from environment variable
    "instagram_username": os.getenv('INSTAGRAM_USERNAME', 'cocos_connected'),
    # Read from environment variable
    "instagram_password": os.getenv('INSTAGRAM_PASSWORD', 'Shannonb3')
}

# Set up logging


def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv(
    'GEMINI_API_KEY', 'AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y')
genai.configure(api_key=GEMINI_API_KEY)

# Helper functions from story1.py


def sanitize_message(message):
    """Remove problematic characters from the message while preserving emojis."""
    # First, remove any asterisks or markdown formatting symbols
    cleaned = message.replace('*', '').replace('_', '').replace('#', '')

    # Remove other problematic characters but KEEP emojis (Unicode range U+1F600-U+1F64F, U+1F300-U+1F5FF, U+1F680-U+1F6FF, U+1F700-U+1F77F, U+1F780-U+1F7FF, U+1F800-U+1F8FF, U+1F900-U+1F9FF, U+1FA00-U+1FA6F, U+1FA70-U+1FAFF, U+2600-U+26FF, U+2700-U+27BF)
    allowed_chars = []
    for char in cleaned:
        char_code = ord(char)
        # Keep basic ASCII, extended ASCII, and emoji ranges
        if (char_code < 127 or  # Basic ASCII
            (0x1F600 <= char_code <= 0x1F64F) or  # Emoticons
            (0x1F300 <= char_code <= 0x1F5FF) or  # Misc Symbols
            (0x1F680 <= char_code <= 0x1F6FF) or  # Transport
            (0x1F700 <= char_code <= 0x1F77F) or  # Alchemical
            (0x1F780 <= char_code <= 0x1F7FF) or  # Geometric Shapes Extended
            (0x1F800 <= char_code <= 0x1F8FF) or  # Supplemental Arrows-C
            # Supplemental Symbols and Pictographs
            (0x1F900 <= char_code <= 0x1F9FF) or
            (0x1FA00 <= char_code <= 0x1FA6F) or  # Chess Symbols
            # Symbols and Pictographs Extended-A
            (0x1FA70 <= char_code <= 0x1FAFF) or
            (0x2600 <= char_code <= 0x26FF) or   # Misc symbols
                (0x2700 <= char_code <= 0x27BF)):    # Dingbats
            allowed_chars.append(char)
        elif char_code < 256:  # Extended ASCII
            allowed_chars.append(char)

    return ''.join(allowed_chars).strip()


def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time to appear more human-like"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time


def wait_for_user_input(message):
    """Wait for the user to press Enter before continuing."""
    print("\n" + "!" * 50)
    print(message)
    print("Press ENTER to continue...")
    print("!" * 50 + "\n")
    # Wait for Enter key press
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':  # Enter key
                break
        time.sleep(0.1)
    print("Continuing...")


def print_step(message):
    """Print a step with clear formatting"""
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


def print_substep(message):
    """Print a substep with clear formatting"""
    print("-" * 30)
    print(message)
    print("-" * 30)


class PauseMonitor:
    """
    Simple background monitor that continuously ensures a story stays paused.
    """

    def __init__(self, driver):
        self.driver = driver
        self.monitoring_active = False
        self.monitoring_thread = None
        self.check_interval = 0.8  # Check every 0.8 seconds
        self.pause_count = 0  # Track how many times we've re-paused

    def start_monitoring(self):
        """Start continuous pause monitoring in background thread."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.pause_count = 0
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("🔄 Pause monitoring started")

    def stop_monitoring(self):
        """Stop pause monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        if self.pause_count > 0:
            print(
                f"🔄 Pause monitoring stopped (re-paused {self.pause_count} times)")
        else:
            print("🔄 Pause monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that runs in background thread."""
        while self.monitoring_active:
            try:
                # Check if story is still paused
                if not self._is_story_paused_quick():
                    # Story became unpaused, re-pause it
                    self._re_pause_story()
                    self.pause_count += 1
                    print(
                        f"⚠️ Story auto-advanced, re-paused (#{self.pause_count})")

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"⚠️ Pause monitoring error: {e}")
                time.sleep(1)  # Longer sleep on error

    def _is_story_paused_quick(self):
        """Quick check if story is paused - simplified version."""
        try:
            # Look for play button (most reliable indicator of pause)
            play_indicators = self.driver.find_elements(By.XPATH,
                                                        "//div[contains(@aria-label, 'Play')] | //*[name()='svg' and contains(@aria-label, 'Play')]")

            if play_indicators:
                for indicator in play_indicators:
                    if indicator.is_displayed():
                        return True

            # If no clear play button found, assume it might be playing
            return False

        except Exception:
            # If we can't check, assume it's playing to be safe
            return False

    def _re_pause_story(self):
        """Re-pause the story."""
        try:
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.1)  # Brief pause after re-pausing
        except Exception as e:
            print(f"⚠️ Failed to re-pause story: {e}")


class ConversationAnalytics:
    def __init__(self):
        self.analytics_db = os.path.join(os.path.expanduser(
            "~"), "OneDrive", "Desktop", "shanbot", "app", "analytics_data_good.sqlite")
        self.conversation_metrics = {}
        self.global_metrics = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_story_comments": 0,
            "total_corrections": 0,
            "correction_percentage": 0.0
        }
        self.correction_patterns = {}  # Track common correction reasons
        self.user_preferences = {}     # Learn user preferences
        self._analytics_loaded_successfully = False  # New flag
        self._analytics_file_existed_at_load = False  # New flag
        self.load_analytics()

    def load_analytics(self):
        """Load analytics data from SQLite database."""
        try:
            if os.path.exists(self.analytics_db):
                self._analytics_file_existed_at_load = True  # Mark that file existed
                print(f"Loading analytics from: {self.analytics_db}")

                conn = sqlite3.connect(self.analytics_db)
                cursor = conn.cursor()

                # Load conversation metrics from users table using metrics_json column
                cursor.execute("SELECT ig_username, metrics_json FROM users")
                rows = cursor.fetchall()

                for ig_username, metrics_json in rows:
                    conversation_history = []

                    # First, try to get conversation history from metrics_json
                    if metrics_json:
                        try:
                            metrics_data = json.loads(metrics_json)
                            conversation_history = metrics_data.get(
                                "conversation_history", [])
                        except json.JSONDecodeError:
                            print(
                                f"⚠️ Could not parse metrics for {ig_username}")

                    # Also load conversation history from messages table
                    cursor.execute("""
                        SELECT timestamp, type, text FROM messages
                        WHERE ig_username = ?
                        ORDER BY timestamp ASC
                    """, (ig_username,))
                    message_rows = cursor.fetchall()

                    # Convert messages to conversation history format and add to existing history
                    for timestamp, msg_type, text in message_rows:
                        conversation_history.append({
                            "timestamp": timestamp,
                            "type": msg_type,
                            "text": text
                        })

                    # Store the combined conversation history
                    self.conversation_metrics[ig_username] = {
                        "metrics": {
                            "ig_username": ig_username,
                            "conversation_history": conversation_history
                        }
                    }

                conn.close()
                self._analytics_loaded_successfully = True  # Mark success
                print(
                    f"Successfully loaded analytics data from SQLite ({len(self.conversation_metrics)} users)")
            else:
                print("No existing analytics database found. Starting fresh.")
                # Starting fresh is also a "successful" load state
                self._analytics_loaded_successfully = True
                self._analytics_file_existed_at_load = False
        except Exception as e:
            print(
                f"CRITICAL Error loading analytics: {e}. Analytics will not be saved by this script instance to prevent data loss.")
            self._analytics_loaded_successfully = False  # Mark failure

    def export_analytics(self):
        """Save analytics data to SQLite database."""
        # Safety check: If loading failed AND the file existed before, do NOT export to prevent overwrite.
        if not self._analytics_loaded_successfully and self._analytics_file_existed_at_load:
            print(
                "CRITICAL: Analytics loading failed, but database previously existed. Skipping export to prevent data loss.")
            return

        try:
            conn = sqlite3.connect(self.analytics_db)
            cursor = conn.cursor()

            # Update conversation metrics in existing users table
            for username, data in self.conversation_metrics.items():
                conversation_history = data.get(
                    "metrics", {}).get("conversation_history", [])

                # Get existing metrics_json for this user
                cursor.execute(
                    "SELECT metrics_json FROM users WHERE ig_username = ?", (username,))
                result = cursor.fetchone()

                if result and result[0]:
                    # Update existing metrics_json with new conversation_history
                    try:
                        existing_metrics = json.loads(result[0])
                        existing_metrics["conversation_history"] = conversation_history
                        updated_metrics_json = json.dumps(existing_metrics)
                    except json.JSONDecodeError:
                        # If existing data is corrupted, create new metrics
                        updated_metrics_json = json.dumps(
                            {"conversation_history": conversation_history})
                else:
                    # Create new metrics_json
                    updated_metrics_json = json.dumps(
                        {"conversation_history": conversation_history})

                # Update the user's metrics_json
                cursor.execute('''
                    UPDATE users SET metrics_json = ? WHERE ig_username = ?
                ''', (updated_metrics_json, username))

                # If no rows were updated, the user doesn't exist, so insert them
                if cursor.rowcount == 0:
                    cursor.execute('''
                        INSERT INTO users (ig_username, metrics_json) VALUES (?, ?)
                    ''', (username, updated_metrics_json))

            conn.commit()
            conn.close()
            print("Successfully exported analytics data to SQLite")
        except Exception as e:
            print(f"Error exporting analytics: {e}")

    def update_story_interaction(self, username: str, story_description: str, comment_text: str, change_reason: str = None):
        """Record a story interaction in analytics (conversation_history only)."""
        current_timestamp = datetime.now(timezone.utc).isoformat()

        # Initialize metrics if this is a new user (minimal profile)
        if username not in self.conversation_metrics:
            self.conversation_metrics[username] = {
                "metrics": {
                    "ig_username": username,
                    "conversation_history": []
                }
            }
            print(f"Created new profile for {username}")

        # Update existing user's metrics
        metrics = self.conversation_metrics[username]["metrics"]

        # Create the analytics text
        analytics_text = f"[Commented on story] (story was about: {story_description}): {comment_text}"

        # Add change reason if provided
        if change_reason:
            analytics_text += f" [Manual edit reason: {change_reason}]"

        # Add the story comment to conversation history with description
        metrics["conversation_history"].append({
            "timestamp": current_timestamp,
            "type": "ai",
            "text": analytics_text
        })

        # Also save directly to messages table
        try:
            conn = sqlite3.connect(self.analytics_db)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (ig_username, timestamp, type, text)
                VALUES (?, ?, ?, ?)
            """, (username, current_timestamp, "ai", analytics_text))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error saving to messages table: {e}")

        # Update global metrics
        self.global_metrics["total_story_comments"] += 1
        if change_reason:
            self.global_metrics["total_corrections"] += 1
            self.track_correction_pattern(
                change_reason, story_description, comment_text)

        # Calculate correction percentage
        if self.global_metrics["total_story_comments"] > 0:
            self.global_metrics["correction_percentage"] = (
                self.global_metrics["total_corrections"] /
                self.global_metrics["total_story_comments"] * 100
            )

        # Save changes to users table as well
        self.export_analytics()
        print(f"Updated analytics for {username}'s story comment")

        # Show performance stats periodically
        if self.global_metrics["total_story_comments"] % 10 == 0:
            self.show_performance_stats()

    def track_correction_pattern(self, reason: str, story_description: str, comment_text: str):
        """Track patterns in user corrections to improve AI prompts."""
        if reason not in self.correction_patterns:
            self.correction_patterns[reason] = {
                "count": 0,
                "examples": []
            }

        self.correction_patterns[reason]["count"] += 1
        self.correction_patterns[reason]["examples"].append({
            "story": story_description[:100],  # First 100 chars
            "original_comment": comment_text[:50]  # First 50 chars
        })

        # Keep only last 5 examples to avoid memory bloat
        if len(self.correction_patterns[reason]["examples"]) > 5:
            self.correction_patterns[reason]["examples"] = self.correction_patterns[reason]["examples"][-5:]

    def show_performance_stats(self):
        """Display current bot performance statistics."""
        total = self.global_metrics["total_story_comments"]
        corrections = self.global_metrics["total_corrections"]
        percentage = self.global_metrics["correction_percentage"]

        print("\n" + "📊" * 30)
        print("🤖 BOT PERFORMANCE STATS")
        print("📊" * 30)
        print(f"📝 Total Comments: {total}")
        print(f"✏️ Total Corrections: {corrections}")
        print(f"📈 Correction Rate: {percentage:.1f}%")

        if self.correction_patterns:
            print("\n🔍 Top Correction Reasons:")
            sorted_patterns = sorted(self.correction_patterns.items(),
                                     key=lambda x: x[1]["count"], reverse=True)
            for reason, data in sorted_patterns[:3]:
                print(f"  • {reason}: {data['count']} times")

        print("📊" * 30 + "\n")

    def get_adaptive_prompt_additions(self) -> str:
        """Generate additional prompt text based on user correction patterns."""
        if not self.correction_patterns:
            return ""

        additions = []

        # Get most common correction reasons
        sorted_patterns = sorted(self.correction_patterns.items(),
                                 key=lambda x: x[1]["count"], reverse=True)

        for reason, data in sorted_patterns[:3]:  # Top 3 correction reasons
            if data["count"] >= 2:  # Only include if happened multiple times
                if "too generic" in reason.lower():
                    additions.append(
                        "- Avoid generic comments like 'Looking good!' - be more specific about what you see")
                elif "wrong tone" in reason.lower():
                    additions.append(
                        "- Match the energy/tone of the story content")
                elif "not relevant" in reason.lower():
                    additions.append(
                        "- Ensure comment directly relates to what's visible in the story")
                elif "too long" in reason.lower():
                    additions.append(
                        "- Keep comments very short (1-5 words max)")
                elif "emoji" in reason.lower():
                    additions.append(
                        "- Be more careful with emoji usage - match the story mood")
                elif "no question" in reason.lower():
                    additions.append(
                        "- Always try to include a short question to encourage engagement")
                elif "question too long" in reason.lower():
                    additions.append(
                        "- Keep questions very short (2-4 words max)")

        if additions:
            return "\n\nBased on recent corrections, please also:\n" + "\n".join(additions)

        return ""


# Initialize analytics (global instance)
analytics = ConversationAnalytics()


class ClientDataManager:
    """Handles reading client data from the analytics JSON file"""

    def __init__(self):
        self.analytics_file = CONFIG["analytics_file"]
        self.analytics_data = self._load_analytics_data()

    @staticmethod
    def get_coaching_potential_category(score):
        """Categorize users based on their coaching potential score"""
        if score >= 80:
            return "🌟 Excellent Prospect"
        elif score >= 65:
            return "🔥 High Potential"
        elif score >= 50:
            return "⭐ Good Potential"
        elif score >= 35:
            return "💡 Some Potential"
        else:
            return "❌ Low Potential"

    def _load_analytics_data(self) -> Dict:
        """Loads analytics data from the JSON file."""
        if not os.path.exists(self.analytics_file):
            logger.error(f"Analytics file not found: {self.analytics_file}")
            return {}
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(
                f"Error loading analytics data from {self.analytics_file}: {e}")
            return {}

    def get_high_potential_clients(self, min_coaching_score: int = 85) -> List[Dict]:
        """
        Get leads with high potential from the SQLite database using alternative criteria.
        Since coaching scores don't exist yet, we'll use fitness indicators and engagement.

        Args:
            min_coaching_score: Minimum coaching score threshold (default: 85) - used as engagement threshold

        Returns:
            List of dict containing client information
        """
        high_potential_clients = []

        try:
            import sqlite3
            conn = sqlite3.connect('app/analytics_data_good.sqlite')
            cursor = conn.cursor()

            # Get users with client analysis data (shows engagement)
            # Exclude Shannon's own accounts and system accounts
            excluded_accounts = [
                'cocos_pt_studio', 'cocos_connected', 'shannonbirch2', 'calorie_tracking']
            placeholders = ','.join(['?' for _ in excluded_accounts])

            cursor.execute(f"""
                SELECT ig_username, metrics_json, client_analysis_json
                FROM users
                WHERE client_analysis_json IS NOT NULL
                AND ig_username IS NOT NULL
                AND ig_username NOT IN ({placeholders})
            """, excluded_accounts)

            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} users with client analysis data")

            for ig_username, metrics_json, client_analysis_json in rows:
                try:
                    # Parse metrics and client analysis
                    metrics = json.loads(metrics_json) if metrics_json else {}
                    client_analysis = json.loads(
                        client_analysis_json) if client_analysis_json else {}

                    # Calculate a potential score based on available indicators
                    potential_score = self._calculate_potential_score(
                        metrics, client_analysis, ig_username)

                    if potential_score >= min_coaching_score:
                        client_info = {
                            'username': ig_username,
                            'score': potential_score,
                            'category': self.get_coaching_potential_category(potential_score),
                            'coaching_analysis': {"score": potential_score, "reasons": []},
                            'profile_bio': client_analysis.get('profile_bio', {}),
                            'interests': client_analysis.get('interests', []),
                            'recent_activities': client_analysis.get('recent_activities', []),
                            'conversation_topics': client_analysis.get('conversation_topics', []),
                            'ig_username': ig_username,
                            'last_interaction': metrics.get('last_interaction_timestamp'),
                            'journey_stage': metrics.get('journey_stage', {})
                        }
                        high_potential_clients.append(client_info)

                except Exception as e:
                    logger.warning(f"Error processing {ig_username}: {e}")
                    continue

            conn.close()

        except Exception as e:
            logger.error(f"Database error: {e}")
            return []

        # Sort by calculated potential score (highest first)
        high_potential_clients.sort(key=lambda x: x['score'], reverse=True)

        logger.info(
            f"Found {len(high_potential_clients)} high-potential clients with calculated score >= {min_coaching_score}")
        return high_potential_clients

    def _calculate_potential_score(self, metrics: dict, client_analysis: dict, username: str) -> int:
        """Calculate a potential score based on available data indicators"""
        score = 50  # Base score

        # Check conversation engagement
        total_messages = metrics.get('total_messages', 0)
        if total_messages > 10:
            score += 15
        elif total_messages > 5:
            score += 10
        elif total_messages > 2:
            score += 5

        # Check fitness-related topics
        conversation_topics = client_analysis.get('conversation_topics', [])
        interests = client_analysis.get('interests', [])

        fitness_keywords = ['fitness', 'gym', 'workout', 'exercise', 'training', 'muscle',
                            'weight', 'health', 'nutrition', 'diet', 'protein', 'vegan', 'vegetarian']

        fitness_mentions = 0
        for topic in conversation_topics + interests:
            topic_lower = str(topic).lower()
            for keyword in fitness_keywords:
                if keyword in topic_lower:
                    fitness_mentions += 1
                    break

        if fitness_mentions >= 3:
            score += 20
        elif fitness_mentions >= 2:
            score += 15
        elif fitness_mentions >= 1:
            score += 10

        # Check if they have posts analyzed (shows Instagram engagement)
        if client_analysis.get('posts_analyzed', 0) > 0:
            score += 10

        # Check for specific fitness indicators
        lifestyle_indicators = client_analysis.get('lifestyle_indicators', [])
        for indicator in lifestyle_indicators:
            indicator_lower = str(indicator).lower()
            if any(keyword in indicator_lower for keyword in fitness_keywords):
                score += 5

        # Check for coaching inquiries
        coaching_inquiries = metrics.get('coaching_inquiry_count', 0)
        if coaching_inquiries > 0:
            score += 25

        # Check if they mentioned weight loss, muscle gain, etc.
        if metrics.get('weight_loss_mentioned', False):
            score += 15
        if metrics.get('muscle_gain_mentioned', False):
            score += 15
        if metrics.get('vegan_topic_mentioned', False):
            score += 10  # Good fit for Shannon's specialty

        # Limit score to reasonable range
        return min(max(score, 0), 100)


class PotentialClientAnalytics:
    """Handles analytics and tracking for the story targeting campaign"""

    def __init__(self):
        self.analytics_file = CONFIG["analytics_file"]
        self.analytics_data = self.load_analytics()

        # Ensure essential top-level keys exist in analytics_data
        if "campaign_stats" not in self.analytics_data:
            self.analytics_data["campaign_stats"] = {
                "total_users_targeted": 0,
                "stories_analyzed": 0,
                "messages_sent": 0,
                "successful_interactions": 0,
                "campaign_start_date": datetime.now().isoformat()
            }
        if "user_interactions" not in self.analytics_data:
            self.analytics_data["user_interactions"] = {}
        if "daily_stats" not in self.analytics_data:
            self.analytics_data["daily_stats"] = {}

    def load_analytics(self) -> Dict:
        """Load analytics data from file"""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Default analytics structure
        return {
            "campaign_stats": {
                "total_users_targeted": 0,
                "stories_analyzed": 0,
                "messages_sent": 0,
                "successful_interactions": 0,
                "campaign_start_date": datetime.now().isoformat()
            },
            "user_interactions": {},
            "daily_stats": {}
        }

    def save_analytics(self):
        """Save analytics data to file"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")

    def update_user_interaction(self, username: str, story_description: str,
                                message_sent: str, success: bool):
        """Update user interaction data"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Update user-specific data
        if username not in self.analytics_data["user_interactions"]:
            self.analytics_data["user_interactions"][username] = {
                "first_contact": datetime.now().isoformat(),
                "interactions": []
            }

        interaction = {
            "date": datetime.now().isoformat(),
            "story_description": story_description,
            "message_sent": message_sent,
            "success": success
        }

        self.analytics_data["user_interactions"][username]["interactions"].append(
            interaction)

        # Update daily stats
        if today not in self.analytics_data["daily_stats"]:
            self.analytics_data["daily_stats"][today] = {
                "users_targeted": 0,
                "stories_analyzed": 0,
                "messages_sent": 0,
                "successful_interactions": 0
            }

        self.analytics_data["daily_stats"][today]["users_targeted"] += 1
        self.analytics_data["daily_stats"][today]["stories_analyzed"] += 1

        if message_sent:
            self.analytics_data["daily_stats"][today]["messages_sent"] += 1
            self.analytics_data["campaign_stats"]["messages_sent"] += 1

        if success:
            self.analytics_data["daily_stats"][today]["successful_interactions"] += 1
            self.analytics_data["campaign_stats"]["successful_interactions"] += 1

        # Update campaign totals
        self.analytics_data["campaign_stats"]["total_users_targeted"] += 1
        self.analytics_data["campaign_stats"]["stories_analyzed"] += 1

        self.save_analytics()


class PotentialClientBot:
    """Main bot class for targeting potential clients through stories"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.analytics = PotentialClientAnalytics()
        self.db_manager = ClientDataManager()
        self.processed_users_file = "processed_users_today.json"
        self.processed_users = self.load_processed_users()

        # Configure Gemini
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # Initialize PauseMonitor
        self.pause_monitor = None  # Will be initialized after driver setup
        print("✔️ Pause monitoring system initialized (pending driver)")

        # Set to track usernames that have already received DMs in this session
        self.processed_usernames = set()
        self.max_tracked_usernames = 1000
        self.load_processed_usernames()

        logger.info("PotentialClientBot initialized")

    def load_processed_users(self) -> set:
        """Load list of users already processed today"""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"processed_users_{today}.json"

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return set()

    def save_processed_users(self):
        """Save list of processed users"""
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"processed_users_{today}.json"

        try:
            with open(file_path, 'w') as f:
                json.dump(list(self.processed_users), f)
        except Exception as e:
            logger.error(f"Error saving processed users: {e}")

    def get_target_users(self, min_coaching_score: int = 70) -> List[Dict]:
        """
        Get target users from database with coaching score >= min_coaching_score

        Args:
            min_coaching_score: Minimum coaching score threshold

        Returns:
            List of target user data
        """
        high_potential_clients = self.db_manager.get_high_potential_clients(
            min_coaching_score)

        # Filter out already processed users
        target_users = [
            client for client in high_potential_clients
            if client['ig_username'] not in self.processed_users
        ]

        logger.info(
            f"Found {len(target_users)} unprocessed high-potential clients")
        return target_users

    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        try:
            print_substep("Setting up Chrome WebDriver...")
            service = Service(executable_path=CONFIG["chromedriver_path"])
            chrome_options = Options()

            # Use unique Chrome profile to prevent conflicts
            unique_id = str(uuid.uuid4())[:8]
            profile_dir = os.path.join(os.path.expanduser(
                "~"), "OneDrive", "Desktop", "shanbot", f"chrome_profile_{unique_id}")
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f"--user-data-dir={profile_dir}")

            print(f"Using Chrome profile: {profile_dir}")

            # Enhanced anti-detection measures
            chrome_options.add_argument(
                '--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option(
                'useAutomationExtension', False)
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--lang=en-US")

            # Add random viewport size to appear more human-like
            viewports = [
                (1920, 1080),
                (1366, 768),
                (1536, 864),
                (1440, 900),
                (1280, 720)
            ]
            viewport = random.choice(viewports)
            chrome_options.add_argument(
                f"--window-size={viewport[0]},{viewport[1]}")

            # Add modern user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

            # Initialize the driver
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)

            # Store profile directory for cleanup
            self.profile_dir = profile_dir

            # Additional anti-detection measures via CDP
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = {
                    runtime: {}
                };
                """
            })

            self.wait = WebDriverWait(self.driver, 10)
            print("ChromeDriver initialized successfully")
            time.sleep(random.uniform(1, 2))

            # Initialize pause monitor with new driver
            self.pause_monitor = PauseMonitor(self.driver)
            print("✔️ Pause monitoring system initialized")

            return True

        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            return False

    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def safe_screenshot(self, filename: str):
        """Take screenshot safely"""
        try:
            self.driver.save_screenshot(f"screenshots/{filename}")
        except Exception as e:
            logger.warning(f"Could not take screenshot: {e}")

    def _handle_potential_dialogs(self):
        """Handle common Instagram dialogs that might appear after login or navigation."""
        print_substep("Handling potential dialogs (if any)...")

        # Common dialog selectors and actions
        dialog_actions = [
            {
                "name": "Save Login Info",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Not now')]"]},
            {
                "name": "Turn On Notifications",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Not now')]"]},
            {
                "name": "Add to Home Screen",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Cancel')]"]}
        ]

        for dialog in dialog_actions:
            try:
                for selector in dialog["selectors"]:
                    try:
                        element = WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            print(
                                f"📱 Handling dialog: {dialog['name']}")
                            element.click()
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                continue

        print_substep("Finished checking for dialogs.")

    def login_to_instagram(self) -> bool:
        """Login to Instagram"""
        print_step("AUTOMATIC INSTAGRAM LOGIN")
        max_login_attempts = 3

        for login_attempt in range(max_login_attempts):
        try:
                print_substep(
                    f"Login attempt {login_attempt + 1}/{max_login_attempts}")

                # Navigate to Instagram
            self.driver.get("https://www.instagram.com/accounts/login/")
                print_substep("Navigated to Instagram login page...")
                time.sleep(random.uniform(3, 5))

                # Handle potential dialogs first
                self._handle_potential_dialogs()

                # Check if already logged in
                if self._check_if_logged_in():
                    print("✔️ Already logged in!")
                    return True

                # Find username field with multiple selectors
                username_field = self._find_login_field("username")
                if not username_field:
                    print("❌ Could not find username field")
                    if login_attempt < max_login_attempts - 1:
                        continue
                    return False

                # Find password field
                password_field = self._find_login_field("password")
                if not password_field:
                    print("❌ Could not find password field")
                    if login_attempt < max_login_attempts - 1:
                        continue
                    return False

                # Clear and fill username
                print_substep("Entering username...")
            username_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                for char in CONFIG["instagram_username"]:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                time.sleep(random.uniform(0.8, 1.5))

                # Clear and fill password
                print_substep("Entering password...")
            password_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                for char in CONFIG["instagram_password"]:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                time.sleep(random.uniform(1.0, 2.0))

                # Find and click login button
                login_button = self._find_login_button()
                if not login_button:
                    print("❌ Could not find login button")
                    if login_attempt < max_login_attempts - 1:
                        continue
                    return False

                print_substep("Clicking login button...")
            login_button.click()
                time.sleep(random.uniform(3, 5))

                # Check for 2FA or other security checks
                if self._handle_security_challenges():
                    print("✔️ Handled security challenges")

                # Wait and verify login success
                max_wait_time = 30  # 30 seconds
                start_time = time.time()

                while time.time() - start_time < max_wait_time:
                    if self._check_if_logged_in():
                        print("✔️ Login successful!")
                        time.sleep(2)  # Brief pause after login
                        self._handle_potential_dialogs()  # Handle post-login dialogs
                        return True

                    # Check for login errors
                    if self._check_login_errors():
                        print("❌ Login error detected")
                        if login_attempt < max_login_attempts - 1:
                            print(
                                f"Retrying login (attempt {login_attempt + 2}/{max_login_attempts})...")
                            time.sleep(random.uniform(3, 5))
                            break
                        return False

                    time.sleep(1)

                # If we get here, login timed out
                print(f"❌ Login timeout on attempt {login_attempt + 1}")
                if login_attempt < max_login_attempts - 1:
                    time.sleep(random.uniform(2, 4))

            except Exception as e:
                print(f"❌ Login attempt {login_attempt + 1} failed: {e}")
                if login_attempt < max_login_attempts - 1:
                    time.sleep(random.uniform(2, 4))

        print("❌ All login attempts failed")
        return False

    def _find_login_field(self, field_type):
        """Find login fields with multiple selector strategies."""
        if field_type == "username":
            selectors = [
                "//input[@name='username']",
                "//input[@aria-label='Phone number, username, or email']",
                "//input[@placeholder='Phone number, username, or email']",
                "//input[@placeholder='Username']",
                "//input[@type='text' and contains(@class, '_aa4b')]",
                "//input[contains(@class, '_aa4b') and @type='text']",
                "//input[@autocomplete='username']",
                "//form//input[@type='text'][1]",
                "//div[@role='main']//input[@type='text']"
            ]
        else:  # password
            selectors = [
                "//input[@name='password']",
                "//input[@aria-label='Password']",
                "//input[@placeholder='Password']",
                "//input[@type='password']",
                "//input[contains(@class, '_aa4b') and @type='password']",
                "//form//input[@type='password']",
                "//div[@role='main']//input[@type='password']"
            ]

        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element.is_displayed():
                    print(
                        f"✔️ Found {field_type} field using selector: {selector}")
                    return element
            except:
                continue

        return None

    def _find_login_button(self):
        """Find login button with multiple selector strategies."""
        button_selectors = [
            "//button[@type='submit']",
            "//button[contains(text(), 'Log in') or contains(text(), 'Log In') or contains(text(), 'LOGIN')]",
            "//button[contains(@class, '_acan') and contains(@class, '_acap')]",
            "//button[contains(@class, '_acan')]",
            "//div[@role='button' and contains(text(), 'Log in')]",
            "//input[@type='submit']",
            "//form//button[contains(@class, '_a9_') or contains(@class, 'sqdOP')]",
            "//button[contains(@class, 'L3NKy')]",
            "//div[contains(@class, 'L3NKy')]//button",
            "//form//button[last()]"]

        for selector in button_selectors:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element.is_displayed():
                    print(f"✔️ Found login button using selector: {selector}")
                    return element
            except:
                continue

        return None

    def _check_if_logged_in(self):
        """Check if user is already logged in by looking for home page indicators."""
        logged_in_indicators = [
            "//a[@href='/']",  # Home button
            "//div[@role='tablist']",  # Navigation bar
            "//svg[@aria-label='Home']",  # Home icon
            "//a[contains(@href, '/direct/')]",  # Messages link
            "//span[text()='Home']",  # Home text
            # Home link in nav
            "//div[contains(@class, 'x1iyjqo2')]//a[@href='/']",
            "//nav//a[contains(@role, 'link')]",  # Navigation home
            "//header//a[@href='/']"  # Header home link
        ]

        for indicator in logged_in_indicators:
            try:
                element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                if element and element.is_displayed():
                    return True
            except:
                continue

        # Also check URL - if we're not on login/accounts page, likely logged in
        current_url = self.driver.current_url.lower()
        if 'login' not in current_url and 'accounts' not in current_url and 'instagram.com' in current_url:
            # Additional check - look for any story or feed content
            try:
                content_indicators = [
                    "//section",  # Main content sections
                    "//article",  # Posts
                    "//div[contains(@class, '_aarf')]"  # Story tray
                ]
                for indicator in content_indicators:
                    if self.driver.find_elements(By.XPATH, indicator):
                        return True
            except:
                pass

        return False

    def _check_login_errors(self):
        """Check for login error messages."""
        error_selectors = [
            "//div[contains(@class, 'piCib')]",  # Error message container
            "//p[contains(@class, 'piCib')]",   # Error paragraph
            "//div[contains(text(), 'incorrect') or contains(text(), 'wrong') or contains(text(), 'error')]",
            "//p[contains(text(), 'incorrect') or contains(text(), 'wrong') or contains(text(), 'error')]",
            "//div[@role='alert']",  # Alert messages
            "//div[contains(@class, 'error')]",
            "//span[contains(text(), 'Sorry') or contains(text(), 'incorrect')]"
        ]

        for selector in error_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        error_text = element.text.strip()
                        if any(keyword in error_text.lower() for keyword in ['incorrect', 'wrong', 'error', 'sorry', 'try again']):
                            print(f"⚠️ Login error detected: {error_text}")
                return True
            except:
                continue

                return False

    def _handle_security_challenges(self):
        """Handle 2FA, suspicious login, and other security challenges."""
        print_substep("Checking for security challenges...")

        # Wait a moment for any security pages to load
        time.sleep(3)

        # Check for 2FA page
        twofa_indicators = [
            "//input[@name='verificationCode']",
            "//input[@placeholder='Security code']",
            "//input[@aria-label='Security code']",
            "//h1[contains(text(), 'Two-Factor')]",
            "//div[contains(text(), 'Enter the 6-digit code')]",
            "//div[contains(text(), 'security code')]"
        ]

        for indicator in twofa_indicators:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                if element.is_displayed():
                    print("🔐 2FA challenge detected")
                    return self._handle_2fa_challenge()
            except:
                continue

        # Check for suspicious login detection
        suspicious_indicators = [
            "//div[contains(text(), 'suspicious') or contains(text(), 'Suspicious')]",
            "//h2[contains(text(), 'Help Us Confirm')]",
            "//div[contains(text(), 'unusual activity')]",
            "//button[contains(text(), 'This Was Me') or contains(text(), 'this was me')]"
        ]

        for indicator in suspicious_indicators:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, indicator))
                )
                if element.is_displayed():
                    print("🛡️ Suspicious login challenge detected")
                    return self._handle_suspicious_login()
            except:
                continue

        # Check for "Save Login Info" dialog
        save_login_selectors = [
            "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
            "//button[contains(text(), 'Not now')]"]

        for selector in save_login_selectors:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if element.is_displayed():
                    print("💾 Save login info dialog detected - clicking 'Not Now'")
                    element.click()
                    time.sleep(1)
                    break
            except:
                continue

        return True

    def _handle_2fa_challenge(self):
        """Handle 2FA challenge with user input."""
        print("🔐 2FA Required - Please check your authenticator app or SMS")

        max_2fa_attempts = 3
        for attempt in range(max_2fa_attempts):
            try:
                # Get 2FA code from user
                code = input(
                    f"➤ Enter 6-digit 2FA code (attempt {attempt + 1}/{max_2fa_attempts}): ").strip()

                if len(code) != 6 or not code.isdigit():
                    print("❌ Invalid code format. Please enter exactly 6 digits.")
                    continue

                # Find 2FA input field
                code_field_selectors = [
                    "//input[@name='verificationCode']",
                    "//input[@placeholder='Security code']",
                    "//input[@aria-label='Security code']",
                    "//input[@type='text' and @maxlength='6']"
                ]

                code_field = None
                for selector in code_field_selectors:
                    try:
                        code_field = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue

                if not code_field:
                    print("❌ Could not find 2FA code input field")
                    continue

                # Enter code
                code_field.clear()
                time.sleep(0.5)
                for char in code:
                    code_field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.2))

                time.sleep(1)

                # Find and click submit button
                submit_selectors = [
                    "//button[@type='submit']",
                    "//button[contains(text(), 'Confirm') or contains(text(), 'Submit')]",
                    "//button[contains(@class, '_acan')]"
                ]

                for selector in submit_selectors:
                    try:
                        submit_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        submit_button.click()
                        break
                    except:
                        continue

                time.sleep(3)

                # Check if 2FA was successful
                if self._check_if_logged_in():
                    print("✔️ 2FA successful!")
                    return True

                # Check for 2FA error
                if self._check_2fa_error():
                    print("❌ Invalid 2FA code, please try again")
                    continue

            except KeyboardInterrupt:
                print("\n🛑 2FA cancelled by user")
                return False
        except Exception as e:
                print(f"❌ 2FA attempt {attempt + 1} failed: {e}")

        print("❌ 2FA failed after maximum attempts")
        return False

    def _check_2fa_error(self):
        """Check for 2FA error messages."""
        error_selectors = [
            "//div[contains(text(), 'Please check the code') or contains(text(), 'incorrect')]",
            "//p[contains(text(), 'Please check the code') or contains(text(), 'incorrect')]",
            "//div[@role='alert']"
        ]

        for selector in error_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and 'code' in element.text.lower():
                        return True
            except:
                continue
        return False

    def _handle_suspicious_login(self):
        """Handle suspicious login detection."""
        print("🛡️ Handling suspicious login detection...")

        # Look for "This Was Me" or similar button
        confirm_selectors = [
            "//button[contains(text(), 'This Was Me') or contains(text(), 'this was me')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Yes')]"
        ]

        for selector in confirm_selectors:
            try:
                button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if button.is_displayed():
                    print("✔️ Clicking 'This Was Me' button")
                    button.click()
                    time.sleep(2)
                    return True
            except:
                continue

        print("⚠️ Could not find confirmation button for suspicious login")
            return False

    def navigate_to_user_profile(self, username: str) -> bool:
        """Navigate to a user's profile"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            logger.info(f"Navigating to profile: {username}")

            self.driver.get(profile_url)
            self.random_delay(3, 5)

            # Check if profile exists and is accessible
            if "Sorry, this page isn't available" in self.driver.page_source:
                logger.warning(
                    f"Profile {username} not found or not accessible")
                return False

            # Check if account is private
            if "This Account is Private" in self.driver.page_source:
                logger.warning(f"Profile {username} is private")
                return False

            logger.info(f"Successfully navigated to {username}'s profile")

            # Attempt to dismiss the "Turn on Notifications" popup if it appears
            try:
                not_now_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[text()='Not Now']"))
                )
                not_now_button.click()
                logger.info("Dismissed 'Turn on Notifications' popup.")
                self.random_delay(1, 2)  # Small delay after dismissing
            except TimeoutException:
                logger.info("'Turn on Notifications' popup did not appear.")
            except Exception as e:
                logger.warning(f"Error dismissing notification popup: {e}")

            return True

        except Exception as e:
            logger.error(f"Error navigating to profile {username}: {e}")
            return False

    def analyze_profile_for_stories(self, username: str) -> Dict:
        """Analyze profile screenshot to detect stories and highlights using Gemini AI"""
        try:
            print_substep("Taking profile screenshot for analysis...")

            # Take screenshot of profile page
            profile_screenshot = f"screenshots/profile_analysis_{username}_{int(time.time())}.png"
            os.makedirs("screenshots", exist_ok=True)

            if not self.capture_verified_screenshot(profile_screenshot):
                logger.error("Failed to capture profile screenshot")
                return {"has_story": False, "has_highlights": False, "action": "skip"}

            print_substep("Analyzing profile with Gemini AI...")

            # Load the image for Gemini
            with open(profile_screenshot, 'rb') as f:
                image_data = f.read()

            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }

            analysis_prompt = f"""You are analyzing an Instagram profile page screenshot for {username}. I need you to detect if there are stories or highlights available.

🚨 CRITICAL: ACTIVE STORIES ALWAYS TAKE ABSOLUTE PRIORITY OVER HIGHLIGHTS! 🚨

STEP 1 - STORY DETECTION (CHECK THIS FIRST!):
Look at the main profile picture at the top. Is there ANY colored border around it?
- RED, PINK, ORANGE, PURPLE gradient ring = ACTIVE STORY
- Even a THIN colored line = ACTIVE STORY  
- Rainbow colors = ACTIVE STORY
- ANY color other than plain gray/white = ACTIVE STORY
- If you see ANY hint of color around the profile picture → HAS_STORY: True

STEP 2 - HIGHLIGHT DETECTION:
Only look at highlights if NO story was found in Step 1.
- Small circular icons below the profile with text labels
- Usually in a row beneath the bio

MANDATORY PRIORITY LOGIC:
🔥 IF HAS_STORY = True → ACTION MUST BE "click_story" (ignore highlights completely)
🔥 IF HAS_STORY = False AND highlights exist → ACTION: "click_highlight"
🔥 IF HAS_STORY = False AND no highlights → ACTION: "skip"

Please analyze this profile and respond in this EXACT format:

HAS_STORY: [True if there's ANY colored ring/border around profile picture, False only if completely plain]
HAS_HIGHLIGHTS: [True if circular highlight icons visible below profile, False if not]
HIGHLIGHT_COUNT: [Number of highlight circles you see, 0 if none]
DESCRIPTION: [Describe what you see around the profile picture border specifically, then mention highlights if any]
ACTION: [MUST be "click_story" if HAS_STORY is True, otherwise "click_highlight" if highlights exist, otherwise "skip"]

🔍 EXAMINE THE PROFILE PICTURE BORDER VERY CAREFULLY FOR ANY COLORED RING!
"""

            try:
                response = self.model.generate_content(
                    contents=[
                        {"text": analysis_prompt},
                        {"inline_data": image_part}
                    ],
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 300,
                    }
                )

                if not response or not response.text:
                    logger.error("Empty response from Gemini")
                    return {"has_story": False, "has_highlights": False, "action": "skip"}

                # Parse response
                response_text = response.text.strip()
                logger.info(f"Gemini analysis response: {response_text}")

                analysis = {"has_story": False, "has_highlights": False,
                            "action": "skip", "highlight_count": 0}

                for line in response_text.split('\n'):
                    line = line.strip()
                    if line.startswith('HAS_STORY:'):
                        analysis['has_story'] = 'true' in line.lower()
                    elif line.startswith('HAS_HIGHLIGHTS:'):
                        analysis['has_highlights'] = 'true' in line.lower()
                    elif line.startswith('HIGHLIGHT_COUNT:'):
                        try:
                            count = int(line.split(':')[1].strip())
                            analysis['highlight_count'] = count
                        except:
                            analysis['highlight_count'] = 0
                    elif line.startswith('DESCRIPTION:'):
                        analysis['description'] = line.replace(
                            'DESCRIPTION:', '').strip()
                    elif line.startswith('ACTION:'):
                        action = line.replace('ACTION:', '').strip().lower()
                        if action in ['click_story', 'click_highlight', 'skip']:
                            analysis['action'] = action

                # Add debugging output to understand AI decisions
                print(f"🔍 AI Analysis Results for {username}:")
                print(f"   HAS_STORY: {analysis['has_story']}")
                print(f"   HAS_HIGHLIGHTS: {analysis['has_highlights']}")
                print(f"   ACTION: {analysis['action']}")
                print(f"   DESCRIPTION: {analysis.get('description', 'N/A')}")

                # Validate the priority logic
                if analysis['has_story'] and analysis['action'] != 'click_story':
                    print(
                        f"⚠️ WARNING: Story detected but action is '{analysis['action']}' - forcing to click_story")
                    analysis['action'] = 'click_story'

                logger.info(f"Profile analysis for {username}: {analysis}")
                return analysis

                            except Exception as e:
                logger.error(f"Error analyzing profile with Gemini: {e}")
                return {"has_story": False, "has_highlights": False, "action": "skip"}

        except Exception as e:
            logger.error(f"Error in profile analysis for {username}: {e}")
            return {"has_story": False, "has_highlights": False, "action": "skip"}

    def click_user_story(self, username: str) -> bool:
        """Analyze profile visually and click story or highlight if available"""
        try:
                    logger.info(
                f"Analyzing {username}'s profile for stories/highlights...")

            # First, ensure we're on the user's profile
            if not self.navigate_to_user_profile(username):
                return False

            # Analyze the profile page with AI
            analysis = self.analyze_profile_for_stories(username)

            if analysis['action'] == 'skip':
                logger.info(
                    f"No stories or highlights available for {username} - skipping")
                return False
            elif analysis['action'] == 'click_story':
                logger.info(
                    f"Active story detected for {username} - attempting to click")
                return self._click_story_element(username)
            elif analysis['action'] == 'click_highlight':
                logger.info(
                    f"Highlights available for {username} - attempting to click first highlight")
                return self._click_highlight_element(username)
            else:
                logger.warning(
                    f"Unknown action for {username}: {analysis['action']}")
                return False

                except Exception as e:
            logger.error(f"Error in click_user_story for {username}: {e}")
            return False

    def _click_story_element(self, username: str) -> bool:
        """Click on the story ring around profile picture with enhanced targeting"""
        try:
            print(f"🎯 Targeting story ring for {username}...")

            # Enhanced selectors prioritizing story rings and canvas elements
            story_selectors = [
                # Look for canvas elements first (story rings are often canvas)
                "//header//canvas[1]",
                "//header//canvas/..",
                # Profile picture with story ring (button containers)
                "//header//div[@role='button'][.//canvas]",
                "//header//div[@role='button'][.//img[contains(@alt, 'profile')]]",
                # Direct profile picture containers
                "//header//img[contains(@alt, 'profile picture')]/../..",
                "//header//img[contains(@alt, 'profile picture')]/..",
                # Alternative story ring selectors
                "//header//div[contains(@style, 'gradient') or contains(@class, 'gradient')]",
                "//a[contains(@href, '/{username}/')]//div[.//canvas]".format(
                    username=username)
            ]

            for selector in story_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(
                        f"   Found {len(elements)} elements with selector: {selector}")

                    for i, element in enumerate(elements):
                        try:
                            # Enhanced checks for story elements
                            is_story_candidate = False

                            # Check for canvas children (story rings)
                            canvas_children = element.find_elements(
                                By.XPATH, ".//canvas")
                            if canvas_children:
                                print(
                                    f"   Element {i} has {len(canvas_children)} canvas children - likely story ring")
                                is_story_candidate = True

                            # Check if it's a clickable button
                            if element.get_attribute('role') == 'button':
                                print(f"   Element {i} is a clickable button")
                                is_story_candidate = True

                            # Check position - story elements should be near top of page
                            try:
                                location = element.location
                                if location['y'] < 400:  # Top area of profile
                                    print(
                                        f"   Element {i} is in top area (y={location['y']})")
                                    is_story_candidate = True
                            except:
                                pass

                            if is_story_candidate:
                                print(
                                    f"🎯 Clicking story candidate element {i} for {username}")

                                # Scroll element into view first
                self.driver.execute_script(
                                    "arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)

                                # Click the element
                                element.click()
            self.random_delay(2, 4)

                                # Verify the story opened
                                if self._verify_story_opened(username):
                                    print(
                                        f"✅ Successfully opened story for {username}")
                                    return True
                                else:
                                    print(
                                        f"⚠️ Click registered but story didn't open - trying next element")

                        except Exception as e:
                            print(f"   Error with element {i}: {e}")
                            continue

                except Exception as e:
                    print(f"   Selector failed: {e}")
                    continue

            logger.warning(
                f"Could not find clickable story element for {username}")
            return False

        except Exception as e:
            logger.error(f"Error clicking story for {username}: {e}")
            return False

    def _click_highlight_element(self, username: str) -> bool:
        """Click on the first highlight reel"""
        try:
            # Look for highlight elements below the profile
            highlight_selectors = [
                # General highlight buttons
                "//div[contains(@class, 'x6s0dn4')]//div[@role='button']",
                # Highlight with images
                "//section//div[@role='button'][.//img]",
                # Circular highlight buttons
                "//div[@role='button'][contains(@style, 'border-radius')]"
            ]

            for selector in highlight_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    # Skip the first few elements which might be profile picture/story
                    # Look for elements that seem like highlights (further down the page)
                    # Skip first 2 elements
                    for i, element in enumerate(elements[2:], 2):
                        try:
                            # Check if this element has characteristics of a highlight
                            location = element.location
                            if location['y'] > 300:  # Elements below profile area
                        logger.info(
                                    f"Clicking highlight element #{i} for {username}")
                                element.click()
                                self.random_delay(2, 4)
                                return self._verify_story_opened(username)
                        except Exception as e:
                            logger.debug(f"Highlight element #{i} failed: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Highlight selector failed: {e}")
                        continue

                    logger.warning(
                f"Could not find clickable highlight element for {username}")
                    return False

        except Exception as e:
            logger.error(f"Error clicking highlight for {username}: {e}")
            return False

    def _verify_story_opened(self, username: str) -> bool:
        """Verify that a story or highlight opened successfully"""
        try:
            # First check URL - most reliable indicator
            current_url = self.driver.current_url
            if 'stories/' in current_url or '/highlights/' in current_url:
                logger.info(
                    f"Story/highlight URL detected for {username}: {current_url}")
                return True

            # Check for story viewer indicators
            story_indicators = [
                "//div[@role='dialog']",  # Story viewer dialog
                "//div[@role='progressbar']",  # Progress bars
                "//section[contains(@class, 'x78zum5')]",  # Story section
                # Alternative story container
                "//div[contains(@class, 'x1qjc9v5')]",
                "//canvas",  # Progress rings
                "//video",  # Video content
                "//img[contains(@alt, 'Story')]"  # Story images
            ]

            for indicator in story_indicators:
                try:
                    elements = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, indicator))
                    )
                    if elements:
                        logger.info(
                            f"Story/highlight opened successfully for {username} (found {len(elements)} {indicator} elements)")
                return True
            except TimeoutException:
                    continue

                logger.warning(
                f"Could not verify story/highlight opened for {username}")
                return False

        except Exception as e:
            logger.error(f"Error verifying story opened for {username}: {e}")
            return False

    def pause_story(self) -> bool:
        """Pause the story to analyze it"""
        try:
            # Try to pause the story by clicking on it
            story_container = self.driver.find_element(
                By.XPATH, "//div[contains(@role, 'dialog')]")
            story_container.click()
            self.random_delay(1, 2)

            logger.info("Story paused for analysis")
            return True

        except Exception as e:
            logger.error(f"Error pausing story: {e}")
            return False

    def analyze_story_with_gemini(self, image_path: str, username: str) -> Optional[Dict]:
        """Analyze story image with Gemini AI using the same method as story1.py"""
        print_step("ANALYZING IMAGE WITH GEMINI")
        try:
            print_substep("Preparing image for Gemini...")

            # Load the image file for Gemini
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Create a Gemini image part - using the correct format
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }

            if not image_data:
                logger.error("No image data found")
                return None

            print_substep("Sending request to Gemini...")

            # Get adaptive prompt additions based on user corrections
            adaptive_additions = analytics.get_adaptive_prompt_additions()

            # Create the system prompt (adapted for Shannon's fitness coaching context)
            system_prompt = f"""You are analyzing an Instagram story screenshot posted by {username}. I need four pieces of information:

            1. DESCRIPTION: Briefly describe what is happening in the MAIN story in the image in 2-3 sentences. Be specific about visible content. NOTE: The screenshot may include other stories in the background or UI elements - focus ONLY on the main central story being viewed.
            
            2. IS_NEGATIVE: Based on the visual content and any text, is the primary subject of this story related to war, violence, tragedy, or other significantly negative themes? Respond True or False.
            
            3. IS_REEL: Does the visual content appear to be a reshared video, a "Reel" from another creator, or a screen recording of a video, rather than original content directly from this user's camera? Respond True or False.

            4. COMMENT: Create a friendly, casual comment in Shannon's style (Female Australian Vegetarian Personal Trainer from Melbourne - modern, energetic, supportive vibe) to respond to this story:
               
               **CRITICAL: ANALYZE THE ACTUAL CONTENT FIRST**
               - Look carefully at what's actually happening in the image
               - Consider the setting, activity, objects, and context
               - Your comment must be directly relevant to what you see
               
               **COMMENT RULES:**
               - If IS_REEL is True:
                 * Use a single emoji reaction (😂, 💯, 🔥) OR
                 * If there's clear text within the reel, create a 1-4 word REACTION to that text
                 * REACTION examples: "So true!", "Love this!", "Facts!", "Exactly!", "This!" 
                 * NEVER just repeat the text from the reel - always react TO it
               
               - If IS_REEL is False (original content):
                 * Keep it 3-8 words maximum
                 * Be specific to what you actually see in the image
                 * Examples of GOOD contextual comments:
                   - For gym/workout: "Get it!", "Crushing it!", "Strong work!"
                   - For food: "Looks amazing!", "Yum!", "Plant power!"
                   - For lifestyle: "Love this!", "Beautiful!", "Goals!"
                   - For travel: "Gorgeous!", "Amazing spot!", "Enjoy!"
                 
               **QUESTION STRATEGY (Use questions frequently for engagement):**
               - About 60% of your comments should include a short question
               - Keep questions to 2-4 words maximum
               - Make questions relevant to what you actually see
               - Examples: "Morning session?", "Homemade?", "New recipe?", "Favorite spot?"
               
               **ALWAYS:**
               - Match the energy of the content
               - Be authentic to what's shown
               - Keep it short and genuine
               - Use 0-1 emojis maximum
               - NO asterisks or special formatting
               - NEVER leave the comment empty
               - Focus on fitness/health when relevant (Shannon's specialty)

            Respond in this EXACT format:
            DESCRIPTION: [brief description of main story content]
            IS_NEGATIVE: [True or False]
            IS_REEL: [True or False]
            COMMENT: [short friendly comment, preferably with a relevant question]
            {adaptive_additions}"""

            analysis_instruction = f"Analyze this Instagram story screenshot from {username} according to my instructions above, providing DESCRIPTION, IS_NEGATIVE, IS_REEL, and COMMENT sections."

            # Add retry logic for Gemini API
            max_api_retries = 3
            api_retry_count = 0
            api_success = False

            while api_retry_count < max_api_retries and not api_success:
                try:
                    print(
                        f"Gemini API attempt {api_retry_count + 1}/{max_api_retries}...")

                    # Use the correct Gemini API format
                    response = self.model.generate_content(
                        contents=[
                            {"text": system_prompt},
                            {"text": analysis_instruction},
                            {"inline_data": image_part}
                        ],
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 500,
                        }
                    )

                    if response and response.text:
                        api_success = True
                        print("✅ Gemini API call successful")
                        break
                    else:
                        print(
                            f"❌ Empty response from Gemini API (attempt {api_retry_count + 1})")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            time.sleep(2)

                except Exception as api_error:
                    print(
                        f"❌ Gemini API error (attempt {api_retry_count + 1}): {api_error}")
                    api_retry_count += 1
                    if api_retry_count < max_api_retries:
                        time.sleep(2)

            if not api_success:
                logger.error("All Gemini API attempts failed")
                return None

            # Parse the response
            response_text = response.text.strip()
            print_substep("Parsing Gemini response...")

            # Parse the formatted response
            analysis_lines = response_text.split('\n')
            analysis = {}

            for line in analysis_lines:
                if line.startswith('DESCRIPTION:'):
                    analysis['content_description'] = line.replace(
                        'DESCRIPTION:', '').strip()
                elif line.startswith('IS_NEGATIVE:'):
                    is_negative = line.replace(
                        'IS_NEGATIVE:', '').strip().lower()
                    analysis['is_negative'] = is_negative == 'true'
                elif line.startswith('IS_REEL:'):
                    is_reel = line.replace('IS_REEL:', '').strip().lower()
                    analysis['is_reel'] = is_reel == 'true'
                elif line.startswith('COMMENT:'):
                    analysis['suggested_message'] = line.replace(
                        'COMMENT:', '').strip()

            # Add fitness relevance scores for compatibility
            description = analysis.get('content_description', '').lower()
            fitness_keywords = ['gym', 'workout', 'fitness', 'exercise',
                                'training', 'protein', 'diet', 'nutrition', 'health', 'muscle']
            fitness_score = sum(
                1 for keyword in fitness_keywords if keyword in description)
            analysis['fitness_relevance_score'] = min(
                fitness_score + 3, 10)  # Base score + keywords
            # Simple mapping
            analysis['client_potential_score'] = analysis['fitness_relevance_score']

            logger.info(f"Story analysis complete for {username}")
            logger.info(
                f"Description: {analysis.get('content_description', 'N/A')}")
            logger.info(
                f"Suggested comment: {analysis.get('suggested_message', 'N/A')}")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing story with Gemini: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def send_story_reply(self, message: str) -> bool:
        """Send a reply to the story using proven story1.py method"""
        try:
            print(f"💬 Sending story reply: {message[:50]}...")
            
            # Use story1.py proven selectors
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//form//textarea"
            ]

            max_send_retries = 2
            
            for attempt in range(max_send_retries):
                try:
                    print(f"   Attempt {attempt + 1}/{max_send_retries}")
                    
                    # Find reply box
                    reply_box = None
                    for selector in reply_box_selectors:
                        try:
                            reply_box = WebDriverWait(self.driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            print(f"   ✅ Found reply box with: {selector}")
                            break
                        except:
                            continue

                    if not reply_box:
                        print(f"   ❌ Could not find reply box on attempt {attempt+1}")
                        time.sleep(0.5)
                        continue

                    # Clear and type message character by character (story1.py method)
                    reply_box.clear()
                    print(f"   📝 Typing message character by character...")
                    
                    for char_send in message:
                        reply_box.send_keys(char_send)
                        time.sleep(random.uniform(0.05, 0.15))  # Human-like typing

                    # Brief pause before sending
                    time.sleep(random.uniform(0.3, 0.7))
                    
                    # Send with Enter key (story1.py method)
                    reply_box.send_keys(Keys.ENTER)
                    time.sleep(random.uniform(0.8, 1.2))

                    print(f"   ✅ Message sent successfully: {message}")
                    return True

                except Exception as e_send:
                    print(f"   ⚠️ Send attempt {attempt+1} failed: {e_send}")
                    time.sleep(1)

            print(f"❌ Failed to send message after {max_send_retries} attempts")
            return False

        except Exception as e:
            logger.error(f"Error sending story reply: {e}")
            return False

    def generate_fallback_message(self, user_info: Dict) -> str:
        """Generate a personalized message for users without stories"""
        try:
            username = user_info['ig_username']
            coaching_score = user_info['score']
            interests = user_info.get('interests', [])
            coaching_analysis = user_info.get('coaching_analysis', {})

            # Get specific indicators from coaching analysis
            vegan_indicators = coaching_analysis.get(
                'vegetarian_vegan_indicators', '')
            fitness_indicators = coaching_analysis.get(
                'fitness_health_indicators', '')

            prompt = f"""
            Create a personalized Instagram DM for reaching out to a high-potential vegetarian/vegan fitness coaching prospect.

            CLIENT INFO:
            Username: {username}
            Coaching Score: {coaching_score}/100 (Excellent Prospect)
            Interests: {', '.join(interests) if interests else 'General wellness focus'}
            Vegetarian/Vegan Indicators: {vegan_indicators or 'Plant-based lifestyle interest'}
            Fitness Indicators: {fitness_indicators or 'Health and wellness focused'}

            REQUIREMENTS:
            - Keep it under 120 words
            - Be genuine and personal, not salesy
            - Mention Shannon's vegetarian fitness coaching naturally
            - Reference their interests/lifestyle if available
            - Include a soft call-to-action or question
            - Sound natural and friendly
            - Don't mention seeing their story (they don't have one)

            STYLE: 
            - Shannon is an Australian vegetarian fitness coach
            - Modern, authentic, supportive tone
            - Focus on plant-based fitness and lifestyle

            EXAMPLE TOPICS TO REFERENCE:
            - Plant-based nutrition and fitness
            - Sustainable lifestyle choices
            - Building strength on a vegetarian diet
            - Connecting with like-minded people
            """

            response = self.model.generate_content(prompt)

            if response and response.text:
                message = response.text.strip()
                # Clean up any quotes or formatting
                message = message.replace('"', '').replace('*', '').strip()
                logger.info(f"Generated fallback message for {username}")
                return message
            else:
                # Fallback template
                return f"Hi! I'm Shannon, a vegetarian fitness coach from Australia. I love connecting with people who are into plant-based living and wellness. Would you be interested in chatting about fitness and nutrition? 🌱💪"

        except Exception as e:
            logger.error(f"Error generating fallback message: {e}")
            # Simple fallback
            return f"Hi! I'm Shannon, a vegetarian fitness coach. I'd love to connect with like-minded people who are passionate about plant-based living and fitness! 🌱"

    def send_direct_message(self, username: str, message: str) -> bool:
        """Send a direct message to the user"""
        try:
            # Navigate to user's profile
            if not self.navigate_to_user_profile(username):
                return False

            # Click on Message button
            message_button_selectors = [
                "//div[contains(text(), 'Message')]//parent::button",
                "//button[contains(text(), 'Message')]",
                "//a[contains(@href, '/direct/')]"
            ]

            message_button = None
            for selector in message_button_selectors:
                try:
                    message_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not message_button:
                logger.error(f"Could not find message button for {username}")
                return False

            logger.info(f"Clicking message button for {username}")
            message_button.click()
            self.random_delay(3, 5)

            # Wait for message interface to load
            try:
                message_input = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//div[@contenteditable='true']"))
                )
            except TimeoutException:
                logger.error("Message interface did not load")
                return False

            # Type and send message
            logger.info(f"Sending DM to {username}: {message[:50]}...")
            message_input.click()
            self.random_delay(1, 2)
            message_input.send_keys(message)
            self.random_delay(1, 2)

            # Send the message
            send_button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Send')]")
            send_button.click()
            self.random_delay(2, 3)

            logger.info(f"DM sent successfully to {username}")
            return True

        except Exception as e:
            logger.error(f"Error sending DM to {username}: {e}")
            return False

    def is_story_paused(self):
        """Check if the story is currently paused by looking for pause indicators - IMPROVED VERSION"""
        try:
            # Multiple approaches to detect if story is paused
            pause_indicators_found = False

            # Method 1: Look for play button (most reliable indicator of pause)
            play_button_selectors = [
                "//div[contains(@aria-label, 'Play')]",
                "//*[name()='svg' and contains(@aria-label, 'Play')]",
                "//button[contains(@aria-label, 'Play')]",
                "//*[contains(@class, 'play') and contains(@class, 'button')]"
            ]

            for selector in play_button_selectors:
                try:
                    play_elements = WebDriverWait(self.driver, 0.2).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector))
                    )
                    for element in play_elements:
                        if element.is_displayed():
                            print(
                                "🟡 Story appears to be paused (play button visible)")
                            pause_indicators_found = True
                            break
                    if pause_indicators_found:
                        break
                except:
                    continue

            # Method 2: Check for story progress bar movement (if available)
            if not pause_indicators_found:
                try:
                    # Look for progress bars and check if they seem static
                    progress_selectors = [
                        "//div[contains(@style, 'width') and contains(@style, '%')]",
                        "//div[@role='progressbar']"
                    ]

                    for selector in progress_selectors:
                        try:
                            elements = self.driver.find_elements(
                                By.XPATH, selector)
                            if elements:
                                # Quick check - take two measurements 0.3 seconds apart
                                initial_widths = []
                                for elem in elements[:3]:  # Check first 3 elements
                                    style = elem.get_attribute('style')
                                    if 'width' in style:
                                        initial_widths.append(style)

                                time.sleep(0.3)

                                current_widths = []
                                for elem in elements[:3]:
                                    style = elem.get_attribute('style')
                                    if 'width' in style:
                                        current_widths.append(style)

                                # If widths haven't changed, story might be paused
                                if initial_widths == current_widths and initial_widths:
                                    pause_indicators_found = True
                                    print(
                                        "🟡 Story appears paused (progress bar static)")
                                break
                        except:
                            continue
                except:
                    pass

            return pause_indicators_found

        except Exception as e:
            print(f"⚠️ Error checking pause status: {e}")
            return False  # Default to not paused if we can't tell

    def robust_pause_story(self):
        """Robust story pausing with multiple attempts and verification"""
        try:
            print("🟡 Attempting to pause story...")

            max_attempts = 5
            for attempt in range(max_attempts):
                print(f"   Pause attempt {attempt + 1}/{max_attempts}")

                # Try pausing
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                time.sleep(0.2)  # Give it time to register

                # Check if it worked
                if self.is_story_paused():
                    print(
                        f"✅ Story successfully paused on attempt {attempt + 1}")
                    return True

                # If not paused, try clicking on the story area first, then pause
                if attempt < max_attempts - 1:
                    try:
                        # Click on story area to ensure focus
                        story_container = self.driver.find_element(
                            By.XPATH, "//div[@role='dialog']")
                        story_container.click()
                        time.sleep(0.1)
                    except:
                        # If dialog not found, click on body
                        try:
                            self.driver.find_element(
                                By.TAG_NAME, "body").click()
                            time.sleep(0.1)
                        except:
                            pass

            print(
                f"⚠️ Could not confirm story pause after {max_attempts} attempts")
                return False

        except Exception as e:
            print(f"❌ Error in robust_pause_story: {e}")
                return False

    def has_comment_box(self):
        """Enhanced comment box detection with better selectors"""
        try:
            reply_box_selectors = [
                "//textarea[@placeholder='Reply...']",
                "//textarea[contains(@placeholder, 'Reply')]",
                "//textarea[@autocomplete='off']",
                "//div[@contenteditable='true' and @role='textbox']",
                "//textarea[contains(@class, 'x1i10hfl')]",
                "//form//textarea",
                "//div[contains(@aria-label, 'Add a comment')]//textarea",
                "//textarea[contains(@placeholder, 'Message')]",
                "//input[contains(@placeholder, 'Message')]",
                "//div[contains(@contenteditable, 'true')]"
            ]

            # Try each selector with slightly longer timeout
            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        print(f"✅ Found comment box with selector: {selector}")
                        return True
                except:
                    continue

            print("❌ No comment box found with any selector")
            return False

        except Exception as e:
            print(f"❌ Error in comment box detection: {e}")
                return False

    def extract_instagram_username(self, quiet=False):
        """Extracts the Instagram username directly from the HTML element in the story."""
        try:
            last_extracted_username = getattr(
                self, '_last_extracted_username', None)

            # Save and log the current URL for debugging
            current_url = self.driver.current_url
            if not quiet:
                print(f"Extracting username from story URL: {current_url}")

            # APPROACH 1: Try direct extraction from HTML elements
            selectors = [
                "//span[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w') and contains(@class, 'x6ikm8r') and contains(@class, 'x10wlt62') and contains(@class, 'xlyipyv') and contains(@class, 'xuxw1ft')]",
                "//div[contains(@class, 'x1i10hfl')]//a[starts-with(@href, '/') and not(contains(@href, 'direct'))]",
                "//header//a[starts-with(@href, '/')]",
                "//div[contains(@class, 'x9f619')]//a",
                "//div[contains(@class, 'x3nfvp2')]//span",
                "//div[contains(@aria-labelledby, 'story')]//a"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            # Try to get username from href attribute
                            href = element.get_attribute('href')
                            if href and '/' in href:
                                username_candidate = href.strip(
                                    '/').split('/')[-1]
                                # Validate username format (3-30 chars, alphanumeric, dots, underscores)
                                if re.match(r'^[a-zA-Z0-9._]{3,30}$', username_candidate):
                                    if not quiet:
                                        print(
                                            f"✅ Extracted username from element href: {username_candidate}")
                                    self._last_extracted_username = username_candidate
                                    return username_candidate

                            # Try to get text directly from element
                            text = element.text.strip()
                            if text and re.match(r'^[a-zA-Z0-9._]{3,30}$', text):
                                if not quiet:
                                    print(
                                        f"✅ Extracted username from element text: {text}")
                                    self._last_extracted_username = text
                                    return text
                        except Exception as element_error:
                            if not quiet:
                                print(
                                    f"Error extracting from element: {element_error}")
                            continue
                except Exception as selector_error:
                    if not quiet:
                        print(f"Selector failed: {selector_error}")
                    continue

            # APPROACH 2: Story URL Parsing - Instagram URLs may contain username
            try:
                if 'instagram.com/stories/' in current_url:
                    # Format: https://instagram.com/stories/username/12345678
                    parts = current_url.split('/')
                    if len(parts) > 5:
                        username_idx = parts.index('stories') + 1
                        if username_idx < len(parts):
                            username = parts[username_idx]
                            if re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                                if not quiet:
                                    print(
                                        f"✅ Extracted username from URL: {username}")
                                self._last_extracted_username = username
                                return username
            except Exception as url_error:
                if not quiet:
                    print(f"URL parsing failed: {url_error}")

            # APPROACH 3: Page source regex extraction
            try:
                page_source = self.driver.page_source
                username_patterns = [
                    # Instagram patterns for usernames in the page source
                    r'"username":"([a-zA-Z0-9._]{3,30})"',
                    r'"user":{"username":"([a-zA-Z0-9._]{3,30})"',
                    r'@([a-zA-Z0-9._]{3,30})',
                    r"([a-zA-Z0-9._]{3,30})'s story",
                    r'Stories · ([a-zA-Z0-9._]{3,30})',
                    r'instagram.com/([a-zA-Z0-9._]{3,30})(?:/|")',
                ]

                extracted_usernames = []
                for pattern in username_patterns:
                    matches = re.findall(pattern, page_source)
                    if matches:
                        # Add all valid matches to our list
                        for match in matches:
                            if re.match(r'^[a-zA-Z0-9._]{3,30}$', match):
                                extracted_usernames.append(match)

                if extracted_usernames:
                    # Try to find the most common username in the matches
                    username_counter = Counter(extracted_usernames)
                    most_common = username_counter.most_common(1)[0][0]

                    if not quiet:
                        print(
                            f"✅ Extracted username using regex: {most_common}")
                    self._last_extracted_username = most_common
                    return most_common
            except Exception as regex_error:
                if not quiet:
                    print(f"Regex extraction failed: {regex_error}")

            # APPROACH 4: Page title extraction
            try:
                page_title = self.driver.title
                if "Instagram" in page_title:
                    # Format might be "Instagram • username's story"
                    if "•" in page_title:
                        parts = page_title.split("•")
                        if len(parts) > 1:
                            title_part = parts[1].strip()
                            if "'s" in title_part:
                                username_candidate = title_part.split("'s")[
                                    0].strip()
                                if username_candidate and re.match(r'^[a-zA-Z0-9._]{3,30}$', username_candidate):
                                    if not quiet:
                                        print(
                                            f"✅ Extracted username from page title: {username_candidate}")
                                    self._last_extracted_username = username_candidate
                                    return username_candidate
            except Exception as title_error:
                if not quiet:
                    print(f"Title extraction failed: {title_error}")

            # Use previously extracted username if available
            if last_extracted_username:
                if not quiet:
                    print(
                        f"⚠️ Using previously extracted username as fallback: {last_extracted_username}")
                return last_extracted_username

            if not quiet:
                print("❌ Could not extract username with any method")
            return None

        except Exception as e:
            if not quiet:
                print(f"❌ Error in username extraction: {e}")
            # Use previously extracted username if available
            if last_extracted_username := getattr(self, '_last_extracted_username', None):
                if not quiet:
                    print(
                        f"⚠️ Using previously extracted username after error: {last_extracted_username}")
                return last_extracted_username
            return None

    def simple_manual_confirmation(self, username, story_description, proposed_comment):
        """
        Simplified manual confirmation with pause monitoring.
        Just maintains basic pause state during user input.
        Returns: (final_comment, should_send, change_reason)
        """
        print("\n" + "=" * 80)
        print("🔍 MESSAGE CONFIRMATION REQUIRED")
        print("=" * 80)
        print(f"👤 Username: {username}")
        print(f"📖 Story Description: {story_description}")
        print(f"💬 Proposed Comment: '{proposed_comment}'")

        total_comments = analytics.global_metrics.get(
            "total_story_comments", 0)
        correction_rate = analytics.global_metrics.get(
            "correction_percentage", 0)
        if total_comments > 0:
            print(
                f"📊 Bot Stats: {total_comments} comments, {correction_rate:.1f}% correction rate")

        # Show available screenshots
        import os
        screenshot_files = [f for f in os.listdir(
            "screenshots") if f.endswith('.png')]
        recent_screenshots = sorted(screenshot_files, key=lambda x: os.path.getctime(
            f"screenshots/{x}"), reverse=True)[:3]

        if recent_screenshots:
            print("\n📸 Recent Screenshots (most recent first):")
            for i, screenshot in enumerate(recent_screenshots, 1):
                full_path = os.path.abspath(f"screenshots/{screenshot}")
                print(f"   {i}. {screenshot}")
                print(f"      Path: {full_path}")

        print("=" * 80)

        # The pause monitor is already running, so we don't need manual pausing
        print("🔄 Pause monitor is maintaining story pause state...")

        final_comment = proposed_comment
        should_send = True
        change_reason = None

        try:
            while True:
                print("\n📋 Options:")
                print("  1. Press ENTER to send the message as-is")
                print("  2. Type 'edit' or 'e' to modify the message")
                print("  3. Type 'skip' or 's' to skip this story")
                print("  4. Type 'quit' or 'q' to stop the bot")

                user_input = input("\n➤ Your choice: ").strip().lower()

                if user_input == "" or user_input == "1":
                    print("✅ Sending message as-is...")
                    return proposed_comment, True, None

                elif user_input in ["edit", "e", "2"]:
                    print(f"\n📝 Current message: '{proposed_comment}'")
                    new_message = input("➤ Enter new message: ").strip()

                    if new_message:
                        reason_input = input(
                            "➤ Why did you change the message? (optional): ").strip()
                        change_reason = reason_input if reason_input else "User preferred different message"

                        print(f"\n✅ Message updated to: '{new_message}'")
                        print(f"📝 Reason: {change_reason}")

                        confirm = input(
                            "\n➤ Send this new message? (y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '']:
                            print("✅ Sending updated message...")
                            return new_message, True, change_reason
                    else:
                            print("🔄 Let's try again...")
                            continue
                else:
                        print("❌ Empty message not allowed. Try again.")
                        continue

                elif user_input in ["skip", "s", "3"]:
                    reason_input = input(
                        "➤ Why are you skipping? (optional): ").strip()
                    change_reason = reason_input if reason_input else "User chose to skip"
                    print(f"⏭️ Skipping story for {username}")
                    return None, False, change_reason

                elif user_input in ["quit", "q", "4"]:
                    print("🛑 Stopping bot as requested")
                    return None, False, "User requested to quit"

                    else:
                    print(
                        "❌ Invalid option. Please choose 1, 2, 3, 4, or use the shortcuts.")
                    continue

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user (Ctrl+C)")
            return None, False, "User interrupted with Ctrl+C"
        except Exception as e:
            print(f"❌ Error getting user input: {e}")
            print("⚠️ Defaulting to sending original message...")
            return proposed_comment, True, None

    def capture_verified_screenshot(self, filepath, expected_username=None):
        """Enhanced screenshot capture with verification and feedback"""
        try:
            print(f"📸 Capturing verified screenshot: {filepath}")

            # Take screenshot
            success = self.driver.save_screenshot(filepath)
            if not success:
                print("❌ Screenshot capture failed")
                return False

            # Quick verification - check if screenshot has content
            try:
                from PIL import Image
                img = Image.open(filepath)
                width, height = img.size
                if width < 100 or height < 100:
                    print(f"⚠️ Screenshot seems too small: {width}x{height}")
                    return False

                print(f"✅ Screenshot captured successfully: {width}x{height}")
        except Exception as e:
                print(f"⚠️ Screenshot verification failed: {e}")
                # Still return True since screenshot was taken

            return True

        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            return False

    def analyze_current_story_state(self):
        """Analyze current story state and provide detailed feedback"""
        try:
            print_substep("📊 ANALYZING CURRENT STORY STATE")

            # Take a state analysis screenshot
            state_screenshot = f"screenshots/state_analysis_{int(time.time())}.png"
            os.makedirs("screenshots", exist_ok=True)

            if not self.capture_verified_screenshot(state_screenshot):
                print("❌ Could not capture state screenshot")
                return None

            # Basic state analysis
            state_info = {
                'screenshot_path': state_screenshot,
                'timestamp': time.time(),
                'url': self.driver.current_url,
                'title': self.driver.title
            }

            # Check for UI elements
            ui_elements = {}

            # Check for story viewer (including highlights)
            story_viewer_selectors = [
                "//div[@role='dialog']",  # Regular stories
                # Alternative story container
                "//section[contains(@class, 'x78zum5')]",
                # Another story container
                "//div[contains(@class, 'x1qjc9v5')]"
            ]

            story_viewer_found = False
            current_url = self.driver.current_url

            # Check URL patterns for story/highlight indication
            if 'stories/' in current_url or 'highlights/' in current_url:
                story_viewer_found = True
                print("✅ Story/highlight viewer detected via URL")
            else:
                # Check DOM elements
                for selector in story_viewer_selectors:
                    try:
                        story_dialog = self.driver.find_element(
                            By.XPATH, selector)
                        if story_dialog:
                            story_viewer_found = True
                            print(
                                f"✅ Story viewer detected with selector: {selector}")
                            break
                    except:
                        continue

            ui_elements['story_viewer'] = story_viewer_found
            if not story_viewer_found:
                print("❌ No story viewer found")

            # Check for progress bars
            try:
                progress_bars = self.driver.find_elements(
                    By.XPATH, "//div[@role='progressbar']")
                ui_elements['progress_bars'] = len(progress_bars)
                print(f"📊 Found {len(progress_bars)} progress bars")
            except:
                ui_elements['progress_bars'] = 0

            # Check for comment box using enhanced detection
            ui_elements['comment_box'] = self.has_comment_box()

            # Extract username
            current_username = self.extract_instagram_username(quiet=True)
            ui_elements['extracted_username'] = current_username
            if current_username:
                print(f"👤 Current username: {current_username}")
            else:
                print("❓ Could not extract username")

            state_info['ui_elements'] = ui_elements

            # Visual feedback
            print("📸 Current State Summary:")
            print(
                f"   Story Viewer: {'✅' if ui_elements['story_viewer'] else '❌'}")
            print(f"   Progress Bars: {ui_elements['progress_bars']}")
            print(
                f"   Comment Box: {'✅' if ui_elements['comment_box'] else '❌'}")
            print(f"   Username: {current_username or 'Unknown'}")
            print(f"   URL: {self.driver.current_url}")

            return state_info

        except Exception as e:
            print(f"❌ Error analyzing story state: {e}")
            return None

    def process_single_story(self, story_number, total_stories):
        """Enhanced story processing with visual feedback and state monitoring"""
        screenshot_path = None
        success = False

        try:
            print_step(f"PROCESSING STORY {story_number}/{total_stories}")

            # 0. Start pause monitoring
            print_substep("0. Starting pause monitoring...")
            if self.pause_monitor:
                self.pause_monitor.start_monitoring()

            # 1. ANALYZE CURRENT STATE FIRST
            print_substep("1. Analyzing current story state...")
            initial_state = self.analyze_current_story_state()

            if not initial_state:
                print("❌ Could not analyze initial state")
                return "NO_REPLY_BOX"

            # Check if we're actually in a story
            if not initial_state['ui_elements']['story_viewer']:
                print("❌ Not in story viewer - skipping")
                return "NO_REPLY_BOX"

                # 2. ROBUST PAUSE with feedback
            print_substep("2. Pausing story with verification...")
            pause_success = self.robust_pause_story()

            # 2.5. WAIT FOR STORY STABILITY
            print_substep("2.5. Waiting for story to stabilize...")
            stable_screenshot = self.wait_for_story_stability(
                timeout_seconds=3)

            if not stable_screenshot:
                print("⚠️ Story did not stabilize - taking immediate screenshot")
                post_pause_screenshot = f"screenshots/post_pause_{story_number}_{int(time.time())}.png"
                self.capture_verified_screenshot(post_pause_screenshot)
            else:
                post_pause_screenshot = stable_screenshot
                print(f"✅ Using stable screenshot: {post_pause_screenshot}")

            # 3. Check for comment capability
            can_comment = initial_state['ui_elements']['comment_box']
            if not can_comment:
                print(
                    "❌ No comment box available - this might be an ad or story without reply option")
                # Still continue - highlights often don't have comment boxes but we can analyze

            # 4. Get username with verification
            print_substep("3. Extracting and verifying username...")
            html_username = initial_state['ui_elements']['extracted_username']

            if not html_username:
                # Try again with more aggressive extraction
                html_username = self.extract_instagram_username()

            if not html_username:
                print("❌ Could not extract username after multiple attempts")
                return "NO_REPLY_BOX"

            print(f"👤 Processing story for username: {html_username}")

            # Check if already processed
            if html_username in self.processed_usernames:
                print(f"⚠️ Already processed {html_username} this session")
                return "NO_REPLY_BOX"

            # 5. ENHANCED SCREENSHOT AND ANALYSIS
            print_substep("4. Taking verified screenshot for analysis...")

            screenshot_path = f"screenshots/story_{story_number}_{html_username}_analysis.png"

            if not self.capture_verified_screenshot(screenshot_path, html_username):
                print("❌ Failed to capture analysis screenshot")
                return "NO_REPLY_BOX"

            # Analyze with Gemini
            print_substep("5. Analyzing content with Gemini AI...")
            analysis_result = self.analyze_story_with_gemini(
                screenshot_path, html_username)

            if not analysis_result:
                print("❌ Failed to analyze screenshot with Gemini")
                return "NO_REPLY_BOX"

            comment = analysis_result.get('suggested_message', 'Love it! 🔥')
            description = analysis_result.get(
                'content_description', 'Story content')

            print(f"🤖 AI Analysis Complete:")
            print(f"   📝 Description: {description}")
            print(f"   💬 Suggested Comment: {comment}")

            # Sanitize the comment
            sanitized_comment = sanitize_message(
                comment) if 'sanitize_message' in globals() else comment

            if not sanitized_comment or sanitized_comment.strip() == '' or sanitized_comment.strip() == "''" or sanitized_comment.strip() == '""' or sanitized_comment.lower() == 'null':
                sanitized_comment = "Love this! 👌"
                print(f"   🔄 Using fallback comment: '{sanitized_comment}'")

            # 6. Manual confirmation with enhanced feedback
            print_substep("6. Manual message confirmation...")

            print(f"📸 Screenshots available for review:")
            print(f"   Initial State: {initial_state['screenshot_path']}")
            print(f"   Post-Pause: {post_pause_screenshot}")
            print(f"   Analysis: {screenshot_path}")

            confirmed_message, should_send, change_reason = self.simple_manual_confirmation(
                html_username,
                description,
                sanitized_comment
            )

            if not should_send:
                if change_reason == "User requested to quit":
                    print("🛑 User requested to quit the bot")
                    return "USER_QUIT"
                else:
                    print(
                        f"⏭️ Skipping story for {html_username}: {change_reason}")
                    return "USER_SKIP"

            sanitized_comment = confirmed_message

            # 7. Send message with verification
            print_substep("7. Sending message...")

            # Analytics update
            analytics.update_story_interaction(
                html_username,
                description,
                sanitized_comment,
                change_reason
            )

            # Determine send method based on comment box availability
            if can_comment:
                send_success = self.send_story_reply(sanitized_comment)
            else:
                print("📱 No comment box - sending as DM instead...")
                send_success = self.send_direct_message(
                    html_username, sanitized_comment)

            if send_success:
                self.processed_usernames.add(html_username)
                self.save_processed_usernames()
                success = True
                print(f"✅ Successfully engaged with {html_username}")

                # Take success screenshot
                success_screenshot = f"screenshots/success_{html_username}_{int(time.time())}.png"
                self.capture_verified_screenshot(success_screenshot)
                print(f"📸 Success screenshot: {success_screenshot}")
            else:
                print(f"❌ Failed to send message to {html_username}")
                return "NO_REPLY_BOX"

            return success

        except Exception as e_outer:
            print(f"❌ Error processing story: {e_outer}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
            return "NO_REPLY_BOX"

        finally:
            if self.pause_monitor:
                self.pause_monitor.stop_monitoring()
            # Keep screenshots for debugging - don't auto-delete
            print(f"📁 Screenshots saved for review in screenshots/ directory")

    def detect_story_changes(self, before_screenshot, after_screenshot):
        """Compare two screenshots to detect if story has changed"""
        try:
            from PIL import Image
            import hashlib

            # Calculate simple hashes for comparison
            def image_hash(img_path):
                try:
                    with Image.open(img_path) as img:
                        # Resize to small size for quick comparison
                        img = img.resize((32, 32))
                        # Convert to grayscale and get hash
                        img = img.convert('L')
                        pixels = list(img.getdata())
                        return hashlib.md5(str(pixels).encode()).hexdigest()
                except:
                    return None

            hash1 = image_hash(before_screenshot)
            hash2 = image_hash(after_screenshot)

            if hash1 and hash2:
                if hash1 != hash2:
                    print("📸 Story change detected via image comparison")
                    return True
                else:
                    print("📸 No story change detected")
                    return False

            print("⚠️ Could not compare screenshots for changes")
            return None

        except Exception as e:
            print(f"❌ Error detecting story changes: {e}")
            return None

    def wait_for_story_stability(self, timeout_seconds=5):
        """Wait for story to stabilize before taking action"""
        try:
            print(f"⏱️ Waiting for story to stabilize ({timeout_seconds}s)...")

            stable_screenshots = []
            check_interval = 0.5
            checks = int(timeout_seconds / check_interval)

            for i in range(checks):
                # Take a stability check screenshot
                stability_screenshot = f"screenshots/stability_check_{i}_{int(time.time())}.png"
                if self.capture_verified_screenshot(stability_screenshot):
                    stable_screenshots.append(stability_screenshot)

                    # If we have at least 2 screenshots, compare them
                    if len(stable_screenshots) >= 2:
                        changed = self.detect_story_changes(
                            stable_screenshots[-2],
                            stable_screenshots[-1]
                        )

                        if changed is False:  # No change detected
                            print(
                                f"✅ Story stable after {(i+1) * check_interval}s")
                            # Clean up stability screenshots except the last one
                            for screenshot in stable_screenshots[:-1]:
                                try:
                                    os.remove(screenshot)
                                except:
                                    pass
                            # Return path to stable screenshot
                            return stable_screenshots[-1]
                        elif changed is True:
                            print(
                                f"🔄 Story still changing at {(i+1) * check_interval}s...")

                time.sleep(check_interval)

            print(f"⚠️ Story did not stabilize within {timeout_seconds}s")
            return stable_screenshots[-1] if stable_screenshots else None

        except Exception as e:
            print(f"❌ Error waiting for story stability: {e}")
            return None

    def run_targeting_campaign(self, min_coaching_score: int = 50, max_users_per_day: int = 20):
        """Run the main targeting campaign"""
        logger.info("Starting Potential Clients Story Targeting Campaign")
        logger.info(
            f"Targeting users with coaching score >= {min_coaching_score}")

        # Ensure screenshots directory exists
        os.makedirs("screenshots", exist_ok=True)

        try:
            # Setup browser
            if not self.setup_driver():
                logger.error("Failed to setup WebDriver")
                return False

            # Login to Instagram
            if not self.login_to_instagram():
                logger.error("Failed to login to Instagram")
                return False

            # Get target users from database
            target_users = self.get_target_users(min_coaching_score)

            if not target_users:
                logger.info("No target users found")
                return True

            # Limit to max users per day
            if len(target_users) > max_users_per_day:
                target_users = target_users[:max_users_per_day]
                logger.info(f"Limited to {max_users_per_day} users for today")

            logger.info(f"Processing {len(target_users)} target users")

            # Process each user
            successful_interactions = 0
            for i, user_info in enumerate(target_users, 1):
                logger.info(
                    f"Processing user {i}/{len(target_users)}: {user_info['ig_username']}")

                # Navigate to user profile
                if not self.navigate_to_user_profile(user_info['ig_username']):
                    self.analytics.update_user_interaction(
                        user_info['ig_username'], "Profile not accessible", "", False)
                    continue

                    # Try visual analysis and click on story/highlight
                story_click_success = self.click_user_story(
                    user_info['ig_username'])

                if not story_click_success:
                    logger.info(
                        f"No stories or highlights available for {user_info['ig_username']} - skipping")
                    self.analytics.update_user_interaction(
                        user_info['ig_username'], "No stories/highlights available", "", False)

                    # Mark as processed and move to next user (no DM attempts)
                    self.processed_users.add(user_info['ig_username'])
                    self.save_processed_users()
                    # Shorter delay since we're just skipping
                    self.random_delay(15, 30)
                    continue

                # Story clicked successfully - process with enhanced visual feedback system
                logger.info(
                    f"Story loaded for {user_info['ig_username']} - starting enhanced processing")
                story_processing_result = self.process_single_story(
                    i, len(target_users))

                if story_processing_result is True:
                    successful_interactions += 1
                    logger.info(
                        f"Successfully processed story for {user_info['ig_username']}")

                elif story_processing_result == "NO_REPLY_BOX":
                    logger.info(
                        f"Skipping story for {user_info['ig_username']} due to no reply box.")

                elif story_processing_result == "NEGATIVE_CONTENT":
                    logger.info(
                        f"Skipping story for {user_info['ig_username']} due to negative content.")

                elif story_processing_result == "USER_QUIT":
                    logger.info("User requested to quit. Ending campaign.")
                    break

                elif story_processing_result == "USER_SKIP":
                    logger.info(
                        f"User skipped story for {user_info['ig_username']}.")

                self.processed_users.add(user_info['ig_username'])
                self.save_processed_users()
                self.processed_usernames.add(
                    user_info['ig_username'])  # Also track in session
                self.save_processed_usernames()  # Save session usernames
                self.random_delay(30, 60)  # 30-60 seconds between users

                # Add longer delay every few users
                if i % 5 == 0:
                    logger.info("Taking extended break...")
                    # 2-3 minute break every 5 users
                    self.random_delay(120, 180)

            logger.info(
                f"Campaign completed. Successfully interacted with {successful_interactions}/{len(target_users)} users")
            return True

        except Exception as e:
            logger.error(f"Error in targeting campaign: {e}")
            return False
        finally:
            self.cleanup()

    def load_processed_usernames(self):
        """Load the set of processed usernames from a file if it exists."""
        filename = "processed_usernames.json"
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    data = json.load(file)
                    if 'usernames' in data:
                        self.processed_usernames = set(data['usernames'])
                        print(
                            f"✅ Loaded {len(self.processed_usernames)} previously processed usernames")
                        logger.info(
                            f"Loaded {len(self.processed_usernames)} previously processed usernames")
        except Exception as e:
            print(f"⚠️ Error loading processed usernames: {e}")
            logger.error(f"Error loading processed usernames: {e}")
            # If there's an error, start with an empty set
            self.processed_usernames = set()

    def save_processed_usernames(self):
        """Save the set of processed usernames to a file."""
        filename = "processed_usernames.json"

        # Check if we've exceeded the maximum number of tracked usernames
        if len(self.processed_usernames) > self.max_tracked_usernames:
            print(
                f"⚠️ Tracked usernames exceeded limit of {self.max_tracked_usernames}. Clearing list.")
            logger.warning(
                f"Tracked usernames exceeded limit of {self.max_tracked_usernames}. Clearing list.")
            self.processed_usernames = set()
            # Don't save an empty set
            return

        try:
            data = {'usernames': list(self.processed_usernames)}
            with open(filename, 'w') as file:
                json.dump(data, file)
            print(
                f"✅ Saved {len(self.processed_usernames)} processed usernames")
            logger.info(
                f"Saved {len(self.processed_usernames)} processed usernames to {filename}")
        except Exception as e:
            print(f"⚠️ Error saving processed usernames: {e}")
            logger.error(f"Error saving processed usernames: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver cleaned up")

        # Stop pause monitoring if active
        if hasattr(self, 'pause_monitor') and self.pause_monitor:
            self.pause_monitor.stop_monitoring()
            print("✔️ Pause monitoring stopped")

        # Clean up unique Chrome profile directory
        if hasattr(self, 'profile_dir') and os.path.exists(self.profile_dir):
            try:
                import shutil
                shutil.rmtree(self.profile_dir)
                print(f"✔️ Cleaned up Chrome profile: {self.profile_dir}")
            except Exception as profile_cleanup_error:
                print(
                    f"⚠️ Could not clean up profile directory: {profile_cleanup_error}")

        # Delete processed users file for today to ensure it resets daily
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"processed_users_{today}.json"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted daily processed users file: {file_path}")
            except Exception as e:
                logger.warning(
                    f"Could not delete daily processed users file {file_path}: {e}")


def main():
    """Main function"""
    print("🎯 Potential Clients Story Commentor")
    print("=" * 50)

    # Get configuration from user
    min_score = input("Enter minimum coaching score (default 70): ").strip()
    if not min_score:
        min_score = 70
    else:
        min_score = int(min_score)

    max_users = input("Enter max users per day (default 20): ").strip()
    if not max_users:
        max_users = 20
    else:
        max_users = int(max_users)

    print(f"\n🎯 Configuration:")
    print(f"   Minimum Coaching Score: {min_score}")
    print(f"   Max Users Per Day: {max_users}")
    print("\n🚀 Starting campaign...")

    # Create and run bot
    bot = PotentialClientBot()
    success = bot.run_targeting_campaign(
        min_coaching_score=min_score,
        max_users_per_day=max_users
    )

    if success:
        print("\n✅ Campaign completed successfully!")
        print("📊 Check story_targeting_analytics.json for detailed results")
    else:
        print("\n❌ Campaign failed. Check logs for details.")


if __name__ == "__main__":
    setup_logging()
    main()
