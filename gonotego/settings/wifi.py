"""WiFi settings module for Go Note Go using NetworkManager."""
import json
import subprocess
import re
import os
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


def configure_network_connections():
  """Configure NetworkManager connections for Go Note Go managed WiFi networks."""
  networks = get_networks()
  
  try:
    # Get existing NetworkManager connections
    existing_connections = get_network_manager_connections()
    
    # Get network details by SSID for easy lookup
    network_by_ssid = {network['ssid']: network for network in networks}
    
    # First, handle existing connections
    for conn_name in existing_connections:
      # Check if this is a connection we should manage
      if conn_name in network_by_ssid:
        # It's one of our managed connections
        network = network_by_ssid[conn_name]
        
        # Check if we need to update this connection
        update_needed = False
        
        # Get existing connection details
        details = get_network_manager_connection_details(conn_name)
        if not details:
          # Connection might exist in the list but can't be retrieved - recreate it
          update_needed = True
        else:
          # Check if connection settings differ
          ssid_matches = details.get('802-11-wireless.ssid') == conn_name
          
          # Check security settings
          if network.get('psk'):
            # This should be a secured connection
            has_psk = '802-11-wireless-security.psk' in details
            psk_matches = details.get('802-11-wireless-security.psk') == network['psk']
            update_needed = not (ssid_matches and has_psk and psk_matches)
          else:
            # This should be an open connection
            has_psk = '802-11-wireless-security.psk' in details
            update_needed = not ssid_matches or has_psk  # Update if SSID doesn't match or it has a password
        
        if update_needed:
          # Remove and recreate with correct settings
          remove_connection(conn_name)
          
          # Recreate the connection with current settings
          if network.get('psk'):
            add_wifi_connection(conn_name, network['psk'])
          else:
            add_wifi_connection(conn_name)
        
        # Mark as processed
        network_by_ssid[conn_name]['processed'] = True
    
    # Now add any connections that weren't already in NetworkManager
    for network in networks:
      # Skip networks we already processed
      if network.get('processed'):
        continue
        
      ssid = network['ssid']
      
      # Create new connection
      if network.get('psk'):
        # WPA secured network
        add_wifi_connection(ssid, network['psk'])
      else:
        # Open network
        add_wifi_connection(ssid)
    
    return True
  except Exception as e:
    print(f"Error updating NetworkManager connections: {e}")
    return False


def get_network_manager_connections():
  """Get list of all WiFi connections from NetworkManager."""
  try:
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        capture_output=True, text=True, check=True
    )
    
    # Get all WiFi connections
    connections = []
    for line in result.stdout.splitlines():
      parts = line.split(':', 1)
      if len(parts) == 2:
        name, conn_type = parts
        if conn_type == 'wifi':
          connections.append(name)
    
    return connections
  except subprocess.CalledProcessError as e:
    print(f"Error getting NetworkManager connections: {e}")
    return []


def get_network_manager_connection_details(conn_name):
  """Get details about a specific NetworkManager connection.
  
  Returns:
    A dictionary with connection details or None if connection not found
  """
  try:
    result = subprocess.run(
        ["sudo", "nmcli", "--show-secrets", "connection", "show", conn_name],
        capture_output=True, text=True, check=True
    )
    
    # Parse the connection details
    details = {}
    for line in result.stdout.splitlines():
      if ":" in line:
        key, value = line.split(":", 1)
        details[key.strip()] = value.strip()
    
    return details
  except subprocess.CalledProcessError as e:
    print(f"Error getting details for connection {conn_name}: {e}")
    return None


def add_wifi_connection(ssid, password=None):
  """Add a new WiFi connection (secure or open).
  
  Args:
    ssid: The SSID of the network to add
    password: If provided, adds a WPA secured network. If None, adds an open network.
  
  Returns:
    True on success, False on error
  """
  try:
    conn_name = ssid
    
    # Base command for both connection types
    cmd = [
        "sudo", "nmcli", "connection", "add",
        "type", "wifi",
        "con-name", conn_name,
        "ifname", "wlan0",
        "ssid", ssid
    ]
    
    # Add security parameters if password is provided
    if password:
      cmd.extend([
          "wifi-sec.key-mgmt", "wpa-psk",
          "wifi-sec.psk", password
      ])
    
    subprocess.run(cmd, check=True, capture_output=True)
    return True
  except subprocess.CalledProcessError as e:
    conn_type = "WPA" if password else "open"
    print(f"Error adding {conn_type} connection for {ssid}: {e}")
    print(f"Error output: {e.stderr}")
    return False


def remove_connection(conn_name):
  """Remove a NetworkManager connection."""
  try:
    subprocess.run(
        ["sudo", "nmcli", "connection", "delete", conn_name],
        check=True, capture_output=True
    )
    return True
  except subprocess.CalledProcessError as e:
    print(f"Error removing connection {conn_name}: {e}")
    print(f"Error output: {e.stderr}")
    return False


def reconfigure_wifi():
  """Reconnect to available WiFi networks."""
  # Refresh all connections and activate the best available one
  try:
    # Restart NetworkManager service to apply changes
    shell('sudo systemctl restart NetworkManager')
    
    # Get list of available configured networks
    networks = get_networks()
    
    # Try to connect to the first available network
    for network in networks:
      ssid = network['ssid']
      try:
        # Check if we can see this network
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
            capture_output=True, text=True, check=True
        )
        
        available_networks = [line.strip() for line in result.stdout.splitlines()]
        
        if ssid in available_networks:
          # Try to connect to this network
          subprocess.run(
              ["nmcli", "connection", "up", "id", ssid],
              check=True, capture_output=True
          )
          print(f"Connected to {ssid}")
          break
      except Exception as e:
        print(f"Error connecting to {ssid}: {e}")
        continue
    
    return True
  except Exception as e:
    print(f"Error reconfiguring WiFi: {e}")
    return False


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


def migrate_from_networkmanager():
  """Scan NetworkManager connections and migrate to Redis."""
  try:
    # Get all wifi connections
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        capture_output=True, text=True, check=True
    )
    
    wifi_connections = []
    for line in result.stdout.splitlines():
      parts = line.split(':', 1)
      if len(parts) == 2:
        name, conn_type = parts
        if conn_type == 'wifi':
          wifi_connections.append(name)
    
    networks = []
    for conn_name in wifi_connections:
      # Get connection details
      result = subprocess.run(
          ["sudo", "nmcli", "--show-secrets", "connection", "show", conn_name],
          capture_output=True, text=True, check=True
      )
      
      # Parse output to get SSID and PSK
      ssid = None
      psk = None
      
      for line in result.stdout.splitlines():
        if "802-11-wireless.ssid:" in line:
          ssid = line.split(":", 1)[1].strip()
        elif "802-11-wireless-security.psk:" in line:
          psk = line.split(":", 1)[1].strip()
      
      if ssid:
        if psk:
          networks.append({'ssid': ssid, 'psk': psk})
        else:
          networks.append({'ssid': ssid})
    
    return networks
  except Exception as e:
    print(f"Error migrating from NetworkManager: {e}")
    return None
