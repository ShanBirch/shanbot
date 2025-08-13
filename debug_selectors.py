from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time


def test_selectors():
    """Test different selectors to see what elements are found."""

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize Chrome driver
    service = Service("chromedriver-137/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Load the saved HTML
        driver.get(
            "file:///c:/Users/Shannon/OneDrive/Desktop/shanbot/calednarhtml.xml")
        time.sleep(2)

        print("🔍 Testing different selectors...")

        # Test workout selectors
        workout_selectors = [
            "//*[contains(text(), 'Chest Day')]",
            "//*[contains(text(), 'Core Day')]",
            "//*[contains(text(), 'Back Day')]",
            "//*[contains(text(), 'Shoulder Day')]",
            "//*[contains(text(), 'Leg Day')]",
            "//*[contains(text(), 'Functional')]",
            "//*[contains(text(), 'Resistance Training')]"
        ]

        print("\n🏋️ WORKOUT SELECTORS:")
        for selector in workout_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"  {selector}: {len(elements)} elements")
                for i, elem in enumerate(elements[:3]):
                    try:
                        print(f"    [{i+1}] {elem.text[:50]}...")
                    except:
                        print(f"    [{i+1}] <no text>")
            except Exception as e:
                print(f"  {selector}: ERROR - {e}")

        # Test nutrition selectors
        nutrition_selectors = [
            "//*[contains(text(), 'Cals')]",
            "//*[contains(text(), 'Meals')]",
            "//*[contains(text(), 'cal')]",
            "//*[contains(text(), 'Cal')]"
        ]

        print("\n🍽️ NUTRITION SELECTORS:")
        for selector in nutrition_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"  {selector}: {len(elements)} elements")
                for i, elem in enumerate(elements[:3]):
                    try:
                        print(f"    [{i+1}] {elem.text[:50]}...")
                    except:
                        print(f"    [{i+1}] <no text>")
            except Exception as e:
                print(f"  {selector}: ERROR - {e}")

        # Test walking selectors
        walking_selectors = [
            "//*[contains(text(), 'Walking')]",
            "//*[contains(text(), 'walking')]"
        ]

        print("\n🚶 WALKING SELECTORS:")
        for selector in walking_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"  {selector}: {len(elements)} elements")
                for i, elem in enumerate(elements[:3]):
                    try:
                        print(f"    [{i+1}] {elem.text[:50]}...")
                    except:
                        print(f"    [{i+1}] <no text>")
            except Exception as e:
                print(f"  {selector}: ERROR - {e}")

        # Test weight selectors
        weight_selectors = [
            "//*[contains(text(), 'kg')]",
            "//*[contains(text(), 'lbs')]"
        ]

        print("\n⚖️ WEIGHT SELECTORS:")
        for selector in weight_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"  {selector}: {len(elements)} elements")
                for i, elem in enumerate(elements[:3]):
                    try:
                        print(f"    [{i+1}] {elem.text[:50]}...")
                    except:
                        print(f"    [{i+1}] <no text>")
            except Exception as e:
                print(f"  {selector}: ERROR - {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_selectors()
