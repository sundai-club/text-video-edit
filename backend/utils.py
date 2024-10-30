import tempfile
import os
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import replicate
import time
import requests


DATA_DIR = 'data'

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_uploaded_video(uploaded_video):
    with open(DATA_DIR + '/uploaded_video.mp4', 'wb') as f:
        f.write(uploaded_video.getbuffer())
    return DATA_DIR + '/uploaded_video.mp4'

def extract_audio(video_path):
    audio_path = DATA_DIR + '/audio.wav'
    subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', '-y', audio_path])
    return audio_path

def extract_video_segments(video_path, timestamps):
    video = VideoFileClip(video_path)
    
    output_path = DATA_DIR + '/new_video.mp4'
    
    segments = []
    
    for ts in timestamps:
        start = float(ts['start'].replace(":", "").replace(".", "")) / 1000
        end = float(ts['end'].replace(":", "").replace(".", "")) / 1000
        segment = video.subclip(start, end)
        segments.append(segment)
    
    final_video = concatenate_videoclips(segments)
    
    final_video.write_videofile(output_path, codec="libx264")
    
    video.close()
    final_video.close()
    for segment in segments:
        segment.close()
    return output_path


def get_cloned_voice(audio_path, ref_text, text):
    
    speaker = open(audio_path, "rb")

    input = {
            "gen_text": text,
            "ref_text": ref_text,
            "ref_audio": speaker,
            "speed": 0.8
            }


    prediction = replicate.predictions.create(
        "87faf6dd7a692dd82043f662e76369cab126a2cf1937e25a9d41e0b834fd230e",
        input=input
    )


    for i in range(100):
        prediction.reload()
        if prediction.status in {"succeeded", "failed", "canceled"}:
            break
        time.sleep(2)


    output_url = prediction.output

    response = requests.get(output_url)
    if response.status_code == 200:
        content_type = response.headers.get('content-type')
        if 'audio' in content_type:
            extension = '.mp3'
        
        filename = f"cloned_voice{extension}"
        
        with open(os.path.join(DATA_DIR, filename), 'wb') as f:
            f.write(response.content)

        return os.path.join(DATA_DIR, filename)



def modify_and_patch_video(video_path, audio_path, timestamps, ref_text):
    """
    Modifies a video by replacing audio in specified segments with cloned voice audio.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path to the reference audio file
        timestamps (list): List of dictionaries containing segment information
        ref_text (str): Reference text for voice cloning
    
    Returns:
        str: Path to the output synchronized video file
    """
    video = VideoFileClip(video_path)
    output_path = os.path.join(DATA_DIR, 'synced_video.mp4')
    temp_clips = []  # Store temporary clips
    
    try:
        segments = []
        current_time = 0  # Keep track of cumulative duration
        
        for ts in timestamps:
            # Convert timestamps to seconds more reliably
            start = float(ts['start'].replace(":", "").replace(".", "")) / 1000
            end = float(ts['end'].replace(":", "").replace(".", "")) / 1000
            duration = end - start
            
            # Ensure chronological order and valid durations
            if start < 0 or end > video.duration or start >= end:
                raise ValueError(f"Invalid timestamp values: start={start}, end={end}")
            
            # Extract video segment
            video_segment = video.subclip(start, end)
            
            if ts.get('sync', False):  # Check if this segment needs audio sync
                # Generate cloned voice audio
                cloned_audio_path = get_cloned_voice(audio_path, ref_text, ts['text'])
                if not cloned_audio_path or not os.path.exists(cloned_audio_path):
                    raise ValueError(f"Failed to generate cloned audio for segment: {ts}")
                
                # Load and verify cloned audio
                cloned_audio = AudioFileClip(cloned_audio_path)
                temp_clips.append(cloned_audio)  # Store for cleanup
                
                # Adjust audio duration to match video segment if needed
                if abs(cloned_audio.duration - duration) > 0.1:  # Allow small tolerance
                    cloned_audio = cloned_audio.set_duration(duration)
                
                # Apply the new audio to the video segment
                video_segment = video_segment.set_audio(cloned_audio)
            
            segments.append(video_segment)
            current_time += duration
        
        # Concatenate all segments
        final_video = concatenate_videoclips(segments, method="compose")
        
        # Write the final video with proper codec settings
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(DATA_DIR, "temp-audio.m4a"),
            remove_temp=True,
            fps=video.fps
        )
        
        return output_path
    
    finally:
        # Clean up resources
        video.close()
        
        # Clean up all temporary clips
        for clip in temp_clips:
            try:
                clip.close()
            except Exception:
                pass
                
        # Clean up segments
        for segment in segments:
            try:
                segment.close()
            except Exception:
                pass