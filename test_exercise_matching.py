#!/usr/bin/env python3
"""
Test Exercise Matching Debug Script
===================================

This script helps debug exercise matching issues in the weekly program updater.
It will test the fuzzy matching algorithm to identify potential problems.

Usage: python test_exercise_matching.py
"""


def clean_name(name: str) -> str:
    """Clean exercise names for comparison (same logic as weekly_program_updater.py)"""
    cleaned = name.lower()
    cleaned = cleaned.replace("barbell", "").replace(
        "dumbbell", "").replace("machine", "")
    cleaned = cleaned.replace("-", " ")  # Replace hyphen with space
    # Remove trailing 's' for basic plural handling
    if cleaned.endswith('s'):
        cleaned = cleaned[:-1]
    return cleaned.strip()


def find_closest_exercise_debug(target_exercise: str, available_exercises: list) -> tuple:
    """Debug version of the fuzzy matching algorithm"""
    print(f"\n=== DEBUGGING EXERCISE MATCH FOR: '{target_exercise}' ===")

    # Define confused exercise pairs
    confused_exercise_pairs = [
        ('lat pulldown', 'chin up'),
        ('lat pull down', 'chin up'),
        ('pulldown', 'chin up'),
        ('pull down', 'chin up'),
        ('lat pulldown', 'pull up'),
        ('lat pull down', 'pull up'),
        ('pulldown', 'pull up'),
        ('pull down', 'pull up'),
    ]

    target_clean = clean_name(target_exercise)
    best_match = None
    best_ratio = 0
    all_scores = []

    print(f"Target cleaned: '{target_clean}'")

    # Check if target exercise is in a confused pair
    is_confused_exercise = False
    for pair in confused_exercise_pairs:
        if target_clean in pair:
            is_confused_exercise = True
            print(
                f"⚠️  WARNING: '{target_exercise}' is in confused exercise pair: {pair}")
            break

    print(f"\nAvailable exercises ({len(available_exercises)}):")
    for i, ex in enumerate(available_exercises, 1):
        print(f"  {i}. {ex}")

    print(f"\n--- DETAILED MATCHING ANALYSIS ---")

    for exercise in available_exercises:
        exercise_clean = clean_name(exercise)

        # Check for exact matches first (highest priority)
        if target_clean == exercise_clean:
            print(f"✅ EXACT MATCH: '{target_exercise}' -> '{exercise}'")
            return exercise, 1.0, "EXACT_MATCH"

        # Safety check for confused exercises
        safety_blocked = False
        if is_confused_exercise:
            for pair in confused_exercise_pairs:
                if exercise_clean in pair and target_clean in pair:
                    safety_blocked = True
                    print(
                        f"🚫 SAFETY BLOCK: Prevented match between '{target_exercise}' and '{exercise}' (confused pair)")
                    break

        if safety_blocked:
            continue

        # Calculate matching scores
        target_words = set(target_clean.split())
        exercise_words = set(exercise_clean.split())

        if len(target_words) > 0:
            word_match_ratio = len(target_words.intersection(
                exercise_words)) / len(target_words)
        else:
            word_match_ratio = 0

        # Calculate character similarity
        char_match = 0
        for i in range(min(len(target_clean), len(exercise_clean))):
            if target_clean[i] == exercise_clean[i]:
                char_match += 1
        char_ratio = char_match / max(len(target_clean), len(exercise_clean)) if max(
            len(target_clean), len(exercise_clean)) > 0 else 0

        # Length penalty
        length_diff = abs(len(target_clean) - len(exercise_clean))
        max_length = max(len(target_clean), len(exercise_clean))
        length_penalty = length_diff / max_length if max_length > 0 else 1

        # Combined score
        match_ratio = (word_match_ratio * 0.7) + \
            (char_ratio * 0.3) - (length_penalty * 0.2)

        # Store all scores for analysis
        all_scores.append({
            'exercise': exercise,
            'exercise_clean': exercise_clean,
            'word_match': word_match_ratio,
            'char_match': char_ratio,
            'length_penalty': length_penalty,
            'final_score': match_ratio,
            'target_words': target_words,
            'exercise_words': exercise_words
        })

        print(f"\n🔍 '{exercise}' (cleaned: '{exercise_clean}')")
        print(f"   Target words: {target_words}")
        print(f"   Exercise words: {exercise_words}")
        print(f"   Word overlap: {target_words.intersection(exercise_words)}")
        print(f"   Word match: {word_match_ratio:.3f}")
        print(f"   Char match: {char_ratio:.3f}")
        print(f"   Length penalty: {length_penalty:.3f}")
        print(f"   Final score: {match_ratio:.3f}")

        if match_ratio > best_ratio:
            best_ratio = match_ratio
            best_match = exercise

    # Sort by score for analysis
    all_scores.sort(key=lambda x: x['final_score'], reverse=True)

    print(f"\n--- FINAL RANKING ---")
    for i, score in enumerate(all_scores[:5], 1):  # Show top 5
        print(f"{i}. {score['exercise']} - Score: {score['final_score']:.3f}")

    # Determine threshold
    threshold = 0.9 if is_confused_exercise else 0.7

    print(f"\n--- FINAL DECISION ---")
    print(f"Best match: '{best_match}' with score {best_ratio:.3f}")
    print(
        f"Threshold: {threshold} (confused exercise: {is_confused_exercise})")

    if best_match and best_ratio > threshold:
        print(f"✅ MATCH ACCEPTED: '{target_exercise}' -> '{best_match}'")
        return best_match, best_ratio, "FUZZY_MATCH"
    else:
        print(
            f"❌ MATCH REJECTED: Score {best_ratio:.3f} below threshold {threshold}")
        return None, best_ratio, "NO_MATCH"


