import streamlit as st
import requests

st.title('Script Cut')

# Create two columns
cols = st.columns(2)

# Initialize a variable to hold the transcribed text
transcribed_text = ""

if 'original_script' not in st.session_state:
    st.session_state.original_script = []

if 'new_script' not in st.session_state:
    st.session_state.new_script = []

# Left column for video upload
with cols[0]:
    uploaded_video = st.file_uploader("Upload Video")
    if uploaded_video is not None:
        st.video(uploaded_video)
        
        # Send video to the API
        transcript_response = requests.post(
            'http://127.0.0.1:8000/upload_mp4/',
            files={'file': uploaded_video}
        )

        if transcript_response.status_code == 200:
            # Process the transcript response
            transcript_data = transcript_response.json()
            transcript = transcript_data['transcription']  # Fixed the typo from 'transciption' to 'transcription'

            # Extract text and timestamps from the transcript
            transcribed_text = ' '.join([x['text'] for x in transcript])
            st.session_state.original_script = transcribed_text.split(' ')

            time_stamps = [(x['start'], x['end']) for x in transcript]

        else:
            st.error(f"Failed to process transcript. Error code: {transcript_response.status_code}")

# Right column for transcript display and editing
with cols[1]:
    # Use the text area to show the transcript and allow user editing
    script = st.text_area("Transcript", transcribed_text, height=300, placeholder="Script")
    submit = st.button("Submit")
    new_script_final = []
    if submit:
        if script:
            new_script = script.split(' ')
            for i in range(len(st.session_state.original_script)):
                if st.session_state.original_script[i] == new_script[i]:
                    new_script_final.append(st.session_state.original_script[i])
                else:
                    if st.session_state.original_script[i] in new_script:
                        new_script_final.append(st.session_state.original_script[i])
                    else:
                        new_script_final.append(new_script[i])

    

    

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
