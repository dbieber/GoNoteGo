"""Tests for profile commands."""
from unittest import mock

from gonotego.command_center import profile_commands
from gonotego.settings import settings


def test_use_profile_creates_and_switches(fake_redis):
  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.use_profile('work')
  assert settings.get_active_profile() == 'work'
  assert 'created' in say.call_args[0][0]

  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.use_profile('default')
    profile_commands.use_profile('work')
  assert settings.get_active_profile() == 'work'
  assert 'created' not in say.call_args[0][0]


def test_use_profile_by_number(fake_redis):
  settings.set_active_profile('work')
  settings.set_active_profile('default')
  # Profiles: 1. default, 2. work
  with mock.patch.object(profile_commands, 'say'):
    profile_commands.use_profile('2')
  assert settings.get_active_profile() == 'work'

  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.use_profile('9')
  assert settings.get_active_profile() == 'work'
  assert 'No profile number' in say.call_args[0][0]


def test_use_profile_invalid_name(fake_redis):
  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.use_profile('bad name!')
  assert settings.get_active_profile() == 'default'
  assert 'Invalid' in say.call_args[0][0]


def test_list_profiles_marks_active(fake_redis):
  settings.set_active_profile('work')
  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.list_profiles()
  spoken = say.call_args[0][0]
  assert '1. default' in spoken
  assert '2. work (active)' in spoken


def test_delete_profile_command(fake_redis):
  settings.set_active_profile('work')
  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.delete_profile('work')
  assert settings.get_active_profile() == 'default'
  assert 'deleted' in say.call_args[0][0]

  with mock.patch.object(profile_commands, 'say') as say:
    profile_commands.delete_profile('default')
  assert 'cannot be deleted' in say.call_args[0][0]


def test_command_patterns_registered():
  from gonotego.command_center import registry
  patterns = {command.regex.pattern for command in registry.COMMANDS}
  assert '^use profile (.*)$' in patterns
  assert '^profiles$' in patterns
  assert '^profile$' in patterns
  assert '^profile delete (.*)$' in patterns
