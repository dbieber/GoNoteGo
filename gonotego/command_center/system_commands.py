from datetime import datetime
import os
import platform
import subprocess
import sys

from gonotego.common import internet
from gonotego.common import status
from gonotego.command_center import note_commands
from gonotego.command_center import registry
from gonotego.settings import settings

register_command = registry.register_command

Status = status.Status


SAY_COMMAND = 'say' if platform.system() == 'Darwin' else 'espeak'


@register_command('whoami')
@register_command('who am i')
def whoami():
  note_taking_system = settings.get('NOTE_TAKING_SYSTEM')
  if note_taking_system == 'email':
    user = settings.get('EMAIL')
  elif note_taking_system == 'ideaflow':
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
  shell(f'date "+%A, %B%e %l:%M%p" | {SAY_COMMAND} &')


@register_command('at {}:{}', requirements=('scheduler',))
def schedule(at, what, scheduler):
  scheduler.schedule(at, what)


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
  cmd = f'cat tmp-say | {SAY_COMMAND} &'
  shell(cmd)


@register_command('silence')
@register_command('silencio')
def silence():
  shell(f'pkill {SAY_COMMAND}')


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
  hostname = hostname_output.split(' ')[0]
  say(hostname)
  note_commands.add_note(hostname)


@register_command('i')
@register_command('internet')
def check_internet():
  say('yes' if internet.is_internet_available() else 'no')


@register_command('wifi {} {}')
@register_command('wpa {} {}')
def add_wpa_wifi(ssid, psk):
  if '"' in ssid or '"' in psk:
    say('WiFi not set.')
    return
  network_string = f"""
network={{
        ssid="{ssid}"
        psk="{psk}"
        key_mgmt=WPA-PSK
}}
"""
  filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
  shell(f"echo '{network_string}' | sudo tee -a {filepath}")
  reconfigure_wifi()


@register_command('wifi {}')
def add_wifi_no_psk(ssid):
  if '"' in ssid:
    say('WiFi not set.')
    return
  network_string = f"""
network={{
        ssid="{ssid}"
        key_mgmt=NONE
}}
"""
  filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
  shell(f"echo '{network_string}' | sudo tee -a {filepath}")
  reconfigure_wifi()


@register_command('reconnect')
@register_command('wifi refresh')
@register_command('wifi reconfigure')
def reconfigure_wifi():
  shell('wpa_cli -i wlan0 reconfigure')
