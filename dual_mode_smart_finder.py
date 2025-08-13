#!/usr/bin/env python3
# Dual Mode Smart Lead Finder - Run Both Modes Simultaneously
# Launches both online and local searches in parallel with different accounts

import argparse
import sys
import os
import time
import datetime
import json
import random
import pickle
import re
import traceback
import base64
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# Gemini AI imports
import google.generativeai as genai
import google.api_core.exceptions

# Import the SmartLeadFinder class
from smart_lead_finder import SmartLeadFinder, CHROMEDRIVER_PATH, SQLITE_DB_PATH, PASSWORD

# Lock for thread-safe console output
print_lock = threading.Lock()


def thread_safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)


def get_chrome_options(mode, headless=True):
    """Get Chrome options specific to each mode"""
    chrome_options = Options()

    # Always run in headless mode for efficiency
    if headless:
        chrome_options.add_argument("--headless")

    # Common arguments for stability
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    # Different user data directories for each mode to avoid conflicts
    base_profile_dir = os.path.join(
        os.path.dirname(__file__), f"chrome_profile_{mode}")
    chrome_options.add_argument(f"--user-data-dir={base_profile_dir}")

    # Different ports for remote debugging to avoid conflicts
    debug_port = 9222 if mode == 'online' else 9223
    chrome_options.add_argument(f"--remote-debugging-port={debug_port}")

    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    return chrome_options


