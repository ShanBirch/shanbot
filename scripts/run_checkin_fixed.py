import os
import sys
import time
import subprocess
import json
from datetime import datetime

# Full list of all clients to process
CLIENTS = [
    "Shannon Birch",
    "Ben Pryke",
    "Alice Forster",
    "Sarika Ramani",
    "Helen Forster",
    "Nicole Lynch",
    "Conor Beveridge",
    "Rebecca DAngelo",
    "Rick Preston",
    "Claire Ruberu",
    "Kylie Pinder",
    "Jo Foy",
    "Manny Le-ray",
    "Tony Strupl",
    "Heath Kilgour",
    "Anna Somogyi",
    "Danny Birch",
    "MJ Devine",
    "Ben Norman",
    "Adri Rivera",
    "Amanda Buckingham",
    "Naman Tiwari",
    "Kelly Smith",
    "Shane Minahan"
]


def main():
    """Run the check-in for each client by directly calling the automation script"""
    print(f"Starting check-ins for {len(CLIENTS)} clients...")

    try:
        # Define credentials
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk"

        # Import the automation class
        from checkin import TrainerizeAutomation

        # Initialize the TrainerizeAutomation
        trainerize_bot = TrainerizeAutomation()

        # Login
        if not trainerize_bot.login(username, password):
            print("Login failed!")
            return

        print("Login successful!")

        # After login, let's check where we are and use a different approach
        print("Navigating to main dashboard...")
        try:
            # First try to go to the main dashboard
            trainerize_bot.driver.get(
                "https://www.trainerize.com/dashboard.aspx")
            time.sleep(5)  # Wait for the page to load

            # Now check if we're on the 404 page
            if "Oops. We can't find this page" in trainerize_bot.driver.page_source:
                print("Detected 404 page. Trying alternative navigation...")
                # Try a different URL
                trainerize_bot.driver.get(
                    "https://www.trainerize.com/dashboard")
                time.sleep(5)

            # Try clicking the "Clients" link if it exists
            try:
                # Look for any element that might get us to the clients page
                links = trainerize_bot.driver.find_elements("tag name", "a")
                for link in links:
                    try:
                        text = link.text.lower()
                        if "client" in text:
                            print(f"Found client link with text: {link.text}")
                            link.click()
                            time.sleep(5)
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error clicking clients link: {e}")
        except Exception as e:
            print(f"Error navigating to dashboard: {e}")

        # Take a screenshot to see where we are
        try:
            screenshot_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "trainerize_screenshot.png")
            trainerize_bot.driver.save_screenshot(screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")

        # Process each client
        successful_clients = []

        for i, client_name in enumerate(CLIENTS, 1):
            print(f"\nProcessing client {i}/{len(CLIENTS)}: {client_name}")

            try:
                # Try a direct search for the client
                print("Trying direct search for client...")
                try:
                    search_box = None
                    # Try different methods to find a search box
                    try:
                        search_box = trainerize_bot.driver.find_element(
                            "id", "txtSearch")
                    except:
                        try:
                            search_box = trainerize_bot.driver.find_element(
                                "name", "txtSearch")
                        except:
                            try:
                                # Try to find by placeholder text
                                inputs = trainerize_bot.driver.find_elements(
                                    "tag name", "input")
                                for input_elem in inputs:
                                    if input_elem.get_attribute("placeholder") and "search" in input_elem.get_attribute("placeholder").lower():
                                        search_box = input_elem
                                        break
                            except:
                                pass

                    if search_box:
                        search_box.clear()
                        search_box.send_keys(client_name)
                        time.sleep(1)
                        search_box.submit()
                        time.sleep(5)

                        # Look for the client in the results
                        links = trainerize_bot.driver.find_elements(
                            "tag name", "a")
                        for link in links:
                            try:
                                if client_name.lower() in link.text.lower():
                                    print(f"Found client link: {link.text}")
                                    link.click()
                                    time.sleep(5)
                                    break
                            except:
                                continue
                    else:
                        print("Could not find search box")
                except Exception as e:
                    print(f"Error searching for client: {e}")

                # Try the normal navigation as a backup
                if not client_found:
                    print("Trying standard navigation method...")
                    if trainerize_bot.navigate_to_client(client_name):
                        print(
                            f"Successfully navigated to client: {client_name}")
                        client_found = True
                    else:
                        print(f"Failed to navigate to client: {client_name}")
                        continue

                # Get current page source to see where we are
                print("Current page title:", trainerize_bot.driver.title)
                print("Taking screenshot of client page...")
                try:
                    screenshot_path = os.path.join(os.path.dirname(
                        os.path.abspath(__file__)), f"{client_name}_page.png")
                    trainerize_bot.driver.save_screenshot(screenshot_path)
                    print(f"Saved client page screenshot to {screenshot_path}")
                except Exception as e:
                    print(f"Error taking client page screenshot: {e}")

                # Just try to create a dummy JSON file for now
                print("Creating dummy JSON file for testing...")
                fitness_wrapped_data = {
                    "name": client_name,
                    "business_name": "Coco's Personal Training",
                    "current_weight": 75,
                    "weight_loss": 2.5,
                    "has_weight_data": True,
                    "workouts_this_week": 3,
                    "total_reps": 250,
                    "total_sets": 30,
                    "total_weight_lifted": 3000,
                    "has_workout_data": True,
                    "calories_consumed": 2100,
                    "has_nutrition_data": True,
                    "step_count": 8500,
                    "has_steps_data": True,
                    "sleep_hours": "7.5 hours daily",
                    "has_sleep_data": True,
                    "workload_increase": 15,
                    "top_exercises": [
                        {"name": "Squat", "improvement": 20},
                        {"name": "Bench Press", "improvement": 15},
                        {"name": "Deadlift", "improvement": 10}
                    ],
                    "personalized_message": "Great progress this week! Keep up the good work and focus on your nutrition."
                }

                # Save to JSON file with today's date
                today_str = datetime.now().strftime('%Y-%m-%d')
                json_filename = f"{client_name.replace(' ', '_')}_{today_str}_fitness_wrapped_data.json"

                with open(json_filename, 'w') as f:
                    json.dump(fitness_wrapped_data, f, indent=2)

                print(f"Created JSON file: {json_filename}")
                successful_clients.append(client_name)

            except Exception as e:
                print(f"Error processing client {client_name}: {e}")

        # Clean up and close the browser
        try:
            trainerize_bot.cleanup()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

        # Generate videos
        if successful_clients:
            print(
                f"\nSuccessfully processed {len(successful_clients)} clients")
            print("Generating videos...")

            try:
                print("Running simple_blue_video.py to generate videos...")
                subprocess.run([sys.executable, "simple_blue_video.py"])
                print("Videos have been generated!")
            except Exception as e:
                print(f"Error running video generation: {e}")

    except Exception as e:
        print(f"Error during check-in process: {e}")


if __name__ == "__main__":
    main()
