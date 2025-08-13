import requests
import google.generativeai as genai
import logging
import os
import io
from typing import Optional
import time  # Added for delay

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# It's generally better to pass the configured genai object or API key
# For simplicity here, we re-configure, but consider passing it in practice.

# --- Constants ---
# REMOVED: Use a model capable of video analysis
# GEMINI_VISION_MODEL = "gemini-1.5-pro-latest"
RETRY_DELAY_TECHNIQUE = 5  # Shorter delay for technique analysis retries

# Detailed prompt for exercise analysis
EXERCISE_ANALYSIS_PROMPT = """Okay, nice [Exercise Name - identify the specific exercise, e.g., squats, deadlifts]. Good! Overall, reckon the form is looking [General positive comment - e.g., pretty solid, definitely getting there]. Few things to keep in mind though. Your setup [Comment briefly on setup - e.g., looks decent, could be tighter]. During the lift itself, [Describe 1-2 key observations about execution, range of motion, or body positioning - e.g., depth is solid but watch those knees drifting in a bit on the way up, bar path is pretty straight which is nice]. One thing you're doing really well is [Highlight 1 specific strength - e.g., keeping that back straight, controlling the descent]. Love to see it! Main thing to maybe focus on is [Identify 1-2 key areas for improvement and explain *briefly* why - e.g., keeping those elbows tucked a bit more on the bench to keep the tension on your chest, or maybe hitting a little more depth on the squat for full range]. Try thinking about [Provide 1-2 simple, actionable cues - e.g., 'bending the bar' on bench, or 'spreading the floor' with your feet on squats]. Give that a crack next session and see how it feels! Keep up the solid work, you're killing it! Let me know if that makes sense.

**IMPORTANT INSTRUCTIONS:**
- Respond *only* with the analysis paragraph.
- Keep the total response under 500 characters.
- Do NOT use formatting like bullet points, numbered lists, asterisks (*), hashes (#), or hyphens (-).
- Keep a friendly, casual, and motivational tone reflecting Shannon's personality
- Use natural-sounding Aussie phrases like "hey", "yeah okay", "solid", "happens like that hey!", "let's get it"  "no worries", "fair enough", "good on ya", "cheers mate".
- If it's clearly NOT an exercise video, respond *only* with: "Checked the video. Doesn't look like an exercise clip this one, more like [Briefly describe content]. All good though!"
"""

# --- MODIFIED FUNCTION SIGNATURE ---


def get_video_analysis(
    video_url: str,
    gemini_api_key: str,
    primary_model: str,
    first_fallback_model: str,
    second_fallback_model: str
) -> Optional[str]:
    """
    Downloads a video from a URL, analyzes it using Gemini for exercise technique
    with specified model fallbacks, and returns the analysis text.

    Args:
        video_url: The URL of the video file (e.g., from Facebook CDN).
        gemini_api_key: The API key for Google Gemini.
        primary_model: The primary Gemini model name to try first.
        first_fallback_model: The model to try if the primary fails.
        second_fallback_model: The model to try if the first fallback fails.

    Returns:
        A string containing the exercise analysis, or None if an error occurs.
    """
    logger.info(f"Starting video analysis for URL: {video_url[:100]}...")
    logger.info(
        f"Using model hierarchy: {primary_model} -> {first_fallback_model} -> {second_fallback_model}")

    if not gemini_api_key:
        logger.error("Gemini API key is missing. Cannot perform analysis.")
        return None

    # Configure Gemini within the function scope (consider passing configured object)
    try:
        genai.configure(api_key=gemini_api_key)
        logger.info("Gemini API configured successfully for analysis.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
        return None

    try:
        # 1. Download video content
        response = requests.get(video_url, stream=True, timeout=20)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        video_bytes = response.content

        if not content_type.startswith('video/'):
            logger.warning(
                f"Content type '{content_type}' is not video. Aborting analysis.")
            return "The provided link does not appear to be a video file."

        logger.info(
            f"Successfully downloaded video data ({len(video_bytes)} bytes) of type {content_type}.")

        # 2. Prepare for Gemini Vision API call
        video_part = {
            "mime_type": content_type,
            "data": video_bytes
        }
        prompt_part = {"text": EXERCISE_ANALYSIS_PROMPT}
        contents = [prompt_part, video_part]

        # Safety settings (can be adjusted)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        generation_config = genai.types.GenerationConfig(
            temperature=0.4)  # Keep config consistent

        # 3. Call Gemini Vision API with Fallback Logic
        models_to_try = [primary_model,
                         first_fallback_model, second_fallback_model]
        analysis_text = None

        for attempt, model_name in enumerate(models_to_try):
            logger.info(f"Attempt {attempt + 1}: Trying model {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                api_response = model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    # Consider adding request_options if needed, e.g., timeout
                )
                analysis_text = api_response.text.strip()
                logger.info(
                    f"Successfully received analysis from {model_name}.")
                break  # Success, exit the loop

            except genai.types.BlockedPromptException as bpe:
                logger.error(
                    f"Gemini analysis request was blocked by {model_name}: {bpe}")
                analysis_text = "Sorry, the analysis could not be completed due to safety filters."
                break  # Safety block, don't retry other models

            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                if attempt < len(models_to_try) - 1:
                    logger.info(
                        f"Waiting {RETRY_DELAY_TECHNIQUE}s before trying next model...")
                    time.sleep(RETRY_DELAY_TECHNIQUE)
                else:
                    logger.error("All models failed.")
                    # analysis_text remains None or the last error message if needed

        if analysis_text:
            return analysis_text
        else:
            # Handle case where all models failed without specific errors caught above
            return "An unexpected error occurred while analyzing the video after trying all models."

    except requests.exceptions.RequestException as req_e:
        logger.error(
            f"Failed to download video from {video_url[:100]}: {req_e}", exc_info=True)
        return "Error: Could not download the video for analysis."
    except Exception as e:
        # Catch any other unexpected errors during setup/download
        logger.error(
            f"An unexpected error occurred before calling Gemini: {e}", exc_info=True)
        return "An unexpected error occurred before analyzing the video."


# Example usage (for testing purposes)
if __name__ == '__main__':
    print("Testing technique_analysis.py")
    test_api_key = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    # Replace with actual model names if testing standalone
    test_primary = os.getenv("TEST_PRIMARY_MODEL",
                             "gemini-1.5-pro-latest")  # Example fallback
    test_fallback1 = os.getenv(
        "TEST_FALLBACK1_MODEL", "gemini-1.5-flash-latest")  # Example fallback
    test_fallback2 = os.getenv(
        "TEST_FALLBACK2_MODEL", "gemini-1.0-pro")  # Example fallback
    # Replace with a real test URL
    test_video_url = "https://example.com/placeholder.mp4"

    if test_api_key == "YOUR_API_KEY_HERE":
        print("Please set the GEMINI_API_KEY environment variable or replace placeholder.")
    elif test_video_url == "https://example.com/placeholder.mp4":
        print("Please provide a valid test video URL.")
    else:
        print(f"Attempting analysis for: {test_video_url}")
        analysis = get_video_analysis(
            test_video_url,
            test_api_key,
            test_primary,
            test_fallback1,
            test_fallback2
        )
        if analysis:
            print("\n--- Analysis Result ---")
            print(analysis)
            print("-----------------------\n")
        else:
            print("\nAnalysis failed.\n")