def main():
    """Test common problematic exercise matching scenarios"""

    # Test case 1: The reported problem
    print("🧪 TEST CASE 1: Lat Pulldown vs Chin Up")
    available_exercises_1 = [
        "Lat Pulldown Wide Grip",
        "Chin Up",
        "Pull Up",
        "Barbell Row",
        "Seated Cable Row"
    ]

    print("\n" + "="*60)
    result1 = find_closest_exercise_debug(
        "Lat Pulldown", available_exercises_1)

    print("\n" + "="*60)
    result2 = find_closest_exercise_debug("Chin Up", available_exercises_1)

    # Test case 2: Similar exercises
    print("\n\n🧪 TEST CASE 2: Similar Exercise Names")
    available_exercises_2 = [
        "Chest Press Machine",
        "Chest Fly Machine",
        "Bench Press",
        "Incline Press"
    ]

    print("\n" + "="*60)
    result3 = find_closest_exercise_debug("Chest Press", available_exercises_2)

    print("\n" + "="*60)
    result4 = find_closest_exercise_debug("Chest Fly", available_exercises_2)

    # Test case 3: Variations in naming
    print("\n\n🧪 TEST CASE 3: Naming Variations")
    available_exercises_3 = [
        "Dumbbell Bicep Curl",
        "Barbell Bicep Curl",
        "Hammer Curl",
        "Concentration Curl"
    ]

    print("\n" + "="*60)
    result5 = find_closest_exercise_debug("Bicep Curl", available_exercises_3)

    print("\n" + "="*60)
    result6 = find_closest_exercise_debug(
        "DB Bicep Curl", available_exercises_3)

    # Summary
    print("\n\n📊 SUMMARY OF RESULTS")
    print("="*60)
    test_cases = [
        ("Lat Pulldown", result1),
        ("Chin Up", result2),
        ("Chest Press", result3),
        ("Chest Fly", result4),
        ("Bicep Curl", result5),
        ("DB Bicep Curl", result6)
    ]

    for test_name, (match, score, match_type) in test_cases:
        status = "✅" if match else "❌"
        print(
            f"{status} {test_name:15} -> {match or 'NO_MATCH':25} ({score:.3f}) [{match_type}]")


if __name__ == "__main__":
    main()
