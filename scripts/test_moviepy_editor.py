try:
    from moviepy.editor import *
    print("Successfully imported moviepy.editor!")
    print(f"MoviePy version: {VideoFileClip.__module__}")
except Exception as e:
    print(f"Error importing moviepy.editor: {e}")