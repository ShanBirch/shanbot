"""
🧈 BUTTER SMOOTH CHROME CONFIGURATION
Optimized Chrome settings for Instagram automation scripts
Author: AI Assistant | Date: January 2025
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import psutil
import os
import time
import logging


class OptimizedChromeManager:
    """Manages Chrome instances with memory optimization and crash prevention"""

    def __init__(self, profile_path=None):
        self.profile_path = profile_path
        self.driver = None
        self.accounts_processed = 0
        self.max_accounts_before_restart = 50  # Restart browser every 50 accounts

    def get_optimized_chrome_options(self):
        """Returns optimized Chrome options for Instagram automation"""
        options = Options()

        # PERFORMANCE OPTIMIZATIONS
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=TranslateUI")

        # MEMORY OPTIMIZATIONS
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=2048")  # Limit to 2GB
        options.add_argument("--js-flags=--max-old-space-size=2048")

        # SPEED OPTIMIZATIONS (Load faster, use less bandwidth)
        options.add_argument("--disable-images")  # Don't load images
        # Disable JS when possible
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-css3d")
        options.add_argument("--disable-web-security")

        # CRASH PREVENTION
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-networking")

        # INSTAGRAM-SPECIFIC OPTIMIZATIONS
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # PROFILE SETTINGS
        if self.profile_path:
            options.add_argument(f"--user-data-dir={self.profile_path}")

        # LOGGING (Reduce verbose output)
        options.add_argument("--log-level=3")  # Only fatal errors
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def check_memory_usage(self):
        """Check system memory and return True if safe to continue"""
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            logging.warning(
                f"High memory usage: {memory.percent}%. Consider restarting browser.")
            return False
        return True

    def create_driver(self):
        """Create a new Chrome driver with optimized settings"""
        if not self.check_memory_usage():
            self.cleanup_browser()
            time.sleep(5)  # Wait for cleanup

        options = self.get_optimized_chrome_options()

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)  # Don't wait forever
            self.driver.implicitly_wait(10)
            logging.info("✅ Optimized Chrome driver created successfully")
            return self.driver
        except Exception as e:
            logging.error(f"❌ Failed to create Chrome driver: {e}")
            return None

    def restart_browser_if_needed(self):
        """Restart browser if too many accounts processed or memory high"""
        self.accounts_processed += 1

        if (self.accounts_processed >= self.max_accounts_before_restart or
                not self.check_memory_usage()):

            logging.info(
                f"🔄 Restarting browser after {self.accounts_processed} accounts")
            self.cleanup_browser()
            time.sleep(3)
            self.create_driver()
            self.accounts_processed = 0
            return True
        return False

    def cleanup_browser(self):
        """Properly cleanup browser and free memory"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("✅ Browser cleaned up successfully")
            except Exception as e:
                logging.warning(f"⚠️ Browser cleanup warning: {e}")
            finally:
                self.driver = None

        # Kill any remaining Chrome processes
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'chrome' in proc.info['name'].lower():
                    if proc.info['pid'] != os.getpid():  # Don't kill ourselves
                        proc.terminate()
        except Exception as e:
            logging.warning(f"⚠️ Process cleanup warning: {e}")

# EASY INTEGRATION FOR EXISTING SCRIPTS


def get_butter_smooth_driver(profile_path=None):
    """Quick function to get optimized driver for existing scripts"""
    manager = OptimizedChromeManager(profile_path)
    return manager.create_driver()


def add_memory_monitoring(func):
    """Decorator to add memory monitoring to any function"""
    def wrapper(*args, **kwargs):
        memory_before = psutil.virtual_memory().percent
        result = func(*args, **kwargs)
        memory_after = psutil.virtual_memory().percent

        if memory_after > 85:
            logging.warning(
                f"🧠 Memory high after {func.__name__}: {memory_after}%")

        return result
    return wrapper

# BATCH PROCESSING OPTIMIZATION


class BatchProcessor:
    """Process leads in smaller batches to prevent crashes"""

    def __init__(self, batch_size=25):
        self.batch_size = batch_size
        self.chrome_manager = OptimizedChromeManager()

    def process_leads_in_batches(self, leads_list, process_function):
        """Process leads in optimized batches"""
        total_leads = len(leads_list)
        processed = 0

        for i in range(0, total_leads, self.batch_size):
            batch = leads_list[i:i + self.batch_size]

            logging.info(
                f"🔥 Processing batch {i//self.batch_size + 1}: {len(batch)} leads")

            # Create fresh driver for each batch
            driver = self.chrome_manager.create_driver()
            if not driver:
                logging.error("❌ Failed to create driver for batch")
                continue

            try:
                for lead in batch:
                    process_function(driver, lead)
                    processed += 1

                    # Check memory every 10 leads
                    if processed % 10 == 0:
                        if not self.chrome_manager.check_memory_usage():
                            logging.warning("🧠 Memory high, taking break...")
                            time.sleep(10)

            except Exception as e:
                logging.error(f"❌ Batch processing error: {e}")
            finally:
                self.chrome_manager.cleanup_browser()

            # Break between batches
            if i + self.batch_size < total_leads:
                logging.info("⏸️ Taking 30-second break between batches...")
                time.sleep(30)

        logging.info(
            f"🎉 Completed processing {processed}/{total_leads} leads!")


if __name__ == "__main__":
    # Test the optimized Chrome setup
    print("🧈 Testing Butter Smooth Chrome Configuration...")

    manager = OptimizedChromeManager()
    driver = manager.create_driver()

    if driver:
        print("✅ Optimized Chrome driver created successfully!")
        driver.get("https://www.instagram.com")
        print("✅ Instagram loaded successfully!")
        manager.cleanup_browser()
        print("✅ Cleanup completed!")
    else:
        print("❌ Failed to create driver")
