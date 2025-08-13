"""
Enhanced Text Overlay Patch for Fitness Videos
Adds social media-optimized text animations, styles, and color grading effects
"""

import sys
import os
import importlib
import traceback
import math
import time
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx

# Global flag to track if we've already patched
_PATCH_APPLIED = False


def apply_text_overlay_patch():
    """Apply the enhanced text overlay patch to simple_blue_video.py."""
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        print("Text overlay patch already applied, skipping...")
        return None

    _PATCH_APPLIED = True

    # Block any subsequent import attempts in the same session
    if len(sys.argv) > 1 and sys.argv[1] == "--block-reimport":
        print("Blocking re-import of text overlay patch.")
        sys.exit(0)

    # Helper function for creating text clips
    def create_text_clip(text, position, size=30, fontcolor="white", fontfamily="Arial", text_style="minimal"):
        """Create a TextClip with specified parameters and enhanced styling for social media."""
        try:
            # Determine text styling based on style
            stroke_width = 2
            stroke_color = "black"
            method = 'caption'

            # Enhanced styling for social media
            if text_style == "instagram_classic":
                # Instagram-style: clean, bold with subtle shadow
                fontfamily = "Arial-Bold"
                stroke_width = 1.5

            elif text_style == "bold_statement":
                # Bold impact font with strong outline
                fontfamily = "Impact"
                stroke_width = 3
                stroke_color = "#333333"

            elif text_style == "fitness_pro":
                # Professional fitness style with accent color
                fontfamily = "Arial-Bold"
                if "TIP" in text or "TECHNIQUE" in text:
                    fontcolor = "#0096FF"  # Blue for tips
                elif "FORM" in text:
                    fontcolor = "#FF4500"  # Orange-red for form guidance

            elif text_style == "minimal":
                # Clean minimal style
                fontfamily = "Arial"
                stroke_width = 1

            elif text_style == "instagram_story":
                # Modern, bold Instagram story style
                fontfamily = "Verdana-Bold"
                stroke_width = 0  # No stroke, clean look

            # Create the basic text clip - using explicit import to avoid the local variable issue
            clip = TextClip(
                text,
                fontsize=size,
                color=fontcolor,
                font=fontfamily,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method=method,
                align='center',
                size=(None, None)
            )

            # Calculate position
            if position == "center_focus":
                position = ('center', 'center')
            elif position == "bottom_banner":
                position = ('center', 0.8)
            elif position == "top_banner":
                position = ('center', 0.2)

            # Set the position
            clip = clip.set_position(position)

            # For glowing style, add a subtle glow effect
            if text_style == "glowing":
                clip = apply_glow_animation(
                    clip, glow_duration=3.0, glow_intensity=1.3)

            return clip

        except Exception as e:
            print(f"Error creating text clip: {e}")
            traceback.print_exc()
            # Return a minimal text clip as fallback
            try:
                return TextClip(text, fontsize=size, color=fontcolor).set_position(position)
            except Exception as e2:
                print(f"Failed to create fallback text clip: {e2}")
                return None

    # Enhanced animation functions
    def apply_fade_animation(clip, duration=1.0, direction="in", offset=0):
        """
        Apply enhanced fade animation with different direction options.

        Parameters:
        - clip: The TextClip to animate
        - duration: Duration of the fade effect
        - direction: "in", "out", or "both"
        - offset: Time offset for when to start the effect
        """
        try:
            clip_duration = clip.duration

            if direction == "in" or direction == "both":
                clip = clip.fx(vfx.fadeIn, duration)

            if direction == "out" or direction == "both":
                # For fade out, apply it at the end of the clip
                fade_out_start = max(0, clip_duration - duration - offset)
                clip = clip.fx(vfx.fadeOut, duration).set_start(fade_out_start)

            return clip
        except Exception as e:
            print(f"Error applying fade animation: {e}")
            return clip

    def apply_slide_animation(clip, slide_duration=1.0, direction="left", slide_distance=None):
        """
        Apply enhanced slide animation with various direction options.

        Parameters:
        - clip: The TextClip to animate
        - slide_duration: Duration of the slide effect
        - direction: "left", "right", "up", "down"
        - slide_distance: How far to slide (if None, uses screen width/height)
        """
        try:
            # Get the dimensions
            if hasattr(clip, 'size'):
                w, h = clip.size
            else:
                # Fallback dimensions if size not available
                w, h = 1280, 720

            # Determine slide distance based on direction
            if slide_distance is None:
                if direction in ["left", "right"]:
                    slide_distance = w * 1.5
                else:  # up or down
                    slide_distance = h * 1.5

            # Create the slide animation
            def slide_position(t):
                progress = min(1, t / slide_duration)

                if direction == "left":
                    # Start from right, move to target position
                    start_x = slide_distance
                    current_x = start_x * (1 - progress)
                    return lambda pos: (pos[0] + current_x, pos[1])

                elif direction == "right":
                    # Start from left, move to target position
                    start_x = -slide_distance
                    current_x = start_x * (1 - progress)
                    return lambda pos: (pos[0] + current_x, pos[1])

                elif direction == "up":
                    # Start from bottom, move to target position
                    start_y = slide_distance
                    current_y = start_y * (1 - progress)
                    return lambda pos: (pos[0], pos[1] + current_y)

                elif direction == "down":
                    # Start from top, move to target position
                    start_y = -slide_distance
                    current_y = start_y * (1 - progress)
                    return lambda pos: (pos[0], pos[1] + current_y)

                else:
                    # Default - no movement
                    return lambda pos: pos

            # Apply the animation by updating the position for each frame
            animated_clip = clip.set_position(slide_position)

            # Combine with a fade effect for smoother appearance
            animated_clip = apply_fade_animation(
                animated_clip, duration=slide_duration, direction="in")

            return animated_clip
        except Exception as e:
            print(f"Error applying slide animation: {e}")
            return clip

    def apply_glow_animation(clip, glow_duration=2.0, glow_intensity=1.2):
        """Apply a subtle pulsing glow effect to a text clip."""
        try:
            def glow_effect(t):
                # Create a subtle pulsing effect
                glow_factor = 1.0 + (glow_intensity - 1.0) * \
                    abs(math.sin(t * math.pi / glow_duration))
                return glow_factor

            # Apply the glow as an opacity/scale transformation
            return clip.fx(vfx.painting,
                           saturation=1.2,
                           black=0.001).transform(lambda get_frame, t: get_frame(t),
                                                  apply_to=['mask'])
        except Exception as e:
            print(f"Error applying glow animation: {e}")
            return clip

    def apply_bounce_animation(clip, bounce_height=20, bounce_duration=0.5):
        """Apply a bouncy animation to the text clip."""
        try:
            def bounce_transform(t):
                # First half second is bouncing in
                if t < bounce_duration:
                    y_offset = bounce_height * \
                        abs(math.sin(t * math.pi / bounce_duration))
                    return ('center', lambda pos: (pos[0], pos[1] - y_offset))
                # After that, stay in place
                else:
                    return ('center', lambda pos: (pos[0], pos[1]))

            animated_clip = clip.set_position(bounce_transform)
            return animated_clip
        except Exception as e:
            print(f"Error applying bounce animation: {e}")
            return clip

    def apply_typewriter_animation(clip, typewriter_speed=0.05, cursor_blink=True):
        """
        Apply an enhanced typewriter animation to text.

        Parameters:
        - clip: The TextClip to animate
        - typewriter_speed: Time per character typing
        - cursor_blink: Whether to show blinking cursor
        """
        try:
            # Get the text from the clip if possible
            text = ""
            if hasattr(clip, 'text'):
                text = clip.text
            else:
                # If we can't get the text, use a minimal effect
                return apply_fade_animation(clip, duration=1.0)

            # Calculate total typing duration based on text length
            typing_duration = len(text) * typewriter_speed

            # Create a series of clips showing progressively more text
            typed_clips = []

            for i in range(1, len(text) + 1):
                current_text = text[:i]
                if cursor_blink and i < len(text):
                    # Add blinking cursor while typing
                    current_text += "│"

                # Create a clip with current text state
                try:
                    char_clip = TextClip(
                        current_text,
                        fontsize=clip.fontsize if hasattr(
                            clip, 'fontsize') else 30,
                        color=clip.color if hasattr(
                            clip, 'color') else 'white',
                        font=clip.font if hasattr(clip, 'font') else 'Arial',
                        stroke_color=clip.stroke_color if hasattr(
                            clip, 'stroke_color') else 'black',
                        stroke_width=clip.stroke_width if hasattr(
                            clip, 'stroke_width') else 2,
                        method='caption',
                        align='center',
                        size=(None, None)
                    ).set_duration(typewriter_speed)

                    if hasattr(clip, 'pos'):
                        char_clip = char_clip.set_position(clip.pos)

                    typed_clips.append(char_clip)
                except Exception as e:
                    print(f"Error in typewriter animation frame {i}: {e}")
                    continue

            try:
                # Concatenate all the clips to create the typing effect
                typing_clip = concatenate_videoclips(
                    typed_clips, method="compose")

                # If the clip should be longer than the typing effect, add the final clip for remaining time
                if clip.duration > typing_duration:
                    final_clip = clip.set_start(typing_duration).set_duration(
                        clip.duration - typing_duration)
                    return CompositeVideoClip([typing_clip, final_clip])
                else:
                    return typing_clip
            except Exception as e:
                print(f"Error finalizing typewriter animation: {e}")
                # Fall back to original clip
                return clip
        except Exception as e:
            print(f"Error with typewriter animation: {e}")
            return clip

    # Create dramatic background effects for text
    def create_background_effect(clip, video_clip, effect_type="gradient_bar", opacity=0.7, padding=20):
        """
        Create a dramatic background effect for text overlays to make them pop on social media.

        Parameters:
        - clip: The text clip to create background for
        - video_clip: The main video clip (for dimensions)
        - effect_type: "gradient_bar", "blur_box", "solid_bar", "shadow_lift", or "corner_box"
        - opacity: Opacity of the background effect
        - padding: Padding around text in pixels
        """
        try:
            from moviepy.editor import ColorClip

            # Get dimensions
            video_w, video_h = video_clip.size
            if hasattr(clip, 'size'):
                text_w, text_h = clip.size
            else:
                # Fallback if we can't get text size
                text_w, text_h = video_w // 2, 50

            # Get position
            if hasattr(clip, 'pos'):
                pos_func = clip.pos
                # Try to get a static position
                try:
                    pos = pos_func(0)
                    if callable(pos):
                        pos = pos((video_w//2, video_h//2))
                except:
                    # Default center position if we can't determine
                    pos = (video_w//2, video_h//2)
            else:
                pos = (video_w//2, video_h//2)

            # Calculate x, y coords (approximate center of text)
            if isinstance(pos, tuple):
                x, y = pos
                if x == 'center':
                    x = video_w // 2
                if y == 'center':
                    y = video_h // 2
            else:
                x, y = video_w // 2, video_h // 2

            # Calculate background dimensions with padding
            bg_w = text_w + padding * 2
            bg_h = text_h + padding * 2

            # Ensure background stays within video
            bg_w = min(bg_w, video_w)

            # Calculate top-left position for background
            bg_x = max(0, x - bg_w // 2)
            bg_y = max(0, y - bg_h // 2)

            # Adjust if we'd go off the right or bottom edge
            if bg_x + bg_w > video_w:
                bg_x = video_w - bg_w
            if bg_y + bg_h > video_h:
                bg_y = video_h - bg_h

            # Create the background based on effect type
            if effect_type == "solid_bar":
                # Create a solid color bar
                bg_color = (0, 0, 0)  # Black
                bg_clip = ColorClip(size=(bg_w, bg_h), color=bg_color)
                bg_clip = bg_clip.set_opacity(opacity)
                bg_clip = bg_clip.set_position((bg_x, bg_y))

            elif effect_type == "gradient_bar":
                # Create a gradient effect (simulated with multiple color bars)
                gradient_clips = []
                # Dark in center, fading to transparent at edges
                center_opacity = opacity
                edge_opacity = opacity * 0.3

                center_color = (30, 30, 30)  # Dark gray center

                # Center bar
                center_clip = ColorClip(size=(bg_w, bg_h), color=center_color)
                center_clip = center_clip.set_opacity(center_opacity)
                center_clip = center_clip.set_position((bg_x, bg_y))
                gradient_clips.append(center_clip)

                # We'll return a CompositeVideoClip of the gradient effects
                bg_clip = CompositeVideoClip(
                    gradient_clips, size=video_clip.size)

            elif effect_type == "blur_box":
                # For a blur effect, we'd need to extract and blur part of the video
                # This is a simplified version that uses a semi-transparent dark box
                bg_color = (10, 10, 10)  # Very dark gray
                bg_clip = ColorClip(size=(bg_w, bg_h), color=bg_color)
                # Slightly more transparent
                bg_clip = bg_clip.set_opacity(opacity * 0.8)
                bg_clip = bg_clip.set_position((bg_x, bg_y))

            elif effect_type == "shadow_lift":
                # Create a shadow effect that lifts text slightly off the background
                shadow_color = (0, 0, 0)  # Black shadow
                shadow_clip = ColorClip(
                    size=(bg_w + 10, bg_h + 10), color=shadow_color)
                shadow_clip = shadow_clip.set_opacity(opacity * 0.7)
                # Offset the shadow slightly
                shadow_clip = shadow_clip.set_position((bg_x - 5, bg_y - 5))

                # Main background (more transparent)
                bg_color = (20, 20, 20)
                bg_main = ColorClip(size=(bg_w, bg_h), color=bg_color)
                bg_main = bg_main.set_opacity(opacity * 0.6)
                bg_main = bg_main.set_position((bg_x, bg_y))

                # Combine shadow and background
                bg_clip = CompositeVideoClip(
                    [shadow_clip, bg_main], size=video_clip.size)

            elif effect_type == "corner_box":
                # A box effect that looks like it's coming from a corner of the screen
                # Determine which corner based on position
                corner_w = bg_w + video_w // 8
                corner_h = bg_h

                # Select corner based on position
                if x < video_w // 2 and y < video_h // 2:
                    # Top left
                    corner_x = 0
                    corner_y = 0
                elif x >= video_w // 2 and y < video_h // 2:
                    # Top right
                    corner_x = video_w - corner_w
                    corner_y = 0
                elif x < video_w // 2 and y >= video_h // 2:
                    # Bottom left
                    corner_x = 0
                    corner_y = video_h - corner_h
                else:
                    # Bottom right
                    corner_x = video_w - corner_w
                    corner_y = video_h - corner_h

                bg_color = (10, 10, 10)
                bg_clip = ColorClip(size=(corner_w, corner_h), color=bg_color)
                bg_clip = bg_clip.set_opacity(opacity)
                bg_clip = bg_clip.set_position((corner_x, corner_y))

            else:
                # Default to a simple dark bar if no valid effect type
                bg_color = (0, 0, 0)
                bg_clip = ColorClip(size=(bg_w, bg_h), color=bg_color)
                bg_clip = bg_clip.set_opacity(opacity)
                bg_clip = bg_clip.set_position((bg_x, bg_y))

            # Set the same duration as the text clip
            bg_clip = bg_clip.set_duration(clip.duration)

            # Make the start time same as text
            if hasattr(clip, 'start'):
                bg_clip = bg_clip.set_start(clip.start)

            return bg_clip
        except Exception as e:
            print(f"Error creating background effect: {e}")
            return None

    # Social media color grading effects
    def apply_color_grading(clip, style="fitness"):
        """
        Apply professional color grading effects that mimic popular social media styles.

        Parameters:
        - clip: The video clip to apply color grading to
        - style: The color grading style to apply:
            * "fitness" - High contrast, slightly warm tones ideal for workout videos
            * "cinematic" - Movie-like color grading with deeper shadows
            * "vibrant" - Bright, vibrant colors popular on social feeds
            * "moody" - Dark, atmospheric look with blue shadows
            * "vintage" - Retro film look with warm highlights
            * "instagram" - Classic Instagram filter look
        """
        try:
            # Apply color grading based on selected style
            if style == "fitness":
                # Fitness videos typically have enhanced contrast and slightly warm tones
                # to make muscles and definition pop
                return clip.fx(vfx.colorx, 1.1).fx(vfx.lum_contrast, contrast=0.15)

            elif style == "cinematic":
                # Movie-like grading with richer colors and deeper shadows
                return clip.fx(vfx.colorx, 1.05).fx(vfx.lum_contrast, contrast=0.2)

            elif style == "vibrant":
                # Vibrant social media style with saturated colors
                return clip.fx(vfx.colorx, 1.2).fx(vfx.lum_contrast, contrast=0.1)

            elif style == "moody":
                # Dark, atmospheric look with blue tint in shadows
                # This simulates the popular moody Instagram aesthetic
                dark_clip = clip.fx(vfx.colorx, 0.95).fx(
                    vfx.lum_contrast, contrast=0.15)
                # We'd ideally add a subtle blue tint to shadows here
                return dark_clip

            elif style == "vintage":
                # Retro film look with warm highlights and faded shadows
                vintage_clip = clip.fx(vfx.colorx, 1.0)
                # Ideally would add a slight yellow/orange tint to highlights
                return vintage_clip

            elif style == "instagram":
                # Classic Instagram filter look (simulating the early popular filters)
                insta_clip = clip.fx(vfx.colorx, 1.1).fx(
                    vfx.lum_contrast, contrast=0.1)
                # Would ideally add the classic subtle vignette here
                return insta_clip

            else:
                # Default - return clip unmodified
                return clip

        except Exception as e:
            print(f"Error applying color grading: {e}")
            traceback.print_exc()
            # Return original clip if color grading fails
            return clip

    # Define the main video processing function
    def safe_process_video(video_path, text_style="bold_statement", hook_position="center_focus",
                           tip_position="bottom_banner", background_effect="gradient_bar", color_grade="fitness"):
        """
        A safe version of process_video that handles errors gracefully and adds complex animated text overlays.

        Parameters:
        - video_path: Path to the video file
        - text_style: Style for text appearance ("bold_statement", "instagram_classic", etc.)
        - hook_position: Position for the hook text
        - tip_position: Position for the tip text
        - background_effect: Type of background effect for text ("gradient_bar", "blur_box", etc.)
        - color_grade: Color grading style to apply to the entire video
        """
        try:
            # Print version info for debugging
            try:
                import moviepy
                print(f"Using MoviePy version: {moviepy.__version__}")
            except:
                print("Could not determine MoviePy version")

            # Get filename parts
            base_name = os.path.basename(video_path)
            name, ext = os.path.splitext(base_name)

            # Get clean exercise name from filename
            exercise_name = name.replace("_", " ").strip().title()
            print(f"Cleaned exercise name from filename: {exercise_name}")

            # Load the video clip
            video_clip = VideoFileClip(video_path)

            # Set animation style from the provided style
            animation_style = text_style

            # Get video dimensions and duration
            width, height = video_clip.size
            video_duration = video_clip.duration

            # Set up timing for text elements (in seconds)
            title_delay = 0.5  # When title appears
            hook_delay = 1.5   # When hook appears
            tip_delay = 2.5    # When tip appears

            # Set text sizes based on video height
            title_size = max(20, int(height * 0.045))  # Title text size
            hook_size = max(18, int(height * 0.035))   # Hook text size
            tip_size = max(16, int(height * 0.03))     # Tip text size

            # Create a list to store all clips (video + text overlays)
            clips_with_text = [video_clip]  # Start with the base video

            # Get exercise information from filename or database
            hook_content = "Keep proper form throughout the movement"
            tip_content = "Control the movement and maintain tension"

            # Create title text with animation
            try:
                title_text = create_text_clip(
                    f"Exercise: {exercise_name}",
                    position=('center', 20),
                    size=title_size,
                    fontcolor='white',
                    fontfamily='Arial-Bold',
                    text_style=animation_style
                )

                if title_text:
                    # Position and set duration
                    title_text = title_text.set_start(title_delay)
                    title_text = title_text.set_duration(
                        video_duration - title_delay)

                    # Apply animation based on style
                    if animation_style == "fade":
                        title_text = apply_fade_animation(
                            title_text, duration=1.5, direction="in")
                    elif animation_style == "slide_in":
                        title_text = apply_slide_animation(
                            title_text, slide_duration=1.2, direction="left")
                    elif animation_style == "typewriter":
                        title_text = apply_typewriter_animation(
                            title_text, typewriter_speed=0.05)
                    elif animation_style == "bounce":
                        title_text = apply_bounce_animation(
                            title_text, bounce_height=20, bounce_duration=0.8)
                    elif animation_style == "glow":
                        title_text = apply_glow_animation(
                            title_text, glow_duration=2.0, glow_intensity=1.3)

                    # Create background effect if specified
                    if background_effect and background_effect != "none":
                        title_bg = create_background_effect(
                            title_text, video_clip,
                            effect_type=background_effect,
                            opacity=0.7,
                            padding=15
                        )
                        if title_bg:
                            clips_with_text.append(title_bg)

                    # Add the title text to clips
                    clips_with_text.append(title_text)
            except Exception as e:
                print(f"Error creating title text: {e}")
                traceback.print_exc()

            # Create hook text if content is available
            if hook_content and len(str(hook_content).strip()) > 0:
                try:
                    hook_text = create_text_clip(
                        f"FORM TIP: {hook_content}",
                        position=('center', int(height * 0.5)),
                        size=hook_size,
                        fontcolor='white',
                        fontfamily='Arial',
                        text_style=animation_style
                    )

                    if hook_text:
                        # Position and set duration
                        hook_text = hook_text.set_start(hook_delay)
                        hook_text = hook_text.set_duration(
                            video_duration - hook_delay)

                        # Apply animation based on style
                        if animation_style == "fade":
                            hook_text = apply_fade_animation(
                                hook_text, duration=1.5, direction="in")
                        elif animation_style == "slide_in":
                            hook_text = apply_slide_animation(
                                hook_text, slide_duration=1.2, direction="right")
                        elif animation_style == "typewriter":
                            hook_text = apply_typewriter_animation(
                                hook_text, typewriter_speed=0.05)
                        elif animation_style == "bounce":
                            hook_text = apply_bounce_animation(
                                hook_text, bounce_height=15, bounce_duration=0.8)
                        elif animation_style == "glow":
                            hook_text = apply_glow_animation(
                                hook_text, glow_duration=2.0, glow_intensity=1.3)

                        # Create background effect if specified
                        if background_effect and background_effect != "none":
                            hook_bg = create_background_effect(
                                hook_text, video_clip,
                                effect_type=background_effect,
                                opacity=0.7,
                                padding=15
                            )
                            if hook_bg:
                                clips_with_text.append(hook_bg)

                        # Add the hook text to clips
                        clips_with_text.append(hook_text)
                except Exception as e:
                    print(f"Error creating hook text: {e}")
                    traceback.print_exc()

            # Create tip text if content is available
            if tip_content and len(str(tip_content).strip()) > 0:
                try:
                    tip_text = create_text_clip(
                        f"TECHNIQUE: {tip_content}",
                        position=('center', height - int(height * 0.12)),
                        size=tip_size,
                        fontcolor='white',
                        fontfamily='Arial',
                        text_style=animation_style
                    )

                    if tip_text:
                        # Position and set duration
                        tip_text = tip_text.set_start(tip_delay)
                        tip_text = tip_text.set_duration(
                            video_duration - tip_delay)

                        # Apply animation based on style
                        if animation_style == "fade":
                            tip_text = apply_fade_animation(
                                tip_text, duration=1.5, direction="in")
                        elif animation_style == "slide_in":
                            tip_text = apply_slide_animation(
                                tip_text, slide_duration=1.2, direction="up")
                        elif animation_style == "typewriter":
                            tip_text = apply_typewriter_animation(
                                tip_text, typewriter_speed=0.05)
                        elif animation_style == "bounce":
                            tip_text = apply_bounce_animation(
                                tip_text, bounce_height=15, bounce_duration=0.8)
                        elif animation_style == "glow":
                            tip_text = apply_glow_animation(
                                tip_text, glow_duration=2.0, glow_intensity=1.3)

                        # Create background effect if specified
                        if background_effect and background_effect != "none":
                            tip_bg = create_background_effect(
                                tip_text, video_clip,
                                effect_type=background_effect,
                                opacity=0.7,
                                padding=15
                            )
                            if tip_bg:
                                clips_with_text.append(tip_bg)

                        # Add the tip text to clips
                        clips_with_text.append(tip_text)
                except Exception as e:
                    print(f"Error creating tip text: {e}")
                    traceback.print_exc()

            # Apply color grading to the video if specified
            if color_grade and color_grade != "none":
                video_clip = apply_color_grading(video_clip, style=color_grade)
                # Update the first clip in our list which is the base video
                clips_with_text[0] = video_clip

            # Create final video with all overlays
            try:
                # Create the composite video
                final_clip = CompositeVideoClip(clips_with_text)

                # Set output path - append _enhanced to filename
                output_path = os.path.splitext(
                    video_path)[0] + "_enhanced" + os.path.splitext(video_path)[1]

                # Write the video file
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    fps=video_clip.fps
                )

                print(f"Enhanced video saved to: {output_path}")
                return output_path

            except Exception as export_error:
                print(f"Error exporting enhanced video: {export_error}")
                traceback.print_exc()
                return None

        except Exception as e:
            print(f"Error in safe_process_video: {e}")
            traceback.print_exc()
            return None

    # Return the safe_process_video function
    return safe_process_video


# Create the main enhancement function
safe_process_video = apply_text_overlay_patch()

# Simple function to enhance a video with social media styling


def enhance_video(video_path, text_style="bold_statement", background_effect="gradient_bar", color_grade="fitness"):
    """Enhance a video with social media optimized text and effects."""
    if safe_process_video:
        return safe_process_video(
            video_path,
            text_style=text_style,
            background_effect=background_effect,
            color_grade=color_grade
        )
    else:
        print("Error: Text overlay patch could not be applied.")
        return None
