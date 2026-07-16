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
  # Seconds to add to the raw system-clock timestamp to get the alleged time.
  # Set via ':xtime' when the system clock is known to be wrong (e.g. no
  # internet while traveling). Notes carry both the raw timestamp and the
  # offset, so either time can be recovered later.
  offset: float = 0.0

  @property
  def effective_timestamp(self):
    """The timestamp with the alleged-time offset applied."""
    if self.timestamp is None:
      return None
    return self.timestamp + (self.offset or 0.0)

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
