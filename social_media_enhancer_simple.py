"""
Social Media Enhancer for Fitness Videos (Simple Version)
Adds professional social media optimizations for text overlays and animations
"""

import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Import the text overlay patch
try:
    from text_overlay_patch_fixed import enhance_video
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure text_overlay_patch_fixed.py is in the same directory.")
    sys.exit(1)


def create_ui_and_process_video():
    """Create a simple UI for selecting options and process the video directly."""

    # Function to process video when button is clicked
    def process_video():
        # Get the selected options
        video_path = path_var.get()
        text_style = text_style_var.get()
        background_effect = bg_var.get()
        color_grade = color_var.get()

        # Validate video path
        if not video_path or video_path == "No video selected":
            tk.messagebox.showerror(
                "Error", "Please select a video file first.")
            return

        # Close the UI
        root.destroy()

        # Process the video
        print(f"\nEnhancing video with social media optimizations...")
        print(f"- Text Style: {text_style}")
        print(f"- Background: {background_effect}")
        print(f"- Color Grade: {color_grade}")

        try:
            # Use our imported enhance_video function
            output_path = enhance_video(
                video_path,
                text_style=text_style,
                background_effect=background_effect,
                color_grade=color_grade
            )

            if output_path:
                print(f"\nSuccess! Enhanced video saved to: {output_path}")

                # Open the video for preview
                try:
                    import platform
                    import subprocess

                    if platform.system() == 'Windows':
                        os.startfile(output_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.call(('open', output_path))
                    else:  # linux
                        subprocess.call(('xdg-open', output_path))

                    print("Opening video for preview...")
                except Exception as e:
                    print(f"Could not automatically open the video: {e}")
            else:
                print("Failed to enhance video. Please check the error messages above.")
        except Exception as e:
            print(f"Error enhancing video: {e}")
            traceback.print_exc()

    # Create the main window
    root = tk.Tk()
    root.title("Social Media Video Enhancer")
    root.geometry("500x550")
    root.configure(bg="#f0f0f0")

    # Add a header
    header_frame = tk.Frame(root, bg="#333333", padx=10, pady=10)
    header_frame.pack(fill=tk.X)

    title_label = tk.Label(
        header_frame,
        text="SOCIAL MEDIA VIDEO ENHANCER",
        font=("Arial", 16, "bold"),
        fg="white",
        bg="#333333"
    )
    title_label.pack()

    subtitle_label = tk.Label(
        header_frame,
        text="Make your fitness videos stand out on social media",
        font=("Arial", 10),
        fg="#cccccc",
        bg="#333333"
    )
    subtitle_label.pack(pady=(0, 5))

    # Main content frame
    content_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Video selection
    file_frame = tk.LabelFrame(
        content_frame,
        text="Select Video",
        font=("Arial", 11, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    file_frame.pack(fill=tk.X, pady=(0, 15))

    path_var = tk.StringVar(value="No video selected")

    path_label = tk.Label(
        file_frame,
        textvariable=path_var,
        bg="#f0f0f0",
        fg="#333333",
        font=("Arial", 10),
        wraplength=400
    )
    path_label.pack(fill=tk.X, pady=(0, 10))

    def browse_video():
        file_path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv")]
        )
        if file_path:
            path_var.set(file_path)

    browse_button = ttk.Button(
        file_frame,
        text="Browse for Video",
        command=browse_video
    )
    browse_button.pack(pady=(0, 5))

    # Text style options
    style_frame = tk.LabelFrame(
        content_frame,
        text="Text Style",
        font=("Arial", 11, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    style_frame.pack(fill=tk.X, pady=(0, 15))

    text_style_var = tk.StringVar(value="bold_statement")

    styles = [
        ("Bold Statement (Impact Font)", "bold_statement"),
        ("Instagram Classic", "instagram_classic"),
        ("Fitness Pro", "fitness_pro"),
        ("Minimal Clean", "minimal"),
        ("Instagram Story", "instagram_story")
    ]

    for text, val in styles:
        radio = ttk.Radiobutton(
            style_frame,
            text=text,
            value=val,
            variable=text_style_var
        )
        radio.pack(anchor=tk.W, pady=2)

    # Background effect options
    bg_frame = tk.LabelFrame(
        content_frame,
        text="Background Effect",
        font=("Arial", 11, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    bg_frame.pack(fill=tk.X, pady=(0, 15))

    bg_var = tk.StringVar(value="gradient_bar")

    backgrounds = [
        ("Gradient Bar", "gradient_bar"),
        ("Solid Bar", "solid_bar"),
        ("Blur Box", "blur_box"),
        ("Shadow Lift", "shadow_lift"),
        ("None (Text Only)", "none")
    ]

    for text, val in backgrounds:
        radio = ttk.Radiobutton(
            bg_frame,
            text=text,
            value=val,
            variable=bg_var
        )
        radio.pack(anchor=tk.W, pady=2)

    # Color grading options
    color_frame = tk.LabelFrame(
        content_frame,
        text="Color Grading",
        font=("Arial", 11, "bold"),
        bg="#f0f0f0",
        padx=10,
        pady=10
    )
    color_frame.pack(fill=tk.X, pady=(0, 15))

    color_var = tk.StringVar(value="fitness")

    colors = [
        ("Fitness (High Contrast)", "fitness"),
        ("Cinematic", "cinematic"),
        ("Vibrant", "vibrant"),
        ("Moody", "moody"),
        ("None (Original Colors)", "none")
    ]

    for text, val in colors:
        radio = ttk.Radiobutton(
            color_frame,
            text=text,
            value=val,
            variable=color_var
        )
        radio.pack(anchor=tk.W, pady=2)

    # Process button
    button_frame = tk.Frame(root, bg="#f0f0f0", pady=15)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    process_button = ttk.Button(
        button_frame,
        text="ENHANCE VIDEO",
        command=process_video
    )
    process_button.pack(pady=10, padx=20, ipadx=10, ipady=5, fill=tk.X)

    # Button styling
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"))

    # Run the UI
    root.mainloop()


def main():
    """Main function to run the social media enhancer."""
    print("╔═════════════════════════════════════════════════╗")
    print("║  Social Media Enhancer for Fitness Videos       ║")
    print("║  Create eye-catching videos optimized for       ║")
    print("║  Instagram, TikTok, and other platforms         ║")
    print("╚═════════════════════════════════════════════════╝")

    try:
        # Create UI and process video
        create_ui_and_process_video()

        # Print completion message
        print("\nVideo processing completed.")
        print(
            "If successful, your enhanced video is in the same folder as the original file.")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

    # Add a pause so the console window doesn't close immediately
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
