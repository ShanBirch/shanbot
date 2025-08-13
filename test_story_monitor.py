#!/usr/bin/env python3
"""
Test script for the StoryMonitor system.
This script demonstrates how the monitoring system works and allows testing without running the full bot.
"""

import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai

# Import the StoryMonitor class from story1.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# You'll need to copy the StoryMonitor class here or import it
# For now, we'll create a simplified version for testing


class StoryMonitorTest:
    """Simplified version of StoryMonitor for testing"""

    def __init__(self, driver, model):
        self.driver = driver
        self.model = model
        self.monitoring_active = False
        self.monitoring_thread = None
        self.state_lock = threading.Lock()
        self.story_change_detected = False
        self.last_analysis_time = 0
        self.analysis_interval = 1.0  # Check every second for testing

        self.current_fingerprint = {
            'url': None,
            'title': None,
            'username': None,
            'timestamp': None
        }

    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.story_change_detected = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("🔍 Test monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("🔍 Test monitoring stopped")

    def _monitoring_loop(self):
        """Simplified monitoring loop"""
        while self.monitoring_active:
            try:
                current_time = time.time()
                if current_time - self.last_analysis_time >= self.analysis_interval:
                    self._analyze_current_state()
                    self.last_analysis_time = current_time
                time.sleep(0.2)
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(1)

    def _analyze_current_state(self):
        """Analyze current state"""
        try:
            new_fingerprint = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'timestamp': time.time()
            }

            with self.state_lock:
                if self.current_fingerprint['url'] is None:
                    self.current_fingerprint = new_fingerprint
                    print(
                        f"📍 Initial fingerprint: {new_fingerprint['title'][:50]}...")
                else:
                    if self._has_changed(self.current_fingerprint, new_fingerprint):
                        print(
                            f"🔄 Change detected: {self.current_fingerprint['title'][:30]} → {new_fingerprint['title'][:30]}")
                        self.story_change_detected = True
                        self.current_fingerprint = new_fingerprint
        except Exception as e:
            print(f"⚠️ Analysis error: {e}")

    def _has_changed(self, old, new):
        """Check if content has changed"""
        return (old['url'] != new['url'] or
                old['title'] != new['title'])

    def has_story_changed_recently(self):
        """Check if story changed recently"""
        with self.state_lock:
            if self.story_change_detected:
                self.story_change_detected = False
                return True
            return False

    def get_current_info(self):
        """Get current story info"""
        with self.state_lock:
            return self.current_fingerprint.copy()


def test_story_monitor():
    """Test the story monitoring system"""
    print("=" * 60)
    print("STORY MONITOR TEST")
    print("=" * 60)

    # Setup Chrome driver
    chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"

    try:
        service = Service(executable_path=chromedriver_path)
        chrome_options = Options()

        # Use persistent profile
        profile_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\chrome_profile"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument(
            '--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Setup Gemini (not really used in this test)
        gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Create monitor
        monitor = StoryMonitorTest(driver, model)

        print("\n1. Starting monitoring...")
        monitor.start_monitoring()

        print("\n2. Navigating to Instagram...")
        driver.get("https://www.instagram.com")
        time.sleep(3)

        print("\n3. Monitoring for 10 seconds...")
        print("   Try navigating to different pages to see change detection!")
        print("   Current info:")

        for i in range(10):
            current_info = monitor.get_current_info()
            if current_info['url']:
                print(f"   URL: {current_info['url'][:60]}...")
                print(f"   Title: {current_info['title'][:40]}...")

            if monitor.has_story_changed_recently():
                print("   🔄 CHANGE DETECTED!")

            time.sleep(1)

        print("\n4. Testing Instagram Stories (if available)...")
        try:
            # Try to navigate to stories
            driver.get("https://www.instagram.com/stories/")
            time.sleep(2)

            print("   Monitoring stories page for 5 seconds...")
            for i in range(5):
                if monitor.has_story_changed_recently():
                    print("   🔄 STORY CHANGE DETECTED!")
                time.sleep(1)

        except Exception as e:
            print(f"   Could not test stories: {e}")

        print("\n5. Stopping monitor...")
        monitor.stop_monitoring()

        print("\n✔️ Test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    test_story_monitor()
