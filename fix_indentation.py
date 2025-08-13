#!/usr/bin/env python3
"""
Quick fix script for indentation errors in smart_lead_finder.py
"""


def fix_smart_lead_finder():
    """Fix the indentation issues in smart_lead_finder.py"""

    # Read the original file
    with open('smart_lead_finder.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Fix specific line issues
    fixes = [
        # Line around 591 - fix indentation for online mode parsing
        (590, 591),  # Lines to replace
        # Line around 1027 - fix for loop indentation
        (1026, 1027)
    ]

    # Apply fixes
    for i, line in enumerate(lines):
        line_num = i + 1

        # Fix the online mode parsing section around line 591
        if line_num == 591 and line.strip().startswith('is_business_or_coach'):
            lines[
                i] = '                is_business_or_coach, business_evidence = parse_line(\n'

        # Fix line 1027 - missing indentation for if statement
        if line_num == 1027 and 'if self.get_daily_follows_count()' in line:
            lines[i] = '                    if self.get_daily_follows_count() >= DAILY_FOLLOW_LIMIT:\n'

        # Fix any other indentation issues on these lines
        if line_num in [595, 597, 599, 607, 617, 635, 638, 642, 646, 649, 651, 652, 653, 656]:
            # Remove excessive indentation and normalize
            content = line.lstrip()
            if content.strip():  # Only if line has content
                if 'apparent_gender' in content or 'is_target_female' in content or 'is_target_male' in content:
                    lines[i] = '                ' + content
                elif 'if (' in content or 'print(' in content or 'self.leads_found' in content:
                    lines[i] = '                ' + content
                elif 'else:' in content:
                    lines[i] = '                else:\n'
                elif content.startswith('#'):
                    lines[i] = '                ' + content

    # Write the fixed file
    with open('smart_lead_finder.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("✅ Fixed indentation issues in smart_lead_finder.py")


if __name__ == "__main__":
    fix_smart_lead_finder()
