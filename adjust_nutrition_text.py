#!/usr/bin/env python
"""
Script to adjust the text spacing in the simple_blue_video_client_folders.py file
"""

import re
import os
from pathlib import Path


def adjust_text_spacing():
    """Adjust the spacing between 'Let's Check Your' and 'Nutrition' text, 
    and between 'Average Daily Intake' and the calorie value"""

    script_path = Path(os.path.dirname(os.path.abspath(__file__))
                       ) / "simple_blue_video_client_folders.py"

    if not script_path.exists():
        print(f"Error: Could not find {script_path}")
        return

    with open(script_path, 'r') as f:
        content = f.read()

    # Find the nutrition slide section using a more specific pattern
    nutrition_section_pattern = r'(# 4\. Nutrition slide.*?print\("✓ Added nutrition slide"\))'

    # Use re.DOTALL to make . match newlines
    nutrition_section_match = re.search(
        nutrition_section_pattern, content, re.DOTALL)

    if not nutrition_section_match:
        print("Error: Could not find nutrition slide section")
        return

    nutrition_section = nutrition_section_match.group(1)

    # Create the replacement text with proper spacing
    replacement_text = """# 4. Nutrition slide
        if "nutrition_analysis" in client_data and client_data["nutrition_analysis"]:
            nutrition_text = client_data["nutrition_analysis"].get("text", "")
            nutrition_value = client_data["nutrition_analysis"].get("value", "")

            nutrition_slide_text = [
                {
                    "text": "Let's Check Your",
                    "font_size": 70,
                    "position": ("center", center_y - 50)  # Reduced vertical spacing
                },
                {
                    "text": "Nutrition",
                    "font_size": 100,
                    "position": ("center", center_y + 20)  # Moved up to be closer to the first text
                },
                {
                    "text": "Average Daily Intake",
                    "font_size": 60,
                    "position": ("center", center_y + 100)  # Adjusted position
                },
                {
                    "text": nutrition_value,
                    "font_size": 80,
                    "position": ("center", center_y + 150)  # Closer to "Average Daily Intake"
                }
            ]
            nutrition_slide = create_slide_with_text(
                video_path, nutrition_slide_text)
            if nutrition_slide:
                slides.append(nutrition_slide)
                print("✓ Added nutrition slide")"""

    # Replace the original nutrition section with the modified one
    modified_content = content.replace(nutrition_section, replacement_text)

    with open(script_path, 'w') as f:
        f.write(modified_content)

    print(f"Successfully adjusted text spacing in {script_path}")


if __name__ == "__main__":
    adjust_text_spacing()
