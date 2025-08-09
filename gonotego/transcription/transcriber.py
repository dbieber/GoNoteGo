import io

import fire
import openai
from gonotego.settings import settings
from gonotego.command_center import llm_provider


class Transcriber:

  def transcribe(self, filepath):
    if not llm_provider.has_openai_key():
      print("No OpenAI API key available for transcription")
      return ""
      
    client = openai.OpenAI(api_key=settings.get('OPENAI_API_KEY'))
    with io.open(filepath, 'rb') as audio_file:
      response = client.audio.transcriptions.create(
          model="whisper-1",
          file=audio_file
      )
      transcription = response.text
      return transcription.strip()


if __name__ == '__main__':
  fire.Fire()
