"""
Social Media Enhancer for Fitness Videos
Adds professional social media optimizations for text overlays and animations
"""

import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk, filedialog
import threading

# Import the simple_blue_video module (assumed to be in the same directory)
try:
    import simple_blue_video
    # Import from our fixed patch file instead
    from text_overlay_patch_fixed import enhance_video, safe_process_video
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure simple_blue_video.py and text_overlay_patch_fixed.py are in the same directory.")
    sys.exit(1)

# Global variable to store enhancement options
selected_options = {
    "text_style": "bold_statement",
    "animation_style": "fade",
    "background_effect": "gradient_bar",
    "color_grade": "fitness",
    "video_path": None
}


def enhance_video_with_options(options):
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

        print(f"\nEnhancing video with social media optimizations...")
        print(f"- Text Style: {options['text_style']}")
        print(f"- Animation: {options['animation_style']}")
        print(f"- Background: {options['background_effect']}")
        print(f"- Color Grade: {options['color_grade']}")

        # Use our imported enhance_video function from the fixed patch
        output_path = enhance_video(
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


def process_video_thread():
    """Function to run in a separate thread to process the video after UI closes"""
    global selected_options
    try:
        enhanced_video_path = enhance_video_with_options(selected_options)

        if enhanced_video_path:
            print("\nVideo enhancement complete! Your video is now social media-ready.")
            print(f"Find your enhanced video at: {enhanced_video_path}")
        else:
            print("\nVideo enhancement could not be completed. Please try again.")
    except Exception as e:
        print(f"Error in video processing thread: {e}")
        traceback.print_exc()


def create_enhancement_ui():
    """
    Create a modern UI for selecting social media enhancement options.
    Updates the global selected_options dictionary.
    """
    global selected_options

    # Create the root window
    root = tk.Tk()
    root.title("Social Media Video Enhancer")
    root.geometry("600x700")  # Increased height to ensure button is visible
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

    # Create a main content with scrollbar if needed
    canvas = tk.Canvas(root, bg="#f0f0f0")
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Main frame for all content
    main_frame = ttk.Frame(scrollable_frame)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Video file selection
    file_frame = ttk.LabelFrame(main_frame, text="Video Selection")
    file_frame.pack(fill=tk.X, pady=(0, 15))

    video_path_var = tk.StringVar(value="No video selected")

    path_label = ttk.Label(file_frame, textvariable=video_path_var)
    path_label.pack(fill=tk.X, pady=(5, 10), padx=10)

    def browse_video():
        file_path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv")]
        )
        if file_path:
            video_path_var.set(file_path)
            selected_options["video_path"] = file_path

    browse_button = ttk.Button(
        file_frame, text="Browse for Video", command=browse_video)
    browse_button.pack(pady=(0, 10), padx=10)

    # Style Options
    style_frame = ttk.LabelFrame(main_frame, text="Text Style")
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
        style_radio.pack(anchor=tk.W, pady=2, padx=10)

    # Animation Options
    animation_frame = ttk.LabelFrame(main_frame, text="Animation Style")
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
        anim_radio.pack(anchor=tk.W, pady=2, padx=10)

    # Background Effect Options
    bg_frame = ttk.LabelFrame(main_frame, text="Background Effect")
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
        bg_radio.pack(anchor=tk.W, pady=2, padx=10)

    # Color Grading Options
    color_frame = ttk.LabelFrame(main_frame, text="Color Grading")
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
        color_radio.pack(anchor=tk.W, pady=2, padx=10)

    # Create a separate frame for the button at the bottom that's always visible
    button_frame = tk.Frame(root, bg="#f0f0f0", pady=15)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Function to handle submit
    def on_submit():
        # First, update all the selected options
        selected_options["text_style"] = text_style_var.get()
        selected_options["animation_style"] = animation_var.get()
        selected_options["background_effect"] = bg_var.get()
        selected_options["color_grade"] = color_var.get()

        # If no video is selected, use the file dialog
        if not selected_options["video_path"]:
            browse_video()
            if not selected_options["video_path"]:
                return

        # Create a progress window
        progress_win = tk.Toplevel(root)
        progress_win.title("Creating Enhanced Video")
        progress_win.geometry("400x200")
        progress_win.configure(bg="#f0f0f0")

        # Make it modal
        progress_win.transient(root)
        progress_win.grab_set()

        # Center the window
        progress_win.update_idletasks()
        width = progress_win.winfo_width()
        height = progress_win.winfo_height()
        x = (progress_win.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_win.winfo_screenheight() // 2) - (height // 2)
        progress_win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # Add a message
        message_label = tk.Label(
            progress_win,
            text="Creating your enhanced video...\nThis may take a few minutes.",
            font=("Arial", 12),
            bg="#f0f0f0",
            pady=20
        )
        message_label.pack(fill=tk.X)

        # Add a progress bar
        progress = ttk.Progressbar(
            progress_win,
            orient="horizontal",
            length=300,
            mode="indeterminate"
        )
        progress.pack(pady=20)
        progress.start(10)

        # Add a tip
        tip_label = tk.Label(
            progress_win,
            text="The main window will close while processing.\nThe enhanced video will open when complete.",
            font=("Arial", 10),
            fg="#555555",
            bg="#f0f0f0"
        )
        tip_label.pack(fill=tk.X, pady=10)

        # Update the UI
        progress_win.update()

        # Wait a moment to show the progress window, then create a thread for processing
        # and destroy the windows
        def start_processing():
            # Create a thread to run the video processing - NON-DAEMON so it won't close
            process_thread = threading.Thread(target=process_video_thread)
            process_thread.daemon = False  # Critical change: make the thread non-daemon

            # Start the thread and close UI
            process_thread.start()
            progress_win.destroy()
            root.destroy()

        # Schedule the processing to start after a brief delay
        root.after(1500, start_processing)

    # Submit Button - now in its own frame at the bottom
    submit_button = ttk.Button(
        button_frame,
        text="CREATE ENHANCED VIDEO",
        command=on_submit,
    )
    submit_button.pack(pady=10, padx=20, ipadx=10, ipady=5, fill=tk.X)

    # Make button stand out with custom style
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"))

    # Start the main loop
    root.mainloop()


def main():
    """Main function to run the social media enhancer."""
    print("╔═════════════════════════════════════════════════╗")
    print("║  Social Media Enhancer for Fitness Videos       ║")
    print("║  Create eye-catching videos optimized for       ║")
    print("║  Instagram, TikTok, and other platforms         ║")
    print("╚═════════════════════════════════════════════════╝")

    # Create UI to get enhancement options (updates global selected_options)
    create_enhancement_ui()

    # If the UI was closed without selecting options, we won't process the video
    if not selected_options["video_path"]:
        print("No video selected. Exiting.")
        return

    # If we get here, it means the UI was closed after selecting options
    # and the thread should be processing the video
    print("Video enhancement in progress. Please wait...")
    print("This window will stay open until processing is complete.")


if __name__ == "__main__":
    main()
