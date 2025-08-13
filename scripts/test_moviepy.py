import sys
print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\nTrying to import moviepy...")
try:
    import moviepy
    print(f"Success! MoviePy version: {moviepy.__version__}")
    print(f"MoviePy path: {moviepy.__file__}")
    
    print("\nTrying to import moviepy.editor...")
    try:
        from moviepy.editor import *
        print("Successfully imported moviepy.editor!")
    except Exception as e:
        print(f"Error importing moviepy.editor: {e}")
except Exception as e:
    print(f"Error importing moviepy: {e}")