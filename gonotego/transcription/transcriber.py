import io

import fire

from google.cloud import speech


class Transcriber:

  def __init__(self):
    self.client = speech.SpeechClient()
    self.config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US',
    )

  def transcribe(self, filepath):
    with io.open(filepath, 'rb') as audio_file:
      content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    response = self.client.recognize(config=self.config, audio=audio)

    return ''.join(
        result.alternatives[0].transcript + '\n'
        for result in response.results)



if __name__ == '__main__':
  fire.Fire()
