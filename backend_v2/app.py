import streamlit as st
import requests
from typing import List
import json

API_URL = "http://localhost:8000"  # FastAPI endpoint

st.set_page_config(
    page_title="ScriptCut",
    page_icon="📝",
)

st.title("ScriptCut")

if 'original_script' not in st.session_state:
    st.session_state.original_script = []
if 'new_script' not in st.session_state:
    st.session_state.new_script = []

st.session_state.bloopers = False

# with st.sidebar:
#     st.title("ScriptCut")
#     st.write("Your personal script editor")
#     bloopers = st.checkbox("Bloopers")
#     st.session_state.bloopers = bloopers

if st.session_state.bloopers:
    cols = st.columns(2)
else:
    cols = st.columns(2)

with cols[0]:
    st.subheader("Upload Video")
    uploaded_video = st.file_uploader("Upload Video")
    button = st.button("Upload")
    if uploaded_video is not None:
        st.video(uploaded_video)

    if button:
        
        # Upload video to FastAPI
        files = {"file": uploaded_video.getvalue()}
        response = requests.post(f"{API_URL}/upload-video/", files=files)
        data = response.json()
        
        
        transcript = ['[' + str(x['start']) + ' - ' + str(x['end']) +']'+ ' :|: ' +  x['text'] 
                     for x in data["transcript"]]
        st.session_state.original_script = '\n'.join(transcript)

with cols[1]:
    st.subheader("Trim Transcript")
    script = st.text_area("Transcript", 
                         st.session_state.original_script if 'original_script' in st.session_state else '', 
                         height=300)
    
    if st.button("Submit"):
        if script:
            timestamps = []
            for line in script.split('\n'):
                timestamp_list = line.split(':|:')
                timestamp = timestamp_list[0]
                text = timestamp_list[1]
                start = timestamp.split('-')[0].replace('[', '').strip()
                end = timestamp.split('-')[1].replace(']', '').strip()
                timestamps.append({"start": start, "end": end, "text": text})
            
            response = requests.post(
                f"{API_URL}/process-video/",
                json={
                    "timestamps": timestamps,
                }
            )
            ## handle file response
            if response.status_code == 200:
                video_content = response.content
                st.video(video_content, format="video/mp4")
                st.session_state.trimmed_video = video_content
                import io

                # Wrap the raw bytes in io.BytesIO
                video_file = io.BytesIO(video_content)
                files = {"file": video_file.getvalue()}
                response = requests.post(f"{API_URL}/upload-video/", files=files)
                data = response.json()
                transcript = ['[' + str(x['start']) + ' - ' + str(x['end']) +']'+ ' :|: ' +  x['text'] 
                     for x in data["transcript"]]
                st.session_state.new_transcript = '\n'.join(transcript)
            
            else:
                st.error(f"Failed to load video: {response.status_code} - {response.text}")


# if not st.session_state.bloopers and 'new_transcript' in st.session_state:
#     with cols[2]:
#         st.subheader("Edit Transcript")
#         new_script = st.text_area("Transcript", st.session_state.new_transcript if 'new_transcript' in st.session_state else '', height=300)
        

        
#         if st.button("Process"):
            
#             response = requests.post(
#                 f"{API_URL}/modify-video/",
#                 json={
#                     "to_lip_sync_transcript": new_script
#                 }
#             )
#             video_content = response.content
#             st.video(video_content, format="video/mp4")