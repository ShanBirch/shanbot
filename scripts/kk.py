from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

service = Service("C:/SeleniumDrivers/chromedriver.exe")
options = Options()
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.google.com")
print("Browser launched successfully!")
driver.quit()
