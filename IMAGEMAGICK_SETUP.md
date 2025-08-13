# ImageMagick Setup for Video Auto-Labeler

The Video Auto-Labeler application requires ImageMagick to be installed on your system for text overlay functionality. This guide will help you install and configure ImageMagick properly.

## Installation Steps

1. **Download ImageMagick**:
   - Go to the [ImageMagick download page](https://imagemagick.org/script/download.php)
   - For Windows 64-bit systems, download the recommended installer: `ImageMagick-7.1.1-44-Q16-HDRI-x64-dll.exe` (or the latest version)

2. **Install with Legacy Utilities**:
   - Run the installer
   - **IMPORTANT**: During installation, make sure to check the "Install legacy utilities" option
   - This is crucial for MoviePy to work correctly with ImageMagick

3. **Verify Installation**:
   - Open a command prompt (cmd)
   - Type `magick --version` and press Enter
   - You should see version information for ImageMagick

## Troubleshooting

If you encounter errors like:

```
OSError: MoviePy Error: creation of None failed because of the following error:
OSError: [WinError 2] The system cannot find the file specified.
"ImageMagick is not installed on your computer, or (for Windows users) that you didn't specify the path to the ImageMagick binary in file conf.py, or that the path you specified is incorrect"
```

Try these solutions:

1. **Run the configuration script**:
   ```
   python configure_imagemagick.py
   ```
   This script will attempt to locate your ImageMagick installation and configure MoviePy to use it.

2. **Manually set the path**:
   - Find where ImageMagick is installed (typically `C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\`)
   - Look for `magick.exe` in that folder
   - Add this code at the beginning of your script:
   ```python
   from moviepy.config import change_settings
   change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
   ```
   (Adjust the path to match your actual installation location)

3. **Reinstall ImageMagick**:
   - Uninstall the current version
   - Download and reinstall, making sure to check "Install legacy utilities"

## Additional Resources

- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [ImageMagick Documentation](https://imagemagick.org/script/command-line-processing.php)

If you continue to experience issues, please check the error messages carefully as they often provide specific information about what's missing or misconfigured. 