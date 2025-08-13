#!/usr/bin/env python3
"""
Comprehensive fix for smart_lead_finder.py indentation issues
"""


def fix_smart_lead_finder():
    """Fix all indentation issues in smart_lead_finder.py"""

    # Read the file
    with open('smart_lead_finder.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into lines
    lines = content.split('\n')

    # Fix the major problematic section around line 590-665
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1

        # Fix the else block for online mode parsing (around line 589-665)
        if line_num == 589 and line.strip() == 'else:':
            # Replace the entire problematic section
            fixed_lines.append('            else:')
            fixed_lines.append(
                '                # Online mode parsing (existing logic)')
            fixed_lines.append(
                '                is_business_or_coach, business_evidence = parse_line(')
            fixed_lines.append(
                "                    'IS_BUSINESS_OR_COACH', response_text)")
            fixed_lines.append(
                '                is_plant_based, plant_evidence = parse_line(')
            fixed_lines.append(
                "                    'IS_PLANT_BASED', response_text)")
            fixed_lines.append(
                '                apparent_gender, gender_evidence = parse_line(')
            fixed_lines.append(
                "                    'APPARENT_GENDER', response_text)")
            fixed_lines.append(
                '                is_target_female, female_evidence = parse_line(')
            fixed_lines.append(
                "                    'IS_TARGET_FEMALE', response_text)")
            fixed_lines.append(
                '                is_target_male, male_evidence = parse_line(')
            fixed_lines.append(
                "                    'IS_TARGET_MALE', response_text)")
            fixed_lines.append(
                '                is_potential_client, client_reason = parse_line(')
            fixed_lines.append(
                "                    'FINAL_VERDICT_POTENTIAL_CLIENT', response_text)")
            fixed_lines.append(
                '                is_fake, fake_evidence = parse_line(')
            fixed_lines.append(
                "                    'IS_FAKE_OR_INACTIVE', response_text)")
            fixed_lines.append('')
            fixed_lines.append(
                '                # Check for AI analysis issues')
            fixed_lines.append(
                '                if ("No evidence found" in business_evidence or')
            fixed_lines.append(
                '                    "No evidence found" in plant_evidence or')
            fixed_lines.append(
                '                        "Cannot determine clearly" in business_evidence):')
            fixed_lines.append('                    print(')
            fixed_lines.append(
                '                        f"⚠️ AI may not be seeing profile clearly for {username}")')
            fixed_lines.append('                    print(')
            fixed_lines.append(
                '                        f"🔍 Raw AI response preview: {response_text[:200]}...")')
            fixed_lines.append('')
            fixed_lines.append(
                '                # STRICT vegan/plant-based criteria as requested')
            fixed_lines.append(
                '                # Only accept people who are clearly vegan/plant-based')
            fixed_lines.append(
                '                is_clearly_vegan_or_plant_based = (')
            fixed_lines.append(
                "                    is_plant_based == 'YES' or")
            fixed_lines.append(
                "                    'plant' in plant_evidence.lower() or")
            fixed_lines.append(
                "                    'vegan' in plant_evidence.lower() or")
            fixed_lines.append(
                "                    'plantbased' in plant_evidence.lower() or")
            fixed_lines.append(
                "                    'plant-based' in plant_evidence.lower()")
            fixed_lines.append('                )')
            fixed_lines.append('')
            fixed_lines.append(
                "                is_potential = (is_business_or_coach != 'YES' and")
            fixed_lines.append(
                '                                is_clearly_vegan_or_plant_based and')
            fixed_lines.append(
                "                                (is_target_female == 'YES' or is_target_male == 'YES') and")
            fixed_lines.append(
                "                                is_fake != 'YES')")
            fixed_lines.append('')
            fixed_lines.append(
                '                # Show the AI\'s reasoning (updated format)')
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   🏢 Business/Coach: {'❌ YES' if is_business_or_coach == 'YES' else '✅ NO'} - {business_evidence}\")")
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   🌱 Plant-Based: {'✅ YES' if is_plant_based == 'YES' else '❌ NO'} - {plant_evidence}\")")
            fixed_lines.append(
                '                print(f"   👤 Gender: {apparent_gender} - {gender_evidence}")')
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   👩 Target Female: {'✅ YES' if is_target_female == 'YES' else '❌ NO/N/A'} - {female_evidence}\")")
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   👨 Target Male: {'✅ YES' if is_target_male == 'YES' else '❌ NO/N/A'} - {male_evidence}\")")
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   🤖 Fake/Inactive: {'❌ YES' if is_fake == 'YES' else '✅ NO'} - {fake_evidence}\")")
            fixed_lines.append('                print(')
            fixed_lines.append(
                "                    f\"   🎯 AI Final Verdict: {'✅ YES' if is_potential_client == 'YES' else '❌ NO'} - {client_reason}\")")
            fixed_lines.append('')
            fixed_lines.append(
                "                # Use AI's final verdict if our logic says potential but AI says no")
            fixed_lines.append(
                "                if is_potential_client == 'YES' or is_potential:")
            fixed_lines.append(
                '                    print(f"✅ POTENTIAL CLIENT FOUND: {username}")')
            fixed_lines.append(
                '                    print(f"   💡 Final verdict: {client_reason}")')
            fixed_lines.append('                    self.leads_found += 1')
            fixed_lines.append('                    return True')
            fixed_lines.append('                else:')
            fixed_lines.append(
                '                    print(f"❌ Not a potential client: {username}")')
            fixed_lines.append(
                '                    print(f"   💡 Reason: {client_reason}")')
            fixed_lines.append('')
            fixed_lines.append(
                '                    # Debug: Show why they failed our criteria')
            fixed_lines.append(
                "                    if is_business_or_coach == 'YES':")
            fixed_lines.append(
                '                        print(f"   🚫 Failed: Is a business/coach")')
            fixed_lines.append(
                '                    elif not is_clearly_vegan_or_plant_based:')
            fixed_lines.append(
                '                        print(f"   🚫 Failed: Not clearly vegan/plant-based")')
            fixed_lines.append(
                "                    elif is_target_female != 'YES' and is_target_male != 'YES':")
            fixed_lines.append(
                '                        print(f"   🚫 Failed: Doesn\'t fit target demographic")')
            fixed_lines.append("                    elif is_fake == 'YES':")
            fixed_lines.append(
                '                        print(f"   🚫 Failed: Appears fake/inactive")')
            fixed_lines.append('')
            fixed_lines.append('                    return False')

            # Skip all the problematic lines until we reach the exception handler
            while i < len(lines) and 'except Exception as e:' not in lines[i]:
                i += 1
            i -= 1  # Back up one to include the except line

        # Fix the for loop indentation issue around line 1026-1027
        elif line_num >= 1026 and 'for hashtag in target_hashtags:' in line:
            fixed_lines.append(
                '                for hashtag in target_hashtags:')
            fixed_lines.append(
                '                    if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:')
            fixed_lines.append('                        break')
            fixed_lines.append('')
            fixed_lines.append(
                '                    self.search_hashtag_for_leads(hashtag, max_to_check=10)')

            # Skip the next few lines that are problematic
            while i < len(lines) and 'time.sleep(random.uniform(10, 20))' not in lines[i]:
                i += 1

        else:
            # Keep all other lines as-is
            fixed_lines.append(line)

        i += 1

    # Write the fixed content
    with open('smart_lead_finder.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))

    print("✅ Fixed all indentation issues in smart_lead_finder.py")


if __name__ == "__main__":
    fix_smart_lead_finder()
