# app.py
import streamlit as st
from src.word_timestamp import transcribe_audio
from utils import (
    save_uploaded_video, 
    extract_audio, 
    extract_video_segments, 
    modify_and_patch_video,
    cleanup_old_files
)
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    initial_state = {
        'original_script': [],
        'new_script': [],
        'bloopers': False,
        'audio_path': None,
        'original_video_path': None,
        'new_video_path': None,
        'ref_text': None,
        'new_transcript': None,
        'last_processed_time': None
    }
    
    for key, value in initial_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_video(uploaded_file):
    """Validate uploaded video file"""
    if uploaded_file is None:
        return False
        
    # Check file size (e.g., 500MB limit)
    MAX_SIZE = 500 * 1024 * 1024  # 500MB in bytes
    if uploaded_file.size > MAX_SIZE:
        st.error("File size too large. Please upload a video smaller than 500MB.")
        return False
    
    # Check file type
    allowed_types = ['video/mp4', 'video/mpeg', 'video/avi']
    if uploaded_file.type not in allowed_types:
        st.error("Please upload a valid video file (MP4, MPEG, or AVI).")
        return False
        
    return True

def parse_timestamp(timestamp_str):
    """Safely parse timestamp string to seconds"""
    try:
        # Remove brackets and split into components
        clean_ts = timestamp_str.replace('[', '').replace(']', '').strip()
        # Parse timestamp in format "HH:MM:SS.mmm"
        time_obj = datetime.strptime(clean_ts, '%H:%M:%S.%f')
        return (time_obj.hour * 3600 + 
                time_obj.minute * 60 + 
                time_obj.second + 
                time_obj.microsecond / 1000000)
    except ValueError as e:
        logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
        st.error(f"Invalid timestamp format: {timestamp_str}")
        return None

def process_transcript(script):
    """Process transcript and extract timestamps"""
    new_script_final = []
    try:
        for line in script.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split(':|:')
            if len(parts) != 2:
                st.error(f"Invalid line format: {line}")
                continue
                
            timestamp, text = parts
            start_end = timestamp.split('-')
            if len(start_end) != 2:
                st.error(f"Invalid timestamp format: {timestamp}")
                continue
                
            start = parse_timestamp(start_end[0])
            end = parse_timestamp(start_end[1])
            
            if start is None or end is None:
                continue
                
            if end <= start:
                st.error(f"End time must be after start time: {timestamp}")
                continue
                
            new_script_final.append({
                'start': start_end[0].strip(),
                'end': start_end[1].strip(),
                'text': text.strip()
            })
    except Exception as e:
        logger.error(f"Error processing transcript: {e}")
        st.error("Error processing transcript. Please check the format.")
        return None
        
    return new_script_final

def main():
    st.set_page_config(
        page_title="ScriptCut",
        page_icon="📝",
        layout="wide",
    )
    
    init_session_state()
    
    # Cleanup old files every hour
    current_time = datetime.now()
    if (st.session_state.last_processed_time is None or 
        (current_time - st.session_state.last_processed_time).total_seconds() > 3600):
        cleanup_old_files()
        st.session_state.last_processed_time = current_time

    st.title("ScriptCut")

    with st.sidebar:
        st.image('sundai_logo.jpg', width=100)
        st.title("ScriptCut")
        st.write("Your personal script editor")
        st.session_state.bloopers = st.checkbox("Bloopers")

    cols = st.columns(2 if st.session_state.bloopers else 3)

    with cols[0]:
        st.subheader("Upload Video")
        uploaded_video = st.file_uploader("Upload Video")
        
        if uploaded_video is not None and validate_video(uploaded_video):
            try:
                st.video(uploaded_video)
                video_path = save_uploaded_video(uploaded_video)
                audio_path = extract_audio(video_path)
                
                st.session_state.audio_path = audio_path
                transcript_response = transcribe_audio(audio_path)
                
                if transcript_response:
                    ref_text = ''.join([x['text'] for x in transcript_response])
                    transcript = [
                        f"[{x['start']} - {x['end']}] :|: {x['text']}" 
                        for x in transcript_response
                    ]
                    st.session_state.original_script = '\n'.join(transcript)
                    st.session_state.original_video_path = video_path
                else:
                    st.error("Failed to transcribe audio")
            
            except Exception as e:
                logger.error(f"Error processing video: {e}")
                st.error("Error processing video. Please try again.")

    with cols[1]:
        st.subheader("Trim Transcript")
        script = st.text_area(
            "Transcript", 
            st.session_state.original_script, 
            height=300, 
            placeholder="Script"
        )
        
        if st.button("Submit"):
            if script:
                new_script_final = process_transcript(script)
                
                if new_script_final:
                    try:
                        new_video_path = extract_video_segments(
                            st.session_state.original_video_path, 
                            new_script_final
                        )
                        
                        if new_video_path and os.path.exists(new_video_path):
                            st.video(new_video_path)
                            st.session_state.new_video_path = new_video_path
                            st.session_state.new_script = script
                            
                            new_audio_path = extract_audio(new_video_path)
                            transcript_response = transcribe_audio(new_audio_path)
                            
                            if transcript_response:
                                st.session_state.ref_text = ''.join(
                                    [x['text'] for x in transcript_response]
                                )
                                transcript = [
                                    f"[{x['start']} - {x['end']}] :|: {x['text']}" 
                                    for x in transcript_response
                                ]
                                st.session_state.new_transcript = '\n'.join(transcript)
                            else:
                                st.error("Failed to transcribe new audio")
                        else:
                            st.error("Failed to create new video")
                            
                    except Exception as e:
                        logger.error(f"Error processing transcript: {e}")
                        st.error("Error processing transcript. Please try again.")

    if not st.session_state.bloopers and len(cols) > 2:
        with cols[2]:
            st.subheader("Edit Transcript")
            new_transcript = st.text_area(
                "Transcript",
                st.session_state.new_transcript if 'new_transcript' in st.session_state else '',
                height=300
            )
            
            if st.button("Process"):
                if new_transcript:
                    try:
                        to_be_synced_time_stamps = []
                        old_lines = st.session_state.new_transcript.split('\n')
                        new_lines = new_transcript.split('\n')
                        
                        if len(old_lines) != len(new_lines):
                            st.error("Number of lines must match original transcript")
                            return
                            
                        for old_line, new_line in zip(old_lines, new_lines):
                            timestamp_parts = new_line.split(':|:')
                            if len(timestamp_parts) != 2:
                                st.error(f"Invalid line format: {new_line}")
                                continue
                                
                            timestamp, text = timestamp_parts
                            start_end = timestamp.split('-')
                            if len(start_end) != 2:
                                st.error(f"Invalid timestamp format: {timestamp}")
                                continue
                                
                            to_be_synced_time_stamps.append({
                                'start': start_end[0].replace('[', '').strip(),
                                'end': start_end[1].replace(']', '').strip(),
                                'text': text.strip(),
                                'sync': old_line != new_line
                            })
                        
                        synced_video_path = modify_and_patch_video(
                            st.session_state.new_video_path,
                            st.session_state.audio_path,
                            to_be_synced_time_stamps,
                            st.session_state.ref_text
                        )
                        
                        if synced_video_path and os.path.exists(synced_video_path):
                            st.video(synced_video_path)
                        else:
                            st.error("Failed to create synced video")
                            
                    except Exception as e:
                        logger.error(f"Error processing edited transcript: {e}")
                        st.error("Error processing edited transcript. Please try again.")

if __name__ == "__main__":
    main()