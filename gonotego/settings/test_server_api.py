"""Tests for the settings server's wifi/hotspot API handlers."""
from unittest import mock

from gonotego.settings import server


def test_wifi_test_requires_ssid():
  status, response = server.handle_wifi_test({})
  assert status == 400
  assert 'error' in response


def test_wifi_test_unknown_network():
  with mock.patch('gonotego.settings.server.wifi.get_networks', return_value=[{'ssid': 'other'}]):
    status, response = server.handle_wifi_test({'ssid': 'home'})
  assert status == 404


def test_wifi_test_success():
  with mock.patch('gonotego.settings.server.wifi.get_networks', return_value=[{'ssid': 'home'}]), \
       mock.patch('gonotego.settings.server.wifi.sync_connections') as sync, \
       mock.patch('gonotego.settings.server.wifi.connect_and_verify',
                  return_value=(True, 'Connected to home. Internet verified.')), \
       mock.patch('gonotego.settings.server.system_commands.say') as say:
    status, response = server.handle_wifi_test({'ssid': 'home'})
  assert status == 200
  assert response['success'] is True
  assert sync.called
  # Spoken feedback both when starting and when finishing the test.
  assert say.call_count == 2


def test_wifi_test_failure_keeps_hotspot():
  with mock.patch('gonotego.settings.server.wifi.get_networks', return_value=[{'ssid': 'home'}]), \
       mock.patch('gonotego.settings.server.wifi.sync_connections'), \
       mock.patch('gonotego.settings.server.wifi.connect_and_verify',
                  return_value=(False, 'Could not connect to home: bad password')), \
       mock.patch('gonotego.settings.server.system_commands.say'), \
       mock.patch('gonotego.settings.server.hotspot.stop') as stop:
    status, response = server.handle_wifi_test({'ssid': 'home'})
  assert status == 200
  assert response['success'] is False
  assert not stop.called


def test_hotspot_stop_refuses_without_verified_internet():
  with mock.patch('gonotego.settings.server.internet.is_internet_available', return_value=False), \
       mock.patch('gonotego.settings.server.hotspot.stop') as stop:
    status, response = server.handle_hotspot_stop({})
  assert status == 409
  assert not stop.called


def test_hotspot_stop_with_internet():
  with mock.patch('gonotego.settings.server.internet.is_internet_available', return_value=True), \
       mock.patch('gonotego.settings.server.hotspot.stop') as stop:
    status, response = server.handle_hotspot_stop({})
  assert status == 200
  assert stop.called


def test_hotspot_stop_force():
  with mock.patch('gonotego.settings.server.internet.is_internet_available', return_value=False), \
       mock.patch('gonotego.settings.server.hotspot.stop') as stop:
    status, response = server.handle_hotspot_stop({'force': True})
  assert status == 200
  assert stop.called
