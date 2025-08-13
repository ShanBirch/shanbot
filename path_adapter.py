#!/usr/bin/env python
"""
Path adapter module to help with the transition to the new folder structure.
Import this in your scripts to get proper paths to files in the new structure.
"""
import os
import yaml
from pathlib import Path

# Get the base directory
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Paths to subdirectories
PATHS = {
    "data": BASE_DIR / "data",
    "scripts": BASE_DIR / "scripts",
    "logs": BASE_DIR / "logs",
    "media": BASE_DIR / "media",
    "media_music": BASE_DIR / "media" / "music",
    "media_templates": BASE_DIR / "media" / "templates",
    "output": BASE_DIR / "output",
    "batch": BASE_DIR / "batch",
}

# Load settings if available
SETTINGS = {}
settings_file = BASE_DIR / "settings.yaml"
if os.path.exists(settings_file):
    try:
        with open(settings_file, 'r') as f:
            SETTINGS = yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load settings file: {e}")

def get_path(name):
    """Get the path to a subdirectory"""
    return PATHS.get(name, BASE_DIR)

def get_data_file_path(filename):
    """Get the path to a data file"""
    return PATHS["data"] / filename

def get_template_video_path():
    """Get the path to the template video"""
    # First try the settings
    if SETTINGS and "video" in SETTINGS and "template" in SETTINGS["video"]:
        template_path = BASE_DIR / SETTINGS["video"]["template"]
        if os.path.exists(template_path):
            return template_path
    
    # Then try the default locations
    template_path = PATHS["media_templates"] / "blue2.mp4"
    if os.path.exists(template_path):
        return template_path
        
    fallback_path = PATHS["media_templates"] / "blue.mp4"
    if os.path.exists(fallback_path):
        return fallback_path
        
    # Finally try the root directory
    root_template = BASE_DIR / "blue2.mp4"
    if os.path.exists(root_template):
        return root_template
        
    root_fallback = BASE_DIR / "blue.mp4"
    if os.path.exists(root_fallback):
        return root_fallback
    
    return None
