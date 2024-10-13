import subprocess

def get_audio(input_video_file, output_audio_file):
    subprocess.run([
            "ffmpeg",
            "-i", input_video_file,  # Input video file
            "-acodec", "pcm_s16le",  # 16-bit PCM codec for WAV
            "-ar", "44100",  # 44.1kHz sample rate
            "-y",  # Overwrite output file if it exists
            output_audio_file
        ], check=True)

    return output_audio_file