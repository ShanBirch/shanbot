#!/usr/bin/env python3
"""
Retry progression updates for clients that failed in the previous run
"""

import json
import logging
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retry_failed_clients.log'),
        logging.StreamHandler()
    ]
)


def load_progression_data():
    """Load the fixed progression data"""
    try:
        # Try to load the fixed version first
        try:
            with open('set_by_set_progressions_fixed.json', 'r') as f:
                data = json.load(f)
            logging.info(
                f"Loaded FIXED set-by-set progressions for {len(data)} clients")
            return data
        except FileNotFoundError:
            # Fall back to original if fixed doesn't exist
            with open('set_by_set_progressions.json', 'r') as f:
                data = json.load(f)
            logging.info(
                f"Loaded original set-by-set progressions for {len(data)} clients")
            return data
    except FileNotFoundError:
        logging.error("No progression data file found!")
        return None


def main():
    """Main function to retry failed clients"""

    # List of clients that failed in the previous run
    failed_clients = [
        "Alice Forster",
        "Anna Somogyi",
        "Elena Green",
        "Jo Foy",
        "Kylie Pinder",
        "Nicole Lynch",
        "Noushi Puddy"
    ]

    logging.info("="*60)
    logging.info("RETRYING FAILED CLIENTS - SET-BY-SET PROGRESSIONS")
    logging.info("="*60)
    logging.info(f"Clients to retry: {len(failed_clients)}")
    for client in failed_clients:
        logging.info(f"  - {client}")
    logging.info("="*60)

    # Load progression data
    progressions_data = load_progression_data()
    if not progressions_data:
        logging.error("Failed to load progression data. Exiting.")
        return

    # Filter data to only include failed clients
    filtered_data = {}
    for client_name in failed_clients:
        if client_name in progressions_data:
            filtered_data[client_name] = progressions_data[client_name]
            logging.info(f"✅ Found progression data for {client_name}")
        else:
            logging.warning(f"⚠️ No progression data found for {client_name}")

    if not filtered_data:
        logging.error(
            "No valid progression data found for any failed clients!")
        return

    logging.info(
        f"Processing {len(filtered_data)} clients with progression data")

    # Initialize automation
    automation = TrainerizeAutomation()

    try:
        # Process only the failed clients
        results = automation.process_multiple_clients(filtered_data)

        # Log final results
        logging.info("\n" + "="*60)
        logging.info("RETRY RESULTS SUMMARY")
        logging.info("="*60)

        successful = []
        still_failed = []

        for client_name, result in results.items():
            if result.get("status") == "success":
                successful.append(client_name)
                logging.info(f"✅ {client_name}: SUCCESS")
            else:
                still_failed.append(client_name)
                logging.info(
                    f"❌ {client_name}: FAILED - {result.get('error', 'Unknown error')}")

        logging.info(f"\nFINAL RETRY RESULTS:")
        logging.info(f"  ✅ Now successful: {len(successful)} clients")
        logging.info(f"  ❌ Still failed: {len(still_failed)} clients")

        if successful:
            logging.info(f"\nSuccessful clients:")
            for client in successful:
                logging.info(f"  - {client}")

        if still_failed:
            logging.info(f"\nStill failed clients:")
            for client in still_failed:
                logging.info(f"  - {client}")

    except Exception as e:
        logging.error(f"Error during retry processing: {e}")
    finally:
        automation.cleanup()


if __name__ == "__main__":
    main()
