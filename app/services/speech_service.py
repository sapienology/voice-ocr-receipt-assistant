
import os

import soundfile as sf
import torch
from transformers import pipeline


class SpeechService:

    def __init__(self):
        self.pipe = None

        if torch.cuda.is_available():
            self.device = 0
        else:
            self.device = -1

    def transcribe(self, audio_file):

        """
        Convert an audio file into text.
        """

        try:
            if self.pipe is None:
                print("Loading Whisper model...")
                pipe = pipeline(
                    "automatic-speech-recognition",
                    model=os.getenv("SPEECH_MODEL", "openai/whisper-tiny"),
                    device=self.device
                )
                self.pipe = pipe

            audio, sample_rate = sf.read(audio_file, dtype="float32")
            if getattr(audio, "ndim", 1) > 1:
                audio = audio.mean(axis=1)
            result = self.pipe(
                {"raw": audio, "sampling_rate": sample_rate},
                return_timestamps=True
            )
        except Exception as error:
            print(f"Speech model unavailable: {error}")
            return f"Audio received, but transcription failed: {error}"

        text = result["text"]

        print("Transcription:", text)

        return text
