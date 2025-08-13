#!/usr/bin/env python3

"""
Fitness Video Auto-Labeler GUI
A graphical user interface for the Fitness Video Auto-Labeler application.
"""

# Configure ImageMagick path for MoviePy
import os
try:
    from moviepy.config import change_settings

    # Common installation paths for ImageMagick on Windows
    possible_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-7.0.8-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-6.9.13-Q16\convert.exe"
    ]

    # Check if any of these paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ImageMagick at: {path}")
            change_settings({"IMAGEMAGICK_BINARY": path})
            break
    else:
        print("Warning: ImageMagick not found at common locations.")
        print("If you encounter errors, please install ImageMagick from:")
        print("https://imagemagick.org/script/download.php")
        print("Make sure to check 'Install legacy utilities' during installation.")
except ImportError:
    print("Warning: MoviePy configuration module not found.")

# Import the patch first to ensure it applies before any other imports
try:
    import text_overlay_patch
    print("Successfully imported text overlay patch")
except ImportError as e:
    print(f"Warning: Could not import text overlay patch: {e}")

# Import the fixed auto labeler
import fixed_video_auto_labeler as auto_labeler
from text_overlay_generator import text_overlay, TEXT_POSITIONS
from exercise_database import exercise_db
import sys
import json
import time
import threading
import subprocess
import queue
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import tkinter.scrolledtext as ScrolledText
import tkinter.font as tkFont


class RedirectText:
    """
    Redirect stdout to a tkinter Text widget.
    """

    def __init__(self, text_widget):
        """Initialize with a text widget to redirect to."""
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        """Write to the text widget."""
        self.buffer += string
        if "\n" in self.buffer:
            self.text_widget.config(state=NORMAL)
            self.text_widget.insert(END, self.buffer)
            self.text_widget.see(END)
            self.text_widget.config(state=DISABLED)
            self.buffer = ""

    def flush(self):
        """Flush the buffer."""
        if self.buffer:
            self.text_widget.config(state=NORMAL)
            self.text_widget.insert(END, self.buffer)
            self.text_widget.see(END)
            self.text_widget.config(state=DISABLED)
            self.buffer = ""


class VideoPreviewPanel(Frame):
    """
    A panel for previewing processed videos.
    """

    def __init__(self, parent):
        """Initialize the preview panel."""
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        """Create the widgets for the preview panel."""
        # Create a label for the preview
        self.preview_label = Label(self, text="Video Preview")
        self.preview_label.pack(side=TOP, fill=X)

        # Create a frame for the preview
        self.preview_frame = Frame(self, bg="black", width=400, height=300)
        self.preview_frame.pack(side=TOP, fill=BOTH,
                                expand=TRUE, padx=10, pady=10)

        # Create a label for the preview image
        self.preview_image_label = Label(
            self.preview_frame, bg="black", text="No video selected")
        self.preview_image_label.pack(side=TOP, fill=BOTH, expand=TRUE)

        # Create controls for the preview
        self.controls_frame = Frame(self)
        self.controls_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        # Create a button to open the selected video
        self.open_button = Button(
            self.controls_frame, text="Open Video", command=self.open_video)
        self.open_button.pack(side=LEFT, padx=5)

        # Create a button to open the directory
        self.open_dir_button = Button(
            self.controls_frame, text="Open Directory", command=self.open_directory)
        self.open_dir_button.pack(side=RIGHT, padx=5)

        # Current video path
        self.current_video = None

    def set_video(self, video_path):
        """Set the current video path."""
        self.current_video = video_path
        if video_path:
            # Update the preview label
            self.preview_label.config(
                text=f"Video Preview: {os.path.basename(video_path)}")

            # Update the preview image
            self.preview_image_label.config(
                text=f"Video loaded: {os.path.basename(video_path)}")
        else:
            # Clear the preview
            self.preview_label.config(text="Video Preview")
            self.preview_image_label.config(text="No video selected")

    def open_video(self):
        """Open the current video in the default video player."""
        if self.current_video and os.path.exists(self.current_video):
            try:
                # Open with default application
                if sys.platform == 'win32':
                    os.startfile(self.current_video)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', self.current_video])
                else:  # Linux
                    subprocess.run(['xdg-open', self.current_video])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open video: {e}")
        else:
            messagebox.showinfo("No Video", "No video is currently selected.")

    def open_directory(self):
        """Open the directory containing the current video."""
        if self.current_video and os.path.exists(self.current_video):
            try:
                # Open directory with default file explorer
                directory = os.path.dirname(self.current_video)
                if sys.platform == 'win32':
                    os.startfile(directory)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', directory])
                else:  # Linux
                    subprocess.run(['xdg-open', directory])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open directory: {e}")
        else:
            messagebox.showinfo("No Video", "No video is currently selected.")


class VideoQueuePanel(Frame):
    """
    A panel for displaying the video processing queue.
    """

    def __init__(self, parent, preview_panel):
        """Initialize the queue panel."""
        super().__init__(parent)
        self.parent = parent
        self.preview_panel = preview_panel
        self.create_widgets()

        # Video queue
        self.video_queue = []
        self.processed_videos = []

    def create_widgets(self):
        """Create the widgets for the queue panel."""
        # Create a label for the queue
        self.queue_label = Label(self, text="Video Queue")
        self.queue_label.pack(side=TOP, fill=X)

        # Create tabs for queue and processed videos
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(side=TOP, fill=BOTH, expand=TRUE, padx=10, pady=10)

        # Create queue tab
        self.queue_tab = Frame(self.tabs)
        self.tabs.add(self.queue_tab, text="Queue")

        # Create processed tab
        self.processed_tab = Frame(self.tabs)
        self.tabs.add(self.processed_tab, text="Processed")

        # Create queue list
        self.queue_frame = Frame(self.queue_tab)
        self.queue_frame.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.queue_scrollbar = Scrollbar(self.queue_frame)
        self.queue_scrollbar.pack(side=RIGHT, fill=Y)

        self.queue_listbox = Listbox(
            self.queue_frame, yscrollcommand=self.queue_scrollbar.set)
        self.queue_listbox.pack(side=LEFT, fill=BOTH, expand=TRUE)

        self.queue_scrollbar.config(command=self.queue_listbox.yview)

        # Bind select event
        self.queue_listbox.bind('<<ListboxSelect>>', self.on_queue_select)

        # Create processed list
        self.processed_frame = Frame(self.processed_tab)
        self.processed_frame.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.processed_scrollbar = Scrollbar(self.processed_frame)
        self.processed_scrollbar.pack(side=RIGHT, fill=Y)

        self.processed_listbox = Listbox(
            self.processed_frame, yscrollcommand=self.processed_scrollbar.set)
        self.processed_listbox.pack(side=LEFT, fill=BOTH, expand=TRUE)

        self.processed_scrollbar.config(command=self.processed_listbox.yview)

        # Bind select event
        self.processed_listbox.bind(
            '<<ListboxSelect>>', self.on_processed_select)

        # Create controls
        self.controls_frame = Frame(self)
        self.controls_frame.pack(side=BOTTOM, fill=X, padx=10, pady=10)

        # Create a button to clear the queue
        self.clear_button = Button(
            self.controls_frame, text="Clear Queue", command=self.clear_queue)
        self.clear_button.pack(side=LEFT, padx=5)

        # Create a button to clear processed
        self.clear_processed_button = Button(
            self.controls_frame, text="Clear Processed", command=self.clear_processed)
        self.clear_processed_button.pack(side=RIGHT, padx=5)

    def update_queue(self):
        """Update the queue listbox."""
        self.queue_listbox.delete(0, END)
        for video in self.video_queue:
            self.queue_listbox.insert(END, os.path.basename(video))

    def update_processed(self):
        """Update the processed listbox."""
        self.processed_listbox.delete(0, END)
        for video in self.processed_videos:
            self.processed_listbox.insert(END, os.path.basename(video))

    def add_to_queue(self, video_path):
        """Add a video to the queue."""
        if video_path not in self.video_queue:
            self.video_queue.append(video_path)
            self.update_queue()

    def add_to_processed(self, video_path):
        """Add a video to the processed list."""
        if video_path not in self.processed_videos:
            self.processed_videos.append(video_path)
            self.update_processed()

    def remove_from_queue(self, video_path):
        """Remove a video from the queue."""
        if video_path in self.video_queue:
            self.video_queue.remove(video_path)
            self.update_queue()

    def on_queue_select(self, event):
        """Handle queue selection event."""
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            video_path = self.video_queue[index]
            self.preview_panel.set_video(video_path)

    def on_processed_select(self, event):
        """Handle processed selection event."""
        selection = self.processed_listbox.curselection()
        if selection:
            index = selection[0]
            video_path = self.processed_videos[index]
            self.preview_panel.set_video(video_path)

    def clear_queue(self):
        """Clear the video queue."""
        if messagebox.askyesno("Clear Queue", "Are you sure you want to clear the queue?"):
            self.video_queue = []
            self.update_queue()

    def clear_processed(self):
        """Clear the processed list."""
        if messagebox.askyesno("Clear Processed", "Are you sure you want to clear the processed list?"):
            self.processed_videos = []
            self.update_processed()


