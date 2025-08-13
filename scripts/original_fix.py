#!/usr/bin/env python

import os
import sys
import re
from pathlib import Path


def fix_indentation_in_fwv():
    """Fix indentation errors in the fwv.py file"""
    print("Fixing indentation in fwv.py...")

    # Path to the original file
    fwv_path = "fwv.py"

    # Read the file
    with open(fwv_path, "r") as f:
        lines = f.readlines()

    # Fix known indentation issue around line 939
    fixed_lines = []
    in_slide_up_function = False
    prev_indent = ""

    for i, line in enumerate(lines):
        # Keep track of indentation level
        indent = re.match(r"^(\s*)", line).group(1)

        # Fix the specific indentation issues we know about
        if "strength_gains_text = [" in line and i > 900:
            # This is where the error starts, adjust indentation
            prev_indent = indent
            line = "                    strength_gains_text = [\n"
        elif "slide_up(t)" in line:
            # Start of the slide_up function
            in_slide_up_function = True
        elif in_slide_up_function and "return (x_pos, current_y)" in line:
            # Fix indentation inside slide_up function
            line = "                                            return (x_pos, current_y)\n"
        elif in_slide_up_function and "return (x_pos, end_y)" in line:
            # Fix indentation inside slide_up function
            line = "                                            return (x_pos, end_y)\n"
        elif "else:" in line and prev_indent and len(indent) < len(prev_indent) and i > 600:
            # Fix misaligned else statements
            line = prev_indent + "else:\n"
        elif "try:" in line and i > 630 and i < 650:
            # Fix the try statement that's missing except or finally
            fixed_lines.append(line)
            fixed_lines.append("            slides = []\n")
            continue
        elif "return True" in line and i > 680 and i < 690:
            # Fix return true indentation
            line = "            return True\n"
        elif "except Exception as e:" in line and i > 680 and i < 700:
            # Fix except statement indentation
            line = "        except Exception as e:\n"
        elif "print(f\"Error creating video: {str(e)}\")" in line:
            # Fix print statement indentation
            line = "            print(f\"Error creating video: {str(e)}\")\n"
        elif "return False" in line and i > 690 and i < 700:
            # Fix return false indentation
            line = "            return False\n"

        # Continue tracking indentation
        if line.strip() and not line.strip().startswith("#"):
            prev_indent = indent

        fixed_lines.append(line)

    # Write the fixed file
    fixed_path = "fixed_fwv.py"
    with open(fixed_path, "w") as f:
        f.writelines(fixed_lines)

    print(f"Fixed file written to {fixed_path}")
    return fixed_path


def add_music_selection(fixed_fwv_path):
    """Add music selection method to the fixed fwv.py file"""
    print("Adding music selection functionality...")

    # Read the fixed file
    with open(fixed_fwv_path, "r") as f:
        lines = f.readlines()

    # Find the right place to insert the select_random_music method
    # (after __init__ but before other methods)
    insert_index = 0
    for i, line in enumerate(lines):
        if "def __init__" in line:
            # Find the end of the __init__ method
            init_indent = re.match(r"^(\s*)", line).group(1)

            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                next_indent = re.match(r"^(\s*)", next_line).group(1)

                # If we find a line with the same indentation as __init__,
                # that's the start of the next method
                if next_indent == init_indent and "def " in next_line:
                    insert_index = j
                    break

            if insert_index > 0:
                break

    if insert_index == 0:
        print("Warning: Couldn't find a good place to insert select_random_music method")
        insert_index = len(lines) // 4  # Insert somewhere in the first quarter

    # Create the select_random_music method
    select_random_music_method = [
        "    def select_random_music(self):\n",
        "        \"\"\"Select a random music file from the music directory\"\"\"\n",
        "        # Get all mp3 files in the music directory\n",
        "        mp3_files = list(self.music_dir.glob(\"*.mp3\"))\n",
        "\n",
        "        # If no mp3 files found, return the default music path\n",
        "        if not mp3_files:\n",
        "            print(\"No music files found. Using default.\")\n",
        "            return self.music_path\n",
        "\n",
        "        # Select a random music file\n",
        "        random_music = random.choice(mp3_files)\n",
        "        print(f\"Selected random music track: {random_music.name}\")\n",
        "        return random_music\n",
        "\n"
    ]

    # Modify the build_video method to use the select_random_music method
    build_video_index = 0
    for i, line in enumerate(lines):
        if "def build_video" in line:
            build_video_index = i
            break

    if build_video_index > 0:
        # Find where to add the music selection in the build_video method
        for i in range(build_video_index, len(lines)):
            if "self.music_path" in lines[i]:
                # Replace the line that uses self.music_path
                lines[i] = lines[i].replace(
                    "self.music_path", "self.select_random_music()")
                break

    # Insert the select_random_music method
    modified_lines = lines[:insert_index] + \
        select_random_music_method + lines[insert_index:]

    # Write the modified file
    modified_path = "fixed_fwv_with_music.py"
    with open(modified_path, "w") as f:
        f.writelines(modified_lines)

    print(f"Added music selection functionality to {modified_path}")
    return modified_path


def create_runner_script(modified_fwv_path):
    """Create a runner script to use the fixed fwv.py file"""
    print("Creating runner script...")

    runner_script = [
        "#!/usr/bin/env python\n",
        "\n",
        "import json\n",
        "import os\n",
        "from pathlib import Path\n",
        "import importlib.util\n",
        "\n",
        "def main():\n",
        "    print(\"Running video generator with original code plus music selection...\")\n",
        "\n",
        "    # Load the client data from the JSON file\n",
        "    json_path = \"Shannon_Birch_fitness_wrapped_data.json\"\n",
        "    with open(json_path, 'r') as f:\n",
        "        client_data = json.load(f)\n",
        "\n",
        f"    print(f\"Loaded client data for: {{client_data.get('name', 'unknown client')}}\")\n",
        "\n",
        "    # Load the modified module\n",
        f"    spec = importlib.util.spec_from_file_location(\"fixed_fwv\", \"{modified_fwv_path}\")\n",
        "    fixed_fwv = importlib.util.module_from_spec(spec)\n",
        "    spec.loader.exec_module(fixed_fwv)\n",
        "\n",
        "    # Create the generator instance\n",
        "    generator = fixed_fwv.FitnessWrappedGenerator(client_data)\n",
        "\n",
        "    # Generate the video\n",
        "    print(\"Building fitness wrapped video with original approach...\")\n",
        "    result = generator.build_video()\n",
        "\n",
        "    if result:\n",
        "        print(f\"Success! Video created and saved to: {generator.output_path}\")\n",
        "    else:\n",
        "        print(\"Error: Failed to create video.\")\n",
        "\n",
        "if __name__ == \"__main__\":\n",
        "    main()\n"
    ]

    # Write the runner script
    runner_path = "original_video.py"
    with open(runner_path, "w") as f:
        f.writelines(runner_script)

    print(f"Created runner script: {runner_path}")
    return runner_path

# Main function


def main():
    print("Starting restoration of original video generator with music...")

    # Step 1: Fix indentation in fwv.py
    fixed_fwv_path = fix_indentation_in_fwv()

    # Step 2: Add music selection to fixed fwv.py
    modified_fwv_path = add_music_selection(fixed_fwv_path)

    # Step 3: Create a runner script
    runner_path = create_runner_script(modified_fwv_path)

    print("All done! Now you can run the original video generator with music selection:")
    print(f"  python {runner_path}")

    # Run the runner script automatically
    print("\nRunning the video generator now...")
    os.system(f"python {runner_path}")


if __name__ == "__main__":
    main()
