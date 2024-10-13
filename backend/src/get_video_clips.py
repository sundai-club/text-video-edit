import ffmpeg
import os
import subprocess
def extract_frames(video_path, timestamp_tuples, output_dir='frames_output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_files = []
    
    for idx, (start_time, _) in enumerate(timestamp_tuples):
        output_frame_path = os.path.join(output_dir, f"frame_{idx + 1}.png")
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
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_files = []
    
    for idx, (start_time, end_time) in enumerate(timestamp_tuples):
        output_video_path = os.path.join(output_dir, f"video_{idx + 1}.mp4")
        output_files.append(output_video_path)
        
        command = [
            'ffmpeg',
            '-i', video_path,        # Input video
            '-ss', start_time,       # Seek to the start_time
            '-t', end_time,          # Extract the duration
            '-c', 'copy',            # Copy the video stream
            output_video_path,       # Output file path
            '-y'                     # Overwrite output if exists
        ]
        
        # Run the ffmpeg command using subprocess
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return output_files