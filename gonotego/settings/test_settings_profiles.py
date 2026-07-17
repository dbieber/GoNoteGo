"""Tests for named settings profiles."""
import pytest

from gonotego.settings import settings


def test_default_profile_uses_legacy_keys(fake_redis):
  # Existing installs' Redis keys keep working with no migration.
  fake_redis.set('GoNoteGo:settings:EMAIL', repr('david@example.com'))
  assert settings.get_active_profile() == 'default'
  assert settings.get('EMAIL') == 'david@example.com'
  settings.set('EMAIL', 'other@example.com')
  assert fake_redis.get('GoNoteGo:settings:EMAIL') == repr('other@example.com').encode('utf-8')


def test_named_profile_overrides_and_falls_back(fake_redis):
  settings.set('EMAIL', 'david@example.com')
  settings.set('SLACK_CHANNEL', 'davids-channel')

  settings.set_active_profile('work')
  # Fallback: unset keys read the default profile's values.
  assert settings.get('EMAIL') == 'david@example.com'
  # Override: setting a key only affects this profile.
  settings.set('EMAIL', 'work@example.com')
  assert settings.get('EMAIL') == 'work@example.com'
  assert settings.get('SLACK_CHANNEL') == 'davids-channel'

  settings.set_active_profile('default')
  assert settings.get('EMAIL') == 'david@example.com'


def test_device_settings_shared_across_profiles(fake_redis):
  settings.set('WIFI_NETWORKS', [{'ssid': 'home', 'psk': 'pw'}])
  settings.set_active_profile('guest')
  assert settings.get('WIFI_NETWORKS') == [{'ssid': 'home', 'psk': 'pw'}]
  settings.set('WIFI_NETWORKS', [{'ssid': 'cafe'}])
  settings.set_active_profile('default')
  assert settings.get('WIFI_NETWORKS') == [{'ssid': 'cafe'}]


def test_secure_settings_fallback_from_named_profile(fake_redis):
  settings.set_active_profile('work')
  # Nothing in Redis for HOTKEY: falls through to secure_settings.
  assert settings.get('HOTKEY') == '<HOTKEY>'


def test_list_profiles_orders_default_first(fake_redis):
  assert settings.list_profiles() == ['default']
  settings.set_active_profile('work')
  settings.set_active_profile('andrea')
  assert settings.list_profiles() == ['default', 'andrea', 'work']


def test_profile_name_validation(fake_redis):
  with pytest.raises(ValueError):
    settings.set_active_profile('bad name!')
  with pytest.raises(ValueError):
    settings.set_active_profile('')
  settings.set_active_profile('work-2')
  assert settings.get_active_profile() == 'work-2'


def test_delete_profile(fake_redis):
  settings.set_active_profile('work')
  settings.set('EMAIL', 'work@example.com')
  assert settings.delete_profile('work') is True
  # Deleting the active profile switches back to default.
  assert settings.get_active_profile() == 'default'
  assert 'work' not in settings.list_profiles()
  # Its settings are gone: switching back recreates an empty profile.
  settings.set_active_profile('work')
  assert settings.get('EMAIL') == '<EMAIL>'


def test_delete_default_profile_refused(fake_redis):
  assert settings.delete_profile('default') is False
  assert settings.list_profiles() == ['default']


def test_clear_all_scoped_to_active_profile(fake_redis):
  settings.set('EMAIL', 'david@example.com')
  settings.set_active_profile('work')
  settings.set('EMAIL', 'work@example.com')

  settings.clear_all()
  # Work's override is gone; the default value shows through again.
  assert settings.get('EMAIL') == 'david@example.com'

  settings.set('EMAIL', 'work@example.com')
  settings.set_active_profile('default')
  settings.clear_all()
  # Default's settings cleared, but the work profile's are untouched.
  assert settings.get('EMAIL') == '<EMAIL>'
  settings.set_active_profile('work')
  assert settings.get('EMAIL') == 'work@example.com'
