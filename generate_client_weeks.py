import argparse
import asyncio
from client_configs import ALL_CLIENT_DATA, ALL_CLIENT_MEAL_ROTATIONS
from weekly_meal_plan_generator import create_pdf


async def generate_client_weeks(client_name: str, num_weeks: int = 6):
    print(
        f"--- Generating {client_name}'s Meal Plans for {num_weeks} Weeks ---")

    client_data = ALL_CLIENT_DATA.get(client_name)
    if not client_data:
        print(
            f"Error: Client '{client_name}' not found in client_configs.py. Please add their data.")
        return

    # The weekly_meal_plan_generator.py already dynamically fetches meal rotations based on client_data.name
    # So, no need to explicitly pass meal rotation dictionaries here, just ensure they are in client_configs.py

    for week in range(1, num_weeks + 1):
        print(f"Generating Week {week} for {client_name}...")
        try:
            create_pdf(client_data=client_data, week=week)
        except Exception as e:
            print(f"Error generating Week {week} for {client_name}: {e}")
    print(f"--- Finished Generating {client_name}'s Meal Plans ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate weekly meal plans for a client.")
    parser.add_argument("--client", type=str, required=True,
                        help="Name of the client (e.g., Linda).")
    parser.add_argument("--weeks", type=int, default=6,
                        help="Number of weeks to generate.")

    args = parser.parse_args()

    asyncio.run(generate_client_weeks(args.client, args.weeks))
