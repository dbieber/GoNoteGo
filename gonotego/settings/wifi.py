"""WiFi settings module for Go Note Go using NetworkManager."""
import json
import subprocess
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
    # Add or update connections - add_wifi_connection handles either adding new 
    # or modifying existing connections as needed
    for network in networks:
      ssid = network['ssid']
      
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


def modify_wifi_connection(ssid, password=None):
  """Modify an existing WiFi connection.
  
  Args:
    ssid: The SSID/name of the connection to modify
    password: If provided, configures as WPA secured network. If None, configures as open network.
  
  Returns:
    True on success, False on error
  """
  conn_name = ssid
  
  try:
    # Build the modify command
    modify_cmd = ["sudo", "nmcli", "connection", "modify", conn_name]
    
    # Add basic settings
    modify_cmd.extend(["802-11-wireless.ssid", ssid])
    
    # Add security settings
    if password:
      modify_cmd.extend([
          "802-11-wireless-security.key-mgmt", "wpa-psk",
          "802-11-wireless-security.psk", password
      ])
    else:
      # For open networks, remove security
      modify_cmd.extend([
          "802-11-wireless-security.key-mgmt", "",
          "-802-11-wireless-security.psk"  # Remove PSK
      ])
    
    # Run the modify command
    subprocess.run(modify_cmd, check=True, capture_output=True)
    return True
  except subprocess.CalledProcessError as e:
    print(f"Error modifying connection {ssid}: {e}")
    print(f"Error output: {e.stderr}")
    return False


def add_wifi_connection(ssid, password=None):
  """Add a new WiFi connection (secure or open).
  
  Args:
    ssid: The SSID of the network to add
    password: If provided, adds a WPA secured network. If None, adds an open network.
  
  Returns:
    True on success, False on error
  """
  conn_name = ssid
  
  # Base command for both connection types
  add_cmd = [
      "sudo", "nmcli", "connection", "add",
      "type", "wifi",
      "con-name", conn_name,
      "ifname", "wlan0",
      "ssid", ssid
  ]
  
  # Add security parameters if password is provided
  if password:
    add_cmd.extend([
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", password
    ])
  
  try:
    # Try to add the connection
    subprocess.run(add_cmd, check=True, capture_output=True)
    return True
  except subprocess.CalledProcessError as e:
    # If the error is that the connection already exists, try to modify it
    if "already exists" in str(e.stderr):
      return modify_wifi_connection(ssid, password)
    else:
      # Other error
      conn_type = "WPA" if password else "open"
      print(f"Error adding {conn_type} connection for {ssid}: {e}")
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

