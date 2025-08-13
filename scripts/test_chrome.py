from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from time import sleep

print("Starting Chrome test...")
try:
    # Setup ChromeDriver using the same path as working scripts
    chromedriver_path = r"C:\SeleniumDrivers\chromedriver-win64\chromedriver.exe"
    service = Service(executable_path=chromedriver_path)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")

    # Initialize the driver
    print("Initializing Chrome driver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open a website
    print("Opening Google...")
    driver.get("https://www.google.com")

    # Wait a bit and get the title
    sleep(3)
    print(f"Page title: {driver.title}")

    # Close the browser
    driver.quit()
    print("Test completed successfully!")

except Exception as e:
    print(f"Test failed with error: {e}")
