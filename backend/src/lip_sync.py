import replicate
import time
import requests
import shutil
import os

def get_lip_sync(face_path, audio_path):
    if os.path.exists("lip_sync_outputs"):
        shutil.rmtree("lip_sync_outputs")
    os.makedirs("lip_sync_outputs", exist_ok=True)

    face = open(face_path, "rb")
    audio = open(audio_path, "rb")
    idx = face_path.split('.')[0].split('_')[-1]

    input={
        "face": face,
        "audio": audio,
        "fps": 25,
        "pads": "0 10 0 0",
        "smooth": True,
        "resize_factor": 1
    }

    prediction = replicate.predictions.create(
        "8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
        input=input
    )

    for i in range(20):
        prediction.reload()
        if prediction.status in {"succeeded", "failed", "canceled"}:
            break

        time.sleep(2)


    output_url = prediction.output

    response = requests.get(output_url)
    if response.status_code == 200:
        content_type = response.headers.get('content-type')
        if 'video' in content_type:
            extension = '.mp4'
        
        filename = f"output_new_clip_{idx}{extension}"
        
        with open(os.path.join('lip_sync_outputs', filename), 'wb') as f:
            f.write(response.content)

