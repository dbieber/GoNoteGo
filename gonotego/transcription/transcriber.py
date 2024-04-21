import io

import fire
import openai
from gonotego.settings import settings


class Transcriber:

  def transcribe(self, filepath):
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
