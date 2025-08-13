from programbuilder import TrainerizeAutomation

# Initialize automation
trainerize_bot = TrainerizeAutomation()

# Login credentials
USERNAME = "Shannonbirch@cocospersonaltraining.com"
PASSWORD = "cyywp7nyk"
CLIENT_NAME = "Shannon Birch"  # Update with the appropriate client name

# Program config
program_config = {
    'program_name': 'Cable & Machine Workout Program',
    'weeks': 6,
    'workouts': [
        {
            'name': 'Full Body Cable Workout',
            'exercises': [
                {'name': 'Cable Chest Press', 'sets': '4', 'reps': '10',
                    'instructions': 'Set 1: 20kg, Set 2: 30kg, Set 3: 35kg, Set 4: 40kg'},
                {'name': 'Cable Rear Delt Row', 'sets': '3',
                    'reps': '10', 'instructions': 'All sets with 8kg'},
                {'name': 'Seated Leg Extension', 'sets': '4', 'reps': '15',
                    'instructions': 'Set 1: 30kg, Set 2: 40kg, Sets 3-4: 50kg'},
                {'name': 'Hyperextension', 'sets': '3',
                    'reps': '10', 'instructions': 'Bodyweight only'},
                {'name': 'Hyperextension Oblique Twists', 'sets': '3',
                    'reps': '10', 'instructions': 'Bodyweight only'}
            ]
        }
    ]
}

# Run the automation
try:
    # Login
    if trainerize_bot.login(USERNAME, PASSWORD):
        trainerize_bot.handle_notification_popup()

        # Create the workout program
        if trainerize_bot.create_workout_program(CLIENT_NAME, program_config):
            print(
                f"Successfully created '{program_config['program_name']}' for {CLIENT_NAME}")
        else:
            print(f"Failed to create workout program")
    else:
        print("Login failed.")

    # Wait for user to review
    input("Press Enter to close the browser and exit...")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'trainerize_bot' in locals():
        trainerize_bot.cleanup()
