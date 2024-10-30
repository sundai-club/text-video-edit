import streamlit as st
from src.word_timestamp import transcribe_audio
from utils import save_uploaded_video, extract_audio, extract_video_segments, modify_and_patch_video
import logging
logging.basicConfig(level=logging.INFO)


st.set_page_config(
    page_title="ScriptCut",
    page_icon="📝",
    layout="wide",
)
st.title("ScriptCut")



# Initialize a variable to hold the transcribed text
transcribed_text = ""

if 'original_script' not in st.session_state:
    st.session_state.original_script = []

if 'new_script' not in st.session_state:
    st.session_state.new_script = []

st.session_state.bloopers = False

with st.sidebar:
    st.image('sundai_logo.jpg', width=100)
    st.title("ScriptCut")
    st.write("Your personal script editor")

    bloopers = st.checkbox("Bloopers")
    st.session_state.bloopers = bloopers

if st.session_state.bloopers:
    cols = st.columns(2)
else:
    cols = st.columns(3)

with cols[0]:
    st.subheader("Upload Video")
    uploaded_video = st.file_uploader("Upload Video")
    if uploaded_video is not None:
        st.video(uploaded_video)
        video_path = save_uploaded_video(uploaded_video)
        audio_path = extract_audio(video_path)        
        if 'audio_path' not in st.session_state:
            st.session_state.audio_path = audio_path
        transcript_response = transcribe_audio(audio_path)
        ref_text = ''.join([x['text'] for x in transcript_response])
        transcript = ['[' + x['start'] + ' - ' + x['end'] +']'+ ' :|: ' +  x['text'] for x in transcript_response]
        transcribed_text = '\n'.join(transcript)
        st.session_state.original_script = transcribed_text
        if 'original_video_path' not in st.session_state:
            st.session_state.original_video_path = video_path
        
        

# Right column for transcript display and editing
with cols[1]:
    st.subheader("Trim Transcript")
    # Use the text area to show the transcript and allow user editing
    script = st.text_area("Transcript", transcribed_text, height=300, placeholder="Script")
    submit = st.button("Submit")
    new_script_final = []
    new_lines = []
    if submit:
        if script:
            new_script = script.split('\n')
            for line in new_script:
                timestamp_list = line.split(':|:')
                timestamp = timestamp_list[0]
                text = timestamp_list[1]
                start = timestamp.split('-')[0].replace('[', '').strip()
                end = timestamp.split('-')[1].replace(']', '').strip()
                new_script_final.append({'start': start, 'end': end, 'text': text})
                new_lines.append(line)
            st.session_state.new_script = script

        if st.session_state.bloopers:
            new_time_stamps = []
            for line in st.session_state.original_script.split('\n'):
                if line not in new_lines:
                    timestamp_list = line.split(':|:')
                    timestamp = timestamp_list[0]
                    text = timestamp_list[1]
                    start = timestamp.split('-')[0].replace('[', '').strip()
                    end = timestamp.split('-')[1].replace(']', '').strip()
                    new_time_stamps.append({'start': start, 'end': end, 'text': text})
            new_script_final = new_time_stamps

        new_video_path = extract_video_segments(st.session_state.original_video_path, new_script_final)
        st.video(new_video_path)
        
        if 'new_video_path' not in st.session_state:
            st.session_state.new_video_path = new_video_path
        new_audio_path = extract_audio(st.session_state.new_video_path)       
        transcript_response = transcribe_audio(new_audio_path)
        ref_text = ''.join([x['text'] for x in transcript_response])
        if 'ref_text' not in st.session_state:
            st.session_state.ref_text = ref_text
        transcript = ['[' + x['start'] + ' - ' + x['end'] +']'+ ' :|: ' +  x['text'] for x in transcript_response]
        transcribed_text = '\n'.join(transcript)
        if 'new_transcript' not in st.session_state:
            st.session_state.new_transcript = transcribed_text

if not st.session_state.bloopers:
    with cols[2]:
        st.subheader("Edit Transcript")

        new_new_script = st.text_area("Transcript",st.session_state.new_transcript if 'new_transcript' in st.session_state else '', height=300)
        process = st.button("Process")

        to_be_synced_time_stamps = []
        if process:
            if new_new_script:
                for old_line, new_line in zip(st.session_state.new_transcript.split('\n'), new_new_script.split('\n')):
                    timestamp_list = new_line.split(':|:')
                    timestamp = timestamp_list[0]
                    text = timestamp_list[1]
                    start = timestamp.split('-')[0].replace('[', '').strip()
                    end = timestamp.split('-')[1].replace(']', '').strip()

                    if old_line != new_line:
                        to_be_synced_time_stamps.append({'start': start, 'end': end, 'text': text, 'sync': True})
                    else:
                        to_be_synced_time_stamps.append({'start': start, 'end': end, 'text': text, 'sync': False})
                
                synced_video_path = modify_and_patch_video(st.session_state.new_video_path, 
                                                        st.session_state.audio_path, 
                                                        to_be_synced_time_stamps, 
                                                        st.session_state.ref_text)

                st.video(synced_video_path)
            





        

        

        # # You can do something with `script` here if the user makes changes or adds text
        # if script:
        #     st.write("Edited/Added Script:")
        #     st.write(script)
        #     submit = st.button("Submit")

        #     if submit:
        #         # Send the edited script to the API
        #         script_response = requests.post(
        #             'http://127.0.0.1:8000/process_script/',
        #             json={'original_script': transcript, 'new_script': script}
        #         )

        #         if script_response.status_code == 200:
        #             # Process the script response
        #             script_data = script_response.json()
        #             new_script = script_data['new_script']  # Fixed the typo from 'new_script' to 'new_script'
