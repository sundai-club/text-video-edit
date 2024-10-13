from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, UploadFile
import shutil
from pathlib import Path
from src.get_audio import extract_audio
from src.word_timestamp import transcribe_audio
from src.get_video_clips import extract_frames, extract_videos
from src.lip_sync import get_lip_sync
from src.voice_cloning import get_cloned_voice
from moviepy.editor import VideoFileClip, concatenate_videoclips


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the directory to store the uploaded videos
UPLOAD_DIR = Path("uploaded_videos")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload_mp4/")
async def upload_mp4(file: UploadFile = File(...)):
    video_path = UPLOAD_DIR / 'uploaded_video.mp4'

    with video_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extract_audio(video_path, video_path.with_suffix(".wav"))
    transcribed_audio = transcribe_audio(video_path.with_suffix(".wav"))

    return {"transciption": transcribed_audio}

def time_str_to_seconds(time_str):
    """Convert a timestamp string (HH:MM:SS.sss) to seconds."""
    hours, minutes, seconds = map(float, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

@app.post("/process_script")
def process_script(original_script, new_script):
    
    to_be_synced = []
    to_be_synced_ids = []
    for _, (old_element, new_element) in enumerate(zip(original_script, new_script)):
        if old_element["start"] == new_element["start"] and old_element["end"] == new_element["end"]:
            if old_element["text"] != new_element["text"]:
                to_be_synced.append({"idx": _+1, "start": old_element["start"], "end": old_element["end"], "text": new_element["text"]})
                to_be_synced_ids.append(_+1)
    time_stamp_tuples = [(x["start"], x["end"]) for x in to_be_synced]
    
    extract_frames('uploaded_videos/uploaded_video.mp4', time_stamp_tuples)

    for i, element in enumerate(to_be_synced):
        text = element["text"]
        get_cloned_voice('output_new.mp3', i, text, 'en')
        get_lip_sync(f'frames_output/frame_{i+1}.png', f'voice_cloned_outputs/voice_cloned_{i}.wav')
    
    org_time_stamps = [(x["start"], x["end"]) for x in original_script]

    extract_videos('uploaded_videos/uploaded_video.mp4', org_time_stamps)

    video_clips = []

    for _, element in enumerate(new_script):
            
        if _+1 in to_be_synced_ids:
            synced_clip_path = f'lip_sync_outputs/output_new_clip_{_+1}.mp4'
            synced_clip = VideoFileClip(synced_clip_path)
            video_clips.append(synced_clip)
        else:
            video_clip_path = f'videos_output/video_{_+1}.mp4'
            video_clip = VideoFileClip(video_clip_path)
            video_clips.append(video_clip)

    final_video = concatenate_videoclips(video_clips)
    final_output_path = 'final_video.mp4'
    final_video.write_videofile(final_output_path)

    return {"message": "Video processed and synced successfully.", "output_video": final_output_path}




    
    
    
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)