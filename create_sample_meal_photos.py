import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Create meal_photos directory if it doesn't exist
MEAL_PHOTOS_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\meal_photos"
os.makedirs(MEAL_PHOTOS_DIR, exist_ok=True)

# Define meal photos to create
MEAL_PHOTOS = {
    "wellness_bowl.jpg": "Wellness Bowl with Curry Roasted Vegetables",
    "green_lentil_curry.jpg": "Green Lentil Curry with Rice",
    "chicken_wrap.jpg": "Mock Chicken Wrap with Red Curry",
    "red_lentil_dahl.jpg": "Red Lentil Dahl with Rice",
    "tempeh_stirfry.jpg": "Tempeh Stir-Fry with Yellow Curry",
    "penang_curry.jpg": "Penang Curry with Rice"
}


def create_meal_photo(filename, meal_name):
    """Create a sample meal photo with text overlay"""
    # Create a 600x450 image (3:2.25 ratio for PDF)
    width, height = 600, 450

    # Create image with gradient background
    # Light blue background
    img = Image.new('RGB', (width, height), color='#f0f8ff')
    draw = ImageDraw.Draw(img)

    # Add a subtle gradient effect
    for y in range(height):
        # Gradient from light to slightly darker
        color_value = int(240 - (y / height) * 40)
        draw.line([(0, y), (width, y)], fill=(
            color_value, color_value + 8, color_value + 16))

    # Add a decorative border
    border_color = '#1A237E'  # Dark blue matching PDF theme
    draw.rectangle([(10, 10), (width-10, height-10)],
                   outline=border_color, width=3)

    # Add meal name text
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Wrap text to fit in image
    lines = textwrap.wrap(meal_name, width=25)
    text_height = len(lines) * 30

    # Draw text with shadow effect
    text_y = (height - text_height) // 2

    for i, line in enumerate(lines):
        # Draw shadow
        draw.text((width//2 + 2, text_y + i*30), line,
                  font=font, fill='#666666', anchor='mm')
        # Draw main text
        draw.text((width//2, text_y + i*30), line,
                  font=font, fill=border_color, anchor='mm')

    # Add a small decorative element
    draw.ellipse([(width//2 - 50, height - 80), (width//2 + 50, height - 60)],
                 fill=border_color, outline='white', width=2)

    # Save the image
    filepath = os.path.join(MEAL_PHOTOS_DIR, filename)
    img.save(filepath, 'JPEG', quality=95)
    print(f"✅ Created: {filename}")


def main():
    """Create sample meal photos"""
    print("=== CREATING SAMPLE MEAL PHOTOS ===")
    print(f"📁 Directory: {MEAL_PHOTOS_DIR}")
    print()

    for filename, meal_name in MEAL_PHOTOS.items():
        create_meal_photo(filename, meal_name)

    print()
    print("=== PHOTO CREATION COMPLETE ===")
    print("• Created 6 sample meal photos")
    print("• Photos are 600x450 pixels (3:2.25 ratio)")
    print("• Matching PDF color scheme")
    print("• Ready for meal plan PDF generation")
    print()
    print("💡 To use real photos:")
    print("• Replace the sample photos in meal_photos/ directory")
    print("• Use high-quality food photography")
    print("• Maintain 3:2.25 aspect ratio for best results")
    print("• Keep file sizes under 1MB for fast PDF generation")


if __name__ == "__main__":
    main()
