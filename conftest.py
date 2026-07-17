"""Shared pytest fixtures for Go Note Go.

Tests run on machines without a secure_settings.py (it's gitignored) and
without a Redis server. This conftest stubs in the settings template as
secure_settings when the real file is missing, and provides a FakeRedis
fixture that patches gonotego.common.interprocess.get_redis_client.
"""
import pathlib
import sys
import types

import pytest


def _install_secure_settings_stub():
  try:
    import gonotego.settings.secure_settings  # noqa: F401
    return
  except ImportError:
    pass
  template_path = (
      pathlib.Path(__file__).parent / 'gonotego' / 'settings' / 'secure_settings_template.py')
  module = types.ModuleType('gonotego.settings.secure_settings')
  exec(template_path.read_text(), module.__dict__)
  sys.modules['gonotego.settings.secure_settings'] = module
  import gonotego.settings
  gonotego.settings.secure_settings = module


_install_secure_settings_stub()


class FakeRedis:
  """A tiny in-memory stand-in for the parts of redis.Redis Go Note Go uses."""

  def __init__(self):
    self.data = {}
    self.sets = {}

  def get(self, key):
    return self.data.get(key)

  def set(self, key, value):
    if isinstance(value, str):
      value = value.encode('utf-8')
    self.data[key] = value

  def delete(self, key):
    self.data.pop(key, None)
    self.sets.pop(key, None)

  def keys(self, pattern='*'):
    import fnmatch
    all_keys = list(self.data.keys()) + list(self.sets.keys())
    return [key for key in all_keys
            if fnmatch.fnmatch(key.decode('utf-8') if isinstance(key, bytes) else key,
                               pattern)]

  def smembers(self, key):
    return set(self.sets.get(key, set()))

  def sadd(self, key, value):
    if isinstance(value, str):
      value = value.encode('utf-8')
    self.sets.setdefault(key, set()).add(value)

  def srem(self, key, value):
    if isinstance(value, str):
      value = value.encode('utf-8')
    self.sets.get(key, set()).discard(value)


@pytest.fixture
def fake_redis(monkeypatch):
  from gonotego.common import interprocess
  r = FakeRedis()
  monkeypatch.setattr(interprocess, 'get_redis_client', lambda: r)
  return r
