from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import os
from services.video_service import VideoService
from services.audio_service import AudioService
from services.transcription_service import TranscriptionService
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()
video_service = VideoService()
audio_service = AudioService()
transcription_service = TranscriptionService()

class TimeStamp(BaseModel):
    start: str
    end: str
    text: str
    sync: bool = False

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    video_path = await video_service.save_video(file)
    audio_path = audio_service.extract_audio(video_path)
    transcript = transcription_service.transcribe_audio(audio_path)
    
    return {
        "video_path": video_path,
        "audio_path": audio_path,
        "transcript": transcript
    }

@app.post("/process-video/")
async def process_video(request: dict):
    video_path = request["video_path"]
    timestamps = request["timestamps"]
    logging.info(f"Video path: {video_path}")
    new_video_path = video_service.extract_segments(video_path, timestamps)
    processed_video = FileResponse(new_video_path, media_type="video/mp4", filename="modified_video.mp4")
    return {"processed_video": processed_video, "new_video_path": new_video_path}


@app.post("/modify-video/")
async def modify_video(
    video_path: str,
    audio_path: str,
    timestamps: List[TimeStamp],
    ref_text: str):
    synced_video_path = video_service.modify_and_patch(
        video_path,
        audio_path,
        timestamps,
        ref_text
    )
    modified_video = FileResponse(synced_video_path, media_type="video/mp4", filename="modified_video.mp4")
    return modified_video

@app.get("/video/{video_name}")
async def get_video(video_name: str):
    video_path = os.path.join("data", video_name)
    return FileResponse(video_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)