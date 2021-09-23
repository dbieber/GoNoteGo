import ast
import enum
import json

from gonotego.common import interprocess


STATUS_KEY = 'GoNoteGo:status'


class Status(enum.Enum):

  def _generate_next_value_(name, start, count, last_values):
    return name

  AUDIO_READY = enum.auto()
  AUDIO_RECORDING = enum.auto()
  TEXT_READY = enum.auto()
  TEXT_LAST_KEYPRESS = enum.auto()
  TRANSCRIPTION_READY = enum.auto()
  TRANSCRIPTION_ACTIVE = enum.auto()
  UPLOADER_READY = enum.auto()
  UPLOADER_ACTIVE = enum.auto()
  INTERNET_AVAILABLE = enum.auto()


def get_redis_key(key):
  return f'{STATUS_KEY}:{key.name}'


def get(key):
  r = interprocess.get_redis_client()
  value_bytes = r.get(get_redis_key(key))
  value_str = value_bytes.decode('utf-8')
  value = ast.literal_eval(value_str)
  return value


def set(key, value):
  r = interprocess.get_redis_client()
  value_str = str(value)
  value_bytes = value_str.encode('utf-8')
  r.set(get_redis_key(key), value_bytes)
