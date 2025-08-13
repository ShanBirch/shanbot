from scripts.programbuilder import TrainerizeAutomation
import json

# Define Kristy's workout program
program_config = {
    'program_name': '4-Day SBD Focus Program',
    'weeks': 8,
    'workouts': [
        {
            'name': 'Day 1: Squat Focus',
            'exercises': [
                {'name': 'Barbell Back Squat', 'sets': '4', 'reps': '8'},
                {'name': 'Machine Leg Press', 'sets': '3', 'reps': '12'},
                {'name': 'Cable Single Leg Kickback', 'sets': '3', 'reps': '15'},
                {'name': 'Leg Extensions', 'sets': '3', 'reps': '15'},
                {'name': 'Plank', 'sets': '3', 'reps': '30'}
            ]
        },
        {
            'name': 'Day 2: Bench Press Focus',
            'exercises': [
                {'name': 'Barbell Bench Chest Press', 'sets': '4', 'reps': '8'},
                {'name': 'Push Up', 'sets': '3', 'reps': '12'},
                {'name': 'Bench Dumbbell Rows', 'sets': '3', 'reps': '12'},
                {'name': 'Machine Assisted Pull Up', 'sets': '3', 'reps': '10'},
                {'name': 'Cable Bench Triceps Push Down', 'sets': '3', 'reps': '15'}
            ]
        },
        {
            'name': 'Day 3: Deadlift/Back Focus',
            'exercises': [
                {'name': 'Barbell Deadlift', 'sets': '4', 'reps': '8'},
                {'name': 'Dumbbell Romanian Deadlift', 'sets': '3', 'reps': '12'},
                {'name': 'Cable Seated Row', 'sets': '3', 'reps': '12'},
                {'name': 'Barbell Bent Over Row', 'sets': '3', 'reps': '12'},
                {'name': 'Cable Crunch', 'sets': '3', 'reps': '20'}
            ]
        },
        {
            'name': 'Day 4: Overhead Press + Accessories',
            'exercises': [
                {'name': 'Barbell Overhead Press', 'sets': '4', 'reps': '8'},
                {'name': 'Dumbbell Chest Press', 'sets': '3', 'reps': '12'},
                {'name': 'Lat Pull Down Wide Grip', 'sets': '3', 'reps': '12'},
                {'name': 'Alternating Hammer Curls', 'sets': '3', 'reps': '12'},
                {'name': 'Face Pulls', 'sets': '3', 'reps': '15'}
            ]
        }
    ]
}

# Save the program configuration to a file (just for reference)
with open('kristy_program_config.json', 'w') as f:
    json.dump(program_config, f, indent=2)

# Set login credentials and client info
USERNAME = "Shannonbirch@cocospersonaltraining.com"
PASSWORD = "cyywp7nyk"
CLIENT_NAME = "Kristy Cooper"  # Specifically targeting Kristy Cooper

# Initialize and run the Trainerize Automation
trainerize_bot = TrainerizeAutomation()

try:
    # Login
    if trainerize_bot.login(USERNAME, PASSWORD):
        trainerize_bot.handle_notification_popup()

        # Create the workout program for Kristy Cooper
        if trainerize_bot.create_workout_program(CLIENT_NAME, program_config):
            print(
                f"Successfully created '{program_config['program_name']}' for {CLIENT_NAME}")
        else:
            print(f"Failed to create workout program for {CLIENT_NAME}")
    else:
        print("Login failed.")

    # Wait for user to review
    input("Press Enter to close the browser and exit...")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'trainerize_bot' in locals():
        trainerize_bot.cleanup()
