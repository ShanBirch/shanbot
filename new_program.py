from pe import TrainerizeAutomation
import logging
import time

if __name__ == '__main__':
    # Example credentials and data (replace with real data as needed)
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    client_name = "Kristy Cooper"  # The client to build a program for
    program_name = "Kristys New Program"

    # 5 exercises for each day, 3 sets, 12 reps
    chest_exercises = [
        {'name': 'Barbell Bench Press', 'sets': '3', 'reps': '12'},
        {'name': 'Incline Dumbbell Bench Press', 'sets': '3', 'reps': '12'},
        {'name': 'Cable Chest Fly', 'sets': '3', 'reps': '12'},
        {'name': 'Tricep Push Down', 'sets': '3', 'reps': '12'},
        {'name': 'Dumbbell Skull Crusher', 'sets': '3', 'reps': '12'},
    ]
    back_exercises = [
        {'name': 'Lat Pull Down', 'sets': '3', 'reps': '12'},
        {'name': 'Seated Row', 'sets': '3', 'reps': '12'},
        {'name': 'Barbell Bent Over Row', 'sets': '3', 'reps': '12'},
        {'name': 'Face Pulls', 'sets': '3', 'reps': '12'},
        {'name': 'Alternating Hammer Curls', 'sets': '3', 'reps': '12'},
    ]
    shoulder_exercises = [
        {'name': 'Lateral Raise', 'sets': '3', 'reps': '12'},
        {'name': 'Reverse Pec Deck', 'sets': '3', 'reps': '12'},
        {'name': 'Dumbbell Shoulder Press', 'sets': '3', 'reps': '12'},
        {'name': 'Woodchop', 'sets': '3', 'reps': '12'},
        {'name': 'Hollow Body Hold', 'sets': '3', 'reps': '12'},
    ]
    leg_exercises = [
        {'name': 'Leg Press', 'sets': '3', 'reps': '12'},
        {'name': 'Barbell Back Squat', 'sets': '3', 'reps': '12'},
        {'name': 'Adduction Machine', 'sets': '3', 'reps': '12'},
        {'name': 'Leg Extension', 'sets': '3', 'reps': '12'},
        {'name': 'Lying Leg Curl', 'sets': '3', 'reps': '12'},
    ]

    trainerize_bot = TrainerizeAutomation()
    try:
        if trainerize_bot.login(username, password):
            trainerize_bot.handle_notification_popup()
            # 1. Navigate to the client
            if trainerize_bot.navigate_to_client(client_name):
                print(f"Navigated to client: {client_name}")
                # 2. Go to Training Program tab
                if trainerize_bot.navigate_to_training_program():
                    print("Navigated to Training Program tab.")
                    # 3. Create a new program
                    if trainerize_bot.create_program(program_name):
                        print(f"Created program: {program_name}")
                        # 4. Create workouts for the program (4 days)
                        trainerize_bot.create_workout_chest_day(
                            program_name, chest_exercises)
                        trainerize_bot.create_workout_back_day(
                            program_name, back_exercises)
                        trainerize_bot.create_workout_shoulder_day(
                            program_name, shoulder_exercises)
                        trainerize_bot.create_workout_leg_day(
                            program_name, leg_exercises)
                        # 5. Schedule the workouts and cardio
                        trainerize_bot.schedule_workouts_and_cardio()
                        print("Workouts created and scheduled.")
                    else:
                        print(f"Failed to create program: {program_name}")
                else:
                    print("Failed to navigate to Training Program tab.")
            else:
                print(f"Failed to navigate to client: {client_name}")
        else:
            print("Login failed.")
        input("Press Enter to close...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'trainerize_bot' in locals():
            trainerize_bot.cleanup()
