# services/audio_service.py
import os
import subprocess
from moviepy.editor import AudioFileClip
from moviepy.audio.fx.all import volumex
import replicate
import requests
import time

class AudioService:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

    def extract_audio(self, video_path: str, audio_path: str) -> str:
        audio_path = os.path.join(self.data_dir, audio_path)
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            '-y', audio_path
        ])
        return audio_path

    def get_cloned_voice(self, audio_path: str, ref_text: str, text: str) -> str:
        with open(audio_path, "rb") as speaker:
            prediction = replicate.predictions.create(
                "87faf6dd7a692dd82043f662e76369cab126a2cf1937e25a9d41e0b834fd230e",
                input={
                    "gen_text": text,
                    "ref_text": ref_text,
                    "ref_audio": speaker,
                }
            )

        for _ in range(100):
            prediction.reload()
            if prediction.status in {"succeeded", "failed", "canceled"}:
                break
            time.sleep(2)

        output_url = prediction.output
        response = requests.get(output_url)
        
        if response.status_code == 200:
            filename = os.path.join(self.data_dir, "cloned_voice.mp3")
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            audio = AudioFileClip(filename)
            audio = volumex(audio, 1.5)
            return audio

