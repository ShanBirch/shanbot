import re

file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\checkin_current.py"

# Read the file content
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Search for the function definition
pattern = r'def update_json_files_with_most_improved\(.*?\):.*?(?=def|\Z)'
matches = re.search(pattern, content, re.DOTALL)

if matches:
    function_code = matches.group(0)
    print("Function found!")
    print("-" * 80)
    print(function_code)
    print("-" * 80)
else:
    print("Function not found!")

# Find the part where it searches for JSON files
json_search_pattern = r'.*?JSON file.*?client:'
json_matches = re.findall(json_search_pattern, content, re.DOTALL)

if json_matches:
    print("\nJSON file references found:")
    # Show only first 5 matches to keep output manageable
    for match in json_matches[:5]:
        print(match.strip())
else:
    print("\nNo JSON file references found!")
