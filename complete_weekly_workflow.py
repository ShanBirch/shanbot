#!/usr/bin/env python3
"""
Complete Weekly Workflow for Shannon's Coaching Business

This script runs the complete weekly workflow:
1. Generate client checkin data (checkin_good110525.py)
2. Create videos with progression analysis (simple_blue_video.py)
3. Update Trainerize with new progression goals
4. Optionally upload videos to Google Drive

Usage:
    python complete_weekly_workflow.py [--upload] [--skip-checkin] [--skip-video] [--skip-trainerize]
"""

import subprocess
import sys
import os
import time
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_workflow.log'),
        logging.StreamHandler()
    ]
)


def run_command(command, description, check_success=True):
    """Run a command and handle errors"""
    logging.info(f"🚀 Starting: {description}")
    logging.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if result.stdout:
            logging.info(f"Output: {result.stdout}")

        if result.stderr:
            logging.warning(f"Stderr: {result.stderr}")

        if check_success and result.returncode != 0:
            logging.error(f"❌ Failed: {description}")
            logging.error(f"Return code: {result.returncode}")
            return False

        logging.info(f"✅ Completed: {description}")
        return True

    except Exception as e:
        logging.error(f"❌ Error running {description}: {e}")
        return False


def check_file_exists(filepath, description):
    """Check if a required file exists"""
    if os.path.exists(filepath):
        logging.info(f"✅ Found: {description} at {filepath}")
        return True
    else:
        logging.error(f"❌ Missing: {description} at {filepath}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run complete weekly workflow')
    parser.add_argument('--upload', action='store_true',
                        help='Upload videos to Google Drive after creation')
    parser.add_argument('--skip-checkin', action='store_true',
                        help='Skip the checkin data generation step')
    parser.add_argument('--skip-video', action='store_true',
                        help='Skip the video generation step')
    parser.add_argument('--skip-trainerize', action='store_true',
                        help='Skip the Trainerize update step')
    parser.add_argument('--date', type=str,
                        help='Date for processing (YYYY-MM-DD format)')

    args = parser.parse_args()

    # Set target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            date_str = target_date.strftime('%Y-%m-%d')
        except ValueError:
            logging.error("Invalid date format. Please use YYYY-MM-DD format.")
            return 1
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    logging.info(f"🎯 Starting Weekly Workflow for {date_str}")
    logging.info("="*80)

    # Step 1: Generate client checkin data
    if not args.skip_checkin:
        logging.info("📊 STEP 1: Generating client checkin data...")

        if not check_file_exists('checkin_good110525.py', 'Checkin script'):
            return 1

        success = run_command(
            [sys.executable, 'checkin_good110525.py'],
            "Generate client checkin data"
        )

        if not success:
            logging.error(
                "Failed to generate checkin data. Stopping workflow.")
            return 1

        # Verify output files were created
        checkin_dir = 'output/checkin_reviews'
        if os.path.exists(checkin_dir):
            json_files = [f for f in os.listdir(checkin_dir)
                          if f.endswith('_fitness_wrapped_data.json') and date_str in f]
            logging.info(f"✅ Generated {len(json_files)} client data files")

            if len(json_files) == 0:
                logging.warning(
                    "No client data files generated. Continuing anyway...")
        else:
            logging.warning("Checkin reviews directory not found")
    else:
        logging.info("⏭️  Skipping checkin data generation")

    # Step 2: Generate videos with progression analysis
    if not args.skip_video:
        logging.info(
            "🎥 STEP 2: Generating videos with progression analysis...")

        if not check_file_exists('simple_blue_video.py', 'Video generation script'):
            return 1

        # Build command for video generation
        video_command = [sys.executable, 'simple_blue_video.py']
        if args.date:
            video_command.extend(['--date', date_str])
        if args.upload:
            video_command.append('--upload')

        success = run_command(
            video_command,
            "Generate videos with progression analysis"
        )

        if not success:
            logging.error(
                "Failed to generate videos. Continuing with Trainerize update...")
        else:
            # Check output videos
            output_dir = 'output'
            if os.path.exists(output_dir):
                video_files = [f for f in os.listdir(output_dir)
                               if f.endswith('.mp4') and 'week_summary' in f]
                logging.info(f"✅ Generated {len(video_files)} video files")
    else:
        logging.info("⏭️  Skipping video generation")

    # Step 3: Update Trainerize with progression goals
    if not args.skip_trainerize:
        logging.info("💪 STEP 3: Updating Trainerize with progression goals...")

        # Check which progression update script to use
        if check_file_exists('update_with_set_by_set_progressions.py', 'Set-by-set progression updater'):
            success = run_command(
                [sys.executable, 'update_with_set_by_set_progressions.py'],
                "Update Trainerize with set-by-set progressions"
            )
        elif check_file_exists('update_with_fresh_progressions.py', 'Fresh progression updater'):
            success = run_command(
                [sys.executable, 'update_with_fresh_progressions.py'],
                "Update Trainerize with fresh progressions"
            )
        else:
            logging.error("No progression update script found!")
            success = False

        if not success:
            logging.error(
                "Failed to update Trainerize. Please check manually.")
        else:
            logging.info(
                "✅ Successfully updated Trainerize with new progression goals")
    else:
        logging.info("⏭️  Skipping Trainerize update")

    # Final summary
    logging.info("="*80)
    logging.info("🎉 WEEKLY WORKFLOW COMPLETE!")
    logging.info("="*80)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Completed at: {current_time}")

    if not args.skip_checkin:
        logging.info("✅ Client checkin data generated")
    if not args.skip_video:
        logging.info("✅ Videos created with progression analysis")
        if args.upload:
            logging.info("✅ Videos uploaded to Google Drive")
    if not args.skip_trainerize:
        logging.info("✅ Trainerize updated with new goals")

    logging.info("\n📋 Next steps:")
    logging.info("1. Check videos in output/ directory")
    logging.info("2. Verify Trainerize goals were updated correctly")
    logging.info("3. Send videos to clients if not auto-uploaded")

    return 0


if __name__ == "__main__":
    sys.exit(main())
