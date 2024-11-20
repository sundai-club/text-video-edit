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
    audio_path = audio_service.extract_audio(video_path, 'original_audio.wav')
    transcript = transcription_service.transcribe_audio(audio_path)
    with open('data/original_reference_text.txt', 'w') as f:
        f.write(''.join([t['text'] for t in transcript]))
    
    return {
        "transcript": transcript
    }

@app.post("/process-video/")
async def process_video(request: dict):
    video_path = 'data/uploaded_video.mp4'
    timestamps = request["timestamps"]
    logging.info(f"Video path: {video_path}")
    new_video_path = video_service.extract_segments(video_path, timestamps)
    processed_video = FileResponse(new_video_path, media_type="video/mp4", filename="modified_video.mp4")
    return processed_video

def get_to_synced_timestamps(new_transcript, new_new_script):
    to_be_synced_time_stamps = []
    for old_line, new_line in zip(new_transcript.split('\n'), new_new_script.split('\n')):
        timestamp_list = new_line.split(':|:')
        timestamp = timestamp_list[0]
        text = timestamp_list[1]
        start = timestamp.split('-')[0].replace('[', '').strip()
        end = timestamp.split('-')[1].replace(']', '').strip()

        if old_line != new_line:
            to_be_synced_time_stamps.append({'start': start, 'end': end, 'text': text, 'sync': True})
        else:
            to_be_synced_time_stamps.append({'start': start, 'end': end, 'text': text, 'sync': False})
    
    return to_be_synced_time_stamps


@app.post("/modify-video/")
async def modify_video(request: dict):
    new_new_transcript = request["to_lip_sync_transcript"]
    print(new_new_transcript)
    new_audio_path = audio_service.extract_audio('data/new_video.mp4', 'new_audio.wav')
    new_transcript = transcription_service.transcribe_audio(new_audio_path)
    new_transcript = ['[' + x['start'] + ' - ' + x['end'] +']'+ ' :|: ' +  x['text'] for x in new_transcript]
    new_transcript = '\n'.join(new_transcript)

    reference_text = open('data/original_reference_text.txt', 'r').read().strip()
    original_audio_path = 'data/original_audio.wav'
    to_be_synced_time_stamps = get_to_synced_timestamps(new_transcript, new_new_transcript)
    synced_video_path = video_service.modify_and_patch(
        'data/new_video.mp4',
        original_audio_path,
        to_be_synced_time_stamps,
        reference_text
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