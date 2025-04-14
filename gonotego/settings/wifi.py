"""WiFi settings module for Go Note Go."""
import json
import os
import re
from gonotego.settings import settings
from gonotego.command_center import system_commands

shell = system_commands.shell


def get_networks():
  """Get the list of WiFi networks from Redis settings."""
  try:
    return json.loads(settings.get('WIFI_NETWORKS') or '[]')
  except (json.JSONDecodeError, TypeError):
    return []


def save_networks(networks):
  """Save the list of WiFi networks to Redis settings."""
  settings.set('WIFI_NETWORKS', json.dumps(networks))


def update_wpa_supplicant_config():
  """Update the Go Note Go managed section of wpa_supplicant.conf."""
  networks = get_networks()
  filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
  
  # Check if the file exists
  if not os.path.exists(filepath):
    print('WiFi configuration file not found.')
    return False
  
  # Create network configurations
  network_configs = []
  for network in networks:
    if network.get('psk'):
      network_config = f"""network={{
        ssid="{network['ssid']}"
        psk="{network['psk']}"
        key_mgmt=WPA-PSK
}}"""
    else:
      network_config = f"""network={{
        ssid="{network['ssid']}"
        key_mgmt=NONE
}}"""
    network_configs.append(network_config)
  
  managed_config = "# BEGIN Go Note Go managed WiFi networks\n"
  if networks:
    managed_config += "\n" + "\n".join(network_configs) + "\n"
  managed_config += "# END Go Note Go managed WiFi networks"
  
  # Read the existing config
  try:
    with open(filepath, 'r') as f:
      config = f.read()
    
    # Check if the managed section exists
    pattern = r'# BEGIN Go Note Go managed WiFi networks\n.*?# END Go Note Go managed WiFi networks'
    if re.search(pattern, config, re.DOTALL):
      # Replace the existing managed section
      new_config = re.sub(pattern, managed_config, config, flags=re.DOTALL)
    else:
      # Append the managed section to the end of the file
      new_config = config.rstrip() + "\n\n" + managed_config + "\n"
    
    # Write the new config
    with open('/tmp/wpa_supplicant.conf', 'w') as f:
      f.write(new_config)
    
    # Use sudo to copy the file to the correct location
    shell('sudo cp /tmp/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf')
    shell('rm /tmp/wpa_supplicant.conf')
    
    return True
  except Exception as e:
    print(f"Error updating wpa_supplicant.conf: {e}")
    return False


def reconfigure_wifi():
  """Reconfigure WiFi to apply changes."""
  shell('wpa_cli -i wlan0 reconfigure')


def migrate_networks_from_wpa_supplicant():
  """Scan wpa_supplicant.conf and migrate existing networks to Redis."""
  
  filepath = '/etc/wpa_supplicant/wpa_supplicant.conf'
  
  if not os.path.exists(filepath):
    print('WiFi configuration file not found.')
    return None
    
  try:
    # Read the existing configuration
    with open(filepath, 'r') as f:
      config = f.read()
    
    # Extract network blocks
    network_blocks = re.findall(r'network\s*=\s*{(.*?)}', config, re.DOTALL)
    
    # Process each network block
    networks = []
    for block in network_blocks:
      # Extract SSID
      ssid_match = re.search(r'ssid\s*=\s*"(.*?)"', block)
      if not ssid_match:
        continue
      
      ssid = ssid_match.group(1)
      
      # Check if it's an open network
      if 'key_mgmt=NONE' in block:
        networks.append({'ssid': ssid})
      else:
        # Extract password for WPA networks
        psk_match = re.search(r'psk\s*=\s*"(.*?)"', block)
        if psk_match:
          psk = psk_match.group(1)
          networks.append({'ssid': ssid, 'psk': psk})
    
    # Return the extracted networks
    return networks
  except Exception as e:
    print(f"Error migrating WiFi networks: {e}")
    return None