class StylePreviewPanel(Frame):
    """
    A panel for previewing and selecting different text styles in an Instagram-like interface.
    """

    def __init__(self, parent, config, on_style_selected=None):
        """Initialize the style preview panel."""
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.on_style_selected = on_style_selected
        self.current_video = None
        self.style_frames = {}  # Store style frames for reference
        self.style_thumbnails = {}  # Store thumbnail images
        self.thumbnail_labels = {}  # Store thumbnail labels for updating
        self.process_all_after_selection = False  # Flag for processing all videos

        # Create the widgets
        self.create_widgets()

        # Initially hide the panel
        self.pack_forget()

        # Generate style thumbnails after initialization
        self.after(100, self.generate_style_thumbnails)

    def create_widgets(self):
        """Create the widgets for the style preview panel."""
        # Main label
        self.title_label = Label(
            self, text="Select Text Style", font=("Arial", 14, "bold"))
        self.title_label.pack(side=TOP, fill=X, padx=10, pady=5)

        # Description label
        self.description_label = Label(
            self,
            text="Choose how text will appear on your video",
            font=("Arial", 10)
        )
        self.description_label.pack(side=TOP, fill=X, padx=10, pady=2)

        # Create a frame for the style thumbnails
        self.styles_container = Frame(self)
        self.styles_container.pack(
            side=TOP, fill=BOTH, expand=TRUE, padx=10, pady=10)

        # Get available styles
        available_styles = ["minimal", "bold_statement",
                            "fitness_pro", "instagram_classic"]

        # Create a grid layout for style thumbnails
        num_styles = len(available_styles)
        cols = 2  # Two columns of styles
        rows = (num_styles + 1) // 2  # Calculate rows needed

        # Configure the grid
        for i in range(rows):
            self.styles_container.rowconfigure(i, weight=1)
        for i in range(cols):
            self.styles_container.columnconfigure(i, weight=1)

        # Create style thumbnails
        for idx, style in enumerate(available_styles):
            row = idx // cols
            col = idx % cols

            # Create a frame for each style
            style_frame = Frame(
                self.styles_container,
                borderwidth=2,
                relief="ridge",
                padx=5,
                pady=5
            )
            style_frame.grid(row=row, column=col, padx=5,
                             pady=5, sticky="nsew")

            # Store the frame for later reference
            self.style_frames[style] = style_frame

            # Create a placeholder for the thumbnail
            thumbnail_label = Label(
                style_frame,
                text=f"Preview of\n{style.replace('_', ' ').title()}",
                width=15,
                height=6,
                background=self.get_style_color(style)
            )
            thumbnail_label.pack(side=TOP, fill=BOTH,
                                 expand=TRUE, padx=2, pady=2)

            # Store the thumbnail label for later updating
            self.thumbnail_labels[style] = thumbnail_label

            # Style name label
            name_label = Label(
                style_frame,
                text=style.replace('_', ' ').title(),
                font=("Arial", 10, "bold")
            )
            name_label.pack(side=TOP, fill=X, padx=2, pady=2)

            # Select button
            select_button = Button(
                style_frame,
                text="Select",
                command=lambda s=style: self.select_style(s)
            )
            select_button.pack(side=BOTTOM, fill=X, padx=2, pady=2)

            # Preview animation button
            preview_button = Button(
                style_frame,
                text="Preview Animation",
                command=lambda s=style: self.preview_animation(s)
            )
            preview_button.pack(side=BOTTOM, fill=X, padx=2, pady=2)

            # Mark current active style
            if style == self.config.get("text_style", "minimal"):
                style_frame.config(
                    highlightbackground="blue", highlightthickness=3)

        # Create buttons at the bottom
        self.buttons_frame = Frame(self)
        self.buttons_frame.pack(side=BOTTOM, fill=X, padx=10, pady=5)

        # Back button (to go back to queue)
        self.back_button = Button(
            self.buttons_frame,
            text="Back",
            command=self.hide
        )
        self.back_button.pack(side=LEFT, padx=5, pady=5)

        # Apply button (to apply selected style)
        self.apply_button = Button(
            self.buttons_frame,
            text="Apply Style & Process",
            command=self.apply_style_and_process
        )
        self.apply_button.pack(side=RIGHT, padx=5, pady=5)

    def get_style_color(self, style_name):
        """Get a representative color for the style thumbnail background."""
        # Colors that represent the different styles
        style_colors = {
            "minimal": "#EEEEEE",  # Light gray
            "bold_statement": "#333333",  # Dark gray
            "fitness_pro": "#FF4500",  # Orange-red
            "instagram_classic": "#E1306C"  # Instagram pink
        }
        return style_colors.get(style_name, "#CCCCCC")  # Default to gray

    def select_style(self, style_name):
        """Select a style."""
        print(f"Style selected: {style_name}")

        # Update frames to show selection
        for style, frame in self.style_frames.items():
            if style == style_name:
                frame.config(highlightbackground="blue", highlightthickness=3)
            else:
                frame.config(
                    highlightbackground=self.master["background"], highlightthickness=0)

        # Update config
        self.config.set("text_style", style_name)

        # Call callback if provided
        if self.on_style_selected:
            self.on_style_selected(style_name)

    def apply_style_and_process(self):
        """Apply the selected style and process the video."""
        if not self.current_video:
            messagebox.showinfo("No Video", "Please select a video first.")
            return

        # Hide this panel
        self.hide()

        # Trigger processing
        if self.on_style_selected:
            self.on_style_selected(self.config.get("text_style"), process=True)

    def show(self, video_path=None):
        """Show the style preview panel."""
        if video_path:
            self.current_video = video_path
            self.title_label.config(
                text=f"Select Style for: {os.path.basename(video_path)}")

            # Generate video-specific thumbnails if a video is provided
            self.after(100, lambda: self.generate_video_thumbnails(video_path))

        # Mark current style
        current_style = self.config.get("text_style", "minimal")
        self.select_style(current_style)

        # Show the panel
        self.pack(side=TOP, fill=BOTH, expand=TRUE, padx=10, pady=10)

    def generate_video_thumbnails(self, video_path):
        """Generate thumbnails for each style using the actual video frame."""
        try:
            # Import necessary modules
            from moviepy.editor import VideoFileClip
            from PIL import Image, ImageDraw, ImageFont, ImageTk
            import numpy as np

            print(
                f"Generating video thumbnails for {os.path.basename(video_path)}...")

            # Load the video and extract a frame
            try:
                video = VideoFileClip(video_path)

                # Get a frame from 1 second in or the middle of the video, whichever is earlier
                target_time = min(1.0, video.duration / 2)
                frame = video.get_frame(target_time)

                # Convert to PIL Image
                frame_img = Image.fromarray(frame)

                # Resize to our desired thumbnail size
                width, height = 240, 135  # 16:9 aspect ratio
                frame_img = frame_img.resize((width, height), Image.LANCZOS)

                # Get exercise name from filename
                base_name = os.path.basename(video_path)
                name, _ = os.path.splitext(base_name)
                exercise_name = name.replace("_", " ").strip().title()

                # Get hook and tip text - either from database or defaults
                hook_text = "Engage your core for maximum power"
                tip_text = "Keep proper form throughout the movement"

                try:
                    # Try to find exercise info if database is available
                    if 'exercise_db' in globals():
                        for ex in exercise_db.exercises:
                            if ex['name'].lower() in exercise_name.lower():
                                if 'hook' in ex and ex['hook']:
                                    hook_text = ex['hook']
                                if 'technique_tip' in ex and ex['technique_tip']:
                                    tip_text = ex['technique_tip']
                                break
                except Exception as e:
                    print(f"Error getting exercise info: {e}")

                # Generate thumbnails for each style with the video frame as background
                for style_name in self.style_frames.keys():
                    # Create a copy of the frame
                    img = frame_img.copy()
                    draw = ImageDraw.Draw(img)

                    # Get style settings
                    style_config = self.get_style_config(style_name)

                    # Get font settings
                    font_name = style_config.get("font", "Arial")
                    try:
                        title_font = ImageFont.truetype(font_name, 18)
                        body_font = ImageFont.truetype(font_name, 12)
                    except:
                        title_font = ImageFont.load_default()
                        body_font = ImageFont.load_default()

                    # Get colors
                    text_color = style_config.get("color", "white")
                    if text_color == "white":
                        text_color = (255, 255, 255)
                    elif text_color.startswith("#"):
                        text_color = tuple(
                            int(text_color[i:i+2], 16) for i in (1, 3, 5))

                    # Draw background if style has it
                    if style_config.get("background", False):
                        bg_color = style_config.get(
                            "background_color", (0, 0, 0, 128))
                        # Draw rectangles for text backgrounds
                        draw.rectangle([(5, 5), (width-5, 30)], fill=bg_color)
                        draw.rectangle(
                            [(5, height-60), (width-5, height-35)], fill=bg_color)
                        draw.rectangle(
                            [(5, height-30), (width-5, height-5)], fill=bg_color)

                    # Add shadow for text if style has it
                    if style_config.get("shadow", False):
                        shadow_color = style_config.get(
                            "shadow_color", "black")
                        # Draw with slight offset for shadow
                        draw.text((width//2+1, 18+1), exercise_name,
                                  font=title_font, fill=shadow_color, anchor="mm")
                        draw.text(
                            (width//2+1, height-48+1), hook_text[:20] + "...", font=body_font, fill=shadow_color, anchor="mm")
                        draw.text(
                            (width//2+1, height-48+1), hook_text[:20] + "...", font=body_font, fill=shadow_color, anchor="mm")
                        draw.text(
                            (width//2+1, height-18+1), tip_text[:20] + "...", font=body_font, fill=shadow_color, anchor="mm")

                    # Draw text
                    draw.text((width//2, 18), exercise_name,
                              font=title_font, fill=text_color, anchor="mm")
                    draw.text(
                        (width//2, height-48), hook_text[:20] + "...", font=body_font, fill=text_color, anchor="mm")
                    draw.text(
                        (width//2, height-18), tip_text[:20] + "...", font=body_font, fill=text_color, anchor="mm")

                    # Add style indicator
                    style_indicator = style_name.replace("_", " ").title()
                    draw.text((width-5, 15), style_indicator,
                              font=body_font, fill=text_color, anchor="rm")

                    # Convert to a format tkinter can use
                    self.style_thumbnails[style_name] = self.pil_to_tkinter(
                        img)

                    # Update thumbnail label
                    if style_name in self.thumbnail_labels:
                        self.thumbnail_labels[style_name].config(
                            image=self.style_thumbnails[style_name], text="")

                # Clean up
                video.close()

                print("Generated video thumbnails successfully")

            except Exception as e:
                print(f"Error processing video for thumbnails: {e}")
                # Use generic thumbnails as fallback
                self.generate_style_thumbnails()

        except Exception as e:
            print(f"Error generating video thumbnails: {e}")
            # Use generic thumbnails as fallback
            self.generate_style_thumbnails()

    def pil_to_tkinter(self, pil_image):
        """Convert PIL image to a format tkinter can display."""
        from PIL import ImageTk
        return ImageTk.PhotoImage(pil_image)

    def get_style_config(self, style_name):
        """Get the configuration for a style from text_overlay_generator."""
        # Default configuration if we can't access the real styles
        default_styles = {
            "minimal": {
                "font": "Arial",
                "color": "white",
                "shadow": True,
                "shadow_color": "black",
                "background": False,
                "animation": "fade",
            },
            "bold_statement": {
                "font": "Impact",
                "color": "white",
                "shadow": True,
                "shadow_color": "black",
                "background": True,
                "background_color": (0, 0, 0, 128),
                "animation": "slide",
            },
            "fitness_pro": {
                "font": "Arial",
                "color": "#FF4500",
                "accent_color": "#0096FF",
                "shadow": False,
                "background": False,
                "animation": "fade",
            },
            "instagram_classic": {
                "font": "Arial",
                "color": "white",
                "background": True,
                "background_color": (255, 90, 95, 230),
                "animation": "slide",
            }
        }

        try:
            # Try to import the real styles from text_overlay_generator
            from text_overlay_generator import TEXT_STYLES
            return TEXT_STYLES.get(style_name, default_styles.get(style_name, {}))
        except:
            # Use our default styles if import fails
            return default_styles.get(style_name, {})

    def preview_animation(self, style_name):
        """Show a preview animation of the selected style."""
        try:
            # Create a top-level window for the animation
            preview_window = Toplevel(self)
            preview_window.title(
                f"{style_name.replace('_', ' ').title()} Animation Preview")
            preview_window.geometry("600x400")
            # Set to be on top of the parent window
            preview_window.transient(self)
            preview_window.grab_set()  # Make the window modal

            # Add a label to show the animation
            preview_label = Label(preview_window, bg="black")
            preview_label.pack(fill=BOTH, expand=TRUE, padx=10, pady=10)

            # Add a close button
            close_button = Button(
                preview_window,
                text="Close Preview",
                command=preview_window.destroy
            )
            close_button.pack(side=BOTTOM, pady=10)

            # Get style configuration
            style_config = self.get_style_config(style_name)
            animation_type = style_config.get("animation", "fade")

            # Define example text
            title_text = "Deadlift"
            hook_text = "Powerhouse Movement for Total Body Strength"
            tip_text = "Keep your back straight and engage your core"

            # Define animation frames
            num_frames = 20  # 20 frames for the animation

            # Setup for animation rendering
            frame_width, frame_height = 580, 320

            # Create animation frames
            try:
                from PIL import Image, ImageDraw, ImageFont, ImageTk
                import time

                # Get font settings
                font_name = style_config.get("font", "Arial")
                try:
                    title_font = ImageFont.truetype(font_name, 36)
                    body_font = ImageFont.truetype(font_name, 24)
                except:
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()

                # Text color
                text_color = style_config.get("color", "white")
                if text_color == "white":
                    text_color = (255, 255, 255)
                elif text_color.startswith("#"):
                    text_color = tuple(
                        int(text_color[i:i+2], 16) for i in (1, 3, 5))

                # Background color
                has_bg = style_config.get("background", False)
                bg_color = style_config.get("background_color", (0, 0, 0, 128))

                # Start the animation sequence
                def animate_frames():
                    for frame_idx in range(num_frames):
                        # Create new frame
                        img = Image.new(
                            'RGB', (frame_width, frame_height), (0, 0, 0))
                        draw = ImageDraw.Draw(img)

                        # Determine animation progress (0.0 to 1.0)
                        progress = frame_idx / (num_frames - 1)

                        # Apply different animations based on style
                        if animation_type == "fade":
                            # Fade in title
                            title_alpha = min(1.0, progress * 2)
                            # Draw background if needed
                            if has_bg:
                                bg_alpha = int(255 * title_alpha)
                                bg_with_alpha = (*bg_color[:3], bg_alpha)
                                draw.rectangle(
                                    [(10, 10), (frame_width-10, 70)], fill=bg_with_alpha)

                            # Draw title with alpha
                            title_color = (
                                *text_color[:3], int(255 * title_alpha))
                            draw.text((frame_width//2, 40), title_text,
                                      font=title_font, fill=title_color, anchor="mm")

                            # Fade in hook after title starts
                            if progress > 0.3:
                                hook_alpha = min(1.0, (progress - 0.3) * 2)
                                if has_bg:
                                    bg_alpha = int(255 * hook_alpha)
                                    bg_with_alpha = (*bg_color[:3], bg_alpha)
                                    draw.rectangle(
                                        [(10, 80), (frame_width-10, 140)], fill=bg_with_alpha)

                                hook_color = (
                                    *text_color[:3], int(255 * hook_alpha))
                                draw.text((frame_width//2, 110), hook_text,
                                          font=body_font, fill=hook_color, anchor="mm")

                            # Fade in tip after hook starts
                            if progress > 0.6:
                                tip_alpha = min(1.0, (progress - 0.6) * 2.5)
                                if has_bg:
                                    bg_alpha = int(255 * tip_alpha)
                                    bg_with_alpha = (*bg_color[:3], bg_alpha)
                                    draw.rectangle(
                                        [(10, 150), (frame_width-10, 210)], fill=bg_with_alpha)

                                tip_color = (
                                    *text_color[:3], int(255 * tip_alpha))
                                draw.text((frame_width//2, 180), tip_text,
                                          font=body_font, fill=tip_color, anchor="mm")

                        elif animation_type == "slide":
                            # Slide in title from left
                            title_x = -300 + progress * (frame_width//2 + 300)
                            # Draw background if needed
                            if has_bg:
                                draw.rectangle(
                                    [(10, 10), (frame_width-10, 70)], fill=bg_color)
                            draw.text((title_x, 40), title_text,
                                      font=title_font, fill=text_color, anchor="mm")

                            # Slide in hook after title starts
                            if progress > 0.3:
                                hook_progress = min(
                                    1.0, (progress - 0.3) * 1.4)
                                hook_x = frame_width + 300 - \
                                    hook_progress * (frame_width//2 + 300)
                                if has_bg:
                                    draw.rectangle(
                                        [(10, 80), (frame_width-10, 140)], fill=bg_color)
                                draw.text(
                                    (hook_x, 110), hook_text, font=body_font, fill=text_color, anchor="mm")

                            # Slide in tip after hook starts
                            if progress > 0.6:
                                tip_progress = min(1.0, (progress - 0.6) * 2.5)
                                tip_y = frame_height + 100 - \
                                    tip_progress * (frame_height//2)
                                if has_bg:
                                    draw.rectangle(
                                        [(10, 150), (frame_width-10, 210)], fill=bg_color)
                                draw.text((frame_width//2, tip_y), tip_text,
                                          font=body_font, fill=text_color, anchor="mm")

                        else:  # Default simple fade for any other type
                            title_alpha = min(1.0, progress * 2)
                            hook_alpha = min(
                                1.0, (progress - 0.3) * 2) if progress > 0.3 else 0
                            tip_alpha = min(1.0, (progress - 0.6)
                                            * 2.5) if progress > 0.6 else 0

                            # Draw with appropriate alpha
                            draw.text((frame_width//2, 40), title_text, font=title_font,
                                      fill=(*text_color[:3], int(255 * title_alpha)), anchor="mm")
                            draw.text((frame_width//2, 110), hook_text, font=body_font,
                                      fill=(*text_color[:3], int(255 * hook_alpha)), anchor="mm")
                            draw.text((frame_width//2, 180), tip_text, font=body_font,
                                      fill=(*text_color[:3], int(255 * tip_alpha)), anchor="mm")

                        # Display the frame
                        frame_image = ImageTk.PhotoImage(img)
                        preview_label.config(image=frame_image)
                        preview_label.image = frame_image  # Keep a reference

                        # Update the window
                        preview_window.update()
                        # 50ms delay between frames (about 20fps)
                        time.sleep(0.05)

                    # Loop the animation once more
                    preview_window.after(500, animate_frames)

                # Start animation after a short delay
                preview_window.after(100, animate_frames)

            except Exception as e:
                error_msg = f"Error creating animation: {e}"
                print(error_msg)
                preview_label.config(text=error_msg, fg="red", image="")

        except Exception as e:
            print(f"Error showing animation preview: {e}")
            messagebox.showerror(
                "Preview Error", f"Could not create animation preview: {e}")

    def hide(self):
        """Hide the style preview panel."""
        self.pack_forget()

    def generate_style_thumbnails(self):
        """Generate thumbnails for each text style."""
        try:
            # Import required modules
            from PIL import Image, ImageDraw, ImageFont
            from io import BytesIO
            import base64

            # Thumbnail size
            width, height = 240, 135  # 16:9 aspect ratio

            # Sample text for thumbnails
            title_text = "Bench Press"
            hook_text = "Engage your core for stability"
            tip_text = "Keep shoulders back throughout"

            # Generate thumbnails for each style
            for style_name in self.style_frames.keys():
                # Create a black background image
                img = Image.new('RGB', (width, height), (0, 0, 0))
                draw = ImageDraw.Draw(img)

                # Get style settings
                style_config = self.get_style_config(style_name)

                # Draw text based on style
                font_name = style_config.get("font", "Arial")
                try:
                    title_font = ImageFont.truetype(font_name, 24)
                    body_font = ImageFont.truetype(font_name, 16)
                except:
                    # Fallback to default
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()

                # Get text color
                text_color = style_config.get("color", "white")
                if text_color == "white":
                    text_color = (255, 255, 255)
                elif text_color.startswith("#"):
                    # Convert hex to RGB
                    text_color = tuple(
                        int(text_color[i:i+2], 16) for i in (1, 3, 5))

                # Draw background if style has it
                if style_config.get("background", False):
                    bg_color = style_config.get(
                        "background_color", (0, 0, 0, 128))
                    # Draw rectangles for text backgrounds
                    draw.rectangle([(10, 10), (width-10, 40)], fill=bg_color)
                    draw.rectangle([(10, 50), (width-10, 90)], fill=bg_color)
                    draw.rectangle([(10, 100), (width-10, 125)], fill=bg_color)

                # Draw text
                draw.text((width//2, 25), title_text,
                          font=title_font, fill=text_color, anchor="mm")
                draw.text((width//2, 70), hook_text, font=body_font,
                          fill=text_color, anchor="mm")
                draw.text((width//2, 112), tip_text, font=body_font,
                          fill=text_color, anchor="mm")

                # Add style indicator
                style_indicator = style_name.replace("_", " ").title()
                draw.text((width-10, height-10), style_indicator,
                          font=body_font, fill=text_color, anchor="rb")

                # Convert to a format tkinter can use
                self.style_thumbnails[style_name] = self.pil_to_tkinter(img)

                # Update thumbnail label
                if style_name in self.thumbnail_labels:
                    self.thumbnail_labels[style_name].config(
                        image=self.style_thumbnails[style_name], text="")

            print("Generated style thumbnails successfully")

        except Exception as e:
            print(f"Error generating thumbnails: {e}")


class InstagramStylePanel(Frame):
    """
    A modern Instagram-like style selection interface with high-quality animations.
    """

    def __init__(self, parent, config, video_path=None, on_style_selected=None):
        """Initialize the Instagram-style panel."""
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.video_path = video_path
        self.on_style_selected = on_style_selected
        self.current_style = config.get("text_style", "instagram_classic")

        # Set dark theme colors
        self.bg_color = "#121212"  # Instagram dark mode background
        self.text_color = "#FFFFFF"  # White text
        self.accent_color = "#3897F0"  # Instagram blue
        self.card_color = "#262626"  # Slightly lighter background for cards
        self.configure(bg=self.bg_color)

        # Style frames and elements
        self.style_frames = {}
        self.style_buttons = {}
        self.style_thumbnails = {}
        self.video_frame = None
        self.current_animation = None
        self.process_all_after_selection = False

        # Create widgets
        self.create_widgets()

        # Initially hidden
        self.pack_forget()

    def create_widgets(self):
        """Create the Instagram-like interface widgets."""
        # Configure the font styles
        title_font = ("Helvetica", 18, "bold")
        subtitle_font = ("Helvetica", 12)
        button_font = ("Helvetica", 12, "bold")

        # Create a top header
        self.header_frame = Frame(self, bg=self.bg_color, pady=10)
        self.header_frame.pack(side=TOP, fill=X)

        # Back button in header
        self.back_button = Button(
            self.header_frame,
            text="← Back",
            font=button_font,
            bg=self.bg_color,
            fg=self.text_color,
            bd=0,
            activebackground=self.bg_color,
            activeforeground=self.accent_color,
            cursor="hand2",
            command=self.hide
        )
        self.back_button.pack(side=LEFT, padx=20)

        # Title in header
        self.title_label = Label(
            self.header_frame,
            text="Choose Your Style",
            font=title_font,
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.pack(side=LEFT, expand=TRUE)

        # Done button in header
        self.done_button = Button(
            self.header_frame,
            text="Apply & Process",
            font=button_font,
            bg=self.accent_color,
            fg=self.text_color,
            bd=0,
            activebackground="#2D6DA8",  # Darker blue when active
            activeforeground=self.text_color,
            cursor="hand2",
            command=self.apply_and_process
        )
        self.done_button.pack(side=RIGHT, padx=20)

        # Create main content area with video preview and style selection
        self.content_frame = Frame(self, bg=self.bg_color)
        self.content_frame.pack(side=TOP, fill=BOTH,
                                expand=TRUE, padx=20, pady=10)

        # Left side - Video preview area
        self.preview_frame = Frame(self.content_frame, bg=self.bg_color)
        self.preview_frame.pack(side=LEFT, fill=BOTH, expand=TRUE, padx=10)

        # Video preview container (16:9 aspect ratio)
        self.video_frame = Frame(
            self.preview_frame,
            bg="black",
            width=640,
            height=360
        )
        self.video_frame.pack(side=TOP, padx=10, pady=10)
        self.video_frame.pack_propagate(FALSE)  # Maintain size

        # Placeholder for video preview
        self.video_preview_label = Label(
            self.video_frame,
            text="Video Preview",
            font=title_font,
            bg="black",
            fg="white"
        )
        self.video_preview_label.pack(fill=BOTH, expand=TRUE)

        # Information about current style
        self.style_info_frame = Frame(
            self.preview_frame, bg=self.bg_color, pady=10)
        self.style_info_frame.pack(side=TOP, fill=X)

        self.current_style_label = Label(
            self.style_info_frame,
            text=f"Current style: {self.current_style.replace('_', ' ').title()}",
            font=subtitle_font,
            bg=self.bg_color,
            fg=self.text_color
        )
        self.current_style_label.pack(side=TOP)

        self.style_description = Label(
            self.style_info_frame,
            text=self.get_style_description(self.current_style),
            font=subtitle_font,
            bg=self.bg_color,
            fg=self.text_color,
            wraplength=600
        )
        self.style_description.pack(side=TOP, pady=5)

        # Right side - Style selection options
        self.styles_frame = Frame(self.content_frame, bg=self.bg_color)
        self.styles_frame.pack(side=RIGHT, fill=Y, padx=10)

        # Style selection label
        self.styles_label = Label(
            self.styles_frame,
            text="Animation Styles",
            font=subtitle_font,
            bg=self.bg_color,
            fg=self.text_color
        )
        self.styles_label.pack(side=TOP, pady=(0, 10))

        # Create scrollable frame for styles
        self.styles_canvas = Canvas(
            self.styles_frame,
            bg=self.bg_color,
            bd=0,
            highlightthickness=0,
            width=200
        )
        self.styles_canvas.pack(side=LEFT, fill=Y, expand=TRUE)

        # Add scrollbar to canvas
        self.styles_scrollbar = Scrollbar(
            self.styles_frame,
            orient=VERTICAL,
            command=self.styles_canvas.yview
        )
        self.styles_scrollbar.pack(side=RIGHT, fill=Y)
        self.styles_canvas.configure(yscrollcommand=self.styles_scrollbar.set)

        # Create frame inside canvas to hold style options
        self.styles_container = Frame(self.styles_canvas, bg=self.bg_color)
        self.styles_canvas.create_window(
            (0, 0), window=self.styles_container, anchor=NW)

        # Add style options
        self.create_style_options()

        # Update scrollregion when the size of the frame changes
        self.styles_container.bind("<Configure>", lambda e: self.styles_canvas.configure(
            scrollregion=self.styles_canvas.bbox("all")
        ))

    def create_style_options(self):
        """Create Instagram-like style selection buttons."""
        # Available styles
        styles = [
            ("instagram_classic", "Instagram Classic"),
            ("minimal", "Minimal"),
            ("bold_statement", "Bold Statement"),
            ("fitness_pro", "Fitness Pro"),
            ("instagram_story", "Instagram Story"),
            ("typewriter", "Typewriter"),
            ("bouncy_text", "Bouncy Text"),
            ("slide_up", "Slide Up"),
            ("glowing", "Glowing"),
            ("zoom_in", "Zoom In")
        ]

        # Create a button for each style
        for i, (style_id, style_name) in enumerate(styles):
            # Check if style exists in TEXT_STYLES
            if i >= 4:  # Custom styles we'll add later
                # Add extra styles to our custom implementation
                pass

            # Create style frame
            style_frame = Frame(
                self.styles_container,
                bg=self.card_color,
                padx=10,
                pady=10,
                bd=1,
                relief=FLAT
            )
            style_frame.pack(side=TOP, fill=X, pady=5)

            # Create style button
            style_button = Button(
                style_frame,
                text=style_name,
                font=("Helvetica", 11),
                bg=self.card_color,
                fg=self.text_color,
                activebackground=self.accent_color,
                activeforeground=self.text_color,
                bd=0,
                cursor="hand2",
                anchor=W,
                command=lambda s=style_id: self.select_style(s)
            )
            style_button.pack(side=TOP, fill=X, pady=2)

            # Add a preview button
            preview_button = Button(
                style_frame,
                text="Preview",
                font=("Helvetica", 9),
                bg=self.card_color,
                fg=self.accent_color,
                activebackground=self.card_color,
                activeforeground=self.text_color,
                bd=1,
                relief=FLAT,
                cursor="hand2",
                command=lambda s=style_id: self.preview_style(s)
            )
            preview_button.pack(side=TOP, pady=2)

            # Highlight current style
            if style_id == self.current_style:
                style_frame.config(bg=self.accent_color)
                style_button.config(bg=self.accent_color)
                preview_button.config(bg=self.accent_color, fg=self.text_color)

            # Store references
            self.style_frames[style_id] = style_frame
            self.style_buttons[style_id] = style_button

    def get_style_description(self, style_name):
        """Get a description of the selected style."""
        descriptions = {
            "instagram_classic": "The classic Instagram style with smooth fade and slide animations. Perfect for fitness videos that need a clean, professional look.",
            "minimal": "A subtle, clean design with simple fade animations. Ideal for videos where the focus should be on the movement.",
            "bold_statement": "Makes a strong impression with dramatic slide animations and bold text. Great for highlight videos or promotional content.",
            "fitness_pro": "Designed specifically for fitness professionals with energetic animations. Helps viewers focus on proper form and technique.",
            "instagram_story": "Modern, trendy animations inspired by Instagram stories. Full-screen text with smooth transitions for maximum impact.",
            "typewriter": "Text appears character by character, like someone is typing in real-time. Creates engagement and anticipation.",
            "bouncy_text": "Fun, energetic animations where text bounces into place. Great for upbeat, motivational content.",
            "slide_up": "Clean, professional animations where text slides up from the bottom. Perfect for step-by-step instructions.",
            "glowing": "Text pulses with a subtle glow effect. Draws attention to important form tips or instructions.",
            "zoom_in": "Text starts small and zooms into place. Creates a dramatic, eye-catching effect."
        }
        return descriptions.get(style_name, "A custom text style with animations.")

    def select_style(self, style_name):
        """Select a style and update the interface."""
        print(f"Selected style: {style_name}")

        # Update current style
        self.current_style = style_name

        # Update UI
        self.current_style_label.config(
            text=f"Current style: {style_name.replace('_', ' ').title()}")
        self.style_description.config(
            text=self.get_style_description(style_name))

        # Update config
        self.config.set("text_style", style_name)

        # Update highlighting
        for style_id, frame in self.style_frames.items():
            if style_id == style_name:
                frame.config(bg=self.accent_color)
                self.style_buttons[style_id].config(bg=self.accent_color)
            else:
                frame.config(bg=self.card_color)
                self.style_buttons[style_id].config(bg=self.card_color)

        # Preview the style automatically
        self.preview_style(style_name)

        # Call callback if provided
        if self.on_style_selected:
            self.on_style_selected(style_name)

    def preview_style(self, style_name):
        """Show a preview of the selected style animation."""
        # Stop any current animation
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.after_cancel(self.animation_after_id)

        # Clear previous animation elements
        for widget in self.video_frame.winfo_children():
            if widget != self.video_preview_label:
                widget.destroy()

        # Get style configuration
        style_config = self.get_style_config(style_name)
        animation_type = style_config.get("animation", "fade")

        # Determine text colors and fonts based on style
        text_color = style_config.get("color", "white")
        bg_color = style_config.get("background_color", (0, 0, 0, 128)) if style_config.get(
            "background", False) else None

        if isinstance(text_color, str) and text_color.startswith("#"):
            pass
        else:
            text_color = "white"

        # Create example text frames with the style
        title_frame = Frame(self.video_frame, bg="black")
        title_frame.place(relx=0.5, rely=0.2, anchor=CENTER,
                          width=600, height=60)

        hook_frame = Frame(self.video_frame, bg="black")
        hook_frame.place(relx=0.5, rely=0.5, anchor=CENTER,
                         width=600, height=60)

        tip_frame = Frame(self.video_frame, bg="black")
        tip_frame.place(relx=0.5, rely=0.8, anchor=CENTER,
                        width=600, height=60)

        # Example text
        example_text = {
            "title": "Deadlift",
            "hook": "Power Move for Total Body Strength",
            "tip": "Keep your back straight and core engaged"
        }

        # Create labels for the text
        title_label = Label(
            title_frame,
            text=example_text["title"],
            font=("Impact" if style_name ==
                  "bold_statement" else "Arial", 24, "bold"),
            bg="black" if not bg_color else "#%02x%02x%02x" % bg_color[:3],
            fg=text_color,
            bd=0
        )

        hook_label = Label(
            hook_frame,
            text=example_text["hook"],
            font=("Impact" if style_name == "bold_statement" else "Arial", 18),
            bg="black" if not bg_color else "#%02x%02x%02x" % bg_color[:3],
            fg=text_color,
            bd=0
        )

        tip_label = Label(
            tip_frame,
            text=example_text["tip"],
            font=("Impact" if style_name == "bold_statement" else "Arial", 18),
            bg="black" if not bg_color else "#%02x%02x%02x" % bg_color[:3],
            fg=text_color,
            bd=0
        )

        # Place labels within frames
        title_label.pack(fill=BOTH, expand=TRUE)
        hook_label.pack(fill=BOTH, expand=TRUE)
        tip_label.pack(fill=BOTH, expand=TRUE)

        # Initial state - hide all
        title_frame.place_forget()
        hook_frame.place_forget()
        tip_frame.place_forget()

        # Animations based on style
        if animation_type == "fade" or style_name == "minimal" or style_name == "instagram_classic":
            self.animate_fade(title_frame, hook_frame, tip_frame)
        elif animation_type == "slide" or style_name == "bold_statement":
            self.animate_slide(title_frame, hook_frame, tip_frame)
        elif style_name == "typewriter":
            self.animate_typewriter(
                title_label, hook_label, tip_label, example_text)
        elif style_name == "bouncy_text":
            self.animate_bounce(title_frame, hook_frame, tip_frame)
        elif style_name == "slide_up":
            self.animate_slide_up(title_frame, hook_frame, tip_frame)
        elif style_name == "glowing":
            self.animate_glow(title_label, hook_label, tip_label)
        elif style_name == "zoom_in":
            self.animate_zoom(title_frame, hook_frame, tip_frame)
        else:
            # Default animation
            self.animate_fade(title_frame, hook_frame, tip_frame)

    def animate_fade(self, title_frame, hook_frame, tip_frame):
        """Create a fade-in animation."""
        # Function to create fade effect
        def fade_in(frame, alpha, max_alpha, step=0.05):
            if alpha < max_alpha:
                frame.place(relx=0.5, rely=frame._rely,
                            anchor=CENTER, width=600, height=60)
                alpha += step
                frame.attributes = alpha  # Store alpha value
                self.animation_after_id = self.after(
                    30, lambda: fade_in(frame, alpha, max_alpha, step))
            else:
                # Start next animation if needed
                pass

        # Set positions
        title_frame._rely = 0.2
        hook_frame._rely = 0.5
        tip_frame._rely = 0.8

        # Start fade animations in sequence
        title_frame.attributes = 0.0
        hook_frame.attributes = 0.0
        tip_frame.attributes = 0.0

        # Start first animation
        fade_in(title_frame, 0.0, 1.0)

        # After 500ms, start second animation
        self.after(500, lambda: fade_in(hook_frame, 0.0, 1.0))

        # After 1000ms, start third animation
        self.after(1000, lambda: fade_in(tip_frame, 0.0, 1.0))

    def animate_slide(self, title_frame, hook_frame, tip_frame):
        """Create a slide animation."""
        # Set initial positions off-screen
        title_frame.place(relx=-0.5, rely=0.2, anchor=CENTER,
                          width=600, height=60)
        hook_frame.place(relx=1.5, rely=0.5, anchor=CENTER,
                         width=600, height=60)
        tip_frame.place(relx=-0.5, rely=0.8, anchor=CENTER,
                        width=600, height=60)

        # Function to slide element
        def slide(frame, start_x, end_x, step=0.05):
            current_x = frame.place_info()['relx']
            current_x = float(current_x)

            if (start_x < end_x and current_x < end_x) or (start_x > end_x and current_x > end_x):
                next_x = current_x + step if start_x < end_x else current_x - step
                frame.place(relx=next_x, rely=frame.place_info()[
                            'rely'], anchor=CENTER, width=600, height=60)
                self.animation_after_id = self.after(
                    20, lambda: slide(frame, start_x, end_x, step))

        # Start slide animations
        slide(title_frame, -0.5, 0.5)
        self.after(400, lambda: slide(hook_frame, 1.5, 0.5))
        self.after(800, lambda: slide(tip_frame, -0.5, 0.5))

    def animate_typewriter(self, title_label, hook_label, tip_label, example_text):
        """Create a typewriter animation."""
        # Place frames
        title_label.master.place(
            relx=0.5, rely=0.2, anchor=CENTER, width=600, height=60)
        hook_label.master.place(
            relx=0.5, rely=0.5, anchor=CENTER, width=600, height=60)
        tip_label.master.place(
            relx=0.5, rely=0.8, anchor=CENTER, width=600, height=60)

        # Set initial empty text
        title_label.config(text="")
        hook_label.config(text="")
        tip_label.config(text="")

        # Function to simulate typing
        def type_text(label, full_text, index=0, delay=50):
            if index <= len(full_text):
                label.config(text=full_text[:index])
                self.animation_after_id = self.after(
                    delay, lambda: type_text(label, full_text, index + 1, delay))

        # Start typing animations in sequence
        type_text(title_label, example_text["title"])
        self.after(1000, lambda: type_text(hook_label, example_text["hook"]))
        self.after(2500, lambda: type_text(tip_label, example_text["tip"]))

    def animate_bounce(self, title_frame, hook_frame, tip_frame):
        """Create a bouncing animation."""
        # Set initial positions
        title_frame.place(relx=0.5, rely=-0.2, anchor=CENTER,
                          width=600, height=60)
        hook_frame.place(relx=0.5, rely=-0.2, anchor=CENTER,
                         width=600, height=60)
        tip_frame.place(relx=0.5, rely=-0.2, anchor=CENTER,
                        width=600, height=60)

        # Function to create bounce effect
        def bounce(frame, target_y, bounce_height=0.05, steps=20):
            current_y = float(frame.place_info()['rely'])
            distance = target_y - current_y

            if abs(distance) > 0.01:
                next_y = current_y + distance / steps
                frame.place(relx=0.5, rely=next_y,
                            anchor=CENTER, width=600, height=60)
                self.animation_after_id = self.after(
                    20, lambda: bounce(frame, target_y, bounce_height, steps))
            else:
                # Add small bounces
                self.after(50, lambda: frame.place(
                    relx=0.5, rely=target_y+bounce_height, anchor=CENTER, width=600, height=60))
                self.after(100, lambda: frame.place(
                    relx=0.5, rely=target_y-bounce_height/2, anchor=CENTER, width=600, height=60))
                self.after(150, lambda: frame.place(
                    relx=0.5, rely=target_y+bounce_height/4, anchor=CENTER, width=600, height=60))
                self.after(200, lambda: frame.place(
                    relx=0.5, rely=target_y, anchor=CENTER, width=600, height=60))

        # Start bounce animations
        bounce(title_frame, 0.2)
        self.after(400, lambda: bounce(hook_frame, 0.5))
        self.after(800, lambda: bounce(tip_frame, 0.8))

    def animate_slide_up(self, title_frame, hook_frame, tip_frame):
        """Create a slide-up animation."""
        # Set initial positions
        title_frame.place(relx=0.5, rely=1.2, anchor=CENTER,
                          width=600, height=60)
        hook_frame.place(relx=0.5, rely=1.4, anchor=CENTER,
                         width=600, height=60)
        tip_frame.place(relx=0.5, rely=1.6, anchor=CENTER,
                        width=600, height=60)

        # Function to slide up
        def slide_up(frame, target_y, steps=20):
            current_y = float(frame.place_info()['rely'])
            distance = target_y - current_y

            if abs(distance) > 0.01:
                next_y = current_y + distance / steps
                frame.place(relx=0.5, rely=next_y,
                            anchor=CENTER, width=600, height=60)
                self.animation_after_id = self.after(
                    20, lambda: slide_up(frame, target_y, steps))

        # Start slide-up animations
        slide_up(title_frame, 0.2)
        self.after(300, lambda: slide_up(hook_frame, 0.5))
        self.after(600, lambda: slide_up(tip_frame, 0.8))

    def animate_glow(self, title_label, hook_label, tip_label):
        """Create a glow animation effect."""
        # Place frames
        title_label.master.place(
            relx=0.5, rely=0.2, anchor=CENTER, width=600, height=60)
        hook_label.master.place(
            relx=0.5, rely=0.5, anchor=CENTER, width=600, height=60)
        tip_label.master.place(
            relx=0.5, rely=0.8, anchor=CENTER, width=600, height=60)

        # Set initial transparent text
        title_label.configure(fg="#FFFFFF")
        hook_label.configure(fg="#FFFFFF")
        tip_label.configure(fg="#FFFFFF")

        # Function to create glow effect by alternating colors
        def glow(label, glow_colors, index=0):
            if index < len(glow_colors):
                label.configure(fg=glow_colors[index])
                self.animation_after_id = self.after(100, lambda: glow(
                    label, glow_colors, (index + 1) % len(glow_colors)))

        # Define glow color sequence
        glow_colors_title = ["#FFFFFF", "#FFFFCC", "#FFFFFF", "#CCCCFF"]
        glow_colors_hook = ["#FFFFFF", "#CCFFCC", "#FFFFFF", "#CCFFFF"]
        glow_colors_tip = ["#FFFFFF", "#FFCCCC", "#FFFFFF", "#FFFFCC"]

        # Start glow animations
        self.after(200, lambda: glow(title_label, glow_colors_title))
        self.after(700, lambda: glow(hook_label, glow_colors_hook))
        self.after(1200, lambda: glow(tip_label, glow_colors_tip))

    def animate_zoom(self, title_frame, hook_frame, tip_frame):
        """Create a zoom-in animation."""
        # Set initial scaling (very small)
        title_frame.place(relx=0.5, rely=0.2, anchor=CENTER,
                          width=10, height=10)
        hook_frame.place(relx=0.5, rely=0.5, anchor=CENTER,
                         width=10, height=10)
        tip_frame.place(relx=0.5, rely=0.8, anchor=CENTER, width=10, height=10)

        # Function to zoom in
        def zoom(frame, target_width, target_height, steps=20):
            current_width = int(frame.place_info()['width'])
            current_height = int(frame.place_info()['height'])

            width_diff = target_width - current_width
            height_diff = target_height - current_height

            if abs(width_diff) > 10:
                next_width = current_width + width_diff // steps
                next_height = current_height + height_diff // steps

                frame.place(relx=0.5, rely=float(frame.place_info()['rely']),
                            anchor=CENTER, width=next_width, height=next_height)
                self.animation_after_id = self.after(
                    20, lambda: zoom(frame, target_width, target_height, steps))

        # Start zoom animations
        zoom(title_frame, 600, 60)
        self.after(500, lambda: zoom(hook_frame, 600, 60))
        self.after(1000, lambda: zoom(tip_frame, 600, 60))

    def get_style_config(self, style_name):
        """Get style configuration from text_overlay_generator or defaults."""
        # Default style settings
        default_styles = {
            "instagram_classic": {
                "font": "Arial",
                "color": "white",
                "background": True,
                "background_color": (255, 90, 95, 230),
                "animation": "fade",
            },
            "minimal": {
                "font": "Arial",
                "color": "white",
                "shadow": True,
                "shadow_color": "black",
                "background": False,
                "animation": "fade",
            },
            "bold_statement": {
                "font": "Impact",
                "color": "white",
                "shadow": True,
                "shadow_color": "black",
                "background": True,
                "background_color": (0, 0, 0, 128),
                "animation": "slide",
            },
            "fitness_pro": {
                "font": "Arial",
                "color": "#FF4500",
                "accent_color": "#0096FF",
                "shadow": False,
                "background": False,
                "animation": "fade",
            },
            "instagram_story": {
                "font": "Arial",
                "color": "white",
                "background": True,
                "background_color": (255, 90, 95, 230),
                "animation": "slide",
            },
            "typewriter": {
                "font": "Arial",
                "color": "white",
                "background": False,
                "animation": "typewriter",
            },
            "bouncy_text": {
                "font": "Arial",
                "color": "#FF9500",
                "background": False,
                "animation": "bounce",
            },
            "slide_up": {
                "font": "Arial",
                "color": "white",
                "background": True,
                "background_color": (0, 120, 255, 200),
                "animation": "slide_up",
            },
            "glowing": {
                "font": "Arial",
                "color": "#FFFFFF",
                "background": False,
                "animation": "glow",
            },
            "zoom_in": {
                "font": "Arial",
                "color": "white",
                "background": True,
                "background_color": (80, 200, 120, 200),
                "animation": "zoom",
            }
        }

        try:
            # Try to import real styles
            from text_overlay_generator import TEXT_STYLES
            if style_name in TEXT_STYLES:
                return TEXT_STYLES[style_name]
            elif style_name in default_styles:
                return default_styles[style_name]
            else:
                return default_styles["minimal"]
        except:
            if style_name in default_styles:
                return default_styles[style_name]
            else:
                return default_styles["minimal"]

    def apply_and_process(self):
        """Apply selected style and process the video."""
        # Update config with selected style
        self.config.set("text_style", self.current_style)
        print(f"Applying style '{self.current_style}' and processing video")

        # Hide panel
        self.hide()

        # Call callback to process video
        if self.on_style_selected:
            self.on_style_selected(self.current_style, process=True)

    def show(self, video_path=None):
        """Show the Instagram-like interface."""
        if video_path:
            self.video_path = video_path
            self.title_label.config(
                text=f"Style: {os.path.basename(video_path)}")

            # If possible, show video thumbnail
            self.load_video_thumbnail(video_path)

        # Default style from config
        self.current_style = self.config.get("text_style", "instagram_classic")

        # Update style selection
        for style_id, frame in self.style_frames.items():
            if style_id == self.current_style:
                frame.config(bg=self.accent_color)
                self.style_buttons[style_id].config(bg=self.accent_color)
            else:
                frame.config(bg=self.card_color)
                self.style_buttons[style_id].config(bg=self.card_color)

        # Update style info
        self.current_style_label.config(
            text=f"Current style: {self.current_style.replace('_', ' ').title()}")
        self.style_description.config(
            text=self.get_style_description(self.current_style))

        # Preview the current style
        self.preview_style(self.current_style)

        # Show the panel
        self.pack(side=TOP, fill=BOTH, expand=TRUE)

    def load_video_thumbnail(self, video_path):
        """Load a thumbnail from the video for preview."""
        try:
            # Import required modules
            from moviepy.editor import VideoFileClip
            from PIL import Image, ImageTk
            import numpy as np

            # Open video and get a frame
            video = VideoFileClip(video_path)
            target_time = min(1.0, video.duration / 2)
            frame = video.get_frame(target_time)

            # Convert to PIL Image and resize to fit frame
            frame_img = Image.fromarray(frame)

            # Calculate new size maintaining aspect ratio
            width, height = frame_img.size
            target_width = self.video_frame.winfo_width() or 640
            target_height = self.video_frame.winfo_height() or 360

            # Calculate ratio to fit in bounds
            ratio = min(target_width / width, target_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # Resize image
            frame_img = frame_img.resize(
                (new_width, new_height), Image.LANCZOS)

            # Convert to Tkinter-compatible image
            tk_img = ImageTk.PhotoImage(frame_img)

            # Update preview label
            self.video_preview_label.config(image=tk_img, text="")
            self.video_preview_label.image = tk_img  # Keep a reference

            # Clean up
            video.close()

        except Exception as e:
            print(f"Error loading video thumbnail: {e}")
            self.video_preview_label.config(
                text=f"Could not load preview for:\n{os.path.basename(video_path)}")

    def hide(self):
        """Hide the panel."""
        # Stop any ongoing animations
        if hasattr(self, 'animation_after_id') and self.animation_after_id:
            self.after_cancel(self.animation_after_id)
            self.animation_after_id = None

        # Hide the panel
        self.pack_forget()


class SettingsPanel(LabelFrame):
    """
    A panel for configuring the application settings.
    """

    def __init__(self, parent, config):
        """Initialize the settings panel."""
        super().__init__(parent, text="Settings")
        self.parent = parent
        self.config = config
        self.create_widgets()

    def create_widgets(self):
        """Create the widgets for the settings panel."""
        # Use a more compact grid layout instead of packed frames
        settings_frame = Frame(self)
        settings_frame.pack(side=TOP, fill=BOTH, expand=TRUE, padx=5, pady=5)

        # Set up grid columns
        # Label column (fixed width)
        settings_frame.columnconfigure(0, weight=0)
        # Entry/combobox column (flexible)
        settings_frame.columnconfigure(1, weight=1)
        # Button column (fixed width)
        settings_frame.columnconfigure(2, weight=0)

        # Row 0: Directory setting
        Label(settings_frame, text="Monitor Directory:", width=15,
              anchor=W).grid(row=0, column=0, padx=5, pady=2, sticky=W)
        self.dir_var = StringVar(value=self.config.get("monitor_directory"))
        Entry(settings_frame, textvariable=self.dir_var, width=30).grid(
            row=0, column=1, padx=5, pady=2, sticky=EW)
        Button(settings_frame, text="Browse", command=self.browse_directory).grid(
            row=0, column=2, padx=5, pady=2)

        # Row 1: Text style setting
        Label(settings_frame, text="Text Style:", width=15, anchor=W).grid(
            row=1, column=0, padx=5, pady=2, sticky=W)
        self.style_var = StringVar(value=self.config.get("text_style"))
        style_options = ["minimal", "bold_statement",
                         "fitness_pro", "instagram_classic"]
        ttk.Combobox(settings_frame, textvariable=self.style_var, values=style_options).grid(
            row=1, column=1, padx=5, pady=2, sticky=EW)

        # Row 2: Hook position setting
        Label(settings_frame, text="Hook Position:", width=15, anchor=W).grid(
            row=2, column=0, padx=5, pady=2, sticky=W)
        self.hook_var = StringVar(value=self.config.get("hook_position"))
        hook_options = list(TEXT_POSITIONS.keys())
        ttk.Combobox(settings_frame, textvariable=self.hook_var, values=hook_options).grid(
            row=2, column=1, padx=5, pady=2, sticky=EW)

        # Row 3: Tip position setting
        Label(settings_frame, text="Tip Position:", width=15, anchor=W).grid(
            row=3, column=0, padx=5, pady=2, sticky=W)
        self.tip_var = StringVar(value=self.config.get("tip_position"))
        tip_options = list(TEXT_POSITIONS.keys())
        ttk.Combobox(settings_frame, textvariable=self.tip_var, values=tip_options).grid(
            row=3, column=1, padx=5, pady=2, sticky=EW)

        # Row 4: Auto-process existing setting
        Label(settings_frame, text="Auto-Process:", width=15,
              anchor=W).grid(row=4, column=0, padx=5, pady=2, sticky=W)
        self.auto_var = BooleanVar(
            value=self.config.get("auto_process_existing"))
        Checkbutton(settings_frame, text="Process existing videos on startup",
                    variable=self.auto_var).grid(row=4, column=1, padx=5, pady=2, sticky=W)

        # Row 5: Buttons in a horizontal frame
        buttons_frame = Frame(settings_frame)
        buttons_frame.grid(row=5, column=0, columnspan=3, pady=5, sticky=EW)

        Button(buttons_frame, text="Reset to Default",
               command=self.reset_to_default).pack(side=LEFT, padx=5)
        Button(buttons_frame, text="Save Settings",
               command=self.save_settings).pack(side=RIGHT, padx=5)

    def browse_directory(self):
        """Open a directory browser dialog."""
        # Get current directory from config
        current_dir = self.config.get("monitor_directory")

        # If directory doesn't exist, use a reasonable default
        if not current_dir or not os.path.exists(current_dir):
            # Try to find a good starting directory with videos
            initial_dirs = [
                os.path.join(os.path.expanduser("~"), "OneDrive",
                             "Desktop", "shanbot", "Content Videos"),
                os.path.join(os.path.expanduser("~"), "OneDrive",
                             "Desktop", "Final Edits"),
                os.path.join(os.path.expanduser("~"), "OneDrive",
                             "Desktop", "random camera clips"),
                os.path.join(os.path.expanduser("~"),
                             "OneDrive", "Desktop", "camera"),
                os.path.join(os.path.expanduser("~"), "OneDrive",
                             "Desktop", "back day 2025"),
                os.path.join(os.path.expanduser("~"), "OneDrive",
                             "Desktop", "shanbot", "22.04", "Trainerize vids"),
            ]

            # Find the first directory that exists
            for dir_path in initial_dirs:
                if os.path.exists(dir_path):
                    current_dir = dir_path
                    break

            # Fall back to user's home directory
            if not current_dir or not os.path.exists(current_dir):
                current_dir = os.path.expanduser("~")

        print(f"Opening directory browser at: {current_dir}")

        directory = filedialog.askdirectory(
            initialdir=current_dir,
            title="Select Directory to Monitor"
        )

        if directory:
            self.dir_var.set(directory)
            print(f"Selected directory: {directory}")

    def save_settings(self):
        """Save the current settings to the configuration."""
        try:
            # Update configuration
            self.config.set("monitor_directory", self.dir_var.get())
            self.config.set("text_style", self.style_var.get())
            self.config.set("hook_position", self.hook_var.get())
            self.config.set("tip_position", self.tip_var.get())
            self.config.set("auto_process_existing", self.auto_var.get())

            messagebox.showinfo("Settings", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")

    def reset_to_default(self):
        """Reset settings to default values."""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset to default settings?"):
            # Reset to default
            self.dir_var.set(auto_labeler.DEFAULT_MONITOR_DIR)
            self.style_var.set("minimal")
            self.hook_var.set("center_focus")
            self.tip_var.set("bottom_banner")
            self.auto_var.set(False)


class VideoAutoLabelerGUI:
    """
    Main GUI for the Fitness Video Auto-Labeler application.
    """

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Fitness Video Auto-Labeler")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)

        # Set icon
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # Create configuration object
        self.config = auto_labeler.Config()

        # Create main frame that takes 70% of the window height
        self.main_frame = Frame(self.root)
        self.main_frame.pack(side=TOP, fill=BOTH, expand=TRUE, pady=5)

        # Create panels
        self.create_panels()

        # Configure grid
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=2)
        # Top row gets 70% of main frame
        self.main_frame.rowconfigure(0, weight=7)
        # Progress bar row
        self.main_frame.rowconfigure(1, weight=0)
        # Console gets 30% of main frame
        self.main_frame.rowconfigure(2, weight=3)

        # Bottom frame for settings and controls (30% of window height)
        self.bottom_frame = Frame(self.root)
        self.bottom_frame.pack(side=BOTTOM, fill=X, expand=FALSE)

        # Create settings panel in bottom frame
        self.settings_panel = SettingsPanel(self.bottom_frame, self.config)
        self.settings_panel.pack(side=TOP, fill=X, padx=10, pady=5)

        # Create control buttons in bottom frame
        self.buttons_frame = Frame(self.bottom_frame)
        self.buttons_frame.pack(side=TOP, fill=X, padx=10, pady=5)

        # Start/Stop monitoring button
        self.monitor_button_text = StringVar(value="Start Monitoring")
        self.monitor_button = Button(
            self.buttons_frame,
            textvariable=self.monitor_button_text,
            command=self.toggle_monitoring,
            width=15
        )
        self.monitor_button.pack(side=LEFT, padx=5)

        # Process selected video button
        self.process_button = Button(
            self.buttons_frame,
            text="Process Selected",
            command=self.process_selected,
            width=15
        )
        self.process_button.pack(side=LEFT, padx=5)

        # Add a "Choose Style" button for direct style selection
        self.style_button = Button(
            self.buttons_frame,
            text="Choose Style",
            command=self.choose_style,
            width=15
        )
        self.style_button.pack(side=LEFT, padx=5)

        # Add video button
        self.add_button = Button(
            self.buttons_frame,
            text="Add Video",
            command=self.add_video,
            width=15
        )
        self.add_button.pack(side=LEFT, padx=5)

        # Process all videos button
        self.process_all_button = Button(
            self.buttons_frame,
            text="Process All",
            command=self.process_all,
            width=15
        )
        self.process_all_button.pack(side=RIGHT, padx=5)

        # Create status bar
        self.status_var = StringVar()
        self.status_var.set("Ready")
        self.status_bar = Label(
            self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Initialize monitoring thread
        self.monitoring_running = False
        self.monitor_thread = None

        # Create video processing queue
        self.processing_queue = queue.Queue()

        # Create video handler
        self.video_handler = None

        # Periodically update the UI
        self.update_ui()

    def create_panels(self):
        """Create the panels for the GUI."""
        # Create preview panel
        self.preview_panel = VideoPreviewPanel(self.main_frame)
        self.preview_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Create queue panel
        self.queue_panel = VideoQueuePanel(self.main_frame, self.preview_panel)
        self.queue_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create style preview panel (initially hidden)
        self.style_panel = InstagramStylePanel(
            self.root, self.config, self.preview_panel.current_video, self.on_style_selected)

        # Create progress bar for processing status
        self.progress_frame = Frame(self.main_frame)
        self.progress_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=0)

        # Progress bar label
        self.progress_label = Label(
            self.progress_frame, text="Processing Progress:")
        self.progress_label.pack(side=LEFT, padx=5)

        # Progress bar
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=200,
            mode='determinate'
        )
        self.progress_bar.pack(side=LEFT, fill=X, expand=TRUE, padx=5)

        # Progress percentage
        self.progress_percent = Label(self.progress_frame, text="0%")
        self.progress_percent.pack(side=RIGHT, padx=5)

        # Hide progress bar initially
        self.progress_frame.grid_remove()

        # Create console output panel
        self.console_frame = LabelFrame(self.main_frame, text="Console Output")
        self.console_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.console_text = ScrolledText.ScrolledText(
            self.console_frame, state=DISABLED, height=12)  # Increased height
        self.console_text.pack(side=TOP, fill=BOTH,
                               expand=TRUE, padx=5, pady=5)

        # Redirect stdout to console
        self.stdout_redirect = RedirectText(self.console_text)
        sys.stdout = self.stdout_redirect

    def update_ui(self):
        """Update the UI periodically."""
        # Check if monitoring thread is still alive
        if self.monitor_thread and not self.monitor_thread.is_alive():
            self.monitoring_running = False
            self.monitor_button_text.set("Start Monitoring")
            self.status_var.set("Monitoring stopped")

        # Schedule next update
        self.root.after(1000, self.update_ui)

    def toggle_monitoring(self):
        """Toggle the directory monitoring on/off."""
        if not self.monitoring_running:
            # Start monitoring
            try:
                # Save settings first
                self.settings_panel.save_settings()

                # Update status
                self.monitoring_running = True
                self.monitor_button_text.set("Stop Monitoring")
                self.status_var.set(
                    f"Monitoring {self.config.get('monitor_directory')}")

                # Start monitoring in a separate thread
                self.monitor_thread = threading.Thread(
                    target=self.start_monitoring, daemon=True)
                self.monitor_thread.start()

                print(
                    f"Started monitoring {self.config.get('monitor_directory')}")

            except Exception as e:
                messagebox.showerror(
                    "Error", f"Could not start monitoring: {e}")
                self.monitoring_running = False
                self.monitor_button_text.set("Start Monitoring")
        else:
            # Stop monitoring
            self.monitoring_running = False
            self.monitor_button_text.set("Start Monitoring")
            self.status_var.set("Stopping monitoring...")
            print("Stopping monitoring...")

    def start_monitoring(self):
        """Start monitoring the directory for new videos."""
        try:
            # Get monitoring directory and video extensions
            monitor_dir = self.config.get("monitor_directory")
            video_extensions = self.config.get("video_extensions")

            # Ensure monitoring directory exists
            if not os.path.exists(monitor_dir):
                os.makedirs(monitor_dir, exist_ok=True)
                print(f"Created monitoring directory: {monitor_dir}")

            # Initialize video handler
            self.video_handler = auto_labeler.VideoHandler(
                monitor_dir, video_extensions)

            # Start video processor worker thread
            processor_thread = threading.Thread(
                target=self.video_processor_worker, daemon=True)
            processor_thread.start()

            # Process existing videos if enabled
            if self.config.get("auto_process_existing"):
                self.process_existing_videos(monitor_dir, video_extensions)

            # Start directory observer
            observer = auto_labeler.Observer()
            observer.schedule(self.video_handler, monitor_dir, recursive=True)
            observer.start()

            print(f"Monitoring directory: {monitor_dir}")
            print("Waiting for new videos...")

            # Keep running until monitoring is stopped
            while self.monitoring_running:
                time.sleep(1)

            # Stop observer
            observer.stop()
            observer.join()

            print("Monitoring stopped")
        except Exception as e:
            print(f"Error in monitoring thread: {e}")

    def video_processor_worker(self):
        """Worker thread for processing videos from the queue."""
        while self.monitoring_running:
            try:
                # Get video from queue with 1-second timeout
                video_path = self.processing_queue.get(timeout=1)

                # Process the video
                print(f"Processing video from queue: {video_path}")

                # Update status
                self.status_var.set(
                    f"Processing {os.path.basename(video_path)}")

                # Show progress bar
                self.root.after(0, lambda: self.progress_frame.grid())
                self.root.after(0, lambda: self.progress_var.set(0))
                self.root.after(
                    0, lambda: self.progress_percent.config(text="0%"))

                # Get settings from config
                text_style = self.config.get("text_style", "minimal")
                # Debug output
                print(f"DEBUG: Using text_style from config: '{text_style}'")
                hook_position = self.config.get(
                    "hook_position", "center_focus")
                tip_position = self.config.get("tip_position", "bottom_banner")

                # Create a callback for progress updates
                def update_progress(progress):
                    self.root.after(
                        0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(
                        0, lambda p=progress: self.progress_percent.config(text=f"{int(p)}%"))

                # Process the video with progress updates
                try:
                    # Set initial progress
                    update_progress(5)

                    # Process the video
                    output_path, caption = text_overlay.process_video(
                        video_path,
                        text_style=text_style,
                        hook_position=hook_position,
                        tip_position=tip_position
                    )

                    # Simulate progress updates since we can't get real-time updates from the processor
                    total_steps = 10
                    for i in range(1, total_steps):
                        if not self.monitoring_running:
                            break
                        time.sleep(0.2)  # Brief pause between updates
                        update_progress(
                            i * (90 / total_steps) + 5)  # 5% to 95%

                    # Set to 100% when done
                    update_progress(100)

                    if output_path:
                        # Mark as processed
                        if self.video_handler:
                            self.video_handler.mark_as_processed(video_path)

                        # Add to processed list
                        self.root.after(
                            0, lambda p=output_path: self.queue_panel.add_to_processed(p))

                        # Remove from queue
                        self.root.after(
                            0, lambda p=video_path: self.queue_panel.remove_from_queue(p))

                        # Save caption to a text file
                        if caption:
                            caption_path = os.path.splitext(
                                output_path)[0] + "_caption.txt"
                            with open(caption_path, 'w', encoding='utf-8') as f:
                                f.write(caption)
                            print(f"Caption saved to: {caption_path}")

                        # Update status
                        self.status_var.set(
                            f"Processed {os.path.basename(video_path)}")

                    else:
                        # Update status
                        self.status_var.set(
                            f"Failed to process {os.path.basename(video_path)}")

                finally:
                    # Hide progress bar after a delay
                    self.root.after(
                        2000, lambda: self.progress_frame.grid_remove())

                # Mark task as done
                self.processing_queue.task_done()

            except queue.Empty:
                # Queue is empty, end processing
                processing = False
            except Exception as e:
                print(f"Error in video processor worker: {e}")
                # Update status
                self.status_var.set("Error processing video")
                # Hide progress bar
                self.root.after(0, lambda: self.progress_frame.grid_remove())
                # Mark task as done even if it failed
                try:
                    self.processing_queue.task_done()
                except:
                    pass

    def process_existing_videos(self, directory, video_extensions):
        """
        Process existing videos in the monitoring directory.

        Args:
            directory (str): Directory to scan for videos
            video_extensions (list): List of video file extensions to process
        """
        print(f"Scanning for existing videos in {directory}...")

        try:
            for root, _, files in os.walk(directory):
                # Skip the processed subdirectory
                processed_dir = self.config.get("processed_subdirectory")
                if processed_dir in os.path.normpath(root).split(os.sep):
                    continue

                for filename in files:
                    filepath = os.path.join(root, filename)

                    # Check if it's a video file and not already processed
                    if any(filename.lower().endswith(ext) for ext in video_extensions) and \
                       (not self.video_handler or filepath not in self.video_handler.processed_files) and \
                       "_processed" not in filename:  # Also check for processed in filename

                        print(f"Found existing video: {filepath}")
                        self.processing_queue.put(filepath)

                        # Add to queue panel
                        self.root.after(
                            0, lambda p=filepath: self.queue_panel.add_to_queue(p))

        except Exception as e:
            print(f"Error scanning for existing videos: {e}")

    def process_selected(self):
        """Process the selected video in the queue."""
        selection = self.queue_panel.queue_listbox.curselection()
        if selection:
            index = selection[0]
            video_path = self.queue_panel.video_queue[index]

            # Show the Instagram-style selection panel instead of the old style panel
            self.style_panel.show(video_path)
            self.main_frame.pack_forget()  # Hide main panels
            self.bottom_frame.pack_forget()  # Hide bottom panels
        else:
            messagebox.showinfo(
                "No Selection", "Please select a video from the queue to process.")

    def process_all(self):
        """Process all videos in the queue."""
        if not self.queue_panel.video_queue:
            messagebox.showinfo("Empty Queue", "The video queue is empty.")
            return

        # Show style selection panel first to confirm style for all videos
        if self.queue_panel.video_queue:
            first_video = self.queue_panel.video_queue[0]
            self.style_panel.show(first_video)
            # Set a flag to process all videos after style selection
            self.style_panel.process_all_after_selection = True
            self.main_frame.pack_forget()  # Hide main panels
            self.bottom_frame.pack_forget()  # Hide bottom panels
        else:
            messagebox.showinfo("Empty Queue", "The video queue is empty.")

    def temp_video_processor_worker(self):
        """Temporary worker thread for processing videos from the queue when not monitoring."""
        processing = True
        while processing and not self.processing_queue.empty():
            try:
                # Get video from queue with 1-second timeout
                video_path = self.processing_queue.get(timeout=1)

                # Process the video
                print(f"Processing video from queue: {video_path}")

                # Update status
                self.status_var.set(
                    f"Processing {os.path.basename(video_path)}")

                # Show progress bar
                self.root.after(0, lambda: self.progress_frame.grid())
                self.root.after(0, lambda: self.progress_var.set(0))
                self.root.after(
                    0, lambda: self.progress_percent.config(text="0%"))

                # Get settings from config
                text_style = self.config.get("text_style", "minimal")
                # Debug output
                print(f"DEBUG: Using text_style from config: '{text_style}'")
                hook_position = self.config.get(
                    "hook_position", "center_focus")
                tip_position = self.config.get("tip_position", "bottom_banner")

                # Create a callback for progress updates
                def update_progress(progress):
                    self.root.after(
                        0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(
                        0, lambda p=progress: self.progress_percent.config(text=f"{int(p)}%"))

                # Process the video with progress updates
                try:
                    # Set initial progress
                    update_progress(5)

                    # Process the video
                    output_path, caption = text_overlay.process_video(
                        video_path,
                        text_style=text_style,
                        hook_position=hook_position,
                        tip_position=tip_position
                    )

                    # Simulate progress updates since we can't get real-time updates from the processor
                    total_steps = 10
                    for i in range(1, total_steps):
                        time.sleep(0.2)  # Brief pause between updates
                        update_progress(
                            i * (90 / total_steps) + 5)  # 5% to 95%

                    # Set to 100% when done
                    update_progress(100)

                    if output_path:
                        # Add to processed list
                        self.root.after(
                            0, lambda p=output_path: self.queue_panel.add_to_processed(p))

                        # Remove from queue
                        self.root.after(
                            0, lambda p=video_path: self.queue_panel.remove_from_queue(p))

                        # Save caption to a text file
                        if caption:
                            caption_path = os.path.splitext(
                                output_path)[0] + "_caption.txt"
                            with open(caption_path, 'w', encoding='utf-8') as f:
                                f.write(caption)
                            print(f"Caption saved to: {caption_path}")

                        # Update status
                        self.status_var.set(
                            f"Processed {os.path.basename(video_path)}")

                    else:
                        # Update status
                        self.status_var.set(
                            f"Failed to process {os.path.basename(video_path)}")

                finally:
                    # Hide progress bar after a delay
                    self.root.after(
                        2000, lambda: self.progress_frame.grid_remove())

                # Mark task as done
                self.processing_queue.task_done()

            except queue.Empty:
                # Queue is empty, end processing
                processing = False
            except Exception as e:
                print(f"Error in video processor worker: {e}")
                # Update status
                self.status_var.set("Error processing video")
                # Hide progress bar
                self.root.after(0, lambda: self.progress_frame.grid_remove())
                # Mark task as done even if it failed
                try:
                    self.processing_queue.task_done()
                except:
                    pass

    def add_video(self):
        """Add a video file to the queue."""
        filetypes = [
            ("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv *.MP4 *.MOV *.AVI *.MKV *.WMV"),
            ("All Files", "*.*")
        ]

        # Try to find a good starting directory with videos
        initial_dirs = [
            self.config.get("monitor_directory"),
            os.path.join(os.path.expanduser("~"), "OneDrive",
                         "Desktop", "shanbot", "Content Videos"),
            os.path.join(os.path.expanduser("~"), "OneDrive",
                         "Desktop", "Final Edits"),
            os.path.join(os.path.expanduser("~"), "OneDrive",
                         "Desktop", "random camera clips"),
            os.path.join(os.path.expanduser("~"),
                         "OneDrive", "Desktop", "camera"),
            os.path.join(os.path.expanduser("~"), "OneDrive",
                         "Desktop", "back day 2025"),
            os.path.join(os.path.expanduser("~"), "OneDrive",
                         "Desktop", "shanbot", "22.04", "Trainerize vids"),
        ]

        # Find the first directory that exists
        initial_dir = None
        for dir_path in initial_dirs:
            if dir_path and os.path.exists(dir_path):
                initial_dir = dir_path
                break

        if not initial_dir:
            initial_dir = os.path.expanduser("~")  # Default to home directory

        print(f"Opening file browser at: {initial_dir}")

        video_paths = filedialog.askopenfilenames(
            initialdir=initial_dir,
            title="Select Video File(s)",
            filetypes=filetypes
        )

        if video_paths:
            for video_path in video_paths:
                # Add to queue panel
                self.queue_panel.add_to_queue(video_path)
                print(f"Added {os.path.basename(video_path)} to queue")

    def choose_style(self):
        """Open the style selection panel without a specific video."""
        # Get current video if any is selected
        current_video = None
        selection = self.queue_panel.queue_listbox.curselection()
        if selection:
            index = selection[0]
            current_video = self.queue_panel.video_queue[index]

        # Show the Instagram-style panel
        self.style_panel.show(current_video)
        self.main_frame.pack_forget()  # Hide main panels
        self.bottom_frame.pack_forget()  # Hide bottom panels

    def on_style_selected(self, style_name, process=False):
        """Handle style selection from the style preview panel."""
        print(f"Style selected in main GUI: {style_name}, process: {process}")

        # Update the style in settings panel
        if hasattr(self, 'settings_panel') and hasattr(self.settings_panel, 'style_var'):
            self.settings_panel.style_var.set(style_name)

        if process:
            # Show main panels again
            self.main_frame.pack(side=TOP, fill=BOTH, expand=TRUE, pady=5)
            self.bottom_frame.pack(side=BOTTOM, fill=X, expand=FALSE)

            # Check if we should process all videos
            if hasattr(self.style_panel, 'process_all_after_selection') and self.style_panel.process_all_after_selection:
                # Process all videos with the selected style
                for video_path in self.queue_panel.video_queue:
                    # Add to processing queue
                    self.processing_queue.put(video_path)

                print(
                    f"Added {len(self.queue_panel.video_queue)} videos to processing queue with style: {style_name}")

                # Reset the flag
                self.style_panel.process_all_after_selection = False

                # Start processing if not already monitoring
                if not self.monitoring_running:
                    # Start a temporary processing thread
                    process_thread = threading.Thread(
                        target=self.temp_video_processor_worker,
                        daemon=True
                    )
                    process_thread.start()
            elif hasattr(self.style_panel, 'video_path') and self.style_panel.video_path:
                # Process just the selected video
                video_path = self.style_panel.video_path

                # Add to processing queue
                self.processing_queue.put(video_path)
                print(
                    f"Added {os.path.basename(video_path)} to processing queue with style: {style_name}")

                # Start processing if not already monitoring
                if not self.monitoring_running:
                    # Start a temporary processing thread
                    process_thread = threading.Thread(
                        target=self.temp_video_processor_worker,
                        daemon=True
                    )
                    process_thread.start()


if __name__ == "__main__":
    # Create the root window
    root = Tk()

    # Create the GUI
    app = VideoAutoLabelerGUI(root)

    # Start the main loop
    root.mainloop()

    # Restore stdout
    sys.stdout = sys.__stdout__