class DualModeSmartLeadFinder(SmartLeadFinder):
    """Extended SmartLeadFinder with dual-mode support"""

    def __init__(self, mode='online'):
        super().__init__(mode)
        self.thread_id = threading.get_ident()

    def setup_driver(self):
        """Initialize Chrome driver with mode-specific options"""
        try:
            # Use mode-specific Chrome options
            chrome_options = get_chrome_options(self.mode, headless=True)

            service = webdriver.chrome.service.Service(
                executable_path=CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(
                service=service, options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            thread_safe_print(
                f"✅ [{self.mode.upper()}] Chrome driver initialized in headless mode (Thread {self.thread_id})")
            return True
        except Exception as e:
            thread_safe_print(
                f"❌ [{self.mode.upper()}] Failed to setup driver: {e}")
            return False

    def log_run(self, status, error_message=None):
        """Log run status with mode prefix"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            current_time = datetime.datetime.now().isoformat()

            if status == 'started':
                cursor.execute("""
                    INSERT INTO lead_generation_runs
                    (run_type, run_timestamp, status, leads_found, leads_followed, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f'find_leads_{self.mode}', current_time, status, 0, 0, error_message))
                self.run_id = cursor.lastrowid
                thread_safe_print(
                    f"📈 [{self.mode.upper()}] Started new session (ID: {self.run_id})")
            elif self.run_id:
                cursor.execute("""
                    UPDATE lead_generation_runs
                    SET status = ?, leads_found = ?, leads_followed = ?, error_message = ?
                    WHERE id = ?
                """, (status, self.leads_found, self.leads_followed, error_message, self.run_id))
                thread_safe_print(
                    f"📈 [{self.mode.upper()}] Session {self.run_id}: {status} - Found: {self.leads_found}, Followed: {self.leads_followed}")

            conn.commit()
        finally:
            conn.close()

    def run_lead_finding_session(self):
        """Main function with thread-safe output"""
        thread_safe_print(
            f"🚀 [{self.mode.upper()}] Starting Smart Lead Finder...")

        # Create tables if needed
        self.create_tables_if_needed()

        # Log session start
        self.log_run('started')

        try:
            # Check daily limit
            daily_follows = self.get_daily_follows_count()
            remaining = 75 - daily_follows  # DAILY_FOLLOW_LIMIT = 75

            if remaining <= 0:
                thread_safe_print(
                    f"⏳ [{self.mode.upper()}] Daily follow limit already reached ({daily_follows}/75)")
                self.log_run('completed')
                return

            thread_safe_print(
                f"📊 [{self.mode.upper()}] Daily follows: {daily_follows}/75 (can follow {remaining} more)")

            # Setup browser
            if not self.setup_driver():
                self.log_run('failed', 'Failed to setup browser')
                return

            # Login
            if not self.login_to_instagram():
                self.log_run('failed', 'Failed to login to Instagram')
                return

            # Phase 1: Mine followers from influencers
            thread_safe_print(
                f"\n🎯 [{self.mode.upper()}] PHASE 1: Mining followers from target accounts...")
            leads_from_followers = self.mine_followers_from_influencers()
            thread_safe_print(
                f"✅ [{self.mode.upper()}] Found {leads_from_followers} leads from followers")

            # Phase 2: Search hashtags for leads (if still under daily limit)
            if self.get_daily_follows_count() < 75:
                thread_safe_print(
                    f"\n🔍 [{self.mode.upper()}] PHASE 2: Searching hashtags for leads...")

                # Import hashtags based on mode
                if self.mode == 'local':
                    from smart_lead_finder import LOCAL_HASHTAGS as target_hashtags
                    thread_safe_print(
                        f"🏠 [{self.mode.upper()}] Using local Bayside hashtags...")
                else:
                    from smart_lead_finder import ONLINE_HASHTAGS as target_hashtags
                    thread_safe_print(
                        f"🌱 [{self.mode.upper()}] Using vegan/plant-based hashtags...")

                for hashtag in target_hashtags:
                    if self.get_daily_follows_count() >= 75:
                        break

                    self.search_hashtag_for_leads(hashtag, max_to_check=10)

                    # Small delay between hashtags
                    time.sleep(random.uniform(10, 20))

            thread_safe_print(
                f"\n🎉 [{self.mode.upper()}] Lead finding session complete!")
            thread_safe_print(
                f"📊 [{self.mode.upper()}] Final stats: Found {self.leads_found} leads, Followed {self.leads_followed} users")

            self.log_run('completed')

        except Exception as e:
            thread_safe_print(f"❌ [{self.mode.upper()}] Critical error: {e}")
            traceback.print_exc()
            self.log_run('failed', str(e))

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    thread_safe_print(
                        f"✅ [{self.mode.upper()}] Browser closed")
                except:
                    pass


def run_mode(mode):
    """Run a single mode in a thread"""
    try:
        thread_safe_print(
            f"\n🔥 Starting {mode.upper()} mode in thread {threading.get_ident()}")
        finder = DualModeSmartLeadFinder(mode=mode)
        finder.run_lead_finding_session()
        thread_safe_print(f"✅ {mode.upper()} mode completed successfully")
        return True
    except Exception as e:
        thread_safe_print(f"❌ {mode.upper()} mode failed: {e}")
        traceback.print_exc()
        return False


def run_dual_mode():
    """Run both online and local modes simultaneously"""
    print("🚀 DUAL-MODE SMART LEAD FINDER")
    print("=" * 50)
    print("🌱 ONLINE MODE: cocos_connected → Vegan/plant-based clients")
    print("🏠 LOCAL MODE: cocos_pt_studio → Bayside gym clients (women 30+)")
    print("🔄 Both running in HEADLESS mode (no browser windows)")
    print("📊 Daily limit: 75 follows per account (150 total)")
    print("=" * 50)

    # Create thread pool for concurrent execution
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="LeadFinder") as executor:
        # Submit both tasks
        online_future = executor.submit(run_mode, 'online')
        local_future = executor.submit(run_mode, 'local')

        # Wait for completion and collect results
        online_success = online_future.result()
        local_success = local_future.result()

    print("\n" + "=" * 50)
    print("🏁 DUAL-MODE EXECUTION COMPLETE")
    print(f"🌱 Online Mode: {'✅ SUCCESS' if online_success else '❌ FAILED'}")
    print(f"🏠 Local Mode: {'✅ SUCCESS' if local_success else '❌ FAILED'}")
    print("=" * 50)

    return online_success and local_success


def run_single_mode(mode):
    """Run a single mode"""
    print(f"🚀 SINGLE-MODE SMART LEAD FINDER - {mode.upper()}")
    print("=" * 50)
    if mode == 'online':
        print("🌱 ONLINE MODE: cocos_connected → Vegan/plant-based clients")
    else:
        print("🏠 LOCAL MODE: cocos_pt_studio → Bayside gym clients (women 30+)")
    print("🔄 Running in HEADLESS mode (no browser windows)")
    print("📊 Daily limit: 75 follows")
    print("=" * 50)

    success = run_mode(mode)

    print("\n" + "=" * 50)
    print(f"🏁 {mode.upper()} MODE EXECUTION COMPLETE")
    print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 50)

    return success


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Dual-Mode Smart Lead Finder - Run both accounts simultaneously'
    )
    parser.add_argument('--mode', type=str, choices=['online', 'local', 'dual'],
                        default='dual',
                        help='Mode: "online", "local", or "dual" for both simultaneously')

    args = parser.parse_args()

    if args.mode == 'dual':
        success = run_dual_mode()
    else:
        success = run_single_mode(args.mode)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
