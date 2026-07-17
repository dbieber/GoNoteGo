"""Network watchdog: syncs WiFi settings and auto-starts the setup hotspot.

Runs as its own supervisord program (GoNoteGo-network). On startup it
pushes the WIFI_NETWORKS setting into NetworkManager (the setting is the
single source of truth for WiFi configuration -- including networks
configured in secure_settings.py on the boot partition). After that it
checks connectivity periodically; if the device can't get online for a
few consecutive checks, it stands up the configuration hotspot and speaks
instructions, so a Go Note Go with no known WiFi nearby can always be
configured without a monitor.

The hotspot is only auto-started once per offline stretch, and never while
it is already running. Set AUTO_HOTSPOT to False to disable the automatic
behavior (':hotspot' still works manually).
"""
import time

from gonotego.common import internet
from gonotego.command_center import system_commands
from gonotego.settings import hotspot
from gonotego.settings import settings
from gonotego.settings import wifi

CHECK_INTERVAL_SECONDS = 30
FAILURES_BEFORE_HOTSPOT = 4


def auto_hotspot_enabled():
  """Whether the watchdog may start the hotspot automatically. Default True."""
  try:
    value = settings.get('AUTO_HOTSPOT')
  except AttributeError:
    # Older secure_settings.py files don't define AUTO_HOTSPOT.
    return True
  if isinstance(value, str):
    if value.startswith('<'):
      # Unconfigured template placeholder.
      return True
    return value.strip().lower() not in ('false', 'off', 'no', '0')
  return bool(value)


class Watchdog:

  def __init__(self):
    self.failures = 0
    self.hotspot_started = False

  def tick(self):
    """Runs one connectivity check. Returns True if it started the hotspot."""
    if hotspot.is_active():
      # Don't interfere while the hotspot is up; the settings app owns it.
      return False
    if internet.is_internet_available():
      self.failures = 0
      self.hotspot_started = False
      return False
    self.failures += 1
    if (self.failures >= FAILURES_BEFORE_HOTSPOT
        and not self.hotspot_started
        and auto_hotspot_enabled()):
      # Only start the hotspot once per offline stretch, so turning it off
      # by hand while offline doesn't lead to a tug-of-war.
      self.hotspot_started = True
      system_commands.say('No WiFi connection. Starting the setup hotspot.')
      hotspot.start()
      return True
    return False


def main():
  print('Starting network watchdog.')
  try:
    wifi.sync_connections()
  except Exception as e:
    print(f'Error syncing WiFi connections: {e}')
  watchdog = Watchdog()
  while True:
    try:
      watchdog.tick()
    except Exception as e:
      print(f'Network watchdog error: {e}')
    time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
  main()
