import ffmpeg
import os
import subprocess
import shutil
import logging

logging.basicConfig(level=logging.INFO)

def extract_videos(video_path, timestamp_tuples, output_dir='videos_output'):
    """
    Extract video segments based on precise time stamps.
    
    Args:
        video_path (str): Path to the input video file
        timestamp_tuples (list): List of tuples containing (start_time, end_time) in format "HH:MM:SS.NNNNNN"
        output_dir (str): Directory to store output video segments
    
    Returns:
        list: List of paths to the extracted video files
    """
    # Clean/create output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    
    for idx, (start_time, end_time) in enumerate(timestamp_tuples):
        output_video_path = os.path.join(output_dir, f"video_{idx}.mp4")
        output_files.append(output_video_path)
        
        try:
            # Calculate duration by subtracting timestamps directly
            start_seconds = sum(float(x) * y for x, y in zip(
                start_time.split(':')[::-1],
                [1, 60, 3600]
            ))
            end_seconds = sum(float(x) * y for x, y in zip(
                end_time.split(':')[::-1],
                [1, 60, 3600]
            ))
            duration = end_seconds - start_seconds
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-ss', start_time,
                '-t', f"{duration:.6f}",
                '-c', 'copy',  # Use stream copy for faster processing
                '-avoid_negative_ts', '1',  # Handle negative timestamps
                '-y',  # Overwrite output file if it exists
                output_video_path
            ]
            
            # Run ffmpeg command
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Error processing segment {idx}. FFmpeg error: {result.stderr}")
            else:
                logging.info(f"Successfully extracted segment {idx}: {start_time} to {end_time}")
                
        except Exception as e:
            logging.error(f"Error processing segment {idx}: {str(e)}")
            continue
    
    return output_files