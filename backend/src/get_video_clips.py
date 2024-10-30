import subprocess

def timestamp_to_seconds(timestamp):
    """Converts a timestamp string to seconds."""
    time_parts = timestamp.split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds_part = time_parts[2].split('.')
    seconds = int(seconds_part[0])
    milliseconds = int(seconds_part[1]) if len(seconds_part) > 1 else 0
    total_seconds = (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000)
    return total_seconds

def extract_subclips(video_path, final_timestamps):
    """Extracts subclips from a video based on timestamps."""
    for clip_num, (start_timestamp, end_timestamp) in final_timestamps.items():
        start_seconds = timestamp_to_seconds(start_timestamp)
        end_seconds = timestamp_to_seconds(end_timestamp)
        output_path = f"clip_{clip_num}.mp4"
        
        cmd = [
            "ffmpeg",
            "-ss", str(start_seconds),  # Move -ss before -i
            "-i", video_path,
            "-to", str(end_seconds - start_seconds),  # Duration instead of end time
            "-map", "0:v",  # Select video stream
            "-map", "0:a",  # Select audio stream
            "-c:v", "libx264",  # Re-encode video with libx264
            "-c:a", "aac",  # Re-encode audio with AAC
            "-avoid_negative_ts", "make_zero",
            output_path,
            "-y"  # Overwrite existing files
        ]
        
        # Capture FFmpeg's output for debugging
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"Extracted clip {clip_num} to {output_path}")
        else:
            print(f"Error extracting clip {clip_num}: {result.stderr.decode()}")