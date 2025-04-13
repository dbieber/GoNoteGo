"""To modify settings, edit secure_settings.py or run ":set KEY VALUE" on Go Note Go.

Settings set on Go Note Go take precedence.
Run ":clear all" to clear settings set on Go Note Go, reverting back to those set
in secure_settings.py.
Run ":clear KEY" to clear an individual setting on Go Note Go, reverting it back
to its value from secure_settings.py.
"""
import ast
from gonotego.settings import secure_settings
from gonotego.common import interprocess

SETTINGS_KEY = 'GoNoteGo:settings'

# Mapping of display names to internal identifiers for note taking systems
NOTE_TAKING_SYSTEM_MAP = {
    # Display name to internal ID
    'roam research': 'roam',
    'remnote': 'remnote',
    'ideaflow': 'ideaflow',
    'mem': 'mem',
    'notion': 'notion',
    'twitter': 'twitter',
    'email': 'email',
    'dropbox': 'dropbox',
    
    # Already normalized values (pass-through)
    'roam': 'roam',
    
    # Handle capitalized versions 
    'Roam Research': 'roam',
    'RemNote': 'remnote',
    'IdeaFlow': 'ideaflow',
    'Mem': 'mem',
    'Notion': 'notion',
    'Twitter': 'twitter',
    'Email': 'email',
    'Dropbox': 'dropbox'
}

# Mapping of internal IDs to display names
DISPLAY_NAME_MAP = {
    'roam': 'Roam Research',
    'remnote': 'RemNote',
    'ideaflow': 'IdeaFlow',
    'mem': 'Mem',
    'notion': 'Notion',
    'twitter': 'Twitter',
    'email': 'Email',
    'dropbox': 'Dropbox'
}


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


def normalize_system_name(system_name):
  """Convert any format of system name to its normalized internal identifier.
  
  Args:
    system_name: String representation of a note taking system.
    
  Returns:
    The normalized internal identifier for the system.
  """
  if not system_name:
    return system_name
    
  # Try direct lookup first
  if system_name in NOTE_TAKING_SYSTEM_MAP:
    return NOTE_TAKING_SYSTEM_MAP[system_name]
  
  # Try lowercase version
  lowercase_name = system_name.lower()
  if lowercase_name in NOTE_TAKING_SYSTEM_MAP:
    return NOTE_TAKING_SYSTEM_MAP[lowercase_name]
  
  # If not found, return original (for backward compatibility)
  return system_name


def get_display_name(system_name):
  """Convert internal system identifier to its display name.
  
  Args:
    system_name: Internal identifier of a note taking system.
    
  Returns:
    The user-friendly display name for the system.
  """
  normalized = normalize_system_name(system_name)
  return DISPLAY_NAME_MAP.get(normalized, system_name)
