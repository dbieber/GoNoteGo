# Settings commands. Commands for setting settings.

import json
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


@register_command('wifi add')
def add_wifi_network_from_settings(json_network_data=None):
  """Add a WiFi network from the settings UI.
  
  Accepts a JSON string containing 'ssid' and optionally 'psk'.
  """
  if not json_network_data:
    say('WiFi network not added: missing network data')
    return
  
  try:
    network_data = json.loads(json_network_data)
    ssid = network_data.get('ssid')
    psk = network_data.get('psk')
    
    if not ssid:
      say('WiFi network not added: missing SSID')
      return
      
    # Get current WiFi networks
    networks = settings.get('WIFI_NETWORKS') or []
    
    # Create new network entry
    new_network = {'ssid': ssid}
    
    # If password provided, it's a WPA network
    if psk:
      new_network['psk'] = psk
      new_network['key_mgmt'] = 'WPA-PSK'
      # Also update wpa_supplicant.conf
      system_commands.add_wpa_wifi(ssid, psk)
    else:
      new_network['key_mgmt'] = 'NONE'
      # Also update wpa_supplicant.conf
      system_commands.add_wifi_no_psk(ssid)
    
    # Add to settings (avoid duplicates by removing any networks with same SSID)
    networks = [net for net in networks if net.get('ssid') != ssid]
    networks.append(new_network)
    
    # Save updated networks list
    settings.set('WIFI_NETWORKS', networks)
    say(f'Added WiFi network {ssid}')
    
  except json.JSONDecodeError:
    say('WiFi network not added: invalid JSON format')
  except Exception as e:
    say(f'WiFi network not added: {str(e)}')


@register_command('wifi list')
def list_wifi_networks():
  """List all configured WiFi networks."""
  networks = settings.get('WIFI_NETWORKS') or []
  if not networks:
    say('No WiFi networks configured')
    return
    
  network_names = [net.get('ssid', 'Unknown') for net in networks]
  say(f'Configured networks: {", ".join(network_names)}')


@register_command('wifi remove {}')
def remove_wifi_network(ssid):
  """Remove a WiFi network by SSID."""
  if not ssid:
    say('WiFi network not removed: missing SSID')
    return
    
  networks = settings.get('WIFI_NETWORKS') or []
  networks = [net for net in networks if net.get('ssid') != ssid]
  settings.set('WIFI_NETWORKS', networks)
  
  # We can't easily remove from wpa_supplicant.conf without rewriting the whole file
  # For now, just notify that a manual reconfiguration might be needed
  say(f'Removed WiFi network {ssid} from settings. You may need to edit wpa_supplicant.conf manually to remove it completely.')
