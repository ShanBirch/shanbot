from programbuilder import TrainerizeAutomation

# Initialize automation
trainerize_bot = TrainerizeAutomation()

# Login credentials
USERNAME = "Shannonbirch@cocospersonaltraining.com"
PASSWORD = "cyywp7nyk"
CLIENT_NAME = "Rick Preston"

# Program config
program_config = {
    'program_name': '6-Week At-Home Dumbbell Program',
    'weeks': 6,
    'workouts': [
        {
            'name': 'Workout A',
            'exercises': [
                {'name': 'Body Weight Squat', 'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Chest Press', 'sets': '4', 'reps': '12'},
                {'name': '2 Handed Dumbbell Bent Over Rows',
                    'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Shoulder Press', 'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Romanian Deadlifts', 'sets': '4', 'reps': '12'}
            ]
        },
        {
            'name': 'Workout B',
            'exercises': [
                {'name': 'Dumbbell Sumo Squats', 'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Chest Fly', 'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Upright Rows', 'sets': '4', 'reps': '12'},
                {'name': 'Bicep Curls D.B', 'sets': '4', 'reps': '12'},
                {'name': 'Dumbbell Tricep Extensions', 'sets': '4', 'reps': '12'}
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
