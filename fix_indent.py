#!/usr/bin/env python3

# Read the file
with open('potential_clients_story_commentor.py', 'r') as f:
    content = f.read()

# Fix the indentation issue on line 207
# Replace the over-indented "if" with properly indented "if"
content = content.replace(
    '                                                        if \'stories/\' in current_url or \'highlights/\' in current_url:',
    '                            if \'stories/\' in current_url or \'highlights/\' in current_url:'
)

# Write back the fixed content
with open('potential_clients_story_commentor.py', 'w') as f:
    f.write(content)

print("Fixed indentation error in potential_clients_story_commentor.py")
