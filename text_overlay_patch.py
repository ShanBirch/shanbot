"""
Enhanced Text Overlay Patch for Fitness Videos
Adds social media-optimized text animations, styles, and color grading effects
"""

try:
    import os
    import sys
    import traceback
    import math
    import time
    import numpy as np
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx

    # Global flag to track if we've already patched
    _PATCH_APPLIED = False

    def apply_text_overlay_patch():
        """Apply the enhanced text overlay patch to simple_blue_video.py."""
        try:
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
                        # Add a shadow instead
                        shadow_color = "#000000"

                    elif text_style == "typewriter":
                        # Typewriter style with monospace font
                        fontfamily = "Courier"
                        fontcolor = "#FFFFCC"  # Slight yellow tint for vintage feel

                    elif text_style == "bouncy_text":
                        # Fun, playful style
                        fontfamily = "Comic-Sans-MS-Bold" if "Comic-Sans-MS-Bold" else "Arial-Bold"
                        fontcolor = "#FF9500"  # Vibrant orange

                    elif text_style == "glowing":
                        # Glowing text effect
                        fontfamily = "Arial-Bold"
                        fontcolor = "#FFFFFF"  # Bright white
                        stroke_color = "#00CCFF"  # Cyan glow
                        stroke_width = 3

                    elif text_style == "zoom_in":
                        # Clean, dramatic style
                        fontfamily = "Arial-Black" if "Arial-Black" else "Arial-Bold"
                        stroke_width = 2

                    # Create the basic text clip
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
                    # Return a minimal text clip as fallback
                    try:
                        from moviepy.editor import TextClip
                        return TextClip(text, fontsize=size, color=fontcolor).set_position(position)
                    except:
                        # If all else fails, return None and handle upstream
                        print("Failed to create fallback text clip")
                        return None

            # Additional animation functions
            def apply_fade_animation(clip, duration=1.0, direction="in", offset=0):
                """
                Apply enhanced fade animation with different direction options.

                Parameters:
                - clip: The TextClip to animate
                - duration: Duration of the fade effect
                - direction: "in", "out", or "both"
                - offset: Time offset for when to start the effect
                """
                clip_duration = clip.duration

                if direction == "in" or direction == "both":
                    clip = clip.fx(vfx.fadeIn, duration)

                if direction == "out" or direction == "both":
This patch file fixes the "unsupported operand type(s) for *: 'function' and 'float'" error
that occurs during text overlay generation and adds advanced animations for more visually appealing videos.
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
already_patched = False

