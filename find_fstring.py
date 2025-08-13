import os
import re


def find_problematic_fstrings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if 'f"' in line or "f'" in line:
                if '\\' in line:
                    print(f"Line {i}: {line.strip()}")


target_file = os.path.join(
    'app', 'dashboard_modules', 'scheduled_followups.py')
print(f"Checking {target_file}")
find_problematic_fstrings(target_file)
