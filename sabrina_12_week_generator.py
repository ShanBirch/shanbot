#!/usr/bin/env python3
"""
Sabrina's 12-Week Unique Meal Plan Generator

This script generates 12 unique weeks of meal plans for Sabrina Woods,
with different meals each week while maintaining the same format as
our standard 6-week rotation system.

Each week has unique meals based on Sabrina's preferences:
- Curries (African peanut stew, Indian palak paneer, Sri Lankan eggplant, Japanese katsu)
- Rice bowls (jasmine, basmati, red, black rice - NO brown rice)
- Creative salads with roasted veggies (no cucumber, raw tomatoes, lettuce)
- Rice noodle dishes (broth or stir fry)
- Pasta dishes (impossible beef bolognese, cashew cream, baked tofu)
- Roasted potato bowls

Focus on addressing evening binge eating with satisfying, high-protein meals.
"""

import argparse
from datetime import datetime
from client_configs import ALL_CLIENT_DATA
from weekly_meal_plan_generator import create_pdf

# Sabrina's unique weekly meal rotations - 12 different weeks
SABRINA_WEEKLY_MEAL_PLANS = {
    # Week 1: Curry Focus
    1: {
        "theme": "African & Indian Curry Week",
        "breakfasts": {
            1: ("High-Protein Smoothie Bowl with Mango (Mon-Wed batch)",
                "- 30g Vegan Protein Powder (vanilla)\n- 250ml Soy Milk\n- 100g Frozen Mango\n- 30g Granola\n- 15g Chia Seeds\n- 10g Coconut Flakes",
                "Blend protein powder, soy milk, mango until smooth. Top with granola, chia seeds, coconut. (5 mins)",
                "Macros: 485 calories, 54g carbs, 33g protein, 18g fats"),
            2: ("Tofu Scramble with Spinach in GF High-Protein Wraps (Thu-Sat batch)",
                "- 2 Gluten-Free High-Protein Wraps\n- 150g Firm Tofu (crumbled)\n- 100g Baby Spinach\n- 15g Nutritional Yeast (B12-fortified)\n- 10ml Olive Oil\n- 50g Red Capsicum (finely diced)\n- 1/2 Lemon (juice)\n- Turmeric, garlic powder, black pepper",
                "Scramble tofu with turmeric/garlic in olive oil; wilt spinach. Warm GF wraps. Fill with scramble and red capsicum; finish with lemon juice for vitamin C to enhance iron absorption. (8 mins)",
                "Macros: 525 calories, 50g carbs, 35g protein, 20g fats"),
        },
        "lunches_mon_wed": {
            1: ("African Peanut Stew with Jasmine Rice (Mon-Wed batch)",
                "- 180g Cooked Jasmine Rice\n- 150g Sweet Potato (cubed)\n- 120g Firm Tofu (cubed)\n- 60ml Coconut Milk\n- 30g Natural Peanut Butter\n- 100g Baby Spinach\n- 80g Red Capsicum (diced, fresh)\n- 1/2 Lemon (wedges)\n- Ginger, garlic, chili",
                "Simmer sweet potato and tofu with coconut milk, peanut butter, ginger/garlic/chili. Stir in spinach. Serve over rice and top with fresh red capsicum; squeeze lemon at the table for vitamin C to boost iron absorption. (20 mins)",
                "Macros: 585 calories, 70g carbs, 29g protein, 22g fats"),
        },
        "lunches_thu_sat": {
            1: ("Indian Palak Tofu with Jasmine + Lemon (Thu-Sat batch)",
                "- 180g Cooked Jasmine Rice\n- 150g Firm Tofu (cubed)\n- 200g Baby Spinach\n- 60ml Coconut Milk\n- 15g Cashews (for creaminess)\n- 60g Red Capsicum (diced, fresh)\n- 1/2 Lemon (wedges)\n- Garam masala, turmeric, ginger",
                "Blend spinach with coconut milk and cashews; simmer to a creamy sauce. Pan-sear tofu; fold into palak. Serve over jasmine rice, top with fresh red capsicum; squeeze lemon for vitamin C to enhance iron absorption. (18 mins)",
                "Macros: 575 calories, 65g carbs, 30g protein, 21g fats"),
        },
        "snacks": {
            1: ("Anti-Binge Trail Mix",
                "- 30g Mixed Nuts\n- 20g Dark Chocolate (70%)\n- 10g Pumpkin Seeds",
                "Combine all ingredients. Portion-controlled to prevent overeating. (1 min)",
                "Macros: 290 calories, 13g carbs, 8g protein, 23g fats"),
            2: ("Satisfying Protein Smoothie",
                "- 25g Vegan Protein Powder\n- 200ml Soy Milk\n- 15g Almond Butter\n- Cinnamon",
                "Blend until smooth. Helps prevent evening cravings. (3 mins)",
                "Macros: 250 calories, 8g carbs, 28g protein, 12g fats"),
        },
        "dinners": {
            1: [
                ("Sri Lankan Eggplant Curry with Jasmine Rice + Kiwi",
                 "- 180g Cooked Jasmine Rice\n- 200g Eggplant (cubed)\n- 120g Firm Tofu (cubed)\n- 60ml Coconut Milk\n- 1 tsp Mustard Seeds\n- 8–10 Fresh Curry Leaves\n- 1/2 tsp Turmeric\n- Chili to taste\n- 1 small Onion (sliced)\n- 2 cloves Garlic (minced)\n- 5g Fresh Ginger (grated)\n- 1 Kiwi Fruit (side)",
                 "Heat 1 tsp oil in a pan on medium. Add mustard seeds until they pop (30–45s), then add onion, garlic, ginger and curry leaves; sauté 2–3 mins. Add eggplant; cook 5–6 mins. Stir in tofu and turmeric; cook 2 mins. Pour in coconut milk and a splash of water; simmer gently 5–7 mins until eggplant is tender and sauce thickens. Serve with sliced kiwi on the side for vitamin C to support non‑heme iron absorption. (25 mins)",
                 "Macros: 585 calories, 74g carbs, 27g protein, 19g fats"),
                ("Japanese Katsu Curry with Jasmine Rice + Capsicum & Lemon",
                 "- 180g Cooked Jasmine Rice\n- 150g Baked Tofu Katsu (breadcrumb-coated)\n- Homemade curry sauce with vegetables\n- 100g Mixed Asian Vegetables\n- 60g Red Capsicum (fresh strips)\n- 1/2 Lemon (wedge)",
                 "Bake crumbed tofu on a lined tray at 200°C for 15–18 mins until crisp. Simmer curry sauce in a small pot 6–8 mins until glossy. Steam or stir-fry vegetables 3–4 mins. Bowl up jasmine rice, top with katsu, pour curry sauce, add vegetables, finish with fresh red capsicum and lemon for vitamin C. (30 mins)",
                 "Macros: 605 calories, 76g carbs, 28g protein, 20g fats"),
                ("Aloo Chana (Chickpea & Potato Curry) with Jasmine Rice + Orange",
                 "- 180g Cooked Jasmine Rice\n- 240g Canned Chickpeas (drained)\n- 150g Potato (cubed)\n- 100g Tomato Passata\n- 1 small Onion (diced)\n- 2 cloves Garlic (minced)\n- 1 tsp Garam Masala\n- 1/2 tsp Turmeric\n- 1/2 tsp Cumin\n- 60ml Light Coconut Milk\n- Fresh Coriander\n- 1 Small Orange (segments, side)",
                 "Sauté onion and garlic 2–3 mins. Add spices; toast 30s. Stir in potato cubes, chickpeas, passata and splash of water; simmer 12–15 mins until potato is tender. Stir in coconut milk; simmer 2–3 mins to thicken. Season and finish with coriander. Serve with orange segments for vitamin C to aid iron absorption. (25 mins)",
                 "Macros: 595 calories, 84g carbs, 22g protein, 14g fats")
            ],
            2: []
        }
    },

    # Week 2: Rice Bowl Focus
    2: {
        "theme": "Creative Rice Bowl Week",
        "breakfasts": {
            1: ("Quinoa Breakfast Bowl (Mon-Wed batch)",
                "- 120g Cooked Quinoa\n- 25g Protein Powder\n- 100g Mixed Berries\n- 15g Hemp Seeds\n- 20g Coconut Yogurt",
                "Mix warm quinoa with protein powder, top with berries, seeds, yogurt. (5 mins)",
                "Macros: 475 calories, 52g carbs, 32g protein, 16g fats"),
            2: ("Savory Breakfast Rice Bowl (Thu-Sat batch)",
                "- 150g Cooked Jasmine Rice\n- 100g Firm Tofu (scrambled)\n- 50g Avocado\n- 10g Nori Sheets\n- Soy sauce, sesame oil",
                "Warm rice, scramble tofu, assemble bowl with avocado and nori. (10 mins)",
                "Macros: 510 calories, 55g carbs, 25g protein, 20g fats"),
        },
        "lunches_mon_wed": {
            1: ("Thai-Style Jasmine Rice Bowl (Mon-Wed batch)",
                "- 180g Cooked Jasmine Rice\n- 120g Firm Tofu (marinated)\n- 150g Asian Vegetables (capsicum, snow peas)\n- 30g Cashews\n- Thai basil, lime, chili",
                "Marinate and pan-fry tofu, stir-fry vegetables, assemble over rice with cashews. (18 mins)",
                "Macros: 575 calories, 64g carbs, 29g protein, 21g fats"),
        },
        "lunches_thu_sat": {
            1: ("Mediterranean Basmati Bowl (Thu-Sat batch)",
                "- 180g Cooked Basmati Rice\n- 120g Baked Tofu\n- 150g Roasted Mediterranean Veg\n- 30g Hummus\n- Lemon, herbs",
                "Roast vegetables, bake tofu, assemble bowl with hummus drizzle. (20 mins)",
                "Macros: 560 calories, 63g carbs, 28g protein, 19g fats"),
        },
        "snacks": {
            1: ("Energy Rice Paper Rolls",
                "- 2 Rice Paper Sheets\n- 50g Avocado\n- 50g Tofu\n- Fresh Herbs\n- Peanut Dipping Sauce",
                "Assemble fresh rolls, serve with peanut sauce. Satisfying but not heavy. (8 mins)",
                "Macros: 275 calories, 25g carbs, 12g protein, 16g fats"),
            2: ("Protein-Rich Red Rice Pudding",
                "- 100g Cooked Red Rice\n- 150ml Soy Milk\n- 15g Protein Powder\n- Cinnamon, vanilla",
                "Warm rice with soy milk, stir in protein powder and spices. (5 mins)",
                "Macros: 240 calories, 35g carbs, 18g protein, 4g fats"),
        },
        "dinners": {
            1: [("Korean-Style Black Rice Bowl",
                 "- 180g Cooked Black Rice\n- 120g Baked Tofu\n- 150g Kimchi\n- 50g Avocado\n- Sesame oil, nori",
                 "Assemble bowl with warm rice, baked tofu, fermented kimchi, avocado. (12 mins)",
                 "Macros: 535 calories, 62g carbs, 27g protein, 22g fats")],
            2: [("Mexican Red Rice Power Bowl",
                 "- 180g Cooked Red Rice\n- 120g Black Beans\n- 100g Roasted Capsicum\n- 50g Avocado\n- Salsa, lime",
                 "Layer rice, beans, roasted veg, top with avocado and fresh salsa. (15 mins)",
                 "Macros: 520 calories, 68g carbs, 24g protein, 16g fats")],
        }
    },

    # Week 3: Pasta & Noodle Focus
    3: {
        "theme": "Pasta & Rice Noodle Week",
        "breakfasts": {
            1: ("Protein Pancakes (Mon-Wed batch)",
                "- 40g Oat Flour\n- 25g Protein Powder\n- 200ml Soy Milk\n- 1/2 Banana\n- 15g Maple Syrup",
                "Blend ingredients, cook as pancakes. Top with remaining banana. (12 mins)",
                "Macros: 485 calories, 58g carbs, 30g protein, 12g fats"),
            2: ("Avocado Toast Deluxe (Thu-Sat batch)",
                "- 2 Slices Sourdough\n- 80g Avocado\n- 15g Hemp Seeds\n- 50g Cherry Tomatoes\n- Lemon, salt",
                "Toast bread, mash avocado, top with seeds and tomatoes. (6 mins)",
                "Macros: 495 calories, 52g carbs, 18g protein, 26g fats"),
        },
        "lunches_mon_wed": {
            1: ("Vietnamese Rice Noodle Soup (Mon-Wed batch)",
                "- 120g Rice Noodles\n- 800ml Vegetable Broth\n- 100g Firm Tofu\n- Asian herbs, bean sprouts\n- Lime, chili",
                "Prepare broth, cook noodles, assemble with tofu and fresh herbs. (15 mins)",
                "Macros: 485 calories, 68g carbs, 22g protein, 12g fats"),
        },
        "lunches_thu_sat": {
            1: ("Impossible Beef Bolognese Pasta (Thu-Sat batch)",
                "- 100g Pasta (protein variety)\n- 100g Impossible Beef\n- 150ml Tomato Sauce\n- 15g Nutritional Yeast\n- Italian herbs",
                "Cook pasta, brown impossible beef, simmer with sauce. Top with nutritional yeast. (15 mins)",
                "Macros: 565 calories, 58g carbs, 35g protein, 18g fats"),
        },
        "snacks": {
            1: ("Rice Cake Stack",
                "- 2 Brown Rice Cakes\n- 30g Hummus\n- 10g Hemp Seeds\n- Cherry tomatoes",
                "Stack rice cakes with hummus and toppings. (3 mins)",
                "Macros: 245 calories, 28g carbs, 10g protein, 12g fats"),
            2: ("Noodle Soup Mug",
                "- 30g Rice Noodles\n- 200ml Vegetable Broth\n- 20g Tofu\n- Green onions",
                "Quick mug soup for light evening snack. (5 mins)",
                "Macros: 185 calories, 32g carbs, 8g protein, 3g fats"),
        },
        "dinners": {
            1: [("Cashew Cream Pasta with Roasted Vegetables",
                 "- 100g Pasta\n- 40g Cashews\n- 200g Roasted Seasonal Vegetables\n- Nutritional yeast, herbs",
                 "Roast vegetables, blend cashews with soy milk for cream sauce, toss pasta. (25 mins)",
                 "Macros: 585 calories, 68g carbs, 24g protein, 24g fats")],
            2: [("Thai Rice Noodle Stir Fry",
                 "- 120g Rice Noodles\n- 120g Firm Tofu\n- 150g Asian Vegetables\n- Thai basil, lime, peanuts",
                 "Stir fry tofu and vegetables, toss with cooked noodles and Thai flavors. (18 mins)",
                 "Macros: 520 calories, 62g carbs, 26g protein, 20g fats")],
        }
    },

    # Week 4: Roasted Potato Focus
    4: {
        "theme": "Roasted Potato Power Week",
        "breakfasts": {
            1: ("Sweet Potato Breakfast Hash (Mon-Wed batch)",
                "- 150g Roasted Sweet Potato\n- 100g Firm Tofu (scrambled)\n- 50g Baby Spinach\n- 15g Nutritional Yeast\n- Herbs, spices",
                "Roast sweet potato, scramble tofu, combine with spinach. (15 mins)",
                "Macros: 475 calories, 52g carbs, 28g protein, 15g fats"),
            2: ("Protein Smoothie with Berries (Thu-Sat batch)",
                "- 30g Protein Powder\n- 250ml Soy Milk\n- 100g Mixed Berries\n- 10g Almond Butter",
                "Blend until smooth and creamy. (3 mins)",
                "Macros: 450 calories, 35g carbs, 35g protein, 12g fats"),
        },
        "lunches_mon_wed": {
            1: ("Mediterranean Roasted Potato Bowl (Mon-Wed batch)",
                "- 200g Roasted Baby Potatoes\n- 120g Baked Tofu\n- 150g Mediterranean Vegetables\n- 30g Hummus\n- Lemon, herbs",
                "Roast potatoes and vegetables, serve with baked tofu and hummus. (25 mins)",
                "Macros: 545 calories, 68g carbs, 26g protein, 18g fats"),
        },
        "lunches_thu_sat": {
            1: ("Loaded Potato Skins Vegan Style (Thu-Sat batch)",
                "- 200g Baked Potato (flesh scooped)\n- 80g Cashew Cream\n- 30g Nutritional Yeast\n- Green onions, herbs",
                "Bake potatoes, make cashew cream filling, stuff and bake again. (30 mins)",
                "Macros: 520 calories, 65g carbs, 22g protein, 20g fats"),
        },
        "snacks": {
            1: ("Roasted Chickpeas",
                "- 100g Cooked Chickpeas\n- 5ml Olive Oil\n- Spices (cumin, paprika)",
                "Roast seasoned chickpeas until crispy. (20 mins prep, batch made)",
                "Macros: 185 calories, 28g carbs, 8g protein, 5g fats"),
            2: ("Sweet Potato Smoothie",
                "- 100g Roasted Sweet Potato\n- 200ml Soy Milk\n- Cinnamon, vanilla",
                "Blend roasted sweet potato with soy milk and spices. (3 mins)",
                "Macros: 165 calories, 32g carbs, 6g protein, 3g fats"),
        },
        "dinners": {
            1: [("Crispy Potato & Tofu Buddha Bowl",
                 "- 180g Roasted Crispy Potatoes\n- 120g Baked Tofu\n- 150g Seasonal Roasted Vegetables\n- Tahini dressing",
                 "Roast potatoes until crispy, bake tofu, assemble with vegetables and dressing. (35 mins)",
                 "Macros: 565 calories, 62g carbs, 28g protein, 22g fats")],
            2: [("Stuffed Sweet Potatoes with Black Beans",
                 "- 200g Baked Sweet Potato\n- 120g Black Beans\n- 50g Avocado\n- Salsa, lime",
                 "Bake sweet potatoes, warm black beans, stuff and top with avocado. (25 mins)",
                 "Macros: 485 calories, 72g carbs, 22g protein, 12g fats")],
        }
    }

    # Additional weeks 5-12 can be added here as needed...
}


