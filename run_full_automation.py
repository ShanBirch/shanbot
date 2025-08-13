#!/usr/bin/env python3
"""
Complete Fitness Coaching Automation Workflow
Runs the full end-to-end automation process:
1. Data Collection (Checkin)
2. Video Generation (Simple Blue Video)  
3. Program Implementation (Program Adjuster)
"""

import subprocess
import sys
import os
import time
from datetime import datetime
from pathlib import Path


def run_command(command, description, timeout=1800):  # 30 minute timeout
    """Run a command with timeout and logging"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Start the process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        # Monitor the process
        start_time = time.time()
        output_lines = []

        while True:
            # Check if process is still running
            if process.poll() is not None:
                break

            # Check for timeout
            if time.time() - start_time > timeout:
                print(f"⏰ Process timed out after {timeout} seconds")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                return False

            # Read output
            try:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    output_lines.append(line)
                    print(f"  {line}")
                else:
                    time.sleep(1)
            except:
                break

        # Get final output
        remaining_output, _ = process.communicate()
        if remaining_output:
            for line in remaining_output.strip().split('\n'):
                if line.strip():
                    output_lines.append(line.strip())
                    print(f"  {line.strip()}")

        # Check return code
        return_code = process.returncode
        elapsed = time.time() - start_time

        print(f"\nCompleted in {elapsed:.1f} seconds")
        print(f"Return code: {return_code}")

        if return_code == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code {return_code}")
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def check_prerequisites():
    """Check if all required files exist"""
    required_files = [
        "checkin_good_110525.py",
        "simple_blue_video_enhanced_flow.py",
        "program_adjuster.py"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("✅ All required files found")
    return True


def main():
    """Main automation workflow"""
    print("🤖 Shanbot Complete Automation Workflow")
    print("=" * 60)
    print("This will run the complete coaching automation:")
    print("1. 📊 Data Collection (Checkin)")
    print("2. 🎬 Video Generation (Enhanced Flow)")
    print("3. 💪 Program Implementation (Adjuster)")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        return 1

    # Ask for confirmation
    response = input("\nProceed with full automation? (y/n): ").strip().lower()
    if response != 'y':
        print("Automation cancelled by user")
        return 0

    workflow_start = time.time()

    # Step 1: Run Checkin (Data Collection)
    print("\n🔄 Starting Step 1: Data Collection...")
    checkin_success = run_command(
        "python checkin_good_110525.py",
        "Data Collection (Checkin)",
        timeout=3600  # 1 hour for checkin
    )

    if not checkin_success:
        print("❌ Data collection failed. Stopping automation.")
        return 1

    # Wait a bit for files to be written
    print("⏳ Waiting for data files to be written...")
    time.sleep(10)

    # Step 2: Generate Videos
    print("\n🔄 Starting Step 2: Video Generation...")
    video_success = run_command(
        "python simple_blue_video_enhanced_flow.py",
        "Video Generation (Enhanced Flow)",
        timeout=3600  # 1 hour for video generation
    )

    if not video_success:
        print("❌ Video generation failed. Continuing with program adjustments...")
        # Don't return here - we can still do program adjustments

    # Step 3: Implement Program Adjustments
    print("\n🔄 Starting Step 3: Program Implementation...")
    program_success = run_command(
        "python program_adjuster.py --all",
        "Program Implementation (Adjuster)",
        timeout=3600  # 1 hour for program adjustments
    )

    if not program_success:
        print("❌ Program implementation failed.")

    # Summary
    workflow_end = time.time()
    total_time = workflow_end - workflow_start

    print(f"\n{'='*60}")
    print("🏁 AUTOMATION WORKFLOW COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Data Collection: {'✅ Success' if checkin_success else '❌ Failed'}")
    print(f"Video Generation: {'✅ Success' if video_success else '❌ Failed'}")
    print(
        f"Program Implementation: {'✅ Success' if program_success else '❌ Failed'}")

    # Overall success
    overall_success = checkin_success and (video_success or program_success)

    if overall_success:
        print("\n🎉 Automation workflow completed successfully!")
        print("📧 Client videos are ready for delivery")
        print("💪 Workout programs have been updated in Trainerize")
        return 0
    else:
        print("\n⚠️ Automation workflow completed with some failures")
        print("Please check the logs above for details")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
