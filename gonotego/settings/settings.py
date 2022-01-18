"""To modify settings, edit secure_settings.py or run ":set KEY VALUE" on Go Note Go.

Settings set on Go Note Go take precedence.
Run ":clear all" to clear settings set on Go Note Go, reverting back to those set
in secure_settings.py.
Run ":clear KEY" to clear an individual setting on Go Note Go, reverting it back
to it's value from secure_settings.py.
"""
import ast
from gonotego.settings import secure_settings
from gonotego.common import interprocess

SETTINGS_KEY = 'GoNoteGo:settings'


def get_redis_key(key):
  return f'{SETTINGS_KEY}:{key}'


def get(key):
  r = interprocess.get_redis_client()
  value_bytes = r.get(get_redis_key(key))
  if value_bytes is None:
    # If the setting isn't set in redis, fall back to the value from secure_settings.
    return getattr(secure_settings, key)
  value_repr = value_bytes.decode('utf-8')
  value = ast.literal_eval(value_repr)
  return value


def set(key, value):
  r = interprocess.get_redis_client()
  value_repr = repr(value)
  value_bytes = value_repr.encode('utf-8')
  r.set(get_redis_key(key), value_bytes)


def clear(key):
  r = interprocess.get_redis_client()
  r.delete(get_redis_key(key))


def clear_all():
  r = interprocess.get_redis_client()
  for key in r.keys(get_redis_key('*')):
    r.delete(key)
