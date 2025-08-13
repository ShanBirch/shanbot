from typing import Dict, Any, List, Optional, Tuple, Union
import json
import requests
import logging
import hashlib
import hmac
import os
import random
import msvcrt
import google.generativeai as genai
import re
from datetime import datetime, timezone
import pytz
import time
from collections import defaultdict
import dateutil.parser as parser
import sqlite3
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
    SessionNotCreatedException,
    InvalidSessionIdException,
)
import threading  # Add threading
import uuid  # Add uuid

# Analytics Integration


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
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver import ActionChains
            ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.1)  # Brief pause after re-pausing
        except Exception as e:
            print(f"⚠️ Failed to re-pause story: {e}")


class ConversationAnalytics:
    def __init__(self):
        self.analytics_db = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite"
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
            print("CRITICAL: Analytics loading failed, but database previously existed. Skipping export to prevent data loss.")
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


class StoryMonitor:
    """
    Continuous story monitoring system that tracks story state, content, and changes in real-time.
    Provides robust story change detection and content validation.
    """

    def __init__(self, driver, gemini_model):
        self.driver = driver
        self.gemini_model = gemini_model
        self.current_story_state = None
        self.monitoring_active = False
        self.monitoring_thread = None
        self.state_lock = threading.Lock()
        self.story_change_detected = False
        self.last_analysis_time = 0
        # Check every 1 second (reduced from 500ms for much less aggressive monitoring)
        self.analysis_interval = 1.0

        # Story fingerprint components
        self.current_fingerprint = {
            'url': None,
            'title': None,
            'username': None,
            'dom_signature': None,
            'visual_hash': None,
            'progress_state': None,
            'timestamp': None
        }

        # Change detection sensitivity - Made MUCH more forgiving to prevent false positives
        self.fingerprint_tolerance = {
            'url_change': True,  # URL changes always indicate story change
            'username_change': True,  # Username changes always indicate story change
            # 30% similarity required (very forgiving)
            'dom_signature_threshold': 0.3,
            # 40% visual similarity required (very forgiving)
            'visual_hash_threshold': 0.4,
            'max_fingerprint_age': 60,      # Allow fingerprints up to 60 seconds old
            'story_stability_timeout': 1,   # Very quick stability check
            'consistency_check_timeout': 30  # Allow up to 30 seconds for consistency checks
        }

    def start_monitoring(self):
        """Start continuous story monitoring in background thread."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.story_change_detected = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("🔍 Story monitoring started")

    def stop_monitoring(self):
        """Stop story monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("🔍 Story monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that runs in background thread."""
        while self.monitoring_active:
            try:
                current_time = time.time()
                if current_time - self.last_analysis_time >= self.analysis_interval:
                    self._analyze_current_state()
                    self.last_analysis_time = current_time
                time.sleep(0.1)  # Small sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"⚠️ Monitoring loop error: {e}")
                time.sleep(0.5)  # Longer sleep on error

    def _analyze_current_state(self):
        """Analyze current story state and detect changes."""
        try:
            new_fingerprint = self._create_story_fingerprint()

            with self.state_lock:
                if self.current_fingerprint['url'] is None:
                    # First time setup
                    self.current_fingerprint = new_fingerprint
                    print(
                        f"📍 Initial story fingerprint captured for: {new_fingerprint.get('username', 'Unknown')}")
                else:
                    # Check for changes with multiple confirmations to prevent false positives
                    if self._has_story_changed(self.current_fingerprint, new_fingerprint):
                        # Wait and take THREE confirmation samples to ensure the change is real
                        confirmation_fingerprints = []

                        for confirmation_attempt in range(3):
                            time.sleep(0.3)  # Wait between samples
                            confirmation_fingerprint = self._create_story_fingerprint()
                            confirmation_fingerprints.append(
                                confirmation_fingerprint)

                        # Check if ALL confirmations show the same change
                        all_confirmations_match = True
                        for conf_fp in confirmation_fingerprints:
                            if not self._has_story_changed(self.current_fingerprint, conf_fp):
                                all_confirmations_match = False
                                break

                        # Only report change if all confirmations agree
                        if all_confirmations_match:
                            # Use the last confirmation fingerprint
                            final_confirmation = confirmation_fingerprints[-1]
                            print(
                                f"🔄 Story change confirmed after 3 checks: {self.current_fingerprint.get('username')} → {final_confirmation.get('username')}")

                            # IMMEDIATELY PAUSE when story change is detected
                            try:
                                print(
                                    "🛑 IMMEDIATE PAUSE due to story change detection...")
                                for immediate_pause in range(2):
                                    webdriver.ActionChains(self.driver).send_keys(
                                        Keys.SPACE).perform()
                                    time.sleep(0.1)
                            except Exception as pause_error:
                                print(
                                    f"⚠️ Failed to immediately pause: {pause_error}")

                            self.story_change_detected = True
                            self.current_fingerprint = final_confirmation
                        else:
                            print(
                                "📍 False change detection prevented by triple confirmation check")
        except Exception as e:
            print(f"⚠️ Error in state analysis: {e}")

    def _create_story_fingerprint(self):
        """Create a comprehensive fingerprint of the current story."""
        fingerprint = {
            'timestamp': time.time(),
            'url': None,
            'title': None,
            'username': None,
            'dom_signature': None,
            'visual_hash': None,
            'progress_state': None
        }

        try:
            # URL fingerprint
            fingerprint['url'] = self.driver.current_url

            # Title fingerprint
            fingerprint['title'] = self.driver.title

            # Username extraction
            fingerprint['username'] = self._extract_username_fast()

            # DOM signature (key elements that indicate story content)
            fingerprint['dom_signature'] = self._create_dom_signature()

            # Progress state
            fingerprint['progress_state'] = self._get_progress_indicators()

            # Visual hash (lightweight visual fingerprint)
            fingerprint['visual_hash'] = self._create_visual_hash()

        except Exception as e:
            print(f"⚠️ Error creating fingerprint: {e}")

        return fingerprint

    def _extract_username_fast(self):
        """Fast username extraction for monitoring - focused on active story only."""
        try:
            # URL-based extraction first (most reliable for active story)
            current_url = self.driver.current_url
            if 'instagram.com/stories/' in current_url:
                parts = current_url.split('/')
                if len(parts) > 5:
                    username_idx = parts.index('stories') + 1
                    if username_idx < len(parts):
                        username = parts[username_idx]
                        if re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                            return username

            # More specific selectors focused on the active story area, not the story tray
            selectors = [
                # Focus on the main story dialog area only
                "//div[@role='dialog']//span[contains(@class, 'x1lliihq') and contains(@class, 'x193iq5w')]",
                "//div[@role='dialog']//header//a[starts-with(@href, '/')]",
                # Target the story header specifically (exclude tray elements)
                "//section[contains(@class, 'x78zum5')]//div[contains(@class, 'x1qjc9v5')]//a[starts-with(@href, '/')]",
                # Look for username in the story header area
                "//div[contains(@class, 'x1i10hfl') and not(ancestor::div[contains(@class, '_aarf')])]//a[starts-with(@href, '/')]"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        # Try href first
                        href = element.get_attribute('href')
                        if href and '/' in href:
                            username = href.strip('/').split('/')[-1]
                            if re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                                # Additional validation: make sure this username matches the URL
                                if 'instagram.com/stories/' in current_url and username in current_url:
                                    return username

                        # Try text content
                        text = element.text.strip()
                        if text and re.match(r'^[a-zA-Z0-9._]{3,30}$', text):
                            # Additional validation: make sure this username matches the URL
                            if 'instagram.com/stories/' in current_url and text in current_url:
                                return text
                except:
                    continue

        except:
            pass

        return None

    def _create_dom_signature(self):
        """Create a signature based on key DOM elements."""
        try:
            signature_elements = []

            # Key selectors that indicate story structure
            key_selectors = [
                "//div[@role='dialog']",
                "//canvas[contains(@class, 'x1upo8f9')]",
                "//div[contains(@class, '_aarf')]",
                "//textarea[@placeholder='Reply...']",
                "//div[@role='progressbar']"
            ]

            for selector in key_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    signature_elements.append(len(elements))
                except:
                    signature_elements.append(0)

            # Create a simple hash of the signature
            signature_str = '-'.join(map(str, signature_elements))
            return hash(signature_str) % 1000000  # Simple 6-digit hash
        except:
            return None

    def _get_progress_indicators(self):
        """Get story progress indicators."""
        try:
            progress_info = {}

            # Progress bars
            progress_selectors = [
                "//div[contains(@class, 'x1i10hfl')]//div[contains(@style, 'width')]",
                "//div[@role='progressbar']"
            ]

            for selector in progress_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        progress_info['progress_elements'] = len(elements)
                        # Get width of first element if available
                        style = elements[0].get_attribute('style')
                        if 'width' in style:
                            import re
                            width_match = re.search(
                                r'width:\s*(\d+(?:\.\d+)?)%', style)
                            if width_match:
                                progress_info['width_percent'] = float(
                                    width_match.group(1))
                        break
                except:
                    continue

            return progress_info
        except:
            return {}

    def _create_visual_hash(self):
        """Create a lightweight visual hash of the current story."""
        try:
            # Take a small screenshot and create a hash
            # We'll use a simple approach - get page source hash as a proxy
            # First 5000 chars
            page_source_sample = self.driver.page_source[:5000]
            return hash(page_source_sample) % 1000000  # Simple 6-digit hash
        except:
            return None

    def _has_story_changed(self, old_fingerprint, new_fingerprint):
        """Determine if story has changed based on fingerprint comparison."""
        try:
            # URL change (most reliable)
            old_url = old_fingerprint['url']
            new_url = new_fingerprint['url']
            if old_url != new_url:
                # Extract story IDs from URLs to check if it's actually a different story
                old_story_id = None
                new_story_id = None

                if old_url and 'instagram.com/stories/' in old_url:
                    old_parts = old_url.split('/')
                    if len(old_parts) > 6:
                        old_story_id = old_parts[-1]

                if new_url and 'instagram.com/stories/' in new_url:
                    new_parts = new_url.split('/')
                    if len(new_parts) > 6:
                        new_story_id = new_parts[-1]

                # Only consider it a change if the story ID actually changed
                if old_story_id and new_story_id and old_story_id != new_story_id:
                    return True

            # Username change (only if significantly different)
            old_username = old_fingerprint['username']
            new_username = new_fingerprint['username']
            if (old_username and new_username and old_username != new_username):
                # Only consider it a change if usernames are completely different
                # (not just minor variations due to extraction differences)
                if (old_username.lower() not in new_username.lower() and
                        new_username.lower() not in old_username.lower()):
                    return True

            # DOM signature change (structural changes) - be more tolerant
            old_dom = old_fingerprint['dom_signature']
            new_dom = new_fingerprint['dom_signature']
            if (old_dom and new_dom and old_dom != new_dom):
                # Only flag as change if DOM signature is significantly different
                # Small variations are normal and don't indicate story changes
                dom_diff = abs(old_dom - new_dom) if isinstance(old_dom,
                                                                (int, float)) and isinstance(new_dom, (int, float)) else 0
                if dom_diff > 100000:  # Only major structural changes
                    return True

            # Visual hash change (content changes) - be more tolerant
            old_visual = old_fingerprint['visual_hash']
            new_visual = new_fingerprint['visual_hash']
            if (old_visual and new_visual and old_visual != new_visual):
                # Only flag as change if visual hash is significantly different
                visual_diff = abs(old_visual - new_visual) if isinstance(
                    old_visual, (int, float)) and isinstance(new_visual, (int, float)) else 0
                if visual_diff > 500000:  # Only major visual changes
                    return True

            # Progress state significant change - be more tolerant
            old_progress = old_fingerprint.get('progress_state', {})
            new_progress = new_fingerprint.get('progress_state', {})

            # Only check progress elements if they changed significantly
            old_elements = old_progress.get('progress_elements', 0)
            new_elements = new_progress.get('progress_elements', 0)
            if abs(old_elements - new_elements) > 1:  # More than 1 element difference
                return True

            # Check for significant progress bar movement - be more tolerant
            old_width = old_progress.get('width_percent', 0)
            new_width = new_progress.get('width_percent', 0)
            if abs(old_width - new_width) > 40:  # More than 40% progress change (was 20%)
                return True

            return False
        except Exception as e:
            print(f"⚠️ Error comparing fingerprints: {e}")
            return False

    def has_story_changed_recently(self):
        """Check if story has changed recently and reset flag."""
        with self.state_lock:
            if self.story_change_detected:
                self.story_change_detected = False
                return True
            return False

    def get_current_story_info(self):
        """Get current story information."""
        with self.state_lock:
            return self.current_fingerprint.copy()

    def validate_story_consistency(self, expected_username=None, max_age_seconds=None):
        """Validate that we're still looking at the expected story."""
        try:
            # Use more forgiving default timeout
            if max_age_seconds is None:
                max_age_seconds = self.fingerprint_tolerance['consistency_check_timeout']

            with self.state_lock:
                current_info = self.current_fingerprint

                # Check age - more forgiving
                if current_info['timestamp']:
                    age = time.time() - current_info['timestamp']
                    if age > max_age_seconds:
                        print(
                            f"⚠️ Story info is {age:.1f}s old (max: {max_age_seconds}s) - refreshing fingerprint")
                        # Instead of failing, try to refresh the fingerprint
                        try:
                            new_fingerprint = self._create_story_fingerprint()
                            self.current_fingerprint = new_fingerprint
                            print("✔️ Fingerprint refreshed successfully")
                            return True
                        except Exception as refresh_error:
                            print(
                                f"❌ Could not refresh fingerprint: {refresh_error}")
                            return False

                # Check username if provided - more forgiving
                if expected_username and current_info['username']:
                    if current_info['username'] != expected_username:
                        print(
                            f"⚠️ Username mismatch: expected {expected_username}, got {current_info['username']}")
                        # Don't fail immediately - try to refresh and check again
                        try:
                            new_fingerprint = self._create_story_fingerprint()
                            if new_fingerprint['username'] == expected_username:
                                self.current_fingerprint = new_fingerprint
                                print("✔️ Username mismatch resolved after refresh")
                                return True
                            else:
                                print(
                                    f"❌ Username still mismatched after refresh: {new_fingerprint['username']}")
                                return False
                        except Exception as refresh_error:
                            print(
                                f"⚠️ Could not refresh for username check: {refresh_error}")
                            # If we can't refresh, be more lenient - only fail if names are completely different
                            if expected_username.lower() not in current_info['username'].lower() and current_info['username'].lower() not in expected_username.lower():
                                return False

                return True
        except Exception as e:
            print(f"⚠️ Error validating story consistency: {e}")
            # More forgiving - don't fail on validation errors
            return True

    def wait_for_story_stability(self, timeout_seconds=None):
        """Wait for story to become stable (no changes for a period)."""
        if timeout_seconds is None:
            timeout_seconds = self.fingerprint_tolerance['story_stability_timeout']

        stable_period = 0.8  # Story must be stable for 0.8 seconds (reduced)
        start_time = time.time()
        last_change_time = start_time

        while time.time() - start_time < timeout_seconds:
            if self.has_story_changed_recently():
                last_change_time = time.time()

            # Check if we've been stable long enough
            if time.time() - last_change_time >= stable_period:
                print("✔️ Story is stable")
                return True

            time.sleep(0.1)

        print(
            f"⚠️ Story did not stabilize within {timeout_seconds}s - continuing anyway")
        return False  # Changed to still return False but be less strict in calling code

    def capture_verified_screenshot(self, filepath, expected_username=None):
        """Capture screenshot with verification that we're looking at the right story."""
        max_attempts = 2  # Reduced attempts to speed up processing

        for attempt in range(max_attempts):
            try:
                # More lenient consistency check
                if not self.validate_story_consistency(expected_username, max_age_seconds=20):
                    print(
                        f"⚠️ Story consistency check failed on attempt {attempt + 1}")
                    if attempt < max_attempts - 1:
                        time.sleep(0.3)  # Shorter wait
                        continue
                    else:
                        # More forgiving - try to take screenshot anyway
                        print(
                            "⚠️ Taking screenshot despite consistency check failure")

                # Take screenshot
                success = self.driver.save_screenshot(filepath)
                if success:
                    print(f"✔️ Screenshot captured: {filepath}")
                    return True
                else:
                    print(f"❌ Screenshot failed on attempt {attempt + 1}")

            except Exception as e:
                print(f"❌ Screenshot error on attempt {attempt + 1}: {e}")

            if attempt < max_attempts - 1:
                time.sleep(0.2)  # Shorter wait between attempts

        # Final fallback - try basic screenshot without verification
        try:
            print("⚠️ Attempting fallback screenshot without verification")
            success = self.driver.save_screenshot(filepath)
            if success:
                print(f"✔️ Fallback screenshot captured: {filepath}")
                return True
        except Exception as fallback_error:
            print(f"❌ Fallback screenshot failed: {fallback_error}")

        return False


# Initialize analytics
analytics = ConversationAnalytics()


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


def encode_image(image_path):
    """Encodes an image file to Base64 format."""
    print_substep(f"Encoding image: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None


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


def manual_message_confirmation(username, story_description, proposed_comment):
    """
    Allow user to manually confirm, edit, or reject a message before sending.
    Returns: (final_comment, should_send, change_reason)
    """
    print("\n" + "=" * 80)
    print("🔍 MESSAGE CONFIRMATION REQUIRED")
    print("=" * 80)
    print(f"👤 Username: {username}")
    print(f"📖 Story Description: {story_description}")
    print(f"💬 Proposed Comment: '{proposed_comment}'")

    # Show bot performance stats
    total_comments = analytics.global_metrics.get("total_story_comments", 0)
    correction_rate = analytics.global_metrics.get("correction_percentage", 0)
    if total_comments > 0:
        print(
            f"📊 Bot Stats: {total_comments} comments, {correction_rate:.1f}% correction rate")

    print("=" * 80)

    while True:
        print("\n📋 Options:")
        print("  1. Press ENTER to send the message as-is")
        print("  2. Type 'edit' or 'e' to modify the message")
        print("  3. Type 'skip' or 's' to skip this story")
        print("  4. Type 'quit' or 'q' to stop the bot")

        try:
            user_input = input("\n➤ Your choice: ").strip().lower()

            if user_input == "" or user_input == "1":
                # Send as-is
                print("✅ Sending message as-is...")
                return proposed_comment, True, None

            elif user_input in ["edit", "e", "2"]:
                # Edit the message
                print(f"\n📝 Current message: '{proposed_comment}'")
                new_message = input("➤ Enter new message: ").strip()

                if new_message:
                    # Ask for reason
                    reason = input(
                        "➤ Why did you change the message? (optional): ").strip()
                    if not reason:
                        reason = "User preferred different message"

                    print(f"\n✅ Message updated to: '{new_message}'")
                    print(f"📝 Reason: {reason}")

                    # Confirm the new message
                    confirm = input(
                        "\n➤ Send this new message? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '']:
                        print("✅ Sending updated message...")
                        return new_message, True, reason
                    else:
                        print("🔄 Let's try again...")
                        continue
                else:
                    print("❌ Empty message not allowed. Try again.")
                    continue

            elif user_input in ["skip", "s", "3"]:
                # Skip this story
                reason = input("➤ Why are you skipping? (optional): ").strip()
                if not reason:
                    reason = "User chose to skip"
                print(f"⏭️ Skipping story for {username}")
                return None, False, reason

            elif user_input in ["quit", "q", "4"]:
                # Quit the bot
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


class InstagramBot:
    def __init__(self):
        """Initialize the Instagram bot with configuration."""
        print_step("INITIALIZING BOT CONFIGURATION")

        # Setup logging
        logging.basicConfig(
            filename="instagram_bot_debug.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(message)s",
        )

        # Configuration (replace with your credentials)
        self.username = "cocos_connected"
        self.password = "Shannonb3"
        self.gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"

        # Using the same ChromeDriver path that's working in other scripts
        self.chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

        # Initialize Gemini client
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-lite')
        logging.info("Gemini API configured.")

        # Set to track usernames that have already received DMs in this session
        # ALWAYS start with an empty set to avoid thinking we've commented when we haven't
        self.processed_usernames = set()
        print_step("STARTING WITH FRESH PROCESSED USERNAMES LIST")
        logging.info("Starting fresh with empty processed usernames list")

        # Maximum number of usernames to track before resetting
        self.max_tracked_usernames = 1000

        # Initialize WebDriver
        self.setup_driver()

        # Initialize pause monitoring system
        self.pause_monitor = PauseMonitor(self.driver)
        print("✔️ Pause monitoring system initialized")

        # DISABLED: Initialize StoryMonitor (causing pause/play conflicts)
        # self.story_monitor = StoryMonitor(self.driver, self.model)
        # print("✔️ Story monitoring system initialized")
        print(
            "✔️ Story processing system initialized (old monitoring disabled for stability)")

    def setup_driver(self):
        """Setup and configure the Chrome WebDriver with anti-detection measures."""
        try:
            print_substep("Setting up Chrome WebDriver...")
            service = Service(executable_path=self.chromedriver_path)
            chrome_options = Options()

            # Use unique Chrome profile to prevent conflicts
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            profile_dir = rf"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome_profile_{unique_id}"
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

            print("ChromeDriver initialized successfully")
            time.sleep(random.uniform(1, 2))

            # Reinitialize pause monitor with new driver if it exists
            if hasattr(self, 'pause_monitor'):
                self.pause_monitor = PauseMonitor(self.driver)
                print("✔️ Pause monitor reinitialized with new driver")

        except Exception as e:
            print(f"❌ Error initializing ChromeDriver: {e}")
            raise

    def get_first_non_live_story(self, max_retries=3):
        """Find the first non-live story in the tray with retry mechanism."""
        print_step("SCANNING FOR NON-LIVE STORY")

        for retry in range(max_retries):
            try:
                # If this is a retry, refresh the page
                if retry > 0:
                    print(
                        f"Retry attempt {retry + 1}/{max_retries} for finding stories...")
                    self.driver.refresh()
                    random_sleep(4, 6)

                # Multiple selectors for story elements - Prioritize more specific ones
                story_selectors = [
                    # More specific selector based on user feedback (clickable element containing the canvas)
                    "//div[@role='button' and .//canvas[contains(@class, 'x1upo8f9') and contains(@class, 'xpdipgo') and contains(@class, 'x87ps6o')]]",
                    # Your original good selectors, slightly reordered or kept as fallbacks
                    "//div[contains(@class, '_aarf')]/div/div/div/div/div/div/div/div/div",
                    "//div[@role='button'][tabindex='0']//canvas",
                    "//div[@role='button']/div/span//img[contains(@class, 'x') and @draggable='false']/..",
                    "//div[contains(@role, 'button')]//img[contains(@draggable, 'false')]/..",
                    "//div[contains(@class, 'x6s0dn4')]//div[@role='button']",
                    "//div[contains(@role, 'presentation')]//canvas/..",
                    # Direct canvas match as a last resort if it's clickable itself
                    "//canvas[contains(@class, 'x1upo8f9') and contains(@class, 'xpdipgo') and contains(@class, 'x87ps6o')]"
                ]

                for selector_idx, selector in enumerate(story_selectors):
                    try:
                        print(f"Trying story selector #{selector_idx + 1}...")
                        story_elements = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, selector))
                        )

                        if len(story_elements) > 0:
                            print(
                                f"Found {len(story_elements)} story elements with selector #{selector_idx + 1}")

                            # Check each story
                            for idx, story in enumerate(story_elements, 1):
                                print(
                                    f"\nChecking story {idx}/{len(story_elements)}")

                                try:
                                    # Updated LIVE indicator selector
                                    live_indicators = story.find_elements(
                                        By.XPATH,
                                        ".//span[text()='LIVE' or contains(@class, 'LiveIndicator')]"
                                    )

                                    if not live_indicators:
                                        print("✅ Found non-live story!")
                                        return story
                                    else:
                                        print("⏭️ Skipping live story...")
                                except Exception as e:
                                    print(f"Error checking story {idx}: {e}")
                                    continue

                            # If we checked all stories but none were suitable, try the next selector
                            continue

                    except Exception as e:
                        print(f"Selector #{selector_idx + 1} failed: {e}")
                        continue

                # If we've tried all selectors and still haven't found a story
                print("❌ No stories found with standard selectors")

                # Direct approach - try clicking the first story element regardless of type
                try:
                    print("Attempting direct approach to find any story...")
                    first_story = None

                    # Try these direct selectors
                    direct_selectors = [
                        "//div[contains(@class, '_aarf')]/div/div/div/div/div[1]",
                        "//section[contains(@class, 'x78zum5')]//div[@role='button'][1]",
                        "//div[contains(@class, 'x1lliihq')]/div[1]",
                        "//div[contains(@class, 'x6s0dn4')]/div[1]//div[@role='button']"
                    ]

                    for direct_selector in direct_selectors:
                        try:
                            first_story = self.driver.find_element(
                                By.XPATH, direct_selector)
                            if first_story:
                                print("✅ Found story with direct selector")
                                return first_story
                        except:
                            continue

                    if not first_story and retry < max_retries - 1:
                        print("No stories found. Retrying...")
                        random_sleep(2, 4)
                        continue

                    return None

                except Exception as e:
                    print(f"Direct approach failed: {e}")
                    if retry < max_retries - 1:
                        continue
                    else:
                        return None

            except Exception as e:
                print(f"Error finding stories: {e}")
                if retry < max_retries - 1:
                    print(
                        f"Retrying story search (attempt {retry + 2}/{max_retries})...")
                    random_sleep(3, 5)
                else:
                    return None

        return None

    def verify_stories_remaining(self):
        """Verify if there are more stories to process."""
        try:
            # Updated selector for story container
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "section._aa64")
                )
            )
            return True
        except:
            try:
                # Alternative selector
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[role='dialog']")
                    )
                )
                return True
            except:
                return False

    def analyze_image_with_gpt(self, image_path, known_username=None):
        """Analyzes an image using Gemini to extract username, describe the content, and generate a response

        Args:
            image_path: Path to the screenshot image
            known_username: Username if already extracted from HTML (optional)
        """
        print_step("ANALYZING IMAGE WITH GEMINI")
        try:
            # Prepare the image for Gemini
            print_substep("Preparing image for Gemini...")

            # Load the image file for Gemini
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Create a Gemini image part - fixing the format
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }

            if not image_data:
                return None

            print_substep("Sending request to Gemini...")

            # Get adaptive prompt additions based on user corrections
            adaptive_additions = analytics.get_adaptive_prompt_additions()

            # Adjust the prompt based on whether we already have the username
            if known_username:
                system_prompt = f"""You are analyzing an Instagram story screenshot posted by {known_username}. I need four pieces of information:

                1. DESCRIPTION: Briefly describe what is happening in the MAIN story in the image in 2-3 sentences. Be specific about visible content. NOTE: The screenshot may include other stories in the background or UI elements - focus ONLY on the main central story being viewed.
                
                2. IS_NEGATIVE: Based on the visual content and any text, is the primary subject of this story related to war, violence, tragedy, or other significantly negative themes? Respond True or False.
                
                3. IS_REEL: Does the visual content appear to be a reshared video, a "Reel" from another creator, or a screen recording of a video, rather than original content directly from this user's camera? Respond True or False.

                4. COMMENT: Create a friendly, casual comment in Shannon's style (Male Australian Personal Trainer from the Gold Coast - modern, cool, energetic vibe) to respond to this story:
                   
                   **CRITICAL: ANALYZE THE ACTUAL CONTENT FIRST**
                   - Look carefully at what's actually happening in the image
                   - Consider the setting, activity, objects, and context
                   - Your comment must be directly relevant to what you see
                   
                   **COMMENT RULES:**
                   - If IS_REEL is True:
                     * Use a single laughing emoji (😂) OR
                     * If there's clear text within the reel, create a 1-4 word REACTION to that text, NOT a repetition
                     * REACTION examples for text: "Haha love it!", "So relatable!", "Facts!", "Too funny!", "This!" 
                     * NEVER just repeat the text from the reel - always react TO it
                     * Do NOT use generic phrases like "Looking good!" for reels
                   
                   - If IS_REEL is False (original content):
                     * Keep it 3-10 words maximum
                     * Be specific to what you actually see in the image
                     * Examples of GOOD contextual comments:
                       - For gym/workout: "Get it!", "Beast mode!", "Crushing it!"
                       - For food: "Looks amazing!", "Yum!", "That looks good!"
                       - For pets: "Cutie!", "Good boy!", "Adorable!"
                       - For travel/location: "Beautiful spot!", "Nice views!", "Love this place!"
                       - For shopping/retail: "Nice finds!", "Good choice!", "Shopping spree!"
                       - For hobbies/activities: "Cool setup!", "Nice collection!", "Looking good!"
                     
                   **AVOID THESE GENERIC/IRRELEVANT PHRASES:**
                   - "Mad views!" (unless it's actually about a scenic view)
                   - "Where's this at?" (unless the location is the main focus)
                   - Generic fitness comments on non-fitness content
                   - Comments that don't match the actual scene
                   
                   **ALWAYS:**
                   - Match the energy of the content
                   - Be authentic to what's shown
                   - Keep it short and genuine
                   - Use 0-2 emojis maximum
                   - NO asterisks or special formatting
                   - NEVER leave the comment empty - always provide something
                   - FOR THE TRUCK/CAR EXAMPLE: Use "Nice ride!" or "Cool truck!" (NOT "mad views where's this")
                   - If completely unsure about content, use "Love this!" as a safe fallback

                   **QUESTION STRATEGY (Use questions frequently for engagement):**
                   - About 60-70% of your comments should include a short question
                   - Keep questions to 2-5 words maximum
                   - Make questions relevant to what you actually see
                   - Examples of GOOD questions by content type:
                     * Workout/gym: "New PR?" "Leg day?" "Morning session?"
                     * Food: "Homemade?" "Breakfast?" "Recipe?"
                     * Pets: "Good boy?" "New trick?" "Sleepy?"
                     * Travel: "Holiday?" "Business trip?" "First time?"
                     * Cars: "Your ride?" "New purchase?" "Weekend drive?"
                     * Shopping: "New haul?" "Sale shopping?" "Birthday gift?"
                     * Hobbies: "New gear?" "Latest project?" "How long?"
                     * Friends/social: "Fun night?" "Reunion?" "Birthday?"
                   - Avoid overused questions like "How's it going?" or "What's up?"
                   - Questions should show genuine interest in the specific activity shown

                Respond in this EXACT format:
                DESCRIPTION: [brief description of main story content]
                IS_NEGATIVE: [True or False]
                IS_REEL: [True or False]
                COMMENT: [short friendly comment, preferably with a relevant question]
                {adaptive_additions}"""
                analysis_instruction = f"Analyze this Instagram story screenshot from {known_username} according to my instructions above, providing DESCRIPTION, IS_NEGATIVE, IS_REEL, and COMMENT sections."
            else:
                # Even if we don't have a known username, we'll get it from HTML later
                system_prompt = """You are analyzing an Instagram story screenshot. I need four pieces of information:

                1. DESCRIPTION: Briefly describe what is happening in the MAIN story in the image in 2-3 sentences. Be specific about visible content. NOTE: The screenshot may include other stories in the background or UI elements - focus ONLY on the main central story being viewed.

                2. IS_NEGATIVE: Based on the visual content and any text, is the primary subject of this story related to war, violence, tragedy, or other significantly negative themes? Respond True or False.
                
                3. IS_REEL: Does the visual content appear to be a reshared video, a "Reel" from another creator, or a screen recording of a video, rather than original content directly from this user's camera? Respond True or False.

                4. COMMENT: Create a friendly, casual comment in Shannon's style (Male Australian Personal Trainer from the Gold Coast - modern, cool, energetic vibe) to respond to this story:
                   
                   **CRITICAL: ANALYZE THE ACTUAL CONTENT FIRST**
                   - Look carefully at what's actually happening in the image
                   - Consider the setting, activity, objects, and context
                   - Your comment must be directly relevant to what you see
                   
                   **COMMENT RULES:**
                   - If IS_REEL is True:
                     * Use a single laughing emoji (😂) OR
                     * If there's clear text within the reel, create a 1-4 word REACTION to that text, NOT a repetition
                     * REACTION examples for text: "Haha love it!", "So relatable!", "Facts!", "Too funny!", "This!" 
                     * NEVER just repeat the text from the reel - always react TO it
                     * Do NOT use generic phrases like "Looking good!" for reels
                   
                   - If IS_REEL is False (original content):
                     * Keep it 3-10 words maximum
                     * Be specific to what you actually see in the image
                     * Examples of GOOD contextual comments:
                       - For gym/workout: "Get it!", "Beast mode!", "Crushing it!"
                       - For food: "Looks amazing!", "Yum!", "That looks good!"
                       - For pets: "Cutie!", "Good boy!", "Adorable!"
                       - For travel/location: "Beautiful spot!", "Nice views!", "Love this place!"
                       - For shopping/retail: "Nice finds!", "Good choice!", "Shopping spree!"
                       - For hobbies/activities: "Cool setup!", "Nice collection!", "Looking good!"
                     
                   **AVOID THESE GENERIC/IRRELEVANT PHRASES:**
                   - "Mad views!" (unless it's actually about a scenic view)
                   - "Where's this at?" (unless the location is the main focus)
                   - Generic fitness comments on non-fitness content
                   - Comments that don't match the actual scene
                   
                   **ALWAYS:**
                   - Match the energy of the content
                   - Be authentic to what's shown
                   - Keep it short and genuine
                   - Use 0-2 emojis maximum
                   - NO asterisks or special formatting
                   - NEVER leave the comment empty - always provide something
                   - FOR THE TRUCK/CAR EXAMPLE: Use "Nice ride!" or "Cool truck!" (NOT "mad views where's this")
                   - If completely unsure about content, use "Love this!" as a safe fallback

                   **QUESTION STRATEGY (Use questions frequently for engagement):**
                   - About 60-70% of your comments should include a short question
                   - Keep questions to 2-5 words maximum
                   - Make questions relevant to what you actually see
                   - Examples of GOOD questions by content type:
                     * Workout/gym: "New PR?" "Leg day?" "Morning session?"
                     * Food: "Homemade?" "Breakfast?" "Recipe?"
                     * Pets: "Good boy?" "New trick?" "Sleepy?"
                     * Travel: "Holiday?" "Business trip?" "First time?"
                     * Cars: "Your ride?" "New purchase?" "Weekend drive?"
                     * Shopping: "New haul?" "Sale shopping?" "Birthday gift?"
                     * Hobbies: "New gear?" "Latest project?" "How long?"
                     * Friends/social: "Fun night?" "Reunion?" "Birthday?"
                   - Avoid overused questions like "How's it going?" or "What's up?"
                   - Questions should show genuine interest in the specific activity shown

                Respond in this EXACT format:
                DESCRIPTION: [brief description of main story content]
                IS_NEGATIVE: [True or False]
                IS_REEL: [True or False]
                COMMENT: [short friendly comment, preferably with a relevant question]
                {adaptive_additions}"""
                analysis_instruction = "Analyze this Instagram story screenshot according to my instructions above, providing DESCRIPTION, IS_NEGATIVE, IS_REEL, and COMMENT sections."

            # Combine prompt and image for Gemini - fixing the format
            try:
                # Add retry logic for Gemini API
                max_api_retries = 3
                api_retry_count = 0
                api_success = False

                while api_retry_count < max_api_retries and not api_success:
                    try:
                        print(
                            f"Gemini API attempt {api_retry_count + 1}/{max_api_retries}...")

                        # Increase timeout for Gemini API call
                        response = self.model.generate_content(
                            contents=[
                                {"text": system_prompt},
                                {"text": analysis_instruction},
                                {"inline_data": image_part}
                            ],
                            generation_config=genai.GenerationConfig(
                                max_output_tokens=500,
                                temperature=0.6
                            )
                        )

                        # Check if response has valid content
                        if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                            # Valid response with content
                            analysis = response.text.strip()
                            print("\n--- Gemini Analysis ---")
                            print(analysis)
                            api_success = True
                        else:
                            # Empty response, retry if possible
                            print(
                                f"⚠️ Gemini returned empty response on attempt {api_retry_count + 1}")
                            api_retry_count += 1
                            if api_retry_count < max_api_retries:
                                print(
                                    f"Waiting before retry {api_retry_count + 1}...")
                                random_sleep(3, 5)  # Wait between retries
                            else:
                                print(
                                    "⚠️ All Gemini API retries failed, using fallback values")
                                return {
                                    "username": known_username or "Unknown",
                                    "description": "Image content unavailable",
                                    "comment": "Love it!",
                                    "is_negative": False,  # Default
                                    "is_reel": False      # Default
                                }
                    except Exception as retry_error:
                        print(
                            f"⚠️ Gemini API error on attempt {api_retry_count + 1}: {retry_error}")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            print(
                                f"Waiting before retry {api_retry_count + 1}...")
                            random_sleep(3, 5)  # Wait between retries
                        else:
                            print(
                                "⚠️ All Gemini API retries failed, using fallback values")
                            return {
                                "username": known_username or "Unknown",
                                "description": "Error analyzing image",
                                "comment": "Looking good!",
                                "is_negative": False,  # Default
                                "is_reel": False      # Default
                            }
            except Exception as api_error:
                print(f"⚠️ Gemini API error: {api_error}")
                return {
                    "username": known_username or "Unknown",
                    "description": "Error analyzing image",
                    "comment": "Looking good!",
                    "is_negative": False,  # Default
                    "is_reel": False      # Default
                }

            # Parse the response to extract the parts
            try:
                # Initialize variables before parsing to avoid reference errors
                instagram_username = known_username or "Unknown"  # We'll use the one from HTML
                image_description = None
                comment = None
                is_negative = False  # Default
                is_reel = False     # Default

                # Check if response is in JSON format (starts with curly brace or has ```json)
                if '{' in analysis and ('"DESCRIPTION"' in analysis.upper() or '"description"' in analysis or '"COMMENT"' in analysis.upper() or '"comment"' in analysis):
                    print("Detected JSON response, parsing as JSON...")

                    # Extract the JSON part from the response if it's wrapped in code blocks
                    if '```json' in analysis.lower():
                        json_text = analysis.split(
                            '```json')[1].split('```')[0].strip()
                    elif '```' in analysis:
                        json_text = analysis.split(
                            '```')[1].split('```')[0].strip()
                    else:
                        # If not wrapped in code blocks, just use the entire text
                        json_text = analysis

                    # Clean up any non-JSON content
                    start_idx = json_text.find('{')
                    end_idx = json_text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_text = json_text[start_idx:end_idx]

                    # Parse JSON
                    import json
                    try:
                        json_data = json.loads(json_text)
                        print("Successfully parsed JSON data:", json_data)

                        # Extract data from JSON (handle different possible key formats)
                        # We're not looking for USERNAME anymore since we get it from HTML

                        # Check for DESCRIPTION keys (uppercase or lowercase)
                        for desc_key in ['DESCRIPTION', 'description', 'Description']:
                            if desc_key in json_data:
                                image_description = json_data.get(
                                    desc_key, "Image content unavailable")
                                break

                        # Check for IS_NEGATIVE keys
                        for neg_key in ['IS_NEGATIVE', 'is_negative', 'Is_Negative', 'isNegative']:
                            if neg_key in json_data:
                                is_negative_val = json_data.get(neg_key)
                                if isinstance(is_negative_val, bool):
                                    is_negative = is_negative_val
                                elif isinstance(is_negative_val, str):
                                    is_negative = is_negative_val.lower() == 'true'
                                break

                        # Check for IS_REEL keys
                        for reel_key in ['IS_REEL', 'is_reel', 'Is_Reel', 'isReel']:
                            if reel_key in json_data:
                                is_reel_val = json_data.get(reel_key)
                                if isinstance(is_reel_val, bool):
                                    is_reel = is_reel_val
                                elif isinstance(is_reel_val, str):
                                    is_reel = is_reel_val.lower() == 'true'
                                break

                        # Check for COMMENT keys (uppercase or lowercase)
                        for comment_key in ['COMMENT', 'comment', 'Comment']:
                            if comment_key in json_data:
                                comment = json_data.get(
                                    comment_key, "Love it!")
                                break

                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        print(f"Attempted to parse: {json_text}")
                        # Fall back to regular text parsing below
                else:
                    # Traditional line-by-line parsing for non-JSON responses
                    print("Using traditional line-by-line parsing")
                    lines = analysis.split('\n')
                    for i, line in enumerate(lines):
                        line_upper = line.upper()
                        # Don't look for USERNAME anymore
                        if "DESCRIPTION:" in line_upper:
                            # Collect description (might span multiple lines)
                            image_description = line.replace(
                                "DESCRIPTION:", "").replace("Description:", "").strip()
                            j = i + 1
                            while j < len(lines) and not (
                                lines[j].upper().startswith("COMMENT:") or
                                lines[j].upper().startswith("IS_NEGATIVE:") or
                                lines[j].upper().startswith("IS_REEL:")
                            ):
                                image_description += " " + lines[j].strip()
                                j += 1
                        elif "IS_NEGATIVE:" in line_upper:
                            is_negative_str = line.split(
                                ":", 1)[-1].strip().lower()
                            is_negative = is_negative_str == 'true'
                        elif "IS_REEL:" in line_upper:
                            is_reel_str = line.split(
                                ":", 1)[-1].strip().lower()
                            is_reel = is_reel_str == 'true'
                        elif "COMMENT:" in line_upper:
                            comment = line.replace("COMMENT:", "").replace(
                                "Comment:", "").strip()
            except Exception as parse_error:
                print(f"Error parsing Gemini response: {parse_error}")
                # Continue with fallback values below

            # If we couldn't parse properly, provide fallbacks
            if not image_description:
                image_description = "Could not analyze image content"
            if not comment:
                comment = "Love it!"

            print("\n--- Extracted Information ---")
            print(f"Instagram Username: {instagram_username}")
            print(f"Image Description: {image_description}")
            print(f"Is Negative: {is_negative}")
            print(f"Is Reel: {is_reel}")
            print(f"Original Comment: {comment}")
            print(f"Sanitized Comment: {sanitize_message(comment)}")

            # Combine description and comment for Google Sheets
            combined_data_for_sheet = f"Story Analysis: {image_description}\n\nComment Sent: {sanitize_message(comment)}"

            # Return all three components
            return {
                "username": instagram_username,
                "description": image_description,
                "comment": comment,
                "is_negative": is_negative,
                "is_reel": is_reel
            }

        except Exception as e:
            print(f"❌ Error analyzing image with Gemini: {e}")
            # Return default values in case of error
            return {
                "username": known_username or "Unknown",
                "description": "Error analyzing image",
                "comment": "Love it!",  # Fallback response
                "is_negative": False,  # Default
                "is_reel": False      # Default
            }

    def save_cookies(self):
        """Save cookies to skip login & 2FA in future runs."""
        try:
            cookies = self.driver.get_cookies()
            with open("instagram_cookies.json", "w") as f:
                json.dump(cookies, f)
            print("✔️ Saved cookies to instagram_cookies.json")
        except Exception as e:
            print(f"⚠️ Failed to save cookies: {e}")

    def load_cookies(self):
        """Load cookies file if present and apply them."""
        if os.path.exists("instagram_cookies.json"):
            print("🔄 Loading cookies from instagram_cookies.json to skip login...")
            self.driver.get("https://www.instagram.com")
            with open("instagram_cookies.json", "r") as f:
                cookies = json.load(f)
            for cookie in cookies:
                try:
                    cookie.pop('sameSite', None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Could not add cookie: {e}")
            self.driver.refresh()
            random_sleep(3, 5)
            return True
        return False

    def record_story_video(self, story_number, html_username, duration=10, interval=0.5):
        """Record story via screenshots if direct download fails."""
        print_substep(f"Recording story for ~{duration}s...")
        frames = []
        video_path = f"story_{story_number}_{html_username}_recorded.mp4"

        try:
            # 1. Unpause the story to let it play (only if currently paused)
            print("Unpausing story for recording...")
            if self.is_story_paused():
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                print("Story was paused, unpaused for recording")
            else:
                print("Story was already playing")
            time.sleep(0.2)  # Small buffer after unpausing

            # 2. Capture frames
            num_frames = int(duration / interval)
            start_time = time.time()
            for i in range(num_frames):
                loop_start = time.time()
                frame_path = f"story_{story_number}_{html_username}_frame_{i}.png"
                if not self.driver.save_screenshot(frame_path):
                    print(f"❌ Failed to save frame {i}")
                    continue  # Skip this frame if save fails
                frames.append(frame_path)
                # Try to maintain the interval timing
                elapsed = time.time() - loop_start
                sleep_duration = max(0, interval - elapsed)
                time.sleep(sleep_duration)

            print(
                f"Captured {len(frames)} frames in {time.time() - start_time:.2f}s.")

            # 3. Stitch frames into video using imageio
            if not frames:
                print("❌ No frames captured, cannot create video.")
                return None

            print(f"Stitching {len(frames)} frames into {video_path}...")
            writer = imageio.get_writer(video_path, fps=int(1/interval))
            for frame_fp in frames:
                try:
                    img = imageio.v2.imread(frame_fp)  # Use imageio.v2.imread
                    writer.append_data(img)
                except Exception as read_err:
                    print(
                        f"⚠️ Skipping frame {frame_fp} due to read error: {read_err}")
            writer.close()
            print(f"✔️ Recorded video saved to {video_path}")
            return video_path

        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None
        finally:
            # 4. Clean up individual frame images
            if frames:
                print(f"Cleaning up {len(frames)} temporary frames...")
                for frame_fp in frames:
                    try:
                        if os.path.exists(frame_fp):
                            os.remove(frame_fp)
                    except Exception as del_err:
                        print(
                            f"⚠️ Failed to delete frame {frame_fp}: {del_err}")

    def _handle_potential_dialogs(self):
        """Handle common Instagram dialogs that might appear after login or navigation."""
        print_substep("Handling potential dialogs (if any)...")

        # Common dialog selectors and actions
        dialog_actions = [
            {
                "name": "Save Login Info",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Not now')]"
                ]
            },
            {
                "name": "Turn On Notifications",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Not now')]"
                ]
            },
            {
                "name": "Add to Home Screen",
                "selectors": [
                    "//button[contains(text(), 'Not Now') or contains(text(), 'not now')]",
                    "//button[contains(text(), 'Cancel')]"
                ]
            }
        ]

        for dialog in dialog_actions:
            try:
                for selector in dialog["selectors"]:
                    try:
                        element = WebDriverWait(self.driver, 1).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if element.is_displayed():
                            print(f"📱 Handling dialog: {dialog['name']}")
                            element.click()
                            time.sleep(1)
                            break
                    except:
                        continue
            except:
                continue

        print_substep("Finished checking for dialogs.")

    def login(self):
        """Automatic login with adaptive detection for different Instagram login page layouts."""
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
                for char in self.username:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                time.sleep(random.uniform(0.8, 1.5))

                # Clear and fill password
                print_substep("Entering password...")
                password_field.clear()
                time.sleep(random.uniform(0.5, 1.0))
                for char in self.password:
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
            "//form//button[last()]"
        ]

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
            "//nav//a[contains(@href, '/')]",  # Navigation home
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
            "//button[contains(text(), 'Not now')]"
        ]

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

    def navigate_home(self, max_retries=3):
        """Navigates to Instagram home page with retry mechanism."""
        print_step("NAVIGATING TO HOME PAGE")

        for retry in range(max_retries):
            try:
                print_substep(
                    f"Navigation attempt {retry + 1}/{max_retries}...")
                print_substep("Looking for home button...")

                # Multiple selectors for the home button
                home_selectors = [
                    "//a//*[name()='svg' and @aria-label='Home']/ancestor::a",
                    "//a[@href='/']",
                    "//a[contains(@href, '/')]//svg[contains(@aria-label, 'Home')]/..",
                    "//span[text()='Home']/ancestor::a",
                    "//a[contains(@class, 'x1i10hfl') and contains(@href, '/')]",
                    "//nav//a[contains(@role, 'link')]"
                ]

                for selector in home_selectors:
                    try:
                        home_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        # Random pause before clicking
                        random_sleep(0.5, 1.5)
                        home_button.click()
                        print("✔️ Successfully clicked home button")
                        random_sleep(3, 5)
                        return True
                    except:
                        continue

                # If all selectors fail, try navigating directly to homepage
                print(
                    "⚠️ Could not find home button, navigating directly to homepage...")
                self.driver.get("https://www.instagram.com/")
                random_sleep(3, 5)
                print("✔️ Navigated directly to homepage")
                return True

            except Exception as e:
                print(f"❌ Navigation error: {e}")

                # Check if the session is invalid or browser closed
                if "invalid session id" in str(e) or "session deleted" in str(e) or "no such window" in str(e):
                    if retry < max_retries - 1:
                        print("Browser closed unexpectedly. Reinitializing...")
                        try:
                            self.setup_driver()
                            # Try to log in again
                            if self.login():
                                print("✔️ Successfully reinitialized and logged in")
                                continue
                            else:
                                print("❌ Failed to login after reinitialization")
                                return False
                        except Exception as setup_error:
                            print(
                                f"❌ Failed to reinitialize driver: {setup_error}")
                            return False
                    else:
                        return False

                # For other errors, just retry
                if retry < max_retries - 1:
                    print(
                        f"Retrying navigation (attempt {retry + 2}/{max_retries})...")
                    random_sleep(2, 4)
                else:
                    return False

        return False

    def get_total_stories(self):
        """Gets the total number of available stories."""
        try:
            # Try multiple selectors for story elements
            selectors = [
                "//div[@role='presentation']//canvas/ancestor::div[@role='button']",
                "//div[contains(@class, '_aarf')]//div[@role='button']",
                "//div[contains(@class, 'x1qjc9v5') and @role='button']"
            ]

            for selector in selectors:
                try:
                    story_elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector))
                    )
                    if len(story_elements) > 0:
                        return len(story_elements)
                except:
                    continue

            return 0
        except Exception as e:
            print(f"❌ Error counting stories: {e}")
            return 0

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

    def pause_and_check_comment_box(self):
        """Enhanced pause and comment box check with better verification"""
        try:
            # First, try to pause the story robustly
            pause_success = self.robust_pause_story()

            # Short delay to let UI settle
            time.sleep(0.3)

            # Check for comment box
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//form//textarea"
            ]

            comment_box_found = False
            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        comment_box_found = True
                        break
                except:
                    continue

            if comment_box_found:
                print("✅ Story paused and comment box found")
                return True
            else:
                print("❌ No comment box found (likely an ad or non-commentable story)")
                return False

        except Exception as e:
            print(f"❌ Error in pause_and_check_comment_box: {e}")
            return False

    def ensure_story_stays_paused(self):
        """Ensure story remains paused during processing"""
        try:
            if not self.is_story_paused():
                print("⚠️ Story became unpaused, re-pausing...")
                return self.robust_pause_story()
            return True
        except Exception as e:
            print(f"⚠️ Error ensuring story stays paused: {e}")
            return False

    def has_comment_box(self):
        """Ultra-fast comment box detection"""
        try:
            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//form//textarea"
            ]

            # Single fast attempt
            for selector in reply_box_selectors:
                try:
                    element = WebDriverWait(self.driver, 0.3).until(
                        EC.presence_of_element_located((By.XPATH, selector)))
                    if element.is_displayed():
                        return True
                except:
                    continue

            return False

        except Exception as e:
            return False

    def get_story_progress_info(self):
        """Get current story progress information to detect story changes"""
        try:
            # Try to find progress bars or story indicators
            progress_selectors = [
                "//div[contains(@class, 'x1i10hfl')]//div[contains(@style, 'width')]",
                "//div[@role='progressbar']",
                "//div[contains(@class, '_ac0k')]//div[contains(@style, 'width')]"
            ]

            progress_info = {}

            for selector in progress_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        # Get the first few progress elements
                        progress_info['progress_elements'] = len(elements)
                        if elements:
                            # Try to get width style of first element
                            style = elements[0].get_attribute('style')
                            if 'width' in style:
                                progress_info['first_width'] = style
                        break
                except:
                    continue

            # Also get current URL as a backup identifier
            progress_info['url'] = self.driver.current_url

            # Get page title
            try:
                progress_info['title'] = self.driver.title
            except:
                progress_info['title'] = ""

            return progress_info

        except Exception as e:
            print(f"⚠️ Error getting story progress: {e}")
            return {'url': self.driver.current_url, 'title': ''}

    def has_story_changed(self, before_info, after_info):
        """Check if we've moved to a different story"""
        try:
            # Check URL change (most reliable)
            if before_info.get('url') != after_info.get('url'):
                print("🔍 Story change detected: URL changed")
                return True

            # Check title change
            if before_info.get('title') != after_info.get('title'):
                print("🔍 Story change detected: Title changed")
                return True

            # Check progress bar count change (indicates different story)
            before_progress = before_info.get('progress_elements', 0)
            after_progress = after_info.get('progress_elements', 0)
            if before_progress != after_progress:
                print("🔍 Story change detected: Progress bar count changed")
                return True

            return False

        except Exception as e:
            print(f"⚠️ Error checking story change: {e}")
            return False

    def is_story_near_end(self):
        """Check if story is near the end to avoid auto-advance during frame capture"""
        try:
            # Look for progress bars that might indicate story progress
            progress_selectors = [
                "//div[contains(@class, 'x1i10hfl')]//div[contains(@style, 'width')]",
                "//div[@role='progressbar']"
            ]

            for selector in progress_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        style = element.get_attribute('style')
                        if 'width' in style:
                            # Try to extract width percentage
                            import re
                            width_match = re.search(
                                r'width:\s*(\d+(?:\.\d+)?)%', style)
                            if width_match:
                                width_percent = float(width_match.group(1))
                                if width_percent > 85:  # If more than 85% complete
                                    print(
                                        f"⚠️ Story is {width_percent}% complete - too close to end")
                                    return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"⚠️ Error checking story progress: {e}")
            return False

    def capture_story_frames(self, story_number, username, num_frames=2, frame_interval=0.2):
        """
        ULTRA-FAST frame capture with minimal delays to prevent story advancement.
        Returns list of screenshot paths.
        """
        screenshot_paths = []

        try:
            # Get initial URL for change detection
            initial_url = self.driver.current_url

            # First frame: immediate capture
            frame1_path = f"story_{story_number}_{username}_frame1.png"
            self.driver.save_screenshot(frame1_path)
            screenshot_paths.append(frame1_path)

            # Only capture additional frames if requested and safe
            if num_frames > 1:
                # Ultra-fast unpause
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()

                # Capture second frame very quickly
                time.sleep(frame_interval)  # Minimal wait

                # Quick URL check
                if self.driver.current_url != initial_url:
                    # Story changed - pause immediately and return
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.SPACE).perform()
                    return "STORY_CHANGED"

                frame2_path = f"story_{story_number}_{username}_frame2.png"
                self.driver.save_screenshot(frame2_path)
                screenshot_paths.append(frame2_path)

                # Immediate pause
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()

                # Final URL check
                if self.driver.current_url != initial_url:
                    return "STORY_CHANGED"

            return screenshot_paths

        except Exception as e:
            print(f"❌ Error capturing frames: {e}")
            # Always try to pause on error
            try:
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
            except:
                pass

            # Return what we have or fallback
            if screenshot_paths:
                return screenshot_paths

            try:
                fallback_path = f"story_{story_number}_{username}_fallback.png"
                self.driver.save_screenshot(fallback_path)
                return [fallback_path]
            except:
                return []

    def keep_story_paused(self):
        """Ultra-fast re-pause without checking state"""
        try:
            # Just pause again - faster than checking state
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.1)  # Minimal wait
        except Exception as e:
            print(f"⚠️ Re-pause failed: {e}")

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
                    r'\"username\":\"([a-zA-Z0-9._]{3,30})\"',
                    r'\"user\":{\"username\":\"([a-zA-Z0-9._]{3,30})\"',
                    r'@([a-zA-Z0-9._]{3,30})',
                    r'([a-zA-Z0-9._]{3,30})\'s story',
                    r'Stories · ([a-zA-Z0-9._]{3,30})',
                    r'instagram.com/([a-zA-Z0-9._]{3,30})(?:/|\")',
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
                    from collections import Counter
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
                                username = title_part.split("'s")[0].strip()
                                if username and re.match(r'^[a-zA-Z0-9._]{3,30}$', username):
                                    if not quiet:
                                        print(
                                            f"✅ Extracted username from page title: {username}")
                                    self._last_extracted_username = username
                                    return username
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

    def find_and_click_next_story(self):
        """Navigate to next story using DOWN arrow key only."""
        try:
            print_substep("Navigating to next story...")

            # Keep track of the current URL to verify movement
            current_url = self.driver.current_url

            # Use DOWN arrow key only - most reliable method
            webdriver.ActionChains(self.driver).send_keys(
                Keys.ARROW_DOWN).perform()
            time.sleep(1.5)  # Increased wait time

            # Check if URL changed to confirm navigation
            new_url = self.driver.current_url
            if new_url != current_url:
                print("✔️ Successfully navigated to next story")
                return True

            # If first attempt failed, try one more time
            print("First navigation attempt failed, trying again...")
            webdriver.ActionChains(self.driver).send_keys(
                Keys.ARROW_DOWN).perform()
            time.sleep(1.5)

            new_url = self.driver.current_url
            if new_url != current_url:
                print("✔️ Successfully navigated on second attempt")
                return True

            print("❌ Navigation failed")
            return False

        except Exception as e:
            print(f"❌ Error in story navigation: {e}")
            return False

    def verify_username_with_gemini(self, image_path: str, expected_username: str) -> bool:
        """
        Verifies that the current screenshot shows a story from the expected username.
        Returns True if username matches, False if different or error.
        """
        print_substep(
            f"VERIFYING USERNAME: Expected '{expected_username}' with screenshot verification...")
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            image_part = {"mime_type": "image/jpeg", "data": image_data}

            if not image_data:
                print("❌ No image data for username verification.")
                return False

            verification_prompt = f"""You are analyzing an Instagram story screenshot to verify the username.

Look at this Instagram story screenshot and identify the username of the person who posted this story.

The username I expect to see is: "{expected_username}"

Instructions:
1. Look for the username displayed in the story interface (usually at the top of the story)
2. Extract the exact username as it appears (without @ symbol)
3. Compare it with the expected username: "{expected_username}"

Respond with ONLY one of these exact formats:

VERIFIED: YES - {expected_username}
(if the username in the screenshot exactly matches the expected username)

VERIFIED: NO - [actual_username_you_see]
(if the username is different, replace [actual_username_you_see] with what you actually see)

VERIFIED: ERROR
(if you cannot clearly identify any username in the screenshot)"""

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    print(
                        f"Gemini username verification attempt {attempt + 1}/{max_retries}...")
                    response = self.model.generate_content(
                        contents=[
                            {"text": verification_prompt},
                            {"inline_data": image_part}
                        ],
                        generation_config=genai.GenerationConfig(
                            max_output_tokens=100,
                            temperature=0.2  # Low temperature for precise verification
                        )
                    )

                    if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                        response_text = response.text.strip()
                        print(
                            f"--- Gemini Username Verification ---\n{response_text}\n--------------------------------")

                        if f"VERIFIED: YES - {expected_username}" in response_text:
                            print(f"✅ USERNAME VERIFIED: {expected_username}")
                            return True
                        elif "VERIFIED: NO -" in response_text:
                            actual_username = response_text.replace(
                                "VERIFIED: NO -", "").strip()
                            print(
                                f"❌ USERNAME MISMATCH: Expected '{expected_username}' but found '{actual_username}'")
                            return False
                        elif "VERIFIED: ERROR" in response_text:
                            print(
                                "❌ USERNAME VERIFICATION ERROR: Could not identify username in screenshot")
                            return False
                        else:
                            print(
                                f"⚠️ Unexpected verification response: {response_text}")
                            if attempt < max_retries - 1:
                                continue
                            return False
                    else:
                        print(
                            f"⚠️ Empty response from Gemini on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        return False

                except Exception as e:
                    print(
                        f"⚠️ Gemini username verification error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return False

            return False

        except Exception as e:
            print(f"❌ Error in username verification: {e}")
            return False

    def confirm_comment_with_gemini(self, image_path: str, comment_to_check: str, original_username: str) -> Tuple[Optional[str], bool]:
        """
        Confirms if a previously generated comment is still relevant to the current story screenshot.
        Returns the confirmed/new comment (or None if error) and a boolean indicating if it was confirmed as is.
        """
        print_substep(
            f"CONFIRMING COMMENT for {original_username} with new screenshot...")
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            image_part = {"mime_type": "image/jpeg", "data": image_data}

            if not image_data:
                print("❌ No image data for confirmation.")
                return None, False  # No image, can't confirm

            confirmation_prompt = f"""You are an Instagram comment confirmation assistant.
I have an Instagram story screenshot and a comment I'm about to post.

Here is the comment I plan to send:
"{comment_to_check}"

Analyze the NEW screenshot of the story currently on screen.

1.  Is the comment "{comment_to_check}" relevant and appropriate for the VISUALS and any TEXT in THIS NEW screenshot?
    *   Consider if the story might have changed since the original comment was generated.
    *   Focus on the MAIN story content.

2.  Respond in one of the following two formats ONLY:

    EITHER (if the comment is good):
    CONFIRMED: YES

    OR (if the comment is NOT good, or if the story seems completely different/unrelated):
    CORRECTED_COMMENT: [New, very short, appropriate comment in Shannon's style (Male Australian Personal Trainer). Use casual Aussie slang. 1-10 words. Emojis are okay. If it's a Reel, a single laughing emoji is preferred or a 1-5 word reaction to text IN the reel. If unsure or it's an ad/reshare without clear original content, default to a single relevant emoji like 👍 or 😂.]
"""
            analysis_instruction = "Confirm or correct the comment based on the new screenshot and my instructions."

            max_api_retries = 2  # Fewer retries for confirmation
            api_retry_count = 0
            response_text = None

            while api_retry_count < max_api_retries and not response_text:
                try:
                    print(
                        f"Gemini confirmation API attempt {api_retry_count + 1}/{max_api_retries}...")
                    response = self.model.generate_content(
                        contents=[
                            {"text": confirmation_prompt},
                            {"text": analysis_instruction},
                            {"inline_data": image_part}
                        ],
                        generation_config=genai.GenerationConfig(
                            max_output_tokens=100,  # Shorter response needed
                            temperature=0.5      # Slightly lower temp for more deterministic confirmation
                        )
                    )
                    if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                        response_text = response.text.strip()
                        print(
                            f"--- Gemini Confirmation Response ---\\n{response_text}\\n---------------------------------")
                    else:
                        print(
                            f"⚠️ Gemini confirmation returned empty response on attempt {api_retry_count + 1}")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            random_sleep(2, 3)
                        else:
                            print(
                                "⚠️ All Gemini confirmation retries failed (empty response).")
                            return None, False  # Error
                except Exception as retry_error:
                    print(
                        f"⚠️ Gemini confirmation API error on attempt {api_retry_count + 1}: {retry_error}")
                    api_retry_count += 1
                    if api_retry_count < max_api_retries:
                        random_sleep(2, 3)
                    else:
                        print(
                            "⚠️ All Gemini confirmation retries failed (API error).")
                        return None, False  # Error

            if not response_text:
                return None, False

            if response_text.startswith("CONFIRMED: YES"):
                print("✔️ Comment confirmed as relevant.")
                return comment_to_check, True
            elif response_text.startswith("CORRECTED_COMMENT:"):
                new_comment = response_text.replace(
                    "CORRECTED_COMMENT:", "").strip()
                print(
                    f"⚠️ Comment was not relevant. Using new comment: '{new_comment}'")
                return new_comment, False
            else:
                print(
                    f"⚠️ Unusual response from confirmation: {response_text}. Defaulting to original comment.")
                return comment_to_check, False

        except Exception as e:
            print(f"❌ Error in confirm_comment_with_gemini: {e}")
            return None, False  # Error

    def verify_story_match_with_gemini(self, image_path: str, original_description: str, original_username: str) -> Optional[bool]:
        """
        Verifies if the current story screenshot still matches the original analysis.
        Returns: True if matches, False if not, None if error.
        """
        print_substep(
            f"VERIFYING STORY CONTENT for {original_username} against new screenshot...")
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            image_part = {"mime_type": "image/jpeg", "data": image_data}

            if not image_data:
                print("❌ No image data for story content verification.")
                return None

            verification_prompt = f"""You are an Instagram story content verification assistant.
I have a NEW screenshot from an Instagram story. My goal is to ensure this NEW screenshot is still showing the EXACT SAME story content that I analyzed previously.

- The story was originally posted by: "{original_username}"
- The original description of the story was: "{original_description}"

Based *only* on the NEW screenshot provided:
1. Is the username "{original_username}" clearly visible and identifiable in the new screenshot?
2. Does the primary visual content of the NEW screenshot strongly and unmistakably align with the original description: "{original_description}"?

Consider if the new screenshot shows a completely different scene, a different person, or a significantly different activity than what was originally described. Minor changes in angle or expression are acceptable if the core subject and context are the same.

Respond ONLY with one of these exact phrases:
- CONFIRMED: YES (If you are highly confident it's the same story moment from the same user matching the description)
- CONFIRMED: NO (If it's clearly a different story, different user, or the content does not match the description)
"""
            analysis_instruction = "Verify the story content based on the new screenshot and my instructions."

            max_api_retries = 2
            api_retry_count = 0
            response_text = None

            while api_retry_count < max_api_retries and not response_text:
                try:
                    print(
                        f"Gemini story match API attempt {api_retry_count + 1}/{max_api_retries}...")
                    response = self.model.generate_content(
                        contents=[
                            {"text": verification_prompt},
                            {"text": analysis_instruction},
                            {"inline_data": image_part}
                        ],
                        generation_config=genai.GenerationConfig(
                            max_output_tokens=50,  # Short response
                            temperature=0.3     # Lower temp for more deterministic verification
                        )
                    )
                    if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                        response_text = response.text.strip()
                        print(
                            f"--- Gemini Story Match Response ---\\n{response_text}\\n---------------------------------")
                    else:
                        print(
                            f"⚠️ Gemini story match returned empty response on attempt {api_retry_count + 1}")
                        api_retry_count += 1
                        if api_retry_count < max_api_retries:
                            random_sleep(1, 2)
                except Exception as retry_error:
                    print(
                        f"⚠️ Gemini story match API error on attempt {api_retry_count + 1}: {retry_error}")
                    api_retry_count += 1
                    if api_retry_count < max_api_retries:
                        random_sleep(1, 2)

            if not response_text:
                print("⚠️ All Gemini story match retries failed (empty or API error).")
                return None  # Error

            if "CONFIRMED: YES" in response_text:
                print("✔️ Story content MATCHES original analysis.")
                return True
            elif "CONFIRMED: NO" in response_text:
                print("❌ Story content DOES NOT MATCH original analysis.")
                return False
            else:
                print(
                    f"⚠️ Unusual response from story match: {response_text}. Assuming no match for safety.")
                return False  # Default to False for safety on ambiguous response

        except Exception as e:
            print(f"❌ Error in verify_story_match_with_gemini: {e}")
            return None  # Error

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

    def manual_message_confirmation(self, username, story_description, proposed_comment):
        """
        Allow user to manually confirm, edit, or reject a message before sending.
        WITH CRITICAL STORY CHANGE DETECTION - abort if story changes during confirmation.
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
        print("=" * 80)

        # Get initial story state to detect changes
        initial_url = self.driver.current_url
        initial_username = self.extract_instagram_username()

        # ROBUST initial pause
        print("🛑 Robustly pausing story for confirmation...")
        for initial_pause in range(3):
            try:
                webdriver.ActionChains(self.driver).send_keys(
                    Keys.SPACE).perform()
                time.sleep(0.2)
            except:
                pass
        print("✅ Story paused for confirmation")

        stop_pausing_event = threading.Event()
        story_changed_during_confirmation = False

        def _aggressive_story_pausing():
            """VERY aggressive story pausing during user confirmation"""
            pause_interval = 1.0  # Pause every 1 second (more frequent)
            last_url_check = time.time()
            # Check URL every 2 seconds (more frequent)
            url_check_interval = 2.0

            while not stop_pausing_event.is_set():
                try:
                    # ALWAYS pause first, regardless of checks
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.SPACE).perform()

                    current_time = time.time()

                    # Check for story changes more frequently
                    if current_time - last_url_check > url_check_interval:
                        # Quick URL-only check (no expensive username extraction)
                        current_url = self.driver.current_url

                        # Simple URL change detection (most reliable indicator)
                        if current_url != initial_url:
                            nonlocal story_changed_during_confirmation
                            story_changed_during_confirmation = True
                            print(
                                f"\n🚨 CRITICAL: Story URL changed during confirmation!")
                            print(f"   Expected URL: {initial_url}")
                            print(f"   Current URL: {current_url}")
                            print(
                                "   ABORTING CONFIRMATION TO PREVENT WRONG MESSAGE!")

                            # EMERGENCY PAUSE before aborting
                            print(
                                "🛑 EMERGENCY PAUSING current story before abort...")
                            for emergency_pause in range(3):
                                try:
                                    webdriver.ActionChains(self.driver).send_keys(
                                        Keys.SPACE).perform()
                                    time.sleep(0.2)
                                except:
                                    pass

                            stop_pausing_event.set()
                            break

                        last_url_check = current_time

                    time.sleep(pause_interval)

                except Exception as e:
                    # Continue pausing even on errors
                    try:
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.SPACE).perform()
                    except:
                        pass
                    time.sleep(pause_interval)

        # Start aggressive pausing thread
        pause_thread = threading.Thread(
            target=_aggressive_story_pausing, daemon=True)
        pause_thread.start()

        final_comment = proposed_comment
        should_send = True
        change_reason = None
        user_choice_made = False

        try:
            while not user_choice_made and not story_changed_during_confirmation:
                print("\n📋 Options:")
                print("  1. Press ENTER to send the message as-is")
                print("  2. Type 'edit' or 'e' to modify the message")
                print("  3. Type 'skip' or 's' to skip this story")
                print("  4. Type 'quit' or 'q' to stop the bot")

                # Check for story change before getting input
                if story_changed_during_confirmation:
                    break

                user_input = input("\n➤ Your choice: ").strip().lower()

                # Check again after user input
                if story_changed_during_confirmation:
                    break

                if user_input == "" or user_input == "1":
                    print("✅ Sending message as-is...")
                    final_comment, should_send, change_reason = proposed_comment, True, None
                    user_choice_made = True
                elif user_input in ["edit", "e", "2"]:
                    print(f"\n📝 Current message: '{proposed_comment}'")
                    new_message = input("➤ Enter new message: ").strip()

                    # Check for story change during editing
                    if story_changed_during_confirmation:
                        break

                    if new_message:
                        reason_input = input(
                            "➤ Why did you change the message? (optional): ").strip()
                        change_reason = reason_input if reason_input else "User preferred different message"
                        print(f"\n✅ Message updated to: '{new_message}'")
                        print(f"📝 Reason: {change_reason}")

                        # Check for story change before final confirmation
                        if story_changed_during_confirmation:
                            break

                        confirm = input(
                            "\n➤ Send this new message? (y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '']:
                            print("✅ Sending updated message...")
                            final_comment, should_send = new_message, True
                            user_choice_made = True
                        else:
                            print("🔄 Let's try again...")
                    else:
                        print("❌ Empty message not allowed. Try again.")
                elif user_input in ["skip", "s", "3"]:
                    reason_input = input(
                        "➤ Why are you skipping? (optional): ").strip()
                    change_reason = reason_input if reason_input else "User chose to skip"
                    print(f"⏭️ Skipping story for {username}")
                    final_comment, should_send = None, False
                    user_choice_made = True
                elif user_input in ["quit", "q", "4"]:
                    print("🛑 Stopping bot as requested")
                    final_comment, should_send, change_reason = None, False, "User requested to quit"
                    user_choice_made = True
                else:
                    print(
                        "❌ Invalid option. Please choose 1, 2, 3, 4, or use the shortcuts.")

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user (Ctrl+C)")
            final_comment, should_send, change_reason = None, False, "User interrupted with Ctrl+C"
        except Exception as e:
            print(f"❌ Error getting user input: {e}")
            print("⚠️ Defaulting to sending original message...")
            final_comment, should_send, change_reason = proposed_comment, True, None
        finally:
            # Stop the pause monitoring thread
            stop_pausing_event.set()
            pause_thread.join(timeout=2)

        # Handle story change detection
        if story_changed_during_confirmation:
            print(
                "🚨 STORY CHANGED DURING CONFIRMATION - ABORTING TO PREVENT WRONG MESSAGE")
            return None, False, "Story changed during confirmation - prevented wrong message"

        # Final verification that we're still on the right story
        final_url = self.driver.current_url
        final_username = self.extract_instagram_username(quiet=True)

        if (final_url != initial_url or
                (final_username and initial_username and final_username != initial_username)):
            print(
                f"🚨 FINAL CHECK: Story changed from {initial_username} to {final_username}")
            print("🚨 ABORTING TO PREVENT SENDING MESSAGE TO WRONG PERSON")
            return None, False, "Story changed after confirmation - prevented wrong message"

        return final_comment, should_send, change_reason

    def process_single_story(self, story_number, total_stories):
        """Process a single story with simplified single-screenshot approach."""
        screenshot_path = None
        success = False

        try:
            print_step(f"PROCESSING STORY {story_number}/{total_stories}")

            # 0. Start pause monitoring to keep story paused during processing
            print_substep("0. Starting pause monitoring...")
            self.pause_monitor.start_monitoring()

            # 1. SIMPLE PAUSE - no complex monitoring
            print_substep("1. Pausing story and checking for comment box...")

            # ROBUST PAUSE - Multiple attempts with verification
            pause_success = False
            for pause_attempt in range(5):  # Try up to 5 times
                try:
                    print(f"   Pause attempt {pause_attempt + 1}/5...")
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.SPACE).perform()
                    time.sleep(0.3)  # Wait for pause to register

                    # Quick check if pause worked by looking for play button or static progress
                    try:
                        # Look for play button indicators
                        play_indicators = self.driver.find_elements(By.XPATH,
                                                                    "//div[contains(@aria-label, 'Play')] | //*[name()='svg' and contains(@aria-label, 'Play')]")
                        if play_indicators:
                            print(
                                f"   ✅ Pause confirmed on attempt {pause_attempt + 1}")
                            pause_success = True
                            break
                    except:
                        pass

                    # If no clear play button, assume paused after attempt 3
                    if pause_attempt >= 2:
                        print(
                            f"   ⚠️ Assuming paused after {pause_attempt + 1} attempts")
                        pause_success = True
                        break

                except Exception as pause_error:
                    print(
                        f"   ❌ Pause attempt {pause_attempt + 1} failed: {pause_error}")
                    time.sleep(0.2)

            if not pause_success:
                print("⚠️ Could not confirm pause, but continuing...")

            can_comment = self.has_comment_box()

            if not can_comment:
                print("❌ No comment box found - this is likely an ad, skipping...")
                return "NO_REPLY_BOX"

            # 2. Get username
            print_substep("2. Extracting username...")
            html_username = self.extract_instagram_username()
            if not html_username:
                print("❌ Could not extract username, skipping...")
                return "NO_REPLY_BOX"

            print(f"Processing story for username: {html_username}")

            # Check if already processed
            if html_username in self.processed_usernames:
                print(f"⚠️ Already processed {html_username} this session")
                return "NO_REPLY_BOX"

            # 2.5. ENSURE PAUSE BEFORE SCREENSHOT
            print_substep("2.5. Final pause before screenshot...")
            webdriver.ActionChains(self.driver).send_keys(Keys.SPACE).perform()
            time.sleep(0.3)

            # 3. Take ONE screenshot and analyze
            print_substep("3. Taking screenshot and analyzing...")

            screenshot_path = f"story_{story_number}_{html_username}_single.png"

            # Simple screenshot capture
            try:
                success = self.driver.save_screenshot(screenshot_path)
                if not success:
                    print("❌ Failed to capture screenshot")
                    return "NO_REPLY_BOX"
                print(f"✔️ Screenshot captured: {screenshot_path}")
            except Exception as screenshot_error:
                print(f"❌ Screenshot error: {screenshot_error}")
                return "NO_REPLY_BOX"

            # Analyze with Gemini
            analysis_result = self.analyze_image_with_gpt(
                screenshot_path, html_username)
            if not analysis_result:
                print("❌ Failed to analyze screenshot")
                return "NO_REPLY_BOX"

            comment = analysis_result.get('comment', 'Love it! 🔥')
            description = analysis_result.get('description', 'Story content')
            is_negative = analysis_result.get('is_negative', False)

            # FIRST sanitize the comment
            sanitized_comment = sanitize_message(comment)

            # THEN handle empty comments AFTER sanitization (this is where the problem was!)
            if not sanitized_comment or sanitized_comment.strip() == '' or sanitized_comment.strip() == "''" or sanitized_comment.strip() == '""':
                print("⚠️ Empty comment detected after sanitization, using fallback...")

                # Generate fallback comments WITH emojis (since we now preserve them)
                is_reel = analysis_result.get('is_reel', False)

                if is_reel:
                    # For reels, prefer laughing emoji or simple reactions
                    sanitized_comment = "😂"
                elif 'workout' in description.lower() or 'gym' in description.lower() or 'fitness' in description.lower():
                    sanitized_comment = random.choice(
                        ["Get it! 💪", "Crushing it! 💪", "New PR? 💪"])
                elif 'food' in description.lower() or 'meal' in description.lower() or 'eat' in description.lower():
                    sanitized_comment = random.choice(
                        ["Looks good! 😋", "Yum! 😋", "Homemade? 😋"])
                elif 'pet' in description.lower() or 'dog' in description.lower() or 'cat' in description.lower():
                    sanitized_comment = random.choice(
                        ["Cutie! 🥰", "Good boy? 🥰", "Adorable! 🥰"])
                elif 'car' in description.lower() or 'truck' in description.lower() or 'vehicle' in description.lower():
                    sanitized_comment = random.choice(
                        ["Nice ride! 🔥", "Your ride? 🔥", "New purchase? 🔥"])
                elif 'travel' in description.lower() or 'beach' in description.lower() or 'view' in description.lower():
                    sanitized_comment = random.choice(
                        ["Beautiful! 😍", "Amazing view! 😍", "Holiday? 😍"])
                else:
                    sanitized_comment = random.choice(
                        ["Love this! 👌", "Nice! 👌", "Looking good! 💯"])  # Generic fallbacks

                print(f"   Using fallback comment: '{sanitized_comment}'")

            if is_negative:
                print(
                    f"⚠️ Skipping story for {html_username} due to negative content detected.")
                return "NEGATIVE_CONTENT"

            # 4. SIMPLIFIED Manual user confirmation (NO AGGRESSIVE PAUSING THREAD)
            print_substep("4. Manual message confirmation...")

            change_reason = None
            try:
                # SIMPLE confirmation with basic pause maintenance
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

                # Update the final comment if user made changes
                if confirmed_message != sanitized_comment:
                    sanitized_comment = confirmed_message
                    print(f"💬 Message updated by user: '{sanitized_comment}'")

            except Exception as manual_confirm_err:
                print(
                    f"❌ Error during manual confirmation: {manual_confirm_err}")
                change_reason = None

            # 5. Final username verification before sending
            print_substep("5. Final username verification before sending...")

            # Take a fresh screenshot for verification
            verification_screenshot_path = f"story_{story_number}_{html_username}_verification.png"
            try:
                verification_success = self.driver.save_screenshot(
                    verification_screenshot_path)
                if not verification_success:
                    print("❌ Failed to capture verification screenshot")
                    return "NO_REPLY_BOX"

                # Verify username with Gemini
                username_verified = self.verify_username_with_gemini(
                    verification_screenshot_path, html_username)

                if not username_verified:
                    print(
                        f"🚨 USERNAME VERIFICATION FAILED! Will NOT send message to prevent wrong recipient.")
                    print(
                        f"🚨 Expected: {html_username}, but verification failed.")
                    print(f"🚨 ABORTING MESSAGE SEND FOR SAFETY")
                    return "VERIFICATION_FAILED"

                print(f"✅ Username verification PASSED for {html_username}")

            except Exception as verification_error:
                print(f"❌ Username verification error: {verification_error}")
                print(
                    f"🚨 ABORTING MESSAGE SEND due to verification error (safety first)")
                return "VERIFICATION_ERROR"
            finally:
                # Clean up verification screenshot
                if os.path.exists(verification_screenshot_path):
                    try:
                        os.remove(verification_screenshot_path)
                    except:
                        pass

            # 6. Send message (simplified)
            print_substep("6. Sending message...")

            # Analytics update
            try:
                analytics.update_story_interaction(
                    html_username,
                    description,
                    sanitized_comment,
                    change_reason
                )
                print(f"✔️ Updated analytics for {html_username}")
            except Exception as analytics_error:
                print(f"⚠️ Analytics update error: {analytics_error}")

            # Send message with simple retry
            send_success = False
            max_send_retries = 2

            reply_box_selectors = [
                "//textarea[@autocomplete='off' and contains(@class, 'x1i10hfl')]",
                "//textarea[@placeholder='Reply...']",
                "//textarea[@placeholder='Send message']",
                "//form//textarea"
            ]

            for attempt in range(max_send_retries):
                try:
                    reply_box = None
                    for selector in reply_box_selectors:
                        try:
                            reply_box = WebDriverWait(self.driver, 2).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, selector))
                            )
                            break
                        except:
                            continue

                    if not reply_box:
                        print(
                            f"❌ Could not find reply box on send attempt {attempt+1}")
                        time.sleep(0.5)
                        continue

                    reply_box.clear()
                    for char_send in sanitized_comment:
                        reply_box.send_keys(char_send)
                        time.sleep(random.uniform(0.05, 0.15))

                    time.sleep(random.uniform(0.3, 0.7))
                    reply_box.send_keys(Keys.ENTER)
                    time.sleep(random.uniform(0.8, 1.2))

                    print(
                        f"✔️ Sent message to {html_username}: {sanitized_comment}")
                    send_success = True
                    break

                except Exception as e_send:
                    print(f"⚠️ Send attempt {attempt+1} failed: {e_send}")
                    time.sleep(1)

            if send_success:
                self.processed_usernames.add(html_username)
                success = True
            else:
                print(
                    f"❌ Failed to send message to {html_username} after {max_send_retries} attempts")
                return "NO_REPLY_BOX"

            return success

        except Exception as e_outer:
            print(f"❌ Error processing story: {e_outer}")
            return "NO_REPLY_BOX"

        finally:
            # Stop pause monitoring
            self.pause_monitor.stop_monitoring()

            # Cleanup screenshot
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                except:
                    pass

    def interact_with_stories(self):
        """Interacts with all available Instagram stories with improved error handling."""
        story_count = 0
        successful_comments = 0
        processing = True
        consecutive_failures = 0
        MAX_FAILURES = 5
        last_story_time = time.time()
        max_retries = 3

        # Target successful comments count (keep processing until we reach this)
        TARGET_SUCCESSFUL_COMMENTS = 100

        # Maximum number of stories to process before restarting completely
        MAX_STORIES_BEFORE_RESTART = 150

        # Track consecutive same username to detect being stuck
        last_username = None
        same_username_count = 0
        MAX_SAME_USERNAME = 5  # After this many repeats, consider stuck

        # Only track usernames we've commented on in this session (separate from processed_usernames which persists across sessions)
        seen_usernames = set()

        try:
            # Find first non-live story with retries
            print_step("FINDING FIRST NON-LIVE STORY")
            first_story_element = self.get_first_non_live_story(
                max_retries=max_retries)

            if not first_story_element:
                print("❌ No suitable stories found to process after retries.")
                # Try refreshing the page and attempt again as a last resort
                print("Refreshing page and trying to find stories one last time...")
                self.driver.refresh()
                random_sleep(5, 7)
                first_story_element = self.get_first_non_live_story(
                    max_retries=1)  # Only one attempt after refresh
                if not first_story_element:
                    print(
                        "❌ Still no suitable stories found after refresh. Exiting story interaction.")
                    return

            print_step("OPENING FIRST STORY")
            random_sleep(1, 2)  # Human-like delay

            try:
                # Ensure element is clickable and in view
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(first_story_element)
                )
                # Try JavaScript click first as it can be more reliable for complex elements
                self.driver.execute_script(
                    "arguments[0].click();", first_story_element)
                print("✔️ Clicked first story using JavaScript.")
            except Exception as e_js_click:
                print(
                    f"⚠️ JavaScript click failed: {e_js_click}. Trying regular click...")
                try:
                    # Fallback to regular Selenium click
                    # ActionChains can sometimes help with elements that are tricky to click
                    actions = ActionChains(self.driver)
                    actions.move_to_element(
                        first_story_element).click().perform()
                    print("✔️ Clicked first story using ActionChains.")
                except Exception as e_regular_click:
                    print(
                        f"❌ Failed to click on first story with both methods: {e_regular_click}")
                    return

            # Wait for story to potentially load/transition
            random_sleep(1.5, 2.5)

            # Immediately pause the first story and check if it's commentable
            print_substep("Pausing first story and checking if commentable...")
            can_comment = self.pause_and_check_comment_box()
            if not can_comment:
                print(
                    "⚠️ First story is not commentable (likely an ad), will skip during processing")
            print("✔️ First story pausing completed")
            random_sleep(0.5, 0.8)

            # Process stories with improved error handling
            while processing and story_count < MAX_STORIES_BEFORE_RESTART and successful_comments < TARGET_SUCCESSFUL_COMMENTS:
                try:
                    story_count += 1
                    print_step(f"PROCESSING STORY {story_count}")

                    # STEP 1: Story is already paused at this point
                    print_substep(
                        "Checking for username and analyzing story...")

                    # Extract username
                    html_username = self.extract_instagram_username()

                    # Check if we're stuck on the same username
                    if html_username == last_username:
                        same_username_count += 1
                        if same_username_count >= MAX_SAME_USERNAME:
                            print(
                                f"⚠️ Stuck on same username ({html_username}) {same_username_count} times")
                            # Take screenshot before waiting for user
                            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                            screenshot_filename = f"stuck_debug_USER_{html_username}_{timestamp}.png"
                            try:
                                self.driver.save_screenshot(
                                    screenshot_filename)
                                print(
                                    f"📸 Screenshot saved to {screenshot_filename} for debugging.")
                            except Exception as ss_err:
                                print(
                                    f"⚠️ Could not save screenshot: {ss_err}")
                            wait_for_user_input(
                                "STUCK DETECTED (SAME USERNAME): Please manually navigate or check screenshot.")
                            same_username_count = 0  # Reset after user intervention
                    else:
                        same_username_count = 0
                        last_username = html_username

                    # Check if we've already processed this username
                    if html_username in seen_usernames:
                        print(
                            f"⚠️ Already processed {html_username} this session")

                        # STEP 5: Use keyboard navigation instead of clicking coordinates
                        print_substep(
                            "Skipping to next story (using keyboard navigation)...")
                        try:
                            # Use DOWN arrow key which is more reliable than clicking coordinates
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.ARROW_DOWN).perform()
                            print("✔️ Advanced to next story using DOWN arrow")
                        except Exception as nav_err:
                            print(
                                f"❌ Failed to navigate with keyboard: {nav_err}")
                            # As a final fallback, try SPACE key to advance
                            try:
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.SPACE).perform()
                                print("✔️ Advanced story using SPACE key")
                            except Exception as space_err:
                                print(
                                    f"❌ All navigation methods failed: {space_err}")

                        # STEP 6: Immediately pause the next story (reduce delay)
                        # Very short fixed delay before pausing
                        time.sleep(0.3)
                        self.robust_pause_story()
                        print("✔️ Next story paused")
                        random_sleep(0.5, 0.8)
                        continue

                    # Add username to seen set for this session
                    seen_usernames.add(html_username)

                    # STEP 2: Analyze story and send DM
                    story_processing_result = self.process_single_story(
                        story_count, MAX_STORIES_BEFORE_RESTART - story_count
                    )

                    # STEP 3 & 4: Update counts and stats
                    if story_processing_result is True:
                        successful_comments += 1
                        consecutive_failures = 0
                        print(
                            f"✔️ Successfully processed {html_username} ({successful_comments}/{TARGET_SUCCESSFUL_COMMENTS})")
                        # Successfully processed, so navigate to the NEXT story
                        print_substep(
                            "Moving to next story (keyboard navigation after successful processing)...")
                        try:
                            # Use reliable keyboard navigation
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.ARROW_DOWN).perform()
                            print("✔️ Advanced to next story using DOWN arrow")
                        except Exception as nav_error:
                            print(f"❌ Navigation failed: {nav_error}")
                            # Fallback to SPACE key
                            try:
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.SPACE).perform()
                                print("✔️ Advanced using SPACE key")
                            except Exception as space_error:
                                print(
                                    f"❌ All navigation failed: {space_error}")

                        time.sleep(0.3)  # Brief pause after navigation
                        self.robust_pause_story()  # Pause next story
                        print(
                            "✔️ Paused story after successful processing and advancing.")
                        random_sleep(0.5, 0.8)

                    elif story_processing_result in ["NO_REPLY_BOX", "VERIFICATION_FAILED", "VERIFICATION_ERROR"]:
                        # This is an Ad, a story without a reply box, or content verification failed.
                        log_message = {
                            "NO_REPLY_BOX": f"⚠️ No reply box for {html_username} (likely an ad). Performing skip-pause.",
                            "VERIFICATION_FAILED": f"❌ Story content verification FAILED for {html_username}. Skipping.",
                            "VERIFICATION_ERROR": f"⚠️ Story content verification ERROR for {html_username}. Skipping for safety."
                        }
                        print_substep(log_message.get(
                            story_processing_result, "Skipping story."))
                        consecutive_failures = 0  # Reset failures as this is a planned skip

                        # First action: unpause if paused, or advance if playing
                        if self.is_story_paused():
                            # Story is paused, unpause it to let it advance
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.SPACE).perform()
                            print_substep("Unpaused story to let it advance")
                            random_sleep(0.7, 1.3)  # Wait for story to advance
                        else:
                            # Story is playing, let it advance naturally or press space to advance
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.SPACE).perform()
                            print_substep("Advanced to next story")
                            random_sleep(0.7, 1.3)

                        # Now pause the newly loaded story
                        self.robust_pause_story()
                        print("✔️ Story skipped and new story paused.")
                        random_sleep(0.5, 0.8)
                        # The loop will continue and process this newly paused story

                    elif story_processing_result == "NEGATIVE_CONTENT":
                        # Story was flagged as negative content by Gemini analysis
                        print_substep(
                            f"⏩ Skipping story for {html_username} due to negative content. Performing skip-pause.")
                        consecutive_failures = 0  # Reset failures, this is a planned skip

                        # First action: unpause if paused, or advance if playing
                        if self.is_story_paused():
                            # Story is paused, unpause it to let it advance
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.SPACE).perform()
                            print_substep(
                                "Unpaused negative story to let it advance")
                            random_sleep(0.7, 1.3)  # Wait for story to advance
                        else:
                            # Story is playing, let it advance naturally or press space to advance
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.SPACE).perform()
                            print_substep("Advanced past negative story")
                            random_sleep(0.7, 1.3)

                        # Now pause the newly loaded story
                        self.robust_pause_story()
                        print("✔️ Negative story skipped and new story paused.")
                        random_sleep(0.5, 0.8)

                    elif story_processing_result == "USER_QUIT":
                        # User requested to quit the bot
                        print(
                            "🛑 User requested to quit the bot. Stopping story processing.")
                        processing = False
                        break

                    elif story_processing_result == "USER_SKIP":
                        # User chose to skip this story
                        print_substep(
                            f"⏩ User chose to skip story for {html_username}. Moving to next story.")
                        consecutive_failures = 0  # Reset failures, this is a planned skip

                        # Navigate to next story
                        try:
                            # Use keyboard navigation instead of clicking
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.ARROW_DOWN).perform()
                            print(
                                "✔️ Advanced to next story using DOWN arrow after user skip")
                        except Exception as nav_error:
                            print(
                                f"❌ Navigation failed after user skip: {nav_error}")
                            # Fallback to SPACE key
                            try:
                                webdriver.ActionChains(self.driver).send_keys(
                                    Keys.SPACE).perform()
                                print("✔️ Advanced using SPACE key after user skip")
                            except Exception as space_error:
                                print(
                                    f"❌ All navigation failed after user skip: {space_error}")

                        time.sleep(0.3)
                        self.robust_pause_story()
                        print("✔️ Paused story after user skip.")
                        random_sleep(0.5, 0.8)

                    # story_processing_result is False (an actual error during processing)
                    else:
                        consecutive_failures += 1
                        print(
                            f"⚠️ Failed to process {html_username} (Failure #{consecutive_failures})")
                        if consecutive_failures >= MAX_FAILURES:
                            print("❌ Too many consecutive failures")
                            # Take screenshot before waiting for user
                            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                            screenshot_filename = f"stuck_debug_FAILURE_{timestamp}.png"
                            try:
                                self.driver.save_screenshot(
                                    screenshot_filename)
                                print(
                                    f"📸 Screenshot saved to {screenshot_filename} for debugging.")
                            except Exception as ss_err:
                                print(
                                    f"⚠️ Could not save screenshot: {ss_err}")
                            wait_for_user_input(
                                "MULTIPLE FAILURES: Please manually check the browser or screenshot.")
                            consecutive_failures = 0  # Reset after user intervention

                        # Attempt to recover by moving to the next story if processing failed
                        print_substep(
                            "Moving to next story after error (clicking right)...")
                        try:
                            story_container = self.driver.find_element(
                                By.XPATH, "//div[@role='dialog']")
                        except NoSuchElementException:
                            story_container = self.driver.find_element(
                                By.TAG_NAME, "body")
                        actions = webdriver.ActionChains(self.driver)
                        actions.move_to_element_with_offset(
                            story_container,
                            int(story_container.size["width"] * 0.90),
                            int(story_container.size["height"] * 0.50)
                        ).click().perform()
                        print("✔️ Clicked right side to advance after error.")
                        time.sleep(0.3)
                        self.robust_pause_story()
                        print("✔️ Paused story after error and advancing.")
                        random_sleep(0.5, 0.8)

                    print(
                        f"Progress: {story_count} stories, {successful_comments}/{TARGET_SUCCESSFUL_COMMENTS} successful")

                except InvalidSessionIdException as e:
                    print(f"❌ Browser closed during story processing: {e}")
                    break

                except Exception as e:
                    print(f"❌ Error during story processing: {e}")
                    consecutive_failures += 1

                    if consecutive_failures >= MAX_FAILURES:
                        wait_for_user_input(
                            "ERROR STATE: Please check browser and press Enter")
                        consecutive_failures = 0

                    # Try to continue by going to next story
                    try:
                        print_substep(
                            "Attempting to continue to next story...")
                        webdriver.ActionChains(self.driver).send_keys(
                            Keys.ARROW_DOWN).perform()
                        print("✔️ Advanced to next story using DOWN arrow")
                        time.sleep(0.3)
                        self.robust_pause_story()
                        print("✔️ Next story paused after error")
                        random_sleep(0.5, 0.8)
                    except Exception as nav_error:
                        print(f"❌ Failed to navigate after error: {nav_error}")
                        # Try SPACE key as fallback
                        try:
                            webdriver.ActionChains(self.driver).send_keys(
                                Keys.SPACE).perform()
                            print("✔️ Advanced using SPACE key after error")
                            time.sleep(0.3)
                            self.robust_pause_story()
                            print("✔️ Next story paused after error (SPACE method)")
                            random_sleep(0.5, 0.8)
                        except Exception as space_error:
                            print(
                                f"❌ All navigation methods failed: {space_error}")
                            wait_for_user_input(
                                "NAVIGATION ERROR: Please manually advance to next story")

            # If we reached the story count limit but haven't reached comment target, restart
            if successful_comments < TARGET_SUCCESSFUL_COMMENTS and story_count >= MAX_STORIES_BEFORE_RESTART:
                print(
                    f"Reached {MAX_STORIES_BEFORE_RESTART} stories but only {successful_comments}/{TARGET_SUCCESSFUL_COMMENTS} comments")
                print("Restarting from home to continue...")

                # Try to exit stories and navigate home
                try:
                    webdriver.ActionChains(self.driver).send_keys(
                        Keys.ESCAPE).perform()
                    random_sleep(2, 3)
                    self.navigate_home()

                    # Recursive call to continue processing with fresh start
                    remaining_target = TARGET_SUCCESSFUL_COMMENTS - successful_comments
                    print(
                        f"Continuing to collect {remaining_target} more comments...")
                    more_success = self.interact_with_stories()

                except Exception as restart_error:
                    print(f"Error during restart: {restart_error}")
                    wait_for_user_input(
                        "RESTART ERROR: Please manually navigate home")

        except InvalidSessionIdException as e:
            print(f"❌ Browser closed during story interaction: {e}")

        except Exception as e:
            print(f"❌ Error in story interaction: {e}")

        finally:
            print_step("STORY INTERACTION SUMMARY")
            print(
                f"""
Stories Statistics:
Stories processed: {story_count}
Successful comments: {successful_comments}/{TARGET_SUCCESSFUL_COMMENTS}
Success rate: {(successful_comments/story_count)*100 if story_count > 0 else 0:.2f}%
"""
            )
            return successful_comments

    def cleanup(self):
        """Clean up resources and delete processed usernames file."""
        try:
            # Stop pause monitoring if active
            if hasattr(self, 'pause_monitor'):
                self.pause_monitor.stop_monitoring()
                print("✔️ Pause monitoring stopped")

            # Stop story monitoring if active
            if hasattr(self, 'story_monitor'):
                self.story_monitor.stop_monitoring()
                print("✔️ Story monitoring stopped")

            # Delete processed usernames file instead of saving it
            filename = "processed_usernames.json"
            if os.path.exists(filename):
                os.remove(filename)
                print_step("DELETED PROCESSED USERNAMES FILE")
                logging.info(
                    "Deleted processed usernames file to reset tracking for next run")

            self.driver.quit()
            print_step("BROWSER CLOSED")

            # Clean up unique Chrome profile directory
            if hasattr(self, 'profile_dir') and os.path.exists(self.profile_dir):
                try:
                    import shutil
                    shutil.rmtree(self.profile_dir)
                    print(f"✔️ Cleaned up Chrome profile: {self.profile_dir}")
                except Exception as profile_cleanup_error:
                    print(
                        f"⚠️ Could not clean up profile directory: {profile_cleanup_error}")

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            logging.error(f"Error during cleanup: {e}")

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
                        logging.info(
                            f"Loaded {len(self.processed_usernames)} previously processed usernames")
        except Exception as e:
            print(f"⚠️ Error loading processed usernames: {e}")
            logging.error(f"Error loading processed usernames: {e}")
            # If there's an error, start with an empty set
            self.processed_usernames = set()

    def save_processed_usernames(self):
        """Save the set of processed usernames to a file."""
        filename = "processed_usernames.json"

        # Check if we've exceeded the maximum number of tracked usernames
        if len(self.processed_usernames) > self.max_tracked_usernames:
            print(
                f"⚠️ Tracked usernames exceeded limit of {self.max_tracked_usernames}. Clearing list.")
            logging.warning(
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
            logging.info(
                f"Saved {len(self.processed_usernames)} processed usernames to {filename}")
        except Exception as e:
            print(f"⚠️ Error saving processed usernames: {e}")
            logging.error(f"Error saving processed usernames: {e}")


def main():
    bot = None
    max_retries = 3

    try:
        print_step("STARTING INSTAGRAM STORY BOT")

        for attempt in range(max_retries):
            try:
                print(
                    f"Attempt {attempt + 1}/{max_retries} to initialize and run bot")
                bot = InstagramBot()

                login_success = bot.login()
                if not login_success:
                    print("❌ Failed to log in on this attempt.")
                    if attempt < max_retries - 1:
                        print(
                            f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                        if bot:
                            bot.cleanup()
                        bot = None
                        random_sleep(5, 10)
                        continue

                nav_success = bot.navigate_home(max_retries=2)
                if not nav_success:
                    print("❌ Failed to navigate home after multiple attempts")
                    if attempt < max_retries - 1:
                        print(
                            f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                        if bot:
                            bot.cleanup()
                        bot = None
                        random_sleep(5, 10)
                        continue

                # If we made it here, we're logged in and at home page
                bot.interact_with_stories()
                print_step("BOT COMPLETED SUCCESSFULLY")
                break  # Exit retry loop if successful

            except InvalidSessionIdException as e:
                print(f"❌ Browser session was closed: {e}")
                if attempt < max_retries - 1:
                    print(
                        f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                    if bot:
                        try:
                            bot.cleanup()
                        except:
                            pass
                    bot = None
                    random_sleep(5, 10)
                else:
                    print_step("EXCEEDED MAXIMUM RETRIES")

            except Exception as e:
                print(f"❌ Unexpected error during attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(
                        f"Retrying entire process (attempt {attempt + 2}/{max_retries})...")
                    if bot:
                        try:
                            bot.cleanup()
                        except:
                            pass
                    bot = None
                    random_sleep(5, 10)
                else:
                    print_step(f"UNEXPECTED ERROR: {e}")

    except KeyboardInterrupt:
        print_step("BOT INTERRUPTED BY USER")
    except Exception as e:
        print_step(f"CRITICAL ERROR: {e}")
    finally:
        if bot:
            try:
                bot.cleanup()
            except Exception as cleanup_error:
                print(f"❌ Error during cleanup: {cleanup_error}")


if __name__ == "__main__":
    main()
