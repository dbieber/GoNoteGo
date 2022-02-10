from datetime import datetime
import os
import subprocess
import sys

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import status
from gonotego.command_center import registry
from gonotego.settings import settings

register_command = registry.register_command

Status = status.Status


@register_command('whoami')
@register_command('who am i')
def whoami():
  note_taking_system = settings.get('NOTE_TAKING_SYSTEM')
  if note_taking_system == 'ideaflow':
    user = settings.get('IDEAFLOW_USER')
  elif note_taking_system == 'remnote':
    user = settings.get('REMNOTE_USER_ID')[:6]
  elif note_taking_system == 'roam':
    user = f'{settings.get("ROAM_GRAPH")} {settings.get("ROAM_USER")}'
  elif note_taking_system == 'mem':
    user = settings.get('MEM_API_KEY')[:6]
  elif note_taking_system == 'notion':
    user = settings.get('NOTION_DATABASE_ID')[:6]
  elif note_taking_system == 'twitter':
    user = settings.get('twitter.screen_name')
  say(f'uploader {note_taking_system} ; user {user}')


@register_command('t')
@register_command('time')
def time():
  shell('date "+%A, %B%e %l:%M%p" | espeak &')


@register_command('at {}:{}', requirements=('scheduler',))
def schedule(at, what, scheduler):
  scheduler.schedule(at, what)


@register_command('on {}:{}')
def schedule(on, what):
  ip = settings.get_machine_ip(on)
  password = settings.get_machine_password(on)
  command_event = events.CommandEvent(command_text=what)
  command_event_bytes = bytes(command_event)
  command = [
      'sshpass', '-p', password, 'ssh', ip,
      'redis-cli',
      'set', 'command_events_queue:latest', command_event_bytes,
      # 'rpush', 'command_events_queue', command_event_bytes]
  ]
  subprocess.check_output(command)


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


@register_command('env')
def env():
  shell('env | sort')


@register_command('ip')
def ip_address():
  hostname_output = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
  say(hostname_output)


@register_command('i')
@register_command('internet')
def check_internet():
  say('yes' if internet.is_internet_available() else 'no')
