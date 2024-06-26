# Settings commands. Commands for setting settings.

import subprocess

from dateutil import parser

from gonotego.common import status
from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.settings import settings
from gonotego.settings import secure_settings

register_command = registry.register_command

Status = status.Status

SETTING_NAME_MAPPINGS = {
    'uploader': 'NOTE_TAKING_SYSTEM',
}
SETTINGS_NAMES = [s.lower() for s in dir(secure_settings) if not s.startswith('_')]

say = system_commands.say


@register_command('set {} {}')
def set(key, value):
  if key.lower() in SETTING_NAME_MAPPINGS:
    key = SETTING_NAME_MAPPINGS[key.lower()]
  if key.lower() in SETTINGS_NAMES:
    settings.set(key, value)
  if key.lower() in ('v', 'volume'):
    set_volume(value)
  if key.lower() in ('t', 'time'):
    set_time(value)
  if key.lower() in ('tz', 'timezone'):
    set_timezone(value)


def set_time(value):
  try:
    t = parser.parse(value)
  except parser.ParserError:
    say('Time not set.')
    return
  time_string = (
      f'{t.year:04d}-{t.month:02d}-{t.day:02d} '
      f'{t.hour:02d}:{t.minute:02d}:{t.second:02d}'
  )
  command = f'date -s "{time_string}"'
  system_commands.shell(command)


def list_timezones():
  output = subprocess.check_output(['timedatectl', 'list-timezones'])
  timezones_str = output.decode('utf-8')
  timezones = timezones_str.strip().split('\n')
  return timezones


def set_timezone(value):
  timezone_mapping = {
      'ET': 'America/New_York',
      'EST': 'America/New_York',
      'EDT': 'America/New_York',
      'PT': 'America/Los_Angeles',
      'PST': 'America/Los_Angeles',
      'PDT': 'America/Los_Angeles',
  }
  if value in timezone_mapping:
    value = timezone_mapping[value]
  if value not in list_timezones():
    say('Timezone not set.')
    return
  command = f'sudo timedatectl set-timezone {value}'
  system_commands.shell(command)


@register_command('ntp on')
def enable_ntp():
  system_commands.shell('sudo timedatectl set-ntp true')


@register_command('ntp off')
def disable_ntp():
  system_commands.shell('sudo timedatectl set-ntp false')


@register_command('get status {}')
def get_status(key):
  if 'secret' in key.lower() or 'password' in key.lower():
    return
  status_key = getattr(status.Status, key)
  say(str(status.get(status_key)))


@register_command('get {}')
def get_setting(key):
  if 'secret' in key.lower() or 'password' in key.lower():
    return
  if key.lower() in SETTING_NAME_MAPPINGS:
    key = SETTING_NAME_MAPPINGS[key.lower()]
  if key.lower() in SETTINGS_NAMES:
    say(settings.get(key))


@register_command('clear {}')
def clear_setting(key):
  if key.lower() in SETTING_NAME_MAPPINGS:
    key = SETTING_NAME_MAPPINGS[key.lower()]
  if key.lower() in SETTINGS_NAMES:
    settings.clear(key)
    value = settings.get(key)
    say(f'New value: {value}')


@register_command('clear')
def clear_all_settings():
  settings.clear_all()
  say('Cleared.')


@register_command('v {}')
@register_command('volume {}')
def set_volume(value):
  if value in ('off', 'on'):
    status.set(Status.VOLUME_SETTING, value)
