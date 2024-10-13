from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, File, UploadFile
import shutil
from pathlib import Path


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
    video_path = UPLOAD_DIR / file.filename

    with video_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "File uploaded successfully"}



@app.post("/get_transcription")
async def get_transcription():
    pass


@app.post("/process_script")
def process_script(new_script):
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)