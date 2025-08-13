#!/usr/bin/env python3
"""
Test script for multiple client workout progression updates
Uses the smart progression data from smart_progressions.json
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
        logging.FileHandler('multiple_clients_test.log'),
        logging.StreamHandler()
    ]
)


def load_smart_progressions():
    """Load the smart progression data from JSON file"""
    try:
        with open('smart_progressions.json', 'r') as f:
            data = json.load(f)
        logging.info(f"Loaded progression data for {len(data)} clients")
        return data
    except FileNotFoundError:
        logging.error("smart_progressions.json not found!")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error reading JSON file: {e}")
        return {}


def main():
    """Main test function"""
    print("=== MULTIPLE CLIENT WORKOUT PROGRESSION RUN ===")

    # Load progression data
    all_progression_data = load_smart_progressions()

    if not all_progression_data:
        print(
            "❌ No progression data available. Please run smart_weight_progression.py first.")
        return

    print(f"\n🎯 Processing {len(all_progression_data)} clients:")
    for client_name, workouts in all_progression_data.items():
        print(f"  📋 {client_name}: {len(workouts)} workouts")
        for workout_name in workouts.keys():
            print(f"    - {workout_name}")

    # Credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"

    # Initialize automation
    trainerize_bot = TrainerizeAutomation()

    try:
        print("\n🔐 Logging in...")
        if not trainerize_bot.login(username, password):
            print("❌ Login failed")
            return

        print("✅ Login successful")

        # Handle any popups
        trainerize_bot.handle_notification_popup()
        time.sleep(2)

        print("\n🚀 Starting multiple client processing...")

        # Process multiple clients (using all data)
        results = trainerize_bot.process_multiple_clients(all_progression_data)

        print("\n📊 RESULTS SUMMARY:")
        print("=" * 50)

        for client_name in all_progression_data.keys():
            client_results = results.get(
                client_name, {"status": "not_processed", "outcome": "client data not in results"})

            status = client_results.get("status", "unknown")
            print(f"\n👤 {client_name}: {status.upper()}")

            if "error" in client_results:
                print(f"   ❌ Error: {client_results['error']}")

            # Show workout results
            workout_results = {k: v for k, v in client_results.items()
                               if k not in ["status", "error"]}

            if workout_results:
                print("   Workouts:")
                for workout_name, workout_status in workout_results.items():
                    status_emoji = "✅" if workout_status == "success" else "❌"
                    print(
                        f"     {status_emoji} {workout_name}: {workout_status}")

        success_count = sum(1 for result in results.values()
                            if result.get("status") == "success" or result.get("outcome") == "completed_nothing_to_do")
        total_count = len(all_progression_data)
        failed_count = total_count - success_count

        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   ✅ Successful: {success_count}/{total_count}")
        print(f"   ❌ Failed: {failed_count}/{total_count}")
        print(f"   📈 Success Rate: {(success_count/total_count)*100:.1f}%" if total_count >
              0 else "  📈 Success Rate: N/A")

        if success_count == total_count:
            print("\n🎉 ALL CLIENTS PROCESSED SUCCESSFULLY!")
        elif success_count > 0:
            print(f"\n⚠️  PARTIAL SUCCESS - {success_count} clients completed")
        else:
            print("\n💥 ALL PROCESSING FAILED")

    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        print(f"❌ Test failed: {e}")

    finally:
        print("\n🧹 Cleaning up...")
        trainerize_bot.cleanup()


if __name__ == "__main__":
    main()
