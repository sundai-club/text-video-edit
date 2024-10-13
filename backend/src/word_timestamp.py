import whisper
import moviepy.editor as mp
import os
from datetime import timedelta
import subprocess
import time

model = whisper.load_model("medium")

def convert_windows_path_to_wsl(windows_path):
    try:
        wsl_path = subprocess.check_output(['wslpath', '-u', windows_path]).decode('utf-8').strip()
        return wsl_path
    except subprocess.CalledProcessError:
        print("Error converting Windows path to WSL path.")
        return windows_path


def extract_audio(video_path, audio_path):
    try:
        wsl_video_path = convert_windows_path_to_wsl(video_path)
        wsl_audio_path = convert_windows_path_to_wsl(audio_path)

        video = mp.VideoFileClip(wsl_video_path)
        video.audio.write_audiofile(wsl_audio_path)
        video.close()
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


def transcribe_audio(audio_file):

    result = model.transcribe(audio_file, word_timestamps=True)

    return convert_to_timestamp_word_tuples(result)

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def convert_to_timestamp_word_tuples(result):
    timestamp_word_tuples = []
    for segment in result['segments']:
        for word in segment.get('words', []):
            start_time = format_timestamp(word['start'])
            end_time = format_timestamp(word['end'])
            timestamp_word_tuples.append({f"{start_time} - {end_time}": word['word']})
    return timestamp_word_tuples
