import sys
import json
import asyncio
from playwright_onboarding_sequence import run_onboarding

if __name__ == "__main__":
    arg1 = sys.argv[1]
    meal_plan_pdf_path = sys.argv[2]
    if arg1.endswith('.json'):
        print(f"Reading client_data from file: {arg1}")
        with open(arg1, 'r') as f:
            client_data = json.load(f)
    else:
        print("Parsing client_data from string")
        client_data = json.loads(arg1)
    print("client_data:", client_data)
    print("meal_plan_pdf_path:", meal_plan_pdf_path)
    asyncio.run(run_onboarding(client_data, meal_plan_pdf_path)) 