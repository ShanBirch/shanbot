import json
import logging
from datetime import datetime
import pytz
from typing import Dict, Optional, Tuple
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('calorie_tracker')


class CalorieTracker_CalorieTracker:
    def __init__(self, analytics_file_path: str = None):
        """Initialize the calorie tracker with the path to analytics data."""
        self.analytics_file_path = analytics_file_path or r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.json"
        self.melbourne_tz = pytz.timezone('Australia/Melbourne')

    def _load_analytics_data(self) -> dict:
        """Load the analytics data from file."""
        try:
            with open(self.analytics_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analytics data: {e}")
            return {}

    def _save_analytics_data(self, data: dict) -> bool:
        """Save the analytics data back to file."""
        try:
            with open(self.analytics_file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")
            return False

    def _get_user_calorie_data(self, ig_username: str) -> Tuple[dict, dict, dict]:
        """
        Get user's calorie tracking data from analytics file.
        Returns: (analytics_data, user_data, calorie_data)
        """
        analytics_data = self._load_analytics_data()
        user_data = None
        calorie_data = None

        # Search for user in conversations
        conversations = analytics_data.get('conversations', {})
        for user_id, data in conversations.items():
            if isinstance(data, dict) and 'metrics' in data:
                metrics = data['metrics']
                if isinstance(metrics, dict) and metrics.get('ig_username') == ig_username:
                    user_data = data
                    calorie_data = metrics.get('calorie_tracking', {})
                    break

        return analytics_data, user_data, calorie_data

    def get_user_calories(self, ig_username: str) -> Optional[dict]:
        """Get current calorie and macro data for user."""
        _, _, calorie_data = self._get_user_calorie_data(ig_username)
        return calorie_data if calorie_data else None

    def log_meal(self, ig_username: str, calories: int, protein: float, carbs: float, fats: float, meal_description: str) -> Optional[dict]:
        """Log a meal and update remaining calories/macros."""
        analytics_data, user_data, calorie_data = self._get_user_calorie_data(
            ig_username)

        if not calorie_data:
            logger.error(
                f"No calorie tracking data found for user {ig_username}")
            return None

        # Update calories
        calorie_data['calories_consumed'] += calories
        calorie_data['remaining_calories'] = calorie_data['daily_target'] - \
            calorie_data['calories_consumed']

        # Update macros
        calorie_data['macros']['protein']['consumed'] += protein
        calorie_data['macros']['protein']['remaining'] = calorie_data['macros']['protein']['daily_target'] - \
            calorie_data['macros']['protein']['consumed']

        calorie_data['macros']['carbs']['consumed'] += carbs
        calorie_data['macros']['carbs']['remaining'] = calorie_data['macros']['carbs']['daily_target'] - \
            calorie_data['macros']['carbs']['consumed']

        calorie_data['macros']['fats']['consumed'] += fats
        calorie_data['macros']['fats']['remaining'] = calorie_data['macros']['fats']['daily_target'] - \
            calorie_data['macros']['fats']['consumed']

        # Add meal to today's meals
        meal = {
            "time": datetime.now(self.melbourne_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "description": meal_description,
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }
        calorie_data['meals_today'].append(meal)

        # Save updated data
        if self._save_analytics_data(analytics_data):
            return calorie_data
        return None

    def get_daily_summary(self, ig_username: str) -> Optional[str]:
        """Get formatted summary of daily calories and macros."""
        calorie_data = self.get_user_calories(ig_username)
        if not calorie_data:
            return None

        summary = f"""📊 Daily Nutrition Summary:

🔸 Calories: {calorie_data['calories_consumed']}/{calorie_data['daily_target']} ({calorie_data['remaining_calories']} remaining)

Macros Remaining:
🔹 Protein: {calorie_data['macros']['protein']['remaining']}g/{calorie_data['macros']['protein']['daily_target']}g
🔹 Carbs: {calorie_data['macros']['carbs']['remaining']}g/{calorie_data['macros']['carbs']['daily_target']}g
🔹 Fats: {calorie_data['macros']['fats']['remaining']}g/{calorie_data['macros']['fats']['daily_target']}g

Today's Meals:"""

        if calorie_data['meals_today']:
            for meal in calorie_data['meals_today']:
                summary += f"\n• {meal['description']} ({meal['calories']} cals)"
        else:
            summary += "\nNo meals logged today"

        return summary

    def reset_daily_tracking(self, ig_username: str) -> bool:
        """Reset daily tracking while preserving targets."""
        analytics_data, user_data, calorie_data = self._get_user_calorie_data(
            ig_username)

        if not calorie_data:
            return False

        # Reset consumed values while keeping targets
        calorie_data['calories_consumed'] = 0
        calorie_data['remaining_calories'] = calorie_data['daily_target']

        for macro in ['protein', 'carbs', 'fats']:
            calorie_data['macros'][macro]['consumed'] = 0
            calorie_data['macros'][macro]['remaining'] = calorie_data['macros'][macro]['daily_target']

        calorie_data['meals_today'] = []
        calorie_data['current_date'] = datetime.now(
            self.melbourne_tz).strftime("%Y-%m-%d")

        return self._save_analytics_data(analytics_data)

    def parse_meal_from_analysis(self, analysis_text: str) -> Optional[Dict]:
        """
        Parse calorie and macro data from the analysis text returned by the image analysis.
        Example input: "Calories = 550, Fats = 22g, Carbohydrates = 55g, Protein = 35g"
        """
        try:
            # Extract numbers using regex
            import re
            calories = re.search(r'Calories\s*=\s*(\d+)', analysis_text)
            fats = re.search(r'Fats\s*=\s*(\d+)g', analysis_text)
            carbs = re.search(r'Carbohydrates\s*=\s*(\d+)g', analysis_text)
            protein = re.search(r'Protein\s*=\s*(\d+)g', analysis_text)

            if all([calories, fats, carbs, protein]):
                return {
                    'calories': int(calories.group(1)),
                    'fats': float(fats.group(1)),
                    'carbs': float(carbs.group(1)),
                    'protein': float(protein.group(1))
                }
            return None
        except Exception as e:
            logger.error(f"Error parsing meal data: {e}")
            return None

    def get_webhook_responses(self, ig_username: str, analysis_text: str) -> Tuple[str, str]:
        """
        Process food analysis and return both webhook responses.
        Returns: (o1_response, o1_response_2)

        o1_response: The food analysis result (calories/macros in the meal)
        o1_response_2: The updated daily totals after logging the meal
        """
        try:
            # Parse the meal data from analysis
            meal_data = self.parse_meal_from_analysis(analysis_text)
            if not meal_data:
                return "Sorry, I couldn't analyze that meal properly. Please try again.", ""

            # First response - just the meal analysis
            o1_response = f"""📱 Food Analysis:
Your meal contains:
• {meal_data['calories']} calories
• {meal_data['protein']}g protein
• {meal_data['carbs']}g carbs
• {meal_data['fats']}g fats"""

            # Log the meal
            self.log_meal(
                ig_username=ig_username,
                calories=meal_data['calories'],
                protein=meal_data['protein'],
                carbs=meal_data['carbs'],
                fats=meal_data['fats'],
                meal_description=f"Meal from photo analysis ({meal_data['calories']} cals)"
            )

            # Get updated totals for second response
            calorie_data = self.get_user_calories(ig_username)
            if not calorie_data:
                return o1_response, "Sorry, couldn't update your daily totals."

            o1_response_2 = f"""📊 Updated Daily Totals:
Calories: {calorie_data['calories_consumed']}/{calorie_data['daily_target']} ({calorie_data['remaining_calories']} remaining)
Protein: {calorie_data['macros']['protein']['remaining']}g/{calorie_data['macros']['protein']['daily_target']}g remaining
Carbs: {calorie_data['macros']['carbs']['remaining']}g/{calorie_data['macros']['carbs']['daily_target']}g remaining
Fats: {calorie_data['macros']['fats']['remaining']}g/{calorie_data['macros']['fats']['daily_target']}g remaining"""

            return o1_response, o1_response_2

        except Exception as e:
            logger.error(f"Error processing webhook responses: {e}")
            return "Sorry, something went wrong analyzing your meal.", ""

    def handle_food_analysis_webhook(self, ig_username: str, analysis_text: str, description: str = "") -> Tuple[str, str]:
        """
        Handle food analysis from webhook and return both responses.
        Args:
            ig_username: Instagram username
            analysis_text: The analysis text from Gemini (e.g., "Calories = 550, Fats = 22g...")
            description: Optional description of the meal
        Returns:
            Tuple of (o1_response, o1_response_2)
        """
        try:
            # Parse the meal data
            meal_data = self.parse_meal_from_analysis(analysis_text)
            if not meal_data:
                return analysis_text, "Sorry, couldn't update your daily totals."

            # Format first response with better spacing
            o1_response = f"""📱 Food Analysis:


Your meal contains:
• {meal_data['calories']} calories
• {meal_data['protein']}g protein
• {meal_data['carbs']}g carbs
• {meal_data['fats']}g fats"""

            # Log the meal with description
            meal_desc = description if description else f"Meal from photo analysis ({meal_data['calories']} cals)"
            self.log_meal(
                ig_username=ig_username,
                calories=meal_data['calories'],
                protein=meal_data['protein'],
                carbs=meal_data['carbs'],
                fats=meal_data['fats'],
                meal_description=meal_desc
            )

            # Get updated totals
            calorie_data = self.get_user_calories(ig_username)
            if not calorie_data:
                return o1_response, "Sorry, couldn't update your daily totals."

            # Format second response with better spacing and cleaner macro display
            o1_response_2 = f"""📊 Updated Daily Totals:


Calories: {calorie_data['remaining_calories']}/{calorie_data['daily_target']} Remaining
Protein: {calorie_data['macros']['protein']['remaining']}g remaining
Carbs: {calorie_data['macros']['carbs']['remaining']}g remaining
Fats: {calorie_data['macros']['fats']['remaining']}g remaining"""

            return o1_response, o1_response_2

        except Exception as e:
            logger.error(f"Error handling food analysis webhook: {e}")
            return analysis_text, "Sorry, something went wrong updating your daily totals."


# Example usage and testing
if __name__ == "__main__":
    # Test the calorie tracker with cocos_pt_studio
    tracker = CalorieTracker_CalorieTracker()

    # Test getting current calories
    print("\nTesting get_user_calories:")
    calories = tracker.get_user_calories("cocos_pt_studio")
    print(f"Current calorie data: {calories}")

    # Test logging a meal
    print("\nTesting log_meal:")
    test_meal = tracker.log_meal(
        "cocos_pt_studio",
        calories=500,
        protein=30,
        carbs=60,
        fats=15,
        meal_description="Test breakfast - Oats with protein"
    )
    print(f"Updated calorie data after meal: {test_meal}")

    # Test getting daily summary
    print("\nTesting get_daily_summary:")
    summary = tracker.get_daily_summary("cocos_pt_studio")
    print(summary)

    # Test parsing meal from analysis
    print("\nTesting parse_meal_from_analysis:")
    test_analysis = "Calories = 550, Fats = 22g, Carbohydrates = 55g, Protein = 35g"
    parsed_meal = tracker.parse_meal_from_analysis(test_analysis)
    print(f"Parsed meal data: {parsed_meal}")

    # Test webhook responses
    print("\nTesting webhook responses:")
    test_analysis = "Calories = 550, Fats = 22g, Carbohydrates = 55g, Protein = 35g"
    response1, response2 = tracker.get_webhook_responses(
        "cocos_pt_studio", test_analysis)
    print("\nFirst Response (o1 Response):")
    print(response1)
    print("\nSecond Response (o1 Response 2):")
    print(response2)

    # Test webhook handling
    print("\nTesting webhook handling:")
    test_analysis = "Calories = 550, Fats = 22g, Carbohydrates = 55g, Protein = 35g"
    response1, response2 = tracker.handle_food_analysis_webhook(
        "cocos_pt_studio",
        test_analysis,
        "Protein pizza"
    )
    print("\nFirst Response (o1 Response):")
    print(response1)
    print("\nSecond Response (o1 Response 2):")
    print(response2)