try:
    # Only apply the patch once
    if not already_patched:
        already_patched = True

        # Safely import required modules
        text_overlay_generator = None
        exercise_db = None

        try:
            import text_overlay_generator
            print("Successfully imported text_overlay_generator")
        except ImportError as ie:
            print(f"Warning: Could not import text_overlay_generator: {ie}")
            # Exit gracefully without crashing
            sys.exit(0)

        try:
            from exercise_database import exercise_db
            print("Successfully imported exercise_db")
        except ImportError as ie:
            print(f"Warning: Could not import exercise_database: {ie}")
            # Continue without exercise database
            pass

        # Check if text_overlay exists
        if not hasattr(text_overlay_generator, 'text_overlay'):
            print("Warning: text_overlay not found in text_overlay_generator module")
            sys.exit(0)

        # Get the text_overlay object
        text_overlay = text_overlay_generator.text_overlay

        # Store original process_video function
        if hasattr(text_overlay, 'process_video'):
            original_process_video = text_overlay.process_video
        else:
            print("Warning: process_video not found in text_overlay")
            sys.exit(0)

        # Main patch function implementation
        def apply_text_overlay_patch():
            """Apply the enhanced text overlay patch to simple_blue_video.py."""
            try:
                # Helper function for creating text clips
                def create_text_clip(text, position, size=30, fontcolor="white", fontfamily="Arial", text_style="minimal"):
                    """Create a TextClip with specified parameters and enhanced styling for social media."""
                    try:
                        from moviepy.editor import TextClip, CompositeVideoClip, ColorClip

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
                            # Add a shadow instead
                            shadow_color = "#000000"

                        elif text_style == "typewriter":
                            # Typewriter style with monospace font
                            fontfamily = "Courier"
                            fontcolor = "#FFFFCC"  # Slight yellow tint for vintage feel

                        elif text_style == "bouncy_text":
                            # Fun, playful style
                            fontfamily = "Comic-Sans-MS-Bold" if "Comic-Sans-MS-Bold" else "Arial-Bold"
                            fontcolor = "#FF9500"  # Vibrant orange

                        elif text_style == "glowing":
                            # Glowing text effect
                            fontfamily = "Arial-Bold"
                            fontcolor = "#FFFFFF"  # Bright white
                            stroke_color = "#00CCFF"  # Cyan glow
                            stroke_width = 3

                        elif text_style == "zoom_in":
                            # Clean, dramatic style
                            fontfamily = "Arial-Black" if "Arial-Black" else "Arial-Bold"
                            stroke_width = 2

                        # Create the basic text clip
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
                        # Return a minimal text clip as fallback
                        try:
                            from moviepy.editor import TextClip
                            return TextClip(text, fontsize=size, color=fontcolor).set_position(position)
                        except:
                            # If all else fails, return None and handle upstream
                            print("Failed to create fallback text clip")
                            return None

                # Additional animation functions
                def apply_fade_animation(clip, duration=1.0, direction="in", offset=0):
                    """
                    Apply enhanced fade animation with different direction options.

                    Parameters:
                    - clip: The TextClip to animate
                    - duration: Duration of the fade effect
                    - direction: "in", "out", or "both"
                    - offset: Time offset for when to start the effect
                    """
                    clip_duration = clip.duration

                    if direction == "in" or direction == "both":
                        clip = clip.fx(vfx.fadeIn, duration)

                    if direction == "out" or direction == "both":
                        # For fade out, apply it at the end of the clip
                        fade_out_start = max(
                            0, clip_duration - duration - offset)
                        clip = clip.fx(vfx.fadeOut, duration).set_start(
                            fade_out_start)

                    return clip

                def apply_slide_animation(clip, slide_duration=1.0, direction="left", slide_distance=None):
                    """
                    Apply enhanced slide animation with various direction options.

                    Parameters:
                    - clip: The TextClip to animate
                    - slide_duration: Duration of the slide effect
                    - direction: "left", "right", "up", "down"
                    - slide_distance: How far to slide(if None, uses screen width/height)
                    """
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

                def apply_typewriter_animation(clip, typewriter_speed=0.05, cursor_blink=True):
                    """
                    Apply an enhanced typewriter animation to text.

                    Parameters:
                    - clip: The TextClip to animate
                    - typewriter_speed: Time per character typing
                    - cursor_blink: Whether to show blinking cursor
                    """
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
                                font=clip.font if hasattr(
                                    clip, 'font') else 'Arial',
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
                            print(
                                f"Error in typewriter animation frame {i}: {e}")
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

                def apply_glow_animation(clip, glow_duration=2.0, glow_intensity=1.2):
                    """Apply a subtle pulsing glow effect to a text clip."""
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

                def apply_bounce_animation(clip, bounce_height=20, bounce_duration=0.5):
                    """Apply a bouncy animation to the text clip."""
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

                def apply_zoom_animation(txt_clip, zoom_duration=0.8, zoom_factor=1.5):
                    """Apply a zoom-in animation to a text clip."""
                    try:
                        w, h = txt_clip.size

                        def zoom_transform(get_frame, t):
                            frame = get_frame(t)
                            if t < zoom_duration:
                                # Calculate zoom scale
                                scale = 1.0 + (zoom_factor - 1.0) * \
                                    (1.0 - (zoom_duration - t) / zoom_duration)
                                # For zooming in effect, we start small and get bigger
                                zoom_scale = max(0.1, min(scale, zoom_factor))

                                # Apply zoom
                                import cv2
                                h, w = frame.shape[:2]
                                # Create new dimensions
                                new_h, new_w = int(
                                    h * zoom_scale), int(w * zoom_scale)
                                # Resize frame
                                zoomed = cv2.resize(
                                    frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                                # Center crop to original size
                                y_start = max(0, (new_h - h) // 2)
                                x_start = max(0, (new_w - w) // 2)

                                # Ensure we have enough area to crop
                                if new_h >= h and new_w >= w:
                                    result = zoomed[y_start:y_start +
                                                    h, x_start:x_start+w]
                                    return result

                            # Return original frame if we can't process
                            return frame

                        try:
                            # Try to apply transformation
                            return txt_clip.fl(zoom_transform)
                        except:
                            # Fallback method if fl method fails
                            def zoom_pos(t):
                                if t < zoom_duration:
                                    # Start from smaller size and grow
                                    scale = 1.0 + (zoom_factor - 1.0) * \
                                        (1.0 - (zoom_duration - t) / zoom_duration)
                                    # Larger than original
                                    size = (w * scale, h * scale)
                                    return ('center', 'center')
                                else:
                                    return txt_clip.pos(t)

                            return txt_clip.set_position(zoom_pos)
                    except Exception as e:
                        print(f"Error applying zoom animation: {e}")
                        traceback.print_exc()  # Print stack trace for debugging
                        return txt_clip  # Return the original clip if animation fails

                def apply_slide_up_animation(txt_clip, slide_duration=0.8):
                    """Apply a slide-up animation where text comes from bottom of the screen."""
                    try:
                        # Get screen dimensions estimate
                        w, h = txt_clip.size
                        screen_h = h * 3  # Estimate screen height

                        def slide_up_pos(t):
                            if t < slide_duration:
                                progress = min(1.0, t / slide_duration)
                                # Start below screen and move up
                                y_pos = screen_h - progress * screen_h
                                return (txt_clip.pos(t)[0], y_pos)
                            else:
                                return txt_clip.pos(t)

                        return txt_clip.set_position(slide_up_pos)
                    except Exception as e:
                        print(f"Error applying slide-up animation: {e}")
                        traceback.print_exc()
                        return txt_clip

                def apply_instagram_story_animation(txt_clip, duration=1.0):
                    """Apply an Instagram-story style animation with slide and scale."""
                    try:
                        w, h = txt_clip.size
                        screen_w, screen_h = w * 3, h * 3  # Estimate screen size

                        def insta_story_pos(t):
                            if t < duration:
                                progress = min(1.0, t / duration)

                                # Slide from right with slight bounce
                                # Slightly faster for bounce effect
                                x_progress = min(1.0, progress * 1.2)
                                if x_progress > 1.0:
                                    # Create small bounce back effect
                                    x_bounce = (x_progress - 1.0) * 0.2
                                    x_pos = screen_w * 0.5 - (x_bounce * w)
                                else:
                                    x_pos = screen_w - \
                                        (screen_w * 0.5) * x_progress

                                # Slight vertical movement
                                y_pos = txt_clip.pos(
                                    t)[1] + math.sin(progress * math.pi) * 10

                                return (x_pos, y_pos)
                            else:
                                return txt_clip.pos(t)

                        # Instagram stories often have a slight scale-up effect
                        def insta_scale(t):
                            if t < duration:
                                progress = min(1.0, t / duration)
                                # Start slightly smaller and scale up
                                scale = 0.8 + 0.2 * progress
                                return ('center', 'center', scale)
                            else:
                                return txt_clip.pos(t)

                        # Apply position animation
                        return txt_clip.set_position(insta_story_pos)
                    except Exception as e:
                        print(f"Error applying Instagram story animation: {e}")
                        traceback.print_exc()
                        return txt_clip

                # Create dramatic background effects for text
                def create_background_effect(clip, video_clip, effect_type="gradient_bar", opacity=0.7, padding=20):
                    """
                    Create a dramatic background effect for text overlays to make them pop on social media.

                    Parameters:
                    - clip: The text clip to create background for
                    - video_clip: The main video clip(for dimensions)
                    - effect_type: "gradient_bar", "blur_box", "solid_bar", "shadow_lift", or "corner_box"
                    - opacity: Opacity of the background effect
                    - padding: Padding around text in pixels
                    """
                    from moviepy.editor import ColorClip, CompositeVideoClip

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
                        center_clip = ColorClip(
                            size=(bg_w, bg_h), color=center_color)
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
                        shadow_clip = shadow_clip.set_position(
                            (bg_x - 5, bg_y - 5))

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
                        bg_clip = ColorClip(
                            size=(corner_w, corner_h), color=bg_color)
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
                    from moviepy.editor import vfx

                    try:
                        # Apply color grading based on selected style
                        if style == "fitness":
                            # Fitness videos typically have enhanced contrast and slightly warm tones
                            # to make muscles and definition pop
                            return clip.fx(vfx.colorx, 1.1).fx(vfx.lum_contrast, bright=0.05, contrast=0.15, contrast_thr=0.5)

                        elif style == "cinematic":
                            # Movie-like grading with richer colors and deeper shadows
                            return clip.fx(vfx.colorx, 1.05).fx(vfx.lum_contrast, bright=-0.05, contrast=0.2)

                        elif style == "vibrant":
                            # Vibrant social media style with saturated colors
                            return clip.fx(vfx.colorx, 1.2).fx(vfx.lum_contrast, bright=0.1, contrast=0.1)

                        elif style == "moody":
                            # Dark, atmospheric look with blue tint in shadows
                            # This simulates the popular moody Instagram aesthetic
                            dark_clip = clip.fx(vfx.colorx, 0.95).fx(
                                vfx.lum_contrast, bright=-0.1, contrast=0.15)
                            # We'd ideally add a subtle blue tint to shadows here
                            return dark_clip

                        elif style == "vintage":
                            # Retro film look with warm highlights and faded shadows
                            vintage_clip = clip.fx(vfx.colorx, 1.0).fx(
                                vfx.lum_contrast, bright=0.05, contrast=-0.05)
                            # Ideally would add a slight yellow/orange tint to highlights
                            return vintage_clip

                        elif style == "instagram":
                            # Classic Instagram filter look (simulating the early popular filters)
                            insta_clip = clip.fx(vfx.colorx, 1.1).fx(
                                vfx.lum_contrast, bright=0.05, contrast=0.1)
                            # Would ideally add the classic subtle vignette here
                            return insta_clip

                        else:
                            # Default - return clip unmodified
                            return clip

                    except Exception as e:
                        print(f"Error applying color grading: {e}")
                        # Return original clip if color grading fails
                        return clip

                # Define the main video processing function
                def safe_process_video(video_path, text_style="bold_statement", hook_position="center_focus",
                                       tip_position="bottom_banner", background_effect="gradient_bar", color_grade="fitness"):
                    """
                    A safe version of process_video that handles errors gracefully and adds complex animated text overlays.

                    Parameters:
                    - video_path: Path to the video file
                    - text_style: Style for text appearance("bold_statement", "instagram_classic", etc.)
                    - hook_position: Position for the hook text
                    - tip_position: Position for the tip text
                    - background_effect: Type of background effect for text("gradient_bar", "blur_box", etc.)
                    - color_grade: Color grading style to apply to the entire video
                    """
                    try:
                        # Basic video processing with minimal dependencies
                        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
                        import moviepy.config as mp_config

                        # Try to get MoviePy version for debugging
                        try:
                            import moviepy
                            print(
                                f"Using MoviePy version: {moviepy.__version__}")
                        except:
                            print("Could not determine MoviePy version")

                        print(f"Processing video: {video_path}")
                        print(f"Moviepy config: {mp_config.FFMPEG_BINARY}")
                        # Print the text style received from the GUI
                        print(f"Received text_style parameter: '{text_style}'")

                        # Create the output path
                        output_dir = os.path.join(
                            os.path.dirname(video_path), "processed")
                        os.makedirs(output_dir, exist_ok=True)

                        base_name = os.path.basename(video_path)
                        name, ext = os.path.splitext(base_name)
                        output_path = os.path.join(
                            output_dir, f"{name}_processed{ext}")

                        # Get clean exercise name from filename
                        exercise_name = name.replace("_", " ").strip().title()
                        print(
                            f"Cleaned exercise name from filename: {exercise_name}")

                        # Try to find exercise info if database is available
                        exercise_info = None
                        best_match = None
                        best_match_score = 0

                        if exercise_db and hasattr(exercise_db, 'exercises'):
                            print(
                                f"Found exercise database with {len(exercise_db.exercises)} exercises")

                            # First, try exact match
                            for exercise in exercise_db.exercises:
                                if hasattr(exercise, 'name'):
                                    db_name = exercise.name.lower()
                                    file_name = exercise_name.lower()

                                    # Exact match
                                    if db_name == file_name:
                                        exercise_info = exercise
                                        exercise_name = exercise.name
                                        print(
                                            f"Found exact match for exercise: {exercise_name}")
                                        break

                                    # Check if file name is in database name or database name is in file name
                                    # Calculate a simple match score
                                    if db_name in file_name or file_name in db_name:
                                        # Calculate match score based on length of common substring
                                        score = len(
                                            db_name if db_name in file_name else file_name)
                                        if score > best_match_score:
                                            best_match = exercise
                                            best_match_score = score

                            # If no exact match but we have a partial match
                            if not exercise_info and best_match:
                                exercise_info = best_match
                                exercise_name = best_match.name
                                print(
                                    f"Found partial match for exercise: {exercise_name}")

                            # Debug: print exercise info if found
                            if exercise_info:
                                print(f"Exercise info found:")
                                if hasattr(exercise_info, 'hook'):
                                    print(f"  Hook: {exercise_info.hook}")
                                else:
                                    print("  No hook available")

                                if hasattr(exercise_info, 'technique_tips'):
                                    tips = exercise_info.technique_tips
                                    if isinstance(tips, list):
                                        print(
                                            f"  Technique tips: {tips[0] if tips else 'None'}")
                                    else:
                                        print(f"  Technique tips: {tips}")
                                else:
                                    print("  No technique tips available")
                            else:
                                print("No matching exercise found in database")

                        # Load the video clip
                        video_clip = VideoFileClip(video_path)

                        # Instagram-optimized sizes
                        width, height = video_clip.size
                        print(f"Original video dimensions: {width}x{height}")

                        # Calculate aspect ratio to determine the best Instagram format
                        aspect_ratio = width / height
                        print(f"Video aspect ratio: {aspect_ratio:.2f}")

                        # Determine if we need to resize for Instagram
                        # Instagram prefers 1:1 (square), 4:5 (portrait), or 16:9 (landscape)
                        insta_resize = False
                        new_width, new_height = width, height

                        if aspect_ratio < 0.8:  # Very tall video - resize to 4:5
                            insta_resize = True
                            new_height = height
                            new_width = int(new_height * 0.8)  # 4:5 ratio
                            print(
                                f"Resizing for Instagram portrait (4:5): {new_width}x{new_height}")
                        elif aspect_ratio > 2.0:  # Very wide video - resize to 16:9
                            insta_resize = True
                            new_width = width
                            new_height = int(new_width / 1.778)  # 16:9 ratio
                            print(
                                f"Resizing for Instagram landscape (16:9): {new_width}x{new_height}")

                        # Resize if needed
                        if insta_resize:
                            print("Resizing video for Instagram...")
                            # Create a black background of the target size
                            bg = ColorClip(size=(new_width, new_height),
                                           color=(0, 0, 0))
                            bg = bg.set_duration(video_clip.duration)

                            # Resize the video maintaining aspect ratio
                            if aspect_ratio < 0.8:  # Portrait
                                resized_clip = video_clip.resize(
                                    width=new_width)
                            else:  # Landscape
                                resized_clip = video_clip.resize(
                                    height=new_height)

                            # Center the video on the background
                            resized_clip = resized_clip.set_position("center")

                            # Composite the video on the background
                            video_clip = CompositeVideoClip([bg, resized_clip])
                            width, height = new_width, new_height

                        print(
                            f"Final video dimensions for processing: {width}x{height}")

                        # Create the basic clips list
                        clips = [video_clip]

                        # Video duration
                        video_duration = video_clip.duration
                        print(f"Video duration: {video_duration:.2f} seconds")

                        # Define larger font sizes for better visibility on Instagram
                        title_size = int(height * 0.08)  # Increase from 0.06
                        hook_size = int(height * 0.07)   # Increase from 0.05
                        tip_size = int(height * 0.06)    # Increase from 0.04

                        # Ensure the animation style is treated case-insensitively and defaulted properly
                        if text_style:
                            animation_style = text_style.lower().strip()
                        else:
                            animation_style = "minimal"  # Default if no style provided

                        # Validate that animation_style is one of the supported styles
                        if animation_style not in ["bold_statement", "fitness_pro", "instagram_classic", "minimal",
                                                   "instagram_story", "typewriter", "bouncy_text", "slide_up",
                                                   "glowing", "zoom_in"]:
                            print(
                                f"WARNING: Unsupported style '{animation_style}', defaulting to 'minimal'")
                            animation_style = "minimal"

                        # Default timing for text appearance
                        title_delay = 0.0  # Title appears immediately
                        hook_delay = 1.0   # Hook text appears after 1 second
                        tip_delay = 2.0    # Technique tip appears after 2 seconds

                        # Advanced animation configuration by style
                        if animation_style == "bold_statement":
                            # Bold statement style - dramatic entrances
                            title_animation = "slide_right"
                            hook_animation = "typewriter"
                            tip_animation = "slide_bottom"

                            title_delay = 0.2
                            hook_delay = 1.5
                            tip_delay = 3.0

                        elif animation_style == "fitness_pro":
                            # Fitness pro style - clean, quick animations
                            title_animation = "fade"
                            hook_animation = "bounce"
                            tip_animation = "slide_left"

                            title_delay = 0.2
                            hook_delay = 0.7
                            tip_delay = 1.5

                        elif animation_style == "instagram_classic":
                            # Instagram classic - trendy animations
                            title_animation = "typewriter"
                            hook_animation = "fade"
                            tip_animation = "glow"

                            title_delay = 0.5
                            hook_delay = 1.5
                            tip_delay = 2.5

                        elif animation_style == "instagram_story":
                            # Instagram story - modern, full-screen animations
                            title_animation = "instagram_story"
                            hook_animation = "slide_right"
                            tip_animation = "slide_up"

                            title_delay = 0.2
                            hook_delay = 1.2
                            tip_delay = 2.0

                        elif animation_style == "typewriter":
                            # All typewriter style
                            title_animation = "typewriter"
                            hook_animation = "typewriter"
                            tip_animation = "typewriter"

                            title_delay = 0.5
                            hook_delay = 2.0
                            tip_delay = 3.5

                        elif animation_style == "bouncy_text":
                            # Bouncy animations
                            title_animation = "bounce"
                            hook_animation = "bounce"
                            tip_animation = "bounce"

                            title_delay = 0.3
                            hook_delay = 1.2
                            tip_delay = 2.1

                        elif animation_style == "slide_up":
                            # Bottom-to-top slide animations
                            title_animation = "slide_up"
                            hook_animation = "slide_up"
                            tip_animation = "slide_up"

                            title_delay = 0.3
                            hook_delay = 1.0
                            tip_delay = 1.7

                        elif animation_style == "glowing":
                            # Glowing text animations
                            title_animation = "glow"
                            hook_animation = "glow"
                            tip_animation = "glow"

                            title_delay = 0.2
                            hook_delay = 1.0
                            tip_delay = 1.8

                        elif animation_style == "zoom_in":
                            # Zoom animations
                            title_animation = "zoom"
                            hook_animation = "zoom"
                            tip_animation = "zoom"

                            title_delay = 0.3
                            hook_delay = 1.2
                            tip_delay = 2.1

                        else:  # "minimal" or any other style
                            # Minimal style - subtle animations
                            title_animation = "fade"
                            hook_animation = "fade"
                            tip_animation = "fade"

                            title_delay = 0.0
                            hook_delay = 1.0
                            tip_delay = 2.0

                        print(f"Using animation style: {animation_style}")
                        print(
                            f"Selected animations - Title: {title_animation}, Hook: {hook_animation}, Tip: {tip_animation}")

                        # Add text overlays with COMPLEX ANIMATIONS
                        try:
                            # Create title text with animation
                            try:
                                title_text = create_text_clip(
                                    f"Exercise: {exercise_name}",
                                    position=('center', 20),
                                    size=title_size,
                                    fontcolor='white',
                                    fontfamily='Arial-Bold',
                                    text_style=animation_style  # Pass the style to the function
                                )

                                # Position and set duration
                                title_text = title_text.set_start(title_delay)
                                title_text = title_text.set_duration(
                                    video_duration - title_delay)

                                # Apply animation based on style
                                if title_animation == "fade":
                                    title_text = apply_fade_animation(
                                        title_text, duration=1.5, direction="in")
                                elif title_animation == "slide_right":
                                    title_text = apply_slide_animation(
                                        title_text, slide_duration=1.2, direction="right")
                                elif title_animation == "typewriter":
                                    title_text = apply_typewriter_animation(
                                        title_text, typewriter_speed=0.05)
                                elif title_animation == "bounce":
                                    title_text = apply_bounce_animation(
                                        title_text, bounce_height=20, bounce_duration=0.8)
                                elif title_animation == "slide_up":
                                    title_text = apply_slide_up_animation(
                                        title_text, 1.0)
                                elif title_animation == "glow":
                                    title_text = apply_glow_animation(
                                        title_text, glow_duration=2.0, glow_intensity=1.3)
                                elif title_animation == "zoom":
                                    title_text = apply_zoom_animation(
                                        title_text, 1.0, 1.8)
                                elif title_animation == "instagram_story":
                                    title_text = apply_instagram_story_animation(
                                        title_text, 1.2)

                                # Create background effect if specified
                                if background_effect and background_effect != "none":
                                    title_bg = create_background_effect(
                                        title_text, video_clip,
                                        effect_type=background_effect,
                                        opacity=0.7,
                                        padding=15
                                    )
                                    clips.append(title_bg)

                                # Add to clips
                                clips.append(title_text)
                                print(
                                    f"Added animated title text overlay with {title_animation} effect")
                            except Exception as title_error:
                                print(
                                    f"Error creating animated title: {title_error}. Using simple text.")
                                # Fallback to simple text
                                title_text = TextClip(f"Exercise: {exercise_name}",
                                                      fontsize=title_size,
                                                      color='white',
                                                      bg_color='black',
                                                      font='Arial-Bold')
                                title_text = title_text.set_position(
                                    ('center', 20))
                                title_text = title_text.set_start(title_delay)
                                title_text = title_text.set_duration(
                                    video_duration - title_delay)
                                clips.append(title_text)

                            # Add form tip in the middle (either from database or generic)
                            hook_content = None
                            if exercise_info and hasattr(exercise_info, 'hook') and exercise_info.hook:
                                hook_content = exercise_info.hook
                            else:
                                hook_content = "Maintain proper form throughout exercise"

                            if hook_content and len(str(hook_content).strip()) > 0:
                                try:
                                    hook_text = create_text_clip(
                                        f"FORM TIP: {hook_content}",
                                        position=('center', int(height * 0.5)),
                                        size=hook_size,
                                        fontcolor='white',
                                        fontfamily='Arial',
                                        text_style=animation_style  # Pass the style
                                    )

                                    # Position and set duration
                                    hook_text = hook_text.set_start(hook_delay)
                                    hook_text = hook_text.set_duration(
                                        video_duration - hook_delay)

                                    # Apply animation based on style
                                    if hook_animation == "fade":
                                        hook_text = apply_fade_animation(
                                            hook_text, duration=1.5, direction="in")
                                    elif hook_animation == "slide_right":
                                        hook_text = apply_slide_animation(
                                            hook_text, slide_duration=1.2, direction="right")
                                    elif hook_animation == "typewriter":
                                        hook_text = apply_typewriter_animation(
                                            hook_text, typewriter_speed=0.05)
                                    elif hook_animation == "bounce":
                                        hook_text = apply_bounce_animation(
                                            hook_text, bounce_height=15, bounce_duration=0.8)
                                    elif hook_animation == "glow":
                                        hook_text = apply_glow_animation(
                                            hook_text, glow_duration=2.0, glow_intensity=1.3)
                                    elif hook_animation == "zoom":
                                        hook_text = apply_zoom_animation(
                                            hook_text, 1.0, 1.8)
                                    elif hook_animation == "instagram_story":
                                        hook_text = apply_instagram_story_animation(
                                            hook_text, 1.2)

                                    # Create background effect if specified
                                    if background_effect and background_effect != "none":
                                        hook_bg = create_background_effect(
                                            hook_text, video_clip,
                                            effect_type=background_effect,
                                            opacity=0.7,
                                            padding=15
                                        )
                                        clips.append(hook_bg)

                                    # Add to clips
                                    clips.append(hook_text)
                                    print(
                                        f"Added animated hook text overlay with {hook_animation} effect: {hook_content}")
                                except Exception as hook_error:
                                    print(
                                        f"Error creating hook text clip: {hook_error}")
                                    # Fallback to simple text
                                    hook_text = TextClip(f"FORM TIP: {hook_content}",
                                                         fontsize=hook_size,
                                                         color='white',
                                                         bg_color='black',
                                                         font='Arial')
                                    hook_text = hook_text.set_position(
                                        ('center', int(height * 0.5)))
                                    hook_text = hook_text.set_start(
                                        hook_delay)
                                    hook_text = hook_text.set_duration(
                                        video_duration - hook_delay)
                                    clips.append(hook_text)

                            # Add technique tip at the bottom (either from database or generic)
                            tip_content = None
                            if exercise_info and hasattr(exercise_info, 'technique_tips') and exercise_info.technique_tips:
                                tip = exercise_info.technique_tips
                                if isinstance(tip, list) and len(tip) > 0:
                                    tip_content = tip[0]
                                else:
                                    tip_content = tip
                            else:
                                tip_content = "Control movement, feel the muscle"

                            if tip_content and len(str(tip_content).strip()) > 0:
                                try:
                                    tip_text = create_text_clip(
                                        f"TECHNIQUE: {tip_content}",
                                        position=('center', height -
                                                  int(height * 0.12)),
                                        size=tip_size,
                                        fontcolor='white',
                                        fontfamily='Arial',
                                        text_style=animation_style  # Pass the style
                                    )

                                    # Position and set duration
                                    tip_text = tip_text.set_start(tip_delay)
                                    tip_text = tip_text.set_duration(
                                        video_duration - tip_delay)

                                    # Apply animation based on style
                                    if tip_animation == "fade":
                                        tip_text = apply_fade_animation(
                                            tip_text, duration=1.5, direction="in")
                                    elif tip_animation == "slide_left":
                                        tip_text = apply_slide_animation(
                                            tip_text, slide_duration=1.2, direction="left")
                                    elif tip_animation == "slide_bottom":
                                        tip_text = apply_slide_animation(
                                            tip_text, slide_duration=1.2, direction="bottom")
                                    elif tip_animation == "glow":
                                        tip_text = apply_glow_animation(
                                            tip_text, glow_duration=2.0, glow_intensity=1.3)
                                    elif tip_animation == "bounce":
                                        tip_text = apply_bounce_animation(
                                            tip_text, bounce_height=15, bounce_duration=0.8)
                                    elif tip_animation == "typewriter":
                                        tip_text = apply_typewriter_animation(
                                            tip_text, typewriter_speed=0.05)
                                    elif tip_animation == "slide_up":
                                        tip_text = apply_slide_up_animation(
                                            tip_text, 1.0)
                                    elif tip_animation == "zoom":
                                        tip_text = apply_zoom_animation(
                                            tip_text, 1.0, 1.8)
                                    elif tip_animation == "instagram_story":
                                        tip_text = apply_instagram_story_animation(
                                            tip_text, 1.2)

                                    # Create background effect if specified
                                    if background_effect and background_effect != "none":
                                        tip_bg = create_background_effect(
                                            tip_text, video_clip,
                                            effect_type=background_effect,
                                            opacity=0.7,
                                            padding=15
                                        )
                                        clips.append(tip_bg)

                                    # Add to clips
                                    clips.append(tip_text)
                                    print(
                                        f"Added animated technique tip overlay with {tip_animation} effect: {tip_content}")
                                except Exception as tip_error:
                                    print(
                                        f"Error creating technique tip clips: {tip_error}")
                                    # Fallback to simple text
                                    tip_text = TextClip(f"TECHNIQUE: {tip_content}",
                                                        fontsize=tip_size,
                                                        color='white',
                                                        bg_color='black',
                                                        font='Arial')
                                    tip_text = tip_text.set_position(
                                        ('center', height - int(height * 0.12)))
                                    tip_text = tip_text.set_start(
                                        tip_delay)
                                    tip_text = tip_text.set_duration(
                                        video_duration - tip_delay)
                                    clips.append(tip_text)

                        except Exception as text_error:
                            print(
                                f"Error creating text overlays: {text_error}")
                            traceback.print_exc()
                            # Continue with just the video if text overlays fail

                        # Apply instagram-style color grading to the video if specified
                        if color_grade and color_grade != "none":
                            video_clip = apply_color_grading(
                                video_clip, style=color_grade)

                        # Create the final video
                        try:
                            print(
                                f"Creating final video with {len(clips)} clips")
                            final_clip = CompositeVideoClip(clips)

                            # Export settings optimized for Instagram
                            final_clip.write_videofile(
                                output_path,
                                codec='libx264',
                                audio_codec='aac',
                                temp_audiofile='temp-audio.m4a',
                                remove_temp=True,
                                bitrate='8000k'
                            )

                            # Create a basic caption
                            caption = f"Exercise: {exercise_name}\n"
                            if exercise_info:
                                if hasattr(exercise_info, 'hook') and exercise_info.hook:
                                    caption += f"\nForm Tip: {exercise_info.hook}\n"
                                if hasattr(exercise_info, 'technique_tips') and exercise_info.technique_tips:
                                    tip = exercise_info.technique_tips
                                    if isinstance(tip, list) and len(tip) > 0:
                                        tip = tip[0]
                                    caption += f"\nTechnique: {tip}\n"
                            else:
                                # Add generic captions if no exercise info
                                caption += "\nForm Tip: Maintain proper form throughout exercise\n"
                                caption += "\nTechnique: Control movement, feel the muscle\n"

                            print(
                                f"Video processing complete. Saved to: {output_path}")
                            return output_path, caption

                        except Exception as composite_error:
                            print(
                                f"Error creating composite video: {composite_error}")
                            traceback.print_exc()
                            # Try basic file copy as last resort
                            import shutil
                            shutil.copy(video_path, output_path)
                            return output_path, f"Exercise: {exercise_name}"

                    except Exception as e:
                        print(f"Error in safe_process_video: {e}")
                        traceback.print_exc()
                        # If we get here, everything failed, so try original or return None
                        try:
                            print(
                                "Attempting to use original process_video method...")
                            return original_process_video(video_path, text_style, hook_position, tip_position)
                        except Exception as final_error:
                    print(f"All processing methods failed: {final_error}")
                    # Return None values to indicate failure
                    # The calling code should handle this gracefully
                    return None, None

        # Replace the original function with our safe version
        text_overlay.process_video = safe_process_video

        print("Enhanced text overlay patch with complex animations applied successfully.")

        # Create a social media style selection UI
        def select_social_media_style(video_path=None):
            """
            Present a UI for selecting social media style options for the video.

            Returns a dictionary with all the selected style options.
            """
            import tkinter as tk
            from tkinter import ttk, filedialog
            import os

            # Initialize with defaults
            selected_options = {
                "text_style": "bold_statement",
                "animation_style": "fade",
                "background_effect": "gradient_bar",
                "color_grade": "fitness",
                "video_path": video_path
            }

            # Create the root window
            root = tk.Tk()
            root.title("Social Media Video Styler")
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

            video_path_var = tk.StringVar(
                value=video_path if video_path else "No video selected")

            path_label = tk.Label(file_frame, textvariable=video_path_var,
                                  bg="#f0f0f0", fg="#333333", font=("Arial", 10))
            path_label.pack(fill=tk.X, pady=(0, 10))

            def browse_video():
                file_path = filedialog.askopenfilename(
                    filetypes=[
                        ("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv")]
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
                ("Instagram Story", "instagram_story"),
                ("Typewriter", "typewriter"),
                ("Bouncy Text", "bouncy_text"),
                ("Glowing Text", "glowing"),
                ("Zoom In", "zoom_in")
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
                ("Glowing", "glow"),
                ("Zoom", "zoom")
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
                ("Corner Box", "corner_box"),
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
                ("Vintage", "vintage"),
                ("Instagram Classic", "instagram"),
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

        # Function to patch the original simple_blue_video.py
        def patch_simple_blue_video():
            """
            Main function to apply the patch to the simple_blue_video.py script.
            Enhances the video generation with social media optimized text and animations.
            """
            try:
                # Allow user to select style options through UI
                style_options = select_social_media_style()

                if not style_options["video_path"]:
                    print("No video selected. Exiting.")
                    return

                # Process the video with the selected style options
                output_path = safe_process_video(
                    style_options["video_path"],
                    text_style=style_options["text_style"],
                    background_effect=style_options["background_effect"],
                    color_grade=style_options["color_grade"]
                )

                if output_path:
                    print(f"\nSuccess! Enhanced video saved to: {output_path}")
                    print(
                        "Your video now has professional social media-ready text and animations!")

                    # Attempt to open the video for preview
                    try:
                        import os
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
                else:
                    print(
                        "Failed to enhance video. Please check the error messages above.")

            except Exception as e:
                print(f"Error in patch execution: {e}")
                import traceback
                traceback.print_exc()

except Exception as e:
    print(f"Error loading text overlay patch: {e}")
    import traceback
    traceback.print_exc()
