import sys
import json
from playwright_onboarding_sequence import run_onboarding

# Default client data configuration
client_data = {
    'coach_email': 'shannonbirch@cocospersonaltraining.com',
    'coach_password': 'cyywp7nyk2',
    'email': 'shannonbirch@live.com',
    'first_name': 'Shannon',
    'last_name': 'Birch',
    'program_name': 'Shannons Program'
}

# Default meal plan path
meal_plan_pdf_path = r'C:\Users\Shannon\OneDrive\Desktop\shanbot\output\meal plans\Shannon_Birch_meal_plan_20250508_173956.pdf'

if __name__ == "__main__":
    # If arguments are provided, use them
    if len(sys.argv) == 3:
        try:
            client_data = json.loads(sys.argv[1])
            meal_plan_pdf_path = sys.argv[2]
        except Exception as e:
            print(f"Error parsing arguments: {e}")
            sys.exit(1)
    else:
        print("No arguments provided, using default test data.")
    run_onboarding(client_data, meal_plan_pdf_path) 