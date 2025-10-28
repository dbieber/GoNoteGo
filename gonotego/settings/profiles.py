"""Profile management for Go Note Go settings.

Profiles allow switching between different configurations (roam, work, assistant, guest).
Each profile stores a complete snapshot of all settings.
"""
import json
from gonotego.settings import settings
from gonotego.settings import secure_settings
from gonotego.common import interprocess

PROFILES_KEY = 'GoNoteGo:profiles'
CURRENT_PROFILE_KEY = 'GoNoteGo:current_profile'
BACKUP_PROFILE_KEY = 'GoNoteGo:backup_profile'


def get_redis_key(profile_name):
  """Get Redis key for a specific profile."""
  return f'{PROFILES_KEY}:{profile_name}'


def get_all_settings():
  """Get all current settings as a dict."""
  settings_dict = {}
  # Get all setting names from secure_settings
  setting_names = [s for s in dir(secure_settings) if not s.startswith('_')]
  for key in setting_names:
    settings_dict[key] = settings.get(key)
  return settings_dict


def save_profile(profile_name):
  """Save current settings to a named profile."""
  r = interprocess.get_redis_client()
  current_settings = get_all_settings()
  settings_json = json.dumps(current_settings)
  r.set(get_redis_key(profile_name), settings_json)
  return current_settings


def load_profile(profile_name):
  """Load settings from a named profile.

  1. Backs up current settings to 'backup' profile
  2. Loads all settings from the specified profile
  3. Sets current profile marker
  """
  r = interprocess.get_redis_client()

  # First, backup current settings
  save_profile('backup')

  # Load the requested profile
  profile_json = r.get(get_redis_key(profile_name))
  if profile_json is None:
    return None

  profile_settings = json.loads(profile_json)

  # Clear all current settings and load profile settings
  settings.clear_all()
  for key, value in profile_settings.items():
    settings.set(key, value)

  # Mark this as the current profile
  r.set(CURRENT_PROFILE_KEY, profile_name)

  return profile_settings


def get_current_profile():
  """Get the name of the currently active profile."""
  r = interprocess.get_redis_client()
  profile_bytes = r.get(CURRENT_PROFILE_KEY)
  if profile_bytes is None:
    return None
  return profile_bytes.decode('utf-8')


def list_profiles():
  """List all saved profile names."""
  r = interprocess.get_redis_client()
  profile_keys = r.keys(get_redis_key('*'))
  profile_names = []
  for key in profile_keys:
    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
    # Extract profile name from key
    if key_str.startswith(f'{PROFILES_KEY}:'):
      profile_name = key_str[len(f'{PROFILES_KEY}:'):]
      profile_names.append(profile_name)
  return sorted(profile_names)


def delete_profile(profile_name):
  """Delete a saved profile."""
  r = interprocess.get_redis_client()
  r.delete(get_redis_key(profile_name))
