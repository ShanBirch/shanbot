import time
import random
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# List of comments to choose from
COMMENTS = ["Awesome story! 👌", "Love this! 😊", "Keep it up! 💪", "🔥🔥🔥"]

def login_to_instagram(page, username, password, session_file="session.json"):
    """Logs into Instagram and saves the session."""
    try:
        if session_file and os.path.exists(session_file):
            print("Trying to use saved session...")
            # Session is loaded during context creation; no action needed here.
            page.goto("https://www.instagram.com/")
            page.wait_for_selector("svg[aria-label='Home']", timeout=10000)
            print("Session restored successfully!")
            return
    except Exception as e:
        print(f"Session restoration failed: {e}. Logging in manually...")

    print("Logging into Instagram...")
    page.goto("https://www.instagram.com/accounts/login/")
    try:
        page.wait_for_selector("input[name='username']", timeout=15000)
    except PlaywrightTimeoutError:
        print("Username input not found. Taking screenshot for debugging...")
        page.screenshot(path="login_page.png")
        raise

    # Fill in credentials
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.locator("button[type='submit']").click()

    # Wait for home icon to confirm successful login
    try:
        page.wait_for_selector("svg[aria-label='Home']", timeout=20000)
        print("Login successful!")
        # Save the session
        context = page.context
        context.storage_state(path=session_file)
        print(f"Session saved to {session_file}.")
    except PlaywrightTimeoutError:
        print("Login failed: Home icon not found. Possible incorrect credentials or login issues.")
        page.screenshot(path="login_failed.png")
        raise

def dismiss_popups(page):
    """Dismisses common Instagram pop-ups that may interfere with automation."""
    popups = [
        "button:has-text('Not Now')",        # Save Your Login Info
        "button:has-text('Turn Off')",       # Turn on Notifications
        "button:has-text('Accept All')",     # Accept Cookies
        "button:has-text('Cancel')",         # Any other potential cancel buttons
    ]
    for popup_selector in popups:
        try:
            page.wait_for_selector(popup_selector, timeout=5000)
            page.click(popup_selector)
            print(f"Dismissed popup: {popup_selector}")
            time.sleep(random.uniform(1, 2))  # Wait a bit after dismissing
        except PlaywrightTimeoutError:
            # Popup not found; continue
            pass

def locate_story_tray(page):
    """Locate and return the story tray element."""
    print("Navigating to the story tray...")
    page.goto("https://www.instagram.com/")

    try:
        page.wait_for_selector("svg[aria-label='Home']", timeout=15000)
        print("Home page loaded.")
    except PlaywrightTimeoutError:
        print("Could not confirm home page load. Taking screenshot for debugging...")
        page.screenshot(path="home_page_load_failed.png")
        return None

    # Dismiss any pop-ups that might appear
    dismiss_popups(page)

    # List of potential selectors
    possible_selectors = [
        "section[aria-labelledby='Stories'] div[role='button'] img[decoding='auto']",
        "//section[@aria-labelledby='Stories']//div[@role='button']//img[@decoding='auto']",
        "div[aria-label='Stories'] div[role='button'] img",
        "div[role='button'][aria-label*='Story'] img",
        "div[role='button'][data-testid='story'] img",  # Example if data-testid is used
    ]

    for selector in possible_selectors:
        try:
            print(f"Trying selector: {selector}")
            if selector.startswith("//"):
                # XPath selector
                story_trays = page.query_selector_all(selector, strict=False, xpath=True)
            else:
                # CSS selector
                story_trays = page.query_selector_all(selector)

            print(f"Found {len(story_trays)} elements with selector {selector}")
            if story_trays:
                story_trays[0].click()
                print("Clicked on the first story tray.")
                return True
        except Exception as e:
            print(f"Selector {selector} failed: {e}")
            continue

    # If none of the selectors worked
    print("No story trays found with the provided selectors. Taking screenshot for debugging...")
    page.screenshot(path="story_tray_not_found.png")
    print("Printing page HTML for manual inspection:")
    with open("page_content.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    return None

def comment_on_other_stories(page):
    """Navigate to other users' stories and comment."""
    story_tray_found = locate_story_tray(page)
    if not story_tray_found:
        print("No story tray located. Exiting...")
        return

    commented_users = set()

    while True:
        try:
            time.sleep(random.uniform(2, 4))  # Mimic human behavior

            # Dismiss any pop-ups that might appear during story viewing
            dismiss_popups(page)

            user_element = page.query_selector("header [role='button']")
            if not user_element:
                print("User element not found. Taking screenshot for debugging...")
                page.screenshot(path="user_element_not_found.png")
                print("Exiting...")
                break
            user = user_element.text_content().strip()
            print(f"Viewing story from user: {user}")

            if user in commented_users:
                print(f"Already commented on {user}. Skipping...")
            else:
                comment_field = page.query_selector("textarea")
                if comment_field:
                    comment = random.choice(COMMENTS)
                    comment_field.fill(comment)
                    page.locator("button[type='submit']").click()
                    print(f"Commented on {user}'s story: {comment}")
                    commented_users.add(user)
                else:
                    print(f"Could not find comment field for {user}'s story. Taking screenshot...")
                    page.screenshot(path=f"comment_field_missing_{user}.png")
                    print("Skipping...")

            # Attempt to click the 'Next' button to move to the next story
            next_button = page.query_selector("button[aria-label='Next']")
            if next_button:
                next_button.click()
                print("Moved to the next story.")
            else:
                print("No 'Next' button found. Assuming end of stories.")
                break
        except Exception as e:
            print(f"An error occurred while processing a story: {e}")
            page.screenshot(path="error_processing_story.png")
            break

def main():
    # **Important:** Replace the placeholders below with your actual credentials
    INSTAGRAM_USERNAME = "your_username"  # Replace with your username
    INSTAGRAM_PASSWORD = "your_password"  # Replace with your password

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)  # slow_mo added for easier observation
        try:
            # Check if session file exists
            session_file = "session.json"  # Path to your session file
            if os.path.exists(session_file):
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/91.0.4472.124 Safari/537.36",
                    storage_state=session_file
                )
                print("Loaded browser context from session file.")
            else:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/91.0.4472.124 Safari/537.36"
                )
                print("Created new browser context.")

            page = context.new_page()

            login_to_instagram(page, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, session_file=session_file)
            comment_on_other_stories(page)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
