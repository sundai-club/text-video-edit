import whisper
import moviepy.editor as mp
import os
from datetime import timedelta
import subprocess
import time

def convert_windows_path_to_wsl(windows_path):
    try:
        wsl_path = subprocess.check_output(['wslpath', '-u', windows_path]).decode('utf-8').strip()
        return wsl_path
    except subprocess.CalledProcessError:
        print("Error converting Windows path to WSL path.")
        return windows_path


def extract_audio(video_path, audio_path):
    try:
        wsl_video_path = convert_windows_path_to_wsl(video_path)
        wsl_audio_path = convert_windows_path_to_wsl(audio_path)

        video = mp.VideoFileClip(wsl_video_path)
        video.audio.write_audiofile(wsl_audio_path)
        video.close()
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


def transcribe_audio(audio_file):
    # Load the Whisper model
    model = whisper.load_model("base")

    # Start timing the transcription process
    start_time = time.time()

    # Load the audio file and transcribe
    result = model.transcribe(audio_file, word_timestamps=True)

    # Calculate transcription time
    elapsed_time = time.time() - start_time

    print(f"File: {audio_file}")
    print(f"Transcription: {result['text']}")
    print(f"Transcription took: {elapsed_time:.2f} seconds")

    return result, elapsed_time

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def save_word_timestamps(result, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for segment in result['segments']:
            for word in segment.get('words', []):
                f.write(f"{format_timestamp(word['start'])} - {format_timestamp(word['end'])}: {word['word']}\n")


def convert_to_timestamp_word_tuples(result):
    timestamp_word_tuples = []
    for segment in result['segments']:
        for word in segment.get('words', []):
            start_time = format_timestamp(word['start'])
            end_time = format_timestamp(word['end'])
            timestamp_word_tuples.append({f"{start_time} - {end_time}": word['word']})
    return timestamp_word_tuples


def main(video_path, output_file):
    audio_path = r"C:\Users\rushi\PycharmProjects\text-video-edit\Audio Files\temp_audio.wav"

    try:
        # Extract audio from video
        extract_audio(video_path, audio_path)

        # Convert audio_path to WSL format for transcription
        wsl_audio_path = convert_windows_path_to_wsl(audio_path)

        # Transcribe audio
        transcription_result, transcription_time = transcribe_audio(wsl_audio_path)

        # Save word timestamps
        save_word_timestamps(transcription_result, output_file)

        # Convert to timestamp-word tuples
        timestamp_word_tuples = convert_to_timestamp_word_tuples(transcription_result)

        print(f"Transcription complete. Output saved to {output_file}")
        print(f"Total transcription time: {transcription_time:.2f} seconds")
        print("\ntimestamp-word tuples:")
        for tuple in timestamp_word_tuples:
            print(tuple)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up temporary audio file
        wsl_audio_path = convert_windows_path_to_wsl(audio_path)
        if os.path.exists(wsl_audio_path):
            os.remove(wsl_audio_path)

    return timestamp_word_tuples


if __name__ == "__main__":
    video_path = r"C:\Users\rushi\Downloads\IMG_7684.MOV"
    output_file = "transcript_with_timestamps.txt"
    main(video_path, output_file)
