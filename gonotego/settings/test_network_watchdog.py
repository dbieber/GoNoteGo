"""Tests for the auto-hotspot network watchdog."""
from unittest import mock

from gonotego.settings import network_watchdog


def make_patches(hotspot_active=False, internet_available=False, enabled=True):
  return (
      mock.patch('gonotego.settings.network_watchdog.hotspot.is_active', return_value=hotspot_active),
      mock.patch('gonotego.settings.network_watchdog.internet.is_internet_available', return_value=internet_available),
      mock.patch('gonotego.settings.network_watchdog.auto_hotspot_enabled', return_value=enabled),
      mock.patch('gonotego.settings.network_watchdog.hotspot.start'),
      mock.patch('gonotego.settings.network_watchdog.system_commands.say'),
  )


def run_ticks(watchdog, n, **kwargs):
  patches = make_patches(**kwargs)
  results = []
  with patches[0], patches[1], patches[2], patches[3] as start, patches[4]:
    for _ in range(n):
      results.append(watchdog.tick())
  return results, start


def test_hotspot_starts_after_consecutive_failures():
  watchdog = network_watchdog.Watchdog()
  n = network_watchdog.FAILURES_BEFORE_HOTSPOT
  results, start = run_ticks(watchdog, n)
  assert results == [False] * (n - 1) + [True]
  assert start.call_count == 1


def test_hotspot_only_starts_once_per_offline_stretch():
  watchdog = network_watchdog.Watchdog()
  n = network_watchdog.FAILURES_BEFORE_HOTSPOT
  results, start = run_ticks(watchdog, n + 5)
  assert sum(results) == 1
  assert start.call_count == 1


def test_internet_resets_failure_count():
  watchdog = network_watchdog.Watchdog()
  n = network_watchdog.FAILURES_BEFORE_HOTSPOT
  run_ticks(watchdog, n - 1)
  # Internet comes back: counter resets, and the hotspot can fire again later.
  run_ticks(watchdog, 1, internet_available=True)
  assert watchdog.failures == 0
  results, start = run_ticks(watchdog, n)
  assert results[-1] is True


def test_no_hotspot_while_hotspot_active():
  watchdog = network_watchdog.Watchdog()
  n = network_watchdog.FAILURES_BEFORE_HOTSPOT
  results, start = run_ticks(watchdog, n + 2, hotspot_active=True)
  assert results == [False] * (n + 2)
  assert start.call_count == 0


def test_no_hotspot_when_disabled():
  watchdog = network_watchdog.Watchdog()
  n = network_watchdog.FAILURES_BEFORE_HOTSPOT
  results, start = run_ticks(watchdog, n + 2, enabled=False)
  assert results == [False] * (n + 2)
  assert start.call_count == 0


def test_auto_hotspot_enabled_values(fake_redis, monkeypatch):
  from gonotego.settings import settings

  monkeypatch.setattr(settings, 'get', lambda key: True)
  assert network_watchdog.auto_hotspot_enabled() is True

  monkeypatch.setattr(settings, 'get', lambda key: False)
  assert network_watchdog.auto_hotspot_enabled() is False

  monkeypatch.setattr(settings, 'get', lambda key: 'off')
  assert network_watchdog.auto_hotspot_enabled() is False

  monkeypatch.setattr(settings, 'get', lambda key: '<AUTO_HOTSPOT>')
  assert network_watchdog.auto_hotspot_enabled() is True

  def raise_attribute_error(key):
    raise AttributeError(key)
  monkeypatch.setattr(settings, 'get', raise_attribute_error)
  assert network_watchdog.auto_hotspot_enabled() is True
