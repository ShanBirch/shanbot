#!/usr/bin/env python3
"""
Update progression goals for a single client to avoid Chrome stability issues
"""

import json
import logging
import sys
from weekly_program_updater import TrainerizeAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('single_client_update.log'),
        logging.StreamHandler()
    ]
)


def load_progression_data():
    """Load the fixed progression data"""
    try:
        with open('set_by_set_progressions_fixed.json', 'r') as f:
            data = json.load(f)
        logging.info(
            f"Loaded FIXED set-by-set progressions for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error("set_by_set_progressions_fixed.json not found")
        return None


def update_single_client(client_name):
    """Update progression goals for a single client"""

    # Load progression data
    progression_data = load_progression_data()
    if not progression_data:
        return False

    if client_name not in progression_data:
        logging.error(f"Client '{client_name}' not found in progression data")
        available_clients = list(progression_data.keys())
        logging.info(f"Available clients: {available_clients}")
        return False

    automation = None
    try:
        logging.info(f"=== UPDATING SINGLE CLIENT: {client_name} ===")

        # Initialize automation
        automation = TrainerizeAutomation()

        # Login
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        if not automation.login(username, password):
            logging.error("❌ LOGIN FAILED")
            return False

        logging.info("✅ LOGIN SUCCESSFUL")

        # Process this single client
        client_data = progression_data[client_name]

        # Use the existing method from the automation class
        results = automation.process_multiple_clients(
            {client_name: client_data})
        result = results.get(client_name, {})

        if result.get("status") == "success":
            logging.info(f"✅ SUCCESS: {client_name} updated successfully")
            return True
        else:
            logging.error(
                f"❌ FAILED: {client_name} - {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR: {e}")
        return False

    finally:
        if automation:
            try:
                automation.cleanup()
                logging.info("✅ CLEANUP COMPLETED")
            except:
                logging.warning("⚠️ CLEANUP HAD ISSUES")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python single_client_update.py <client_name>")
        print("\nAvailable clients:")
        try:
            data = load_progression_data()
            if data:
                for client in data.keys():
                    print(f"  - {client}")
        except:
            pass
        sys.exit(1)

    client_name = sys.argv[1]
    success = update_single_client(client_name)

    if success:
        print(f"\n🎉 SUCCESS: {client_name} updated successfully!")
    else:
        print(f"\n❌ FAILED: Could not update {client_name}")
