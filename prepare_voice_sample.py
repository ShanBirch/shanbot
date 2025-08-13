import ffmpeg
import os
from pathlib import Path

def prepare_voice_sample(input_file: str, output_file: str = None, duration: int = 30, start_time: int = 0):
    """
    Convert and trim an audio file for voice cloning.
    
    Args:
        input_file: Path to the input audio file
        output_file: Path for the output WAV file (optional)
        duration: Duration in seconds to extract (default: 30)
        start_time: Start time in seconds for extraction (default: 0)
    """
    try:
        # Create output filename if not provided
        if output_file is None:
            output_dir = Path("voice_samples")
            output_dir.mkdir(exist_ok=True)
            output_file = str(output_dir / "voice_sample.wav")
        
        print(f"Processing audio file: {input_file}")
        print(f"Extracting {duration} seconds starting at {start_time} seconds")
        
        # Process the audio file
        stream = ffmpeg.input(input_file, ss=start_time, t=duration)
        stream = ffmpeg.output(stream, output_file,
                             acodec='pcm_s16le',  # WAV format
                             ac=1,                # Mono audio
                             ar=24000)            # 24kHz sample rate
        
        # Run the conversion
        ffmpeg.run(stream, overwrite_output=True)
        
        print(f"\nProcessed audio saved to: {output_file}")
        print("You can now use this file with test_voice_clone.py")
        
        return output_file
        
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return None

if __name__ == "__main__":
    # Your audio file path
    input_file = r"C:\Users\Shannon\OneDrive\Documents\Sound Recordings\shanbot1.m4a"
    
    # Process the file
    output_file = prepare_voice_sample(
        input_file,
        duration=30,    # Extract 30 seconds
        start_time=0    # Start from beginning
    )
    
    if output_file:
        print("\nNow you can test the voice cloning with:")
        print(f"python test_voice_clone.py {output_file}") 