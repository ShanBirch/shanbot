#!/usr/bin/env python3
"""
Robust retry script for progression updates that handles browser crashes
"""

import json
import logging
import time
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retry_failed_clients_robust.log'),
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


def process_single_client_robust(client_name, client_data):
    """Process a single client with robust error handling and browser re-initialization"""
    max_retries = 3

    for attempt in range(max_retries):
        automation = None
        try:
            logging.info(
                f"Attempt {attempt + 1}/{max_retries} for {client_name}")

            # Initialize fresh automation instance
            automation = TrainerizeAutomation()

            # Process just this one client
            single_client_data = {client_name: client_data}
            results = automation.process_multiple_clients(single_client_data)

            # Check if successful
            if results and client_name in results:
                result = results[client_name]
                if result.get("status") == "success":
                    logging.info(
                        f"SUCCESS: {client_name} completed successfully!")
                    return {"status": "success", "attempt": attempt + 1}
                else:
                    logging.warning(
                        f"FAILED: {client_name} - {result.get('error', 'Unknown error')}")

            # If we get here, it failed
            if attempt < max_retries - 1:
                logging.info(f"Retrying {client_name} in 5 seconds...")
                time.sleep(5)

        except Exception as e:
            logging.error(
                f"Error processing {client_name} on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying {client_name} in 5 seconds...")
                time.sleep(5)
        finally:
            # Always cleanup the automation instance
            if automation:
                try:
                    automation.cleanup()
                except:
                    pass  # Ignore cleanup errors

    return {"status": "failed", "error": f"Failed after {max_retries} attempts"}


def main():
    """Main function to retry failed clients one by one"""

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
    logging.info("ROBUST RETRY - FAILED CLIENTS - SET-BY-SET PROGRESSIONS")
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
            logging.info(f"Found progression data for {client_name}")
        else:
            logging.warning(f"No progression data found for {client_name}")

    if not filtered_data:
        logging.error(
            "No valid progression data found for any failed clients!")
        return

    logging.info(
        f"Processing {len(filtered_data)} clients with progression data")
    logging.info("Processing clients ONE BY ONE to avoid browser crashes...")

    # Process each client individually
    successful = []
    still_failed = []

    for i, (client_name, client_data) in enumerate(filtered_data.items(), 1):
        logging.info(f"\n{'='*60}")
        logging.info(
            f"PROCESSING CLIENT {i}/{len(filtered_data)}: {client_name}")
        logging.info(f"{'='*60}")

        result = process_single_client_robust(client_name, client_data)

        if result["status"] == "success":
            successful.append(client_name)
            logging.info(f"CLIENT {i} COMPLETED: {client_name} - SUCCESS!")
        else:
            still_failed.append(client_name)
            logging.error(
                f"CLIENT {i} FAILED: {client_name} - {result.get('error', 'Unknown error')}")

        # Wait between clients to let system stabilize
        if i < len(filtered_data):
            logging.info("Waiting 10 seconds before next client...")
            time.sleep(10)

    # Log final results
    logging.info("\n" + "="*60)
    logging.info("ROBUST RETRY RESULTS SUMMARY")
    logging.info("="*60)

    logging.info(f"FINAL RESULTS:")
    logging.info(f"  Now successful: {len(successful)} clients")
    logging.info(f"  Still failed: {len(still_failed)} clients")

    if successful:
        logging.info(f"\nSuccessful clients:")
        for client in successful:
            logging.info(f"  - {client}")

    if still_failed:
        logging.info(f"\nStill failed clients:")
        for client in still_failed:
            logging.info(f"  - {client}")

    # Overall success rate
    success_rate = (len(successful) / len(filtered_data)) * \
        100 if filtered_data else 0
    logging.info(f"\nOverall success rate: {success_rate:.1f}%")


if __name__ == "__main__":
    main()
