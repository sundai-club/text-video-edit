import replicate
import time
import sys
import requests
import os


def get_cloned_voice(speaker_wav_path, idx, text, language):
    os.makedirs("voice_cloned_outputs", exist_ok=True)

    speaker = open(speaker_wav_path, "rb")

    input = {
            "speaker": speaker,
            "text": text,
            "language": language,
            "cleanup_voice": True,

            }

    prediction = replicate.predictions.create(
        "684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
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
        if 'audio' in content_type:
            extension = '.mp3'
        
        filename = f"output_new_{idx}{extension}"
        
        with open(os.path.join('voice_cloned_outputs', filename, 'wb')) as f:
            f.write(response.content)


