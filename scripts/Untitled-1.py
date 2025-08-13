def click_start_building(self):
    """
    Click the 'Start building out Ben's program' button
    """
    try:
        print("Looking for 'Start building' button...")

        # Try multiple strategies to find the button
        button_selectors = [
            "//p[contains(text(), 'Start building out Ben')]",
            "//div[contains(@class, 'flex-left')]//p[contains(text(), 'Start building')]",
            "//div[contains(@class, 'flex-column')]//p[contains(text(), 'Start building')]"
        ]

        button = None
        for selector in button_selectors:
            try:
                button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if button:
                    break
            except:
                continue

        if not button:
            raise Exception("Could not find 'Start building' button")

        # Scroll the button into view
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);", button)
        time.sleep(1)

        # Try to click using multiple methods
        try:
            button.click()
        except:
            # If direct click fails, try JavaScript click
            self.driver.execute_script("arguments[0].click();", button)

        print("Successfully clicked 'Start building' button")

        # Wait for page to load after clicking
        self.wait_for_page_load()

    except Exception as e:
        print(f"Error clicking 'Start building' button: {str(e)}")
        self.driver.save_screenshot("start_building_error.png")
        print("Screenshot saved as 'start_building_error.png'")
        raise