def generate_sabrina_week(week_number: int):
    """Generate a specific week's meal plan for Sabrina"""

    # Get Sabrina's client data
    client_data = ALL_CLIENT_DATA.get("Sabrina Woods")
    if not client_data:
        print("Error: Sabrina Woods not found in client data")
        return

    # Check if we have meal plan data for this week
    if week_number not in SABRINA_WEEKLY_MEAL_PLANS:
        print(f"Error: Week {week_number} meal plan not yet created")
        print(f"Available weeks: {list(SABRINA_WEEKLY_MEAL_PLANS.keys())}")
        return

    # Temporarily add this week's meal rotations to the global rotations
    week_meals = SABRINA_WEEKLY_MEAL_PLANS[week_number]

    # Import the global meal rotations and temporarily add Sabrina's
    from client_configs import ALL_CLIENT_MEAL_ROTATIONS

    # Add Sabrina's theme info to her client data temporarily
    client_data_with_theme = client_data.copy()
    client_data_with_theme["weekly_theme"] = week_meals['theme']
    client_data_with_theme["theme_itinerary"] = get_sabrina_12_week_itinerary()

    # Temporarily add Sabrina's week to the rotations
    ALL_CLIENT_MEAL_ROTATIONS["Sabrina Woods"] = week_meals

    print(f"Generating Week {week_number} for Sabrina Woods...")
    print(f"Theme: {week_meals['theme']}")

    try:
        create_pdf(client_data=client_data_with_theme, week=week_number)
        print(
            f"Successfully generated Sabrina_Week{week_number}_Meal_Plan.pdf")
    except Exception as e:
        print(f"Error generating Week {week_number}: {e}")
    finally:
        # Clean up - remove Sabrina from global rotations
        if "Sabrina Woods" in ALL_CLIENT_MEAL_ROTATIONS:
            del ALL_CLIENT_MEAL_ROTATIONS["Sabrina Woods"]


