"""
Social Media Enhancer for Fitness Videos
Adds professional social media optimizations for text overlays and animations
"""

import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, filedialog

# Import the simple_blue_video module (assumed to be in the same directory)
try:
    import simple_blue_video
    from text_overlay_patch import *  # Import all functions from the patch
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure simple_blue_video.py and text_overlay_patch.py are in the same directory.")
    sys.exit(1)


def create_enhancement_ui():
    """
    Create a modern UI for selecting social media enhancement options.
    Returns a dictionary with the selected enhancement options.
    """
    # Initialize with defaults
    selected_options = {
        "text_style": "bold_statement",
        "animation_style": "fade",
        "background_effect": "gradient_bar",
        "color_grade": "fitness",
        "video_path": None
    }

    # Create the root window
    root = tk.Tk()
    root.title("Social Media Video Enhancer")
    root.geometry("600x650")
    root.configure(bg="#f0f0f0")

    # Add a header with title
    header_frame = tk.Frame(root, bg="#333333", padx=10, pady=10)
    header_frame.pack(fill=tk.X)

    title_label = tk.Label(header_frame, text="SOCIAL MEDIA VIDEO ENHANCER",
                           font=("Arial", 16, "bold"), fg="white", bg="#333333")
    title_label.pack()

    subtitle_label = tk.Label(header_frame, text="Make your fitness videos stand out with professional effects",
                              font=("Arial", 10), fg="#cccccc", bg="#333333")
    subtitle_label.pack(pady=(0, 5))

    # Create a main frame for content
    main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Video file selection
    file_frame = tk.LabelFrame(main_frame, text="Video Selection", font=("Arial", 11, "bold"),
                               bg="#f0f0f0", padx=10, pady=10)
    file_frame.pack(fill=tk.X, pady=(0, 15))

    video_path_var = tk.StringVar(value="No video selected")

    path_label = tk.Label(file_frame, textvariable=video_path_var,
                          bg="#f0f0f0", fg="#333333", font=("Arial", 10))
    path_label.pack(fill=tk.X, pady=(0, 10))

    def browse_video():
        file_path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv")]
        )
        if file_path:
            video_path_var.set(file_path)
            selected_options["video_path"] = file_path

    browse_button = ttk.Button(
        file_frame, text="Browse for Video", command=browse_video)
    browse_button.pack()

    # Style Options
    style_frame = tk.LabelFrame(main_frame, text="Text Style", font=("Arial", 11, "bold"),
                                bg="#f0f0f0", padx=10, pady=10)
    style_frame.pack(fill=tk.X, pady=(0, 15))

    text_style_var = tk.StringVar(value="bold_statement")

    # Text style options
    text_styles = [
        ("Bold Statement (Impact Font)", "bold_statement"),
        ("Instagram Classic", "instagram_classic"),
        ("Fitness Pro", "fitness_pro"),
        ("Minimal Clean", "minimal"),
        ("Instagram Story", "instagram_story")
    ]

    for text, val in text_styles:
        style_radio = ttk.Radiobutton(
            style_frame, text=text, value=val, variable=text_style_var)
        style_radio.pack(anchor=tk.W, pady=2)

    # Animation Options
    animation_frame = tk.LabelFrame(main_frame, text="Animation Style", font=("Arial", 11, "bold"),
                                    bg="#f0f0f0", padx=10, pady=10)
    animation_frame.pack(fill=tk.X, pady=(0, 15))

    animation_var = tk.StringVar(value="fade")

    # Animation options
    animations = [
        ("Fade In", "fade"),
        ("Slide In", "slide_in"),
        ("Typewriter Effect", "typewriter"),
        ("Bouncing", "bounce"),
        ("Glowing", "glow")
    ]

    for text, val in animations:
        anim_radio = ttk.Radiobutton(
            animation_frame, text=text, value=val, variable=animation_var)
        anim_radio.pack(anchor=tk.W, pady=2)

    # Background Effect Options
    bg_frame = tk.LabelFrame(main_frame, text="Background Effect", font=("Arial", 11, "bold"),
                             bg="#f0f0f0", padx=10, pady=10)
    bg_frame.pack(fill=tk.X, pady=(0, 15))

    bg_var = tk.StringVar(value="gradient_bar")

    # Background effect options
    backgrounds = [
        ("Gradient Bar", "gradient_bar"),
        ("Solid Bar", "solid_bar"),
        ("Blur Box", "blur_box"),
        ("Shadow Lift", "shadow_lift"),
        ("None (Text Only)", "none")
    ]

    for text, val in backgrounds:
        bg_radio = ttk.Radiobutton(
            bg_frame, text=text, value=val, variable=bg_var)
        bg_radio.pack(anchor=tk.W, pady=2)

    # Color Grading Options
    color_frame = tk.LabelFrame(main_frame, text="Color Grading", font=("Arial", 11, "bold"),
                                bg="#f0f0f0", padx=10, pady=10)
    color_frame.pack(fill=tk.X, pady=(0, 15))

    color_var = tk.StringVar(value="fitness")

    # Color grading options
    colors = [
        ("Fitness (High Contrast)", "fitness"),
        ("Cinematic", "cinematic"),
        ("Vibrant", "vibrant"),
        ("Moody", "moody"),
        ("None (Original Colors)", "none")
    ]

    for text, val in colors:
        color_radio = ttk.Radiobutton(
            color_frame, text=text, value=val, variable=color_var)
        color_radio.pack(anchor=tk.W, pady=2)

    # Submit Button
    submit_button = ttk.Button(
        main_frame,
        text="Create Enhanced Video",
        style="Accent.TButton"
    )
    submit_button.pack(pady=15)

    # Function to handle submit
    def on_submit():
        selected_options["text_style"] = text_style_var.get()
        selected_options["animation_style"] = animation_var.get()
        selected_options["background_effect"] = bg_var.get()
        selected_options["color_grade"] = color_var.get()

        # If no video is selected, use the file dialog
        if not selected_options["video_path"]:
            browse_video()
            if not selected_options["video_path"]:
                return

        root.destroy()

    submit_button.config(command=on_submit)

    # Set up styles
    style = ttk.Style()
    style.configure("Accent.TButton", font=("Arial", 12, "bold"))

    # Start the main loop
    root.mainloop()

    return selected_options


