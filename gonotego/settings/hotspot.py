"""WiFi hotspot control for monitor-free configuration.

The hotspot runs on a virtual access-point interface (uap0) alongside the
wlan0 client interface. That means Go Note Go can try out a new WiFi
network on wlan0 while you stay connected to the hotspot -- so the config
flow can verify a network actually works before the hotspot is torn down,
and a typo'd password can never strand the device.

While the hotspot is up, the settings web app (which is always running on
port 8000) is reachable at http://192.168.4.1:8000.
"""
import subprocess

from gonotego.command_center import system_commands

SSID = 'GoNoteGo-Wifi'
SSID_SPOKEN = 'Go Note Go WiFi'
PASSWORD = 'swingset'
CONFIG_URL = 'http://192.168.4.1:8000'

shell = system_commands.shell


def is_active():
  """Whether the hotspot (hostapd) is currently running."""
  try:
    result = subprocess.run(
        ['systemctl', 'is-active', '--quiet', 'hostapd'], check=False)
    return result.returncode == 0
  except Exception:
    return False


def start(speak=True):
  """Start the hotspot and announce how to connect. Safe to call repeatedly."""
  shell('sudo systemctl stop uap0.service')
  shell('sudo systemctl stop dnsmasq.service')
  shell('sudo systemctl stop hostapd.service')

  shell('sudo systemctl start uap0.service')
  shell('sudo ip addr add 192.168.4.1/24 dev uap0')
  shell('sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE')
  shell('sudo systemctl start dnsmasq.service')
  shell('sudo systemctl start hostapd.service')
  if speak:
    announce()


def announce():
  """Speak the hotspot's SSID, password, and config page address."""
  system_commands.say(
      f'Hotspot on. Join the WiFi network {SSID_SPOKEN}. '
      f'The password is {PASSWORD}. '
      'Then visit 192.168.4.1, port 8000, in a browser.')


def stop(speak=True):
  """Stop the hotspot."""
  shell('sudo systemctl stop hostapd.service')
  shell('sudo systemctl stop dnsmasq.service')
  shell('sudo systemctl stop uap0.service')
  if speak:
    system_commands.say('Hotspot off. Type colon hotspot to turn it back on.')
