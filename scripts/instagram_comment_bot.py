from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
import random

# Instagram credentials
USERNAME = "your_username"
PASSWORD = "your_password"

# OpenAI API Key
OPENAI_API_KEY = "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"

# ChromeDriver setup
service = Service("C:/SeleniumDrivers/chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.maximize_window()

def send_to_gpt4_vision(image_url, caption):
    """Send an image and caption to GPT-4 Vision for comment generation."""
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",  # Use GPT-4 Vision model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Caption: {caption}"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        max_tokens=100)
        comment = response.choices[0].message.content
        return comment.strip()
    except Exception as e:
        print(f"Error sending to GPT-4 Vision: {e}")
        return "Great post!"

def login_to_instagram():
    try:
        driver.get("https://www.instagram.com")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        print("Logged in successfully.")
        sleep(5)  # Wait for login to complete
    except TimeoutException:
        print("Error: Login failed.")
        driver.quit()
        exit()

def navigate_to_followers():
    try:
        # Go to profile
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@aria-label, 'Profile')]"))
        ).click()
        sleep(3)

        # Click on 'Followers'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "followers"))
        ).click()
        sleep(5)

        print("Opened followers list.")
    except TimeoutException:
        print("Error: Could not navigate to followers.")
        driver.quit()
        exit()

def comment_on_posts():
    try:
        followers = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")[:10]  # Adjust number of followers here
        for follower in followers:
            follower_profile = follower.get_attribute("href")
            print(f"Visiting profile: {follower_profile}")
            driver.get(follower_profile)
            sleep(3)

            # Find the most recent post
            try:
                recent_post = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//article//a"))
                )
                recent_post.click()
                sleep(3)

                # Extract the caption
                try:
                    caption_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//span"))
                    )
                    caption = caption_element.text
                    print(f"Caption: {caption}")
                except NoSuchElementException:
                    caption = "No caption available"
                    print("No caption found, using default message.")

                # Extract the image URL
                try:
                    image_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//img[@decoding='auto']"))
                    )
                    image_url = image_element.get_attribute("src")
                    print(f"Image URL: {image_url}")

                    # Send image and caption to GPT-4 Vision
                    comment_text = send_to_gpt4_vision(image_url, caption)
                    print(f"Generated Comment: {comment_text}")

                    # Comment on the post
                    try:
                        comment_box = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//textarea[@placeholder='Add a comment…']"))
                        )
                        comment_box.click()
                        comment_box.send_keys(comment_text)

                        # Click the 'Post' button
                        post_button = driver.find_element(By.XPATH, "//button[text()='Post']")
                        post_button.click()
                        print(f"Commented: {comment_text}")
                        sleep(random.uniform(60, 180))  # Add a delay before moving to the next follower
                    except NoSuchElementException:
                        print("Comment box not found, skipping...")
                        continue

                except NoSuchElementException:
                    print("No image found, skipping...")
                    continue

            except NoSuchElementException:
                print(f"No posts found for {follower_profile}, skipping...")
                continue

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    login_to_instagram()
    navigate_to_followers()
    comment_on_posts()
    print("Task completed.")
    driver.quit()

if __name__ == "__main__":
    main()
