#!/usr/bin/env python

"""
Text Overlay Generator for Fitness Video Auto-Labeler
Generates text overlays for fitness videos based on exercise information.
"""

import os
import json
import random
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from exercise_database import exercise_db

# Text overlay style presets
TEXT_STYLES = {
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
        "background_color": (0, 0, 0, 128),  # Semi-transparent black
        "animation": "slide",
    },
    "fitness_pro": {
        "font": "Montserrat-Bold",
        "color": "#FF4500",  # Bright orange-red
        "accent_color": "#0096FF",  # Bright blue
        "shadow": False,
        "background": False,
        "animation": "fade",
    },
    "instagram_classic": {
        "font": "Arial",
        "color": "white",
        "background": True,
        "background_color": (255, 90, 95, 230),  # Instagram-style pink
        "animation": "slide",
    }
}

# Text positioning templates
TEXT_POSITIONS = {
    "top_banner": {
        "position": "top",
        "padding": 20,
    },
    "bottom_banner": {
        "position": "bottom",
        "padding": 20,
    },
    "side_panel_right": {
        "position": "right",
        "padding": 20,
    },
    "side_panel_left": {
        "position": "left",
        "padding": 20,
    },
    "center_focus": {
        "position": "center",
        "padding": 0,
    },
    "corner_tip": {
        "position": "bottom_right",
        "padding": 30,
    }
}


