# Profile commands for switching between Go Note Go configurations.

from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.settings import profiles

register_command = registry.register_command
say = system_commands.say


@register_command(r'p(\d)')
def load_profile_shortcut(shortcut):
  """Load a profile using numeric shortcut (e.g., :p1, :p2, :p3)."""
  # Check if this is a numeric shortcut
  if not shortcut.isdigit():
    return  # Not a profile shortcut

  profile_name = profiles.get_profile_by_shortcut(shortcut)
  if profile_name is None:
    say(f'Profile {shortcut} not found')
    return  # No profile mapped to this shortcut

  result = profiles.load_profile(profile_name)

  if result is None:
    say(f'Profile {profile_name} not found.')
  else:
    say(f'Loaded profile: {profile_name}')


@register_command('profile save {} {}')
def save_profile_with_shortcut(profile_name, shortcut):
  """Save current settings as a named profile with a shortcut."""
  profiles.save_profile(profile_name, shortcut=shortcut)
  say(f'Saved profile: {profile_name} with shortcut :{shortcut}')


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
  """List all saved profiles with their shortcuts."""
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
