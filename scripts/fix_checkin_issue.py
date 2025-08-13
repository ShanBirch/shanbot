import os
import sys


def fix_checkin_file():
    """Fix the checkin.py file to work with run_checkin.py"""
    try:
        # Read the checkin.py file
        with open('checkin.py', 'r') as f:
            lines = f.readlines()

        # Find the problematic section
        client_names_line = -1
        for i, line in enumerate(lines):
            if "for client_idx, client_name in enumerate(client_names" in line:
                client_names_line = i
                break

        if client_names_line == -1:
            print("Could not find the problematic line in checkin.py")
            return False

        # Create a new version of the file
        with open('checkin_fixed.py', 'w') as f:
            # Write all lines up to the statistics section
            # Skip a few lines before the problematic code
            for i in range(client_names_line - 5):
                f.write(lines[i])

            # Add the new code
            f.write("\n# This code only runs when the script is executed directly\n")
            f.write("if __name__ == \"__main__\":\n")
            f.write("    # Example client list for direct execution\n")
            f.write("    client_names = [\"Shannon Birch\", \"Ben Pryke\"]\n")
            f.write("    print(\"\\n\" + \"=\"*100)\n")
            f.write(
                "    print(\"                          FINAL WORKOUT STATISTICS SUMMARY FOR ALL CLIENTS\")\n")
            f.write("    print(\"=\"*100)\n\n")

            # Add the remaining code but indented
            for i in range(client_names_line - 5, len(lines)):
                f.write("    " + lines[i])  # Indent the line

        print("✓ Successfully created a fixed version at checkin_fixed.py")
        print("Please rename checkin_fixed.py to checkin.py and try running again")
        return True

    except Exception as e:
        print(f"Error fixing checkin.py: {e}")
        return False


if __name__ == "__main__":
    fix_checkin_file()
