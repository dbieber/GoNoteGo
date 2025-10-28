"""Profile management for Go Note Go settings.

Profiles allow switching between different configurations.
Each profile stores a complete snapshot of all settings plus metadata (name, shortcut).
"""
import json
from gonotego.settings import settings
from gonotego.settings import secure_settings
from gonotego.common import interprocess

PROFILES_KEY = 'GoNoteGo:profiles'
PROFILE_SHORTCUTS_KEY = 'GoNoteGo:profile_shortcuts'
CURRENT_PROFILE_KEY = 'GoNoteGo:current_profile'


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


def save_profile(profile_name, shortcut=None):
  """Save current settings to a named profile.

  Args:
    profile_name: Name of the profile
    shortcut: Optional numeric shortcut (e.g., '1', '2', '3')
  """
  r = interprocess.get_redis_client()
  current_settings = get_all_settings()

  # Store profile data
  profile_data = {
    'name': profile_name,
    'settings': current_settings,
  }
  if shortcut is not None:
    profile_data['shortcut'] = shortcut

  profile_json = json.dumps(profile_data)
  r.set(get_redis_key(profile_name), profile_json)

  # Update shortcuts mapping if shortcut is provided
  if shortcut is not None:
    shortcuts = get_shortcuts_mapping()
    shortcuts[shortcut] = profile_name
    r.set(PROFILE_SHORTCUTS_KEY, json.dumps(shortcuts))

  return current_settings


def load_profile(profile_name):
  """Load settings from a named profile.

  1. Backs up current settings to 'backup' profile
  2. Loads all settings from the specified profile
  3. Sets current profile marker
  """
  r = interprocess.get_redis_client()

  # First, backup current settings (without shortcut)
  save_profile('backup', shortcut=None)

  # Load the requested profile
  profile_json = r.get(get_redis_key(profile_name))
  if profile_json is None:
    return None

  profile_data = json.loads(profile_json)
  profile_settings = profile_data.get('settings', profile_data)  # Backward compat

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


def get_shortcuts_mapping():
  """Get the mapping of shortcuts to profile names."""
  r = interprocess.get_redis_client()
  shortcuts_json = r.get(PROFILE_SHORTCUTS_KEY)
  if shortcuts_json is None:
    return {}
  return json.loads(shortcuts_json)


def get_profile_by_shortcut(shortcut):
  """Get profile name for a given shortcut."""
  shortcuts = get_shortcuts_mapping()
  return shortcuts.get(shortcut)


def list_profiles():
  """List all saved profile names with their shortcuts."""
  r = interprocess.get_redis_client()
  profile_keys = r.keys(get_redis_key('*'))

  profiles_info = []
  shortcuts = get_shortcuts_mapping()
  # Reverse mapping for lookup
  name_to_shortcut = {v: k for k, v in shortcuts.items()}

  for key in profile_keys:
    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
    # Extract profile name from key
    if key_str.startswith(f'{PROFILES_KEY}:'):
      profile_name = key_str[len(f'{PROFILES_KEY}:'):]
      shortcut = name_to_shortcut.get(profile_name)
      if shortcut:
        profiles_info.append(f"{profile_name} (:{shortcut})")
      else:
        profiles_info.append(profile_name)

  return sorted(profiles_info)


def delete_profile(profile_name):
  """Delete a saved profile and remove its shortcut if any."""
  r = interprocess.get_redis_client()

  # Remove from shortcuts mapping
  shortcuts = get_shortcuts_mapping()
  shortcut_to_remove = None
  for shortcut, name in shortcuts.items():
    if name == profile_name:
      shortcut_to_remove = shortcut
      break

  if shortcut_to_remove:
    del shortcuts[shortcut_to_remove]
    r.set(PROFILE_SHORTCUTS_KEY, json.dumps(shortcuts))

  # Delete the profile
  r.delete(get_redis_key(profile_name))
