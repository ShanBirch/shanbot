import requests
import json
import google.generativeai as genai
import logging
import os
import io
from typing import Optional, Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
RETRY_DELAY_CALORIE = 5  # Delay for calorie analysis retries

# Detailed prompt for food analysis
FOOD_ANALYSIS_PROMPT = """Analyze the provided food image and estimate its nutritional content.

**Instructions:**
1. Identify the main food items visible in the image.
2. Estimate a SINGLE numerical value for the following:
    - Calories
    - Fats (in grams)
    - Carbohydrates (in grams)
    - Protein (in grams)
    - Approximately
3. Respond ONLY with the estimated values in the following format, separated by commas:
   `Calories = [Estimated Calories], Fats = [Estimated Fats]g, Carbohydrates = [Estimated Carbs]g, Protein = [Estimated Protein]g`
4. Do NOT include any conversational text, greetings, sign-offs, explanations, ranges (e.g., 500-600), or additional formatting (like bullet points, bolding).
5. If the image clearly does NOT contain food, respond ONLY with: `Image does not contain food.`

**Example Output for a food image:**
`Calories = 550, Fats = 22g, Carbohydrates = 55g, Protein = 35g`

**Example Output for a non-food image:**
`Yo this doesnt look like food!`
"""


# Simple food description prompt
FOOD_DESCRIPTION_PROMPT = (
    "Describe the food in this image in one short, friendly sentence. "
    "Name obvious items and preparation if clear. No calories or macros."
)


# Image-only classification prompt
CLASSIFY_PROMPT = (
    "You are a strict food image classifier. Analyze ONLY visual cues from the image."
    " Output compact JSON with keys: item_type (one of 'plated_meal','packaged','ingredient','unclear'),"
    " dish_name (2-5 words), confidence (0-100)."
    " Rules: Bottles/jars/wrappers with labels in hand or on a bench are 'packaged'."
    " Sauces, oils, condiments are 'ingredient'. Plates/bowls with a prepared dish are 'plated_meal'."
    " If unsure, set item_type='unclear' and confidence<=50."
)


def _download_image(image_url: str):
    response = requests.get(image_url, stream=True, timeout=20)
    response.raise_for_status()
    content_type = response.headers.get('Content-Type', '').lower()
    image_bytes = response.content
    if not content_type.startswith('image/'):
        raise ValueError(f"Content type '{content_type}' is not image")
    image_part = {"mime_type": content_type, "data": image_bytes}
    return image_part, content_type, image_bytes


