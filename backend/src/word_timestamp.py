import os
from datetime import timedelta
import subprocess
import moviepy.editor as mp
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def convert_windows_path_to_wsl(windows_path):
    try:
        return subprocess.check_output(['wslpath', '-u', windows_path]).decode('utf-8').strip()
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
    try:
        with open(audio_file, "rb") as audio:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        return response
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise


def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def process_transcription(result, output_file):
    timestamp_word_tuples = []
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in result.words:
            start_time = format_timestamp(word.start)
            end_time = format_timestamp(word.end)
            formatted_word = f" {word.word}"  # Add a space before each word
            if word.word in [',', '.', '!', '?']:  # Remove space before punctuation
                formatted_word = word.word
            f.write(f"{start_time} - {end_time}: {formatted_word}\n")
            timestamp_word_tuples.append({f"{start_time} - {end_time}": formatted_word})

    return timestamp_word_tuples


def main(video_path, output_file):
    audio_path = os.path.join(os.path.dirname(video_path), "temp_audio.wav")

    try:
        extract_audio(video_path, audio_path)
        wsl_audio_path = convert_windows_path_to_wsl(audio_path)
        transcription_result = transcribe_audio(wsl_audio_path)
        timestamp_word_tuples = process_transcription(transcription_result, output_file)

        print(f"Transcription complete. Output saved to {output_file}")
        print("\nTimestamp-word tuples:")
        for tuple in timestamp_word_tuples:
            print(tuple)

        return timestamp_word_tuples

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


if __name__ == "__main__":
    video_path = r"C:\Users\rushi\Downloads\IMG_7684.MOV"
    output_file = "transcript_with_timestamps.txt"
    main(video_path, output_file)