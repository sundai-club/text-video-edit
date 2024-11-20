# services/transcription_service.py
from typing import List
import os
from openai import OpenAI
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)


class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        
    def transcribe_audio(self, audio_file):
        try:
            with open(audio_file, "rb") as audio:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="verbose_json",
                    temperature=0,
                    timestamp_granularities=["word"],
                    prompt="Umm, let me think like, uh, uh, hmm... Okay, here's what I, I'm, like, thinking."
                )
            return self.process_transcription(response)
        except Exception as e:
            logging.error(f"Error during transcription: {e}")
            return []
            

    def format_timestamp(self, seconds):
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


    def process_transcription(self, result):
        timestamp_word_tuples = []
        for word in result.words:
            start_time = self.format_timestamp(word['start'])
            end_time = self.format_timestamp(word['end'])
            formatted_word = f" {word['word']}"  # Add a space before each word
            if word['word'] in [',', '.', '!', '?']:  # Remove space before punctuation
                formatted_word = word['word']
            timestamp_word_tuples.append({"start": start_time, "end": end_time, "text": formatted_word})

        return timestamp_word_tuples