def classify_food_image(image_url: str, gemini_api_key: str, model_name: str = "gemini-2.0-flash") -> Optional[Dict[str, Any]]:
    """Classify image as plated_meal vs packaged vs ingredient using image-only cues.
    Returns dict: {item_type, dish_name, confidence}
    """
    if not gemini_api_key:
        # Fallback env names
        gemini_api_key = os.getenv(
            "GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.error("Gemini API key is missing. Cannot classify image.")
            return None
    try:
        genai.configure(api_key=gemini_api_key)
        image_part, _, _ = _download_image(image_url)
        prompt_part = {"text": CLASSIFY_PROMPT}
        contents = [prompt_part, image_part]
        model = genai.GenerativeModel(model_name)
        result = model.generate_content(contents)
        txt = getattr(result, 'text', '') or ''
        # Best-effort JSON parse
        try:
            data = json.loads(txt)
            # sanitize
            item_type = str(data.get('item_type', 'unclear')).strip().lower()
            if item_type not in {'plated_meal', 'packaged', 'ingredient', 'unclear'}:
                item_type = 'unclear'
            dish_name = str(data.get('dish_name', '')).strip()[:60]
            try:
                confidence = int(data.get('confidence', 0))
            except Exception:
                confidence = 0
            return {"item_type": item_type, "dish_name": dish_name, "confidence": confidence}
        except Exception:
            logger.warning(
                "Classification JSON parse failed; fallback to heuristics")
            return {"item_type": "unclear", "dish_name": "", "confidence": 0}
    except Exception as e:
        logger.error(f"Failed to classify image: {e}", exc_info=True)
        return None


PACKAGED_ANALYSIS_PROMPT = (
    "You are a nutrition label reader. Analyze the product image and, if visible, read the nutrition facts."
    " Output compact JSON with keys if available:"
    " per_serve: {calories, protein_g, carbs_g, fats_g},"
    " per_100g: {calories, protein_g, carbs_g, fats_g},"
    " serving_size: string, servings_per_pack: number, net_weight_g: number,"
    " alt_unit: string (e.g., '2 biscuits' or '1 tbsp') with alt_unit_calories if evident."
    " If label not visible, estimate typical values based on visual category and set field 'estimated': true."
    " Respond ONLY with JSON."
)


def analyze_packaged_food(image_url: str, gemini_api_key: str, model_name: str = "gemini-2.0-flash-thinking-exp-01-21") -> Optional[Dict[str, Any]]:
    """Read/estimate packaged product nutrition. Returns dict with fields described in prompt."""
    if not gemini_api_key:
        gemini_api_key = os.getenv(
            "GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.error(
                "Gemini API key is missing. Cannot analyze packaged food.")
            return None
    try:
        genai.configure(api_key=gemini_api_key)
        image_part, _, _ = _download_image(image_url)
        prompt_part = {"text": PACKAGED_ANALYSIS_PROMPT}
        contents = [prompt_part, image_part]
        model = genai.GenerativeModel(model_name)
        result = model.generate_content(contents)
        txt = getattr(result, 'text', '') or ''
        try:
            data = json.loads(txt)
            return data
        except Exception:
            logger.warning(
                "Packaged analysis JSON parse failed; returning None")
            return None
    except Exception as e:
        logger.error(f"Failed to analyze packaged item: {e}", exc_info=True)
        return None


def format_packaged_summary(data: Dict[str, Any]) -> str:
    """Format a concise packaged-food summary text."""
    lines = []
    per_serve = data.get('per_serve') or {}
    per100 = data.get('per_100g') or {}
    net_g = data.get('net_weight_g')
    servings = data.get('servings_per_pack')
    alt_unit = data.get('alt_unit')
    alt_unit_cal = data.get('alt_unit_calories')
    est = data.get('estimated', False)

    if per_serve:
        lines.append(
            f"Per serving: Calories {int(per_serve.get('calories',0))}, P {int(per_serve.get('protein_g',0))}g, C {int(per_serve.get('carbs_g',0))}g, F {int(per_serve.get('fats_g',0))}g")
    if alt_unit and alt_unit_cal:
        try:
            lines.append(f"{alt_unit}: ~{int(alt_unit_cal)} cals")
        except Exception:
            pass
    if per100:
        lines.append(
            f"Per 100g: Calories {int(per100.get('calories',0))}, P {int(per100.get('protein_g',0))}g, C {int(per100.get('carbs_g',0))}g, F {int(per100.get('fats_g',0))}g")
    if net_g and per100 and isinstance(net_g, (int, float)):
        try:
            total_cal = int(
                float(net_g) * float(per100.get('calories', 0)) / 100.0)
            lines.append(f"Whole pack (~{int(net_g)}g): ~{total_cal} cals")
        except Exception:
            pass
    if servings and per_serve and isinstance(servings, (int, float)):
        try:
            total_cal_s = int(float(servings) *
                              float(per_serve.get('calories', 0)))
            lines.append(
                f"Whole pack ({int(servings)} serves): ~{total_cal_s} cals")
        except Exception:
            pass
    if est:
        lines.append("(Estimated — label not fully visible)")
    if not lines:
        lines.append(
            "Couldn't read the label clearly. Send the back-of-pack nutrition panel for exact values.")
    return "\n".join(lines)


def describe_food_image(
    image_url: str,
    gemini_api_key: str,
    model_name: str = "gemini-2.5-flash-lite"
) -> Optional[str]:
    """Return a short, friendly description of the food in the image."""
    if not gemini_api_key:
        gemini_api_key = os.getenv(
            "GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.error("Gemini API key is missing. Cannot describe image.")
            return None

    try:
        genai.configure(api_key=gemini_api_key)
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
        return None

    try:
        response = requests.get(image_url, stream=True, timeout=20)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        if not content_type.startswith('image/'):
            return None
        image_bytes = response.content

        image_part = {
            "mime_type": content_type,
            "data": image_bytes
        }

        prompt_part = {"text": FOOD_DESCRIPTION_PROMPT}
        contents = [prompt_part, image_part]

        try:
            model = genai.GenerativeModel(model_name)
            result = model.generate_content(contents)
            text = getattr(result, 'text', None)
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"Description model call failed: {e}", exc_info=True)
            return None

    except Exception as e:
        logger.error(
            f"Failed to download image for description: {e}", exc_info=True)
        return None


def get_calorie_analysis(
    image_url: str,
    gemini_api_key: str,
    primary_model: str,
    first_fallback_model: str,
    second_fallback_model: str,
    user_description: Optional[str] = None
) -> Optional[str]:
    """
    Downloads an image from a URL, analyzes it using Gemini for approximate
    calorie and macro content with specified model fallbacks, and returns the analysis text.
    Considers an optional user-provided text description.

    Args:
        image_url: The URL of the image file.
        gemini_api_key: The API key for Google Gemini.
        primary_model: The primary Gemini model name to try first (should be vision-capable).
        first_fallback_model: The model to try if the primary fails (should be vision-capable).
        second_fallback_model: The model to try if the first fallback fails (should be vision-capable).
        user_description: Optional text description provided by the user about the food.

    Returns:
        A string containing the food analysis, or None if a critical error occurs.
    """
    logger.info(f"Starting food analysis for URL: {image_url[:100]}...")
    logger.info(
        f"Using model hierarchy: {primary_model} -> {first_fallback_model} -> {second_fallback_model}")

    if not gemini_api_key:
        logger.error("Gemini API key is missing. Cannot perform analysis.")
        return "Error: Missing API key for analysis."

    # Configure Gemini within the function scope
    try:
        genai.configure(api_key=gemini_api_key)
        logger.info("Gemini API configured successfully for food analysis.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
        return "Error: Failed to configure analysis service."

    try:
        # 1. Download image content
        response = requests.get(image_url, stream=True, timeout=20)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        image_bytes = response.content

        if not content_type.startswith('image/'):
            logger.warning(
                f"Content type '{content_type}' is not image. Aborting analysis.")
            # Return a user-friendly message if it's not an image
            return "Looks like that link wasn't for an image, mate. Send through a photo of the food!"

        logger.info(
            f"Successfully downloaded image data ({len(image_bytes)} bytes) of type {content_type}.")

        # 2. Prepare for Gemini Vision API call
        image_part = {
            "mime_type": content_type,
            "data": image_bytes
        }

        # --- Modify prompt to strictly honor user description if available ---
        final_prompt = FOOD_ANALYSIS_PROMPT
        if user_description:
            safe_description = user_description.replace('\n', ' ').strip()
            if safe_description:
                # If user provides a description, treat it as ground truth for the dish identity
                vegan_cues = [
                    'tempeh', 'tofu', 'chickpea', 'chickpeas', 'lentil', 'lentils',
                    'seitan', 'bean', 'beans', 'vegan', 'plant-based', 'plant based'
                ]
                is_vegan_hint = any(cue in safe_description.lower()
                                    for cue in vegan_cues)

                strict_block = (
                    "The user describes the dish as: '" + safe_description + "'.\n"
                    "Treat this dish label as ground truth. Do not reinterpret it.\n"
                    + ("Do not infer meat ingredients; prefer plant-based variants when in doubt.\n" if is_vegan_hint else "") +
                    "Estimate a SINGLE numerical value for: Calories, Fats (g), Carbohydrates (g), Protein (g).\n"
                    "Respond ONLY with the values in this exact format, separated by commas:\n"
                    "Calories = [Calories], Fats = [Fats]g, Carbohydrates = [Carbs]g, Protein = [Protein]g\n"
                    "Do NOT include any extra words, ranges, or formatting."
                )

                final_prompt = strict_block
                logger.info(
                    f"Using strict user description for analysis: {safe_description[:100]}...")
        # --- End prompt modification ---

        prompt_part = {"text": final_prompt}
        contents = [prompt_part, image_part]

        # Safety settings (consistent with technique analysis)
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
        # Consistent generation config
        generation_config = genai.types.GenerationConfig(temperature=0.5)

        # 3. Call Gemini Vision API with Fallback Logic
        models_to_try = [primary_model,
                         first_fallback_model, second_fallback_model]
        analysis_text = None

        for attempt, model_name in enumerate(models_to_try):
            # Ensure the model is vision-capable (basic check, relies on correct model names being passed)
            # Simple check for keywords in model names
            if not any(keyword in model_name for keyword in ['vision', 'pro', 'flash', 'ultra']):
                logger.warning(
                    f"Skipping model {model_name} as it might not be vision-capable based on name.")
                continue

            logger.info(f"Attempt {attempt + 1}: Trying model {model_name}")
            try:
                model = genai.GenerativeModel(model_name)
                api_response = model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                )
                # Check for valid response text
                if api_response.parts:
                    analysis_text = api_response.text.strip()
                    logger.info(
                        f"Successfully received analysis from {model_name}.")
                    break  # Success, exit the loop
                else:
                    # Handle cases where response is empty or blocked without raising exception explicitly
                    logger.warning(
                        f"Received empty or blocked response from {model_name}. Reason: {api_response.prompt_feedback}")
                    # Provide feedback for debugging
                    analysis_text = f"Analysis from {model_name} blocked or empty."

            except genai.types.BlockedPromptException as bpe:
                logger.error(
                    f"Gemini analysis request was blocked by {model_name}: {bpe}")
                analysis_text = "Sorry mate, couldn't analyse that one due to safety filters."
                # Consider if we should break or try the next model depending on the block reason
                # For now, break on explicit block
                break

            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                # Store specific error for debugging if needed
                analysis_text = f"Model {model_name} encountered an error."
                if attempt < len(models_to_try) - 1:
                    logger.info(
                        f"Waiting {RETRY_DELAY_CALORIE}s before trying next model...")
                    time.sleep(RETRY_DELAY_CALORIE)
                else:
                    logger.error(
                        "All models failed to provide a valid analysis.")
                    # analysis_text will hold the error from the last attempt

        # 4. Return result or final error
        # Check if analysis_text indicates success or a specific handled error
        if analysis_text and not analysis_text.startswith("Analysis from") and not analysis_text.startswith("Model") and not analysis_text.startswith("Sorry mate"):
            # Simple post-processing: remove potential markdown lists if they sneak in
            analysis_text = analysis_text.replace(
                "* ", "").replace("- ", "").replace("\n", " ")
            return analysis_text
        elif analysis_text:  # Return specific error messages if generated
            return analysis_text
        else:
            # Return a generic failure message if all models failed without specific errors caught/set
            return "Had trouble analysing that pic, mate. Maybe try sending it again?"

    except requests.exceptions.RequestException as req_e:
        logger.error(
            f"Failed to download image from {image_url[:100]}: {req_e}", exc_info=True)
        return "Error: Couldn't download the image for analysis."
    except Exception as e:
        # Catch any other unexpected errors during setup/download
        logger.error(
            f"An unexpected error occurred before calling Gemini: {e}", exc_info=True)
        return "An unexpected error occurred while trying to analyse the image."


# Example usage (for testing purposes)
if __name__ == '__main__':
    print("Testing calorietracker.py")
    # Ensure you have GEMINI_API_KEY in your environment variables
    test_api_key = os.getenv("GEMINI_API_KEY")
    # Use the actual model names intended for use in webhook_manychat23.py
    # Make sure these are vision capable!
    test_primary = "gemini-1.5-pro-latest"  # Or your preferred vision model
    test_fallback1 = "gemini-1.5-flash-latest"
    # Ensure fallback models are actually vision capable if needed
    test_fallback2 = "gemini-pro-vision"  # Using a known vision model identifier

    # Replace with a real image URL for testing
    # Example food image
    test_image_url = "https://storage.googleapis.com/generativeai-downloads/images/scones.jpg"
    # test_image_url = "https://www.example.com/not_an_image.html" # Test non-image URL
    # test_image_url = "https://upload.wikimedia.org/wikipedia/commons/5/5a/DALLE_2024-01-09_12.03.03_-_A_photorealistic_image_of_a_golden_retriever_smiling_happily_at_the_camera._The_dog_is_outdoors_in_a_sunny_park_setting..png" # Test non-food image

    if not test_api_key:
        print("Please set the GEMINI_API_KEY environment variable.")
    elif not test_image_url:
        print("Please provide a valid test image URL.")
    else:
        print(f"Attempting analysis for: {test_image_url}")
        analysis = get_calorie_analysis(
            test_image_url,
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
            print("\nAnalysis failed or returned None.\n")
