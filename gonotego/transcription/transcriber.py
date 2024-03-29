import io

import fire
import openai
from gonotego.settings import settings

openai.api_key = settings.get('OPENAI_API_KEY')


class Transcriber:

  def transcribe(self, filepath):
    with io.open(filepath, 'rb') as audio_file:
      response = openai.Audio.transcribe("whisper-1", audio_file)
      transcription = response['text']
      return transcription.strip()


if __name__ == '__main__':
  fire.Fire()
