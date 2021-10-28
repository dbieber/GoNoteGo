from datetime import datetime
import os
import random
import sys

from gonotego.common import status
from gonotego.command_center import registry

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
  query = query.replace(" ", "+")
  cmd = f'chromium-browser "http://www.google.com/search?q={query}&btnI"'
  shell(cmd)


@register_command('time')
def time():
  shell('date "+%A, %B%e %l:%M%p" | espeak &')


@register_command('status')
def status():
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


@register_command('leds {}')
def leds(value):
  if value in ('off', 'on', 'low'):
    status.set(Status.LEDS_SETTING, value)
