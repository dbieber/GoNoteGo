from typing import Text

import dataclasses

AUDIO_DONE = 'done'


@dataclasses.dataclass
class AudioEvent:
  action: Text
  filepath: Text

  def __bytes__(self):
    return f'{self.action}:{self.filepath}'.encode('utf-8')

  @staticmethod
  def from_bytes(b):
    action, filepath = b.decode('utf-8').split(':', 1)
    return AudioEvent(action, filepath)


@dataclasses.dataclass
class TextEvent:
  text: Text

  def __bytes__(self):
    return self.text.encode('utf-8')

  def from_bytes(b):
    text = b.decode('utf-8')
    return TextEvent(text)
