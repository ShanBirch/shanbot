#!/usr/bin/env python3
"""
Script to run both the webhook server and Streamlit dashboard simultaneously.
"""

import multiprocessing
import subprocess
import sys
import os
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_webhook():
    """Run the webhook server"""
    try:
        logger.info("Starting webhook server...")
        # Change to the shanbot directory
        os.chdir(r"C:\Users\Shannon\OneDrive\Desktop\shanbot")

        # Run the webhook
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "webhook0605:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ], check=True)
    except Exception as e:
        logger.error(f"Error running webhook: {e}")


def run_dashboard():
    """Run the Streamlit dashboard"""
    try:
        logger.info("Starting Streamlit dashboard...")
        # Change to the dashboard directory
        os.chdir(r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\dashboard_modules")

        # Run the dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")


def main():
    """Main function to start both services"""
    logger.info("=== Starting Shanbot Services ===")
    logger.info("Starting webhook server and Streamlit dashboard...")

    # Create processes for both services
    webhook_process = multiprocessing.Process(
        target=run_webhook, name="Webhook")
    dashboard_process = multiprocessing.Process(
        target=run_dashboard, name="Dashboard")

    try:
        # Start both processes
        webhook_process.start()
        logger.info("Webhook process started")

        # Small delay before starting dashboard
        time.sleep(2)

        dashboard_process.start()
        logger.info("Dashboard process started")

        logger.info("Both services are starting...")
        logger.info("Webhook will be available at: http://localhost:8001")
        logger.info("Dashboard will be available at: http://localhost:8501")
        logger.info("Press Ctrl+C to stop both services")

        # Wait for both processes
        webhook_process.join()
        dashboard_process.join()

    except KeyboardInterrupt:
        logger.info("Stopping services...")

        # Terminate processes
        if webhook_process.is_alive():
            webhook_process.terminate()
            webhook_process.join(timeout=5)
            if webhook_process.is_alive():
                webhook_process.kill()

        if dashboard_process.is_alive():
            dashboard_process.terminate()
            dashboard_process.join(timeout=5)
            if dashboard_process.is_alive():
                dashboard_process.kill()

        logger.info("Services stopped")

    except Exception as e:
        logger.error(f"Error in main: {e}")

        # Clean up processes
        for process in [webhook_process, dashboard_process]:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()


if __name__ == "__main__":
    # Set multiprocessing start method for Windows
    if sys.platform.startswith('win'):
        multiprocessing.set_start_method('spawn', force=True)

    main()
