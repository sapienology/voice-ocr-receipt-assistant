
import os

from gtts import gTTS


class VoiceService:

    def __init__(self):

        self.output_directory = "uploads"

        os.makedirs(
            self.output_directory,
            exist_ok=True
        )

    def text_to_speech(self, text):

        """
        Convert text into an MP3 audio file.
        """

        output_file = os.path.join(
            self.output_directory,
            "answer.mp3"
        )

        print("Generating speech...")

        tts = gTTS(
            text=text,
            lang="en"
        )

        tts.save(output_file)

        print(
            "Audio saved to:",
            output_file
        )

        return output_file
