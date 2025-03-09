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


@register_command('speak {}')
def speak(text):
  try:
    say_with_openai(text)
  except:
    print("Falling back on traditional say")
    say(text)


@register_command('say {}')
def say(text):
  dt = datetime.now().strftime('%k:%M:%S')
  with open('tmp-say', 'w') as tmp:
    print(f'[{dt}] Writing "{text}" to tmp-say')
    tmp.write(text)
  cmd = f'cat tmp-say | {SAY_COMMAND} &'
  shell(cmd)


@register_command('say_openai {}')
def say_with_openai(text):
  import openai
  client = openai.OpenAI(api_key=settings.get('OPENAI_API_KEY'))
  response = client.audio.speech.create(
      model="tts-1",
      voice="alloy",
      input=text
  )
  response.write_to_file('output.mp3')
  play_mp3('output.mp3')


def play_mp3(path):
  shell(f"cvlc {path} --play-and-exit")


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


@register_command('wifi scan')
def scan_wifi_networks():
  """Scan for available WiFi networks."""
  shell('sudo iwlist wlan0 scan | grep ESSID | cut -d":" -f2')


@register_command('reconnect')
@register_command('wifi refresh')
@register_command('wifi reconfigure')
def reconfigure_wifi():
  shell('wpa_cli -i wlan0 reconfigure')


@register_command('server')
@register_command('settings')
@register_command('configure')
def start_settings_server():
  shell('sudo systemctl stop uap0.service')
  shell('sudo systemctl stop dnsmasq.service')
  shell('sudo systemctl stop hostapd.service')

  shell('sudo systemctl start uap0.service')
  shell('sudo ip addr show uap0')
  shell('sudo ip addr add 192.168.4.1/24 dev uap0')
  shell('sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE')
  shell('sudo systemctl start dnsmasq.service')
  shell('sudo systemctl start hostapd.service')
  
  # Load existing WiFi networks from wpa_supplicant
  load_wifi_networks_from_wpa_supplicant()


def load_wifi_networks_from_wpa_supplicant():
  """Load WiFi networks from wpa_supplicant.conf into settings."""
  from gonotego.settings import settings
  import re
  
  try:
    # Read current wpa_supplicant.conf
    wpa_path = '/etc/wpa_supplicant/wpa_supplicant.conf'
    with open(wpa_path, 'r') as f:
      content = f.read()
    
    # Extract networks with regex
    network_blocks = re.findall(r'network=\{([^}]+)\}', content, re.DOTALL)
    wifi_networks = []
    
    for block in network_blocks:
      network = {}
      
      # Extract SSID
      ssid_match = re.search(r'ssid="([^"]+)"', block)
      if ssid_match:
        network['ssid'] = ssid_match.group(1)
      else:
        continue  # Skip networks without SSID
      
      # Extract key management
      key_mgmt_match = re.search(r'key_mgmt=([^\s]+)', block)
      network['key_mgmt'] = key_mgmt_match.group(1) if key_mgmt_match else 'NONE'
      
      # Extract PSK if present
      psk_match = re.search(r'psk="([^"]+)"', block)
      if psk_match:
        network['psk'] = psk_match.group(1)
      
      wifi_networks.append(network)
    
    # Save to settings
    if wifi_networks:
      settings.set('WIFI_NETWORKS', wifi_networks)
      print(f"Loaded {len(wifi_networks)} WiFi networks from wpa_supplicant.conf")
  
  except Exception as e:
    print(f"Error loading WiFi networks from wpa_supplicant.conf: {str(e)}")

@register_command('server stop')
def stop_settings_server():
  shell('sudo systemctl stop hostapd.service')
