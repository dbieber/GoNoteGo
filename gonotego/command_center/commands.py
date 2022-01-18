from datetime import datetime
import os
import random
import subprocess
import sys

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.common import status
from gonotego.command_center import registry
from gonotego.settings import settings
from gonotego.settings import secure_settings

register_command = registry.register_command

Status = status.Status


@register_command('alarm')
def alarm():
  query = random.choice([
      'tell her about it YouTube',
      'piano man YouTube',
      'rhapsody in blue YouTube',
  ])
  feel_lucky(query)


@register_command('lucky {}')
def feel_lucky(query):
  query = query.replace(' ', '+')
  cmd = f'chromium-browser "http://www.google.com/search?q={query}&btnI"'
  shell(cmd)


@register_command('t')
@register_command('time')
def time():
  shell('date "+%A, %B%e %l:%M%p" | espeak &')


@register_command('status')
@register_command('ok')
def status_command():
  say('ok')


@register_command('say {}')
def say(text):
  dt = datetime.now().strftime('%k:%M:%S')
  with open('tmp-say', 'w') as tmp:
    print(f'[{dt}] Writing "{text}" to tmp-say')
    tmp.write(text)
  cmd = 'cat tmp-say | espeak &'
  shell(cmd)


@register_command('shell {}')
def shell(cmd):
  dt = datetime.now().strftime('%k:%M:%S')
  print(f"[{dt}] Executing command: '{cmd}'")
  os.system(cmd)


@register_command('at {}:{}', requirements=('scheduler',))
def schedule(at, what, scheduler):
  scheduler.schedule(at, what)


@register_command('flush')
def flush():
  sys.stdout.flush()
  sys.stderr.flush()


@register_command('update')
def update():
  shell('git pull')


@register_command('restart')
def restart():
  shell('./env/bin/supervisorctl -u go -p notego restart all')


@register_command('reboot')
def reboot():
  shell('sudo reboot')


@register_command('leds {}')
def set_leds(value):
  if value in ('off', 'on', 'low'):
    status.set(Status.LEDS_SETTING, value)


@register_command('env')
def env():
  shell('env | sort')


@register_command('i')
@register_command('internet')
def check_internet():
  say('yes' if internet.is_internet_available() else 'no')


@register_command('r')
@register_command('read')
def read_latest():
  note_events_queue = interprocess.get_note_events_queue()
  note_event_bytes = note_events_queue.latest()
  note_event = events.NoteEvent.from_bytes(note_event_bytes)
  say(note_event.text)


@register_command('v {}')
@register_command('volume {}')
def set_volume(value):
  if value in ('off', 'on'):
    status.set(Status.VOLUME_SETTING, value)


@register_command('ip')
def ip_address():
  hostname_output = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
  say(hostname_output)


# Settings commands. Commands for setting settings.
SETTING_NAME_MAPPINGS = {
    'uploader': 'NOTE_TAKING_SYSTEM',
}
SETTINGS_NAMES = [s.lower() for s in dir(secure_settings) if not s.startswith('_')]


@register_command('set {} {}')
def set(key, value):
  if key.lower() in SETTING_NAME_MAPPINGS:
    key = SETTING_NAME_MAPPINGS[key.lower()]
  if key.lower() in SETTINGS_NAMES:
    settings.set(key, value)
  if key.lower() in ('v', 'volume'):
    set_volume(value)
  if key.lower() in ('leds'):
    set_leds(value)


@register_command('get {}')
def get_setting(key):
  say(key)
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
def clear_all_settings(key):
  if key.lower() in SETTING_NAME_MAPPINGS:
    key = SETTING_NAME_MAPPINGS[key.lower()]
  if key.lower() in SETTINGS_NAMES:
    settings.clear_all()
    say('Cleared.')
