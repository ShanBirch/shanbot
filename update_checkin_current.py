import re
import os

# File path
file_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\checkin_current.py"
output_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\checkin_current.py.new"

# New path for JSON files
new_json_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"

# Read the file content
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Function to find and update code that saves JSON files


def update_json_file_path(text):
    # Look for patterns that write to or read from JSON files

    # Pattern 1: Save fitness wrapped data function
    save_data_pattern = r'def save_fitness_wrapped_data\(self, client_name, fitness_wrapped_data\):(.*?return json_filename)'
    save_data_match = re.search(save_data_pattern, text, re.DOTALL)

    if save_data_match:
        save_data_code = save_data_match.group(0)
        # Check if it already uses the checkin_reviews path
        if "output/checkin_reviews" not in save_data_code and "output\\\\checkin_reviews" not in save_data_code:
            # Update the code to use the new path
            updated_save_data_code = save_data_code.replace(
                'json_filename = f"{client_name.replace(" ", "_")}_{date_str}_fitness_wrapped_data.json"',
                'output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "checkin_reviews")\n'
                '        os.makedirs(output_dir, exist_ok=True)\n'
                '        json_filename = os.path.join(output_dir, f"{client_name.replace(" ", "_")}_{date_str}_fitness_wrapped_data.json")'
            )
            text = text.replace(save_data_code, updated_save_data_code)

    # Pattern 2: Update JSON files with most improved
    most_improved_pattern = r'def update_json_files_with_most_improved\(all_clients_data, most_improved_info\):(.*?)return True'
    most_improved_match = re.search(most_improved_pattern, text, re.DOTALL)

    if most_improved_match:
        most_improved_code = most_improved_match.group(0)
        # Check if it already uses the checkin_reviews path
        if "output/checkin_reviews" not in most_improved_code and "output\\\\checkin_reviews" not in most_improved_code:
            # Update the code to use the new path in the file search pattern
            updated_most_improved_code = most_improved_code.replace(
                'json_file_pattern = f"{client_name.replace(" ", "_")}*_fitness_wrapped_data.json"',
                'output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "checkin_reviews")\n'
                '        json_file_pattern = os.path.join(output_dir, f"{client_name.replace(" ", "_")}*_fitness_wrapped_data.json")'
            )
            text = text.replace(most_improved_code, updated_most_improved_code)

    return text


# Apply the update
updated_content = update_json_file_path(content)

# Write the updated content back to a new file
with open(output_path, 'w', encoding='utf-8') as file:
    file.write(updated_content)

print(f"Updated file saved to: {output_path}")
print("Review the changes and then rename the file to replace the original.")
