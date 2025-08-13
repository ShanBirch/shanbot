from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from time import sleep
import logging

# Setup logging to file
logging.basicConfig(
    filename="test_startup.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)

print("Starting Instagram bot test...")
logging.info("Starting Instagram bot test...")

try:
    # Setup ChromeDriver using the same path as working scripts
    chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
    print(f"Using ChromeDriver path: {chromedriver_path}")
    logging.info(f"Using ChromeDriver path: {chromedriver_path}")

    service = Service(executable_path=chromedriver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")

    # Initialize the driver
    print("Initializing Chrome driver...")
    logging.info("Initializing Chrome driver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open Instagram
    print("Opening Instagram...")
    logging.info("Opening Instagram...")
    driver.get("https://www.instagram.com")

    # Wait and get the title
    sleep(3)
    title = driver.title
    print(f"Page title: {title}")
    logging.info(f"Page title: {title}")

    # Close the browser
    driver.quit()
    print("Test completed successfully!")
    logging.info("Test completed successfully!")

except Exception as e:
    error_msg = f"Test failed with error: {e}"
    print(error_msg)
    logging.error(error_msg)
