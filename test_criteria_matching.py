import json

# Test the criteria matching logic
CRITERIA_KEYWORDS = {
    'parenting': ['mum', 'mom', 'mama', 'mother', 'parent', 'kids', 'children', 'baby', 'toddler', 'family', 'motherhood', 'mumlife', 'momlife'],
    'plant_based': ['vegan', 'plant-based', 'plantbased', 'vegetarian', 'plant based', 'cruelty free', 'ethical eating', 'plant powered'],
    'fitness': ['fitness', 'workout', 'exercise', 'gym', 'training', 'strength', 'cardio', 'active', 'fit', 'health', 'wellness', 'strong'],
    'weight_loss': ['weight loss', 'lose weight', 'transformation', 'journey', 'healthy', 'goals', 'progress', 'lifestyle', 'wellness journey'],
    'general_health': ['health', 'wellness', 'nutrition', 'mindful', 'balance', 'self care', 'wellbeing']
}

EXCLUDE_KEYWORDS = [
    'coach', 'trainer', 'personal trainer', 'fitness coach', 'online coach', 'mentor', 'instructor', 'pt',
    'nutritionist', 'dietitian', 'wellness coach', 'transformation coach', 'group coach', 'health coach',
    'life coach', 'consultant', 'specialist', 'expert', 'teacher', 'educator', 'business coach', 'business mentor'
]


def test_criteria_matching(text, username="test_user"):
    """Test the criteria matching with detailed output"""
    text = text.lower()
    matches = []

    print(f"🔍 TESTING CRITERIA FOR: {username}")
    print(f"📝 Text: '{text}'")
    print(f"📏 Text length: {len(text)} characters")
    print()

    # Check each category
    for category, keywords in CRITERIA_KEYWORDS.items():
        category_matches = []
        for kw in keywords:
            if kw in text:
                category_matches.append(kw)

        if category_matches:
            matches.extend(category_matches)
            print(f"✅ {category.upper()}: Found {category_matches}")
        else:
            print(f"❌ {category.upper()}: No matches")

    # Check exclusions
    exclusions = []
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            exclusions.append(kw)

    if exclusions:
        print(f"🚫 EXCLUDED TERMS FOUND: {exclusions}")

    # Matching logic
    has_parenting = any(kw in text for kw in CRITERIA_KEYWORDS['parenting'])
    has_plant_based = any(
        kw in text for kw in CRITERIA_KEYWORDS['plant_based'])
    has_fitness = any(kw in text for kw in CRITERIA_KEYWORDS['fitness'])
    has_health = any(kw in text for kw in CRITERIA_KEYWORDS['general_health'])

    is_match = (
        (has_parenting and (has_plant_based or has_fitness or has_health)) or
        (has_plant_based and has_fitness) or
        len(matches) >= 3
    )

    is_excluded = len(exclusions) > 0

    print()
    print(f"📊 ANALYSIS:")
    print(f"   Parenting: {'✅' if has_parenting else '❌'}")
    print(f"   Plant-based: {'✅' if has_plant_based else '❌'}")
    print(f"   Fitness: {'✅' if has_fitness else '❌'}")
    print(f"   Health: {'✅' if has_health else '❌'}")
    print(f"   Total keywords: {len(matches)}")
    print(f"   Excluded: {'🚫 YES' if is_excluded else '✅ NO'}")
    print()

    final_result = is_match and not is_excluded
    print(
        f"🎯 FINAL RESULT: {'✅ POTENTIAL CLIENT' if final_result else '❌ NO MATCH'}")
    print("=" * 60)

    return final_result


# Test with sample profiles that should match
print("TESTING SAMPLE PROFILES:")
print()

# Test 1: Obvious mum profile
test_criteria_matching(
    "Mum of 3 | Plant-based family | Fitness lover | Wellness journey",
    "obvious_mum_example"
)

# Test 2: Subtle mum profile
test_criteria_matching(
    "wellness by renee brown | mother | healthy lifestyle | balance",
    "wellnessbyreneebrown"
)

# Test 3: Vegan fitness profile
test_criteria_matching(
    "Vegan athlete | Strong mama | Plant powered nutrition",
    "vegan_fitness_example"
)

# Test 4: Profile that should be excluded
test_criteria_matching(
    "Personal trainer | Fitness coach | Plant-based nutrition specialist",
    "coach_example"
)

# Test 5: Minimal profile
test_criteria_matching(
    "health wellness",
    "minimal_example"
)

print("\n🔧 DEBUGGING SUGGESTIONS:")
print("1. Check if bio text is being extracted properly")
print("2. Make keywords more flexible (e.g., 'mama', 'mommy', 'mummy')")
print("3. Consider partial word matches")
print("4. Test with real Instagram profile text")
