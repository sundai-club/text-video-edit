import replicate
import time
import sys
import requests
import shutil
import os
import json

def get_cloned_voice(speaker_wav_path, idx, text, language):

    if os.path.exists("voice_cloned_outputs"):
        shutil.rmtree("voice_cloned_outputs")
    
    os.makedirs("voice_cloned_outputs", exist_ok=True)

    speaker = open(speaker_wav_path, "rb")
    ref_text = json.load(open(speaker_wav_path.replace(".wav", ".json"), 'rb'))
    ref_text = [t['text'] for t in ref_text]
    ref_text = ' '.join(ref_text)


    input = {
            "gen_text": text,
            "ref_text": ref_text,
            "ref_audio": speaker,
            }


    prediction = replicate.predictions.create(
        "87faf6dd7a692dd82043f662e76369cab126a2cf1937e25a9d41e0b834fd230e",
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
        
        with open(os.path.join('voice_cloned_outputs', filename), 'wb') as f:
            f.write(response.content)


