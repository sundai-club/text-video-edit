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
    video = VideoFileClip(video_path)
    
    output_path = DATA_DIR + '/synced_video.mp4'
    
    segments = []
    
    for ts in timestamps:
        start = float(ts['start'].replace(":", "").replace(".", "")) / 1000
        end = float(ts['end'].replace(":", "").replace(".", "")) / 1000
        sync = ts['sync']

        if sync:
            segment = video.subclip(start, end)
            text = ts['text']
            to_set_audio_path = get_cloned_voice(audio_path, ref_text, text)
            new_audio = AudioFileClip(to_set_audio_path).subclip(0)
            segment = segment.set_audio(new_audio)
        else:
            segment = video.subclip(start, end)
        segments.append(segment)
    
    final_video = concatenate_videoclips(segments)
    
    final_video.write_videofile(output_path, codec="libx264")
    
    video.close()
    final_video.close()
    for segment in segments:
        segment.close()
    return output_path