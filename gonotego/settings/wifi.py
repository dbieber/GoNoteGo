"""WiFi settings module for Go Note Go using NetworkManager.

The single source of truth for WiFi configuration is the WIFI_NETWORKS
setting (a list of {'ssid': ..., 'psk': ...} dicts; see
gonotego.settings.settings). It can come from Redis (set via the settings
web app or ':wifi' commands) or from secure_settings.py (e.g. placed on
the boot partition before first boot).

sync_connections() pushes that list into NetworkManager. Every connection
Go Note Go creates is recorded in Redis, so connections removed from
WIFI_NETWORKS are also removed from NetworkManager on the next sync.
Connections created outside Go Note Go (e.g. by hand with nmcli) are left
alone.
"""
import json
import subprocess
import time

from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.settings import settings

MANAGED_CONNECTIONS_KEY = 'GoNoteGo:wifi:managed-connections'


def get_networks():
  """Get the list of WiFi networks from settings.

  Accepts either a list (secure_settings.py or new-style Redis values) or a
  JSON string (legacy Redis values written by older versions).
  """
  try:
    value = settings.get('WIFI_NETWORKS')
  except AttributeError:
    return []
  if isinstance(value, str):
    try:
      value = json.loads(value)
    except json.JSONDecodeError:
      return []
  if not isinstance(value, list):
    return []
  return [
      network for network in value
      if isinstance(network, dict) and network.get('ssid')
  ]


def save_networks(networks):
  """Save the list of WiFi networks to settings."""
  settings.set('WIFI_NETWORKS', networks)


def _managed_connections():
  """The set of NetworkManager connection names created by Go Note Go."""
  r = interprocess.get_redis_client()
  return {value.decode('utf-8') for value in r.smembers(MANAGED_CONNECTIONS_KEY)}


def _record_managed_connection(ssid):
  interprocess.get_redis_client().sadd(MANAGED_CONNECTIONS_KEY, ssid)


def _forget_managed_connection(ssid):
  interprocess.get_redis_client().srem(MANAGED_CONNECTIONS_KEY, ssid)


def sync_connections():
  """Make NetworkManager match the WIFI_NETWORKS setting.

  Adds or updates a connection for every configured network and deletes
  Go-Note-Go-managed connections that are no longer configured.

  Returns:
    True if every configured network was added/updated successfully.
  """
  networks = get_networks()
  ok = True
  for network in networks:
    if not add_wifi_connection(network['ssid'], network.get('psk')):
      ok = False
  configured_ssids = {network['ssid'] for network in networks}
  for ssid in sorted(_managed_connections() - configured_ssids):
    delete_connection(ssid)
  return ok


def delete_connection(ssid):
  """Delete a NetworkManager connection and stop tracking it."""
  try:
    subprocess.run(
        ['sudo', 'nmcli', 'connection', 'delete', 'id', ssid],
        check=True, capture_output=True)
  except subprocess.CalledProcessError as e:
    # The connection may already be gone; either way stop tracking it.
    print(f'Error deleting connection {ssid}: {e}')
  _forget_managed_connection(ssid)


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
    _record_managed_connection(ssid)
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
    _record_managed_connection(ssid)
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


def get_connected_ssid():
  """The SSID wlan0 is currently connected to, or None."""
  try:
    result = subprocess.run(
        ['nmcli', '-t', '-f', 'active,ssid', 'device', 'wifi'],
        capture_output=True, text=True, timeout=10)
    for line in result.stdout.splitlines():
      if line.startswith('yes:'):
        return line.split(':', 1)[1] or None
  except Exception as e:
    print(f'Error checking connected SSID: {e}')
  return None


def connect_and_verify(ssid, timeout_seconds=45):
  """Connect to a configured network and verify real internet access.

  Used by the hotspot config flow: the hotspot stays up (on uap0) while
  wlan0 tries the target network, so a bad password can't strand the
  device.

  Returns:
    A (success, message) tuple. success is True only once a genuine
    internet connectivity check passes on the new connection.
  """
  try:
    subprocess.run(
        ['sudo', 'nmcli', 'connection', 'up', 'id', ssid],
        check=True, capture_output=True, text=True, timeout=90)
  except subprocess.CalledProcessError as e:
    detail = (e.stderr or '').strip() or 'unknown error'
    return False, f'Could not connect to {ssid}: {detail}'
  except subprocess.TimeoutExpired:
    return False, f'Timed out connecting to {ssid}.'

  deadline = time.time() + timeout_seconds
  while time.time() < deadline:
    if internet.is_internet_available():
      return True, f'Connected to {ssid}. Internet verified.'
    time.sleep(2)
  return False, f'Joined {ssid} but could not verify internet access.'


def reconfigure_wifi():
  """Reconnect to available WiFi networks."""
  # Refresh all connections and activate the best available one
  try:
    # Restart NetworkManager service to apply changes
    subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'], check=False)

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
