# services/video_service.py
import os
import tempfile
from fastapi import UploadFile
from moviepy.editor import VideoFileClip, concatenate_videoclips
from .audio_service import AudioService

class VideoService:
    def __init__(self):
        self.data_dir = "data"
        self.audio_service = AudioService()
        os.makedirs(self.data_dir, exist_ok=True)

    async def save_video(self, file: UploadFile) -> str:
        video_path = os.path.join(self.data_dir, f"uploaded_video.mp4")
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return video_path

    def extract_segments(self, video_path: str, timestamps: list) -> str:
        output_path = os.path.join(self.data_dir, "new_video.mp4")
        
        with VideoFileClip(video_path) as video:
            segments = []
            for ts in timestamps:
                start = float(ts['start'].replace(":", "").replace(".", "")) / 1000
                end = float(ts['end'].replace(":", "").replace(".", "")) / 1000
                segment = video.subclip(start, end)
                segments.append(segment)
            
            final_video = concatenate_videoclips(segments)
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",  # Use AAC for better compatibility
                audio=True
            )
            
        return output_path

    def modify_and_patch(self, video_path: str, audio_path: str, timestamps: list, ref_text: str) -> str:
        output_path = os.path.join(self.data_dir, "synced_video.mp4")
        
        with VideoFileClip(video_path) as video:
            segments = []
            for ts in timestamps:
                start = float(ts['start'].replace(":", "").replace(".", "")) / 1000
                end = float(ts['end'].replace(":", "").replace(".", "")) / 1000
                
                if ts['sync']:
                    segment = video.subclip(start, end)
                    cloned_audio = self.audio_service.get_cloned_voice(
                        audio_path, ref_text, ts['text']
                    )
                    segment = segment.set_audio(cloned_audio)
                else:
                    segment = video.subclip(start, end)
                segments.append(segment)
            
            final_video = concatenate_videoclips(segments)
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                audio=True
            )
            
        return output_path