class TextOverlayGenerator:
    """
    Generates text overlays for fitness videos based on exercise information.
    """

    def __init__(self, style="minimal", position="center_focus"):
        """
        Initialize the text overlay generator.

        Args:
            style (str): The text style preset to use
            position (str): The text position preset to use
        """
        self.style = TEXT_STYLES.get(style, TEXT_STYLES["minimal"])
        self.position = TEXT_POSITIONS.get(
            position, TEXT_POSITIONS["center_focus"])

    def set_style(self, style):
        """Set the text style preset."""
        if style in TEXT_STYLES:
            self.style = TEXT_STYLES[style]
            return True
        return False

    def set_position(self, position):
        """Set the text position preset."""
        if position in TEXT_POSITIONS:
            self.position = TEXT_POSITIONS[position]
            return True
        return False

    def create_hook_text_clip(self, video_clip, hook_text, duration=3.0):
        """
        Create a text clip for the hook at the beginning of the video.

        Args:
            video_clip (VideoClip): The video clip to overlay text on
            hook_text (str): The hook text to display
            duration (float): Duration in seconds to display the hook

        Returns:
            TextClip: The text clip for the hook
        """
        try:
            # Create text clip with the selected style
            font_size = min(video_clip.w // 15, 80)  # Responsive font size

            # Use center position for hook text
            position = "center"

            text_clip = TextClip(
                hook_text,
                fontsize=font_size,
                color=self.style.get("color", "white"),
                font=self.style.get("font", "Arial"),
                stroke_color=self.style.get("shadow_color", "black") if self.style.get(
                    "shadow", False) else None,
                stroke_width=2 if self.style.get("shadow", False) else 0,
                method='caption',
                size=(video_clip.w * 0.8, None)
            )

            # Add background if specified
            if self.style.get("background", False):
                # Create a background with padding
                padding = 20
                bg_width = text_clip.w + padding * 2
                bg_height = text_clip.h + padding * 2

                # Create background clip
                bg_color = self.style.get("background_color", (0, 0, 0, 128))
                bg_clip = ColorClip(size=(bg_width, bg_height), color=bg_color)

                # Composite text over background
                text_with_bg = CompositeVideoClip([
                    bg_clip,
                    text_clip.set_position(("center", "center"))
                ])

                text_clip = text_with_bg

            # Set position based on the position template
            if position == "center":
                text_pos = ("center", "center")
            elif position == "top":
                text_pos = ("center", self.position.get("padding", 20))
            elif position == "bottom":
                text_pos = ("center", video_clip.h - text_clip.h -
                            self.position.get("padding", 20))
            elif position == "left":
                text_pos = (self.position.get("padding", 20), "center")
            elif position == "right":
                text_pos = (video_clip.w - text_clip.w -
                            self.position.get("padding", 20), "center")
            elif position == "bottom_right":
                text_pos = (video_clip.w - text_clip.w - self.position.get("padding", 20),
                            video_clip.h - text_clip.h - self.position.get("padding", 20))
            else:
                text_pos = ("center", "center")

            # Apply animation
            animation = self.style.get("animation", "fade")
            if animation == "fade":
                # Fade in and out
                text_clip = text_clip.set_position(text_pos).set_opacity(
                    lambda t: 1.0 if t > 0.3 and t < duration -
                    0.3 else max(0, min(t / 0.3, (duration - t) / 0.3, 1.0))
                )
            elif animation == "slide":
                # Slide in from left, define a function to avoid multiplying lambda by float
                def position_func(t):
                    if t < duration - 0.5:
                        # Slide in from left
                        offset = text_clip.w * min(t * 3, 1.0)
                        return (max(-text_clip.w, text_pos[0] - text_clip.w + offset), text_pos[1])
                    else:
                        # Slide out to right
                        exit_progress = min((t - (duration - 0.5)) * 2, 1.0)
                        offset = (video_clip.w + text_clip.w) * exit_progress
                        return (text_pos[0] + offset, text_pos[1])

                text_clip = text_clip.set_position(position_func)

            # Set duration and start time
            text_clip = text_clip.set_duration(duration).set_start(0)

            return text_clip
        except Exception as e:
            print(f"Error creating hook text clip: {e}")
            return None

    def create_technique_tip_clips(self, video_clip, tips, start_time=3.0, tip_duration=2.5, position="bottom_banner"):
        """
        Create text clips for technique tips to be displayed sequentially.

        Args:
            video_clip (VideoClip): The video clip to overlay text on
            tips (list): List of technique tip strings
            start_time (float): When to start showing the tips
            tip_duration (float): How long to show each tip
            position (str): Position preset to use for tips

        Returns:
            list: List of TextClip objects with timing information
        """
        try:
            tip_clips = []

            # Use the specified position
            pos_template = TEXT_POSITIONS.get(
                position, TEXT_POSITIONS["bottom_banner"])

            for i, tip in enumerate(tips):
                # Calculate timing
                tip_start = start_time + (i * tip_duration)

                # Create text clip with the selected style
                font_size = min(video_clip.w // 25, 48)  # Responsive font size

                text_clip = TextClip(
                    tip,
                    fontsize=font_size,
                    color=self.style.get("color", "white"),
                    font=self.style.get("font", "Arial"),
                    stroke_color=self.style.get("shadow_color", "black") if self.style.get(
                        "shadow", False) else None,
                    stroke_width=2 if self.style.get("shadow", False) else 0,
                    method='caption',
                    size=(video_clip.w * 0.8, None)
                )

                # Add background if specified
                if self.style.get("background", False):
                    # Create a background with padding
                    padding = 10
                    bg_width = text_clip.w + padding * 2
                    bg_height = text_clip.h + padding * 2

                    # Create background clip
                    bg_color = self.style.get(
                        "background_color", (0, 0, 0, 128))
                    bg_clip = ColorClip(
                        size=(bg_width, bg_height), color=bg_color)

                    # Composite text over background
                    text_with_bg = CompositeVideoClip([
                        bg_clip,
                        text_clip.set_position(("center", "center"))
                    ])

                    text_clip = text_with_bg

                # Set position based on the position template
                if pos_template["position"] == "center":
                    text_pos = ("center", "center")
                elif pos_template["position"] == "top":
                    text_pos = ("center", pos_template.get("padding", 20))
                elif pos_template["position"] == "bottom":
                    text_pos = ("center", video_clip.h -
                                text_clip.h - pos_template.get("padding", 20))
                elif pos_template["position"] == "left":
                    text_pos = (pos_template.get("padding", 20), "center")
                elif pos_template["position"] == "right":
                    text_pos = (video_clip.w - text_clip.w -
                                pos_template.get("padding", 20), "center")
                elif pos_template["position"] == "bottom_right":
                    text_pos = (video_clip.w - text_clip.w - pos_template.get("padding", 20),
                                video_clip.h - text_clip.h - pos_template.get("padding", 20))
                else:
                    text_pos = ("center", "center")

                # Apply animation
                animation = self.style.get("animation", "fade")
                if animation == "fade":
                    # Fade in and out
                    text_clip = text_clip.set_position(text_pos).set_opacity(
                        lambda t: 1.0 if t > 0.3 and t < tip_duration -
                        0.3 else max(0, min(t / 0.3, (tip_duration - t) / 0.3, 1.0))
                    )
                elif animation == "slide":
                    # Slide in from left, define a function to avoid multiplying lambda by float
                    def position_func(t):
                        if t < tip_duration - 0.5:
                            # Slide in from left
                            offset = text_clip.w * min(t * 3, 1.0)
                            return (max(-text_clip.w, text_pos[0] - text_clip.w + offset), text_pos[1])
                        else:
                            # Slide out to right
                            exit_progress = min(
                                (t - (tip_duration - 0.5)) * 2, 1.0)
                            offset = (video_clip.w + text_clip.w) * \
                                exit_progress
                            return (text_pos[0] + offset, text_pos[1])

                    text_clip = text_clip.set_position(position_func)

                # Set duration and start time
                text_clip = text_clip.set_duration(
                    tip_duration).set_start(tip_start)

                tip_clips.append(text_clip)

            return tip_clips
        except Exception as e:
            print(f"Error creating technique tip clips: {e}")
            return []

    def generate_instagram_caption(self, exercise_info):
        """
        Generate an Instagram caption based on exercise information.

        Args:
            exercise_info (dict): Exercise information from the database

        Returns:
            str: Formatted Instagram caption
        """
        try:
            if not exercise_info:
                return "Check out this exercise demonstration! #fitness #workout"

            # Exercise name and basic description
            name = exercise_info.get("name", "Exercise")
            muscles = exercise_info.get("primary_muscles", [])

            # Build caption components
            emoji_options = ["💪", "🔥", "👊", "💯", "⚡", "🏋️", "🏆", "✨"]

            # Random emojis at start and end
            start_emoji = random.choice(emoji_options)
            end_emoji = random.choice(
                [e for e in emoji_options if e != start_emoji])

            # Build the caption
            caption = f"{start_emoji} {name.upper()} FORM BREAKDOWN {end_emoji}\n\n"

            # Add muscle groups
            if muscles:
                muscle_text = ", ".join(
                    [m.replace("_", " ").title() for m in muscles])
                caption += f"Targeting: {muscle_text}\n\n"

            # Add technique tips
            caption += "📝 TECHNIQUE TIPS:\n"
            for tip in exercise_info.get("technique_tips", []):
                # Convert to sentence case and add emoji
                tip_text = tip.capitalize()
                caption += f"• {tip_text}\n"

            caption += f"\nDrop a {start_emoji} if you're adding this to your workout!\n\n"

            # Add hashtags (limit to 30)
            hashtags = exercise_info.get("hashtags", [])

            # Always include these general fitness hashtags
            general_hashtags = [
                "fitnessform", "exercisetips", "fitnesseducation", "formmatters",
                "trainingtips", "workoutroutine", "fitnessgoals", "exerciselibrary",
                "mobilitytraining", "fitlife", "gymtips", "personaltrainer",
                "corestrength", "movementpatterns", "instafitness", "fitnessaddict"
            ]

            # Combine hashtags and limit to 30
            all_hashtags = hashtags + \
                [h for h in general_hashtags if h not in hashtags]
            all_hashtags = all_hashtags[:30]

            hashtag_text = " ".join([f"#{h}" for h in all_hashtags])
            caption += f"{hashtag_text}"

            return caption
        except Exception as e:
            print(f"Error generating Instagram caption: {e}")
            return "Check out this exercise demonstration! #fitness #workout"

    def process_video(self, video_path, output_path=None, text_style="minimal", hook_position="center_focus", tip_position="bottom_banner"):
        """
        Process a video to add text overlays based on the filename.

        Args:
            video_path (str): Path to the video file
            output_path (str): Path to save the processed video, or None to use default naming
            text_style (str): Text style preset to use
            hook_position (str): Position preset for hook text
            tip_position (str): Position preset for technique tips

        Returns:
            tuple: (output_path, caption) - Path to the processed video and Instagram caption
        """
        try:
            print(f"Processing video: {video_path}")

            # Extract exercise info from filename
            filename = os.path.basename(video_path)
            exercise_info = exercise_db.get_exercise_info(filename)

            if not exercise_info:
                print(f"No exercise information found for {filename}")
                return None, None

            print(f"Found exercise info for {exercise_info['name']}")

            # Set text style
            self.set_style(text_style)

            # Load video
            video = VideoFileClip(video_path)

            # Create hook text
            hook_text = exercise_info.get(
                "hook", f"MASTER THE {exercise_info['name'].upper()}")
            hook_clip = self.create_hook_text_clip(
                video, hook_text, duration=3.0)

            # Create technique tips
            tips = exercise_info.get("technique_tips", [])
            tip_clips = self.create_technique_tip_clips(
                video,
                tips,
                start_time=3.0,
                tip_duration=2.5,
                position=tip_position
            )

            # Combine all clips
            all_clips = [video]
            if hook_clip:
                all_clips.append(hook_clip)
            all_clips.extend(tip_clips)

            # Create final video with text overlays
            final_video = CompositeVideoClip(all_clips)

            # Generate output path if not provided
            if not output_path:
                # Create "processed" directory if it doesn't exist
                output_dir = os.path.join(
                    os.path.dirname(video_path), "processed")
                os.makedirs(output_dir, exist_ok=True)

                # Create output filename
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(
                    output_dir, f"{base_name}_processed.mp4")

            # Generate Instagram caption
            caption = self.generate_instagram_caption(exercise_info)

            # Write final video
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="medium"
            )

            print(f"Video processing complete. Saved to: {output_path}")

            return output_path, caption

        except Exception as e:
            print(f"Error processing video: {e}")
            return None, None


# Create a singleton instance
text_overlay = TextOverlayGenerator()
