#!/usr/bin/env python3
"""
Check for Unread Instagram Messages
This script checks your Instagram inbox for unread messages using multiple methods:
1. Local database (if available)
2. Instagram web interface via Selenium (requires login)
3. Manual check with guidance

Usage:
    python check_unread_instagram_messages.py [--method database|selenium|manual]
"""

import sqlite3
import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def find_database():
    """Find the analytics database"""
    possible_paths = [
        'app/analytics_data_good.sqlite',
        r'C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite',
        'analytics_data_good.sqlite',
        '../app/analytics_data_good.sqlite',
        '/workspace/app/analytics_data_good.sqlite',
    ]
    
    for db_path in possible_paths:
        if os.path.exists(db_path):
            return db_path
    
    return None


def check_unread_messages():
    """Check for unread Instagram messages"""
    
    print("🔍 Checking for unread Instagram messages...")
    print("=" * 60)
    
    # Find database
    db_path = find_database()
    
    if not db_path:
        print("❌ Could not find database file.")
        print("\nSearched in:")
        print("  - app/analytics_data_good.sqlite")
        print("  - C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite")
        print("\nPlease ensure the database exists or update the path in this script.")
        return
    
    print(f"📂 Using database: {db_path}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='messages'
        """)
        
        if not cursor.fetchone():
            print("⚠️  'messages' table not found in database.")
            print("\nAvailable tables:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
            conn.close()
            return
        
        # Query for unread messages or messages needing responses
        # Try different possible schemas
        queries = [
            # Query 1: Messages with response_needed flag
            """
                SELECT 
                    username,
                    message_text,
                    created_at,
                    conversation_id
                FROM messages 
                WHERE response_needed = 1 
                   OR needs_response = 1
                   OR status = 'unread'
                ORDER BY created_at DESC
                LIMIT 20
            """,
            # Query 2: Most recent messages from others
            """
                SELECT 
                    username,
                    message_text,
                    created_at,
                    conversation_id
                FROM messages 
                WHERE is_from_me = 0 
                   OR sender != 'bot'
                ORDER BY created_at DESC
                LIMIT 20
            """,
            # Query 3: Basic query
            """
                SELECT 
                    username,
                    message_text,
                    created_at
                FROM messages 
                ORDER BY created_at DESC
                LIMIT 20
            """
        ]
        
        messages = []
        for i, query in enumerate(queries):
            try:
                cursor.execute(query)
                messages = cursor.fetchall()
                if messages:
                    print(f"✅ Found {len(messages)} messages using query method {i+1}\n")
                    break
            except sqlite3.OperationalError as e:
                if i == len(queries) - 1:
                    # Last query failed too
                    print(f"❌ Error querying messages: {e}")
                    # Show table schema
                    cursor.execute("PRAGMA table_info(messages)")
                    columns = cursor.fetchall()
                    print("\nMessages table columns:")
                    for col in columns:
                        print(f"  - {col[1]} ({col[2]})")
                continue
        
        if not messages:
            print("📭 No unread messages found!")
            conn.close()
            return
        
        # Display messages
        print("📬 UNREAD MESSAGES:")
        print("-" * 60)
        
        for idx, msg in enumerate(messages, 1):
            username = msg[0] if len(msg) > 0 else "Unknown"
            message_text = msg[1] if len(msg) > 1 else "No text"
            created_at = msg[2] if len(msg) > 2 else "Unknown time"
            
            # Truncate long messages
            if message_text and len(message_text) > 100:
                message_text = message_text[:100] + "..."
            
            print(f"\n{idx}. @{username}")
            print(f"   Time: {created_at}")
            print(f"   Message: {message_text}")
        
        print("\n" + "=" * 60)
        print(f"📊 Total unread messages: {len(messages)}")
        
        # Check for conversations table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='conversations'
        """)
        
        if cursor.fetchone():
            # Count active conversations
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT username) 
                    FROM conversations 
                    WHERE last_message_at >= datetime('now', '-7 days')
                """)
                active_convos = cursor.fetchone()[0]
                print(f"💬 Active conversations (last 7 days): {active_convos}")
            except:
                pass
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def check_inbox_summary():
    """Show a summary of inbox status (compatible with inbox.md workflow)"""
    
    print("\n" + "=" * 60)
    print("📊 INBOX SUMMARY")
    print("=" * 60)
    
    db_path = find_database()
    
    if not db_path:
        print("❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Try to get various statistics
        stats = {}
        
        # Count of messages by type
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN needs_response = 1 THEN 1 END) as needs_response
                FROM messages
                WHERE created_at >= datetime('now', '-7 days')
            """)
            row = cursor.fetchone()
            if row:
                stats['total_recent'] = row[0]
                stats['needs_response'] = row[1]
        except:
            pass
        
        # Display stats
        if stats:
            print("\n📈 Statistics (last 7 days):")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not generate full summary: {e}")


