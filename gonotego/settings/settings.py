"""To modify settings, edit secure_settings.py or run ":set KEY VALUE" on Go Note Go.

Settings set on Go Note Go take precedence.
Run ":clear all" to clear settings set on Go Note Go, reverting back to those set
in secure_settings.py.
Run ":clear KEY" to clear an individual setting on Go Note Go, reverting it back
to its value from secure_settings.py.

Profiles
--------
Settings support named profiles (":use profile work"), e.g. for switching
between upload targets or users sharing one device.

- The 'default' profile reads and writes the same Redis keys older versions
  used, so existing single-profile installs keep their settings with no
  migration.
- A named profile stores its values under its own namespace. Reading a key
  the profile doesn't set falls back to the default profile's value, then to
  secure_settings.py -- so a profile only needs to override what differs.
- Device-level settings (WiFi, hotkey, custom command paths, auto-hotspot)
  are shared across all profiles.
"""
import ast
import re

from gonotego.settings import secure_settings
from gonotego.common import interprocess

SETTINGS_KEY = 'GoNoteGo:settings'
PROFILES_KEY = 'GoNoteGo:profiles'
ACTIVE_PROFILE_KEY = 'GoNoteGo:active-profile'

DEFAULT_PROFILE = 'default'

# Settings that belong to the device rather than to a profile.
DEVICE_SETTINGS = {
    'WIFI_NETWORKS',
    'CUSTOM_COMMAND_PATHS',
    'HOTKEY',
    'AUTO_HOTSPOT',
}

PROFILE_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


def is_valid_profile_name(name):
  return bool(name) and bool(PROFILE_NAME_RE.match(name))


def get_active_profile():
  r = interprocess.get_redis_client()
  value_bytes = r.get(ACTIVE_PROFILE_KEY)
  if value_bytes is None:
    return DEFAULT_PROFILE
  return value_bytes.decode('utf-8')


def set_active_profile(name):
  """Switches to a profile, creating (registering) it if needed."""
  if not is_valid_profile_name(name):
    raise ValueError(f'Invalid profile name: {name!r}')
  r = interprocess.get_redis_client()
  if name != DEFAULT_PROFILE:
    r.sadd(PROFILES_KEY, name)
  r.set(ACTIVE_PROFILE_KEY, name)


def list_profiles():
  """All profile names, default first, the rest alphabetical."""
  r = interprocess.get_redis_client()
  names = sorted(value.decode('utf-8') for value in r.smembers(PROFILES_KEY))
  return [DEFAULT_PROFILE] + [name for name in names if name != DEFAULT_PROFILE]


def delete_profile(name):
  """Deletes a named profile and its settings. The default profile can't be deleted.

  Returns:
    True if the profile existed and was deleted.
  """
  if name == DEFAULT_PROFILE:
    return False
  r = interprocess.get_redis_client()
  if name not in list_profiles():
    return False
  for key in r.keys(f'{SETTINGS_KEY}:profiles:{name}:*'):
    r.delete(key)
  r.srem(PROFILES_KEY, name)
  if get_active_profile() == name:
    r.set(ACTIVE_PROFILE_KEY, DEFAULT_PROFILE)
  return True


def get_redis_key(key, profile=None):
  if profile is None:
    profile = get_active_profile()
  if profile == DEFAULT_PROFILE or key in DEVICE_SETTINGS:
    # The default profile uses the legacy key layout, so existing installs
    # need no migration.
    return f'{SETTINGS_KEY}:{key}'
  return f'{SETTINGS_KEY}:profiles:{profile}:{key}'


def get(key):
  r = interprocess.get_redis_client()
  profile = get_active_profile()
  value_bytes = r.get(get_redis_key(key, profile=profile))
  if value_bytes is None and profile != DEFAULT_PROFILE:
    # Fall back to the default profile's value for keys the active profile
    # doesn't override.
    value_bytes = r.get(get_redis_key(key, profile=DEFAULT_PROFILE))
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
  """Clears the active profile's settings (not other profiles')."""
  r = interprocess.get_redis_client()
  profile = get_active_profile()
  if profile == DEFAULT_PROFILE:
    profiles_prefix = f'{SETTINGS_KEY}:profiles:'
    for key in r.keys(f'{SETTINGS_KEY}:*'):
      key_str = key.decode('utf-8') if isinstance(key, bytes) else key
      if not key_str.startswith(profiles_prefix):
        r.delete(key)
  else:
    for key in r.keys(f'{SETTINGS_KEY}:profiles:{profile}:*'):
      r.delete(key)
