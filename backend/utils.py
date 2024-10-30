# utils.py
import tempfile
import os
import subprocess
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import replicate
import time
import requests
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATA_DIR = 'data'
MAX_FILE_AGE = timedelta(hours=24)  # Clean files older than 24 hours

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@contextmanager
def video_clip_manager(clip):
    """Context manager for properly handling video clips"""
    try:
        yield clip
    finally:
        try:
            clip.close()
        except Exception as e:
            logger.error(f"Error closing video clip: {e}")

def cleanup_old_files():
    """Clean up old files from DATA_DIR"""
    try:
        current_time = datetime.now()
        for filename in os.listdir(DATA_DIR):
            filepath = os.path.join(DATA_DIR, filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            if current_time - file_modified > MAX_FILE_AGE:
                try:
                    os.remove(filepath)
                    logger.info(f"Removed old file: {filepath}")
                except Exception as e:
                    logger.error(f"Error removing file {filepath}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def save_uploaded_video(uploaded_video):
    """Save uploaded video with error handling"""
    try:
        filepath = os.path.join(DATA_DIR, 'uploaded_video.mp4')
        with open(filepath, 'wb') as f:
            f.write(uploaded_video.getbuffer())
        return filepath
    except Exception as e:
        logger.error(f"Error saving uploaded video: {e}")
        raise

def extract_audio(video_path):
    """Extract audio from video with error handling"""
    try:
        audio_path = os.path.join(DATA_DIR, 'audio.wav')
        result = subprocess.run(
            ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
             '-ac', '1', '-ar', '16000', '-y', audio_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception("Failed to extract audio")
            
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        raise

def extract_video_segments(video_path, timestamps):
    """Extract video segments with proper resource management"""
    segments = []
    output_path = os.path.join(DATA_DIR, 'new_video.mp4')
    
    try:
        with video_clip_manager(VideoFileClip(video_path)) as video:
            for ts in timestamps:
                try:
                    start_time = float(ts['start'].replace(":", "").replace(".", "")) / 1000
                    end_time = float(ts['end'].replace(":", "").replace(".", "")) / 1000
                    segment = video.subclip(start_time, end_time)
                    segments.append(segment)
                except Exception as e:
                    logger.error(f"Error processing segment {ts}: {e}")
                    continue
            
            if not segments:
                raise Exception("No valid segments to process")
                
            final_video = concatenate_videoclips(segments)
            final_video.write_videofile(output_path, codec="libx264")
            final_video.close()
            
            return output_path
            
    except Exception as e:
        logger.error(f"Error extracting video segments: {e}")
        raise
    finally:
        # Clean up segments
        for segment in segments:
            try:
                segment.close()
            except:
                pass

def get_cloned_voice(audio_path, ref_text, text):
    """Get cloned voice with proper error handling and timeouts"""
    try:
        with open(audio_path, "rb") as speaker:
            input_data = {
                "gen_text": text,
                "ref_text": ref_text,
                "ref_audio": speaker,
                "speed": 0.8
            }
            
            # Create prediction with timeout handling
            prediction = replicate.predictions.create(
                "87faf6dd7a692dd82043f662e76369cab126a2cf1937e25a9d41e0b834fd230e",
                input=input_data
            )
            
            # Wait for prediction with timeout
            timeout = time.time() + 300  # 5 minute timeout
            while time.time() < timeout:
                prediction.reload()
                if prediction.status == "succeeded":
                    break
                elif prediction.status in {"failed", "canceled"}:
                    raise Exception(f"Prediction failed with status: {prediction.status}")
                time.sleep(2)
            else:
                raise Exception("Prediction timed out")
            
            # Download the result
            output_url = prediction.output
            response