def enhance_video(options):
    """
    Apply social media enhancements to a video using the selected options.

    Parameters:
    - options: Dictionary with enhancement options

    Returns:
    - Path to enhanced video, or None if processing failed
    """
    try:
        if not options["video_path"]:
            print("No video selected. Exiting.")
            return None

        print(f"Enhancing video with social media optimizations...")
        print(f"- Text Style: {options['text_style']}")
        print(f"- Animation: {options['animation_style']}")
        print(f"- Background: {options['background_effect']}")
        print(f"- Color Grade: {options['color_grade']}")

        # Process the video (calls the function from text_overlay_patch)
        output_path = safe_process_video(
            options["video_path"],
            text_style=options["text_style"],
            background_effect=options["background_effect"],
            color_grade=options["color_grade"]
        )

        if output_path:
            print(f"\nSuccess! Enhanced video saved to: {output_path}")

            # Attempt to open the video for preview
            try:
                import platform
                import subprocess

                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', output_path))
                elif platform.system() == 'Windows':  # Windows
                    os.startfile(output_path)
                else:  # linux
                    subprocess.call(('xdg-open', output_path))

                print("Opening video for preview...")
            except Exception as e:
                print(f"Could not automatically open the video: {e}")

            return output_path
        else:
            print("Failed to enhance video. Please check the error messages above.")
            return None

    except Exception as e:
        print(f"Error enhancing video: {e}")
        traceback.print_exc()
        return None


def main():
    """Main function to run the social media enhancer."""
    print("╔═════════════════════════════════════════════════╗")
    print("║  Social Media Enhancer for Fitness Videos       ║")
    print("║  Create eye-catching videos optimized for       ║")
    print("║  Instagram, TikTok, and other platforms         ║")
    print("╚═════════════════════════════════════════════════╝")

    # Get enhancement options from UI
    options = create_enhancement_ui()

    # Apply enhancements
    enhanced_video_path = enhance_video(options)

    if enhanced_video_path:
        print("\nVideo enhancement complete! Your video is now social media-ready.")
        print(f"Find your enhanced video at: {enhanced_video_path}")
    else:
        print("\nVideo enhancement could not be completed. Please try again.")


if __name__ == "__main__":
    main()
