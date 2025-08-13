#!/usr/bin/env python

"""
Run the Fitness Video Auto-Labeler GUI with improved error handling.
This script ensures that errors are caught and displayed properly without crashing.
"""

import sys
import traceback
import os
import importlib.util

# Function to check if a module is installed


def is_module_installed(module_name):
    spec = importlib.util.find_spec(module_name)
    return spec is not None


# Check for required dependencies
required_modules = [
    'moviepy', 'tkinter', 'PIL', 'numpy'
]

missing_modules = []
for module in required_modules:
    if not is_module_installed(module):
        missing_modules.append(module)

if missing_modules:
    print(
        f"ERROR: The following required modules are missing: {', '.join(missing_modules)}")
    print("Please install them with pip:")
    print(f"pip install {' '.join(missing_modules)}")
    input("Press Enter to exit...")
    sys.exit(1)

# Set up global exception handler


def show_error(exception_type, exception_value, exception_traceback):
    error_msg = "".join(traceback.format_exception(
        exception_type, exception_value, exception_traceback))
    print(f"ERROR: Unhandled exception: {error_msg}")

    # Try to show a message box
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Application Error",
                             f"An error occurred:\n\n{exception_value}\n\nSee console for details.")
        root.destroy()
    except:
        # If messagebox fails, just print to console
        print("Could not display error dialog. See error details above.")
        input("Press Enter to exit...")


# Install the global error handler
sys.excepthook = show_error

try:
    print("Starting Fitness Video Auto-Labeler with improved error handling...")
    # Import the patch first
    try:
        import text_overlay_patch
        print("Text overlay patch loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load text overlay patch: {e}")

    # Import and run the main application
    import fixed_video_auto_labeler_gui
    print("Application loaded successfully.")

    # Run the application
    if __name__ == "__main__":
        import tkinter as tk
        root = tk.Tk()
        app = fixed_video_auto_labeler_gui.VideoAutoLabelerGUI(root)
        root.mainloop()

except Exception as e:
    print(f"ERROR in startup: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)
