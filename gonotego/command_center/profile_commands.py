# Profile commands for switching between Go Note Go configurations.

from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.settings import profiles

register_command = registry.register_command
say = system_commands.say


# Predefined profile shortcuts
PROFILE_SHORTCUTS = {
    '1': 'roam',
    '2': 'work',
    '3': 'assistant',
    '4': 'guest',
}


@register_command('{}')
def load_profile_shortcut(shortcut):
  """Load a profile using numeric shortcut (e.g., :1 for roam)."""
  if shortcut not in PROFILE_SHORTCUTS:
    return  # Not a profile shortcut, let other commands handle it

  profile_name = PROFILE_SHORTCUTS[shortcut]
  result = profiles.load_profile(profile_name)

  if result is None:
    say(f'Profile {profile_name} not found. Creating from current settings.')
    profiles.save_profile(profile_name)
    say(f'Saved current settings as {profile_name}.')
  else:
    say(f'Loaded profile: {profile_name}')


@register_command('profile save {}')
def save_profile(profile_name):
  """Save current settings as a named profile."""
  profiles.save_profile(profile_name)
  say(f'Saved profile: {profile_name}')


@register_command('profile load {}')
def load_profile(profile_name):
  """Load a named profile."""
  result = profiles.load_profile(profile_name)
  if result is None:
    say(f'Profile not found: {profile_name}')
  else:
    say(f'Loaded profile: {profile_name}')


@register_command('profile list')
def list_profiles():
  """List all saved profiles."""
  profile_names = profiles.list_profiles()
  if not profile_names:
    say('No profiles saved.')
  else:
    say(f'Profiles: {", ".join(profile_names)}')


@register_command('profile current')
def current_profile():
  """Show the currently active profile."""
  current = profiles.get_current_profile()
  if current is None:
    say('No profile currently active.')
  else:
    say(f'Current profile: {current}')


@register_command('profile delete {}')
def delete_profile(profile_name):
  """Delete a saved profile."""
  profiles.delete_profile(profile_name)
  say(f'Deleted profile: {profile_name}')


@register_command('profile init')
def init_default_profiles():
  """Initialize default profiles (roam, work, assistant, guest) from current settings."""
  current_settings = profiles.get_all_settings()

  for shortcut, profile_name in PROFILE_SHORTCUTS.items():
    profiles.save_profile(profile_name)

  say('Initialized default profiles: roam, work, assistant, guest')
