from app.voice_generator import VoiceGenerator
import sys
import os

def test_voice_cloning(sample_path: str, test_text: str = "Hi, this is a test of my cloned voice. How does it sound?"):
    """
    Test voice cloning with a sample audio file.
    
    Args:
        sample_path: Path to the WAV file containing your voice sample
        test_text: Text to synthesize with the cloned voice
    """
    try:
        print("Initializing voice generator...")
        generator = VoiceGenerator()
        
        # Add the voice sample
        print(f"Adding voice sample from: {sample_path}")
        success = generator.add_voice_sample("my_voice", sample_path)
        if not success:
            print("Failed to add voice sample!")
            return
            
        print("Voice sample added successfully!")
        
        # Try different quality presets
        presets = ['ultra_fast', 'fast', 'standard']
        for preset in presets:
            print(f"\nTrying {preset} preset...")
            generator.set_preset(preset)
            
            output_file = f"test_output_{preset}.wav"
            try:
                output_path = generator.generate_speech(test_text, "my_voice", output_file)
                print(f"Generated speech saved to: {output_path}")
            except Exception as e:
                print(f"Error generating speech with {preset} preset: {e}")
                continue
                
        print("\nVoice cloning test complete!")
        
    except Exception as e:
        print(f"Error during voice cloning test: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_voice_clone.py path/to/your/voice_sample.wav [optional_test_text]")
        sys.exit(1)
        
    sample_path = sys.argv[1]
    test_text = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(sample_path):
        print(f"Error: Voice sample file not found: {sample_path}")
        sys.exit(1)
        
    test_voice_cloning(sample_path, test_text) 