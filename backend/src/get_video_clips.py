import ffmpeg
import os
import subprocess
import shutil

from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)


def extract_videos(video_path, timestamp_tuples, output_dir='videos_output'):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    
    for idx, (start_time, end_time) in enumerate(timestamp_tuples):
        output_video_path = os.path.join(output_dir, f"video_{idx}.mp4")
        output_files.append(output_video_path)
        
        try:
            # Convert start and end times to datetime objects
            start = datetime.strptime(start_time.strip('"'), "%H:%M:%S.%f")
            end = datetime.strptime(end_time.strip('"'), "%H:%M:%S.%f")
            
            # Calculate duration in seconds
            duration_seconds = (end - start).total_seconds()
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-ss', start_time.strip('"'),
                '-t', str(duration_seconds),
                '-c', 'copy',
                output_video_path,
                '-y'
            ]
            
            # Run the ffmpeg command using subprocess
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                logging.error(f"Error processing video segment {idx}: {result.stderr}")
            else:
                logging.info(f"Successfully extracted video segment {idx}")
        
        except Exception as e:
            logging.error(f"Error processing video segment {idx}: {str(e)}")
    
    return output_files