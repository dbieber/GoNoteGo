"""WiFi command handlers for Go Note Go."""
from gonotego.command_center import registry
from gonotego.settings import wifi
from gonotego.command_center import system_commands

register_command = registry.register_command
say = system_commands.say
shell = system_commands.shell


@register_command('wifi {} {}')
@register_command('wpa {} {}')
def add_wpa_wifi(ssid, psk):
  if '"' in ssid or '"' in psk:
    say('WiFi not set.')
    return

  # Load existing networks
  networks = wifi.get_networks()

  # Check if this network already exists
  for network in networks:
    if network.get('ssid') == ssid:
      network['psk'] = psk
      break
  else:
    # Network doesn't exist, add it
    networks.append({'ssid': ssid, 'psk': psk})

  # Save updated networks
  wifi.save_networks(networks)
  
  # Update wpa_supplicant.conf
  if wifi.update_wpa_supplicant_config():
    wifi.reconfigure_wifi()
    say(f'WiFi network {ssid} added.')
  else:
    say('Failed to update WiFi configuration.')


@register_command('wifi {}')
def add_wifi_no_psk(ssid):
  if '"' in ssid:
    say('WiFi not set.')
    return
  
  # Load existing networks
  networks = wifi.get_networks()
  
  # Check if this network already exists
  for network in networks:
    if network.get('ssid') == ssid:
      network.pop('psk', None)  # Remove password if it exists
      break
  else:
    # Network doesn't exist, add it
    networks.append({'ssid': ssid})
  
  # Save updated networks
  wifi.save_networks(networks)
  
  # Update wpa_supplicant.conf
  if wifi.update_wpa_supplicant_config():
    wifi.reconfigure_wifi()
    say(f'Open WiFi network {ssid} added.')
  else:
    say('Failed to update WiFi configuration.')


@register_command('wifi-list')
def list_wifi_networks():
  networks = wifi.get_networks()
  if not networks:
    say('No WiFi networks configured.')
    return
  
  network_list = [f"{i+1}. {network['ssid']}" for i, network in enumerate(networks)]
  say('Configured WiFi networks: ' + ', '.join(network_list))


@register_command('wifi-migrate')
def migrate_wifi_networks():
  """Scan wpa_supplicant.conf and migrate existing networks to Redis."""
  networks = wifi.migrate_networks_from_wpa_supplicant()
  
  if networks is None:
    say('WiFi configuration file not found or error reading it.')
    return
    
  # Save the extracted networks to Redis
  if networks:
    wifi.save_networks(networks)
    say(f'Migrated {len(networks)} WiFi networks to settings.')
    
    # Update wpa_supplicant.conf
    wifi.update_wpa_supplicant_config()
  else:
    say('No WiFi networks found to migrate.')


@register_command('wifi-remove {}')
def remove_wifi_network(ssid):
  networks = wifi.get_networks()
  initial_count = len(networks)
  
  # Remove networks with matching SSID
  networks = [network for network in networks if network.get('ssid') != ssid]
  
  if len(networks) < initial_count:
    # Save updated networks
    wifi.save_networks(networks)
    
    # Update wpa_supplicant.conf
    if wifi.update_wpa_supplicant_config():
      wifi.reconfigure_wifi()
      say(f'WiFi network {ssid} removed.')
    else:
      say('Failed to update WiFi configuration.')
  else:
    say(f'WiFi network {ssid} not found.')


@register_command('reconnect')
@register_command('wifi-refresh')
@register_command('wifi-reconfigure')
def reconfigure_wifi():
  wifi.reconfigure_wifi()
