#!/usr/bin/env python3
"""
Instagram Inbox Checker - Advanced Version
Checks for unread Instagram messages using Selenium automation.
Integrates with existing Instagram bot infrastructure.
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class InstagramInboxChecker:
    """Check Instagram inbox for unread messages"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.chrome_driver_path = self._find_chromedriver()
        
    def _find_chromedriver(self):
        """Find ChromeDriver path"""
        paths = [
            r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
            "chromedriver",
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver"
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1200,800")
        
        # Load cookies if available
        if os.path.exists("scripts/instagram_cookies.json"):
            chrome_options.add_argument("--user-data-dir=./chrome-profile")
        
        try:
            if self.chrome_driver_path and self.chrome_driver_path.endswith('.exe'):
                service = webdriver.chrome.service.Service(executable_path=self.chrome_driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute stealth script
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
            self.driver.execute_script(stealth_script)
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Chrome driver: {e}")
            return False
    
    def load_cookies(self):
        """Load Instagram cookies if available"""
        cookie_file = "scripts/instagram_cookies.json"
        
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                
                # Navigate to Instagram first
                self.driver.get("https://www.instagram.com/")
                time.sleep(2)
                
                # Add cookies
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                
                return True
            except Exception as e:
                print(f"⚠️  Could not load cookies: {e}")
                return False
        
        return False
    
    def manual_login(self):
        """Wait for manual login"""
        print("\n👤 MANUAL LOGIN REQUIRED")
        print("-" * 60)
        print("1. Please log in to Instagram in the browser window")
        print("2. Complete any 2FA if required")
        print("3. Press ENTER here after successful login...")
        input()
        
        # Verify login
        current_url = self.driver.current_url.lower()
        if "login" not in current_url:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login verification failed")
            return False
    
    def check_inbox(self):
        """Check inbox for unread messages"""
        
        print("\n🔍 Navigating to Instagram Direct Messages...")
        self.driver.get("https://www.instagram.com/direct/inbox/")
        time.sleep(3)
        
        # Check if we need to login
        if "login" in self.driver.current_url.lower():
            if not self.manual_login():
                return None
            
            # Navigate to inbox again
            self.driver.get("https://www.instagram.com/direct/inbox/")
            time.sleep(3)
        
        print("🔍 Scanning for unread messages...")
        
        results = {
            'unread_count': 0,
            'unread_conversations': [],
            'message_requests': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Wait for inbox to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(2)
            
            # Method 1: Look for notification badge
            try:
                notification_selectors = [
                    "[aria-label*='unread']",
                    "[aria-label*='new message']",
                    "span[class*='badge']",
                    "[data-count]"
                ]
                
                for selector in notification_selectors:
                    try:
                        badge = self.driver.find_element(By.CSS_SELECTOR, selector)
                        badge_text = badge.text or badge.get_attribute('aria-label') or badge.get_attribute('data-count')
                        if badge_text:
                            print(f"🔔 Notification badge found: {badge_text}")
                            try:
                                results['unread_count'] = int(''.join(filter(str.isdigit, badge_text)))
                            except:
                                pass
                            break
                    except:
                        continue
            except:
                pass
            
            # Method 2: Look for unread conversation threads
            try:
                # Instagram thread selectors (may need updating as Instagram changes)
                thread_selectors = [
                    "[role='listitem']",
                    "div[class*='thread']",
                    "a[role='link']"
                ]
                
                for selector in thread_selectors:
                    try:
                        threads = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if threads:
                            print(f"📋 Found {len(threads)} conversation threads")
                            
                            # Check each thread for unread indicators
                            for thread in threads[:20]:  # Limit to first 20
                                try:
                                    # Check if thread has bold text (unread indicator)
                                    html = thread.get_attribute('innerHTML')
                                    
                                    # Look for common unread indicators
                                    is_unread = any([
                                        'font-weight: 600' in html,
                                        'font-weight: 700' in html,
                                        'font-weight:600' in html,
                                        'font-weight:700' in html,
                                        'background-color: rgb(0, 149, 246)' in html,  # Instagram blue
                                    ])
                                    
                                    if is_unread:
                                        try:
                                            # Try to extract username/conversation name
                                            text_elements = thread.find_elements(By.CSS_SELECTOR, "span, div")
                                            conversation_name = None
                                            
                                            for elem in text_elements:
                                                text = elem.text.strip()
                                                if text and len(text) > 0 and len(text) < 50:
                                                    conversation_name = text
                                                    break
                                            
                                            if conversation_name:
                                                results['unread_conversations'].append({
                                                    'name': conversation_name,
                                                    'detected_at': datetime.now().isoformat()
                                                })
                                        except:
                                            results['unread_conversations'].append({
                                                'name': '(Unknown)',
                                                'detected_at': datetime.now().isoformat()
                                            })
                                except:
                                    continue
                            
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"⚠️  Could not scan threads: {e}")
            
            # Method 3: Check for message requests
            try:
                request_selectors = [
                    "a[href*='requests']",
                    "[aria-label*='request']",
                    "div:contains('Requests')"
                ]
                
                for selector in request_selectors:
                    try:
                        request_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        request_text = request_element.text or request_element.get_attribute('aria-label')
                        
                        if request_text and any(char.isdigit() for char in request_text):
                            try:
                                results['message_requests'] = int(''.join(filter(str.isdigit, request_text)))
                                print(f"📨 Message requests: {results['message_requests']}")
                            except:
                                pass
                        break
                    except:
                        continue
            except:
                pass
            
            # Update unread count based on conversations found
            if len(results['unread_conversations']) > results['unread_count']:
                results['unread_count'] = len(results['unread_conversations'])
            
        except Exception as e:
            print(f"❌ Error scanning inbox: {e}")
        
        return results
    
    def display_results(self, results):
        """Display results in a formatted way"""
        
        print("\n" + "=" * 60)
        print("📬 INBOX CHECK RESULTS")
        print("=" * 60)
        print()
        
        if results['unread_count'] == 0 and not results['unread_conversations']:
            print("✅ No unread messages found!")
        else:
            print(f"📊 Total unread: {results['unread_count']}")
            
            if results['unread_conversations']:
                print(f"\n💬 Unread conversations ({len(results['unread_conversations'])}):")
                print("-" * 60)
                for i, conv in enumerate(results['unread_conversations'], 1):
                    print(f"  {i}. {conv['name']}")
        
        if results['message_requests'] > 0:
            print(f"\n📨 Message requests: {results['message_requests']}")
            print("   (Check your 'Requests' folder)")
        
        print("\n" + "=" * 60)
        print(f"🕐 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def save_results(self, results, filename='instagram_inbox_check.json'):
        """Save results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
    
    def run(self, save_to_file=True):
        """Run the complete inbox check"""
        
        print("=" * 60)
        print("   🔍 INSTAGRAM INBOX CHECKER")
        print("=" * 60)
        
        if not self.chrome_driver_path:
            print("\n❌ ChromeDriver not found!")
            print("Please install ChromeDriver or use manual check method")
            return None
        
        print(f"\n🔧 Using ChromeDriver: {self.chrome_driver_path}")
        
        if not self.setup_driver():
            return None
        
        try:
            # Try to load cookies
            self.load_cookies()
            
            # Check inbox
            results = self.check_inbox()
            
            if results:
                self.display_results(results)
                
                if save_to_file:
                    self.save_results(results)
            
            # Keep browser open for review
            print("\n📝 Browser will remain open for manual review...")
            print("Press ENTER to close and exit...")
            input()
            
            return results
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Instagram inbox for unread messages")
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save results to file')
    
    args = parser.parse_args()
    
    checker = InstagramInboxChecker(headless=args.headless)
    results = checker.run(save_to_file=not args.no_save)
    
    if results:
        print("\n✅ Inbox check complete!")
    else:
        print("\n⚠️  Inbox check completed with issues")


if __name__ == "__main__":
    main()
