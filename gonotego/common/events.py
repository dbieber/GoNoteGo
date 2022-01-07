from typing import Text, Tuple

import dataclasses
from datetime import datetime
import json

AUDIO_DONE = 'done'

SUBMIT = 'submit'
UNINDENT = 'unindent'
INDENT = 'indent'
CLEAR_EMPTY = 'clear_empty'
ENTER_EMPTY = 'enter_empty'
END_SESSION = 'end_session'


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
class CommandEvent:
  command_text: Text

  def __bytes__(self):
    return self.command_text.encode('utf-8')

  def from_bytes(b):
    command_text = b.decode('utf-8')
    return CommandEvent(command_text)


@dataclasses.dataclass
class NoteEvent:
  text: Text
  action: Text
  audio_filepath: Text
  timestamp: datetime

  def __bytes__(self):
    return json.dumps(dataclasses.asdict(self)).encode('utf-8')

  def from_bytes(b):
    d = json.loads(b.decode('utf-8'))
    return NoteEvent(**d)


@dataclasses.dataclass
class LEDEvent:
  color: Tuple[int]
  ids: Tuple[int]

  def __bytes__(self):
    return json.dumps(dataclasses.asdict(self)).encode('utf-8')

  def from_bytes(b):
    d = json.loads(b.decode('utf-8'))
    return LEDEvent(**d)
