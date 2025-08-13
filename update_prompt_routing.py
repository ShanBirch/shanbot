#!/usr/bin/env python3

# Script to update webhook routing to use paid challenge prompt

import re

# Read the webhook file
with open('webhook0605.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the prompt template reference
old_pattern = r"prompt = prompts\.PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE\.format\(\s*current_melbourne_time_str=current_time,\s*ig_username=ig_username,\s*challenge_type=challenge_type,\s*script_state=current_state,\s*bio=bio_context,\s*full_conversation=full_conversation\s*\)"

new_replacement = """prompt = prompts.PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE.format(
                current_melbourne_time_str=current_time,
                ig_username=ig_username,
                script_state=current_state,
                initial_trigger='direct_comment',  # Will be updated based on ManyChat button selection
                bio=bio_context,
                full_conversation=full_conversation
            )"""

# Check if we find the pattern
if re.search(old_pattern, content, re.MULTILINE | re.DOTALL):
    print("✅ Found the old prompt pattern")
    # Replace it
    updated_content = re.sub(old_pattern, new_replacement,
                             content, flags=re.MULTILINE | re.DOTALL)

    # Write back to file
    with open('webhook0605.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("✅ Successfully updated webhook routing to use PAID_VEGAN_CHALLENGE_PROMPT_TEMPLATE")
else:
    print("❌ Could not find the old prompt pattern")
    # Let's search for any PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE references
    if "PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE" in content:
        print("Found PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE references in file")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE" in line:
                print(f"Line {i}: {line.strip()}")
    else:
        print("No PLANT_BASED_CHALLENGE_PROMPT_TEMPLATE references found")

print("\nDone!")
