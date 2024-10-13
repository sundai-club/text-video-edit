import ffmpeg
import os
import subprocess
import shutil

from datetime import datetime, timedelta
def extract_frames(video_path, timestamp_tuples, output_dir='frames_output'):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_files = []
    
    for x, (start_time, _, idx) in enumerate(timestamp_tuples):
        output_frame_path = os.path.join(output_dir, f"frame_{idx}.png")
        output_files.append(output_frame_path)
        
        command = [
            'ffmpeg',
            '-ss', start_time,       # Seek to the start_time
            '-i', video_path,        # Input video
            '-vframes', '1',         # Extract only one frame
            '-q:v', '2',             # Quality level for the image
            output_frame_path,       # Output file path
            '-y'                     # Overwrite output if exists
        ]
        
        # Run the ffmpeg command using subprocess
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return output_files

def extract_videos(video_path, timestamp_tuples, output_dir='videos_output'):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    
    for idx, (start_time, end_time) in enumerate(timestamp_tuples):
        output_video_path = os.path.join(output_dir, f"video_{idx}.mp4")
        output_files.append(output_video_path)
        
        # Convert start and end times to datetime objects
        start = datetime.strptime(start_time.strip('"'), "%H:%M:%S.%f")
        end = datetime.strptime(end_time.strip('"'), "%H:%M:%S.%f")
        
        # Calculate duration
        duration = end - start
        duration_str = str(duration)
        
        command = [
            'ffmpeg',
            '-i', video_path,        # Input video
            '-ss', start_time.strip('"'),  # Seek to the start_time
            '-t', duration_str,      # Extract the duration
            '-c', 'copy',            # Copy the video stream
            output_video_path,       # Output file path
            '-y'                     # Overwrite output if exists
        ]
        
        # Run the ffmpeg command using subprocess
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return output_files