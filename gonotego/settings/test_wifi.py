"""Tests for the WiFi settings module."""
import subprocess
from unittest import mock

from gonotego.settings import settings
from gonotego.settings import wifi


def completed(returncode=0, stdout='', stderr=''):
  return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_get_networks_accepts_list_from_secure_settings(fake_redis, monkeypatch):
  # secure_settings-style value: a plain Python list (e.g. from the boot partition).
  monkeypatch.setattr(settings, 'get', lambda key: [{'ssid': 'home', 'psk': 'hunter2'}])
  assert wifi.get_networks() == [{'ssid': 'home', 'psk': 'hunter2'}]


def test_get_networks_accepts_legacy_json_string(fake_redis, monkeypatch):
  # Older versions stored a JSON string in Redis.
  monkeypatch.setattr(settings, 'get', lambda key: '[{"ssid": "home"}]')
  assert wifi.get_networks() == [{'ssid': 'home'}]


def test_get_networks_rejects_malformed_values(fake_redis, monkeypatch):
  monkeypatch.setattr(settings, 'get', lambda key: 'not json')
  assert wifi.get_networks() == []
  monkeypatch.setattr(settings, 'get', lambda key: {'ssid': 'home'})
  assert wifi.get_networks() == []
  monkeypatch.setattr(settings, 'get', lambda key: [{'no-ssid': True}, 'nope'])
  assert wifi.get_networks() == []


def test_get_networks_missing_setting(fake_redis, monkeypatch):
  def raise_attribute_error(key):
    raise AttributeError(key)
  monkeypatch.setattr(settings, 'get', raise_attribute_error)
  assert wifi.get_networks() == []


def test_save_and_get_networks_roundtrip(fake_redis):
  networks = [{'ssid': 'home', 'psk': 'hunter2'}, {'ssid': 'open-cafe'}]
  wifi.save_networks(networks)
  assert wifi.get_networks() == networks


def test_sync_connections_adds_and_prunes(fake_redis):
  wifi.save_networks([{'ssid': 'home', 'psk': 'hunter2'}])
  # Pretend Go Note Go previously created a connection for 'old-network'.
  wifi._record_managed_connection('old-network')

  commands = []

  def fake_run(cmd, **kwargs):
    commands.append(cmd)
    return completed()

  with mock.patch.object(subprocess, 'run', side_effect=fake_run):
    assert wifi.sync_connections() is True

  add_commands = [cmd for cmd in commands if 'add' in cmd]
  delete_commands = [cmd for cmd in commands if 'delete' in cmd]
  assert len(add_commands) == 1 and 'home' in add_commands[0]
  assert len(delete_commands) == 1 and 'old-network' in delete_commands[0]
  # 'old-network' is no longer tracked; 'home' is.
  assert wifi._managed_connections() == {'home'}


def test_sync_connections_reports_failures(fake_redis):
  wifi.save_networks([{'ssid': 'home'}])

  def fake_run(cmd, **kwargs):
    raise subprocess.CalledProcessError(1, cmd, stderr=b'boom')

  with mock.patch.object(subprocess, 'run', side_effect=fake_run):
    assert wifi.sync_connections() is False


def test_connect_and_verify_success(fake_redis):
  with mock.patch.object(subprocess, 'run', return_value=completed()):
    with mock.patch('gonotego.settings.wifi.internet.is_internet_available', return_value=True):
      success, message = wifi.connect_and_verify('home')
  assert success
  assert 'home' in message


def test_connect_and_verify_bad_password(fake_redis):
  def fail_run(cmd, **kwargs):
    raise subprocess.CalledProcessError(1, cmd, stderr='Secrets were required')

  with mock.patch.object(subprocess, 'run', side_effect=fail_run):
    success, message = wifi.connect_and_verify('home')
  assert not success
  assert 'Secrets were required' in message


def test_connect_and_verify_no_internet(fake_redis):
  with mock.patch.object(subprocess, 'run', return_value=completed()):
    with mock.patch('gonotego.settings.wifi.internet.is_internet_available', return_value=False):
      success, message = wifi.connect_and_verify('home', timeout_seconds=0)
  assert not success
  assert 'could not verify' in message.lower()


def test_get_connected_ssid(fake_redis):
  output = 'no:other\nyes:home\n'
  with mock.patch.object(subprocess, 'run', return_value=completed(stdout=output)):
    assert wifi.get_connected_ssid() == 'home'
  with mock.patch.object(subprocess, 'run', return_value=completed(stdout='no:other\n')):
    assert wifi.get_connected_ssid() is None
