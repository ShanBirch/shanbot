#!/usr/bin/env python3
"""
Test the integrated checkin system for Shane Minahan
"""

from checkin_good_110525 import TrainerizeAutomation
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_shane_checkin():
    """Run the complete checkin process for Shane Minahan"""

    # Credentials
    username = "shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
    client_name = "Shane Minahan"

    print("🚀 Running Integrated Checkin for Shane Minahan")
    print("=" * 60)

    try:
        # Initialize automation
        automation = TrainerizeAutomation(gemini_api_key)

        # Login
        print("🔐 Logging in...")
        if automation.login(username, password):
            print("[PASS] Login successful!")

            # Try different client name variations
            client_variations = [
                "Shane Minahan",
                "shane minahan",
                "Shane",
                "Minahan",
                "Shane M"
            ]

            navigation_successful = False

            for client_variant in client_variations:
                print(f"🎯 Trying to navigate to: '{client_variant}'...")

                if automation.navigate_to_client(client_variant):
                    print(
                        f"[PASS] Successfully navigated to {client_variant}!")
                    navigation_successful = True
                    client_name = client_variant  # Use the successful variant
                    break
                else:
                    print(f"[FAIL] Could not navigate to {client_variant}")
                    time.sleep(2)  # Wait before trying next variant

            if not navigation_successful:
                print(
                    "[FAIL] Could not navigate to Shane Minahan with any name variation!")
                print("🔍 Let's try to see what clients are available...")

                # Take a screenshot to see what's on screen
                try:
                    automation.driver.save_screenshot("debug_clients_page.png")
                    print("📸 Saved debug screenshot: debug_clients_page.png")
                except:
                    pass

                automation.cleanup()
                return

            # Add extra wait and verification after successful navigation
            print("⏳ Waiting for client profile to fully load...")
            time.sleep(8)  # Give the new tab time to fully load

            # Verify we're on the correct client page
            try:
                current_url = automation.driver.current_url
                print(f"🔍 Current URL: {current_url}")

                # Take a screenshot to verify we're on the right page
                automation.driver.save_screenshot("shane_profile_page.png")
                print("📸 Saved Shane's profile page screenshot: shane_profile_page.png")

                # Check if we can see client-specific elements
                page_title = automation.driver.title
                print(f"📄 Page title: {page_title}")

            except Exception as e:
                print(f"⚠️ Error verifying client page: {e}")

            # Continue with the rest of the checkin process
            print("🔍 Starting comprehensive calendar analysis...")

            # Use the comprehensive calendar analysis
            calendar_results = automation.analyze_comprehensive_calendar_data(
                client_name, username, password, gemini_api_key
            )

            if calendar_results:
                print("✅ Calendar analysis completed!")
                print(
                    f"📊 Nutrition data: {len(calendar_results.get('nutrition_data', []))} entries")
                print(
                    f"🚶 Walking data: {len(calendar_results.get('walking_data', []))} entries")
                print(
                    f"⚖️ Weight data: {len(calendar_results.get('weight_data', []))} entries")
            else:
                print("⚠️ Calendar analysis returned no data")

            # Continue with other analyses (sleep, photos, workouts)
            print("😴 Analyzing sleep data...")
            try:
                automation.navigate_to_sleep_graphs()
                sleep_availability, sleep_analysis_text, average_sleep_hours = automation.analyze_sleep_graph()
                print(f"✅ Sleep analysis: {sleep_availability}")
            except Exception as e:
                print(f"⚠️ Sleep analysis failed: {e}")
                sleep_availability, sleep_analysis_text, average_sleep_hours = "not_analyzed", "Analysis failed", None

            # Analyze progress photos
            print("📸 Analyzing progress photos...")
            try:
                automation.click_progress_photos_tab()
                photos_analysis = automation.analyze_progress_photos()
                print(f"✅ Photos analysis completed")
            except Exception as e:
                print(f"⚠️ Photos analysis failed: {e}")
                photos_analysis = "No photos analysis available"

            # Get weight goal
            print("🎯 Getting weight goal...")
            try:
                automation.navigate_to_goals_and_habits_tab()
                weight_goal_text = automation.get_current_weight_goal()
                print(f"✅ Weight goal: {weight_goal_text}")
            except Exception as e:
                print(f"⚠️ Weight goal failed: {e}")
                weight_goal_text = "No weight goal available"

            # Process workouts
            print("💪 Processing workouts...")
            try:
                automation.click_review_by_workout()
                workout_data_list = automation.process_workouts()
                print(f"✅ Found {len(workout_data_list)} workouts")
            except Exception as e:
                print(f"⚠️ Workout processing failed: {e}")
                workout_data_list = []

            # Prepare fitness data
            print("📋 Preparing comprehensive fitness data...")

            # Use calendar results for nutrition, bodyweight, and steps
            if calendar_results:
                nutrition_analysis_results = calendar_results.get(
                    'nutrition_analysis', {})
                bodyweight_availability = "available" if calendar_results.get(
                    'weight_data') else "not_available"
                bodyweight_structured_data = calendar_results.get(
                    'weight_data', {})
                bodyweight_analysis_text = calendar_results.get(
                    'weight_analysis', 'No weight data')
                steps_availability = "available" if calendar_results.get(
                    'walking_data') else "not_available"
                steps_structured_data = calendar_results.get(
                    'walking_data', {})
                steps_analysis_text = calendar_results.get(
                    'walking_analysis', 'No walking data')
            else:
                # Fallback to default values
                nutrition_analysis_results = {
                    "calories_protein": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Calendar analysis failed."},
                    "fats_carbs": {"availability": "not_analyzed", "structured_data": {}, "analysis_text": "Calendar analysis failed."}
                }
                bodyweight_availability = "not_analyzed"
                bodyweight_structured_data = {}
                bodyweight_analysis_text = "Calendar analysis failed"
                steps_availability = "not_analyzed"
                steps_structured_data = {}
                steps_analysis_text = "Calendar analysis failed"

            # Generate weekly summary
            weekly_summary_data = {
                "current_week_workouts": len([w for w in workout_data_list if 'current_week' in str(w)]),
                "total_workouts": len(workout_data_list),
                "nutrition_tracked_days": len(calendar_results.get('nutrition_data', [])) if calendar_results else 0,
                "walking_activities": len(calendar_results.get('walking_data', [])) if calendar_results else 0
            }

            # Prepare fitness wrapped data
            fitness_wrapped_data = automation.prepare_fitness_wrapped_data(
                client_name=client_name,
                bodyweight_availability=bodyweight_availability,
                bodyweight_structured_data=bodyweight_structured_data,
                bodyweight_analysis_text=bodyweight_analysis_text,
                nutrition_analysis_results=nutrition_analysis_results,
                sleep_availability=sleep_availability,
                sleep_analysis_text=sleep_analysis_text,
                average_sleep_hours=average_sleep_hours,
                steps_availability=steps_availability,
                steps_structured_data=steps_structured_data,
                steps_analysis_text=steps_analysis_text,
                photos_analysis=photos_analysis,
                weight_goal_text=weight_goal_text,
                weekly_summary_data=weekly_summary_data,
                workouts_completed_analysis="Workouts analyzed",
                total_workout_stats_analysis="Stats calculated",
                workout_data_list=workout_data_list
            )

            # Save JSON data
            print("💾 Saving fitness data...")
            automation.save_fitness_wrapped_data(
                client_name, fitness_wrapped_data)

            # Generate review
            print("📄 Generating professional review...")
            review_content = automation.generate_professional_checkin_review(
                client_name, fitness_wrapped_data)

            # Create PDF
            print("📑 Creating PDF...")
            pdf_path = automation.create_checkin_review_pdf(
                client_name, fitness_wrapped_data, review_content)

            if pdf_path:
                print(f"✅ PDF created: {pdf_path}")
            else:
                print("⚠️ PDF creation failed")

            print("\n🎉 Shane Minahan's integrated checkin completed successfully!")
            print("=" * 60)

        else:
            print("[FAIL] Login failed!")

    except Exception as e:
        print(f"💥 Error during Shane's checkin: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            automation.cleanup()
        except:
            pass
        print("🔧 Please check the logs for details.")


if __name__ == "__main__":
    run_shane_checkin()