def get_sabrina_12_week_itinerary():
    """Return the 12-week theme itinerary for Sabrina"""
    itinerary = {
        1: "African & Indian Curry Week",
        2: "Creative Rice Bowl Week",
        3: "Pasta & Rice Noodle Week",
        4: "Roasted Potato Power Week",
        5: "Fresh & Light Week",
        6: "International Fusion Week",
        7: "Comfort Food Week",
        8: "Spice & Heat Week",
        9: "Protein-Rich Classics Week",
        10: "Seasonal Comfort Week",
        11: "Creative Salad Week",
        12: "Celebration & Favorites Week"
    }
    return itinerary


def generate_all_sabrina_weeks():
    """Generate all available weeks for Sabrina"""
    available_weeks = list(SABRINA_WEEKLY_MEAL_PLANS.keys())
    print(f"Generating {len(available_weeks)} weeks for Sabrina Woods...")

    for week in available_weeks:
        generate_sabrina_week(week)
        print(f"Completed Week {week}")

    print("\nAll available weeks generated!")
    print(f"Generated weeks: {available_weeks}")

    if len(available_weeks) < 12:
        remaining = 12 - len(available_weeks)
        print(f"\nNote: {remaining} weeks still need to be created.")
        print("Please add more weekly meal plans to SABRINA_WEEKLY_MEAL_PLANS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Sabrina's unique weekly meal plans")
    parser.add_argument("--week", type=int,
                        help="Generate specific week (1-12)")
    parser.add_argument("--all", action="store_true",
                        help="Generate all available weeks")

    args = parser.parse_args()

    if args.all:
        generate_all_sabrina_weeks()
    elif args.week:
        generate_sabrina_week(args.week)
    else:
        print("Please specify --week <number> or --all")
        print(f"Available weeks: {list(SABRINA_WEEKLY_MEAL_PLANS.keys())}")
