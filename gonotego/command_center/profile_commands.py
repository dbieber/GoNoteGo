"""Profile commands. Switch between named settings profiles.

A profile is a named overlay over the default settings -- useful for
switching upload targets or sharing one Go Note Go between people.
Switch with ':use profile work' (created on first use) or with
cmd-shift-1/2/3/... (profiles numbered in ':profiles' order).
"""
from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.settings import settings

register_command = registry.register_command

say = system_commands.say


@register_command('profiles')
def list_profiles():
  profiles = settings.list_profiles()
  active = settings.get_active_profile()
  described = [
      f'{i + 1}. {name}' + (' (active)' if name == active else '')
      for i, name in enumerate(profiles)
  ]
  say('Profiles: ' + ', '.join(described))


@register_command('profile')
def current_profile():
  say(f'Profile {settings.get_active_profile()}.')


@register_command('profile delete {}')
def delete_profile(name):
  name = name.strip()
  if name == settings.DEFAULT_PROFILE:
    say('The default profile cannot be deleted.')
    return
  if settings.delete_profile(name):
    say(f'Profile {name} deleted. Profile {settings.get_active_profile()}.')
  else:
    say(f'No profile named {name}.')


@register_command('use profile {}')
@register_command('profile use {}')
def use_profile(name):
  name = name.strip()
  # Allow switching by number, matching the ':profiles' listing and the
  # cmd-shift-N keyboard shortcut.
  if name.isdigit():
    profiles = settings.list_profiles()
    index = int(name)
    if not 1 <= index <= len(profiles):
      say(f'No profile number {name}.')
      return
    name = profiles[index - 1]
  if not settings.is_valid_profile_name(name):
    say('Invalid profile name.')
    return
  created = name not in settings.list_profiles()
  settings.set_active_profile(name)
  if created:
    say(f'Profile {name} created and active.')
  else:
    say(f'Profile {name}.')
