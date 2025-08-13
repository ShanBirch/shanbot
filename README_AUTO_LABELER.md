# Fitness Video Auto-Labeler

An application that automatically analyzes fitness videos, identifies exercises being performed based on filenames, and adds professional text overlays with technique tips and descriptions suitable for social media posting.

## Features

- **Automatic Exercise Recognition**: Identifies exercises from video filenames
- **Professional Text Overlays**: Adds eye-catching hooks and sequential technique tips
- **Instagram Caption Generation**: Creates ready-to-post captions with hashtags
- **Multiple Style Options**: Choose from various text overlay styles and positions
- **Directory Monitoring**: Watches folders for new videos to process automatically
- **Batch Processing**: Process multiple videos at once
- **User-Friendly GUI**: Easy-to-use interface for all functions

## Installation

1. Ensure you have Python 3.7+ installed on your system
2. Clone or download this repository
3. Install required dependencies:

```
pip install -r requirements_auto_labeler.txt
```

## Quick Start

### Command-Line Usage

Run the application without the GUI:

```
python video_auto_labeler.py --directory "C:\Path\To\Your\Videos" --style minimal
```

Options:
- `--directory` or `-d`: Directory to monitor for videos (default: "C:\Users\Shannon\OneDrive\Desktop\shanbot\Content Videos")
- `--style` or `-s`: Text style preset (choices: minimal, bold_statement, fitness_pro, instagram_classic)
- `--hook-position`: Position for hook text (choices: top_banner, bottom_banner, side_panel_left, side_panel_right, center_focus, corner_tip)
- `--tip-position`: Position for technique tips (same choices as hook-position)
- `--process-existing`: Whether to process existing videos in the directory (true/false)
- `--process-now`: Process existing videos once without changing configuration

### GUI Usage

For a more user-friendly experience, run the GUI version:

```
python video_auto_labeler_gui.py
```

With the GUI, you can:
1. Configure monitoring directories
2. Choose text styles and positions
3. Add videos manually
4. Process videos with a click
5. View the processing queue
6. See console output in real-time

## How It Works

### Naming Your Videos

The application recognizes exercises based on video filenames. For best results, use simple descriptive names:

- `Squat.mp4` - Recognized as a basic squat
- `DeadliftRomanian.mov` - Recognized as a Romanian deadlift variation
- `Push_Up.mp4` - Recognized as a push-up
- `SquatGoblet.mp4` - Recognized as a goblet squat variation

### Text Overlay Styles

The app includes several text overlay styles:

1. **Minimal**: Clean white text with subtle drop shadow
2. **Bold Statement**: Large, bold text with semi-transparent background
3. **Fitness Pro**: Medium-sized text in brand colors with accent bars
4. **Instagram Classic**: Text on colored rectangle background

### Text Positioning

Control where text appears with these positioning options:

1. **Top Banner**: Text at top of frame
2. **Bottom Banner**: Text at bottom of frame
3. **Side Panel**: Text along right or left side
4. **Center Focus**: Large text in center (ideal for hooks)
5. **Corner Tip**: Small text in corner (good for numbered tips)

## Extending the Exercise Database

The app comes with a pre-populated database of common exercises. To add more:

1. Open `exercise_database.py`
2. Add a new entry to the `DEFAULT_DATABASE` dictionary
3. Follow the existing format (name, variations, primary muscles, hook, technique tips, etc.)
4. Restart the application

## Troubleshooting

- **Video not recognized**: Ensure the filename matches a known exercise in the database
- **Processing errors**: Check the console output for specific error messages
- **Missing fonts**: The app will fall back to system fonts if specified fonts aren't available
- **Long processing times**: Video processing is CPU-intensive; be patient with longer videos

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using MoviePy for video processing
- Uses Watchdog for directory monitoring
- Designed for fitness professionals, trainers, and content creators 