def check_via_selenium():
    """Check for unread messages using Instagram web interface"""
    
    print("\n🌐 Checking Instagram via Web Interface...")
    print("=" * 60)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("❌ Selenium not installed.")
        print("Install with: pip install selenium")
        print("\nAlternatively, run with --method manual for guided manual check")
        return
    
    # Check for ChromeDriver
    chrome_driver_paths = [
        r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe",
        "chromedriver",
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver"
    ]
    
    chrome_driver_path = None
    for path in chrome_driver_paths:
        if os.path.exists(path):
            chrome_driver_path = path
            break
    
    if not chrome_driver_path:
        print("❌ ChromeDriver not found.")
        print("Download from: https://chromedriver.chromium.org/")
        print("\nAlternatively, run with --method manual for guided manual check")
        return
    
    # Setup browser
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        if chrome_driver_path.endswith('.exe'):
            service = webdriver.chrome.service.Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        print("🌐 Opening Instagram...")
        driver.get("https://www.instagram.com/direct/inbox/")
        
        print("\n👤 LOGIN REQUIRED:")
        print("1. Log in to your Instagram account in the browser window")
        print("2. Navigate to your Direct Messages if not already there")
        print("3. Press ENTER here to scan for unread messages...")
        input()
        
        # Try to find unread message indicators
        print("\n🔍 Scanning for unread messages...")
        
        try:
            # Look for unread message indicators (Instagram uses different selectors)
            # These are common patterns but may need updating based on Instagram's current UI
            
            unread_threads = driver.find_elements(By.CSS_SELECTOR, 
                "[role='listitem'] [data-is-read='false'], .x1iyjqo2 .x1n2onr6, [aria-label*='unread']")
            
            if not unread_threads:
                # Try alternative selector
                all_threads = driver.find_elements(By.CSS_SELECTOR, "[role='listitem']")
                # Check for bold text or notification badges
                unread_threads = [t for t in all_threads if 'font-weight: 600' in t.get_attribute('innerHTML')]
            
            print(f"\n📬 Found {len(unread_threads)} unread conversation(s)!")
            
            if unread_threads:
                print("\nUnread conversations:")
                for i, thread in enumerate(unread_threads[:10], 1):
                    try:
                        username = thread.find_element(By.CSS_SELECTOR, "span, div").text
                        print(f"  {i}. {username}")
                    except:
                        print(f"  {i}. (Unable to extract username)")
            
            # Also try to get the notification count
            try:
                notification_badge = driver.find_element(By.CSS_SELECTOR, 
                    "[aria-label*='notification'], .x1iyjqo2, [data-count]")
                count_text = notification_badge.text or notification_badge.get_attribute('aria-label')
                if count_text:
                    print(f"\n🔔 Notification count: {count_text}")
            except:
                pass
                
        except Exception as e:
            print(f"⚠️  Could not automatically detect unread messages: {e}")
            print("\n📝 Please manually count your unread messages in the browser window.")
            print("The script will wait for you to review...")
            input("Press ENTER when done reviewing...")
        
        print("\nPress ENTER to close the browser...")
        input()
        driver.quit()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def manual_check_guide():
    """Provide step-by-step guidance for manually checking Instagram DMs"""
    
    print("\n📱 Manual Instagram DM Check Guide")
    print("=" * 60)
    print()
    print("Follow these steps to check for unread Instagram messages:")
    print()
    print("METHOD 1: Instagram Mobile App")
    print("-" * 60)
    print("1. Open the Instagram app on your phone")
    print("2. Tap the Messenger icon (top right)")
    print("3. Look for:")
    print("   • Blue dots next to usernames (unread messages)")
    print("   • Numbers in notification badges")
    print("   • Bold usernames (new messages)")
    print()
    print("METHOD 2: Instagram Web")
    print("-" * 60)
    print("1. Go to: https://www.instagram.com/direct/inbox/")
    print("2. Log in if needed")
    print("3. Check the left sidebar for:")
    print("   • Bolded conversation names")
    print("   • Notification counts")
    print("   • Highlighted/unread indicators")
    print()
    print("METHOD 3: Instagram Desktop App")
    print("-" * 60)
    print("1. Open Instagram Desktop app (if installed)")
    print("2. Click the Messages icon")
    print("3. Review unread message indicators")
    print()
    print("📊 WHAT TO LOOK FOR:")
    print("-" * 60)
    print("• Message requests (Primary vs. General tabs)")
    print("• Hidden/filtered messages")
    print("• Group conversations")
    print("• Pending message requests from non-followers")
    print()
    print("💡 PRO TIP:")
    print("Check both 'Primary' and 'General' inboxes!")
    print("Message requests often appear in the 'Requests' folder.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Instagram for unread messages",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--method',
        choices=['database', 'selenium', 'manual', 'all'],
        default='all',
        help='Method to use for checking messages (default: all)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   📬 INSTAGRAM UNREAD MESSAGE CHECKER")
    print("=" * 60)
    print()
    
    if args.method in ['database', 'all']:
        check_unread_messages()
        check_inbox_summary()
    
    if args.method in ['selenium', 'all']:
        print("\n" + "=" * 60)
        check_via_selenium()
    
    if args.method in ['manual', 'all']:
        print("\n" + "=" * 60)
        manual_check_guide()
    
    print("\n" + "=" * 60)
    print("💡 ADDITIONAL OPTIONS:")
    print("=" * 60)
    print("\nFor text-based inbox management, use the inbox.md workflow:")
    print('   • "How many messages are in my inbox?"')
    print('   • "Show me message #1"')
    print('   • "Generate response for @username"')
    print()
    print("Run with --help to see all options")
    print()
