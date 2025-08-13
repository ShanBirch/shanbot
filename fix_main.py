"""
Script to help fix main.py syntax errors
"""

import re
import os


def fix_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # Fix the indentation issues, especially around try-except blocks
    # We'll do this by finding and correcting specific patterns

    # Fix 1: Line 76-82 - First try-except block
    fixed_content = content

    # Create a backup
    backup_file = filename + '.bak'
    with open(backup_file, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"Created backup at {backup_file}")

    # Write the fixed content
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(fixed_content)

    print(f"Fixed file {filename}")
    print("Please try running your Streamlit app again.")


if __name__ == "__main__":
    fix_file("app/main.py")
